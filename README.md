# "The Ends of Reading"

Code and data to support my essay, "The Ends of Reading," which is forthcoming in *American Literature*.

- [Essay](https://doi.org/10.1215/00029831-12720407)
- [Zenodo](https://doi.org/10.5281/zenodo.18434695)

## Reproduce

### Setup

This project is managed with [`uv`](https://docs.astral.sh/uv/), which handles the Python version and dependencies for you.

- [Install `uv`](https://docs.astral.sh/uv/getting-started/installation/)
- Clone this repo.
- Install the pinned dependencies into a local virtual environment. `--locked`
  installs exactly the versions in `uv.lock` and stops if the lockfile is out of date:

```zsh
uv sync --locked
```

### Regenerate

```zsh
uv run python scripts/run_all.py
```

This rebuilds every CSV in `data/derived/` from the raw files in `data/source/`,
then the figures, then `data/derived/cited_values.txt`, which pairs each number
cited in the essay with the value recomputed from the data. The derived CSVs and
cited values are committed, so `git diff` after a run shows whether anything
changed. A GitHub Actions workflow runs the same check on every push.

Figures are written to `figures/` in PNG, SVG, and PDF formats. They are not
committed, so run the pipeline to get them. Reruns produce byte-identical files.

The published figures are set in Helvetica Now Micro, a commercial font that must be
installed locally. Without it, matplotlib falls back to Helvetica (included with
macOS), and then to its bundled DejaVu Sans, printing a "findfont" warning. The
fallbacks change only the typeface; the plotted data are the same.
`scripts/publication.py` sets the manuscript's ATUS cutoff to 2025, the latest
national observation in the repository, for Figure 2, the reading forecast, and
cited values. LTT outputs include the refreshed age-13 observation for 2023
and continue through 2025.

## License

Code is released under the [MIT License](LICENSE). The source values in
`data/source/` are statistics published by U.S. federal agencies and are in the
public domain. The compiled and derived datasets in `data/` are released under
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

## AI Statement

I gathered and verified all data, analyses, and figures manually.

I used Claude Code and OpenAI's Codex to help write code to reshape data, modify figures, and calculate values referenced in the manuscript.
