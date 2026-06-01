from __future__ import annotations

from pathlib import Path
from itertools import cycle, islice
import math

from cycler import cycler
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd


def apply_style() -> None:
    default_colors = plt.rcParamsDefault["axes.prop_cycle"].by_key()["color"]
    markers = ["o", "s", "D", "^", "v", "P", "X"]
    marker_cycle = list(islice(cycle(markers), len(default_colors)))
    plt.rcParams.update(
        {
            "figure.figsize": (8, 6),
            "figure.dpi": 600,
            "font.family": "sans-serif",
            "font.sans-serif": ["Helvetica Neue"],
            "axes.prop_cycle": cycler("color", default_colors)
            + cycler("marker", marker_cycle),
        }
    )


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
    ax.legend(title=legend_title, frameon=False)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path)
    plt.close(fig)


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]
    figures_dir = project_root / "figures"

    apply_style()

    data_path = project_root / "data" / "derived" / "atus.csv"
    odds_ratio_path = project_root / "data" / "derived" / "atus_or.csv"
    atus_output = figures_dir / "atus.png"
    atus_or_output = figures_dir / "fig2.png"

    category_order = [
        "Playing games",
        "Computer use for leisure, excluding games",
        "Watching TV",
        "Socializing, relaxing, and leisure",
        "Arts and entertainment (other than sports)",
        "Reading for personal interest",
    ]
    legend_labels = {
        "Socializing, relaxing, and leisure": "Socializing",
        "Computer use for leisure, excluding games": "Computer use",
        "Reading for personal interest": "Reading",
        "Arts and entertainment (other than sports)": "Arts & entertainment",
    }

    atus_df = pd.read_csv(data_path)
    plot_activity_timeseries(
        df=atus_df,
        category_order=category_order,
        legend_labels=legend_labels,
        value_column="Percent",
        ylabel="% US adults engaging in activity on an average day",
        output_path=atus_output,
        legend_title="Activity (Abbreviated)",
        hline=None,
        ylim=(0, 100),
    )

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
        legend_labels=legend_labels,
        value_column="Odds Ratio",
        ylabel="Odds ratio relative to 2003",
        output_path=atus_or_output,
        legend_title="Activity",
        hline=1,
        ylim=ylim,
    )


if __name__ == "__main__":
    main()
