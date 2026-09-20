# outputs/ — which file is which

## How these were produced

```
python 10_dedupe_and_rank_v1.py    # writes the deduped table script 15 reads
python 15_dissolve_and_rank.py     # the published Phase 3 result (75 wards)
python 05b_grace_coupled_mobility.py
python 14_reconcile_grace.py       # checks Layer 1 figures against the data
python 20_predictive_validation.py # re-checks the arrival-allocation rule
python 21_build_site_geojson.py    # rebuilds the map data inside PRAAN.html
```

Script 10 must run first: script 15 reads the file it writes. Script 10's own
ranking outputs carry a `_v1` suffix so they cannot overwrite the published
ones. Script 13 is the earlier standalone sensitivity run; script 15 does its
own, so you do not normally need it.

## Current results — cite these

| file | what it is |
|---|---|
| `crisis_index_primary.csv` | **The published result.** 75 city-corporation wards with complete BBS 2022 records, after GADM "(Part)" fragments are dissolved into whole wards. 46 low / 18 moderate / 11 high concern, tier boundaries from Jenks natural breaks. Arrivals allocated on population alone. Top ward: Kafrul Ward No-14. |
| `crisis_index_extended.csv` | All 119 city-corporation wards after dissolving, with an `observed` flag. 44 have no BBS match — shown for completeness, not ranked in the headline. |
| `crisis_index_altallocation.csv` | The same 75 wards under the old `pop × (1 − ASI)` rule. Robustness check: 10 of the 13 top wards unchanged, same ward first. |
| `predictive_validation.txt` / `.png` | **Why allocation is population-only.** A stress index rebuilt from year-2000 inputs predicts no subsequent growth in any window (rho = −0.154, p = 0.19 for 2000–2020). The published ASI appears to correlate (+0.267, p = 0.020) only because present-day density is partly a result of that growth. |
| `asi_validation.txt` / `.png` | The raw ASI-vs-observed-growth correlations, and why they cannot settle the allocation rule on their own. Re-runs offline from `ward_observed_growth.csv`; pass `--refresh` to re-extract from Earth Engine. |
| `robust_trend_stats.csv` / `robust_trend_summary.txt` | Every published trend re-tested with Mann-Kendall, Sen's slope and the Hamed-Rao correction for serial correlation. The headline Barind trend survives: p = 0.0103. |
| `regional_trend_comparison.png` / `regional_trend_summary.txt` | The same variable over four regions. Three separate cleanly; the northeast and central series are 0.052 cm apart — one mascon cell, reported as such. |
| `phase3_ward_scores_v4_dissolved.csv` | Ward table after dissolving fragments (1,059 wards). The input to the published ranking. |
| `phase3_ward_scores_v3_deduped.csv` | Deduplicated table before dissolving (1,078 wards). Input to script 15. |
| `sensitivity_results.csv` / `sensitivity_summary.txt` | 625 weight combinations, ±10pp on the four ASI indicators. Top ward stable in 77.1%, mean top-13 overlap 11.6 of 13. |
| `phase2_coupled_scenarios.csv` / `phase2_coupled_summary.txt` | GRACE deficit coupled to the mobility rate through an explicit elasticity. |
| `phase3_gap_map.png` | Crisis Index map, corrected. |
| `grace_fo_extended_trend.png` | GRACE + GRACE-FO trend, MASCON_CRI. |
| `phase2_summary.txt` | Phase 2 mobility summary, MASCON figures. |
| `validation_results.txt` | CHIRPS / NDVI correlation against the TWS anomaly. |
| `PRAAN.html` | The website source (published copy lives in `../deploy/index.html`). |

## Superseded — do not cite

| file | why it is kept |
|---|---|
| `phase3_supply_demand_gap.csv` | The original ranking. 184 rows for 138 wards: DNCC and DSCC both number wards 1..N, so a name-based BBS merge duplicated 46 wards, three of them inside the top 13. Percentile ranks were computed over the duplicated frame. Kept for provenance; `crisis_index_primary.csv` replaces it. |
| `phase3_ward_scores.csv` | Earlier 3-indicator ASI, before BBS 2022 household size was added. |
| `phase3_asi_map.png`, `phase3_asi_map_v2.png` | ASI maps drawn from the duplicated frame. |

`phase3_ward_scores_v2.csv` is an **input**, not a result: it still carries the
1,124 duplicated rows by design, and `10_supply_demand.py` deduplicates it
using the spatial join before anything is ranked.

See `../CORRECTIONS.md` for the full account of what was wrong and how it
was fixed.
