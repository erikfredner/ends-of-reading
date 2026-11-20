# Data Provenance

Data for "The Ends of Reading" compiled from federal surveys in `data/source`.

## General notes

- Unless otherwise specified, values in `data/source` are point estimates for nationally-weighted averages reported by federal agencies in published reports and/or datasets.
- Agencies sometimes revise previously published estimates in subsequent reports. In cases where there are discrepancies between published figures across reports, I use the most recently published value.
- Missing data typically indicates data not collected. A good example would be independent measurements of novel or play reading in the 1982 and 1985 SPPA. (Poetry was asked about independently; novels and plays were not.)
- Following the general practices of these agencies, values are represented as percentages. That is, a cell value of `1.6` means 1.6%.

## Survey of Public Participation in the Arts (SPPA)

SPPA data (`data/source/sppa.csv`) has the most complex provenance since it appears across multiple reports. With the exception of the most recent data for which there is only a single report, all of these values have been validated by cross-referencing multiple reports.

The `Source` and `Page` columns indicate the most recent publication of the values in the table. I link to the full version of the reports cited below using their abbreviated names as given in `data/source/sppa.csv`:

- [Who Reads Literature (1990)](https://www.arts.gov/impact/research/publications/who-reads-literature-future-united-states-nation-readers)
- [How Do We Read (2020)](https://www.arts.gov/impact/research/publications/how-do-we-read-lets-count-ways)
- [By All Means, the Arts (2025)](https://www.arts.gov/impact/research/publications/arts-participation-2022-technical-summary-report)
- [Humanities Indicators (2025)](https://www.amacad.org/humanities-indicators/public-life/book-reading-topics)

The values for reading literature taken from the Humanities Indicators project at the American Academy of Arts & Sciences match those that appeared in previous NEA's reports. I cite Humanities Indicators because it also has the 2022 value for reading literature.

## ATUS

### National

The American Time Use Survey data on reading for personal interest can be accessed from the BLS using the following Series ID: `TUU30105AA01006315`

<https://data.bls.gov/series-report>

Series IDs are indicated in filenames in `data/source/atus`. Each BLS series-report
file records its own extraction date in its first line.

Time-use series beginning `TUU10101` contain average hours per day across the
population, including nonparticipants; `TUU20101` contains average hours among
participants. These are hours, not percentages. The manuscript's change in leisure
time uses the population-average series `TUU10101AA01013585`: 5.11 hours in 2003
and 5.16 in 2025, a change of `(5.16 / 5.11 - 1) * 100 = +0.98%`.

`atus/TUU10101AA01013585.txt` was retrieved on September 14, 2026 from the
[BLS public API](https://api.bls.gov/publicAPI/v2/timeseries/data/TUU10101AA01013585),
requesting 2003–2012, 2013–2022, and 2023–2025. It is a normalized transcription of
the API's year, period, and value fields, with no rounding or imputed observations.
The unavailable 2020 annual estimate remains `-` (BLS footnote M).

Full national ATUS datasets retain observations through 2025. Publication figures
and cited-value calculations use the same 2025 endpoint, set in `scripts/publication.py`.

### By education

BLS does not publicize breakouts by education. I thank Michelle Freeman of the BLS, who shared these estimates with me.
I received the estimates in `atus_ed.csv` in September 2023.
Its values are percent participating on an average day in reading for personal interest,
by educational attainment, as BLS supplied them.

## National Assessment of Education Progress (NAEP) Long-Term Trend (LTT)

The NAEP Data Explorer provides access to the data from the Long-Term Trend
Survey of Student Experiences, specifically the variable "reading for fun on
your own time" (`S003501`).

<https://www.nationsreportcard.gov/ndecore/xplore/ltt>

Each file in `data/source/ltt/` is one Data Explorer table export, named by age
(`9.txt`, `13.txt`, `17.txt`), with these settings: subject Long-Term Trend reading;
variable `S003501`; jurisdiction National; statistic Percentages; all available
years. The files are saved as exported, including NAEP's header, notes, and source
line. `9.txt` and `17.txt` were last updated in this repository on June 10, 2026,
and `13.txt` on September 14, 2026.

The refreshed `ltt/13.txt` release includes 2023: 14% read almost every day and
22% once or twice a week, totaling 36% weekly or more often. Both weekly
derivations and Figure 5 include this observation.

NAEP revised the assessment after 2004. The manuscript's LTT odds ratios are
therefore baselined to 2008, the first revised-format year
(`derived/ltt_or_weekly_revised.csv`); the 1984-baselined series
(`derived/ltt_or_weekly.csv`) spans the change.
