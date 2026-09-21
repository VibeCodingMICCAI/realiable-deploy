#!/usr/bin/env python
import subprocess
import sys
from pathlib import Path

raise SystemExit(subprocess.run([sys.executable, "-m", "pytest"], cwd=Path(__file__).resolve().parents[1]).returncode)
