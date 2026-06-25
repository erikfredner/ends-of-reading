# "The Ends of Reading"

[![DOI](https://zenodo.org/badge/1132267528.svg)](https://doi.org/10.5281/zenodo.18434695)

Code and data to support my essay, "The Ends of Reading."

## Reproduce

This project is managed with [uv](https://docs.astral.sh/uv/), which handles the Python version and dependencies for you. Install uv first (see its docs for instructions for your platform).

1. Clone this repo.
2. Review `data/README.md` for data provenance.
3. Install the pinned dependencies into a local virtual environment:

```zsh
uv sync
```

4. Regenerate every derived CSV and figure from scratch, in the correct order:

```zsh
uv run python scripts/run_all.py
```

Or regenerate a single figure by invoking its script directly:

```zsh
uv run python scripts/figures/sppa.py
```

`uv run` runs the command inside the project environment, so you don't need to activate it yourself.

## AI Statement

I gathered and verified all data and outputs manually.

I used Claude Code and OpenAI's Codex to help write code to reshape data, generate figures, and calculate values referenced in the manuscript.
