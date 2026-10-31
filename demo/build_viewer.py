"""Build both selectable viewer maps without changing the phone server's active map."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
for venue, flags in [('hospital', ['--hospital']), ('cafe', [])]:
    subprocess.run([sys.executable, str(ROOT / 'build_model.py'), *flags,
                    '--output-dir', str(ROOT / 'maps' / venue)], check=True)
