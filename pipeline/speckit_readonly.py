"""Run upstream prerequisite checks without persisting the selected feature."""
import os
from pathlib import Path
import subprocess
import sys

def main():
    root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env['SPECIFY_FEATURE_NO_PERSIST'] = '1'
    return subprocess.call([
        sys.executable,
        str(root / '.specify/scripts/python/check_prerequisites.py'),
        *sys.argv[1:],
    ], cwd=root, env=env)

if __name__ == '__main__':
    raise SystemExit(main())
