from __future__ import annotations

from itertools import cycle
import math
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D

from style import apply_style


def fit_line(years: np.ndarray, values: np.ndarray) -> tuple[float, float]:
    x = years.astype(float)
    y = values.astype(float)
    x_mean = float(np.mean(x))
    y_mean = float(np.mean(y))
    sxx = float(np.sum((x - x_mean) ** 2))
    sxy = float(np.sum((x - x_mean) * (y - y_mean)))
    slope = sxy / sxx
    intercept = y_mean - slope * x_mean
    return slope, intercept


def plot_activity_fits(
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
    df = df.dropna(subset=[value_column])
    min_year = int(df["Year"].min())
    max_year = int(df["Year"].max())
    n_years = (max_year - min_year) + 1
    step = max(1, math.ceil(n_years / 8))
    prop_cycle = plt.rcParams.get("axes.prop_cycle")
    style_cycle = cycle(prop_cycle) if prop_cycle is not None else None

    fig, ax = plt.subplots()
    if hline is not None:
        ax.axhline(hline, color="gray", linestyle="dashed", linewidth=1)

    handles: list[Line2D] = []
    for category in category_order:
        subset = df[df["Activity"] == category].sort_values("Year")
        if subset.empty:
            continue
        style_kwargs = next(style_cycle) if style_cycle is not None else {}
        color = style_kwargs.get("color")
        marker = style_kwargs.get("marker", "o")
        years = subset["Year"].to_numpy()
        values = subset[value_column].to_numpy()
        slope, intercept = fit_line(years, values)
        fit_x = np.array([years.min(), years.max()])
        fit_y = intercept + slope * fit_x
        ax.scatter(
            pd.to_datetime(years, format="%Y"),
            values,
            color=color,
            marker=marker,
            zorder=3,
        )
        ax.plot(
            pd.to_datetime(fit_x, format="%Y"),
            fit_y,
            color=color,
            marker="",
            linewidth=1.5,
        )
        label = legend_labels.get(category, category)
        handles.append(Line2D([0], [0], color=color, marker=marker, label=label))

    ax.set_xlabel("Year")
    ax.set_ylabel(ylabel)
    min_year_ts = pd.to_datetime(min_year, format="%Y")
    max_year_ts = pd.to_datetime(max_year, format="%Y")
    padding = (max_year_ts - min_year_ts) * 0.04
    ax.set_xlim(min_year_ts - padding, max_year_ts + padding)
    ax.xaxis.set_major_locator(mdates.YearLocator(base=step))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    if ylim is not None:
        ax.set_ylim(*ylim)
    if legend_below:
        ax.legend(
            handles=handles,
            title=legend_title,
            frameon=False,
            loc="upper center",
            bbox_to_anchor=(0.5, -0.14),
            ncol=2,
        )
        fig.subplots_adjust(bottom=0.30)
    else:
        ax.legend(handles=handles, title=legend_title, frameon=False)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    for suffix in (".png", ".svg", ".eps"):
        fig.savefig(output_path.with_suffix(suffix))
    plt.close(fig)


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]
    figures_dir = project_root / "figures"

    apply_style()

    odds_ratio_path = project_root / "data" / "derived" / "atus_or.csv"
    output_path = figures_dir / "fig2_fit.png"

    category_order = [
        "Playing games",
        "Computer use for leisure, excluding games",
        "Watching TV",
        "Relaxing and thinking",
        "Socializing and communicating (except social events)",
        "Attending or hosting social events",
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

    plot_activity_fits(
        df=atus_or_df,
        category_order=category_order,
        legend_labels={
            "Socializing and communicating (except social events)": "Socializing & communicating (not events)",
        },
        value_column="Odds Ratio",
        ylabel="Odds ratio for participation relative to 2003",
        output_path=output_path,
        legend_title="Activity",
        hline=1,
        ylim=ylim,
        legend_below=True,
    )


if __name__ == "__main__":
    main()
