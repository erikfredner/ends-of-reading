"""Regenerate every derived CSV and figure from raw sources.

Run as ``python scripts/run_all.py``. Each pipeline script is invoked as its
own subprocess in the order required by the dependency graph: stage-1 tidy
CSVs, then stage-2 odds-ratio (and similarity) derivations, then figures,
then ``cited_values.py`` as a manuscript spot-check.

Subprocess invocation (rather than import) is required because the
``_or.py`` scripts use a bare ``from odds import compute_odds`` that only
resolves when Python puts the script's own directory on ``sys.path``.
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

STAGE_1 = [
    "scripts/data/atus.py",
    "scripts/data/atus_ed.py",
    "scripts/data/ltt_extract.py",
]

STAGE_2 = [
    "scripts/data/atus_or.py",
    "scripts/data/atus_ed_or.py",
    "scripts/data/ltt_or.py",
    "scripts/data/ltt_or_weekly.py",
    "scripts/data/atus_ed_or_similarity.py",
]

STAGE_3 = [
    "scripts/figures/sppa.py",
    "scripts/figures/atus.py",
    "scripts/figures/atus_ed.py",
    "scripts/figures/ltt.py",
    "scripts/figures/atus_prediction.py",
]

STAGE_4 = [
    "scripts/cited_values.py",
]

STAGES: list[tuple[str, list[str]]] = [
    ("Stage 1 — raw source → tidy CSV", STAGE_1),
    ("Stage 2 — tidy CSV → odds-ratio + similarity CSVs", STAGE_2),
    ("Stage 3 — figures", STAGE_3),
    ("Stage 4 — manuscript spot-check", STAGE_4),
]


def run_script(rel_path: str, index: int, total: int) -> None:
    script_path = PROJECT_ROOT / rel_path
    print(f"[{index}/{total}] {rel_path}")
    start = time.perf_counter()
    subprocess.run([sys.executable, str(script_path)], check=True)
    elapsed = time.perf_counter() - start
    print(f"    done in {elapsed:.1f}s")


def main() -> None:
    total = sum(len(scripts) for _, scripts in STAGES)
    index = 0
    for title, scripts in STAGES:
        print(f"\n=== {title} ===")
        for rel_path in scripts:
            index += 1
            run_script(rel_path, index, total)


if __name__ == "__main__":
    main()
