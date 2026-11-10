"""
PRAAN — separating groundwater from total water storage (GLDAS)
Script: 22_gldas_groundwater.py

WHY THIS EXISTS
    GRACE measures total terrestrial water storage (TWS): soil moisture,
    snow, canopy water, surface water and groundwater together. The site
    said the Barind decline was "consistent with" groundwater depletion and
    leaned on BWDB/BMDA well records for that. This script makes the
    attribution quantitative with the standard water-balance residual
    (Rodell et al. 2009): subtract the water a land-surface model puts in
    the soil, snow and canopy, and see whether the remainder still falls.

        GWS anomaly = TWS anomaly (GRACE) - [soil 0-200 cm + SWE + canopy] anomaly (GLDAS)

    GLDAS-2.1 Noah is a NASA model the challenge statement names.

WHAT IT DOES NOT REMOVE
    Rivers, wetlands and reservoirs are not in GLDAS Noah, so the remainder
    is "groundwater plus surface water". In the dry season (January-May)
    surface water is at its lowest, and in the Barind Tract it is small; in
    the haor basin it is not, so read the haor result with that caveat.

SCALE
    GRACE resolves about 300 km; GLDAS is averaged over each region's own
    districts. The subtraction is therefore best matched for "All
    Bangladesh" and is an approximation for the smaller regions.

METHOD
    - Monthly regional means from data/processed/detective_monthly.csv
      (script 23): `tws` in cm, `land` in mm (kg/m2), both on their native
      grids.
    - GLDAS anomaly relative to its January 2004 - December 2009 mean, the
      baseline the JPL mascon anomalies use; mm -> cm.
    - Dry season = January-May, the image-weighted mean of the months GRACE
      has, as scripts 16 and 23. GLDAS is averaged over the same months.
    - Trends: Sen's slope and Mann-Kendall with the Hamed-Rao correction
      (floored at 1), the same tests as script 18. Script 24 checks the
      page computes the same numbers.

NO EARTH ENGINE NEEDED — reads committed CSVs.

OUTPUT
    data/processed/gldas_regional_storage.csv   monthly tws, land, gws per region
    outputs/gldas_groundwater_stats.csv         dry-season trends per region and component
    outputs/gldas_groundwater_summary.txt
    outputs/gldas_groundwater.png
"""
import os
import numpy as np, pandas as pd
from scipy import stats
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + os.sep
DATA, OUT = BASE + 'data/processed/', BASE + 'outputs/'
BASELINE = (2004, 2009)
SEASON = (1, 5)
REGIONS = {'barind': 'Barind Tract (NW)', 'coastal': 'Coastal South (SW)', 'haor': 'Haor Basin (NE)',
           'dhaka': 'Dhaka region', 'bd': 'All Bangladesh'}

# ── 1. MONTHLY GROUNDWATER RESIDUAL ──────────────────────────────────────
m = pd.read_csv(DATA + 'detective_monthly.csv')
if 'land' not in set(m.variable):
    raise SystemExit('No `land` rows in detective_monthly.csv: run `python 23_detective_monthly.py land`')
tws = m[m.variable == 'tws'].rename(columns={'value': 'tws_cm'})[['region', 'year', 'month', 'tws_cm', 'n']]
land = m[m.variable == 'land'].rename(columns={'value': 'land_mm'})[['region', 'year', 'month', 'land_mm']]
base = (land[land.year.between(*BASELINE)].groupby('region').land_mm.mean().rename('base_mm'))
land = land.join(base, on='region')
land['land_anom_cm'] = (land.land_mm - land.base_mm) / 10.0
df = tws.merge(land[['region', 'year', 'month', 'land_mm', 'land_anom_cm']], on=['region', 'year', 'month'])
df['gws_cm'] = df.tws_cm - df.land_anom_cm
df = df.sort_values(['region', 'year', 'month'])
df.to_csv(DATA + 'gldas_regional_storage.csv', index=False)


# ── 2. TRENDS (as script 18) ─────────────────────────────────────────────
def sens_slope(y, x):
    s = [(y[j] - y[i]) / (x[j] - x[i]) for i in range(len(y)) for j in range(i + 1, len(y)) if x[j] != x[i]]
    return float(np.median(s)) if s else np.nan


def tie_ranks(v):
    """Ranks from 0, with ties sharing their average rank. Detrending by
    Sen's slope always leaves two points exactly level (the median slope
    passes through a pair), and floating-point noise would otherwise decide
    their order differently on different machines. Values closer than 1e-9
    of the series' range count as tied."""
    v = np.asarray(v, float)
    order = np.argsort(v, kind='stable')
    tol = 1e-9 * (v.max() - v.min())
    ranks = np.empty(len(v))
    i = 0
    while i < len(v):
        j = i
        while j + 1 < len(v) and v[order[j + 1]] - v[order[j]] <= tol:
            j += 1
        ranks[order[i:j + 1]] = (i + j) / 2
        i = j + 1
    return ranks


def mk_hamed_rao(y):
    y = np.asarray(y, float); n = len(y)
    S = sum(np.sign(y[j] - y[i]) for i in range(n - 1) for j in range(i + 1, n))
    _, counts = np.unique(y, return_counts=True)
    var = (n * (n - 1) * (2 * n + 5) - sum(c * (c - 1) * (2 * c + 5) for c in counts if c > 1)) / 18.0
    x = np.arange(n); detr = y - sens_slope(y, x) * x
    r = tie_ranks(detr); rbar, rvar = r.mean(), r.var(); acc = 0.0
    if rvar > 0:
        for lag in range(1, n):
            rho = np.sum((r[:-lag] - rbar) * (r[lag:] - rbar)) / ((n - lag) * rvar)
            if abs(rho) > 1.96 / np.sqrt(n - lag):
                acc += (n - lag) * (n - lag - 1) * (n - lag - 2) * rho
    var *= max(1 + (2.0 / (n * (n - 1) * (n - 2))) * acc, 1.0)   # never shrink, as script 18
    Z = (S - 1) / np.sqrt(var) if S > 0 else (S + 1) / np.sqrt(var) if S < 0 else 0.0
    return 2 * (1 - stats.norm.cdf(abs(Z)))


d = df[df.month.between(*SEASON)].copy()
for c in ('tws_cm', 'land_anom_cm', 'gws_cm'):
    d[c + '_w'] = d[c] * d.n
g = d.groupby(['region', 'year']).agg(n=('n', 'sum'), months=('month', 'size'),
                                      **{c + '_w': (c + '_w', 'sum') for c in ('tws_cm', 'land_anom_cm', 'gws_cm')}).reset_index()
g = g[g.months >= 2]                      # as the page: at least 2 of the 5 dry-season months
for c in ('tws_cm', 'land_anom_cm', 'gws_cm'):
    g[c] = g[c + '_w'] / g.n
yearly = g[['region', 'year', 'n', 'tws_cm', 'land_anom_cm', 'gws_cm']]

COMP = {'tws_cm': 'total water storage (GRACE)', 'land_anom_cm': 'soil + snow + canopy (GLDAS)',
        'gws_cm': 'groundwater + surface water (GRACE - GLDAS)'}
res = []
for rk, rname in REGIONS.items():
    s = yearly[yearly.region == rk].sort_values('year')
    for label, sub in [('2002-2017', s[s.year <= 2017]), ('2002-2024', s)]:
        for col, name in COMP.items():
            x, y = sub.year.values.astype(float), sub[col].values.astype(float)
            if len(y) < 8:
                continue
            ts = stats.theilslopes(y, x, alpha=0.95)
            p = mk_hamed_rao(y)
            res.append({'region_key': rk, 'region': rname, 'period': label, 'column': col, 'component': name,
                        'n': len(y), 'sens_slope_cm_yr': sens_slope(y, x), 'ci_low': ts.low_slope,
                        'ci_high': ts.high_slope, 'mk_p': p, 'significant': p < 0.05})
rt = pd.DataFrame(res)
rt.to_csv(OUT + 'gldas_groundwater_stats.csv', index=False)

with open(OUT + 'gldas_groundwater_summary.txt', 'w', encoding='utf-8') as f:
    f.write('PRAAN — GRACE minus GLDAS: groundwater plus surface water\n' + '=' * 78 + '\n\n')
    f.write('GWS = TWS (GRACE/GRACE-FO JPL mascon) - [soil moisture 0-200 cm + SWE + canopy] (GLDAS-2.1 Noah)\n')
    f.write(f'January-May means, GLDAS anomaly vs {BASELINE[0]}-{BASELINE[1]}, cm of water.\n')
    f.write('Rivers, wetlands and reservoirs are NOT removed (not in GLDAS Noah).\n')
    f.write("Sen's slope with 95% CI; Mann-Kendall p with the Hamed-Rao correction.\n\n")
    show = rt[['region', 'period', 'component', 'n', 'sens_slope_cm_yr', 'ci_low', 'ci_high', 'mk_p', 'significant']]
    f.write(show.to_string(index=False, float_format=lambda v: f'{v:.4f}') + '\n\n')
    for rk in REGIONS:
        for period in ('2002-2017', '2002-2024'):
            q = rt[(rt.region_key == rk) & (rt.period == period)].set_index('column')
            if len(q) < 3:
                continue
            share = q.sens_slope_cm_yr['gws_cm'] / q.sens_slope_cm_yr['tws_cm'] if q.sens_slope_cm_yr['tws_cm'] else np.nan
            f.write(f"{REGIONS[rk]} {period}: groundwater+surface water {q.sens_slope_cm_yr['gws_cm']:+.2f} cm/yr "
                    f"(p = {q.mk_p['gws_cm']:.3g}, {'SIGNIFICANT' if q.significant['gws_cm'] else 'not significant'}); "
                    f"GLDAS land water {q.sens_slope_cm_yr['land_anom_cm']:+.2f} cm/yr (p = {q.mk_p['land_anom_cm']:.3g}); "
                    f"residual / TWS slope = {share:.0%}\n")
print(open(OUT + 'gldas_groundwater_summary.txt', encoding='utf-8').read())

# ── 3. FIGURE ────────────────────────────────────────────────────────────
b = yearly[yearly.region == 'barind'].sort_values('year')
full = pd.DataFrame({'year': range(int(b.year.min()), int(b.year.max()) + 1)}).merge(b, how='left')
fig, ax = plt.subplots(figsize=(10, 4.8))
ax.plot(full.year, full.tws_cm, 'o-', color='#f85149', label='total water storage (GRACE / GRACE-FO)')
ax.plot(full.year, full.land_anom_cm, 's--', color='#3fb950', label='soil + snow + canopy (GLDAS-2.1 Noah)')
ax.plot(full.year, full.gws_cm, 'd-', color='#58a6ff', label='GRACE minus GLDAS (groundwater + surface water)')
ax.axvspan(2017.5, 2018.5, color='grey', alpha=.15)
ax.axhline(0, color='grey', lw=.6)
ax.set_title('Barind Tract, January-May storage anomalies')
ax.set_ylabel('cm of water'); ax.legend(fontsize=8)
fig.tight_layout(); fig.savefig(OUT + 'gldas_groundwater.png', dpi=150)
print('wrote', DATA + 'gldas_regional_storage.csv,', OUT + 'gldas_groundwater_stats.csv, _summary.txt and .png')
