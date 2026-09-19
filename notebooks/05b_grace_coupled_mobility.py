"""
PRAAN — Layer 1 → Layer 2 coupling
Script: 05b_grace_coupled_mobility.py

WHY THIS SCRIPT EXISTS
    In 05_phase2_mobility.py the GRACE trend is computed, projected and
    plotted, and then line 145 says:

        # Stress ratio kept for reporting only — not applied as multiplier

    So the mobility scenarios were fixed fractions of the exposed
    population (exactly 0.20 / 0.36 / 0.50) and did not depend on the
    satellite signal at all. If the depletion trend were half as steep the
    arrival numbers would have been identical. That breaks the central
    claim of the project — that a NASA Earth-observation signal drives a
    planning output.

    This script closes the loop with an explicit, bounded elasticity.

THE COUPLING
    rate(t) = clip( RATE_ANCHOR * (D_t / D_ref) ** EPSILON, 0.20, 0.50 )

    D_t     projected absolute TWS deficit in year t (from the fitted trend)
    D_ref   deficit during the 2006/07 monga survey period, the year the
            36% behavioural anchor was actually observed
    EPSILON elasticity of mobility to water-storage deficit

    Ratios are unit-free, so this is robust to the cm/m labelling question
    in the raw GRACE export.

CHOOSING EPSILON — AND WHY IT MUST BE SMALL
    D_2026 / D_2006-07 = 2.31. A proportional response (EPSILON = 1) would
    give 0.36 * 2.31 = 0.83, far beyond any observed mobility rate, and it
    saturates the 0.50 cap for any EPSILON >= 0.4. Mobility does not scale
    linearly with water deficit: irrigation investment, remittances,
    adaptation and alternative livelihoods all damp the response. EPSILON is
    therefore a small, explicitly stated assumption, and it is the honest
    place to put the uncertainty — not a hidden constant.

    EPSILON is NOT estimated from data. It is a scenario parameter. Say so.

OUTPUT
    outputs/phase2_coupled_scenarios.csv
    outputs/phase2_coupled_summary.txt
"""
import pandas as pd, numpy as np
from scipy import stats
import os

DATA = '../data/processed/'
OUT = '../outputs/'

# Set True to make the coupled central case the headline number.
# Leave False to publish the original 0.36 anchor and show coupling alongside.
ADOPT_COUPLED_AS_HEADLINE = False

POP_EXPOSED = 7_168_817
RATE_ANCHOR = 0.36          # Khalily/Khandker/Samad, observed 2006/07
RATE_FLOOR, RATE_CAP = 0.20, 0.50
REF_YEARS = (2006, 2007)    # the monga survey period
TARGET_YEAR = 2026
DHAKA_DIV_SHARE, DHAKA_CITY_SHARE = 0.660, 0.450

EPSILON = {'conservative': 0.05, 'central': 0.15, 'high': 0.35}

# ── 1. GRACE TREND ───────────────────────────────────────────
g = pd.read_csv(DATA + 'grace_tws_raw.csv').groupby('year').tws_anomaly.mean()
slope, icpt, r, p, se = stats.linregress(g.index, g.values)
print(f'GRACE trend: slope={slope:.4f}/yr  r={r:.3f}  p={p:.2e}  n={len(g)}')

deficit = lambda y: abs(slope * y + icpt)
D_ref = np.mean([deficit(y) for y in REF_YEARS])
D_t = deficit(TARGET_YEAR)
ratio = D_t / D_ref
print(f'Deficit {REF_YEARS[0]}/{str(REF_YEARS[1])[2:]} = {D_ref:.4f} | '
      f'{TARGET_YEAR} = {D_t:.4f} | ratio = {ratio:.3f}')

# ── 2. COUPLED RATES AND SCENARIOS ───────────────────────────
rows = []
for name, eps in EPSILON.items():
    rate = float(np.clip(RATE_ANCHOR * ratio ** eps, RATE_FLOOR, RATE_CAP))
    mob = int(POP_EXPOSED * rate)
    arr = int(mob * DHAKA_DIV_SHARE * DHAKA_CITY_SHARE)
    rows.append({'scenario': name, 'epsilon': eps, 'mobility_rate': round(rate, 4),
                 'mobility_total': mob, 'dhaka_city_arrivals': arr,
                 'saturated': rate in (RATE_FLOOR, RATE_CAP)})

cpl = pd.DataFrame(rows)

# uncoupled originals for side-by-side
orig = pd.DataFrame([
    {'scenario': 'conservative', 'mobility_rate': 0.20},
    {'scenario': 'central', 'mobility_rate': 0.36},
    {'scenario': 'high', 'mobility_rate': 0.50}])
orig['mobility_total'] = (orig.mobility_rate * POP_EXPOSED).astype(int)
orig['dhaka_city_arrivals'] = (orig.mobility_total * DHAKA_DIV_SHARE
                               * DHAKA_CITY_SHARE).astype(int)

cmp = cpl.merge(orig, on='scenario', suffixes=('_coupled', '_uncoupled'))
print('\n' + cmp[['scenario', 'epsilon', 'mobility_rate_uncoupled',
                  'mobility_rate_coupled', 'dhaka_city_arrivals_uncoupled',
                  'dhaka_city_arrivals_coupled']].to_string(index=False))

# ── 3. SENSITIVITY OF THE OUTPUT TO THE SIGNAL ───────────────
# The point of coupling: if the trend were different, the answer changes.
# Counterfactual holds the 2002 starting level fixed and varies the slope,
# which is the physically meaningful comparison (same aquifer, different
# rate of depletion). Varying the slope with the fitted intercept held fixed
# instead moves the whole curve and gives a non-monotonic, meaningless result.
BASE_2002 = slope * 2002 + icpt
print('\nResponse of the central case to the satellite trend '
      '(2002 level held fixed):')
for mult, label in [(0.5, 'half the observed slope'), (1.0, 'observed slope'),
                    (1.5, '50% steeper')]:
    cf = lambda y: abs(BASE_2002 + slope * mult * (y - 2002))
    ratio_cf = cf(TARGET_YEAR) / np.mean([cf(y) for y in REF_YEARS])
    rate = float(np.clip(RATE_ANCHOR * ratio_cf ** EPSILON['central'],
                         RATE_FLOOR, RATE_CAP))
    print(f'  {label:22s} -> deficit ratio {ratio_cf:.2f} -> rate {rate:.3f} -> '
          f'{int(POP_EXPOSED*rate*DHAKA_DIV_SHARE*DHAKA_CITY_SHARE):,} arrivals')

os.makedirs(OUT, exist_ok=True)
cmp.to_csv(OUT + 'phase2_coupled_scenarios.csv', index=False)

headline = cpl[cpl.scenario == 'central'].iloc[0] if ADOPT_COUPLED_AS_HEADLINE \
    else orig[orig.scenario == 'central'].iloc[0]

with open(OUT + 'phase2_coupled_summary.txt', 'w') as f:
    f.write(f"""PRAAN Phase 2 — GRACE-coupled mobility scenarios
{'=' * 60}

GRACE trend (committed grace_tws_raw.csv, 2002-2017, n={len(g)}):
  slope = {slope:.4f} per year, r = {r:.3f}, p = {p:.2e}
  NOTE: units follow the raw GEE export; the coupling uses ratios only
  and is therefore unaffected by the cm/m labelling question.

Deficit ratio {TARGET_YEAR} vs {REF_YEARS[0]}/{str(REF_YEARS[1])[2:]}: {ratio:.3f}

Coupling: rate = clip({RATE_ANCHOR} * (D_t/D_ref)^EPSILON, {RATE_FLOOR}, {RATE_CAP})
EPSILON is a scenario parameter, not an estimate.

{cmp[['scenario','epsilon','mobility_rate_uncoupled','mobility_rate_coupled',
      'dhaka_city_arrivals_uncoupled','dhaka_city_arrivals_coupled']].to_string(index=False)}

HEADLINE IN USE: {'coupled' if ADOPT_COUPLED_AS_HEADLINE else 'uncoupled (original 0.36 anchor)'}
  central arrivals = {int(headline.dhaka_city_arrivals):,}

WHY EPSILON IS SMALL
  D_2026/D_ref = {ratio:.2f}. A proportional response (EPSILON=1) implies a
  {RATE_ANCHOR*ratio:.2f} mobility rate, which is not credible, and any
  EPSILON >= 0.4 saturates the {RATE_CAP} cap. Mobility is damped relative to
  water stress by irrigation investment, remittances and adaptation.
""")
print(f"\nWrote {OUT}phase2_coupled_scenarios.csv and phase2_coupled_summary.txt")
print(f"Headline in use: {'COUPLED' if ADOPT_COUPLED_AS_HEADLINE else 'UNCOUPLED (original)'}"
      f" -> central arrivals {int(headline.dhaka_city_arrivals):,}")
