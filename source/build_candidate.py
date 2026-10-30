"""Build the labelled standalone candidate without marking formal QA complete."""
import subprocess
import sys
from pathlib import Path
from app import load_resources
from release_bundle import check_translation_rows

ROOT = Path(__file__).resolve().parents[1]
_, _, rows, _, _, _ = load_resources()
check_translation_rows(rows)
out = ROOT / 'dist' / 'YourPaintingSir汉化工具-测试版.exe'
if out.exists():
    raise SystemExit('目标文件已存在；为避免覆盖已有成果，请先检查：' + str(out))
cmd = [sys.executable, '-m', 'PyInstaller', '--noconfirm', '--onefile', '--windowed',
       '--name', 'YourPaintingSir汉化工具-测试版', '--distpath', str(ROOT/'dist'),
       '--workpath', str(ROOT/'qa/build-candidate'), '--specpath', str(ROOT/'qa/build-candidate'),
       '--add-data', str(ROOT/'data') + ';data', str(ROOT/'source/app_candidate.py')]
raise SystemExit(subprocess.call(cmd, cwd=ROOT))
