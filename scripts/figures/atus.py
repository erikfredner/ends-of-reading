from __future__ import annotations

from pathlib import Path
from itertools import cycle
import math

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

from style import apply_style


def plot_activity_timeseries(
    df: pd.DataFrame,
    category_order: list[str],
    legend_labels: dict[str, str],
    value_column: str,
    ylabel: str,
    output_path: Path,
    legend_title: str,
    hline: float | None = None,
    ylim: tuple[float, float] | None = None,
    legend_below: bool = False,
) -> None:
    df = df[df["Activity"].isin(category_order)].copy()
    df["Year"] = pd.to_datetime(df["Year"], format="%Y")
    min_year = df["Year"].min()
    max_year = df["Year"].max()
    n_years = (max_year.year - min_year.year) + 1
    step = max(1, math.ceil(n_years / 8))
    df["Activity"] = pd.Categorical(df["Activity"], categories=category_order, ordered=True)
    df = df.sort_values(["Activity", "Year"])
    prop_cycle = plt.rcParams.get("axes.prop_cycle")
    style_cycle = cycle(prop_cycle) if prop_cycle is not None else None

    fig, ax = plt.subplots()
    if hline is not None:
        ax.axhline(hline, color="gray", linestyle="dashed", linewidth=1)

    for category in category_order:
        subset = df[df["Activity"] == category]
        if subset.empty:
            continue
        full_years = pd.date_range(
            start=subset["Year"].min(), end=subset["Year"].max(), freq="YS"
        )
        subset = subset.set_index("Year").reindex(full_years)
        style_kwargs = next(style_cycle) if style_cycle is not None else {}
        label = legend_labels.get(category, category)
        ax.plot(subset.index, subset[value_column], label=label, **style_kwargs)

    ax.set_xlabel("Year")
    ax.set_ylabel(ylabel)
    padding = (max_year - min_year) * 0.04
    ax.set_xlim(min_year - padding, max_year + padding)
    ax.xaxis.set_major_locator(mdates.YearLocator(base=step))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    if ylim is not None:
        ax.set_ylim(*ylim)
    if legend_below:
        ax.legend(
            title=legend_title,
            frameon=False,
            loc="upper center",
            bbox_to_anchor=(0.5, -0.14),
            ncol=2,
        )
        fig.subplots_adjust(bottom=0.30)
    else:
        ax.legend(title=legend_title, frameon=False)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    for suffix in (".png", ".svg", ".eps"):
        fig.savefig(output_path.with_suffix(suffix))
    plt.close(fig)


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]
    figures_dir = project_root / "figures"

    apply_style()

    odds_ratio_path = project_root / "data" / "derived" / "atus_or.csv"
    atus_or_output = figures_dir / "fig2.png"

    category_order = [
        "Playing games",
        "Computer use for leisure, excluding games",
        "Watching TV",
        "Socializing, relaxing, and leisure",
        "Arts and entertainment (other than sports)",
        "Reading for personal interest",
    ]
    atus_or_df = pd.read_csv(odds_ratio_path)
    odds_ratio_series = atus_or_df["Odds Ratio"]
    padding = (odds_ratio_series.max() - odds_ratio_series.min()) * 0.05
    ylim = (
        max(0, odds_ratio_series.min() - padding),
        odds_ratio_series.max() + padding,
    )

    plot_activity_timeseries(
        df=atus_or_df,
        category_order=category_order,
        legend_labels={},
        value_column="Odds Ratio",
        ylabel="Odds ratio for participation relative to 2003",
        output_path=atus_or_output,
        legend_title="Activity",
        hline=1,
        ylim=ylim,
        legend_below=True,
    )


if __name__ == "__main__":
    main()
