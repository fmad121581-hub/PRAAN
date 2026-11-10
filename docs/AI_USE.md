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
| Claude (Claude Opus 5, Opus 5.5 and Fable 5.2, in chat and Claude Code) | Anthropic | Helping write and debug analysis scripts and website code, reviewing statistical methods, reviewing documentation | Extensive |
| Perplexity | Perplexity AI | Finding literature and data sources | Light |

## Claude

**What it did**

- Helped write and debug, from our instructions, the Python scripts that
  extract and analyse the data (Google Earth Engine extraction, trend tests,
  the Absorption Stress Index, sensitivity analysis, map export).
- Reviewed our methods and flagged problems. Several entries in
  `CORRECTIONS.md` started this way: a wrong unit label on the GRACE LAND
  band, an allocation rule that ran in the wrong direction, an
  autocorrelation correction that could make p-values smaller instead of
  larger, and claims on the site that went further than the data.
- Helped build and revise the single-file website (`deploy/index.html`).
- Helped edit the README, the judge Q&A notes and other documentation.

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

Our team independently conceptualized, designed, and developed PRAAN. We
selected the research problem, defined the study areas, identified the
datasets, established the analytical framework, made decisions regarding
statistical methods, conducted the data analysis, and interpreted the
findings. All major research decisions, methodological choices, and final
conclusions were made by the team.

AI tools were used as supporting assistants during development. Working
from our instructions, they helped us write and debug the analysis scripts
and the website code, identify and correct coding errors, understand which datasets were
required and how to access them, review analytical methods, and critically
evaluate the project's strengths, weaknesses, and limitations from the
perspective of a NASA Space Apps evaluator. AI also assisted in reviewing
documentation and suggesting improvements.

The AI tools did not independently determine our research direction, make
final methodological decisions, or establish our conclusions. Our team
remained responsible for implementing the analysis, verifying outputs
against the source data, evaluating suggestions, and deciding what was
ultimately included in PRAAN. AI served as a supportive resource; the
project's research, development decisions, and final outcomes belong to our
team.
