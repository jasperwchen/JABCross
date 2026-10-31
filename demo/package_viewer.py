"""Build and copy only public viewer assets into the isolated Sites checkout."""
from pathlib import Path
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
DEST = HERE.parent / 'sites/gsmst-viewer/dist'
subprocess.run([sys.executable, str(HERE / 'build_viewer.py')], check=True)
DEST.mkdir(parents=True, exist_ok=True)
for name in ['index.html', 'app.js', 'style.css', 'grady-ground.svg']:
    shutil.copy2(HERE / name, DEST / name)
for name in ['vendor', 'maps']:
    shutil.copytree(HERE / name, DEST / name, dirs_exist_ok=True)
print('Prepared public viewer assets in sites/gsmst-viewer/dist')
