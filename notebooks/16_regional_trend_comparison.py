"""
PRAAN — regional trend comparison
Script: 16_regional_trend_comparison.py

WHY THIS EXISTS
    The challenge statement says, in its own words:

        "a variable can trend one way in one region and the opposite way in
         another, even when the same process drives both"

    PRAAN currently shows ONE region declining. That answers "what, where,
    how much, is it significant" for the Barind Tract, but it does not
    answer the regional-contrast question the challenge actually poses.

    This script extracts the SAME variable (GRACE/GRACE-FO MASCON_CRI
    terrestrial water storage, pre-Aman Jan–May) for four contrasting
    regions of Bangladesh and tests each trend separately.

    Expected contrast: the Barind Tract is irrigation-depleted, while the
    northeastern haor basin receives among the highest rainfall in the
    country and stores water at the surface. If the trends differ in sign
    or magnitude, that is the challenge's question answered with data.

HONESTY CHECK BUILT IN
    GRACE mascons resolve roughly 3 degrees (~300 km). Bangladesh is only
    about 400 km across, so these regions may fall inside the SAME mascon
    cell — in which case their "different" trends would be an artefact,
    not a finding. The script therefore reports, for every pair of
    regions, how much their series actually differ and how strongly they
    correlate. If two regions return near-identical series, say so; that
    is itself a real result about what GRACE can and cannot resolve at
    this scale, and it is the honest answer to the sharpest question a
    judge can ask.

OUTPUT
    data/processed/grace_regional_tws.csv
    outputs/regional_trend_comparison.png
    outputs/regional_trend_summary.txt
"""
import ee, pandas as pd, numpy as np, itertools, time, os
from scipy import stats
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt

ee.Initialize(project='project-attempt-dhaka-heat')

DATA, OUT = '../data/processed/', '../outputs/'
START, END = 2002, 2024

# GAUL ADM2 names. Verified against the dataset below before extraction —
# script 01 silently lost a district to a name mismatch, so we check first.
REGIONS = {
    'Barind Tract (NW)':      ['Rajshahi', 'Naogaon', 'Natore', 'Nawabganj'],
    'Haor Basin (NE)':        ['Sylhet', 'Sunamganj', 'Habiganj', 'Maulvibazar'],
    'Coastal South (SW)':     ['Khulna', 'Satkhira', 'Bagerhat'],
    'Central Floodplain':     ['Dhaka', 'Gazipur', 'Narayanganj', 'Manikganj'],
}
COLORS = {'Barind Tract (NW)': '#f85149', 'Haor Basin (NE)': '#3fb950',
          'Coastal South (SW)': '#58a6ff', 'Central Floodplain': '#ffa657'}

gaul = (ee.FeatureCollection('FAO/GAUL/2015/level2')
        .filter(ee.Filter.eq('ADM0_NAME', 'Bangladesh')))
available = set(gaul.aggregate_array('ADM2_NAME').getInfo())

print('=' * 70)
print('REGION NAME CHECK')
print('=' * 70)
for r, ds in REGIONS.items():
    miss = [d for d in ds if d not in available]
    print(f'  {r:24s} {len(ds)-len(miss)}/{len(ds)} matched'
          + (f'   MISSING: {miss}' if miss else ''))
if any(d not in available for ds in REGIONS.values() for d in ds):
    print('\nGAUL district names available:')
    print('  ' + ', '.join(sorted(available)))
    raise SystemExit('Fix the district names above before extracting.')

mascon = ee.ImageCollection('NASA/GRACE/MASS_GRIDS_V04/MASCON_CRI').select('lwe_thickness')

rows = []
for region, districts in REGIONS.items():
    geom = gaul.filter(ee.Filter.inList('ADM2_NAME', districts)).geometry()
    print(f'\nExtracting {region} ...')
    for year in range(START, END + 1):
        try:
            col = mascon.filterDate(ee.Date.fromYMD(year, 1, 1),
                                    ee.Date.fromYMD(year, 5, 31))
            n = col.size().getInfo()
            if n == 0:
                rows.append({'region': region, 'year': year, 'tws': np.nan, 'n_images': 0})
                continue
            v = col.mean().reduceRegion(reducer=ee.Reducer.mean(), geometry=geom,
                                        scale=55000, maxPixels=1e9,
                                        bestEffort=True).getInfo().get('lwe_thickness')
            rows.append({'region': region, 'year': year, 'tws': v, 'n_images': n})
            time.sleep(0.2)
        except Exception as e:
            print(f'  {year} failed: {e}')
            rows.append({'region': region, 'year': year, 'tws': np.nan, 'n_images': 0})
    print(f'  done ({sum(1 for r in rows if r["region"]==region and pd.notna(r["tws"]))} years)')

df = pd.DataFrame(rows)
os.makedirs(DATA, exist_ok=True)
df.to_csv(DATA + 'grace_regional_tws.csv', index=False)

# ── TRENDS ───────────────────────────────────────────────────
res = []
for region in REGIONS:
    s = df[(df.region == region)].dropna(subset=['tws'])
    for label, sub in [('2002-2017', s[s.year <= 2017]), ('2002-2024', s)]:
        if len(sub) < 4:
            continue
        sl, ic, r, p, se = stats.linregress(sub.year, sub.tws)
        res.append({'region': region, 'period': label, 'n': len(sub),
                    'slope_cm_yr': sl, 'r': r, 'p': p,
                    'significant': p < 0.05,
                    'mean_tws': sub.tws.mean()})
rt = pd.DataFrame(res)

print('\n' + '=' * 78)
print('TREND BY REGION — same variable, same period, same method')
print('=' * 78)
print(rt.to_string(index=False, float_format=lambda x: f'{x:.4f}'))

# ── CAN GRACE ACTUALLY TELL THESE REGIONS APART? ─────────────
print('\n' + '=' * 78)
print('RESOLUTION CHECK — are these regions distinguishable, or one mascon cell?')
print('=' * 78)
piv = df.pivot(index='year', columns='region', values='tws').dropna()
pairs = []
for a, b in itertools.combinations(REGIONS, 2):
    diff = (piv[a] - piv[b]).abs().mean()
    corr = piv[a].corr(piv[b])
    pairs.append({'pair': f'{a} vs {b}', 'mean_abs_diff_cm': diff, 'correlation': corr})
pp = pd.DataFrame(pairs)
print(pp.to_string(index=False, float_format=lambda x: f'{x:.3f}'))
spread = piv.std(axis=1).mean()
overall = piv.stack().std()
print(f'\n  mean spread BETWEEN regions in a year : {spread:.2f} cm')
print(f'  overall variability of the series     : {overall:.2f} cm')
ratio = spread / overall
print(f'  ratio                                 : {ratio:.2f}')
verdict = ('DISTINGUISHABLE — between-region spread is a meaningful fraction '
           'of total variability' if ratio > 0.25 else
           'NOT CLEARLY DISTINGUISHABLE — these regions are likely sampling '
           'largely the same mascon cells. Report the contrast with that caveat, '
           'or drop it.')
print(f'\n  VERDICT: {verdict}')

# ── PLOT ─────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(13, 6.5))
fig.patch.set_facecolor('#0d1117'); ax.set_facecolor('#0d1117')
for region in REGIONS:
    s = df[df.region == region].dropna(subset=['tws']).sort_values('year')
    ax.plot(s.year, s.tws, 'o-', color=COLORS[region], lw=2, ms=4, label=region, zorder=3)
    sl, ic, r, p, _ = stats.linregress(s.year, s.tws)
    x = np.linspace(s.year.min(), s.year.max(), 100)
    ax.plot(x, sl * x + ic, '--', color=COLORS[region], lw=1.3, alpha=.55, zorder=2)
ax.axhline(0, color='#8b949e', lw=.8, alpha=.5)
ax.axvline(2017.5, color='#8b949e', lw=1, ls=':', alpha=.5)
ax.text(2017.6, ax.get_ylim()[1]*0.96, 'GRACE → GRACE-FO', color='#8b949e', fontsize=8)
ax.set_xlabel('Year', color='#e6edf3'); ax.set_ylabel('TWS anomaly (cm)', color='#e6edf3')
ax.set_title('Same satellite, same season, four regions of Bangladesh\n'
             'GRACE/GRACE-FO pre-Aman (Jan–May) terrestrial water storage, 2002–2024',
             color='#e6edf3', fontsize=13, fontweight='bold', pad=14)
ax.tick_params(colors='#8b949e'); ax.grid(True, color='#21262d', lw=.7)
for sp in ax.spines.values(): sp.set_edgecolor('#30363d')
ax.legend(loc='lower left', fontsize=9, facecolor='#161b22',
          edgecolor='#30363d', labelcolor='#e6edf3')
plt.tight_layout()
os.makedirs(OUT, exist_ok=True)
plt.savefig(OUT + 'regional_trend_comparison.png', dpi=150,
            bbox_inches='tight', facecolor='#0d1117')
plt.close()

with open(OUT + 'regional_trend_summary.txt', 'w') as f:
    f.write('PRAAN — regional trend comparison\n' + '=' * 70 + '\n\n')
    f.write('Variable : GRACE/GRACE-FO MASCON_CRI, lwe_thickness (cm)\n')
    f.write('Season   : pre-Aman, January-May\n')
    f.write(f'Period   : {START}-{END}\n\n')
    f.write(rt.to_string(index=False, float_format=lambda x: f'{x:.4f}') + '\n\n')
    f.write('RESOLUTION CHECK\n' + '-' * 70 + '\n')
    f.write(pp.to_string(index=False, float_format=lambda x: f'{x:.3f}') + '\n\n')
    f.write(f'mean between-region spread : {spread:.2f} cm\n')
    f.write(f'overall series variability : {overall:.2f} cm\n')
    f.write(f'ratio                      : {ratio:.2f}\n\n')
    f.write(f'VERDICT: {verdict}\n')
print(f'\nWrote {DATA}grace_regional_tws.csv, {OUT}regional_trend_comparison.png '
      f'and {OUT}regional_trend_summary.txt')
