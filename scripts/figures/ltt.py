from __future__ import annotations

from pathlib import Path

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd

from plotting import _setup_year_axis, plot_grouped_timeseries, save_figure
from style import apply_style

# NAEP administered the LTT reading questions in their original format through
# 2004 and in a revised format from 2008 onward; NCES cautions against
# comparing across the two.
LAST_ORIGINAL_FORMAT_YEAR = 2004


def _lighten(color: str, amount: float = 0.6) -> tuple[float, float, float]:
    """Blend a color toward white by ``amount`` (0 = unchanged, 1 = white)."""
    r, g, b = mcolors.to_rgb(color)
    return (r + (1 - r) * amount, g + (1 - g) * amount, b + (1 - b) * amount)


def plot_format_variant(df: pd.DataFrame, age_order: list, output_path: Path) -> None:
    """One line per age, split into original- and revised-format segments.

    Each age keeps one hue: the original-format points (through 2004) are a
    lightened shade, the revised-format points (2008 onward) the full color,
    with no line bridging the format change.
    """
    prop = plt.rcParams["axes.prop_cycle"].by_key()
    colors, markers = prop["color"], prop["marker"]

    df = df.copy()
    df["Year"] = pd.to_datetime(df["Year"], format="%Y")

    fig, ax = plt.subplots()
    ax.axhline(50, color="gray", linestyle="dashed", linewidth=1)

    for i, age in enumerate(age_order):
        subset = df[df["Age"] == age].sort_values("Year")
        original = subset[subset["Year"].dt.year <= LAST_ORIGINAL_FORMAT_YEAR]
        revised = subset[subset["Year"].dt.year > LAST_ORIGINAL_FORMAT_YEAR]
        ax.plot(
            original["Year"],
            original["Percent"],
            color=_lighten(colors[i]),
            marker=markers[i],
            label="_nolegend_",
        )
        ax.plot(
            revised["Year"],
            revised["Percent"],
            color=colors[i],
            marker=markers[i],
            label=str(age),
        )

    # A divider midway between the last original-format assessment (2004) and
    # the first revised-format one (2008), with one era label on each side,
    # explains the lighter/darker shades without doubling the legend.
    format_divider = pd.to_datetime("2006-01-01")
    ax.axvline(format_divider, color="gray", linestyle="dotted", linewidth=1)
    era_label_kwargs = {"y": 93, "color": "gray", "ha": "center", "va": "center"}
    ax.text(x=pd.to_datetime("1994-01-01"), s="Original format", **era_label_kwargs)
    ax.text(x=pd.to_datetime("2016-07-01"), s="Revised format", **era_label_kwargs)

    ax.set_xlabel("Year")
    ax.set_ylabel("US students reading for fun weekly or more often")
    _setup_year_axis(ax, df["Year"].min(), df["Year"].max())
    ax.set_ylim(0, 100)
    ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=100, decimals=0))
    ax.legend(title="Age", frameon=False)

    save_figure(fig, output_path)


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]
    data_path = project_root / "data" / "derived" / "ltt_or_weekly.csv"
    output_path = project_root / "figures" / "fig5.png"

    apply_style()

    df = pd.read_csv(data_path)
    age_order = sorted(df["Age"].unique())

    plot_grouped_timeseries(
        df=df,
        group_col="Age",
        group_order=age_order,
        value_column="Percent",
        ylabel="US students reading for fun weekly or more often",
        output_path=output_path,
        legend_title="Age",
        hline=50,
        ylim=(0, 100),
        percent_y=True,
    )

    # Variant with every point, but original- vs revised-format segments
    # distinguished by lightened vs full hue within each age's color.
    plot_format_variant(df, age_order, project_root / "figures" / "fig5_formats.png")

    # Variant restricted to the revised assessment format (2008 onward), so
    # no line spans NAEP's original-to-revised format change after 2004.
    plot_grouped_timeseries(
        df=df[df["Year"] >= 2008],
        group_col="Age",
        group_order=age_order,
        value_column="Percent",
        ylabel="US students reading for fun weekly or more often",
        output_path=project_root / "figures" / "fig5_2008.png",
        legend_title="Age",
        hline=50,
        ylim=(0, 100),
        percent_y=True,
    )


if __name__ == "__main__":
    main()
