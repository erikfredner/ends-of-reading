import pandas as pd
import pytest

from conftest import DERIVED

WEEKLY_OR_MORE = {"Almost every day", "Once or twice a week"}

CASES = [
    {
        "name": "sppa_or",
        "output": "sppa_or.csv",
        "group_cols": ["Read in the last year"],
    },
    {"name": "atus_or", "output": "atus_or.csv", "group_cols": ["ID"]},
    {
        "name": "atus_ed_or",
        "output": "atus_ed_or.csv",
        "group_cols": ["Educational Attainment"],
    },
    {"name": "ltt_or", "output": "ltt_or.csv", "group_cols": ["Age", "Read for Fun"]},
    {"name": "ltt_or_weekly", "output": "ltt_or_weekly.csv", "group_cols": ["Age"]},
    {
        "name": "ltt_or_weekly_revised",
        "output": "ltt_or_weekly_revised.csv",
        "group_cols": ["Age"],
    },
]


def _load_or_skip(path):
    if not path.exists():
        pytest.skip(
            f"{path} not found — run scripts/data/*.py and scripts/data/*_or.py first"
        )
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
    baseline = df.loc[baseline_idx, group_cols + ["Year", "Percent"]].rename(
        columns={"Year": "BaselineYear", "Percent": "BaselinePercent"}
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

    merged = output.merge(
        expected, on=["Year", "Age"], how="left", validate="one_to_one"
    )
    assert merged["ExpectedPercent"].notna().all(), (
        "output rows without a matching source aggregate"
    )
    assert (merged["Percent"] - merged["ExpectedPercent"]).abs().max() < 1e-9


# The manuscript's SPPA odds ratios name their baseline year in the prose ("lower
# than they were in 1992"), so the baselines are part of the published claim, not
# an implementation detail. Poetry is the one that cannot be left to the
# earliest-year default: the 1982 and 1985 surveys asked whether respondents read
# *or listened to* poetry, so `sppa_or.py` pins poetry to 1992 and drops the two
# earlier rows.
EXPECTED_SPPA_BASELINES = {
    "Any book or magazine": 1982,
    "Any book": 1992,
    "Literature": 1982,
    "Novels or short stories": 1992,
    "Poetry": 1992,
    "Plays": 1992,
}


def test_sppa_or_baseline_years():
    df = _load_or_skip(DERIVED / "sppa_or.csv")
    baselines = df.groupby("Read in the last year")["Year"].min().to_dict()
    assert baselines == EXPECTED_SPPA_BASELINES


def test_sppa_or_drops_precomparable_poetry():
    """The pre-1992 poetry rows must not survive into the output at all — carrying
    them at a ratio above 1.0 would read as a rise in poetry reading."""
    df = _load_or_skip(DERIVED / "sppa_or.csv")
    poetry_years = set(df.loc[df["Read in the last year"] == "Poetry", "Year"])
    assert not poetry_years & {1982, 1985}


def test_ltt_revised_output_holds_only_revised_format_years():
    """The revised-format variants exist to avoid spanning NAEP's instrument
    change, so a single original-format row leaking in would defeat them."""
    full = _load_or_skip(DERIVED / "ltt_or_weekly.csv")
    revised = _load_or_skip(DERIVED / "ltt_or_weekly_revised.csv")

    assert set(revised["Assessment Format"]) == {"Revised"}
    assert set(revised["Year"]) == set(
        full.loc[full["Assessment Format"] == "Revised", "Year"]
    )
    assert revised.groupby("Age")["Year"].min().unique().tolist() == [2008]


def test_ltt_revised_percents_match_the_full_series():
    """Rebaselining must change only the odds ratios, never the underlying
    participation percentages."""
    full = _load_or_skip(DERIVED / "ltt_or_weekly.csv")
    revised = _load_or_skip(DERIVED / "ltt_or_weekly_revised.csv")

    merged = revised.merge(
        full[["Year", "Age", "Percent"]],
        on=["Year", "Age"],
        how="left",
        suffixes=("", "_full"),
        validate="one_to_one",
    )
    assert merged["Percent_full"].notna().all()
    assert (merged["Percent"] - merged["Percent_full"]).abs().max() < 1e-9
