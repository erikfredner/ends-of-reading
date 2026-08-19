import importlib.util
import io

import pandas as pd
import pytest

from conftest import DERIVED, PROJECT_ROOT


def _load_module(name, rel_path):
    spec = importlib.util.spec_from_file_location(name, PROJECT_ROOT / rel_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# scripts/figures/atus.py shadows scripts/data/atus.py on sys.path (conftest puts
# scripts/figures first), so load the data-extraction module explicitly by path.
atus = _load_module("atus_data_extract", "scripts/data/atus.py")
parse_series_file = atus.parse_series_file
PARTICIPATION_ID_PREFIX = atus.PARTICIPATION_ID_PREFIX

SOURCE_ATUS = PROJECT_ROOT / "data" / "source" / "atus"

# A trimmed copy of a real BLS dump: metadata header, blank lines, the CSV
# header, and a "-(M)" data-suppressed row (2020) that cleaning must drop.
SERIES_DUMP = """\
 Data extracted on: June 25, 2026 (10:10:24 AM)

American Time Use


Series Id:        TUU30105AA01006315

Not seasonally adjusted
Series Title:     Percent participating on an avg day - Reading for personal interest
Type of estimate: Percent of population engaged in activity on an average day
Activity:         Reading for personal interest
Type of Days:     All days
Age Group:        15 years and over


Year,Period,Estimate,Standard Error
2003,Annual,26.3,0.33
2020,Annual,-(M),-(M)
2025,Annual,16.1,0.53
"""


def _write(tmp_path, stem, text, encoding="utf-8"):
    path = tmp_path / f"{stem}.txt"
    path.write_text(text, encoding=encoding)
    return path


# --- parse_series_file: extraction of id / activity / CSV body ---


def test_parse_series_file_extracts_id_activity_and_body(tmp_path):
    path = _write(tmp_path, "TUU30105AA01006315", SERIES_DUMP)
    id_part, activity, data_lines = parse_series_file(path)

    assert id_part == "TUU30105AA01006315"
    assert activity == "Reading for personal interest"
    # Body begins exactly at the CSV header; the metadata block is excluded.
    assert data_lines[0] == "Year,Period,Estimate,Standard Error"
    assert not any(line.startswith("Series Id") for line in data_lines)
    assert data_lines[1:] == [
        "2003,Annual,26.3,0.33",
        "2020,Annual,-(M),-(M)",
        "2025,Annual,16.1,0.53",
    ]


def test_parse_series_file_strips_utf8_bom(tmp_path):
    # BLS dumps are UTF-8 with a BOM; reading as utf-8-sig must strip it so the
    # leading metadata line and the "Year," header are still detected.
    path = _write(tmp_path, "TUU30105AA01006315", "﻿" + SERIES_DUMP)
    _, activity, data_lines = parse_series_file(path)

    assert activity == "Reading for personal interest"
    assert data_lines[0].startswith("Year,")


def test_parse_series_file_id_is_filename_stem(tmp_path):
    # The series id is taken from the filename, not the "Series Id:" line.
    path = _write(tmp_path, "TUU20101AA01013585", SERIES_DUMP)
    id_part, _, _ = parse_series_file(path)
    assert id_part == "TUU20101AA01013585"


def test_parse_series_file_without_year_header_returns_empty(tmp_path):
    text = (
        "Series Id:        TUU30105AA01006315\n"
        "Activity:         Reading for personal interest\n"
    )
    path = _write(tmp_path, "TUU30105AA01006315", text)
    _, activity, data_lines = parse_series_file(path)

    assert activity == "Reading for personal interest"
    assert data_lines == []


def test_parse_series_file_missing_activity_is_empty_string(tmp_path):
    text = (
        "Series Id:        TUU30105AA01006315\n"
        "Year,Period,Estimate,Standard Error\n"
        "2003,Annual,26.3,0.33\n"
    )
    path = _write(tmp_path, "TUU30105AA01006315", text)
    _, activity, data_lines = parse_series_file(path)

    assert activity == ""
    assert data_lines[0].startswith("Year,")


# --- main()'s row cleaning, verified through data/derived/atus.csv ---


def _load_derived_or_skip(path):
    if not path.exists():
        pytest.skip(f"{path} not found — run scripts/data/atus.py first")
    return pd.read_csv(path)


def _rederive_from_source():
    """Re-derive atus.csv straight from the raw dumps, independently of main().

    Uses pandas to coerce the Estimate column to numeric and drop the resulting
    NaNs (blank cells and the "-(M)" suppression marker), so a regression in
    main()'s hand-rolled csv filtering surfaces as a mismatch here.
    """
    records = []
    for txt in sorted(SOURCE_ATUS.glob(f"{PARTICIPATION_ID_PREFIX}*.txt")):
        id_part, activity, data_lines = parse_series_file(txt)
        body = pd.read_csv(io.StringIO("\n".join(data_lines)))
        body["Estimate"] = pd.to_numeric(body["Estimate"], errors="coerce")
        body = body.dropna(subset=["Year", "Estimate"])
        for _, r in body.iterrows():
            records.append(
                {
                    "Year": int(r["Year"]),
                    "ID": id_part,
                    "Activity": activity,
                    "Percent": float(r["Estimate"]),
                }
            )
    return (
        pd.DataFrame(records, columns=["Year", "ID", "Activity", "Percent"])
        .sort_values(["Year", "ID"])
        .reset_index(drop=True)
    )


def test_atus_csv_only_contains_participation_series():
    df = _load_derived_or_skip(DERIVED / "atus.csv")
    assert df["ID"].str.startswith(PARTICIPATION_ID_PREFIX).all()
    # The non-participation dumps in data/source/atus (TUU10101*, TUU20101*)
    # must be excluded by the glob, even though they share the activity label.
    assert not df["ID"].str.match(r"TUU(10101|20101)").any()


def test_atus_csv_drops_suppressed_value_rows():
    df = _load_derived_or_skip(DERIVED / "atus.csv")
    # 2020 is "-(M)" (suppressed) for every series, so no 2020 rows survive.
    assert 2020 not in set(df["Year"])
    # Every surviving Percent is a real (non-NaN) float.
    assert pd.api.types.is_float_dtype(df["Percent"])
    assert df["Percent"].notna().all()


def test_atus_csv_is_sorted_by_year_then_id():
    df = _load_derived_or_skip(DERIVED / "atus.csv")
    keys = list(zip(df["Year"], df["ID"]))
    assert keys == sorted(keys)


def test_atus_csv_matches_independent_rederivation():
    df = (
        _load_derived_or_skip(DERIVED / "atus.csv")
        .sort_values(["Year", "ID"])
        .reset_index(drop=True)
    )
    expected = _rederive_from_source()
    pd.testing.assert_frame_equal(df[["Year", "ID", "Activity", "Percent"]], expected)
