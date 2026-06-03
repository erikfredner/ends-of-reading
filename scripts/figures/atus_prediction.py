from __future__ import annotations

from pathlib import Path
import math
from statistics import NormalDist

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from style import apply_style


ACTIVITY = "Reading for personal interest"


def fit_linear_model(years: np.ndarray, values: np.ndarray) -> dict[str, float]:
    x = years.astype(float)
    y = values.astype(float)
    n = len(x)
    x_mean = float(np.mean(x))
    y_mean = float(np.mean(y))
    sxx = float(np.sum((x - x_mean) ** 2))
    sxy = float(np.sum((x - x_mean) * (y - y_mean)))
    slope = sxy / sxx
    intercept = y_mean - slope * x_mean
    residuals = y - (intercept + slope * x)
    sigma = float(np.sqrt(np.sum(residuals**2) / (n - 2)))
    ss_res = float(np.sum(residuals**2))
    ss_tot = float(np.sum((y - y_mean) ** 2))
    r_squared = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
    return {
        "slope": slope,
        "intercept": intercept,
        "sigma": sigma,
        "x_mean": x_mean,
        "sxx": sxx,
        "n": float(n),
        "r_squared": r_squared,
    }


def predict_with_ci(
    years: np.ndarray, model: dict[str, float], ci: float = 0.95
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    x = years.astype(float)
    slope = model["slope"]
    intercept = model["intercept"]
    sigma = model["sigma"]
    x_mean = model["x_mean"]
    sxx = model["sxx"]
    n = model["n"]

    y_hat = intercept + slope * x
    alpha = 1.0 - ci
    crit = NormalDist().inv_cdf(1 - alpha / 2)
    se_mean = sigma * np.sqrt(1 / n + (x - x_mean) ** 2 / sxx)
    lower = y_hat - crit * se_mean
    upper = y_hat + crit * se_mean
    return y_hat, lower, upper


def first_year_below_threshold(
    model: dict[str, float], threshold: float
) -> int | None:
    slope = model["slope"]
    intercept = model["intercept"]
    if slope == 0:
        return None
    if slope > 0:
        return None

    crossing = (threshold - intercept) / slope
    if math.isclose(crossing, round(crossing), abs_tol=1e-9):
        return int(round(crossing)) + 1
    return math.ceil(crossing)


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]

    apply_style()

    data_path = project_root / "data" / "derived" / "atus.csv"
    output_path = project_root / "figures" / "atus_prediction.png"

    df = pd.read_csv(data_path)
    df = df[df["Activity"] == ACTIVITY].copy()
    df = df.sort_values("Year")

    years = df["Year"].to_numpy()
    values = df["Percent"].to_numpy()

    model = fit_linear_model(years, values)
    threshold_year = first_year_below_threshold(model, 10.0)

    min_year = int(years.min())
    max_year = int(years.max())
    end_year = max(2040, max_year)
    if threshold_year is not None:
        end_year = max(end_year, threshold_year + 1)

    plot_years = np.arange(min_year, end_year + 1)
    y_hat, lower, upper = predict_with_ci(plot_years, model)

    fig, ax = plt.subplots()
    colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]
    color_obs = colors[0]
    color_pred = colors[1] if len(colors) > 1 else colors[0]

    ax.scatter(
        pd.to_datetime(years, format="%Y"),
        values,
        color=color_obs,
        label="Observed",
        zorder=3,
    )
    ax.plot(
        pd.to_datetime(plot_years, format="%Y"),
        y_hat,
        color=color_pred,
        linewidth=1,
        label="Linear fit",
        marker="",
    )
    ax.fill_between(
        pd.to_datetime(plot_years, format="%Y"),
        lower,
        upper,
        color=color_pred,
        alpha=0.2,
        label="95% CI",
    )

    ax.axhline(10, color="gray", linestyle="dashed", linewidth=1)

    if threshold_year is not None:
        predicted_value = model["intercept"] + model["slope"] * threshold_year
        annotation_year = pd.to_datetime(threshold_year, format="%Y")
        annotation_text_year = pd.to_datetime(threshold_year + 1, format="%Y")
        ax.annotate(
            f"{threshold_year}",
            xy=(annotation_year, predicted_value),
            xytext=(annotation_text_year, predicted_value + 5),
            arrowprops={"arrowstyle": "->", "color": "gray", "linewidth": 1},
            fontsize=9,
            ha="left",
        )

    n_years = (end_year - min_year) + 1
    step = max(1, math.ceil(n_years / 8))
    ax.set_xlabel("Year")
    ax.set_ylabel("% US adults reading for personal interest on an average day")
    min_year_ts = pd.to_datetime(min_year, format="%Y")
    max_year_ts = pd.to_datetime(end_year, format="%Y")
    padding = (max_year_ts - min_year_ts) * 0.04
    ax.set_xlim(min_year_ts - padding, max_year_ts + padding)
    ax.xaxis.set_major_locator(mdates.YearLocator(base=step))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.set_ylim(0, max(values) + 5)
    ax.text(
        0.02,
        0.95,
        rf"$R^2$ = {model['r_squared']:.3f}",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=9,
    )
    ax.legend(frameon=False)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    for suffix in (".png", ".svg", ".eps"):
        fig.savefig(output_path.with_suffix(suffix))
    plt.close(fig)


if __name__ == "__main__":
    main()
