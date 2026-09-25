# PRAAN — corrections log

Every number below was recomputed from the CSVs committed in the repo.
Nothing here needs Earth Engine access to reproduce.

---

## 1. Duplicate wards — FIXED

**Cause.** DNCC and DSCC each number their wards from 1, so `NAME_4`
("Ward No-43") is not unique. Merging BBS onto GADM by ward name produced a
cartesian match.

| file | rows | unique wards |
|---|---|---|
| `phase3_ward_scores_v2.csv` | 1,124 | 1,078 |
| `phase3_supply_demand_gap.csv` | 184 | 138 |

The published top 13 contained **10 distinct wards**. Rampura 22, Tejgaon 39
and Mirpur 12 each appeared twice with *different* ASI values — one copy of
each carried the wrong BBS record. Percentile ranks were computed over the
duplicated frame, so every `crisis_index` value was distorted.

**Fix.** The spatial join (ward centroid inside the corporation polygon) is
authoritative. For all 46 duplicated wards, exactly one of the two rows has a
`city_corp` matching the spatial assignment — so the dedupe is unambiguous,
not an arbitrary `keep='first'`.

> A naive `drop_duplicates('GID_4')` picks the **wrong** row for 29 of the 61
> ranked wards. Do not use it.

## 2. Imputed population was being ranked — FIXED

77 of the 138 city-corporation wards have **no BBS match** (mostly GADM
"(Part)" fragments). The old script gave them the **median** population and
the **mean** ASI, then ranked them alongside real data. Over half the ranked
set was imputed.

**Fix.** An `observed` flag, and a primary result restricted to the 61
fully-observed wards. Wards without BBS data now fall back to the
3-indicator ASI (real data) instead of a mean fill. The extended 138-ward
table is still produced, flagged — and reassuringly, no imputed ward reaches
the extended top 13.

## 3. Sensitivity analysis — RE-RUN AND RE-STATED

The old `sensitivity_summary.txt` said, in your own repo:

```
Top-13 unchanged : 1 / 25  (4.0%)
VERDICT: Top 13 changed in 24 combinations
```

while the website said the top 9–12 wards were "consistent" and "robust".
The overlap *count* was 9–12 of 13; that is not rank stability.

The old run also varied the **3-indicator** weights (0.40/0.35/0.25), but
every ranked ward with BBS data uses the **4-indicator** `ASI_updated`
(0.35/0.25/0.20/0.20, including household size). It was testing a formula
that produces none of the published results.

**Corrected run** — 625 combinations, ±10pp on the four real weights,
renormalised, on the deduplicated observed set. *(These are the 61-ward
figures from this round; §7 supersedes them with the 75-ward result, where
top-1 stability rises to 99.7%.)*

| metric | result |
|---|---|
| highest-ranked ward unchanged | **567 / 625 (90.7%)** |
| mean top-5 overlap | **4.2 / 5** |
| mean top-13 overlap | 11.1 / 13 (min 8) |
| exact top-13 set reproduced | 137 / 625 (21.9%) |
| median worst-case rank shift | 6 places |

This is a **better** robustness result than the old one, because the ranked
set is now clean. Say it accurately and it is a strength.

## 4. Layer 1 now drives Layer 2 — NEW SCRIPT

`05_phase2_mobility.py` line 145, your own comment:

```python
# Stress ratio kept for reporting only — not applied as multiplier
```

The scenarios were exactly 20% / 36% / 50% of the exposed population.
1,433,763 / 7,168,817 = 0.2000 exactly. The GRACE trend was computed,
projected, plotted — and never used. If the depletion were half as steep the
arrival numbers would be identical.

`05b_grace_coupled_mobility.py` closes this with an explicit elasticity:

```
rate(t) = clip( 0.36 * (D_t / D_ref)^EPSILON , 0.20, 0.50 )
```

`D_ref` is the deficit during the 2006/07 monga survey — the year the 36%
anchor was actually observed. Ratios are unit-free, so this is immune to the
cm/m question below.

**Why EPSILON must be small:** D(2026)/D(2006–07) = 2.31. A proportional
response implies a 0.83 mobility rate, which is not credible, and any
EPSILON ≥ 0.4 pins the 0.50 cap. Mobility is damped by irrigation
investment, remittances and adaptation. EPSILON is a *scenario parameter*,
not an estimate — say so.

The counterfactual now behaves correctly (2002 level held fixed, slope
varied):

| trend | central arrivals |
|---|---|
| half the observed slope | 835,278 |
| observed slope | 869,208 |
| 50% steeper | 890,128 |

**Decision for you:** `ADOPT_COUPLED_AS_HEADLINE = False` by default, so your
published 766,489 stands and the coupling is shown alongside. Flipping it to
`True` moves the headline to **869,208** and cascades through the site. Your
call — I did not make it for you.

## 5. Allocation rule — DISCLOSED AND TESTED *(superseded by §8)*

Arrivals are distributed as `pop × (1 − ASI)` — *more* arrivals to *less*
stressed wards. This was never stated on the website, and it is arguably
backwards: Dhaka's climate migrants cluster in dense, low-income settlements
(Korail, Sattola, Bhashantek), which are high-ASI.

Tested both ways on the clean 61-ward set: **10 of 13 top wards are shared**.
So the headline survives the assumption — good news, and worth saying out
loud rather than leaving the rule invisible.

> **Superseded.** §8 replaces this. The rule was later tested against
> observed growth rather than only against itself, and the published
> allocation is now population alone.

## 6. Still open — needs your Earth Engine session *(all now closed; see §8)*

At the time of writing, these could not be fixed from the committed data:

- **GRACE stats mismatch.** Website says slope −0.898 cm/yr, r = −0.678,
  p = 0.004. Your `phase2_summary.txt` and the committed `grace_tws_raw.csv`
  both say **−0.0104/yr, r = −0.921, p < 0.001**. r is scale-invariant, so
  this is not a unit conversion — they are different datasets. The website's
  figures come from the MASCON run whose output
  (`grace_mascon_tws_raw.csv`) **is not in the repo**. Commit it.
- **Product mismatch.** Script 01 pulls `MASS_GRIDS_V04/LAND`
  (`lwe_thickness_csr`, CSR, ends 2017); the README credits
  `MASCON_CRI (JPL RL06.3Mv04)`. Pick one and cite it.
- **Units.** Values labelled "cm" throughout, but −0.898 cm/yr and "14 cm"
  only work if the raw band is metres. Check and relabel.
- **Data vintage.** Script 05 uses `POP_2011` grown at 1.21%/yr;
  `phase2_summary.txt` cites Census 2011; the website says Census 2022.
- **GRACE resolution.** Your four districts differ from each other by at most
  0.013 in any year while the temporal range is 0.16 — they are sampling
  essentially one mascon cell. State this as a limitation; it costs nothing
  and pre-empts the sharpest question a hydrology-literate judge can ask.

---

## Headline numbers: before → after

*(The state at the time of the first audit. For what the site publishes
now, see §8.)*

| | published | corrected |
|---|---|---|
| ranked wards | 184 rows / 138 unique | **75** after dissolving fragments |
| distinct wards in top 13 | **10** | 13 |
| high-concern wards | 13 | **5** |
| tier split | 110 / 61 / 13 | **52 / 18 / 5** |
| top ward | Chak Bazar Ward No-65 | **Kafrul Ward No-14** |
| sensitivity claim | "top 9–12 consistent" | top ward stable in 99.7%, top-5 4.2/5 |

---

## Run order

```
python 10_supply_demand_FIXED.py        # dedupe -> crisis index -> map
python 13_sensitivity_analysis_FIXED.py # reads v3_deduped written by 10
python 05b_grace_coupled_mobility.py    # Layer 1 -> Layer 2 coupling
```

Scripts 10 and 13 share `phase3_ward_scores_v3_deduped.csv` so their ASI
normalisation bases cannot drift apart. Both carry asserts that fail loudly
if a duplicate ever reappears.


---

## 7. Ward fragments dissolved — 61 to 75 ranked wards

After the fixes above the ranking still covered only 61 wards, because 77
city-corporation polygons carried no BBS record. The cause was the join key,
not missing data: **BBS 2022 is indexed by `(city_corp, ward_no)`, not by
name**, and GADM 4.1 splits some wards across thana boundaries into
"(Part)" polygons that match no census record by name.

`15_dissolve_and_rank.py` parses the ward number, dissolves the fragments
into whole wards (area-weighting the density and fraction indicators), and
joins on the real key.

*(Figures as they stood after §7; §8d has the current ones.)*

| | before | after |
|---|---|---|
| ranked wards | 61 | **75** |
| tier split | 39 / 15 / 7 | **52 / 18 / 5** |
| top ward | Rampura Ward No-22 | **Kafrul Ward No-14** |
| top-1 sensitivity stability | 90.7% | **99.7%** |
| allocation-rule overlap | 10 / 13 | 9 / 13 |

It also corrected a mislabelling: **DNCC has wards 1–54 only**, so Ward
No-55 can only be DSCC. The name-based join had labelled Ramna Ward No-55
as DNCC while using DSCC's population.

Kafrul Ward No-14 tops the corrected ranking. It holds the largest
population in the city set (196,759) and had been invisible purely because
GADM split it in two.

**Two alternatives for the remaining 44 were tested and rejected**, rather
than imputing population:

- WorldPop density alone correlates **negatively** with census population
  (r = −0.31) — it is a density, not a count
- density × ward area gives rank agreement of only rho = 0.20, with 47%
  median error after calibration

23 of the 44 carry union names with no ward number, and GADM 4.1 predates
the ward expansion, so 55 census wards have no polygon at all. They are
mapped and scored for absorption stress, but not ranked.

---

## 8. The claims were tested against something other than themselves

Everything above fixed the *data handling*. This section is about the
*claims*, and it is the part a judge will care about most, because two of
them did not survive.

### 8a. The trend was tested with the wrong statistic

Every trend in the project used ordinary least squares, which assumes each
year is independent of the last. Water storage is not: the Barind series has
a lag-1 autocorrelation of **+0.724**, so the OLS p-value of 0.0039 is
optimistic.

`18_robust_trends.py` re-runs every published series through Mann-Kendall
with Sen's slope and the Hamed-Rao variance correction for serial
correlation. The headline trend survives: **p = 0.0103, Sen's slope
−0.905 cm/yr**. The site now publishes the stricter number.

### 8b. Only one region was ever examined

The challenge asks for regional contrast; the project showed one region
declining. `16_` and `17_` run the same variable, season and method over
four regions. Three separate cleanly — Barind Tract −0.90 cm/yr (p = 0.004),
coastal southwest −0.57 cm/yr (p = 0.002), northeast haor basin no
significant trend (p = 0.40).

The fourth does not. Haor Basin and Central Floodplain return series
**0.052 cm apart with a correlation of 1.000**: Sylhet and Dhaka sit in one
mascon cell. Bangladesh is ~400 km across, a mascon resolves ~300 km, so the
country supports about three independent samples. Three regions are
reported, and the collapsed pair is published as a measured statement about
instrument resolution rather than quietly dropped.

### 8c. The ASI failed its own validation — and that is now the headline

The Absorption Stress Index had never been checked against anything that
happened. `19_validate_asi.py` extracts observed WorldPop population and
GHSL built-up growth per ward, 2000–2020, over the same boundaries.

The first result looked like a finding: ASI correlates with observed
population growth at **rho = +0.267 (p = 0.020)**, suggesting the old
`pop × (1 − ASI)` rule was backwards and stress attracts arrivals.

It is not usable, and briefly publishing it was itself an error. The ASI's
largest component is present-day density, and a ward is dense today partly
*because* it grew — the outcome is inside the predictor.
`20_predictive_validation.py` rebuilds the index from year-2000 inputs only
(WorldPop 2000, GHSL 2000, plus the two time-invariant components), so
nothing in the predictor can have been caused by the outcome:

| predictor | 2000–2020 | 2000–2010 | 2010–2020 |
|---|---|---|---|
| ASI built from 2000 only | −0.154 (p 0.19) | −0.199 (p 0.09) | −0.119 (p 0.31) |
| population 2000 | −0.132 (p 0.26) | −0.160 (p 0.17) | −0.174 (p 0.14) |
| built-up 2000 | −0.073 (p 0.54) | −0.076 (p 0.52) | −0.124 (p 0.29) |
| flood exposure | −0.206 (p 0.08) | −0.215 (p 0.06) | −0.120 (p 0.31) |
| household size | +0.148 (p 0.20) | +0.128 (p 0.28) | +0.153 (p 0.19) |
| *ASI as published (endogenous)* | *+0.267 (p 0.02)* | *+0.194 (p 0.10)* | *+0.352 (p 0.00)* |

Nothing predicts. Median growth across baseline-stress quartiles is flat
(+105%, +115%, +106%, +106%).

**Conclusion, reported rather than buried:** the ASI describes absorption
stress but carries no demonstrated information about where arrivals land.
Allocation is now `population` alone — the only assumption the data
supports. The ranking is robust to the choice: Kafrul Ward No-14 is first
under population-only, stress-weighted and inverse allocation alike, and 10
of the top 13 are shared.

### 8d. What the published numbers are now

| | previous | current |
|---|---|---|
| allocation rule | `pop × ASI` | **`pop` alone** |
| tier split | 50 / 15 / 10 | **46 / 18 / 11** |
| high-concern wards | 10 | **11** |
| top ward | Kafrul Ward No-14 | Kafrul Ward No-14 *(unchanged)* |
| headline significance | OLS p = 0.0039 | **Mann-Kendall p = 0.0103** |
| tier boundaries | fixed thirds | **Jenks natural breaks** |
| top-1 sensitivity stability | 99.7% | **77.1%** |
| top-13 mean overlap | 10.8 / 13 | **11.6 / 13** |

The sensitivity figures move because they are now computed against the
population-allocated ranking, not because the method changed.

### 8e. Two reproducibility defects fixed at the same time

- Scripts hard-coded `C:/Users/user/OneDrive/...`, so nobody else could run
  them. Project paths now resolve from each script's own location.
- The map data embedded in `outputs/PRAAN.html` was regenerated by hand
  every time the ranking changed, which is how a page ends up disagreeing
  with its own CSVs. `21_build_site_geojson.py` now rebuilds it from the
  committed outputs and mirrors the page to `deploy/index.html`.

---

## 9. One external citation did not check out — FIXED

Every number in sections 1–8 was recomputed from the project's own
committed data. The one claim that was NOT self-computed — the BWDB
tube-well groundwater decline rate used to ground-truth the GRACE
attribution — had never been checked against the paper it names.

**Claim as published:** "BWDB tube-well records showing water-table
decline of 0.5–1 m/yr in Rajshahi."

**What the literature actually says.** Aziz et al. (2015), *Groundwater
Depletion with Expansion of Irrigation in Barind Tract: A Case Study of
Rajshahi District of Bangladesh* (International Journal of Geology,
Agriculture and Environmental Sciences, 3(1)), using BWDB/BMDA
monitoring-well data for 2000–2013, reports a district-average decline of
**0.23 m/yr (dry season) to 0.38 m/yr (wet season)** — roughly half the
published figure. The fastest-depleting upazila in that same study, Tanore,
reaches about 0.62 m/yr. No source was found supporting 0.5–1 m/yr as a
district-wide rate; a judge searching for it would not find it.

**Fix.** Every occurrence (`outputs/PRAAN.html` ×2, `deploy/index.html` ×2,
`JUDGE_QA.md`, `README.md`) now reads "averaging 0.2–0.4 m/yr across
Rajshahi district (2000–2013), and over 0.6 m/yr in the fastest-depleting
upazilas," cited to Aziz et al. (2015), with a matching entry added to the
site's References section. The direction of the claim (BWDB records show a
declining water table, consistent with the GRACE signal) was correct; only
the number was unsupported.

**Lesson for the rest of the citation list.** This was the only claim in the
site that names an external record without a number computed from the
project's own pipeline. Every other cited source (Khalily et al. 2006/07;
GRACE/GRACE-FO, CHIRPS, WorldPop, GHSL, JRC Global Surface Water, BBS
Census 2022, GADM/OCHA) is either a standard, correctly named dataset
citation carrying no invented statistic, or a number reproduced directly
from a committed CSV in this repo (spot-checked here: the "4 of 5 worst
yield years had above-normal rainfall" claim and the "2022 recharge was
transient, back to depleted levels by 2023–24" claim both reproduce exactly
from `data/processed/merged_panel.csv` and `data/processed/grace_regional_tws.csv`).
