# Use of AI in PRAAN

NASA Space Apps asks every team to name each AI tool it used, what it was
used for, the prompts and reasoning behind it, and the data it worked on.
This file is that record.

## Summary

PRAAN itself contains no AI. The deployed site and every number on it come
from deterministic Python scripts in `notebooks/` that read committed CSV
files. No language model computes, estimates or rewrites a statistic, and
the site makes no call to any AI service.

We used two AI tools while building it.

| Tool | Maker | Used for | Extent |
|---|---|---|---|
| Claude (Claude Opus 5 and 5.5, in chat and Claude Code) | Anthropic | Writing and debugging analysis scripts, reviewing statistical methods, building the website, editing documentation | Extensive |
| Perplexity | Perplexity AI | Finding literature and data sources | Light |

## Claude

**What it did**

- Drafted and debugged the Python scripts that extract and analyse the
  data (Google Earth Engine extraction, trend tests, the Absorption Stress
  Index, sensitivity analysis, map export).
- Reviewed our methods and flagged problems. Several entries in
  `CORRECTIONS.md` started this way: a wrong unit label on the GRACE LAND
  band, an allocation rule that ran in the wrong direction, an
  autocorrelation correction that could make p-values smaller instead of
  larger, and claims on the site that went further than the data.
- Built and revised the single-file website (`deploy/index.html`).
- Edited the README, the judge Q&A notes and other documentation.

Commits written with Claude Code carry a `Co-Authored-By: Claude` line, so
the git history shows exactly which changes it touched.

**Examples of the kind of requests we made** (paraphrased)

- "Extract the January to May GRACE MASCON water-storage anomaly for these
  four districts, 2002 to 2024, and save it as a CSV."
- "Replace the OLS trend with Sen's slope and Mann-Kendall, and check the
  residuals for serial correlation."
- "Check every number on the site against the CSVs in `outputs/` and list
  anything that does not match."
- "Does the Absorption Stress Index predict observed ward growth? Test it
  without circularity."

**Data it worked on.** Only open data and our own derived files: GRACE and
GRACE-FO, CHIRPS, MODIS NDVI, GLDAS, WorldPop, JRC GHSL, JRC Global Surface
Water, BBS census tables, and GADM and OCHA boundaries. No personal data.

## Perplexity

Used occasionally to locate papers and official sources, for example
groundwater-decline records for the Barind Tract and migration literature
for the mobility scenario. Every source we cite was opened and read by a
team member; nothing is cited from an AI summary alone.

## What the team did

The team chose the problem and the challenge, decided which datasets and
methods to use, set the study regions, and made the judgement calls about
what to claim and what to leave out. Every AI-written script was run by a
team member, and its output was checked against the committed data before
anything reached the site. Where the AI and the data disagreed, the data
won and the change is logged in `CORRECTIONS.md`.
