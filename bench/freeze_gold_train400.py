#!/usr/bin/env python3
import subprocess, sys
from pathlib import Path
BENCH = Path(__file__).resolve().parent
sys.exit(subprocess.call([
    sys.executable, str(BENCH / "freeze_gold_split.py"),
    "--cases", str(BENCH / "cases_train400.json"),
    "--out", str(BENCH / "gold_jev_train400.json"),
]))
