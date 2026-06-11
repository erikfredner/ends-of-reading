from __future__ import annotations

from pathlib import Path

import pandas as pd

from plotting import plot_grouped_timeseries
from style import apply_style


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
        ylabel="% US students reading for fun weekly or more often",
        output_path=output_path,
        legend_title="Age",
        hline=50,
        ylim=(0, 100),
    )


if __name__ == "__main__":
    main()
