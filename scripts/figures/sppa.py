from __future__ import annotations

import argparse
from pathlib import Path
from itertools import cycle

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

from style import apply_style


def _plot_timeseries(
    df: pd.DataFrame,
    category_order: list[str],
    value_column: str,
    ylabel: str,
    output_path: Path,
    hline: float | None = None,
    ylim: tuple[float, float] | None = None,
) -> None:
    df = df[df["Read in the last year"].isin(category_order)].copy()
    df["Read in the last year"] = pd.Categorical(
        df["Read in the last year"], categories=category_order, ordered=True
    )
    df = df.sort_values(["Read in the last year", "Year"])
    prop_cycle = plt.rcParams.get("axes.prop_cycle")
    style_cycle = cycle(prop_cycle) if prop_cycle is not None else None

    fig, ax = plt.subplots()
    if hline is not None:
        ax.axhline(hline, color="gray", linestyle="dashed", linewidth=1)

    for category in category_order:
        subset = df[df["Read in the last year"] == category]
        if subset.empty:
            continue
        style_kwargs = next(style_cycle) if style_cycle is not None else {}
        ax.plot(subset["Year"], subset[value_column], label=category, **style_kwargs)

    ax.set_xlabel("Year")
    ax.set_ylabel(ylabel)
    years = sorted(df["Year"].unique())
    ax.set_xticks(years)
    padding = (years[-1] - years[0]) * 0.04
    ax.set_xlim(years[0] - padding, years[-1] + padding)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    if ylim is not None:
        ax.set_ylim(*ylim)
    ax.legend(title="Type of reading", frameon=False)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    for suffix in (".png", ".svg", ".eps"):
        fig.savefig(output_path.with_suffix(suffix))
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="Plot SPPA reading rates.")
    parser.add_argument(
        "--include-magazine",
        action="store_true",
        help='Include the "Any book or magazine" series (1982, 1985 only).',
    )
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parents[2]
    data_path = project_root / "data" / "source" / "sppa.csv"
    fig_output = project_root / "figures" / "fig1.png"

    apply_style()

    df = pd.read_csv(data_path)
    df["Year"] = pd.to_datetime(df["Year"], format="%Y")

    category_order = [
        "Any book",
        "Literature",
        "Novels or short stories",
        "Poetry",
        "Plays",
    ]
    if args.include_magazine:
        category_order.insert(0, "Any book or magazine")

    _plot_timeseries(
        df=df,
        category_order=category_order,
        value_column="Percent",
        ylabel="% US adults reading in the past year",
        output_path=fig_output,
        hline=50,
        ylim=(0, 100),
    )


if __name__ == "__main__":
    main()
