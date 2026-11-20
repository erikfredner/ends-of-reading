"""Recompute values cited in the manuscript at the publication data cutoffs.

Run as ``python scripts/cited_values.py``. Each ``Sentence`` block prints one
manuscript sentence, worded as in the corrected American Literature proofs and
tagged with its proof page, followed by the value recomputed from the current
CSVs, with the data source and arithmetic shown in parentheses for
spot-checking. Blocks run in the order the sentences appear in the article.

Odds ratios are read from the committed ``data/derived/*_or.csv`` rather than
recomputed here, so every odds-ratio sentence in the manuscript goes through
the same ``scripts/data/odds.py`` derivation that
``tests/test_odds_ratio_outputs.py`` verifies.

The prediction claim is the one exception to reading from committed CSVs: its
forecast is a regression fit at plot time, so it reuses the fit in
``scripts/figures/atus_prediction.py`` rather than restating a crossing year.

LTT odds ratios are quoted inside NAEP's revised assessment format, baselined
to 2008 (``ltt_or_weekly_revised.csv``). Each LTT sentence adds a ``Compare``
line with the 1984-baselined reading, which spans the format change; that
reading backs only the introduction's cross-decade "about half or more".

``Check`` blocks verify a claim the prose makes without printing a number.
"""

from __future__ import annotations

import csv
import math
import sys
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

from publication import ATUS_END_YEAR

PROJECT_ROOT = Path(__file__).resolve().parents[1]

SPPA_OR_PATH = PROJECT_ROOT / "data" / "derived" / "sppa_or.csv"
ATUS_PATH = PROJECT_ROOT / "data" / "derived" / "atus.csv"
ATUS_OR_PATH = PROJECT_ROOT / "data" / "derived" / "atus_or.csv"
LTT_OR_WEEKLY_PATH = PROJECT_ROOT / "data" / "derived" / "ltt_or_weekly.csv"
LTT_OR_WEEKLY_REVISED_PATH = (
    PROJECT_ROOT / "data" / "derived" / "ltt_or_weekly_revised.csv"
)
FIGURES_DIR = PROJECT_ROOT / "scripts" / "figures"
ATUS_SOURCE_DIR = PROJECT_ROOT / "data" / "source" / "atus"
# Raw BLS ATUS dumps; filenames are bare series ids (see _atus_estimate_rows).
ATUS_AVG_HRS_READING_PATH = ATUS_SOURCE_DIR / "TUU10101AA01006315.txt"
ATUS_AVG_HRS_READING_PARTICIPANTS_PATH = ATUS_SOURCE_DIR / "TUU20101AA01006315.txt"
ATUS_AVG_HRS_LEISURE_PATH = ATUS_SOURCE_DIR / "TUU10101AA01013585.txt"

READING = "Reading for personal interest"
# "fewer than one in ten Americans", the threshold the manuscript's forecast names.
PREDICTION_THRESHOLD = 10.0


def _round(value: float) -> int:
    """Round half away from zero, the convention the manuscript's prose uses.

    Exact halves do occur here — the SPPA non-reader figure is 51.5% — and
    builtin ``round`` is banker's rounding, which sends them to the nearest
    even integer. It happens to agree on 51.5 because 52 is even; a half
    landing on an odd integer would disagree with the manuscript silently.
    """
    return int(Decimal(repr(value)).quantize(Decimal(1), rounding=ROUND_HALF_UP))


def _percent(value: float) -> str:
    """Format a value the way the prose does: "46 percent"."""
    return f"{_round(value)} percent"


def _read(path: Path) -> list[dict[str, str]]:
    with path.open() as f:
        return list(csv.DictReader(f))


def _atus_rows(activity: str) -> list[tuple[int, float]]:
    rows = []
    for row in _read(ATUS_PATH):
        if row["Activity"] != activity or int(row["Year"]) > ATUS_END_YEAR:
            continue
        percent = row["Percent"]
        if not percent:
            continue
        rows.append((int(row["Year"]), float(percent)))
    rows.sort(key=lambda r: r[0])
    return rows


def _atus_estimate_rows(path: Path) -> list[tuple[int, float]]:
    """Read a raw BLS ATUS dump (metadata header + Year,Period,Estimate,...).

    The dumps carry a metadata header block; skip to the ``Year,`` line before
    parsing. Suppressed rows (BLS marks these "-(M)" or similar) are skipped.
    """
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    header_idx = next(
        (i for i, line in enumerate(lines) if line.startswith("Year,")), None
    )
    data_lines = lines[header_idx:] if header_idx is not None else []

    rows = []
    for row in csv.DictReader(data_lines):
        year_str = (row.get("Year") or "").strip()
        estimate = (row.get("Estimate") or "").strip()
        if not year_str or not estimate:
            continue
        try:
            year = int(float(year_str))
            value = float(estimate)
        except ValueError:
            continue
        if math.isnan(value) or year > ATUS_END_YEAR:
            continue
        rows.append((year, value))
    rows.sort(key=lambda r: r[0])
    return rows


def _decline(
    path: Path, group_col: str, group: str, *, end_year: int | None = None
) -> dict:
    """Decline in the odds for one group of a derived ``*_or.csv``.

    The group's baseline year is whichever year the derivation baselined it to,
    i.e. the earliest year present in its output rows, where its odds ratio is
    1.0 by construction.
    """
    rows = [
        row
        for row in _read(path)
        if row[group_col] == group
        and (end_year is None or int(row["Year"]) <= end_year)
    ]
    rows.sort(key=lambda row: int(row["Year"]))
    baseline, latest = rows[0], rows[-1]
    odds_ratio = float(latest["Odds Ratio"])
    return {
        "baseline_year": int(baseline["Year"]),
        "baseline_percent": float(baseline["Percent"]),
        "baseline_odds": float(baseline["Odds"]),
        "latest_year": int(latest["Year"]),
        "latest_percent": float(latest["Percent"]),
        "latest_odds": float(latest["Odds"]),
        "odds_ratio": odds_ratio,
        "lower_pct": (1 - odds_ratio) * 100,
    }


def _arithmetic(source: str, d: dict) -> str:
    return (
        f"({source}, "
        f"{d['baseline_year']}: {d['baseline_percent']}% → odds {d['baseline_odds']:.4f}; "
        f"{d['latest_year']}: {d['latest_percent']}% → odds {d['latest_odds']:.4f}; "
        f"OR {d['odds_ratio']:.4f} → 1−OR)"
    )


def _block(page: str, sentence: str, computed: str) -> str:
    return f"Sentence (p. {page}): {sentence}\n  Computed: {computed}"


def _sppa_decline(category: str) -> dict:
    return _decline(SPPA_OR_PATH, "Read in the last year", category)


def _sppa_or_sentence(page: str, category: str, sentence_template: str) -> str:
    d = _sppa_decline(category)
    sentence = sentence_template.format(
        pct=_percent(d["lower_pct"]),
        baseline_year=d["baseline_year"],
        latest_year=d["latest_year"],
    )
    return _block(
        page,
        sentence,
        f"{d['lower_pct']:.1f}% lower  " + _arithmetic(f'SPPA "{category}"', d),
    )


def _atus_reading_decline() -> dict:
    return _decline(ATUS_OR_PATH, "Activity", READING, end_year=ATUS_END_YEAR)


def _ltt_decline(age: int) -> dict:
    """The decline the prose quotes: revised assessment format, 2008 baseline."""
    return _decline(LTT_OR_WEEKLY_REVISED_PATH, "Age", str(age))


def _ltt_decline_since_1984(age: int) -> dict:
    """The full-series decline, which spans NAEP's post-2004 format change."""
    return _decline(LTT_OR_WEEKLY_PATH, "Age", str(age))


def _ltt_computed(age: int) -> str:
    d = _ltt_decline(age)
    full = _ltt_decline_since_1984(age)
    return (
        f"{d['lower_pct']:.1f}% lower  "
        + _arithmetic(f'LTT "Weekly or more often", age {age}, revised format', d)
        + f"\n  Compare: {full['lower_pct']:.1f}% lower across both assessment "
        f"formats ({full['baseline_year']}–{full['latest_year']}); the prose "
        "quotes the revised-format reading."
    )


def sentence_sppa_any_book_nonreaders() -> str:
    d = _sppa_decline("Any book")
    nonreaders = 100 - d["latest_percent"]
    sentence = (
        f"In {d['latest_year']}, {_percent(nonreaders)} of US adults had not read "
        "any book in the preceding year."
    )
    return _block(
        "535",
        sentence,
        f"{nonreaders:.1f}%  "
        f'(SPPA "Any book", {d["latest_year"]}: {d["latest_percent"]}% read '
        f"→ 100−{d['latest_percent']})",
    )


def sentence_atus_nonreaders() -> str:
    year, percent = _atus_rows(READING)[-1]
    nonreaders = 100 - percent
    sentence = (
        f"In {year}, {_percent(nonreaders)} of US adults did not read anything for "
        "personal interest on an average day, including the news."
    )
    return _block(
        "535",
        sentence,
        f'{nonreaders:.1f}%  (ATUS "{READING}", {year}: {percent}% → 100−{percent})',
    )


def sentence_atus_or_2003() -> str:
    d = _atus_reading_decline()
    sentence = (
        "The odds of US adults reading anything for personal interest on an "
        f"average day were {_percent(d['lower_pct'])} lower in {d['latest_year']} "
        f"than they were in {d['baseline_year']}."
    )
    return _block(
        "535",
        sentence,
        f"{d['lower_pct']:.1f}% lower  " + _arithmetic(f'ATUS "{READING}"', d),
    )


def sentence_sppa_literature_or_1982() -> str:
    return _sppa_or_sentence(
        "536",
        "Literature",
        "The odds of US adults reading a novel, short story, poem, or play in the "
        "previous year were {pct} lower in {latest_year} than they were in "
        "{baseline_year}.",
    )


def sentence_ltt_age13_or_2008() -> str:
    d = _ltt_decline(13)
    sentence = (
        "The odds of US thirteen-year-olds reading for fun weekly or more often "
        f"were {_percent(d['lower_pct'])} lower in {d['latest_year']} than they "
        f"were in {d['baseline_year']}."
    )
    return _block("536", sentence, _ltt_computed(13))


def sentence_decline_by_half_since_1980s() -> str:
    """The introduction's 1980s-to-2020s comparison.

    This is the one claim that needs the LTT's 1984 baselines, since the
    revised format only starts in 2008. Both LTT lines span NAEP's format
    change; the SPPA line alone already supports "about half".
    """
    sppa = _sppa_decline("Literature")
    ltt = {age: _ltt_decline_since_1984(age) for age in (9, 13)}
    sentence = (
        "To say that reading was in “crisis” in the 1980s and is still in “crisis” "
        "in the 2020s obscures the fact of a decline in the odds of voluntary "
        "reading by about half or more in the intervening years."
    )
    lines = [
        f"Sentence (p. 536): {sentence}",
        "  Computed:",
        f"    SPPA Literature: {sppa['lower_pct']:.1f}% lower  "
        + _arithmetic("SPPA", sppa),
    ]
    for age, d in ltt.items():
        lines.append(
            f"    LTT age {age}: {d['lower_pct']:.1f}% lower, spanning NAEP's "
            "format change  " + _arithmetic('LTT "Weekly or more often"', d)
        )
    return "\n".join(lines)


def sentence_sppa_novels_poetry_plays_or_1992() -> str:
    categories = ("Novels or short stories", "Poetry", "Plays")
    declines = [_sppa_decline(category) for category in categories]
    baseline_year = declines[0]["baseline_year"]
    latest_year = declines[0]["latest_year"]
    novels, poetry, plays = (_percent(d["lower_pct"]) for d in declines)
    sentence = (
        f"The odds of reading novels or short stories in {latest_year} are "
        f"{novels} lower than they were in {baseline_year}, whereas the odds of "
        f"reading poetry or plays are down by {poetry} and {plays}, respectively."
    )
    lines = [f"Sentence (p. 544): {sentence}", "  Computed:"]
    for category, d in zip(categories, declines):
        lines.append(
            f"    {category}: {d['lower_pct']:.1f}% lower  " + _arithmetic("SPPA", d)
        )
    return "\n".join(lines)


def sentence_sppa_literature_or_1982_v2() -> str:
    return _sppa_or_sentence(
        "545",
        "Literature",
        "The odds of reading literature in the preceding year are about {pct} "
        "lower in {latest_year} than they were in {baseline_year}.",
    )


def sentence_atus_avg_minutes() -> str:
    rows = dict(_atus_estimate_rows(ATUS_AVG_HRS_READING_PATH))
    year = max(rows)
    hours = rows[year]
    minutes = hours * 60
    sentence = (
        f"As of {year}, {_round(minutes)} minutes a day is about the average amount "
        "of time Americans spent reading anything for personal interest on an "
        "average day."
    )
    return _block(
        "546",
        sentence,
        f"{minutes:.1f} minutes/day  "
        f'(ATUS "Avg hrs per day - Reading for personal interest" '
        f"[TUU10101AA01006315], {year}: {hours} hrs × 60)",
    )


def sentence_atus_zero_minutes() -> str:
    year, percent = _atus_rows(READING)[-1]
    nonreaders = 100 - percent
    sentence = (
        f"However, this average conceals the fact that {_percent(nonreaders)} of "
        "people in the United States read for zero minutes on an average day."
    )
    return _block(
        "546",
        sentence,
        f'{nonreaders:.1f}%  (ATUS "{READING}", {year}: {percent}% participated '
        f"→ 100−{percent})",
    )


def sentence_atus_avg_minutes_participants() -> str:
    rows = dict(_atus_estimate_rows(ATUS_AVG_HRS_READING_PARTICIPANTS_PATH))
    year = max(rows)
    hours = rows[year]
    minutes = hours * 60
    sentence = (
        "On average, those who read for personal interest did so for "
        f"{_round(minutes)} minutes."
    )
    return _block(
        "546",
        sentence,
        f"{minutes:.1f} minutes/day  "
        f'(ATUS "Avg hrs per day for participants - Reading for personal interest" '
        f"[TUU20101AA01006315], {year}: {hours} hrs × 60)",
    )


def sentence_atus_peak_2004_vs_latest() -> str:
    rows = dict(_atus_rows(READING))
    latest_year = max(rows)
    p_latest = rows[latest_year]
    peak_year = max(rows, key=lambda y: rows[y])
    peak_percent = rows[peak_year]
    sentence = (
        f"In the peak year of {peak_year}, {_percent(peak_percent)} of the US "
        "population read for personal interest on an average day; in "
        f"{latest_year}, {_percent(p_latest)} did."
    )
    return _block(
        "546",
        sentence,
        f"{peak_year} = {peak_percent:.1f}%, {latest_year} = {p_latest:.1f}%  "
        f'(ATUS "{READING}")',
    )


def sentence_atus_or_2003_v2() -> str:
    d = _atus_reading_decline()
    sentence = (
        f"In {d['latest_year']}, the odds of Americans reading for personal "
        f"interest were {_percent(d['lower_pct'])} lower than they were in "
        f"{d['baseline_year']}."
    )
    return _block(
        "546",
        sentence,
        f"{d['lower_pct']:.1f}% lower  " + _arithmetic(f'ATUS "{READING}"', d),
    )


def sentence_leisure_time_change() -> str:
    rows = dict(_atus_estimate_rows(ATUS_AVG_HRS_LEISURE_PATH))
    baseline_year = 2003
    latest_year = max(rows)
    baseline_hrs = rows[baseline_year]
    latest_hrs = rows[latest_year]
    change_pct = (latest_hrs - baseline_hrs) / baseline_hrs * 100
    direction = "more" if change_pct >= 0 else "less"
    sentence = (
        "Surprisingly, people in the United States reported about "
        f"{_percent(abs(change_pct))} {direction} leisure time in {latest_year} "
        f"than in {baseline_year}."
    )
    return _block(
        "546–47",
        sentence,
        f"{change_pct:+.1f}%  "
        f'(ATUS "Avg hrs per day - Leisure and sports (includes travel)" '
        f"[TUU10101AA01013585], {baseline_year}: {baseline_hrs} hrs; "
        f"{latest_year}: {latest_hrs} hrs; (latest−baseline)/baseline)",
    )


def check_ltt_weekly_majority() -> str:
    """When each age stopped mostly reading for fun at least weekly.

    Backs the sentence after "As figure 5 shows" and note 20 (no age-17
    survey since 2012). Reads percentages, so the baseline choice is moot.
    """
    by_age: dict[int, list[tuple[int, float]]] = {}
    for row in _read(LTT_OR_WEEKLY_PATH):
        by_age.setdefault(int(row["Age"]), []).append(
            (int(row["Year"]), float(row["Percent"]))
        )

    header = (
        "Check (p. 549): last LTT year in which most children read for fun "
        "weekly or more often, by age"
    )
    lines = [header, "  Computed:"]
    for age, rows in sorted(by_age.items()):
        rows.sort()
        first_year, last_year = rows[0][0], rows[-1][0]
        majority = [(y, p) for y, p in rows if p > 50]
        if len(majority) == len(rows):
            detail = f"a majority in every year, {first_year}–{last_year}"
        else:
            last_y, last_p = majority[-1]
            below = [(y, p) for y, p in rows if y > last_y]
            detail = (
                f"last majority {last_y} ({last_p:.0f}%); below half from "
                f"{below[0][0]} ({below[0][1]:.0f}%)"
            )
        lines.append(
            f"    age {age}: {detail}; last surveyed {last_year} ({rows[-1][1]:.0f}%)"
        )
    return "\n".join(lines)


def sentence_ltt_age9_age13_or_2008() -> str:
    d9, d13 = _ltt_decline(9), _ltt_decline(13)
    sentence = (
        f"In {d9['latest_year']}, the odds of nine-year-olds reading for fun weekly "
        f"or more are {_percent(d9['lower_pct'])} lower than they were in "
        f"{d9['baseline_year']}, but the odds of thirteen-year-olds reading for "
        f"fun weekly or more are {_percent(d13['lower_pct'])} lower."
    )
    computed = "\n".join(
        f"    Age {age}: " + _ltt_computed(age).replace("\n  ", "\n      ")
        for age in (9, 13)
    )
    return f"Sentence (p. 549): {sentence}\n  Computed:\n{computed}"


def sentence_atus_prediction_year() -> str:
    """Recompute the year the manuscript's forecast crosses one in ten.

    This claim is the one here with no committed CSV behind it: the forecast is
    a regression fit at plot time. So rather than restate a crossing year, it
    reuses the fit in ``scripts/figures/atus_prediction.py`` — the same model
    the figure draws — imported bare off its own directory, the way
    ``tests/conftest.py`` reaches the pipeline modules. The import is local to
    this function so the other claims do not pay for pulling in matplotlib.
    """
    figures_dir = str(FIGURES_DIR)
    if figures_dir not in sys.path:
        sys.path.insert(0, figures_dir)

    import numpy as np

    from atus_prediction import first_year_below_threshold, fit_linear_model

    rows = _atus_rows(READING)
    years = np.array([year for year, _ in rows])
    percents = np.array([percent for _, percent in rows])
    model = fit_linear_model(years, percents)
    crossing_year = first_year_below_threshold(model, PREDICTION_THRESHOLD)

    if crossing_year is None:
        sentence = (
            "The fitted trend no longer falls below one in ten, so the "
            "manuscript's prediction sentence needs rewriting."
        )
        computed = "no crossing (the fitted slope is not negative)"
    else:
        sentence = (
            "If the federal government is still administering the ATUS, a simple "
            "linear model predicts that fewer than one in ten Americans will read "
            "for personal interest on an average day for the first time in "
            f"{crossing_year}."
        )
        computed = f"first year below {_round(PREDICTION_THRESHOLD)}% = {crossing_year}"

    return _block(
        "550",
        sentence,
        f"{computed}  "
        f'(OLS on ATUS "{READING}", {rows[0][0]}–{rows[-1][0]}, '
        f"n={model['n']:.0f}: slope {model['slope']:+.4f} points/year, "
        f"intercept {model['intercept']:.1f}, R² {model['r_squared']:.3f}; "
        "same fit as scripts/figures/atus_prediction.py)",
    )


CLAIMS = [
    sentence_sppa_any_book_nonreaders,
    sentence_atus_nonreaders,
    sentence_atus_or_2003,
    sentence_sppa_literature_or_1982,
    sentence_ltt_age13_or_2008,
    sentence_decline_by_half_since_1980s,
    sentence_sppa_novels_poetry_plays_or_1992,
    sentence_sppa_literature_or_1982_v2,
    sentence_atus_avg_minutes,
    sentence_atus_zero_minutes,
    sentence_atus_avg_minutes_participants,
    sentence_atus_peak_2004_vs_latest,
    sentence_atus_or_2003_v2,
    sentence_leisure_time_change,
    check_ltt_weekly_majority,
    sentence_ltt_age9_age13_or_2008,
    sentence_atus_prediction_year,
]


def main() -> None:
    for claim in CLAIMS:
        print(claim())
        print()


if __name__ == "__main__":
    main()
