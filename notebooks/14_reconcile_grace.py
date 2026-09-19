"""
PRAAN — GRACE reconciliation
Script: 14_reconcile_grace.py

THE PROBLEM THIS SOLVES
    Two different GRACE results exist in this project and the website
    publishes the one the repository cannot reproduce:

      website / README   : slope -0.898 cm/yr, r = -0.678, p = 0.004
      phase2_summary.txt : slope -0.0104/yr,   r = -0.921, p < 0.001
      committed CSV      : slope -0.0104/yr,   r = -0.921, p < 0.001

    r is scale-invariant, so this is NOT a unit conversion — they are
    different datasets. The website's figures come from the MASCON_CRI run
    in script 11, whose output CSV was never committed.

    A judge who opens outputs/phase2_summary.txt sees numbers that
    contradict the homepage. This script ends that.

HOW TO USE
    1. Run 11_grace_fo_extension.py with Earth Engine authenticated.
       It writes data/processed/grace_mascon_tws_raw.csv.
    2. Run this script.
    3. Commit grace_mascon_tws_raw.csv. Do not skip this — an uncommitted
       input is the whole reason the numbers diverged.

WHAT IT DOES
    - Reads whichever GRACE CSVs exist and regresses each one.
    - Diagnoses the cm-vs-metre question from the magnitudes.
    - Reports which figures the website can legitimately publish.
    - With --apply, rewrites the Layer 1 figures on outputs/PRAAN.html
      and the trend line in outputs/phase2_summary.txt so every surface
      states the same thing.
"""
import pandas as pd, numpy as np, sys, os, re, shutil
from scipy import stats

BASE = r"C:/Users/user/OneDrive/Nasa_2026/PRAAN/"
DATA, OUT = BASE + "data/processed/", BASE + "outputs/"
APPLY = '--apply' in sys.argv

LAND = DATA + 'grace_tws_raw.csv'            # script 01, MASS_GRIDS_V04/LAND
MASCON = DATA + 'grace_mascon_tws_raw.csv'   # script 11, MASCON_CRI


def fit(path, label):
    if not os.path.exists(path):
        print(f'  {label:10s} MISSING  ({os.path.basename(path)})')
        return None
    df = pd.read_csv(path)
    col = 'tws_anomaly'
    s = df.groupby('year')[col].mean().dropna()
    s = s[s.index <= 2017]   # GRACE era only; 6 GRACE-FO points can't carry a trend
    sl, ic, r, p, se = stats.linregress(s.index, s.values)
    rng = s.max() - s.min()
    # A real Bangladesh TWS signal is tens of cm. Values this small are metres.
    unit = 'm' if abs(rng) < 1.0 else 'cm'
    k = 100 if unit == 'm' else 1
    print(f'  {label:10s} n={len(s):2d}  slope={sl*k:+.3f} cm/yr  r={r:+.3f}  '
          f'p={p:.2e}  range={rng*k:.1f} cm  [raw units look like {unit}]')
    return dict(label=label, slope_cm=sl * k, r=r, p=p, unit=unit,
                depth_cm=abs((sl * s.index.max() + ic) - (sl * s.index.min() + ic)) * k,
                n=len(s))


print('=' * 70)
print('GRACE RECONCILIATION')
print('=' * 70)
land, mascon = fit(LAND, 'LAND/CSR'), fit(MASCON, 'MASCON_CRI')

if mascon is None:
    print("""
MASCON output not found. Until you run 11_grace_fo_extension.py and commit
its CSV, the ONLY figures you may publish are the LAND/CSR ones above,
and the product name on the site must say MASS_GRIDS_V04/LAND, not
MASCON_CRI. Publishing -0.898 / r=-0.678 with nothing in the repo behind
it is the single most checkable weakness in this project.
""")
    if land:
        print(f'Publishable now: {land["slope_cm"]:+.3f} cm/yr, r = {land["r"]:+.3f}, '
              f'p < 0.001, depletion {land["depth_cm"]:.0f} cm over 2002-2017')
    sys.exit(0)

use = mascon
print(f"""
Both products present. Publish MASCON_CRI (it is the better product and
what the site already credits), and make sure the CSV is committed.

  slope     {use['slope_cm']:+.3f} cm/yr
  r         {use['r']:+.3f}
  p         {use['p']:.2e}
  depletion {use['depth_cm']:.1f} cm over the fitted period
  units     raw band appears to be {use['unit']}; figures above are cm
""")
if land and abs(land['r'] - mascon['r']) > 0.1:
    print(f"NOTE: the two products disagree on correlation "
          f"(r={land['r']:+.3f} vs {mascon['r']:+.3f}). Say which one you used.\n")

if not APPLY:
    print('Re-run with --apply to write these into PRAAN.html and phase2_summary.txt.')
    sys.exit(0)

# ── APPLY ────────────────────────────────────────────────────
slope_s = f"{use['slope_cm']:.3f}".lstrip('-')
new_val = (f"&minus;{slope_s} cm/yr &nbsp;·&nbsp; "
           f"r = &minus;{abs(use['r']):.3f}, p = {use['p']:.3f}"
           if use['p'] >= 0.001 else
           f"&minus;{slope_s} cm/yr &nbsp;·&nbsp; "
           f"r = &minus;{abs(use['r']):.3f}, p &lt; 0.001")

html = OUT + 'PRAAN.html'
h = open(html, encoding='utf-8').read()
shutil.copy(html, html + '.pre_grace.bak')
old = re.search(r'−0\.898 cm/yr[^<]*', h)
if old:
    h = h.replace(old.group(0), new_val.replace('&minus;', '\u2212').replace('&nbsp;', '\u00a0').replace('&lt;', '<'), 1)
    print('PRAAN.html  trend figures updated')
else:
    print('PRAAN.html  trend string not found - check manually')

h = re.sub(r'(<div class="val">)14 cm(</div>)',
           rf'\g<1>{use["depth_cm"]:.0f} cm\g<2>', h, count=1)
open(html, 'w', encoding='utf-8').write(h)

summ = OUT + 'phase2_summary.txt'
if os.path.exists(summ):
    t = open(summ, encoding='utf-8', errors='replace').read()
    t = re.sub(r'GRACE TWS trend: *[-\d.]+ cm/year',
               f'GRACE TWS trend: {use["slope_cm"]:.3f} cm/year', t)
    t = re.sub(r'r = *[-\d.]+, p [^\n]*',
               f'r = {use["r"]:.3f}, p = {use["p"]:.2e}', t)
    open(summ, 'w', encoding='utf-8').write(t)
    print('phase2_summary.txt  trend line updated')

print('\nDone. Now commit data/processed/grace_mascon_tws_raw.csv.')
