from typing import Callable, Hashable


def compute_odds(percent: float) -> float:
    probability = percent / 100
    if probability <= 0 or probability >= 1:
        raise ValueError("percent must be between 0 and 100 (exclusive)")
    return probability / (1 - probability)


def add_odds_ratios(
    rows: list[dict], key: Callable[[dict], Hashable]
) -> list[dict]:
    """Return copies of rows with "Odds" and "Odds Ratio" columns added.

    Rows need "Year" and "Percent" keys; ``key(row)`` identifies the group.
    Each group's odds ratio is baselined to its own earliest year. Rows whose
    percent is out of range, or whose group has no valid baseline, are dropped.
    """
    baseline_year: dict[Hashable, int] = {}
    for row in rows:
        group = key(row)
        if group not in baseline_year or row["Year"] < baseline_year[group]:
            baseline_year[group] = row["Year"]

    baseline_odds: dict[Hashable, float] = {}
    for row in rows:
        group = key(row)
        if row["Year"] != baseline_year[group]:
            continue
        try:
            baseline_odds[group] = compute_odds(row["Percent"])
        except ValueError:
            continue

    output_rows = []
    for row in rows:
        group = key(row)
        if group not in baseline_odds:
            continue
        try:
            odds = compute_odds(row["Percent"])
        except ValueError:
            continue
        output_rows.append(
            {
                **row,
                "Odds": round(odds, 6),
                "Odds Ratio": round(odds / baseline_odds[group], 6),
            }
        )
    return output_rows
