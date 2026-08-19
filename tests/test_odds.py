import pytest

from odds import compute_odds


def test_compute_odds_known_values():
    assert compute_odds(50) == pytest.approx(1.0)
    assert compute_odds(80) == pytest.approx(4.0)
    assert compute_odds(25) == pytest.approx(1 / 3)
    assert compute_odds(1.6) == pytest.approx(0.016 / 0.984)


@pytest.mark.parametrize("p", [0.001, 1.6, 25.0, 50.0, 80.0, 99.999])
def test_compute_odds_self_ratio_is_one(p):
    assert compute_odds(p) / compute_odds(p) == pytest.approx(1.0)


@pytest.mark.parametrize("bad", [0, 100, -1, 101, -0.0001, 100.0001])
def test_compute_odds_rejects_out_of_range(bad):
    with pytest.raises(ValueError):
        compute_odds(bad)


@pytest.mark.parametrize(
    "pj,pk",
    [
        (50.0, 25.0),
        (80.0, 20.0),
        (1.6, 0.5),
        (10.0, 90.0),
        (33.3, 66.7),
        (99.0, 1.0),
    ],
)
def test_odds_ratio_matches_paper_definition(pj, pk):
    """compute_odds(pj) / compute_odds(pk) must equal (pj/(100-pj)) / (pk/(100-pk)).

    This is the algebraic restatement of r_jk = (p_j/(1-p_j)) / (p_k/(1-p_k))
    from Martin (2003) when p is supplied as a percentage.
    """
    paper_formula = (pj / (100 - pj)) / (pk / (100 - pk))
    assert compute_odds(pj) / compute_odds(pk) == pytest.approx(paper_formula)


from odds import add_odds_ratios  # noqa: E402


def _rows(*items):
    return [{"Group": g, "Year": y, "Percent": p} for g, y, p in items]


BY_GROUP = lambda row: row["Group"]  # noqa: E731


def test_add_odds_ratios_baselines_each_group_to_its_own_earliest_year():
    out = add_odds_ratios(
        _rows(("a", 2000, 50.0), ("a", 2010, 25.0), ("b", 2005, 80.0), ("b", 2010, 50.0)),
        key=BY_GROUP,
    )
    ratios = {(r["Group"], r["Year"]): r["Odds Ratio"] for r in out}
    assert ratios[("a", 2000)] == pytest.approx(1.0)
    assert ratios[("b", 2005)] == pytest.approx(1.0)
    assert ratios[("a", 2010)] == pytest.approx((1 / 3) / 1.0)
    assert ratios[("b", 2010)] == pytest.approx(1.0 / 4.0)


def test_baseline_year_pins_the_reference_and_drops_earlier_rows():
    """Pinning is what lets `sppa_or.py` start poetry at 1992 rather than at its
    earliest — and not-comparable — 1982 value."""
    out = add_odds_ratios(
        _rows(("a", 1982, 20.0), ("a", 1992, 50.0), ("a", 2022, 25.0)),
        key=BY_GROUP,
        baseline_year=1992,
    )
    assert [r["Year"] for r in out] == [1992, 2022]
    assert out[0]["Odds Ratio"] == pytest.approx(1.0)
    assert out[1]["Odds Ratio"] == pytest.approx((1 / 3) / 1.0)


def test_baseline_year_rejects_a_group_missing_that_year():
    with pytest.raises(ValueError, match="no usable 1992 value"):
        add_odds_ratios(
            _rows(("a", 1992, 50.0), ("b", 2002, 40.0)),
            key=BY_GROUP,
            baseline_year=1992,
        )


def test_require_common_baseline_rejects_mismatched_starts():
    """Figures captioned "relative to 2003" plot several groups on one axis; a
    group missing that first year would otherwise be silently baselined later."""
    with pytest.raises(ValueError, match="do not share a baseline year"):
        add_odds_ratios(
            _rows(("a", 2003, 50.0), ("a", 2010, 25.0), ("b", 2004, 40.0)),
            key=BY_GROUP,
            require_common_baseline=True,
        )


def test_require_common_baseline_accepts_matching_starts():
    out = add_odds_ratios(
        _rows(("a", 2003, 50.0), ("b", 2003, 40.0), ("a", 2010, 25.0)),
        key=BY_GROUP,
        require_common_baseline=True,
    )
    assert len(out) == 3
