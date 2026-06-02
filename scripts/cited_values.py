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
ATUS_AVG_HRS_READING_PARTICIPANTS_PATH = (
    ATUS_SOURCE_DIR
    / "TUU20101AA01006315 Avg hrs per day for participants - Reading for personal interest.csv"
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
    sentence = (
        f'{round(nonreaders)}% of US adults have not read any book in the preceding year.'
    )
    return (
        f'Sentence: {sentence}\n'
        f'  Computed: {nonreaders:.1f}%  '
        f'(SPPA "Any book", {year}: {percent}% read → 100−{percent})'
    )


def sentence_atus_nonreaders() -> str:
    rows = _atus_rows("Reading for personal interest")
    year, percent = rows[-1]
    nonreaders = 100 - percent
    sentence = (
        f'{round(nonreaders)}% of US adults do not read anything for personal interest on '
        'an average day, including the news.'
    )
    return (
        f'Sentence: {sentence}\n'
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
    sentence = (
        f'The odds of US adults reading anything for personal interest on '
        f'an average day are {round(lower_pct)}% lower than they were in {baseline_year}.'
    )
    return (
        f'Sentence: {sentence}\n'
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
    sentence = (
        f'The odds of US adults reading a novel, short story, poem, or '
        f'play in the previous year are {round(lower_pct)}% lower than they were in {baseline_year}.'
    )
    return (
        f'Sentence: {sentence}\n'
        f'  Computed: {lower_pct:.1f}% lower  '
        f'(SPPA "Literature", '
        f'{baseline_year}: {rows[baseline_year]}% → odds {baseline_odds:.4f}; '
        f'{latest_year}: {rows[latest_year]}% → odds {latest_odds:.4f}; '
        f'OR {odds_ratio:.4f} → 1−OR)'
    )


def sentence_ltt_age13_or_1984() -> str:
    return _ltt_age_or(
        age=13,
        sentence_template=(
            'The odds of US thirteen-year-olds reading for fun weekly or '
            'more often are {pct}% lower than they were in {baseline_year}.'
        ),
    )


def _ltt_age_or(age: int, sentence_template: str) -> str:
    rows = []
    for row in _read(LTT_OR_WEEKLY_PATH):
        if int(row["Age"]) != age:
            continue
        rows.append((int(row["Year"]), float(row["Percent"]), float(row["Odds Ratio"])))
    rows.sort(key=lambda r: r[0])
    baseline_year = rows[0][0]
    latest_year, latest_percent, latest_or = rows[-1]
    lower_pct = (1 - latest_or) * 100
    sentence = sentence_template.format(pct=round(lower_pct), baseline_year=baseline_year)
    return (
        f'Sentence: {sentence}\n'
        f'  Computed: {lower_pct:.1f}% lower  '
        f'(LTT "Weekly or more often", age {age}, baselined to {baseline_year} by '
        f'scripts/data/ltt_or_weekly.py; {latest_year}: {latest_percent}%, '
        f'OR {latest_or:.4f} → 1−OR)'
    )


def _sppa_category_or(category: str, baseline_year: int, sentence_template: str) -> str:
    rows = dict(_sppa_rows(category))
    latest_year = max(rows)
    baseline_odds = _odds(rows[baseline_year])
    latest_odds = _odds(rows[latest_year])
    odds_ratio = latest_odds / baseline_odds
    lower_pct = (1 - odds_ratio) * 100
    sentence = sentence_template.format(pct=round(lower_pct), baseline_year=baseline_year)
    return (
        f'Sentence: {sentence}\n'
        f'  Computed: {lower_pct:.1f}% lower  '
        f'(SPPA "{category}", '
        f'{baseline_year}: {rows[baseline_year]}% → odds {baseline_odds:.4f}; '
        f'{latest_year}: {rows[latest_year]}% → odds {latest_odds:.4f}; '
        f'OR {odds_ratio:.4f} → 1−OR)'
    )


def sentence_sppa_novels_poetry_plays_or_1992() -> str:
    baseline_year = 1992
    categories = ("Novels or short stories", "Poetry", "Plays")
    results = []
    for category in categories:
        rows = dict(_sppa_rows(category))
        latest_year = max(rows)
        baseline_odds = _odds(rows[baseline_year])
        latest_odds = _odds(rows[latest_year])
        odds_ratio = latest_odds / baseline_odds
        lower_pct = (1 - odds_ratio) * 100
        results.append((category, rows, latest_year, baseline_odds, latest_odds, odds_ratio, lower_pct))
    novels_pct = round(results[0][6])
    poetry_pct = round(results[1][6])
    plays_pct = round(results[2][6])
    sentence = (
        f'The odds of reading novels or short stories are {novels_pct}% lower than they '
        f'were in {baseline_year}, whereas the odds of reading poetry or plays are down '
        f'by {poetry_pct}% and {plays_pct}%, respectively.'
    )
    lines = [f'Sentence: {sentence}', '  Computed:']
    for category, rows, latest_year, baseline_odds, latest_odds, odds_ratio, lower_pct in results:
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
        'The odds of reading literature in the preceding year are about {pct}% lower '
        'than they were in {baseline_year}.',
    )


def sentence_atus_zero_minutes() -> str:
    rows = _atus_rows("Reading for personal interest")
    year, percent = rows[-1]
    nonreaders = 100 - percent
    sentence = (
        f'However, this average conceals the fact that {round(nonreaders)}% of people in '
        'the US read for zero minutes on an average day.'
    )
    return (
        f'Sentence: {sentence}\n'
        f'  Computed: {nonreaders:.1f}%  '
        f'(ATUS "Reading for personal interest", {year}: {percent}% participated → 100−{percent})'
    )


def sentence_atus_avg_minutes() -> str:
    rows = dict(_atus_estimate_rows(ATUS_AVG_HRS_READING_PATH))
    year = max(rows)
    hours = rows[year]
    minutes = hours * 60
    sentence = (
        f'As of {year}, {round(minutes)} minutes a day is about the average amount of '
        'time Americans spent reading anything for personal interest on an average '
        'day.'
    )
    return (
        f'Sentence: {sentence}\n'
        f'  Computed: {minutes:.1f} minutes/day  '
        f'(ATUS "Avg hrs per day - Reading for personal interest" '
        f'[TUU10101AA01006315], {year}: {hours} hrs × 60)'
    )


def sentence_atus_avg_minutes_participants() -> str:
    rows = dict(_atus_estimate_rows(ATUS_AVG_HRS_READING_PARTICIPANTS_PATH))
    year = max(rows)
    hours = rows[year]
    minutes = hours * 60
    sentence = f'On average, readers read for {round(minutes)} minutes.'
    return (
        f'Sentence: {sentence}\n'
        f'  Computed: {minutes:.1f} minutes/day  '
        f'(ATUS "Avg hrs per day for participants - Reading for personal interest" '
        f'[TUU20101AA01006315], {year}: {hours} hrs × 60)'
    )


def sentence_atus_peak_2004_vs_2024() -> str:
    rows = dict(_atus_rows("Reading for personal interest"))
    latest_year = max(rows)
    p_latest = rows[latest_year]
    peak_year = max(rows, key=lambda y: rows[y])
    peak_percent = rows[peak_year]
    sentence = (
        f'In the peak year of {peak_year}, {round(peak_percent)}% of the US population read for '
        f'personal interest on an average day; in {latest_year}, {round(p_latest)}% did.'
    )
    return (
        f'Sentence: {sentence}\n'
        f'  Computed: {peak_year} = {peak_percent:.1f}%, {latest_year} = {p_latest:.1f}%  '
        f'(ATUS "Reading for personal interest")'
    )


def sentence_atus_or_2003_v2() -> str:
    rows = dict(_atus_rows("Reading for personal interest"))
    baseline_year = 2003
    latest_year = max(rows)
    baseline_odds = _odds(rows[baseline_year])
    latest_odds = _odds(rows[latest_year])
    odds_ratio = latest_odds / baseline_odds
    lower_pct = (1 - odds_ratio) * 100
    sentence = (
        f'In {latest_year}, the odds of Americans reading for personal interest '
        f'were {round(lower_pct)}% lower than they were in {baseline_year}.'
    )
    return (
        f'Sentence: {sentence}\n'
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
    sentence = (
        f'Surprisingly, people in the US reported about {round(change_pct)}% more leisure '
        f'time in {latest_year} than in {baseline_year}.'
    )
    return (
        f'Sentence: {sentence}\n'
        f'  Computed: {change_pct:+.1f}%  '
        f'(ATUS "Avg hrs per day for participants - Leisure and sports (includes travel)" '
        f'[TUU20101AA01013585], {baseline_year}: {baseline_hrs} hrs; '
        f'{latest_year}: {latest_hrs} hrs; (latest−baseline)/baseline)'
    )


def sentence_ltt_age9_or_1984() -> str:
    return _ltt_age_or(
        age=9,
        sentence_template=(
            'Today, the odds of nine-year-olds reading for fun weekly or more '
            'are {pct}% lower than they were in {baseline_year}.'
        ),
    )


def sentence_ltt_age13_or_1984_v2() -> str:
    return _ltt_age_or(
        age=13,
        sentence_template=(
            'But the odds of thirteen-year-olds reading for fun weekly or more '
            'are {pct}% lower.'
        ),
    )


def sentence_ltt_age17_or_1984() -> str:
    return _ltt_age_or(
        age=17,
        sentence_template='The odds of seventeen-year-olds reading are {pct}% lower.',
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
    sentence_atus_avg_minutes_participants,
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
