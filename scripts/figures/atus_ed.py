from __future__ import annotations

from itertools import cycle, islice
import math
from pathlib import Path

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


def plot_education_timeseries(
    df: pd.DataFrame,
    education_order: list[str],
    legend_labels: dict[str, str],
    value_column: str,
    ylabel: str,
    output_path: Path,
    legend_title: str,
    hline: float | None = None,
    ylim: tuple[float, float] | None = None,
) -> None:
    df = df[df["Educational Attainment"].isin(education_order)].copy()
    df["Year"] = pd.to_datetime(df["Year"], format="%Y")
    min_year = df["Year"].min()
    max_year = df["Year"].max()
    n_years = (max_year.year - min_year.year) + 1
    step = max(1, math.ceil(n_years / 8))
    df["Educational Attainment"] = pd.Categorical(
        df["Educational Attainment"], categories=education_order, ordered=True
    )
    df = df.sort_values(["Educational Attainment", "Year"])
    prop_cycle = plt.rcParams.get("axes.prop_cycle")
    style_cycle = cycle(prop_cycle) if prop_cycle is not None else None

    fig, ax = plt.subplots()
    if hline is not None:
        ax.axhline(hline, color="gray", linestyle="dashed", linewidth=1)

    for category in education_order:
        subset = df[df["Educational Attainment"] == category]
        if subset.empty:
            continue
        style_kwargs = next(style_cycle) if style_cycle is not None else {}
        label = legend_labels.get(category, category)
        ax.plot(subset["Year"], subset[value_column], label=label, **style_kwargs)

    ax.set_xlabel("Year")
    ax.set_ylabel(ylabel)
    ax.set_xlim(min_year, max_year)
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

    data_path = project_root / "data" / "derived" / "atus_ed.csv"
    odds_ratio_path = project_root / "data" / "derived" / "atus_ed_or.csv"
    atus_output = figures_dir / "fig3.png"
    atus_or_output = figures_dir / "fig4.png"

    education_order = [
        "Bachelor's degree and higher",
        "Some college or associate degree",
        "High school graduates (no college)",
        "Less than a high school diploma",
    ]
    legend_labels = {}
    activity = "Reading for personal interest"

    atus_ed_df = pd.read_csv(data_path)
    atus_ed_df = atus_ed_df[atus_ed_df["Activity"] == activity].copy()
    plot_education_timeseries(
        df=atus_ed_df,
        education_order=education_order,
        legend_labels=legend_labels,
        value_column="Percent",
        ylabel="% US adults reading for personal interest on an average day",
        output_path=atus_output,
        legend_title="Education",
        hline=50,
        ylim=(0, 100),
    )

    atus_ed_or_df = pd.read_csv(odds_ratio_path)
    atus_ed_or_df = atus_ed_or_df[atus_ed_or_df["Activity"] == activity].copy()
    ylim = (0, 1.1)

    plot_education_timeseries(
        df=atus_ed_or_df,
        education_order=education_order,
        legend_labels=legend_labels,
        value_column="Odds Ratio",
        ylabel="Reading for personal interest odds ratio relative to 2004",
        output_path=atus_or_output,
        legend_title="Education",
        hline=1,
        ylim=ylim,
    )


if __name__ == "__main__":
    main()
