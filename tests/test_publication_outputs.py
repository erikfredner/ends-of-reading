"""Regression checks for the manuscript's source choice and publication cutoffs."""

import importlib.util

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
import pytest

import atus_prediction
import cited_values
from conftest import DERIVED, PROJECT_ROOT
from publication import ATUS_END_YEAR


def test_leisure_change_uses_population_hours():
    sentence = cited_values.sentence_leisure_time_change()
    assert "about 1 percent more leisure time in 2025 than in 2003" in sentence
    assert "Computed: +1.0%" in sentence
    assert "[TUU10101AA01013585]" in sentence
    assert "2003: 5.11 hrs; 2025: 5.16 hrs" in sentence


def test_atus_cited_values_share_latest_cutoff():
    # A new release must advance the publication cutoff as well as the data.
    assert pd.read_csv(DERIVED / "atus.csv")["Year"].max() == ATUS_END_YEAR == 2025
    assert cited_values._atus_rows(cited_values.READING)[-1][0] == 2025
    assert cited_values._atus_reading_decline()["latest_year"] == 2025
    assert "As of 2025, 16 minutes" in cited_values.sentence_atus_avg_minutes()
    assert "did so for 100 minutes" in (
        cited_values.sentence_atus_avg_minutes_participants()
    )
    # The introduction's bullets name the same year as the body (p. 546).
    assert "In 2025, 84 percent of US adults" in cited_values.sentence_atus_nonreaders()
    assert "46 percent lower in 2025 than they were in 2003" in (
        cited_values.sentence_atus_or_2003()
    )
    prediction = cited_values.sentence_atus_prediction_year()
    assert "first year below 10% = 2035" in prediction
    assert "2003–2025, n=22" in prediction


def test_ltt_sentences_quote_the_revised_format_baseline():
    # The prose baselines LTT odds to 2008, the first revised-format year; the
    # 1984 reading spans NAEP's instrument change and appears only to compare.
    age13 = cited_values.sentence_ltt_age13_or_2008()
    assert "48 percent lower in 2025 than they were in 2008" in age13
    assert "Compare: 76.9% lower across both assessment formats (1984–2025)" in age13

    both = cited_values.sentence_ltt_age9_age13_or_2008()
    assert "36 percent lower than they were in 2008" in both
    assert "thirteen-year-olds reading for fun weekly or more are 48 percent" in both


def test_ltt_weekly_majority_check():
    check = cited_values.check_ltt_weekly_majority()
    assert "age 9: a majority in every year, 1984–2025" in check
    assert "age 13: last majority 2012 (53%); below half from 2020 (40%)" in check
    assert "age 17: last majority 2004 (52%); below half from 2008 (42%)" in check
    assert "last surveyed 2012" in check


def test_figure2_uses_publication_cutoff(monkeypatch):
    # Load by path to avoid collision with the data extractor named atus.py.
    spec = importlib.util.spec_from_file_location(
        "atus_figure", PROJECT_ROOT / "scripts" / "figures" / "atus.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    captured = {}
    monkeypatch.setattr(module, "apply_style", lambda: None)
    monkeypatch.setattr(
        module, "plot_grouped_timeseries", lambda **kwargs: captured.update(kwargs)
    )
    module.main()
    df = captured["df"]
    assert df.groupby("Activity")["Year"].max().eq(2025).all()
    assert df["Year"].min() == 2003


def test_forecast_plot_matches_cited_values(monkeypatch):
    def inspect_figure(fig, output_path):
        try:
            ax = fig.axes[0]
            observations = ax.collections[0].get_offsets()
            years = [mdates.num2date(float(x)).year for x in observations[:, 0]]
            assert min(years) == 2003
            assert max(years) == 2025
            assert 2020 not in years
            assert len(years) == 22
            labels = [text.get_text() for text in ax.texts]
            assert "2035" in labels
            assert r"$R^2$ = 0.923" in labels
        finally:
            plt.close(fig)

    monkeypatch.setattr(atus_prediction, "apply_style", lambda: None)
    monkeypatch.setattr(atus_prediction, "save_figure", inspect_figure)
    atus_prediction.main()


def test_refreshed_ltt_2023_observation_reaches_all_derivations():
    for filename in ("ltt.csv", "ltt_or.csv"):
        df = pd.read_csv(DERIVED / filename)
        rows = df[(df["Age"] == 13) & (df["Year"] == 2023)]
        assert len(rows) == 5
        assert dict(zip(rows["Read for Fun"], rows["Percent"])) == {
            "Almost every day": 14,
            "Once or twice a week": 22,
            "Once or twice a month": 17,
            "A few times a year": 16,
            "Never or hardly ever": 31,
        }
    for filename, baseline_percent in (
        ("ltt_or_weekly.csv", 70),
        ("ltt_or_weekly_revised.csv", 51),
    ):
        df = pd.read_csv(DERIVED / filename)
        rows = df[(df["Age"] == 13) & (df["Year"] == 2023)]
        assert len(rows) == 1
        row = rows.iloc[0]
        assert row["Percent"] == 36
        expected = (36 / 64) / (baseline_percent / (100 - baseline_percent))
        assert row["Odds Ratio"] == pytest.approx(expected, abs=5e-7)


def test_committed_cited_values_match_current_data():
    # Pins every claim, including those without a targeted test above.
    path = DERIVED / "cited_values.txt"
    if not path.exists():
        pytest.skip(f"{path} not found — run scripts/cited_values.py first")
    assert path.read_text(encoding="utf-8") == cited_values.render(), (
        "cited values changed; rerun scripts/cited_values.py and check the prose"
    )
