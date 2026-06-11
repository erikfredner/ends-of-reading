import pytest

from atus_prediction import first_year_below_threshold, t_critical


@pytest.mark.parametrize(
    "df,expected",
    [
        (5, 2.5706),
        (10, 2.2281),
        (19, 2.0930),
        (30, 2.0423),
        (100, 1.9840),
    ],
)
def test_t_critical_matches_table_values(df, expected):
    """Two-sided 95% critical values from standard t tables."""
    assert t_critical(df) == pytest.approx(expected, abs=5e-4)


def test_first_year_below_threshold():
    # percent = 110 - 0.05 * year crosses 10% at year 2000 exactly, so the
    # first year strictly below is 2001.
    model = {"slope": -0.05, "intercept": 110.0}
    assert first_year_below_threshold(model, 10.0) == 2001
    # Crossing at 2000.5 → first full year below is 2001.
    model = {"slope": -0.05, "intercept": 110.025}
    assert first_year_below_threshold(model, 10.0) == 2001
    assert first_year_below_threshold({"slope": 0.0, "intercept": 20.0}, 10.0) is None
    assert first_year_below_threshold({"slope": 0.05, "intercept": 20.0}, 10.0) is None
