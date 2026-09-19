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
renormalised, on the deduplicated observed set:

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

## 5. Allocation rule — DISCLOSED AND TESTED

Arrivals are distributed as `pop × (1 − ASI)` — *more* arrivals to *less*
stressed wards. This was never stated on the website, and it is arguably
backwards: Dhaka's climate migrants cluster in dense, low-income settlements
(Korail, Sattola, Bhashantek), which are high-ASI.

Tested both ways on the clean 61-ward set: **10 of 13 top wards are shared**.
So the headline survives the assumption — good news, and worth saying out
loud rather than leaving the rule invisible.

## 6. Still open — needs your Earth Engine session

I could not fix these from the committed data:

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

| | published | corrected |
|---|---|---|
| ranked wards | 184 rows / 138 unique | **61 fully observed** (138 extended) |
| distinct wards in top 13 | **10** | 13 |
| high-concern wards | 13 | **7** (primary) / 6 (extended) |
| tier split | 110 / 61 / 13 | **39 / 15 / 7** |
| top ward | Chak Bazar Ward No-65 | **Rampura Ward No-22** |
| sensitivity claim | "top 9–12 consistent" | top ward stable in 90.7%, top-5 4.2/5 |

**Corrected high-concern wards (7):** Rampura 22 (DNCC), Chak Bazar 65
(DSCC), Lalbagh 60 (DSCC), Ramna 55 (DNCC), Lalbagh 62 (DSCC), Mirpur 12
(DNCC), Pallabi 06 (DNCC).

7 of the 13 previously published wards survive into the corrected top 13.

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
