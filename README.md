# PRAAN — Early Warning System

**Team Voyagers · BUET Department of Urban & Regional Planning · NASA Space Apps Challenge 2026**

> "Detecting the invisible crisis beneath Bangladesh"

## Live Demo
https://praan-voyagers.netlify.app

## What is PRAAN?

PRAAN bridges satellite hydro-meteorology and urban planning by translating NASA GRACE/GRACE-FO water-storage anomaly signals into actionable ward-level absorption stress indices for climate-induced migration planning in Dhaka.

The analytical chain: GRACE TWS anomaly → persistent water-storage depletion consistent with groundwater stress → agricultural pressure → mobility scenarios → Dhaka ward absorption stress

## Three-Layer Framework

**Layer 1 — The Signal (Validated)**
NASA GRACE/GRACE-FO MASCON_CRI reveals persistent water-storage depletion consistent with groundwater stress in the Barind Tract districts of Rajshahi Division (2002–2024). Linear trend in GRACE TWS-equivalent water height (2002–2017): slope = −0.898 cm/yr, r = −0.678, p = 0.004. CHIRPS rainfall showed no statistically significant linear correlation with the GRACE TWS anomaly over 2002–2017 (r = −0.266, p = 0.142). GRACE-FO (2019–2024) confirms TWS remains 11–16 cm below 2002 baseline — structurally depleted, not recovering.

**Layer 2 — The Pressure (Literature-informed)**
Exposed population: 7.17M (Barind Tract districts, rural, agricultural). Mobility rate anchor: Khalily et al. 2006/07 monga survey (36%) — used as scenario parameter, not prediction. Three scenarios: Low 1.43M / Central 2.58M / High 3.58M. Destination: 66% to Dhaka Division (BBS Population Monograph Vol.06, Table 3.8). Central Dhaka City estimate: 766,489 arrivals.

**Layer 3 — The City (Scenario framework)**
1,078 Dhaka Division wards scored on Absorption Stress Index: WorldPop 2020 (0.40) + JRC GHSL 2020 (0.35) + JRC flood risk (0.25). Crisis Index = rank(ASI) × rank(arrivals), normalized 0–1. We use a rank-product formulation so that wards must score highly on both local absorption stress AND projected arrival pressure to reach the highest concern category — a ward that is merely crowded, or merely receives many arrivals, does not qualify alone. Results: 110 low / 61 moderate / 13 high concern wards. Top ward: Chak Bazar Ward No-65 (Crisis Index 1.000). Sensitivity analysis: top 9–12 wards consistent across ±10pp weight variations.

## Key Limitations — Transparently Stated

- GRACE measures total terrestrial water storage — attribution to groundwater is an analytical inference supported by BWDB tube-well records showing water-table decline of 0.5–1 m/yr in Rajshahi, not a direct aquifer measurement
- The Barind Tract districts show ~14 cm of persistent TWS-equivalent depletion relative to the 2002 baseline — the groundwater interpretation is supported but not directly proven by GRACE alone
- Regression limited to 2002–2017 (GRACE era only) — 6 GRACE-FO points are insufficient for trend analysis; the extended period shows persistence, not trend continuation
- 36% mobility rate is a scenario parameter from 2006/07 — not a 2026 prediction
- BBS destination split reflects general internal migration patterns — climate migrants may cluster differently

## Repository Structure

- notebooks/ — Scripts 01–13: GEE extraction, signal validation, mobility model, ASI scoring, sensitivity analysis
- data/processed/ — All processed CSVs
- outputs/ — Maps, charts, website HTML, sensitivity results

## Scripts

| Script | Purpose |
|---|---|
| 01 | CHIRPS rainfall + MODIS NDVI + GRACE TWS extraction (GEE) |
| 02 | BBS yield anomaly processing |
| 03 | Signal validation — regression + correlation |
| 04 | GRACE trend analysis |
| 05 | Phase 2 mobility pressure model |
| 06–07 | Phase 3 Absorption Stress Index |
| 08 | BBS 2022 ward-level data extraction |
| 09 | Phase 3 update with BBS 2022 |
| 10 | Supply-demand gap / Crisis Index |
| 11 | GRACE-FO extension (2002–2024) |
| 13 | Sensitivity analysis — ASI weight robustness |

## Data Sources

- NASA GRACE/GRACE-FO MASCON_CRI (JPL RL06.3Mv04) — NASA/GRACE/MASS_GRIDS_V04/MASCON_CRI — Google Earth Engine
- CHIRPS Rainfall v2.0 — UCSB-CHG/CHIRPS/PENTAD — Google Earth Engine
- WorldPop 2020 — Google Earth Engine
- JRC GHSL P2023A — JRC/GHSL/P2023A/GHS_BUILT_S — Google Earth Engine
- JRC Global Surface Water 1.4 — JRC/GSW1_4/MonthlyHistory — Google Earth Engine
- BBS Population and Housing Census 2022 — Urban Area Report
- BBS Population Monograph Vol.06 (2015) — Table 3.8
- OCHA COD-AB Bangladesh 2025 — DNCC/DSCC boundaries
- GADM 4.1 — Ward-level boundaries

## Challenge

NASA Space Apps Challenge 2026 — "Be An Earth System Trend Detective"
Event: November 14–15, 2026
GEE Project: project-attempt-dhaka-heat
