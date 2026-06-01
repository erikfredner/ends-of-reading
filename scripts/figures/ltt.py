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
    read_weekly: set[str],
    output_path: Path,
) -> None:
    df = df[df["Read for Fun"].isin(read_weekly)].copy()
    df["Year"] = pd.to_datetime(df["Year"], format="%Y")
    df["Age"] = df["Age"].astype(int)
    df = (
        df.groupby(["Year", "Age"], as_index=False)["Percent"]
        .sum()
        .sort_values(["Age", "Year"])
    )

    min_year = df["Year"].min()
    max_year = df["Year"].max()
    n_years = (max_year.year - min_year.year) + 1
    step = max(1, math.ceil(n_years / 8))
    prop_cycle = plt.rcParams.get("axes.prop_cycle")
    style_cycle = cycle(prop_cycle) if prop_cycle is not None else None

    fig, ax = plt.subplots()
    ax.axhline(50, color="gray", linestyle="dashed", linewidth=1)
    for age in age_order:
        subset = df[df["Age"] == age]
        if subset.empty:
            continue
        style_kwargs = next(style_cycle) if style_cycle is not None else {}
        ax.plot(
            subset["Year"],
            subset["Percent"],
            label=f"{age}",
            **style_kwargs,
        )

    ax.set_xlabel("Year")
    ax.set_ylabel("% US students reading weekly or more often")
    ax.set_xlim(min_year, max_year)
    ax.xaxis.set_major_locator(mdates.YearLocator(base=step))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.set_ylim(0, 100)
    ax.legend(title="Age", frameon=False)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path)
    plt.close(fig)


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]

    apply_style()

    data_path = project_root / "data" / "derived" / "ltt.csv"
    output_path = project_root / "figures" / "fig5.png"

    df = pd.read_csv(data_path)

    age_order = sorted(df["Age"].unique())
    read_weekly = {"Almost every day", "Once or twice a week"}

    plot_weekly_reading_by_age(
        df=df,
        age_order=age_order,
        read_weekly=read_weekly,
        output_path=output_path,
    )


if __name__ == "__main__":
    main()
