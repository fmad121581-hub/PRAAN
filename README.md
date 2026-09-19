# PRAAN — Early Warning System

**Team Voyagers · BUET Department of Urban & Regional Planning · NASA Space Apps Challenge 2026**

> "Detecting the invisible crisis beneath Bangladesh"

## Live Demo
https://praan-voyagers.netlify.app

## What is PRAAN?

PRAAN bridges satellite hydro-meteorology and urban planning by translating
NASA GRACE/GRACE-FO water-storage anomaly signals into actionable ward-level
absorption stress indices for climate-induced migration planning in Dhaka.

The analytical chain: GRACE TWS anomaly → persistent water-storage depletion
consistent with groundwater stress → agricultural pressure → mobility
scenarios → Dhaka ward absorption stress

## Three-Layer Framework

**Layer 1 — The Signal (Validated)**

NASA GRACE/GRACE-FO reveals persistent water-storage depletion consistent
with groundwater stress in the Barind Tract districts of Rajshahi Division.
CHIRPS rainfall shows no statistically significant linear correlation with
the TWS anomaly (r = −0.266, p = 0.142), so the depletion is not explained by
rainfall variability.

> **Reproducibility note.** Two GRACE extractions exist in this project. The
> committed `data/processed/grace_tws_raw.csv` (`MASS_GRIDS_V04/LAND`, band
> `lwe_thickness_csr`, 2002–2017, 4 districts) gives slope **−0.0104/yr,
> r = −0.921, p < 0.001**. The MASCON_CRI extraction in script 11 reports
> **−0.898 cm/yr, r = −0.678, p = 0.004** but its output CSV is not yet
> committed. Publish only figures the committed data reproduces, and check
> the band units — the raw values (−0.10 to −0.26) are inconsistent with a
> −0.898 cm/yr slope unless they are metres rather than centimetres.

**Layer 2 — The Pressure (Literature-informed)**

Exposed population: 7.17M (Barind Tract districts, rural, agricultural),
from BBS Census 2011 projected to 2026 at 1.21%/yr. Mobility rate anchor:
Khalily et al. 2006/07 monga survey (36%) — a scenario parameter, not a
prediction. Destination: 66% to Dhaka Division (BBS Population Monograph
Vol.06, Table 3.8), of which ~45% to the city corporations. Central Dhaka
City estimate: **766,489 arrivals**.

The GRACE signal is coupled to the mobility rate through an explicit,
bounded elasticity (`05b_grace_coupled_mobility.py`):

```
rate(t) = clip( 0.36 × (D_t / D_ref)^ε , 0.20, 0.50 )
```

where `D_ref` is the fitted deficit during the 2006/07 monga survey — the
period in which the 36% anchor was observed. ε is an assumed scenario
parameter, not an estimate. Ratios are unit-free, so the coupling is
unaffected by the units question above. Under the coupled central case
(ε = 0.15) the estimate rises to 869,208 arrivals; the uncoupled 766,489
remains the published headline.

**Layer 3 — The City (Scenario framework)**

1,078 Dhaka Division wards are scored on an Absorption Stress Index. Wards
with complete BBS 2022 records use four indicators — WorldPop 2020
population density (0.35), JRC GHSL 2020 built-up surface (0.25), JRC flood
risk (0.20), BBS 2022 mean household size (0.20). Wards without a BBS match
use the three-indicator form (0.40 / 0.35 / 0.25) and are mapped but not
ranked. Weights are expert-defined, not fitted.

City-level arrivals are distributed across wards in proportion to
`population × (1 − ASI)` — more arrivals to lower-stress wards, on the
assumption that lower stress indicates spare capacity. This is an
assumption, not an observation; the opposite allocation was also tested (see
below).

Crisis Index = normalised `rank(ASI) × rank(arrivals)`. The rank-product form
means a ward must score highly on **both** local absorption stress and
projected arrival pressure to reach the highest category — a ward that is
merely crowded, or merely receives many arrivals, does not qualify alone.

**Results (61 fully-observed city-corporation wards):**
39 low / 15 moderate / **7 high concern**.

| rank | ward | corporation | Crisis Index |
|---|---|---|---|
| 1 | Rampura Ward No-22 | DNCC | 1.000 |
| 2 | Chak Bazar Ward No-65 | DSCC | 0.874 |
| 3 | Lalbagh Ward No-60 | DSCC | 0.849 |
| 4 | Ramna Ward No-55 | DNCC | 0.818 |
| 5 | Lalbagh Ward No-62 | DSCC | 0.781 |
| 6 | Mirpur Ward No-12 | DNCC | 0.760 |
| 7 | Pallabi Ward No-06 | DNCC | 0.709 |

**Robustness.** Across 625 weight combinations (±10pp on each of the four
indicators, renormalised), the top-ranked ward is unchanged in **90.7%** of
combinations and the top five overlap by **4.2 of 5** on average. Membership
at the boundary of the top 13 is weighting-dependent — the exact set
reproduces in 21.9% of combinations, mean overlap 11.1 of 13 — and should be
read as indicative. Reversing the arrival-allocation rule so that arrivals
are routed toward *more* stressed wards preserves 10 of the 13 top wards.

## Key Limitations — Transparently Stated

- **GRACE spatial resolution.** Mascon solutions resolve roughly 3° (~300 km),
  which exceeds the Barind Tract. In our extraction the four study districts
  differ from one another by at most 0.013 in any year, against a 0.16 range
  over time — they are effectively sampling a single mascon cell. Read the
  signal as a northwest-Bangladesh water-balance trend consistent with
  localised groundwater depletion, not a Barind-specific aquifer measurement.
- GRACE measures total terrestrial water storage. Attribution to groundwater
  is an analytical inference supported by BWDB tube-well records showing
  water-table decline of 0.5–1 m/yr in Rajshahi, not a direct aquifer
  measurement.
- Regression is limited to the GRACE era in the committed data (2002–2017).
  The GRACE-FO extension shows persistence, not trend continuation; 6 points
  are insufficient for an independent trend.
- The 36% mobility rate is a scenario parameter from a 2006/07 *monga*
  survey — a fast-onset income shock applied to a slow-onset groundwater
  trend — not a 2026 prediction. The elasticity coupling it to the GRACE
  signal is assumed, not estimated.
- BBS destination splits reflect general internal migration patterns;
  climate migrants may cluster differently.
- **Ward coverage.** 77 of the 138 GADM ward polygons inside the city
  corporations have no matching BBS 2022 record, largely because GADM splits
  wards into "(Part)" fragments. They are excluded from the ranking rather
  than imputed. An extended 138-ward table is produced with an `observed`
  flag; no imputed ward reaches its top 13.

## Repository Structure

- `notebooks/` — Scripts 01–13: GEE extraction, signal validation, mobility
  model, ASI scoring, sensitivity analysis
- `data/processed/` — All processed CSVs
- `outputs/` — Maps, charts, website HTML, ward scores, sensitivity results

## Scripts

| Script | Purpose |
|---|---|
| 01 | CHIRPS rainfall + MODIS NDVI + GRACE TWS extraction (GEE) |
| 02 | BBS yield anomaly processing |
| 03 | Signal validation — regression + correlation |
| 04 | GRACE trend analysis |
| 05 | Phase 2 mobility pressure model |
| 05b | **Layer 1 → Layer 2 coupling (GRACE deficit drives the mobility rate)** |
| 06–07 | Phase 3 Absorption Stress Index |
| 08 | BBS 2022 ward-level data extraction |
| 09 | Phase 3 update with BBS 2022 |
| 10 | Dedupe, arrival allocation, rank-product Crisis Index |
| 11 | GRACE-FO extension (2002–2024) |
| 12 | GeoJSON export |
| 13 | Sensitivity analysis — ASI weight robustness |

Run order for Phase 3: `10` → `13` (13 reads the deduplicated frame written
by 10, so their ASI normalisation bases cannot drift apart).

## Data Sources

- NASA GRACE/GRACE-FO — Google Earth Engine.
  Script 01 uses `NASA/GRACE/MASS_GRIDS_V04/LAND` (band `lwe_thickness_csr`);
  script 11 uses `NASA/GRACE/MASS_GRIDS_V04/MASCON_CRI` (JPL RL06.3Mv04,
  band `lwe_thickness`). Watkins et al. (2015), Wiese et al. (2016)
- CHIRPS Rainfall v2.0 — `UCSB-CHG/CHIRPS/PENTAD` — Funk et al. (2015)
- WorldPop 2020 — WorldPop Global Project, University of Southampton
- JRC GHSL P2023A — `JRC/GHSL/P2023A/GHS_BUILT_S` — Pesaresi et al. (2023)
- JRC Global Surface Water 1.4 — `JRC/GSW1_4/MonthlyHistory` — Pekel et al. (2016)
- BBS Population and Housing Census 2022 — Urban Area Report (ward indicators)
- BBS Census 2011 — exposed population base, projected to 2026
- BBS Population Monograph Vol.06 (2015), Table 3.8 — destination shares
- OCHA COD-AB Bangladesh 2025 — DNCC/DSCC boundaries
- GADM 4.1 — ward-level boundaries (ADM4)
- Khalily M.A.B., Khandker S.R., Samad H.A. (2006/07). *Seasonal Migration and
  Coping Strategies: The Monga Context in Bangladesh.* World Bank / BRAC

## Challenge

NASA Space Apps Challenge 2026 — "Be An Earth System Trend Detective"
Event: November 14–15, 2026
GEE Project: `project-attempt-dhaka-heat`
