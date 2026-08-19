# "The Ends of Reading"

Code and data to support my essay, "The Ends of Reading," which is forthcoming in *American Literature*.

- [Essay](https://doi.org/10.1215/00029831-12720407)
- [Zenodo](https://doi.org/10.5281/zenodo.18434695)

## Reproduce

### Setup

This project is managed with [`uv`](https://docs.astral.sh/uv/), which handles the Python version and dependencies for you.

- [Install `uv`](https://docs.astral.sh/uv/getting-started/installation/)
- Clone this repo.
- Install the pinned dependencies into a local virtual environment:

```zsh
uv sync
```

### Regenerate

```zsh
uv run python scripts/run_all.py
```

## AI Statement

I gathered and verified all data, analyses, and figures manually.

I used Claude Code and OpenAI's Codex to help write code to reshape data, modify figures, and calculate values referenced in the manuscript.
