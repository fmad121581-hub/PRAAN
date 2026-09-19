# Pipeline — run order

No `_FIXED` suffixes any more. Superseded versions live in `archive/`.

## Phase 1 — the satellite signal

| # | script | writes |
|---|---|---|
| 01 | `01_gee_chirps_extraction.py` | CHIRPS, MODIS NDVI, GRACE LAND extracts |
| 02 | `02_bbs_yield_processing.py` | `bbs_yield_anomaly.csv` |
| 03 | `03_signal_validation.py` | `validation_results.txt` |
| 04 | `04_grace_analysis.py` | `grace_trend.png` |
| 11 | `11_grace_fo_extension.py` | **`grace_mascon_tws_raw.csv`** — the product the site publishes |
| 11b | `11b_grace_fo_chart.py` | `grace_fo_extended_trend.png` |
| 14 | `14_reconcile_grace.py` | checks every GRACE CSV agrees with the site; `--apply` rewrites the figures |

Run 11 before 14. Layer 1 figures come from MASCON_CRI, not the LAND
product in script 01 — the LAND band is in **metres**, MASCON in **cm**.

## Phase 2 — mobility pressure

| # | script | writes |
|---|---|---|
| 05 | `05_phase2_mobility.py` | `phase2_summary.txt` (fixed 20/36/50% scenarios) |
| 05b | `05b_grace_coupled_mobility.py` | `phase2_coupled_*` — couples the GRACE deficit to the mobility rate |

## Phase 3 — ward ranking

| # | script | writes |
|---|---|---|
| 06 | `06_phase3_absorption.py` | 3-indicator ASI |
| 07 | `07_phase3_part2.py` | `phase3_ward_scores.csv` |
| 08 | `08_bbs_extract.py` | `bbs_2022_ward_final.csv` |
| 09 | `09_phase3_update.py` | `phase3_ward_scores_v2.csv` (4-indicator ASI) |
| 10 | `10_dedupe_and_rank_v1.py` | **`phase3_ward_scores_v3_deduped.csv`** + a `_v1` ranking |
| 15 | `15_dissolve_and_rank.py` | **the published ranking** |
| 12 | `12_export_geojson.py` | ward boundaries for the map |

**13** (`13_sensitivity_v1.py`) is the old sensitivity run. Script 15 does
its own, so you do not normally need it.

### Why both 10 and 15

Script 10 deduplicates (DNCC and DSCC both number wards 1..N, so a
name-based BBS join duplicated 46 wards) and writes
`phase3_ward_scores_v3_deduped.csv`. **Script 15 reads that file**, so 10
must run first.

Script 10 then ranks by joining BBS on ward *name*, which fails for every
GADM "(Part)" fragment and leaves 61 wards. Script 15 dissolves the
fragments and joins on `(city_corp, ward_no)` — how BBS is actually indexed
— giving **75 wards**. Script 10's ranking outputs carry a `_v1` suffix so
they can never overwrite the published ones.

## Minimum rebuild of the published result

```
python 10_dedupe_and_rank_v1.py     # writes the deduped table
python 15_dissolve_and_rank.py      # the published ranking
python 05b_grace_coupled_mobility.py
python 14_reconcile_grace.py
```

Then refresh the map data in `outputs/PRAAN.html`, copy it to
`deploy/index.html`, and upload `deploy/` to Netlify.
