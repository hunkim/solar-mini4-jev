"""Vercel Python entrypoint — System One FastAPI app (BYOK)."""
import sys
from pathlib import Path

# Ensure repo root is importable on Vercel
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server import app  # noqa: E402, F401
