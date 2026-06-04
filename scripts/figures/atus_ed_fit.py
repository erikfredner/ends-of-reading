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


def plot_education_fits(
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
    for category in education_order:
        subset = df[df["Educational Attainment"] == category].sort_values("Year")
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
    ax.legend(handles=handles, title=legend_title, frameon=False)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    for suffix in (".png", ".svg", ".eps"):
        fig.savefig(output_path.with_suffix(suffix))
    plt.close(fig)


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]
    figures_dir = project_root / "figures"

    apply_style()

    odds_ratio_path = project_root / "data" / "derived" / "atus_ed_or.csv"
    output_path = figures_dir / "fig4_fit.png"

    education_order = [
        "Bachelor's degree and higher",
        "Some college or associate degree",
        "High school graduates (no college)",
        "Less than a high school diploma",
    ]
    activity = "Reading for personal interest"

    atus_ed_or_df = pd.read_csv(odds_ratio_path)
    atus_ed_or_df = atus_ed_or_df[atus_ed_or_df["Activity"] == activity].copy()
    ylim = (0, 1.1)

    plot_education_fits(
        df=atus_ed_or_df,
        education_order=education_order,
        legend_labels={},
        value_column="Odds Ratio",
        ylabel="Reading for personal interest odds ratio relative to 2004",
        output_path=output_path,
        legend_title="Education",
        hline=1,
        ylim=ylim,
    )


if __name__ == "__main__":
    main()
