import pytest

from ltt_extract import parse_txt, tidy


def test_parse_txt_handles_current_naep_layout(tmp_path):
    source = tmp_path / "ltt.txt"
    source.write_text(
        "\n".join(
            [
                "Percentages for age 9 long-term trend reading",
                "Data Table 1",
                "Almost every day\tOnce or twice a week\tNever or hardly ever",
                "Year\tJurisdiction\tPercentage\tPercentage\tPercentage",
                "2025\tNational\t37\t24\t17",
                "2004\tNational\t—\t—\t—",
                "2004¹\tNational\t54\t26\t8",
                "¹ Original assessment format.",
                "NOTE: Some apparent differences between estimates may not be statistically significant.",
            ]
        ),
        encoding="utf-8",
    )

    categories, rows = parse_txt(source)

    assert categories == [
        "Almost every day",
        "Once or twice a week",
        "Never or hardly ever",
    ]
    assert rows == [
        {
            "Year": 2025,
            "Jurisdiction": "National",
            "Almost every day": "37",
            "Once or twice a week": "24",
            "Never or hardly ever": "17",
        },
        {
            "Year": 2004,
            "Jurisdiction": "National",
            "Almost every day": "",
            "Once or twice a week": "",
            "Never or hardly ever": "",
        },
        {
            "Year": 2004,
            "Jurisdiction": "National",
            "Almost every day": "54",
            "Once or twice a week": "26",
            "Never or hardly ever": "8",
        },
    ]


def test_tidy_skips_blank_duplicate_year():
    categories = ["Almost every day"]
    txt_rows = [
        {"Year": 2004, "Jurisdiction": "National", "Almost every day": ""},
        {"Year": 2004, "Jurisdiction": "National", "Almost every day": "54"},
    ]

    rows = tidy(9, categories, txt_rows)

    assert rows == [
        {"Year": 2004, "Age": 9, "Read for Fun": "Almost every day", "Percent": 54.0}
    ]


def test_tidy_raises_when_both_assessment_formats_have_values():
    categories = ["Almost every day"]
    txt_rows = [
        {"Year": 2004, "Jurisdiction": "National", "Almost every day": "50"},
        {"Year": 2004, "Jurisdiction": "National", "Almost every day": "54"},
    ]

    with pytest.raises(ValueError, match="duplicate LTT value"):
        tidy(9, categories, txt_rows)
