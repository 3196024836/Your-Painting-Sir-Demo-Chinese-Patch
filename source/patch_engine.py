"""Transactional installer for one explicitly supported fused LÖVE executable."""
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import zipfile

MARKER = '__yps_zh_patch__.json'
BACKUP_SUFFIX = '.zh-backup'


class PatchError(Exception):
    """A safe-to-display explanation; the original/backup are kept on failure."""


@dataclass(frozen=True)
class Bundle:
    original_sha256: str
    patch_id: str
    replacements: dict
    additions: dict


def _failure_message(action, exc):
    if getattr(exc, 'winerror', None) in (32, 33):
        advice = '游戏文件正被其他程序占用，请关闭游戏及占用文件的程序后重试。'
    elif isinstance(exc, PermissionError):
        advice = '可能没有权限写入游戏目录，或游戏文件正被占用。请关闭游戏及占用文件的程序；如果仍失败且游戏位于 Program Files，请右键以管理员身份运行本工具。'
    else:
        advice = '请检查磁盘空间、文件占用和目录权限。'
    return f'{action}未完成：{exc}。{advice}'


def _sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def game_is_running(target):
    """Find the selected executable's process, failing closed if its path is unavailable."""
    if sys.platform != 'win32':
        return False
    import ctypes
    from ctypes import wintypes
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    class ProcessEntry(ctypes.Structure):
        _fields_ = [('dwSize', wintypes.DWORD), ('cntUsage', wintypes.DWORD),
                    ('th32ProcessID', wintypes.DWORD), ('th32DefaultHeapID', ctypes.c_size_t),
                    ('th32ModuleID', wintypes.DWORD), ('cntThreads', wintypes.DWORD),
                    ('th32ParentProcessID', wintypes.DWORD), ('pcPriClassBase', wintypes.LONG),
                    ('dwFlags', wintypes.DWORD), ('szExeFile', wintypes.WCHAR * 260)]
    kernel.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    kernel.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    kernel.Process32FirstW.argtypes = [wintypes.HANDLE, ctypes.POINTER(ProcessEntry)]
    kernel.Process32FirstW.restype = wintypes.BOOL
    kernel.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(ProcessEntry)]
    kernel.Process32NextW.restype = wintypes.BOOL
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
    kernel.QueryFullProcessImageNameW.restype = wintypes.BOOL
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    snapshot = kernel.CreateToolhelp32Snapshot(2, 0)
    if snapshot == ctypes.c_void_p(-1).value:
        raise PatchError('无法检查游戏进程，请关闭游戏后重试。')
    try:
        entry = ProcessEntry(); entry.dwSize = ctypes.sizeof(entry)
        ok = kernel.Process32FirstW(snapshot, ctypes.byref(entry))
        while ok:
            if entry.szExeFile.casefold() == target.name.casefold():
                handle = kernel.OpenProcess(0x1000, False, entry.th32ProcessID)
                if not handle:
                    return True
                try:
                    buffer = ctypes.create_unicode_buffer(32768)
                    size = wintypes.DWORD(len(buffer))
                    if not kernel.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(size)):
                        return True
                    if os.path.normcase(os.path.abspath(buffer.value)) == os.path.normcase(os.path.abspath(target)):
                        return True
                finally:
                    kernel.CloseHandle(handle)
            ok = kernel.Process32NextW(snapshot, ctypes.byref(entry))
    finally:
        kernel.CloseHandle(snapshot)
    return False


def _check_target(target, running):
    if target.name.casefold() != 'your painting, sir.exe' or not target.is_file():
        raise PatchError('请选择游戏目录中的 Your Painting, Sir.exe。')
    if running(target):
        raise PatchError('游戏正在运行，请先退出游戏再重试。')


def _marker(path):
    try:
        with zipfile.ZipFile(path) as z:
            if MARKER not in z.namelist():
                return None
            if z.namelist().count(MARKER) != 1:
                raise PatchError('游戏中的汉化标记异常，请先恢复原版。')
            data = z.read(MARKER)
            if len(data) > 4096:
                raise PatchError('游戏中的汉化标记异常，请先恢复原版。')
            parsed = json.loads(data.decode('utf-8'))
            if not isinstance(parsed, dict):
                raise PatchError('游戏中的汉化标记异常，请先恢复原版。')
            return parsed
    except (OSError, ValueError, zipfile.BadZipFile, KeyError):
        return None


def _temp_file(target):
    fd, path = tempfile.mkstemp(prefix='.yps-zh-', suffix='.tmp', dir=target.parent)
    os.close(fd)
    return Path(path)


def _cleanup(path):
    try:
        path.unlink()
    except FileNotFoundError:
        pass


def _ensure_backup(target, backup, expected):
    if backup.exists():
        if not backup.is_file() or _sha256(backup) != expected:
            raise PatchError('发现现有备份，但内容与当前支持的原版不一致；为保护备份，操作已停止。')
        return
    created = False
    try:
        with open(backup, 'xb') as dst:
            created = True
            with open(target, 'rb') as src:
                shutil.copyfileobj(src, dst, 1024 * 1024)
            dst.flush()
            os.fsync(dst.fileno())
        if _sha256(backup) != expected:
            raise PatchError('原版备份校验失败，未修改游戏。')
        shutil.copystat(target, backup)
    except Exception:
        if created:
            _cleanup(backup)
        raise


def _build_patched(target, temporary, bundle):
    with zipfile.ZipFile(target, 'r') as src:
        infos = src.infolist()
        names = [i.filename for i in infos]
        if len(names) != len(set(names)) or MARKER in names:
            raise PatchError('游戏资源结构异常，已停止汉化。')
        if not infos or any(n not in names for n in bundle.replacements):
            raise PatchError('未找到补丁需要的游戏资源，请确认游戏版本。')
        if any(n in names for n in bundle.additions):
            raise PatchError('补丁资源与原版资源冲突，已停止汉化。')
        prefix_length = min(i.header_offset for i in infos)
        with open(target, 'rb') as game, open(temporary, 'wb') as out:
            remaining = prefix_length
            while remaining:
                chunk = game.read(min(remaining, 1024 * 1024))
                if not chunk:
                    raise PatchError('读取游戏启动文件失败。')
                out.write(chunk)
                remaining -= len(chunk)
            with zipfile.ZipFile(out, 'w') as dst:
                for info in infos:
                    if info.filename in bundle.replacements:
                        dst.writestr(info, bundle.replacements[info.filename])
                    else:
                        with src.open(info, 'r') as reader, dst.open(info, 'w') as writer:
                            shutil.copyfileobj(reader, writer, 1024 * 1024)
                for name, data in bundle.additions.items():
                    dst.writestr(name, data, compress_type=zipfile.ZIP_DEFLATED)
                marker = {'patch_id': bundle.patch_id, 'original_sha256': bundle.original_sha256}
                dst.writestr(MARKER, json.dumps(marker, ensure_ascii=False).encode('utf-8'), compress_type=zipfile.ZIP_DEFLATED)
            out.flush()
            os.fsync(out.fileno())
    with zipfile.ZipFile(temporary, 'r') as check:
        bad = check.testzip()
        if bad:
            raise PatchError('生成的汉化文件未通过校验：' + bad)
        marker = json.loads(check.read(MARKER).decode('utf-8'))
        if marker['patch_id'] != bundle.patch_id or marker['original_sha256'] != bundle.original_sha256:
            raise PatchError('生成的汉化文件标记不正确。')
        for name, contents in {**bundle.replacements, **bundle.additions}.items():
            if check.read(name) != contents:
                raise PatchError('生成的汉化资源校验失败：' + name)


def install(target, bundle, running=game_is_running, replace=os.replace, progress=lambda *_: None):
    target = Path(target)
    try:
        _check_target(target, running)
        progress('正在检查游戏版本…')
        marker = _marker(target)
        backup = target.with_name(target.name + BACKUP_SUFFIX)
        if marker:
            if marker.get('patch_id') != bundle.patch_id or marker.get('original_sha256') != bundle.original_sha256:
                raise PatchError('检测到其他版本的汉化补丁，请先使用对应工具恢复原版。')
            if not backup.is_file() or _sha256(backup) != bundle.original_sha256:
                raise PatchError('汉化已安装，但原版备份缺失或不匹配，请先检查备份。')
            with zipfile.ZipFile(target) as z:
                if z.testzip():
                    raise PatchError('汉化文件校验失败，请使用恢复功能。')
            return 'already_installed'
        if _sha256(target) != bundle.original_sha256:
            raise PatchError('游戏版本或文件校验不匹配；此工具仅支持指定的试玩版。')
        needed = target.stat().st_size + sum(map(len, bundle.additions.values())) + 8 * 1024 * 1024
        if not backup.exists():
            needed += target.stat().st_size
        if shutil.disk_usage(target.parent).free < needed:
            raise PatchError('游戏所在磁盘剩余空间不足，无法安全备份并生成汉化文件。')
        progress('正在备份原版游戏…')
        _ensure_backup(target, backup, bundle.original_sha256)
        if running(target):
            raise PatchError('游戏已启动，请先退出游戏再重试。')
        temp = _temp_file(target)
        try:
            progress('正在生成并校验汉化文件…')
            _build_patched(target, temp, bundle)
            shutil.copystat(target, temp)
            if running(target):
                raise PatchError('游戏已启动，请先退出游戏再重试。')
            progress('正在完成安装…')
            if _sha256(target) != bundle.original_sha256:
                raise PatchError('游戏文件在汉化期间发生变化或被更新，已停止替换。')
            replace(temp, target)
        finally:
            _cleanup(temp)
        return 'installed'
    except PatchError:
        raise
    except (OSError, zipfile.BadZipFile, ValueError, RuntimeError) as exc:
        raise PatchError(_failure_message('汉化', exc)) from exc


def restore(target, bundle, running=game_is_running, replace=os.replace, progress=lambda *_: None):
    target = Path(target)
    try:
        _check_target(target, running)
        progress('正在检查游戏和备份…')
        marker = _marker(target)
        if not marker:
            if _sha256(target) == bundle.original_sha256:
                return 'already_original'
            raise PatchError('所选文件不是此工具支持的汉化版或原版；为保护文件，未执行恢复。')
        if marker.get('patch_id') != bundle.patch_id or marker.get('original_sha256') != bundle.original_sha256:
            raise PatchError('所选游戏不是此工具安装的汉化版本，未执行恢复。')
        current_sha256 = _sha256(target)
        backup = target.with_name(target.name + BACKUP_SUFFIX)
        if not backup.is_file() or _sha256(backup) != bundle.original_sha256:
            raise PatchError('原版备份不存在或校验不符，无法安全恢复。')
        if shutil.disk_usage(target.parent).free < backup.stat().st_size + 1024 * 1024:
            raise PatchError('游戏所在磁盘剩余空间不足，无法安全恢复。')
        temp = _temp_file(target)
        try:
            progress('正在恢复原版…')
            with open(backup, 'rb') as src, open(temp, 'wb') as dst:
                shutil.copyfileobj(src, dst, 1024 * 1024)
                dst.flush(); os.fsync(dst.fileno())
            if _sha256(temp) != bundle.original_sha256:
                raise PatchError('恢复文件校验失败，游戏文件未被修改。')
            shutil.copystat(backup, temp)
            if running(target):
                raise PatchError('游戏已启动，请先退出游戏再重试。')
            if _sha256(target) != current_sha256:
                raise PatchError('游戏文件在恢复期间发生变化或被更新，已停止替换。')
            replace(temp, target)
        finally:
            _cleanup(temp)
        return 'restored'
    except PatchError:
        raise
    except (OSError, zipfile.BadZipFile, ValueError, RuntimeError) as exc:
        raise PatchError(_failure_message('恢复', exc)) from exc
