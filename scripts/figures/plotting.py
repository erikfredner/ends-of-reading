"""Shared plotting helpers for the figure scripts.

Imported bare (``from plotting import …``), same convention as ``style.py``.
"""
from __future__ import annotations

from itertools import cycle
import math
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd


def save_figure(fig, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    for suffix in (".png", ".svg", ".eps", ".pdf"):
        fig.savefig(output_path.with_suffix(suffix))
    plt.close(fig)


def latest_value_order(df: pd.DataFrame, group_col: str, value_column: str) -> list:
    """Groups sorted by their latest-year value, descending (legend order)."""
    latest = (
        df.dropna(subset=[value_column])
        .sort_values("Year")
        .groupby(group_col)[value_column]
        .last()
    )
    return latest.sort_values(ascending=False).index.tolist()


def _setup_year_axis(ax, min_year: pd.Timestamp, max_year: pd.Timestamp) -> None:
    padding = (max_year - min_year) * 0.04
    ax.set_xlim(min_year - padding, max_year + padding)
    n_years = (max_year.year - min_year.year) + 1
    ax.xaxis.set_major_locator(mdates.YearLocator(base=max(1, math.ceil(n_years / 8))))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))


def _finish_legend(fig, ax, legend_title: str, legend_below: bool) -> None:
    kwargs = {"title": legend_title, "frameon": False}
    if legend_below:
        ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.14), ncol=2, **kwargs)
        fig.subplots_adjust(bottom=0.30)
    else:
        ax.legend(**kwargs)


def plot_grouped_timeseries(
    df: pd.DataFrame,
    group_col: str,
    group_order: list,
    value_column: str,
    ylabel: str,
    output_path: Path,
    legend_title: str,
    legend_labels: dict | None = None,
    hline: float | None = None,
    ylim: tuple[float, float] | None = None,
    legend_below: bool = False,
    fill_year_gaps: bool = False,
    tick_every_year: bool = False,
) -> None:
    """One line per group over time.

    ``fill_year_gaps`` reindexes each group to every calendar year so missing
    years (e.g. ATUS 2020) render as gaps instead of being bridged.
    ``tick_every_year`` puts a tick at every observed year (for sparse,
    irregular surveys like the SPPA) instead of an evenly stepped locator.
    """
    legend_labels = legend_labels or {}
    df = df[df[group_col].isin(group_order)].copy()
    df["Year"] = pd.to_datetime(df["Year"], format="%Y")
    min_year = df["Year"].min()
    max_year = df["Year"].max()
    style_cycle = cycle(plt.rcParams["axes.prop_cycle"])

    fig, ax = plt.subplots()
    if hline is not None:
        ax.axhline(hline, color="gray", linestyle="dashed", linewidth=1)

    for group in group_order:
        subset = df[df[group_col] == group].sort_values("Year")
        if subset.empty:
            continue
        if fill_year_gaps:
            full_years = pd.date_range(
                start=subset["Year"].min(), end=subset["Year"].max(), freq="YS"
            )
            subset = subset.set_index("Year").reindex(full_years)
            x = subset.index
        else:
            x = subset["Year"]
        label = str(legend_labels.get(group, group))
        ax.plot(x, subset[value_column], label=label, **next(style_cycle))

    ax.set_xlabel("Year")
    ax.set_ylabel(ylabel)
    _setup_year_axis(ax, min_year, max_year)
    if tick_every_year:
        ax.set_xticks(sorted(df["Year"].unique()))
    if ylim is not None:
        ax.set_ylim(*ylim)
    _finish_legend(fig, ax, legend_title, legend_below)

    save_figure(fig, output_path)
