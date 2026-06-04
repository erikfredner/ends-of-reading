# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Reproducibility code and data for the essay "The Ends of Reading." All outputs (tidy CSVs and figures) are regenerated from raw source files by small, self-contained Python scripts. There is no application and no CLI — every script is invoked as `python <path>` and writes a file next to itself or in a sibling directory. There is a small pytest suite under `tests/` that checks the odds-ratio derivations.

## Environment

- Python 3.14, managed with `uv` (see `pyproject.toml`, `uv.lock`). Runtime deps: `pandas`, `matplotlib` (figure scripts also use `numpy` and `cycler`, both pulled in transitively). Dev dep: `pytest`.
- `uv sync` to install. Run scripts as `uv run python <path>` or `python <path>` inside the venv. Run tests as `uv run pytest`.
- Figure styling prefers Helvetica Now Micro and falls back to Helvetica (both macOS-friendly).

## Pipeline architecture

The repo is a multi-stage pipeline with scripts separated from data. Understand the stages before editing — naming follows them strictly. `scripts/run_all.py` is the canonical orchestrator and is the source of truth for stage membership and ordering; if you add a new pipeline script, register it there too.

Layout: `scripts/data/*.py` and `scripts/figures/*.py` hold all pipeline code; `data/source/` is raw inputs, `data/derived/` is tidy CSVs, `figures/` is rendered outputs. Every script computes `project_root = Path(__file__).resolve().parents[2]` (or `parents[1]` for the top-level orchestrator and `cited_values.py`) and addresses inputs/outputs from there — preserve that pattern when adding new scripts.

**Stage 1 — `data/source/` → `data/derived/*.csv`.** Each script in `scripts/data/` whose name does not end in `_or` (or `_or_similarity`) reads raw file(s) under `data/source/` and writes a tidy CSV to `data/derived/`. Mapping is by filename: `scripts/data/atus.py` reads every CSV under `data/source/atus/` (filenames encode `<series_id> - <activity>`) and writes `data/derived/atus.csv`; `scripts/data/ltt_extract.py` reads `data/source/ltt/<age>.txt` files (raw NAEP tab-delimited dumps) and writes `data/derived/ltt.csv`; `scripts/data/atus_ed.py` reads `data/source/atus_ed.csv`. SPPA has no stage-1 script: `data/source/sppa.csv` is already tidy and is consumed directly by `scripts/figures/sppa.py`.

**Stage 2 — `data/derived/*.csv` → `data/derived/*_or.csv` (odds-ratio + similarity variants).** Scripts ending in `_or.py` consume a stage-1 CSV and emit an odds-ratio version using `compute_odds()` from `scripts/data/odds.py`. The import is bare (`from odds import compute_odds`) and works because Python puts the script's own directory on `sys.path`; run these as `python scripts/data/<name>_or.py`, not as a module. The odds ratio for each category is computed against that category's earliest available year (the baseline). Further derivations layered on top:
- `scripts/data/ltt_or_weekly.py` sums "Almost every day" + "Once or twice a week" before computing odds ratios.
- `scripts/data/atus_ed_or_similarity.py` reads `atus_ed_or.csv` and writes three similarity CSVs (`atus_ed_or_similarity_pairwise.csv`, `_slopes.csv`, `_spread.csv`) summarizing how the four education-level trajectories converge or diverge.

**Stage 3 — tidy CSVs → `figures/*.{png,svg,eps}`.** Scripts in `scripts/figures/` read tidy CSVs (from `data/derived/`, except `sppa.py` which reads `data/source/sppa.csv` directly) and write figures to `figures/`. Each figure script saves three formats by iterating `for suffix in (".png", ".svg", ".eps"): fig.savefig(output_path.with_suffix(suffix))` — preserve that idiom when adding new figure scripts. The published figure mapping:

| Script | Output(s) |
| --- | --- |
| `scripts/figures/sppa.py` | `figures/fig1.{png,svg,eps}` |
| `scripts/figures/atus.py` | `figures/fig2.*` (odds ratio) |
| `scripts/figures/atus_fit.py` | `figures/fig2_fit.*` (linear-fit overlay variant of fig2) |
| `scripts/figures/atus_ed.py` | `figures/fig3.*`, `figures/fig4.*` (odds ratio, by education) |
| `scripts/figures/atus_ed_fit.py` | `figures/fig4_fit.*` (linear-fit overlay variant of fig4) |
| `scripts/figures/ltt.py` | `figures/fig5.*` |
| `scripts/figures/atus_prediction.py` | `figures/atus_prediction.*` (linear fit + 95% CI + year-crosses-10% annotation) |

**Stage 4 — manuscript spot-check.** `scripts/cited_values.py` recomputes every numeric claim cited in the essay from the latest CSVs and prints `Sentence: …` / `Computed: …` pairs. It reads from both `data/derived/` (tidy + odds-ratio CSVs) and `data/source/atus/` (for average-hours BLS series that are not part of the tidy pipeline). Run it after touching any data script to confirm the manuscript numbers still hold.

To regenerate everything from scratch, just run `python scripts/run_all.py` — it invokes each script in dependency order as its own subprocess (required because the `_or.py` scripts depend on `sys.path` containing their own directory for the bare `from odds import …` import). To update a single figure you only need to run that figure's script if its upstream CSV hasn't changed.

## Tests

`tests/` is a pytest suite that validates the stage-2 odds-ratio outputs. `tests/conftest.py` prepends `scripts/data` and `scripts/figures` to `sys.path` so the bare-import convention used by pipeline scripts also works inside tests, and exports `DERIVED = project_root / "data" / "derived"` for the test files to use. Tests that need a derived CSV `pytest.skip(...)` when the file is missing, so it is safe to run `uv run pytest` before the pipeline has produced everything — but a green run only proves what was checked. Run the relevant `scripts/data/*.py` first if you want full coverage.

## Conventions

- **Percentages are stored as `1.6` meaning 1.6%**, matching how the source agencies (NEA/SPPA, BLS/ATUS, NAEP/LTT) publish them.
- **Blank cells in tidy CSVs represent data not collected**, not zero. Scripts skip empty values rather than imputing.
- **Odds-ratio scripts baseline each category to its own earliest year**, not to a global year. Two categories with different first-observed years will have ratio = 1 in different years. The figure y-axis labels currently say "relative to 2003" / "relative to 2004" — if you change the underlying data and a category's first year shifts, update the label too.
- **Figure styling lives in `scripts/figures/style.py`** as a single `apply_style()` (8×6 inches at 600 dpi, Helvetica Now Micro falling back to Helvetica, combined color+marker cycle using the Okabe-Ito colorblind-safe palette). Each figure script imports it as `from style import apply_style` — the bare import works because Python prepends the script's directory to `sys.path`, same as `scripts/data/odds.py`.
- The `_category_order` / `_edu_order` keys you'll see in `scripts/data/*_or.py` are internal sort-stability helpers — they're popped before writing the output CSV.

## AI usage note

The README states the author used OpenAI Codex (`gpt-5.2-codex`) to help write code. Match the existing style (stdlib `csv` for data scripts, pandas only in figure scripts, type hints, `from __future__ import annotations` in figure scripts) when adding new pipeline pieces.
