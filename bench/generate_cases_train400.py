#!/usr/bin/env python3
"""Wrapper: generate both train400 and test400 via shared generator."""
import runpy
from pathlib import Path
runpy.run_path(str(Path(__file__).resolve().parent / "generate_cases_train_test400.py"), run_name="__main__")
