# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Reproducibility code and data for the essay "The Ends of Reading." All outputs (tidy CSVs and figures) are regenerated from raw source files by small, self-contained Python scripts. There is no application, no tests, and no CLI — every script is invoked as `python <path>` and writes a file next to itself or in a sibling directory.

## Environment

- Python 3.14, managed with `uv` (see `pyproject.toml`, `uv.lock`). Dependencies: `pandas`, `matplotlib` (figure scripts also import `cycler` and `numpy` transitively via matplotlib/pandas).
- `uv sync` to install. Run scripts as `uv run python <path>` or `python <path>` inside the venv.
- Figure styling assumes the Helvetica Neue font is available (macOS-friendly default).

## Pipeline architecture

The repo is a two-stage pipeline with scripts separated from data. Understand the stages before editing — naming follows them strictly.

Layout: `scripts/data/*.py` and `scripts/figures/*.py` hold all code; `data/source/` is raw inputs, `data/derived/` is tidy CSVs, `figures/` is PNG outputs. Every script computes `project_root = Path(__file__).resolve().parents[2]` and addresses inputs/outputs from there — preserve that pattern when adding new scripts.

**Stage 1 — `data/source/` → `data/derived/*.csv`.** Each script in `scripts/data/` (excluding the `_or` variants) reads raw file(s) under `data/source/` and writes a tidy CSV to `data/derived/`. Mapping is by filename: `scripts/data/atus.py` reads every CSV under `data/source/atus/` (filenames encode `<series_id> - <activity>`) and writes `data/derived/atus.csv`; `scripts/data/ltt.py` reads `data/source/ltt/<age>.csv` files; `scripts/data/atus_ed.py` reads `data/source/atus_ed.csv`. SPPA has no stage-1 script: `data/source/sppa.csv` is already tidy and is consumed directly by `scripts/figures/sppa.py`.

**Stage 2 — `data/derived/*.csv` → `data/derived/*_or.csv` (odds-ratio variants).** Scripts ending in `_or.py` consume a stage-1 CSV and emit an odds-ratio version, using `compute_odds()` from `scripts/data/odds.py`. The import is bare (`from odds import compute_odds`) and works because Python puts the script's directory on `sys.path`; run these as `python scripts/data/<name>_or.py`, not as a module. The odds ratio for each category is computed against that category's earliest available year (the baseline). `scripts/data/ltt_or_weekly.py` is a further derivation that first sums "Almost every day" + "Once or twice a week" before computing odds ratios.

**Stage 3 — tidy CSVs → `figures/*.png`.** Scripts in `scripts/figures/` read tidy CSVs (from `data/derived/`, except `sppa.py` which reads `data/source/sppa.csv` directly) and write PNGs to `figures/`. The published figure mapping is:

| Script | Output(s) |
| --- | --- |
| `scripts/figures/sppa.py` | `figures/fig1.png` |
| `scripts/figures/atus.py` | `figures/fig2.png` (odds ratio) |
| `scripts/figures/atus_ed.py` | `figures/fig3.png`, `figures/fig4.png` (odds ratio) |
| `scripts/figures/ltt.py` | `figures/fig5.png` |
| `scripts/figures/atus_prediction.py` | `figures/atus_prediction.png` (linear fit + 95% CI + year-crosses-10% annotation) |

To regenerate everything from scratch: re-run every `scripts/data/*.py` (base CSVs first, then `_or` variants), then every `scripts/figures/*.py`. To update a single figure you only need to run that figure's script if its upstream CSV hasn't changed.

## Conventions

- **Percentages are stored as `1.6` meaning 1.6%**, matching how the source agencies (NEA/SPPA, BLS/ATUS, NAEP/LTT) publish them.
- **Blank cells in tidy CSVs represent data not collected**, not zero. Scripts skip empty values rather than imputing.
- **Odds-ratio scripts baseline each category to its own earliest year**, not to a global year. Two categories with different first-observed years will have ratio = 1 in different years. The figure y-axis labels currently say "relative to 2003" / "relative to 2004" — if you change the underlying data and a category's first year shifts, update the label too.
- **Each figure script defines its own `apply_style()`** that sets 8x6 inches at 600 dpi, Helvetica Neue, and a combined color+marker cycle. They're duplicated rather than shared; if you change the style, change it in every figure script.
- The `_category_order` / `_edu_order` keys you'll see in `data/*_or.py` are internal sort-stability helpers — they're popped before writing the output CSV.

## AI usage note

The README states the author used OpenAI Codex (`gpt-5.2-codex`) to help write code. Match the existing style (stdlib `csv` for data scripts, pandas only in figure scripts, type hints, `from __future__ import annotations` in figure scripts) when adding new pipeline pieces.
