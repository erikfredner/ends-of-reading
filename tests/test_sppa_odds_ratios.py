import pandas as pd
import pytest

from sppa import _compute_odds_ratios


def _make_df():
    return pd.DataFrame(
        {
            "Year": pd.to_datetime(
                ["1985", "1992", "2002", "1985", "1992", "2002"], format="%Y"
            ),
            "Read in the last year": [
                "Any book", "Any book", "Any book",
                "Poetry", "Poetry", "Poetry",
            ],
            "Percent": [60.0, 50.0, 40.0, 20.0, 17.0, 12.0],
        }
    )


def test_sppa_drops_pre_baseline_years():
    out = _compute_odds_ratios(_make_df(), baseline_year=1992)
    assert (out["Year"].dt.year >= 1992).all()
    assert len(out) == 4


def test_sppa_baseline_year_odds_ratio_is_one():
    out = _compute_odds_ratios(_make_df(), baseline_year=1992)
    baseline_rows = out[out["Year"].dt.year == 1992]
    assert len(baseline_rows) == 2
    assert (baseline_rows["Odds Ratio"] - 1.0).abs().max() == pytest.approx(0.0, abs=1e-12)


def test_sppa_odds_ratio_matches_paper_formula():
    """`sppa.py` inlines `p/(1-p)` rather than calling `compute_odds()` from odds.py.
    This test pins that independent code path to the same paper definition:
    r_{jk} = (p_j/(1-p_j)) / (p_k/(1-p_k)) with p_k taken at baseline_year per category.
    """
    out = _compute_odds_ratios(_make_df(), baseline_year=1992).copy()

    baseline_pct = {"Any book": 50.0, "Poetry": 17.0}
    out["BaselinePercent"] = out["Read in the last year"].map(baseline_pct)
    pj = out["Percent"]
    pk = out["BaselinePercent"]
    expected_or = (pj / (100 - pj)) / (pk / (100 - pk))

    assert (out["Odds Ratio"] - expected_or).abs().max() == pytest.approx(0.0, abs=1e-12)
