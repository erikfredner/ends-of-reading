from __future__ import annotations

from pathlib import Path

import pandas as pd

from plotting import latest_value_order, plot_grouped_fits
from style import apply_style

LEGEND_LABELS = {
    "Socializing and communicating (except social events)": "Socializing & communicating (not events)",
}


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]
    odds_ratio_path = project_root / "data" / "derived" / "atus_or.csv"
    output_path = project_root / "figures" / "fig2_fit.png"

    apply_style()

    atus_or_df = pd.read_csv(odds_ratio_path)
    # Same ordering as fig2 so each activity keeps its color across variants.
    category_order = latest_value_order(atus_or_df, "Activity", "Odds Ratio")
    odds_ratio_series = atus_or_df["Odds Ratio"]
    padding = (odds_ratio_series.max() - odds_ratio_series.min()) * 0.05
    ylim = (
        max(0, odds_ratio_series.min() - padding),
        odds_ratio_series.max() + padding,
    )

    plot_grouped_fits(
        df=atus_or_df,
        group_col="Activity",
        group_order=category_order,
        legend_labels=LEGEND_LABELS,
        value_column="Odds Ratio",
        ylabel="Odds ratio for participation relative to 2003",
        output_path=output_path,
        legend_title="Activity",
        hline=1,
        ylim=ylim,
        legend_below=True,
        show_r2=True,
        legend_fontsize="x-small",
    )


if __name__ == "__main__":
    main()
