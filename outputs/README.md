# outputs/ — which file is which

## Current results — cite these

| file | what it is |
|---|---|
| `crisis_index_primary.csv` | **The published result.** 61 city-corporation wards with complete BBS 2022 records. 39 low / 15 moderate / 7 high concern. Top ward: Rampura Ward No-22. |
| `crisis_index_extended.csv` | All 138 city-corporation wards, with an `observed` flag. 77 have no BBS match and imputed population — shown for completeness, not ranked in the headline. |
| `crisis_index_altallocation.csv` | The same 61 wards with arrivals routed toward *more* stressed wards instead. Robustness check: 10 of 13 top wards unchanged. |
| `phase3_ward_scores_v3_deduped.csv` | Deduplicated ward table (1,078 unique wards) that scripts 10 and 13 share. |
| `sensitivity_results.csv` / `sensitivity_summary.txt` | 625 weight combinations, ±10pp on the four ASI indicators. Top ward stable in 90.7%. |
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
