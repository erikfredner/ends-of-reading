import csv
import statistics
from itertools import combinations
from pathlib import Path

EDUCATION_ORDER = [
    "Bachelor's degree and higher",
    "Some college or associate degree",
    "High school graduates (no college)",
    "Less than a high school diploma",
]
ACTIVITY = "Reading for personal interest"


def load_odds_ratios(source_path: Path) -> dict[str, dict[int, float]]:
    series: dict[str, dict[int, float]] = {edu: {} for edu in EDUCATION_ORDER}

    with source_path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            activity = (row.get("Activity") or "").strip()
            if activity != ACTIVITY:
                continue

            edu = (row.get("Educational Attainment") or "").strip()
            if edu not in series:
                continue

            year_raw = (row.get("Year") or "").strip()
            or_raw = (row.get("Odds Ratio") or "").strip()
            if not year_raw or not or_raw:
                continue

            try:
                year = int(float(year_raw))
                odds_ratio = float(or_raw)
            except ValueError:
                continue

            series[edu][year] = odds_ratio

    return series


def write_pairwise(
    series: dict[str, dict[int, float]], output_path: Path
) -> list[dict]:
    rows: list[dict] = []
    for edu_a, edu_b in combinations(EDUCATION_ORDER, 2):
        shared_years = sorted(set(series[edu_a]) & set(series[edu_b]))
        values_a = [series[edu_a][y] for y in shared_years]
        values_b = [series[edu_b][y] for y in shared_years]

        pearson_r = statistics.correlation(values_a, values_b)
        mean_abs_diff = statistics.fmean(abs(a - b) for a, b in zip(values_a, values_b))

        rows.append(
            {
                "Group A": edu_a,
                "Group B": edu_b,
                "N Shared Years": len(shared_years),
                "Pearson r": round(pearson_r, 6),
                "Mean Abs Diff": round(mean_abs_diff, 6),
            }
        )

    fieldnames = ["Group A", "Group B", "N Shared Years", "Pearson r", "Mean Abs Diff"]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return rows


def write_spread(series: dict[str, dict[int, float]], output_path: Path) -> list[dict]:
    all_years = sorted(
        {year for group_series in series.values() for year in group_series}
    )

    rows: list[dict] = []
    for year in all_years:
        values = [series[edu][year] for edu in EDUCATION_ORDER if year in series[edu]]
        if len(values) < 2:
            continue

        mean_or = statistics.fmean(values)
        std_or = statistics.stdev(values)
        cv = std_or / mean_or if mean_or != 0 else float("nan")
        range_or = max(values) - min(values)

        rows.append(
            {
                "Year": year,
                "N Groups": len(values),
                "Mean OR": round(mean_or, 6),
                "Std OR": round(std_or, 6),
                "CV": round(cv, 6),
                "Range OR": round(range_or, 6),
            }
        )

    fieldnames = ["Year", "N Groups", "Mean OR", "Std OR", "CV", "Range OR"]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return rows


def write_slopes(series: dict[str, dict[int, float]], output_path: Path) -> list[dict]:
    rows: list[dict] = []
    for edu in EDUCATION_ORDER:
        years_map = series[edu]
        years = sorted(years_map)
        values = [years_map[y] for y in years]

        slope, intercept = statistics.linear_regression(years, values)
        pearson_r_vs_year = statistics.correlation(years, values)

        rows.append(
            {
                "Educational Attainment": edu,
                "N Years": len(years),
                "Slope (OR per year)": round(slope, 6),
                "Intercept": round(intercept, 6),
                "Pearson r vs Year": round(pearson_r_vs_year, 6),
            }
        )

    fieldnames = [
        "Educational Attainment",
        "N Years",
        "Slope (OR per year)",
        "Intercept",
        "Pearson r vs Year",
    ]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return rows


def print_summary(
    pairwise_rows: list[dict],
    spread_rows: list[dict],
    slope_rows: list[dict],
) -> None:
    pearson_rs = [row["Pearson r"] for row in pairwise_rows]
    mean_r = statistics.fmean(pearson_rs)
    min_r = min(pearson_rs)
    min_pair = next(row for row in pairwise_rows if row["Pearson r"] == min_r)

    slopes = [row["Slope (OR per year)"] for row in slope_rows]
    min_slope = min(slopes)
    max_slope = max(slopes)
    slope_ratio = min_slope / max_slope if max_slope != 0 else float("nan")

    widest = max(spread_rows, key=lambda r: r["Range OR"])

    print(f"Activity: {ACTIVITY}")
    print(
        f"Pairwise Pearson r across {len(pairwise_rows)} group pairs: "
        f"mean {mean_r:.3f}, min {min_r:.3f} "
        f"({min_pair['Group A']} vs {min_pair['Group B']})"
    )
    print(
        f"Per-group OLS slopes (OR/year): "
        f"min {min_slope:.4f}, max {max_slope:.4f}, "
        f"ratio min/max {slope_ratio:.3f}"
    )
    print(
        f"Largest cross-group OR range: {widest['Range OR']:.3f} "
        f"in {widest['Year']} (N={widest['N Groups']})"
    )


def main() -> None:
    derived_dir = Path(__file__).resolve().parents[2] / "data" / "derived"
    source_path = derived_dir / "atus_ed_or.csv"

    series = load_odds_ratios(source_path)

    pairwise_rows = write_pairwise(
        series, derived_dir / "atus_ed_or_similarity_pairwise.csv"
    )
    spread_rows = write_spread(series, derived_dir / "atus_ed_or_similarity_spread.csv")
    slope_rows = write_slopes(series, derived_dir / "atus_ed_or_similarity_slopes.csv")

    print_summary(pairwise_rows, spread_rows, slope_rows)


if __name__ == "__main__":
    main()
