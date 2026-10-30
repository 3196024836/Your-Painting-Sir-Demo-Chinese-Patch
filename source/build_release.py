"""Build only after the actual release checklist and translations have been signed off."""
import subprocess,sys
from pathlib import Path
from app import load_resources
from patch_engine import PatchError
from release_bundle import check_release
ROOT=Path(__file__).resolve().parents[1]
profile,checks,rows,_,_,_=load_resources()
try:check_release(rows,checks)
except PatchError as e:raise SystemExit('尚不可打包正式版：'+str(e))
cmd=[sys.executable,'-m','PyInstaller','--noconfirm','--onefile','--windowed',
     '--name','YourPaintingSir汉化工具',
     '--distpath',str(ROOT/'dist'),'--workpath',str(ROOT/'qa/build-release'),
     '--specpath',str(ROOT/'qa/build-release'),
     '--add-data',str(ROOT/'data')+';data',str(ROOT/'source/app.py')]
raise SystemExit(subprocess.call(cmd,cwd=ROOT))
