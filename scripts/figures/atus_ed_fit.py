from __future__ import annotations

from pathlib import Path

import pandas as pd

from plotting import plot_grouped_fits
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
    odds_ratio_path = project_root / "data" / "derived" / "atus_ed_or.csv"
    output_path = project_root / "figures" / "fig4_fit.png"

    apply_style()

    atus_ed_or_df = pd.read_csv(odds_ratio_path)
    atus_ed_or_df = atus_ed_or_df[atus_ed_or_df["Activity"] == ACTIVITY]

    plot_grouped_fits(
        df=atus_ed_or_df,
        group_col="Educational Attainment",
        group_order=EDUCATION_ORDER,
        value_column="Odds Ratio",
        ylabel="Reading for personal interest odds ratio relative to 2004",
        output_path=output_path,
        legend_title="Education",
        hline=1,
        ylim=(0, 1.1),
        show_r2=True,
    )


if __name__ == "__main__":
    main()
