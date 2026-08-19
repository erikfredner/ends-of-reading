# Data Provenance

Data provenance for "The Ends of Reading" for data compiled from federal surveys in `data/source`.

## General notes

- Unless otherwise specified, values in `data/source` are point estimates for nationally-weighted averages reported by federal agencies in published reports and/or datasets.
- Agencies sometimes revise previously published estimates in subsequent reports. In cases where there are discrepancies between published figures across report, I use the most recently published value.
- Missing data typically indicates data not collected. A good example would be independent measurements of novel or play reading in the 1982 and 1985 SPPA. (Poetry was asked about independently; novels and plays were not.)
- Following the general practices of these agencies, values are represented as percentages. That is, a cell value of `1.6` means 1.6%.

## Survey of Public Participation in the Arts (SPPA)

SPPA data (`data/source/sppa.csv`) has the most complex provenance since it appears across multiple reports. With the exception of the most recent data, all of these values have been validated by cross-referencing multiple reports.

The `Source` and `Page` columns indicate the most recent publication of the values in the table. I link to the full version of the reports cited below using their abbreviated names as given in `data/source/sppa.csv`:

- [Who Reads Literature (1990)](https://www.arts.gov/impact/research/publications/who-reads-literature-future-united-states-nation-readers)
- [How Do We Read (2020)](https://www.arts.gov/impact/research/publications/how-do-we-read-lets-count-ways)
- [By All Means, the Arts (2025)](https://www.arts.gov/impact/research/publications/arts-participation-2022-technical-summary-report)
- [Humanities Indicators (2025)](https://www.amacad.org/humanities-indicators/public-life/book-reading-topics)

## ATUS

### National

The American Time Use Survey data on reading for personal interest can be accessed from the BLS using the following Series ID: `TUU30105AA01006315`

<https://data.bls.gov/dataQuery/search>

Other series IDs are prefixed to filenames in `data/source/atus`.

### By education

BLS does not publicize breakouts by education. I thank Michelle Freeman of the BLS, who shared these estimates with me for this essay.

## National Assessment of Education Progress (NAEP) Long-Term Trend (LTT)

The NAEP Data Explorer provides access to the data from the Long-Term Trend
Survey of Student Experiences, specifically the variable "reading for fun on
your own time" (`S003501`).

<https://www.nationsreportcard.gov/ndecore/xplore/ltt>

NAEP revised the assessment after 2004. In the downloaded tables the years collected under the earlier instrument carry a superscript one (`2004¹`); the revised-format years are unmarked. `ltt_extract.py` preserves this distinction as an `Assessment Format` column rather than hard-coding the changeover year, and `ltt_or_weekly.py` uses it to write `ltt_or_weekly_revised.csv`, a copy of the weekly-or-more series restricted to the revised format and baselined to 2008. Comparisons back to 1984 span both formats, and 2004 to 2008 is the largest single step in every age series, so `cited_values.py` reports both readings.
