"""Recompute values cited in the manuscript from the latest data.

Run as ``python scripts/cited_values.py``. Each block prints one manuscript
sentence followed by the value recomputed from the current CSVs, with the
data source and arithmetic shown in parentheses for spot-checking.

Odds ratios are read from the committed ``data/derived/*_or.csv`` rather than
recomputed here, so every odds-ratio sentence in the manuscript goes through
the same ``scripts/data/odds.py`` derivation that
``tests/test_odds_ratio_outputs.py`` verifies.
"""
from __future__ import annotations

import csv
import math
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

SPPA_OR_PATH = PROJECT_ROOT / "data" / "derived" / "sppa_or.csv"
ATUS_PATH = PROJECT_ROOT / "data" / "derived" / "atus.csv"
ATUS_OR_PATH = PROJECT_ROOT / "data" / "derived" / "atus_or.csv"
LTT_OR_WEEKLY_PATH = PROJECT_ROOT / "data" / "derived" / "ltt_or_weekly.csv"
ATUS_SOURCE_DIR = PROJECT_ROOT / "data" / "source" / "atus"
# Raw BLS ATUS dumps; filenames are bare series ids (see _atus_estimate_rows).
ATUS_AVG_HRS_READING_PATH = ATUS_SOURCE_DIR / "TUU10101AA01006315.txt"
ATUS_AVG_HRS_READING_PARTICIPANTS_PATH = ATUS_SOURCE_DIR / "TUU20101AA01006315.txt"
ATUS_AVG_HRS_LEISURE_PARTICIPANTS_PATH = ATUS_SOURCE_DIR / "TUU20101AA01013585.txt"

READING = "Reading for personal interest"


def _round(value: float) -> int:
    """Round half away from zero, the convention the manuscript's prose uses.

    Builtin ``round`` is banker's rounding, so exact halves go to the nearest
    even integer: it renders the seventeen-year-old LTT decline (exactly 62.5%)
    as 62 while the manuscript prints 63.
    """
    return int(Decimal(repr(value)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _read(path: Path) -> list[dict[str, str]]:
    with path.open() as f:
        return list(csv.DictReader(f))


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
    """Read a raw BLS ATUS dump (metadata header + Year,Period,Estimate,...).

    The dumps carry a metadata header block; skip to the ``Year,`` line before
    parsing. Suppressed rows (BLS marks these "-(M)" or similar) are skipped.
    """
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    header_idx = next((i for i, line in enumerate(lines) if line.startswith("Year,")), None)
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
        if math.isnan(value):
            continue
        rows.append((year, value))
    rows.sort(key=lambda r: r[0])
    return rows


def _decline(path: Path, group_col: str, group: str) -> dict:
    """Decline in the odds for one group of a derived ``*_or.csv``.

    The group's baseline year is whichever year the derivation baselined it to,
    i.e. the earliest year present in its output rows, where its odds ratio is
    1.0 by construction.
    """
    rows = [row for row in _read(path) if row[group_col] == group]
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
        f'({source}, '
        f'{d["baseline_year"]}: {d["baseline_percent"]}% → odds {d["baseline_odds"]:.4f}; '
        f'{d["latest_year"]}: {d["latest_percent"]}% → odds {d["latest_odds"]:.4f}; '
        f'OR {d["odds_ratio"]:.4f} → 1−OR)'
    )


def _sppa_decline(category: str) -> dict:
    return _decline(SPPA_OR_PATH, "Read in the last year", category)


def _sppa_or_sentence(category: str, sentence_template: str) -> str:
    d = _sppa_decline(category)
    sentence = sentence_template.format(
        pct=_round(d["lower_pct"]), baseline_year=d["baseline_year"]
    )
    return (
        f'Sentence: {sentence}\n'
        f'  Computed: {d["lower_pct"]:.1f}% lower  '
        + _arithmetic(f'SPPA "{category}"', d)
    )


def _atus_reading_decline() -> dict:
    return _decline(ATUS_OR_PATH, "Activity", READING)


def sentence_atus_nonreaders() -> str:
    rows = _atus_rows(READING)
    year, percent = rows[-1]
    nonreaders = 100 - percent
    sentence = (
        f'{_round(nonreaders)}% of US adults do not read anything for personal interest on '
        'an average day, including the news.'
    )
    return (
        f'Sentence: {sentence}\n'
        f'  Computed: {nonreaders:.1f}%  '
        f'(ATUS "{READING}", {year}: {percent}% → 100−{percent})'
    )


def sentence_atus_or_2003() -> str:
    d = _atus_reading_decline()
    sentence = (
        f'The odds of US adults reading anything for personal interest on '
        f'an average day are {_round(d["lower_pct"])}% lower than they were in '
        f'{d["baseline_year"]}.'
    )
    return (
        f'Sentence: {sentence}\n'
        f'  Computed: {d["lower_pct"]:.1f}% lower  '
        + _arithmetic(f'ATUS "{READING}"', d)
    )


def sentence_sppa_literature_or_1982() -> str:
    return _sppa_or_sentence(
        "Literature",
        'The odds of US adults reading a novel, short story, poem, or play in the '
        'previous year are {pct}% lower than they were in {baseline_year}.',
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
    d = _decline(LTT_OR_WEEKLY_PATH, "Age", str(age))
    sentence = sentence_template.format(
        pct=_round(d["lower_pct"]),
        baseline_year=d["baseline_year"],
        latest_year=d["latest_year"],
    )
    return (
        f'Sentence: {sentence}\n'
        f'  Computed: {d["lower_pct"]:.1f}% lower  '
        + _arithmetic(f'LTT "Weekly or more often", age {age}', d)
    )


def sentence_sppa_novels_poetry_plays_or_1992() -> str:
    categories = ("Novels or short stories", "Poetry", "Plays")
    declines = [_sppa_decline(category) for category in categories]
    baseline_year = declines[0]["baseline_year"]
    latest_year = declines[0]["latest_year"]
    novels_pct, poetry_pct, plays_pct = (_round(d["lower_pct"]) for d in declines)
    sentence = (
        f'The odds of reading novels or short stories in {latest_year} are '
        f'{novels_pct}% lower than they were in {baseline_year}, whereas the odds of '
        f'reading poetry or plays are down by {poetry_pct}% and {plays_pct}%, '
        f'respectively.'
    )
    lines = [f'Sentence: {sentence}', '  Computed:']
    for category, d in zip(categories, declines):
        lines.append(
            f'    {category}: {d["lower_pct"]:.1f}% lower  ' + _arithmetic("SPPA", d)
        )
    return '\n'.join(lines)


def sentence_sppa_literature_or_1982_v2() -> str:
    return _sppa_or_sentence(
        "Literature",
        'The odds of reading literature in the preceding year are about {pct}% lower '
        'than they were in {baseline_year}.',
    )


def sentence_sppa_any_book_nonreaders() -> str:
    d = _sppa_decline("Any book")
    nonreaders = 100 - d["latest_percent"]
    sentence = (
        f'In {d["latest_year"]}, {_round(nonreaders)}% of US adults had not read any '
        'book in the preceding year.'
    )
    return (
        f'Sentence: {sentence}\n'
        f'  Computed: {nonreaders:.1f}%  '
        f'(SPPA "Any book", {d["latest_year"]}: {d["latest_percent"]}% read '
        f'→ 100−{d["latest_percent"]})'
    )


def sentence_atus_zero_minutes() -> str:
    rows = _atus_rows(READING)
    year, percent = rows[-1]
    nonreaders = 100 - percent
    sentence = (
        f'However, this average conceals the fact that {_round(nonreaders)}% of people in '
        'the US read for zero minutes on an average day.'
    )
    return (
        f'Sentence: {sentence}\n'
        f'  Computed: {nonreaders:.1f}%  '
        f'(ATUS "{READING}", {year}: {percent}% participated → 100−{percent})'
    )


def sentence_atus_avg_minutes() -> str:
    rows = dict(_atus_estimate_rows(ATUS_AVG_HRS_READING_PATH))
    year = max(rows)
    hours = rows[year]
    minutes = hours * 60
    sentence = (
        f'As of {year}, {_round(minutes)} minutes a day is about the average amount of '
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
    sentence = f'On average, readers read for {_round(minutes)} minutes.'
    return (
        f'Sentence: {sentence}\n'
        f'  Computed: {minutes:.1f} minutes/day  '
        f'(ATUS "Avg hrs per day for participants - Reading for personal interest" '
        f'[TUU20101AA01006315], {year}: {hours} hrs × 60)'
    )


def sentence_atus_peak_2004_vs_latest() -> str:
    rows = dict(_atus_rows(READING))
    latest_year = max(rows)
    p_latest = rows[latest_year]
    peak_year = max(rows, key=lambda y: rows[y])
    peak_percent = rows[peak_year]
    sentence = (
        f'In the peak year of {peak_year}, {_round(peak_percent)}% of the US population '
        f'read for personal interest on an average day; in {latest_year}, '
        f'{_round(p_latest)}% did.'
    )
    return (
        f'Sentence: {sentence}\n'
        f'  Computed: {peak_year} = {peak_percent:.1f}%, {latest_year} = {p_latest:.1f}%  '
        f'(ATUS "{READING}")'
    )


def sentence_atus_or_2003_v2() -> str:
    d = _atus_reading_decline()
    sentence = (
        f'In {d["latest_year"]}, the odds of Americans reading for personal interest '
        f'were {_round(d["lower_pct"])}% lower than they were in {d["baseline_year"]}.'
    )
    return (
        f'Sentence: {sentence}\n'
        f'  Computed: {d["lower_pct"]:.1f}% lower  '
        + _arithmetic(f'ATUS "{READING}"', d)
    )


def sentence_leisure_time_change() -> str:
    rows = dict(_atus_estimate_rows(ATUS_AVG_HRS_LEISURE_PARTICIPANTS_PATH))
    baseline_year = 2003
    latest_year = max(rows)
    baseline_hrs = rows[baseline_year]
    latest_hrs = rows[latest_year]
    change_pct = (latest_hrs - baseline_hrs) / baseline_hrs * 100
    sentence = (
        f'Surprisingly, people in the US reported about {_round(change_pct)}% more leisure '
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
            'In {latest_year}, the odds of nine-year-olds reading for fun weekly or '
            'more are {pct}% lower than they were in {baseline_year}.'
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
    sentence_sppa_any_book_nonreaders,
    sentence_atus_nonreaders,
    sentence_atus_or_2003,
    sentence_sppa_literature_or_1982,
    sentence_ltt_age13_or_1984,
    sentence_sppa_novels_poetry_plays_or_1992,
    sentence_sppa_literature_or_1982_v2,
    sentence_atus_zero_minutes,
    sentence_atus_avg_minutes,
    sentence_atus_avg_minutes_participants,
    sentence_atus_peak_2004_vs_latest,
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
