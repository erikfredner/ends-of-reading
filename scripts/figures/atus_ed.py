from __future__ import annotations

from pathlib import Path

import pandas as pd

from plotting import plot_grouped_timeseries
from style import apply_style

EDUCATION_ORDER = [
    "Bachelor's degree and higher",
    "Some college or associate degree",
    "High school graduates (no college)",
    "Less than a high school diploma",
]
ACTIVITY = "Reading for personal interest"


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]
    figures_dir = project_root / "figures"
    data_path = project_root / "data" / "derived" / "atus_ed.csv"
    odds_ratio_path = project_root / "data" / "derived" / "atus_ed_or.csv"

    apply_style()

    atus_ed_df = pd.read_csv(data_path)
    atus_ed_df = atus_ed_df[atus_ed_df["Activity"] == ACTIVITY]
    plot_grouped_timeseries(
        df=atus_ed_df,
        group_col="Educational Attainment",
        group_order=EDUCATION_ORDER,
        value_column="Percent",
        ylabel="US adults reading for personal interest on an average day",
        output_path=figures_dir / "fig3.png",
        legend_title="Education",
        hline=50,
        ylim=(0, 100),
        fill_year_gaps=True,
        percent_y=True,
    )

    atus_ed_or_df = pd.read_csv(odds_ratio_path)
    atus_ed_or_df = atus_ed_or_df[atus_ed_or_df["Activity"] == ACTIVITY]
    plot_grouped_timeseries(
        df=atus_ed_or_df,
        group_col="Educational Attainment",
        group_order=EDUCATION_ORDER,
        value_column="Odds Ratio",
        ylabel="Odds ratio of reading for personal interest relative to 2004",
        output_path=figures_dir / "fig4.png",
        legend_title="Education",
        hline=1,
        ylim=(0, 1.1),
        fill_year_gaps=True,
    )


if __name__ == "__main__":
    main()
