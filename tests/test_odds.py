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
