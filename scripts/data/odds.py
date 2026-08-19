from typing import Callable, Hashable


def compute_odds(percent: float) -> float:
    probability = percent / 100
    if probability <= 0 or probability >= 1:
        raise ValueError("percent must be between 0 and 100 (exclusive)")
    return probability / (1 - probability)


def add_odds_ratios(
    rows: list[dict],
    key: Callable[[dict], Hashable],
    baseline_year: int | None = None,
    require_common_baseline: bool = False,
) -> list[dict]:
    """Return copies of rows with "Odds" and "Odds Ratio" columns added.

    Rows need "Year" and "Percent" keys; ``key(row)`` identifies the group.
    Each group's odds ratio is baselined to its own earliest year, so every
    series starts at 1.0. Rows whose percent is out of range, or whose group
    has no valid baseline, are dropped.

    ``baseline_year`` pins every group to that year instead, dropping rows from
    earlier years. Use it when the earliest available value is not comparable
    with the rest of the series — the SPPA's 1982 and 1985 poetry figures come
    from a question that asked about reading *or listening to* poetry, so the
    manuscript baselines poetry to 1992. Every group must carry a value for the
    pinned year.

    ``require_common_baseline`` rejects input whose groups do not all share the
    same baseline year. Figures captioned "relative to 2003" or "relative to
    2004" plot several groups on one axis, and a series that happened to be
    missing that first year would otherwise be baselined to a later year and
    silently plotted against a different reference.
    """
    if baseline_year is not None:
        rows = [row for row in rows if row["Year"] >= baseline_year]

    baseline_by_group: dict[Hashable, int] = {}
    for row in rows:
        group = key(row)
        if baseline_year is not None:
            baseline_by_group[group] = baseline_year
        elif group not in baseline_by_group or row["Year"] < baseline_by_group[group]:
            baseline_by_group[group] = row["Year"]

    if require_common_baseline and len(set(baseline_by_group.values())) > 1:
        by_year: dict[int, list[Hashable]] = {}
        for group, year in sorted(baseline_by_group.items(), key=lambda kv: kv[1]):
            by_year.setdefault(year, []).append(group)
        detail = "; ".join(f"{year}: {groups}" for year, groups in by_year.items())
        raise ValueError(f"groups do not share a baseline year — {detail}")

    baseline_odds: dict[Hashable, float] = {}
    for row in rows:
        group = key(row)
        if row["Year"] != baseline_by_group[group]:
            continue
        try:
            baseline_odds[group] = compute_odds(row["Percent"])
        except ValueError:
            continue

    if baseline_year is not None:
        missing = sorted(
            str(group) for group in baseline_by_group if group not in baseline_odds
        )
        if missing:
            raise ValueError(
                f"no usable {baseline_year} value to baseline against for: "
                f"{', '.join(missing)}"
            )

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
