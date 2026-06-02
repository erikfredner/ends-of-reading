# "The Ends of Reading"

[![DOI](https://zenodo.org/badge/1132267528.svg)](https://doi.org/10.5281/zenodo.18434695)

Code and data to support my essay, "The Ends of Reading."

## Reproduce

1. Clone this repo.
2. Review `data/README.md` for data provenance.
3. Regenerate every derived CSV and figure from scratch, in the correct order:

```zsh
python scripts/run_all.py
```

Or regenerate a single figure by invoking its script directly:

```zsh
python scripts/figures/sppa.py
```

## AI Statement

I used OpenAI's Codex with `gpt-5.2-codex` to help write code.
