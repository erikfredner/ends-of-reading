"""Recompute values cited in the manuscript from the latest data.

Run as ``python scripts/cited_values.py``. Each block prints one manuscript
sentence followed by the value recomputed from the current CSVs, with the
data source and arithmetic shown in parentheses for spot-checking.
"""
from __future__ import annotations

import csv
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SPPA_PATH = PROJECT_ROOT / "data" / "source" / "sppa.csv"
ATUS_PATH = PROJECT_ROOT / "data" / "derived" / "atus.csv"
LTT_OR_WEEKLY_PATH = PROJECT_ROOT / "data" / "derived" / "ltt_or_weekly.csv"
ATUS_SOURCE_DIR = PROJECT_ROOT / "data" / "source" / "atus"
ATUS_AVG_HRS_READING_PATH = (
    ATUS_SOURCE_DIR
    / "TUU10101AA01006315 Avg hrs per day - Reading for personal interest.csv"
)
ATUS_AVG_HRS_LEISURE_PARTICIPANTS_PATH = (
    ATUS_SOURCE_DIR
    / "TUU20101AA01013585 Avg hrs per day for participants - Leisure and sports (includes travel).csv"
)


def _odds(percent: float) -> float:
    p = percent / 100
    return p / (1 - p)


def _read(path: Path) -> list[dict[str, str]]:
    with path.open() as f:
        return list(csv.DictReader(f))


def _sppa_rows(category: str) -> list[tuple[int, float]]:
    rows = []
    for row in _read(SPPA_PATH):
        if row["Read in the last year"] != category:
            continue
        percent = row["Percent"]
        if not percent:
            continue
        rows.append((int(row["Year"]), float(percent)))
    rows.sort(key=lambda r: r[0])
    return rows


def _atus_rows(activity: str) -> list[tuple[int, float]]:
    rows = []
    for row in _read(ATUS_PATH):
        if row["Activity"] != activity:
            continue
        percent = row["Percent"]
        if not percent:
            continue
        rows.append((int(row["Year"]), float(percent)))
    rows.sort(key=lambda r: r[0])
    return rows


def _atus_estimate_rows(path: Path) -> list[tuple[int, float]]:
    """Read a raw BLS ATUS CSV (Year,Period,Estimate,Standard Error).

    Skips suppressed rows (the BLS marks these as "-(M)" or similar).
    """
    rows = []
    for row in _read(path):
        estimate = (row.get("Estimate") or "").strip()
        try:
            value = float(estimate)
        except ValueError:
            continue
        rows.append((int(row["Year"]), value))
    rows.sort(key=lambda r: r[0])
    return rows


def sentence_any_book_nonreaders() -> str:
    rows = _sppa_rows("Any book")
    year, percent = rows[-1]
    nonreaders = 100 - percent
    return (
        'Sentence: 52% of US adults have not read any book in the preceding year.\n'
        f'  Computed: {nonreaders:.1f}%  '
        f'(SPPA "Any book", {year}: {percent}% read → 100−{percent})'
    )


def sentence_atus_nonreaders() -> str:
    rows = _atus_rows("Reading for personal interest")
    year, percent = rows[-1]
    nonreaders = 100 - percent
    return (
        'Sentence: 84% of US adults do not read anything for personal interest on '
        'an average day, including the news.\n'
        f'  Computed: {nonreaders:.1f}%  '
        f'(ATUS "Reading for personal interest", {year}: {percent}% → 100−{percent})'
    )


def sentence_atus_or_2003() -> str:
    rows = dict(_atus_rows("Reading for personal interest"))
    baseline_year = 2003
    latest_year = max(rows)
    baseline_odds = _odds(rows[baseline_year])
    latest_odds = _odds(rows[latest_year])
    odds_ratio = latest_odds / baseline_odds
    lower_pct = (1 - odds_ratio) * 100
    return (
        'Sentence: The odds of US adults reading anything for personal interest on '
        'an average day are 46% lower than they were in 2003.\n'
        f'  Computed: {lower_pct:.1f}% lower  '
        f'(ATUS "Reading for personal interest", '
        f'{baseline_year}: {rows[baseline_year]}% → odds {baseline_odds:.4f}; '
        f'{latest_year}: {rows[latest_year]}% → odds {latest_odds:.4f}; '
        f'OR {odds_ratio:.4f} → 1−OR)'
    )


def sentence_sppa_literature_or_1982() -> str:
    rows = dict(_sppa_rows("Literature"))
    baseline_year = 1982
    latest_year = max(rows)
    baseline_odds = _odds(rows[baseline_year])
    latest_odds = _odds(rows[latest_year])
    odds_ratio = latest_odds / baseline_odds
    lower_pct = (1 - odds_ratio) * 100
    return (
        'Sentence: The odds of US adults reading a novel, short story, poem, or '
        'play in the previous year are 51% lower than they were in 1982.\n'
        f'  Computed: {lower_pct:.1f}% lower  '
        f'(SPPA "Literature", '
        f'{baseline_year}: {rows[baseline_year]}% → odds {baseline_odds:.4f}; '
        f'{latest_year}: {rows[latest_year]}% → odds {latest_odds:.4f}; '
        f'OR {odds_ratio:.4f} → 1−OR)'
    )


def sentence_ltt_age13_or_1984() -> str:
    return _ltt_age_or(
        age=13,
        sentence=(
            'The odds of US thirteen-year-olds reading for fun weekly or '
            'more often are 76% lower than they were in 1984.'
        ),
    )


def _ltt_age_or(age: int, sentence: str) -> str:
    rows = []
    for row in _read(LTT_OR_WEEKLY_PATH):
        if int(row["Age"]) != age:
            continue
        rows.append((int(row["Year"]), float(row["Percent"]), float(row["Odds Ratio"])))
    rows.sort(key=lambda r: r[0])
    baseline_year = rows[0][0]
    latest_year, latest_percent, latest_or = rows[-1]
    lower_pct = (1 - latest_or) * 100
    return (
        f'Sentence: {sentence}\n'
        f'  Computed: {lower_pct:.1f}% lower  '
        f'(LTT "Weekly or more often", age {age}, baselined to {baseline_year} by '
        f'scripts/data/ltt_or_weekly.py; {latest_year}: {latest_percent}%, '
        f'OR {latest_or:.4f} → 1−OR)'
    )


def _sppa_category_or(category: str, baseline_year: int, sentence: str) -> str:
    rows = dict(_sppa_rows(category))
    latest_year = max(rows)
    baseline_odds = _odds(rows[baseline_year])
    latest_odds = _odds(rows[latest_year])
    odds_ratio = latest_odds / baseline_odds
    lower_pct = (1 - odds_ratio) * 100
    return (
        f'Sentence: {sentence}\n'
        f'  Computed: {lower_pct:.1f}% lower  '
        f'(SPPA "{category}", '
        f'{baseline_year}: {rows[baseline_year]}% → odds {baseline_odds:.4f}; '
        f'{latest_year}: {rows[latest_year]}% → odds {latest_odds:.4f}; '
        f'OR {odds_ratio:.4f} → 1−OR)'
    )


def sentence_sppa_novels_poetry_plays_or_1992() -> str:
    sentence = (
        'The odds of reading novels or short stories are 45% lower than they '
        'were in 1992, whereas the odds of reading poetry or plays are down '
        'by 54% and 61%, respectively.'
    )
    baseline_year = 1992
    lines = [f'Sentence: {sentence}', '  Computed:']
    for category in ("Novels or short stories", "Poetry", "Plays"):
        rows = dict(_sppa_rows(category))
        latest_year = max(rows)
        baseline_odds = _odds(rows[baseline_year])
        latest_odds = _odds(rows[latest_year])
        odds_ratio = latest_odds / baseline_odds
        lower_pct = (1 - odds_ratio) * 100
        lines.append(
            f'    {category}: {lower_pct:.1f}% lower  '
            f'({baseline_year}: {rows[baseline_year]}% → odds {baseline_odds:.4f}; '
            f'{latest_year}: {rows[latest_year]}% → odds {latest_odds:.4f}; '
            f'OR {odds_ratio:.4f} → 1−OR)'
        )
    return '\n'.join(lines)


def sentence_sppa_literature_or_1982_v2() -> str:
    return _sppa_category_or(
        "Literature",
        1982,
        'The odds of reading literature in the preceding year are about 51% lower '
        'than they were in 1982.',
    )


def sentence_atus_zero_minutes() -> str:
    rows = _atus_rows("Reading for personal interest")
    year, percent = rows[-1]
    nonreaders = 100 - percent
    return (
        'Sentence: However, this average conceals the fact that 84% of people in '
        'the US read for zero minutes on an average day.\n'
        f'  Computed: {nonreaders:.1f}%  '
        f'(ATUS "Reading for personal interest", {year}: {percent}% participated → 100−{percent})'
    )


def sentence_atus_avg_minutes() -> str:
    rows = dict(_atus_estimate_rows(ATUS_AVG_HRS_READING_PATH))
    year = max(rows)
    hours = rows[year]
    minutes = hours * 60
    return (
        'Sentence: As of 2024, fifteen minutes a day is about the average amount of '
        'time Americans spent reading anything for personal interest on an average '
        'day.\n'
        f'  Computed: {minutes:.1f} minutes/day  '
        f'(ATUS "Avg hrs per day - Reading for personal interest" '
        f'[TUU10101AA01006315], {year}: {hours} hrs × 60)'
    )


def sentence_atus_peak_2004_vs_2024() -> str:
    rows = dict(_atus_rows("Reading for personal interest"))
    p_2004 = rows[2004]
    latest_year = max(rows)
    p_latest = rows[latest_year]
    peak_year = max(rows, key=lambda y: rows[y])
    return (
        'Sentence: In the peak year of 2004, 28% of the US population read for '
        'personal interest on an average day; in 2024, 16% did.\n'
        f'  Computed: 2004 = {p_2004:.1f}%, {latest_year} = {p_latest:.1f}%  '
        f'(ATUS "Reading for personal interest"; peak across series is '
        f'{peak_year} at {rows[peak_year]:.1f}%)'
    )


def sentence_atus_or_2003_v2() -> str:
    rows = dict(_atus_rows("Reading for personal interest"))
    baseline_year = 2003
    latest_year = max(rows)
    baseline_odds = _odds(rows[baseline_year])
    latest_odds = _odds(rows[latest_year])
    odds_ratio = latest_odds / baseline_odds
    lower_pct = (1 - odds_ratio) * 100
    return (
        'Sentence: In 2024, the odds of Americans reading for personal interest '
        'were 46% lower than they were in 2003.\n'
        f'  Computed: {lower_pct:.1f}% lower  '
        f'(ATUS "Reading for personal interest", '
        f'{baseline_year}: {rows[baseline_year]}% → odds {baseline_odds:.4f}; '
        f'{latest_year}: {rows[latest_year]}% → odds {latest_odds:.4f}; '
        f'OR {odds_ratio:.4f} → 1−OR)'
    )


def sentence_leisure_time_change() -> str:
    rows = dict(_atus_estimate_rows(ATUS_AVG_HRS_LEISURE_PARTICIPANTS_PATH))
    baseline_year = 2003
    latest_year = max(rows)
    baseline_hrs = rows[baseline_year]
    latest_hrs = rows[latest_year]
    change_pct = (latest_hrs - baseline_hrs) / baseline_hrs * 100
    return (
        'Sentence: Surprisingly, people in the US reported about 2% more leisure '
        'time in 2024 than in 2003.\n'
        f'  Computed: {change_pct:+.1f}%  '
        f'(ATUS "Avg hrs per day for participants - Leisure and sports (includes travel)" '
        f'[TUU20101AA01013585], {baseline_year}: {baseline_hrs} hrs; '
        f'{latest_year}: {latest_hrs} hrs; (latest−baseline)/baseline)'
    )


def sentence_ltt_age9_or_1984() -> str:
    return _ltt_age_or(
        age=9,
        sentence=(
            'Today, the odds of nine-year-olds reading for fun weekly or more '
            'are 58% lower than they were in 1984.'
        ),
    )


def sentence_ltt_age13_or_1984_v2() -> str:
    return _ltt_age_or(
        age=13,
        sentence=(
            'But the odds of thirteen-year-olds reading for fun weekly or more '
            'are 76% lower.'
        ),
    )


def sentence_ltt_age17_or_1984() -> str:
    return _ltt_age_or(
        age=17,
        sentence='The odds of seventeen-year-olds reading are 63% lower.',
    )


CLAIMS = [
    sentence_any_book_nonreaders,
    sentence_atus_nonreaders,
    sentence_atus_or_2003,
    sentence_sppa_literature_or_1982,
    sentence_ltt_age13_or_1984,
    sentence_sppa_novels_poetry_plays_or_1992,
    sentence_sppa_literature_or_1982_v2,
    sentence_atus_zero_minutes,
    sentence_atus_avg_minutes,
    sentence_atus_peak_2004_vs_2024,
    sentence_atus_or_2003_v2,
    sentence_leisure_time_change,
    sentence_ltt_age9_or_1984,
    sentence_ltt_age13_or_1984_v2,
    sentence_ltt_age17_or_1984,
]


def main() -> None:
    for claim in CLAIMS:
        print(claim())
        print()


if __name__ == "__main__":
    main()
