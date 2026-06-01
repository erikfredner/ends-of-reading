# Data

Data provenance for "The Ends of Reading."

The files assembled in `data/source/` are transformed into the tidy CSVs in `data/derived/` by the `.py` scripts under `scripts/data/`.

## CSVs

- Unless otherwise specified, CSVs in `data/derived/` are point estimates for nationally-weighted averages reported by agencies.
- Blanks represent data that was not collected. A good example would be independent measurements of novel or play readers in the SPPA in 1982 and 1985 in `data/source/sppa.csv`
- Following the general practices of these agencies, values are represented as percentages (i.e., a cell value of `1.6` means 1.6%, not 160%).

## SPPA

Most SPPA data was collected from the National Archive of Data on Arts and Culture:

<https://www.icpsr.umich.edu/sites/nadac/home>

Sunil Iyengar, the Research & Analysis Director at the National Endowment for the Arts, shared estimates for a few values (such as the combined "literature" category) that did not appear in every published report.

<https://www.arts.gov/impact/research/publications?f%5B0%5D=publications_arts_quadrant%3A556>

## ATUS

### National

The American Time Use Survey data on reading for personal interest can be accessed from the BLS using the following Series ID: `TUU30105AA01006315`

<https://data.bls.gov/dataQuery/search>

Other series IDs are prefixed to filenames in `data/source/atus`.

### By education

BLS does not publicize breakouts by education. I thank Michelle Freeman of the BLS, who shared these estimates with me for this essay.

## LTT

The NAEP Data Explorer provides access to the data from the Long-Term Trend
Survey of Student Experiences, specifically the variable "reading for fun on
your own time" (`S003501`). I retrieved data for all available years for each
age group in the national jurisdiction.

<https://www.nationsreportcard.gov/ndecore/xplore/ltt>
