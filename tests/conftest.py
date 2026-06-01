import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DERIVED = PROJECT_ROOT / "data" / "derived"

for subdir in ("scripts/data", "scripts/figures"):
    path = str(PROJECT_ROOT / subdir)
    if path not in sys.path:
        sys.path.insert(0, path)
