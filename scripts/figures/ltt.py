from __future__ import annotations

from itertools import cycle
import math
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

from style import apply_style


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
    for suffix in (".png", ".svg", ".eps"):
        fig.savefig(output_path.with_suffix(suffix))
    plt.close(fig)


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]
    figures_dir = project_root / "figures"

    apply_style()

    data_path = project_root / "data" / "derived" / "ltt.csv"
    output_path = figures_dir / "fig5.png"

    read_weekly = {"Almost every day", "Once or twice a week"}
    df = pd.read_csv(data_path)
    df = df[df["Read for Fun"].isin(read_weekly)]
    df = df.groupby(["Year", "Age"], as_index=False)["Percent"].sum()

    age_order = sorted(df["Age"].unique())

    plot_weekly_reading_by_age(
        df=df,
        age_order=age_order,
        value_column="Percent",
        ylabel="% US students reading for fun weekly or more often",
        output_path=output_path,
        hline=50,
        ylim=(0, 100),
    )


if __name__ == "__main__":
    main()
