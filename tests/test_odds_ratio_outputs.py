import pandas as pd
import pytest

from conftest import DERIVED

WEEKLY_OR_MORE = {"Almost every day", "Once or twice a week"}

CASES = [
    {"name": "atus_or", "output": "atus_or.csv", "group_cols": ["ID"]},
    {"name": "atus_ed_or", "output": "atus_ed_or.csv", "group_cols": ["Educational Attainment"]},
    {"name": "ltt_or", "output": "ltt_or.csv", "group_cols": ["Age", "Read for Fun"]},
    {"name": "ltt_or_weekly", "output": "ltt_or_weekly.csv", "group_cols": ["Age"]},
]


def _load_or_skip(path):
    if not path.exists():
        pytest.skip(f"{path} not found — run scripts/data/*.py and scripts/data/*_or.py first")
    return pd.read_csv(path)


@pytest.mark.parametrize("case", CASES, ids=lambda c: c["name"])
def test_output_csv_matches_paper_formula(case):
    """Each row's stored Odds Ratio must equal (p/(100-p)) / (p_base/(100-p_base)),
    where p_base is the Percent at the earliest year for that row's grouping key.

    Verifies r_{jk} = (p_j/(1-p_j)) / (p_k/(1-p_k)) using output's own Percent column.
    """
    df = _load_or_skip(DERIVED / case["output"])
    group_cols = case["group_cols"]

    baseline_idx = df.groupby(group_cols)["Year"].idxmin()
    baseline = (
        df.loc[baseline_idx, group_cols + ["Year", "Percent"]]
        .rename(columns={"Year": "BaselineYear", "Percent": "BaselinePercent"})
    )
    merged = df.merge(baseline, on=group_cols, how="left", validate="many_to_one")

    pj = merged["Percent"]
    pk = merged["BaselinePercent"]
    expected_odds = pj / (100 - pj)
    expected_or = expected_odds / (pk / (100 - pk))

    # Stored values are rounded to 6 decimals, so max possible delta is 5e-7.
    assert (merged["Odds"] - expected_odds).abs().max() < 1e-6
    assert (merged["Odds Ratio"] - expected_or).abs().max() < 1e-6

    baseline_mask = merged["Year"] == merged["BaselineYear"]
    assert baseline_mask.any(), "no baseline-year rows found"
    assert (merged.loc[baseline_mask, "Odds Ratio"] - 1.0).abs().max() < 1e-6


def test_ltt_or_weekly_aggregates_before_odds():
    """`ltt_or_weekly.py` sums Percent across 'Almost every day' + 'Once or twice a week'
    per (Year, Age) before computing odds. Confirm the output's Percent column equals
    that sum reconstructed from `ltt.csv` — i.e., the aggregation happens first."""
    source = _load_or_skip(DERIVED / "ltt.csv")
    output = _load_or_skip(DERIVED / "ltt_or_weekly.csv")

    source = source.dropna(subset=["Year", "Age", "Read for Fun", "Percent"]).copy()
    source["Year"] = source["Year"].astype(int)
    source["Age"] = source["Age"].astype(int)
    source["Percent"] = source["Percent"].astype(float)

    weekly = source[source["Read for Fun"].isin(WEEKLY_OR_MORE)]
    expected = (
        weekly.groupby(["Year", "Age"], as_index=False)["Percent"]
        .sum()
        .rename(columns={"Percent": "ExpectedPercent"})
    )

    merged = output.merge(expected, on=["Year", "Age"], how="left", validate="one_to_one")
    assert merged["ExpectedPercent"].notna().all(), "output rows without a matching source aggregate"
    assert (merged["Percent"] - merged["ExpectedPercent"]).abs().max() < 1e-9
