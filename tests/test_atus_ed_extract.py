import importlib.util

import pandas as pd
import pytest

from conftest import DERIVED, PROJECT_ROOT


def _load_module(name, rel_path):
    spec = importlib.util.spec_from_file_location(name, PROJECT_ROOT / rel_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# scripts/figures/atus_ed.py shadows scripts/data/atus_ed.py on sys.path, so load
# the data-extraction module explicitly by path.
atus_ed = _load_module("atus_ed_data_extract", "scripts/data/atus_ed.py")
ID_VALUE = atus_ed.ID_VALUE
ACTIVITY_VALUE = atus_ed.ACTIVITY_VALUE

SOURCE_ED = PROJECT_ROOT / "data" / "source" / "atus_ed.csv"


def _load_derived_or_skip(path):
    if not path.exists():
        pytest.skip(f"{path} not found — run scripts/data/atus_ed.py first")
    return pd.read_csv(path)


def _source_long():
    """Independent wide->long melt of the source, dropping blank cells."""
    wide = pd.read_csv(SOURCE_ED, encoding="utf-8-sig")
    edu_columns = [c for c in wide.columns if c != "Year"]
    long = wide.melt(
        id_vars="Year",
        value_vars=edu_columns,
        var_name="Educational Attainment",
        value_name="Percent",
    ).dropna(subset=["Year", "Percent"])
    long["Year"] = long["Year"].astype(int)
    return edu_columns, long


def test_atus_ed_applies_constant_id_and_activity():
    df = _load_derived_or_skip(DERIVED / "atus_ed.csv")
    assert (df["ID"] == ID_VALUE).all()
    assert (df["Activity"] == ACTIVITY_VALUE).all()


def test_atus_ed_drops_all_blank_year():
    df = _load_derived_or_skip(DERIVED / "atus_ed.csv")
    # 2020 is blank across every education column in the source → no 2020 rows.
    assert 2020 not in set(df["Year"])


def test_atus_ed_education_columns_match_source_header():
    edu_columns, _ = _source_long()
    df = _load_derived_or_skip(DERIVED / "atus_ed.csv")
    assert set(df["Educational Attainment"]) == set(edu_columns)


def test_atus_ed_long_format_matches_source():
    _, long = _source_long()
    df = _load_derived_or_skip(DERIVED / "atus_ed.csv")
    key = ["Year", "Educational Attainment"]
    merged = df.merge(
        long, on=key, how="outer", suffixes=("_out", "_src"), indicator=True
    )
    # Every source cell appears exactly once in the output and vice versa.
    assert (merged["_merge"] == "both").all()
    assert (merged["Percent_out"] - merged["Percent_src"]).abs().max() < 1e-9


def test_atus_ed_sorted_by_year_then_education_order():
    edu_columns, _ = _source_long()
    order = {name: idx for idx, name in enumerate(edu_columns)}
    df = _load_derived_or_skip(DERIVED / "atus_ed.csv")
    keys = [
        (int(year), order[edu])
        for year, edu in zip(df["Year"], df["Educational Attainment"])
    ]
    assert keys == sorted(keys)
