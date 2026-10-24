"""
PRAAN — separating groundwater from total water storage (GLDAS)
Script: 22_gldas_groundwater.py

WHY THIS EXISTS
    GRACE measures total terrestrial water storage (TWS). The site says the
    Barind decline is "consistent with" groundwater depletion and leans on
    BWDB/BMDA well records for that. This script makes the attribution
    quantitative: subtract the water a land-surface model puts in the soil,
    snow and plant canopy, and see whether the remainder (mostly groundwater)
    still falls.

        GWS anomaly  =  TWS anomaly (GRACE)  -  [soil moisture + SWE + canopy] anomaly (GLDAS)

    GLDAS-2.1 Noah is a NASA model, which also answers the challenge's
    "variables measured by NASA missions or produced by NASA models".

WHAT IT DOES NOT REMOVE
    Rivers, wetlands and reservoirs are not in GLDAS Noah, so the remainder
    is "groundwater plus surface water". In the Barind Tract, surface water
    storage is small; in the haor basin it is not, so the haor result should
    be read with that caveat.

METHOD
    - GLDAS-2.1 Noah 3-hourly (NASA/GLDAS/V021/NOAH/G025/T3H), January–May
      mean for each year 2002–2024, same window as the GRACE series.
    - Four soil layers (0–200 cm) + snow water equivalent + canopy water,
      kg/m2 = mm, converted to cm.
    - Anomaly relative to the 2004–2009 mean, the same baseline period the
      JPL mascon anomalies use.
    - Region geometry: the same GAUL districts as script 16.
    - TWS: the committed data/processed/grace_regional_tws.csv (script 16).
    - Trends: Sen's slope and Mann-Kendall with the Hamed-Rao correction,
      exactly as script 18.

RUN
    cd notebooks
    python 22_gldas_groundwater.py
    (needs an authenticated Earth Engine account: `earthengine authenticate`)

OUTPUT
    data/processed/gldas_regional_storage.csv
    outputs/gldas_groundwater_summary.txt
    outputs/gldas_groundwater.png

    These are NOT wired into the website. Look at the result first: if the
    Barind GWS trend is significant, it can be added to the site and the
    attribution wording strengthened; if not, the site's current
    "consistent with" wording is already the right one.
"""
import os, time
import numpy as np, pandas as pd
from scipy import stats
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import ee

ee.Initialize(project='project-attempt-dhaka-heat')

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + os.sep
DATA, OUT = BASE + 'data/processed/', BASE + 'outputs/'
START, END = 2002, 2024
BASELINE = (2004, 2009)

REGIONS = {   # same GAUL ADM2 districts as script 16
    'Barind Tract (NW)':  ['Rajshahi', 'Naogaon', 'Natore', 'Nawabganj'],
    'Haor Basin (NE)':    ['Sylhet', 'Sunamganj', 'Habiganj', 'Maulvibazar'],
    'Coastal South (SW)': ['Khulna', 'Satkhira', 'Bagerhat'],
}
BANDS = ['SoilMoi0_10cm_inst', 'SoilMoi10_40cm_inst', 'SoilMoi40_100cm_inst',
         'SoilMoi100_200cm_inst', 'SWE_inst', 'CanopInt_inst']

gaul = ee.FeatureCollection('FAO/GAUL/2015/level2').filter(ee.Filter.eq('ADM0_NAME', 'Bangladesh'))
gldas = ee.ImageCollection('NASA/GLDAS/V021/NOAH/G025/T3H').select(BANDS)

# ── 1. EXTRACT GLDAS JAN–MAY STORAGE ─────────────────────────────────────
rows = []
for region, districts in REGIONS.items():
    geom = gaul.filter(ee.Filter.inList('ADM2_NAME', districts)).geometry()
    print(f'Extracting GLDAS for {region} ...')
    for year in range(START, END + 1):
        try:
            img = (gldas.filterDate(ee.Date.fromYMD(year, 1, 1), ee.Date.fromYMD(year, 6, 1))
                   .mean()
                   .reduce(ee.Reducer.sum())        # all layers + SWE + canopy, kg/m2
                   .rename('storage_mm'))
            v = img.reduceRegion(ee.Reducer.mean(), geom, scale=27830,
                                 maxPixels=1e9, bestEffort=True).getInfo().get('storage_mm')
            rows.append({'region': region, 'year': year, 'land_storage_mm': v})
            time.sleep(0.2)
        except Exception as e:
            print(f'  {year} failed: {e}')
            rows.append({'region': region, 'year': year, 'land_storage_mm': np.nan})

g = pd.DataFrame(rows)
base = (g[(g.year >= BASELINE[0]) & (g.year <= BASELINE[1])]
        .groupby('region').land_storage_mm.mean().rename('base_mm'))
g = g.join(base, on='region')
g['land_anom_cm'] = (g.land_storage_mm - g.base_mm) / 10.0

tws = pd.read_csv(DATA + 'grace_regional_tws.csv')[['region', 'year', 'tws']]
df = g.merge(tws, on=['region', 'year'], how='left')
df['gws_anom_cm'] = df.tws - df.land_anom_cm
df.to_csv(DATA + 'gldas_regional_storage.csv', index=False)


# ── 2. TRENDS (identical to script 18) ───────────────────────────────────
def sens_slope(y, x):
    s = [(y[j] - y[i]) / (x[j] - x[i]) for i in range(len(y)) for j in range(i + 1, len(y)) if x[j] != x[i]]
    return float(np.median(s)) if s else np.nan


def mk_hamed_rao(y):
    y = np.asarray(y, float); n = len(y)
    S = sum(np.sign(y[j] - y[i]) for i in range(n - 1) for j in range(i + 1, n))
    _, counts = np.unique(y, return_counts=True)
    var = (n * (n - 1) * (2 * n + 5) - sum(c * (c - 1) * (2 * c + 5) for c in counts if c > 1)) / 18.0
    x = np.arange(n); detr = y - sens_slope(y, x) * x
    r = np.argsort(np.argsort(detr)); rbar, rvar = r.mean(), r.var(); acc = 0.0
    if rvar > 0:
        for lag in range(1, n):
            rho = np.sum((r[:-lag] - rbar) * (r[lag:] - rbar)) / ((n - lag) * rvar)
            if abs(rho) > 1.96 / np.sqrt(n - lag):
                acc += (n - lag) * (n - lag - 1) * (n - lag - 2) * rho
    var *= max(1 + (2.0 / (n * (n - 1) * (n - 2))) * acc, 1.0)   # never shrink, as script 18
    Z = (S - 1) / np.sqrt(var) if S > 0 else (S + 1) / np.sqrt(var) if S < 0 else 0.0
    return 2 * (1 - stats.norm.cdf(abs(Z)))


res = []
for region in REGIONS:
    d = df[df.region == region]
    for label, sub in [('2002-2017', d[d.year <= 2017]), ('2002-2024', d)]:
        for col, name in [('tws', 'TWS (GRACE)'), ('land_anom_cm', 'soil+snow+canopy (GLDAS)'),
                          ('gws_anom_cm', 'groundwater+surface water (TWS - GLDAS)')]:
            s = sub.dropna(subset=[col]).sort_values('year')
            if len(s) < 5:
                continue
            x, y = s.year.values.astype(float), s[col].values.astype(float)
            p = mk_hamed_rao(y)
            res.append({'region': region, 'period': label, 'component': name, 'n': len(y),
                        'sens_slope_cm_yr': sens_slope(y, x), 'mk_p_corrected': p,
                        'significant': p < 0.05})
rt = pd.DataFrame(res)

with open(OUT + 'gldas_groundwater_summary.txt', 'w', encoding='utf-8') as f:
    f.write('PRAAN — GRACE minus GLDAS (groundwater + surface water)\n' + '=' * 72 + '\n\n')
    f.write('GWS = TWS(GRACE) - [soil moisture 0-200 cm + SWE + canopy](GLDAS-2.1 Noah)\n')
    f.write(f'Jan-May means, anomalies vs {BASELINE[0]}-{BASELINE[1]}, cm of water.\n')
    f.write('Rivers, wetlands and reservoirs are NOT removed (not in GLDAS Noah).\n\n')
    f.write(rt.to_string(index=False, float_format=lambda v: f'{v:.4f}') + '\n\n')
    b = rt[(rt.region == 'Barind Tract (NW)') & (rt.component.str.startswith('groundwater'))]
    for _, r in b.iterrows():
        f.write(f"Barind groundwater {r.period}: Sen's slope {r.sens_slope_cm_yr:+.2f} cm/yr, "
                f"p = {r.mk_p_corrected:.3g} -> {'SIGNIFICANT' if r.significant else 'not significant'}\n")
    share = rt[(rt.region == 'Barind Tract (NW)') & (rt.period == '2002-2017')].set_index('component').sens_slope_cm_yr
    if len(share) == 3 and share.iloc[0] != 0:
        f.write(f"\nShare of the 2002-2017 Barind TWS slope left after removing soil/snow/canopy: "
                f"{share['groundwater+surface water (TWS - GLDAS)'] / share['TWS (GRACE)']:.0%}\n")
print(open(OUT + 'gldas_groundwater_summary.txt', encoding='utf-8').read())

# ── 3. FIGURE ────────────────────────────────────────────────────────────
b = df[df.region == 'Barind Tract (NW)'].sort_values('year')
fig, ax = plt.subplots(figsize=(10, 4.8))
ax.plot(b.year, b.tws, 'o-', label='TWS (GRACE / GRACE-FO)')
ax.plot(b.year, b.land_anom_cm, 's--', label='soil + snow + canopy (GLDAS)')
ax.plot(b.year, b.gws_anom_cm, 'd-', label='TWS minus GLDAS (groundwater + surface water)')
ax.axvspan(2017.5, 2018.5, color='grey', alpha=.15)
ax.set_title('Barind Tract, January-May storage anomalies'); ax.set_ylabel('cm of water'); ax.legend()
fig.tight_layout(); fig.savefig(OUT + 'gldas_groundwater.png', dpi=150)
print('wrote', DATA + 'gldas_regional_storage.csv', OUT + 'gldas_groundwater_summary.txt', OUT + 'gldas_groundwater.png')
