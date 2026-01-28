from __future__ import annotations

from pathlib import Path
from itertools import cycle, islice

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


def main() -> None:
    figures_dir = Path(__file__).resolve().parent
    project_root = figures_dir.parent
    data_path = project_root / "data" / "sppa.csv"
    output_path = figures_dir / "fig1.png"

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

    df = df[df["Read in the last year"].isin(category_order)].copy()
    df["Read in the last year"] = pd.Categorical(
        df["Read in the last year"], categories=category_order, ordered=True
    )
    df = df.sort_values(["Read in the last year", "Year"])
    prop_cycle = plt.rcParams.get("axes.prop_cycle")
    style_cycle = cycle(prop_cycle) if prop_cycle is not None else None

    fig, ax = plt.subplots()

    ax.axhline(50, color="gray", linestyle="dashed", linewidth=1)

    for category in category_order:
        subset = df[df["Read in the last year"] == category]
        if subset.empty:
            continue
        style_kwargs = next(style_cycle) if style_cycle is not None else {}
        ax.plot(subset["Year"], subset["Percent"], label=category, **style_kwargs)

    ax.set_xlabel("Year")
    ax.set_ylabel("% US adults reading in the past year")
    ax.set_xticks(sorted(df["Year"].unique()))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.set_ylim(0, 100)
    ax.legend(title="Type of reading", frameon=False)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path)
    plt.close(fig)


if __name__ == "__main__":
    main()
