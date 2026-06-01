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


def plot_weekly_reading_by_age(
    df: pd.DataFrame,
    age_order: list[int],
    value_column: str,
    ylabel: str,
    output_path: Path,
    hline: float | None = None,
    ylim: tuple[float, float] | None = None,
) -> None:
    df = df.copy()
    df["Year"] = pd.to_datetime(df["Year"], format="%Y")
    df["Age"] = df["Age"].astype(int)
    df = df.sort_values(["Age", "Year"])

    min_year = df["Year"].min()
    max_year = df["Year"].max()
    n_years = (max_year.year - min_year.year) + 1
    step = max(1, math.ceil(n_years / 8))
    prop_cycle = plt.rcParams.get("axes.prop_cycle")
    style_cycle = cycle(prop_cycle) if prop_cycle is not None else None

    fig, ax = plt.subplots()
    if hline is not None:
        ax.axhline(hline, color="gray", linestyle="dashed", linewidth=1)
    for age in age_order:
        subset = df[df["Age"] == age]
        if subset.empty:
            continue
        style_kwargs = next(style_cycle) if style_cycle is not None else {}
        ax.plot(
            subset["Year"],
            subset[value_column],
            label=f"{age}",
            **style_kwargs,
        )

    ax.set_xlabel("Year")
    ax.set_ylabel(ylabel)
    padding = (max_year - min_year) * 0.04
    ax.set_xlim(min_year - padding, max_year + padding)
    ax.xaxis.set_major_locator(mdates.YearLocator(base=step))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    if ylim is not None:
        ax.set_ylim(*ylim)
    ax.legend(title="Age", frameon=False)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path)
    plt.close(fig)


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]
    figures_dir = project_root / "figures"

    apply_style()

    data_path = project_root / "data" / "derived" / "ltt.csv"
    odds_ratio_path = project_root / "data" / "derived" / "ltt_or_weekly.csv"
    output_path = figures_dir / "fig5.png"
    odds_ratio_output = figures_dir / "fig5_or.png"

    read_weekly = {"Almost every day", "Once or twice a week"}
    df = pd.read_csv(data_path)
    df = df[df["Read for Fun"].isin(read_weekly)]
    df = df.groupby(["Year", "Age"], as_index=False)["Percent"].sum()

    age_order = sorted(df["Age"].unique())

    plot_weekly_reading_by_age(
        df=df,
        age_order=age_order,
        value_column="Percent",
        ylabel="% US students reading weekly or more often",
        output_path=output_path,
        hline=50,
        ylim=(0, 100),
    )

    or_df = pd.read_csv(odds_ratio_path)
    odds_ratio_series = or_df["Odds Ratio"]
    or_padding = (odds_ratio_series.max() - odds_ratio_series.min()) * 0.05
    or_ylim = (
        max(0, odds_ratio_series.min() - or_padding),
        odds_ratio_series.max() + or_padding,
    )

    plot_weekly_reading_by_age(
        df=or_df,
        age_order=age_order,
        value_column="Odds Ratio",
        ylabel="Odds ratio relative to 1984",
        output_path=odds_ratio_output,
        hline=1,
        ylim=or_ylim,
    )


if __name__ == "__main__":
    main()
