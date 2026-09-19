# Website copy — exact replacements

Find-and-replace list for `outputs/PRAAN.html` (the Netlify site). Left =
what's there now, right = what to put. Nothing here is cosmetic; each one
closes a gap a judge can open.

---

### 1. Hero stat tiles

| now | replace with |
|---|---|
| `13` / "High-concern wards" | `7` / "High-concern wards" |

Keep `14 cm`, `766K` and `2002–2024` **only after** you have reconciled the
GRACE numbers (see §6). If you cannot commit the MASCON CSV before the
event, change `14 cm` and the Layer 1 statistics to the values your
committed data actually supports.

---

### 2. Layer 3 — ward counts

**Now**
> Results: 110 low / 61 moderate / 13 high concern wards. Top ward: Chak Bazar Ward No-65 (Crisis Index 1.000).

**Replace with**
> Scored on 61 Dhaka city-corporation wards with complete BBS 2022 records: 39 low / 15 moderate / 7 high concern. Top ward: Rampura Ward No-22 (Crisis Index 1.000). A further 77 GADM ward fragments fall inside the city corporations but have no BBS match; they are mapped but not ranked, because ranking them would require imputing their population.

---

### 3. Layer 3 — the sensitivity sentence (highest priority)

**Now**
> A sensitivity analysis varying weights by ±10 percentage points shows the top 9–12 wards are consistent across weight combinations — the highest-concern areas are robust, though the precise boundary of the 13th ward varies with weighting assumptions.

**Replace with**
> A sensitivity analysis across 625 weight combinations (±10pp on each of the four ASI indicators, renormalised) shows the highest-concern wards are robust: the top-ranked ward is unchanged in 90.7% of combinations and the top five overlap by 4.2 of 5 on average. Membership at the boundary of the top 13 is weighting-dependent — the exact set reproduces in 21.9% of combinations, with a mean overlap of 11.1 of 13 — and should be read as indicative rather than fixed.

This is the single most important edit on the page. Your own
`sensitivity_summary.txt` currently contradicts the old sentence in plain
language, and it sits in a public repo.

---

### 4. Layer 3 — ASI weights (currently wrong)

**Now**
> WorldPop 2020 (weight 0.40) + JRC GHSL 2020 (0.35) + JRC flood risk (0.25)

Every ranked ward actually uses the **four**-indicator ASI. Replace with:

> Wards with complete BBS 2022 records are scored on four indicators: WorldPop 2020 population density (0.35), JRC GHSL 2020 built-up surface (0.25), JRC flood risk (0.20) and BBS 2022 mean household size (0.20). Wards without a BBS match use the three-indicator form (0.40 / 0.35 / 0.25) and are mapped but not ranked. Weights are expert-defined, not fitted.

---

### 5. Layer 3 — the allocation rule (currently missing entirely)

Add this immediately before the Crisis Index formula. It is the "how?" that
the page never answers:

> **How arrivals reach individual wards.** The city-level arrival estimate is distributed across wards in proportion to `population × (1 − ASI)` — more arrivals are routed to wards with lower absorption stress, on the assumption that lower stress indicates spare capacity. This is an assumption, not an observation: Dhaka's low-income in-migrants have historically clustered in dense, high-stress settlements, which would imply the opposite allocation. We tested both directions; 10 of the 13 highest-concern wards are the same under either rule, so the headline result does not depend on this choice.

---

### 6. Layer 1 — GRACE statistics

Do not publish `−0.898 cm/yr, r = −0.678, p = 0.004` until
`grace_mascon_tws_raw.csv` is committed and reproduces it. Right now the only
GRACE data in the repo gives `−0.0104/yr, r = −0.921, p < 0.001`, and your own
`phase2_summary.txt` states those figures — so the site and the repo disagree.

Whichever you publish, the product name must match the code. Script 01 pulls
`MASS_GRIDS_V04/LAND` (band `lwe_thickness_csr`); the page credits
`MASCON_CRI (JPL RL06.3Mv04)`. And check the band units — a −0.898 cm/yr
slope is inconsistent with raw values of −0.10 to −0.26 unless those are
metres.

---

### 7. Limitations — three additions

Add to the existing limitations list:

> - **GRACE spatial resolution.** Mascon solutions resolve roughly 3° (~300 km), which exceeds the Barind Tract. In our extraction the four study districts differ from one another by at most 0.013 in any year, against a 0.16 range over time — they are effectively sampling a single mascon cell. The signal should therefore be read as a northwest-Bangladesh water-balance trend consistent with localised groundwater depletion, not as a Barind-specific aquifer measurement.
> - **Mobility scenarios are behavioural, not hydrological.** The 36% anchor comes from a *monga* (seasonal food-insecurity) survey, a fast-onset income shock, applied here to a slow-onset groundwater trend. The coupling between the satellite signal and the mobility rate uses an elasticity that is an assumed scenario parameter, not an estimated one.
> - **Ward coverage.** 77 of 138 GADM ward polygons inside the city corporations have no matching BBS 2022 record, largely because GADM splits wards into "(Part)" fragments. These are excluded from the ranking rather than imputed.

---

### 8. Methodology panel — Layer 2 epistemic label

**Now**
> Layer 2 · Literature-informed — ... Three scenario bounds (20%–36%–50%)

**Replace with**
> Layer 2 · Literature-informed — Exposed population: BBS Census 2011 projected to 2026 at 1.21%/yr · Mobility rate: Khalily et al. 2006/07 monga survey, coupled to the GRACE deficit through an assumed elasticity · Destination: BBS Population Monograph Vol.06 · Scenario bounds bracketed by the elasticity assumption

(If you keep the uncoupled headline, say "reported alongside a
GRACE-coupled variant" rather than implying the headline is coupled.)

Note the page currently says exposed population comes from **BBS Census
2022**; script 05 uses **2011** projected forward. Fix whichever is wrong.

---

### 9. Add the team

The page says only "Team Voyagers". Add member names and one-line roles.
Judges consistently reward knowing who did what.
