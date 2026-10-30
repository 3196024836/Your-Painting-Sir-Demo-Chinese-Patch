import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'source'))
from patch_engine import Bundle, PatchError, install, restore


def digest(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


class InstallerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.exe = self.root / 'Your Painting, Sir.exe'
        self.exe.write_bytes(b'MZ test launcher 1234567')
        with zipfile.ZipFile(self.exe, 'a', zipfile.ZIP_DEFLATED) as z:
            z.writestr('conf.lua', 'GAME_VERSION = "DEMO-1.2.16"')
            z.writestr('data/example.lua', 'return "Hello"')
            z.writestr('assets/untouched.bin', b'original content')
        self.original = self.exe.read_bytes()
        self.bundle = Bundle(
            original_sha256=digest(self.exe),
            patch_id='unit-test-1',
            replacements={'data/example.lua': b'return "\xe4\xbd\xa0\xe5\xa5\xbd"'},
            additions={'assets/fonts/zh.ttf': b'font'},
        )
        self.backup = self.exe.with_name(self.exe.name + '.zh-backup')
        self.not_running = lambda path: False

    def test_installs_and_restores_without_changing_unrelated_entries(self):
        self.assertEqual(install(self.exe, self.bundle, running=self.not_running), 'installed')
        self.assertEqual(self.backup.read_bytes(), self.original)
        with zipfile.ZipFile(self.exe) as z:
            self.assertEqual(z.read('data/example.lua'), b'return "\xe4\xbd\xa0\xe5\xa5\xbd"')
            self.assertEqual(z.read('assets/untouched.bin'), b'original content')
            self.assertEqual(z.read('assets/fonts/zh.ttf'), b'font')
            self.assertEqual(json.loads(z.read('__yps_zh_patch__.json'))['patch_id'], 'unit-test-1')
        self.assertEqual(restore(self.exe, self.bundle, running=self.not_running), 'restored')
        self.assertEqual(self.exe.read_bytes(), self.original)
        self.assertEqual(self.backup.read_bytes(), self.original)

    def test_repeated_install_and_reinstall_after_restoration(self):
        install(self.exe, self.bundle, running=self.not_running)
        patched = self.exe.read_bytes()
        self.assertEqual(install(self.exe, self.bundle, running=self.not_running), 'already_installed')
        self.assertEqual(self.exe.read_bytes(), patched)
        restore(self.exe, self.bundle, running=self.not_running)
        self.assertEqual(install(self.exe, self.bundle, running=self.not_running), 'installed')
        self.assertEqual(self.backup.read_bytes(), self.original)

    def test_rejects_incorrect_version_before_creating_backup(self):
        self.exe.write_bytes(self.original + b'changed')
        with self.assertRaisesRegex(PatchError, '版本|校验'):
            install(self.exe, self.bundle, running=self.not_running)
        self.assertFalse(self.backup.exists())
        self.assertEqual(self.exe.read_bytes(), self.original + b'changed')

    def test_rejects_mismatched_backup_without_overwriting_it(self):
        self.backup.write_bytes(b'user backup')
        with self.assertRaisesRegex(PatchError, '备份'):
            install(self.exe, self.bundle, running=self.not_running)
        self.assertEqual(self.backup.read_bytes(), b'user backup')
        self.assertEqual(self.exe.read_bytes(), self.original)

    def test_refuses_when_game_is_running(self):
        with self.assertRaisesRegex(PatchError, '运行'):
            install(self.exe, self.bundle, running=lambda _: True)
        self.assertFalse(self.backup.exists())
        self.assertEqual(self.exe.read_bytes(), self.original)

    def test_failed_replace_leaves_original_and_backup(self):
        def fail(*_):
            raise PermissionError('locked')
        with self.assertRaises(PatchError):
            install(self.exe, self.bundle, running=self.not_running, replace=fail)
        self.assertEqual(self.exe.read_bytes(), self.original)
        self.assertEqual(self.backup.read_bytes(), self.original)
        self.assertEqual(sorted(p.name for p in self.root.iterdir()), [self.exe.name, self.backup.name])

    def test_permission_error_suggests_administrator_and_keeps_files(self):
        def fail(*_):
            raise PermissionError(13, 'access denied')
        with self.assertRaisesRegex(PatchError, '管理员'):
            install(self.exe, self.bundle, running=self.not_running, replace=fail)
        self.assertEqual(self.exe.read_bytes(), self.original)
        self.assertEqual(self.backup.read_bytes(), self.original)

    def test_sharing_violation_reports_file_in_use(self):
        def fail(*_):
            error = PermissionError(13, 'sharing violation')
            error.winerror = 32
            raise error
        with self.assertRaisesRegex(PatchError, '占用'):
            install(self.exe, self.bundle, running=self.not_running, replace=fail)
        self.assertEqual(self.exe.read_bytes(), self.original)
        self.assertEqual(self.backup.read_bytes(), self.original)

    def test_insufficient_space_stops_before_backup(self):
        with patch('patch_engine.shutil.disk_usage') as usage:
            usage.return_value = type('Usage', (), {'free': 0})()
            with self.assertRaisesRegex(PatchError, '空间不足'):
                install(self.exe, self.bundle, running=self.not_running)
        self.assertEqual(self.exe.read_bytes(), self.original)
        self.assertFalse(self.backup.exists())

    def test_restore_rejects_unknown_current_exe(self):
        install(self.exe, self.bundle, running=self.not_running)
        self.exe.write_bytes(b'new Steam build')
        with self.assertRaisesRegex(PatchError, '版本|不是'):
            restore(self.exe, self.bundle, running=self.not_running)
        self.assertEqual(self.exe.read_bytes(), b'new Steam build')

    def test_missing_or_corrupt_backup_prevents_restore(self):
        install(self.exe, self.bundle, running=self.not_running)
        patched = self.exe.read_bytes()
        self.backup.write_bytes(b'broken backup')
        with self.assertRaisesRegex(PatchError, '备份'):
            restore(self.exe, self.bundle, running=self.not_running)
        self.assertEqual(self.exe.read_bytes(), patched)

    def test_install_refuses_if_steam_changes_exe_before_swap(self):
        def progress(message):
            if message == '正在完成安装…':
                self.exe.write_bytes(b'newer Steam build')
        with self.assertRaisesRegex(PatchError, '变化|更新'):
            install(self.exe, self.bundle, running=self.not_running, progress=progress)
        self.assertEqual(self.exe.read_bytes(), b'newer Steam build')
        self.assertEqual(self.backup.read_bytes(), self.original)

    def test_restore_refuses_if_exe_changes_before_swap(self):
        install(self.exe, self.bundle, running=self.not_running)
        def replace_after_change(src, dst):
            raise AssertionError('restore should have noticed the external change first')
        def progress(message):
            if message == '正在恢复原版…':
                self.exe.write_bytes(b'newer Steam build')
        with self.assertRaisesRegex(PatchError, '变化|更新'):
            restore(self.exe, self.bundle, running=self.not_running, replace=replace_after_change, progress=progress)
        self.assertEqual(self.exe.read_bytes(), b'newer Steam build')

    def test_bad_patch_marker_is_rejected_as_user_facing_error(self):
        with zipfile.ZipFile(self.exe, 'a') as z:
            z.writestr('__yps_zh_patch__.json', '[1]')
        with self.assertRaises(PatchError):
            install(self.exe, self.bundle, running=self.not_running)
    def test_missing_replacement_target_fails_without_replacement(self):
        bundle = Bundle(self.bundle.original_sha256, 'test2', {'absent.lua': b'x'}, {})
        with self.assertRaisesRegex(PatchError, '资源'):
            install(self.exe, bundle, running=self.not_running)
        self.assertEqual(self.exe.read_bytes(), self.original)

if __name__ == '__main__':
    unittest.main()

