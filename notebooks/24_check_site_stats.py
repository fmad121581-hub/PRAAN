"""
PRAAN — check the page's trend statistics against the Python pipeline
Script: 24_check_site_stats.py

WHY THIS EXISTS
    The Trend Detective tool computes Sen's slope, its 95% confidence
    interval and the Mann-Kendall test in the browser, from
    notebooks/site/trend_stats.js. Those numbers must be the same ones the
    Python pipeline publishes, or the tool and the paper disagree.

WHAT IT CHECKS
    1. Every series in outputs/robust_trend_stats.csv (script 18): Sen's
       slope, Mann-Kendall p with the Hamed-Rao correction, and the
       variance ratio.
    2. The 95% confidence interval for Sen's slope against
       scipy.stats.theilslopes on the same series.
    3. The JS erfc against Python's math.erfc over a range of inputs.
    4. If data/processed/detective_monthly.csv exists: the January-May
       GRACE means rebuilt from its monthly values, as the page does, against
       data/processed/grace_regional_tws.csv (script 16). Both place images
       by midpoint and use the mascon product's native grid
       (notebooks/grace_season.py), so they must agree.

    5. If outputs/gldas_groundwater_stats.csv exists (script 22): the
       groundwater-estimate trends, rebuilt from the monthly file the way
       the page aggregates them and run through the page's code.
    6. The figures printed in outputs/PRAAN.html: every headline number
       (slopes, p-values, the dry-season drop) is recomputed from the CSVs
       and must appear in the page text, so the prose cannot go stale.

    Needs Node.js. No Earth Engine.

RUN
    cd notebooks
    python 24_check_site_stats.py
"""
import json, math, os, subprocess, sys
import numpy as np, pandas as pd
from scipy import stats

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + os.sep
DATA, OUT = BASE + 'data/processed/', BASE + 'outputs/'
JS = BASE + 'notebooks/site/trend_stats.js'
REL = 1e-6

# ── series, built exactly as script 18 builds them ───────────────────────
series = {}
reg = pd.read_csv(DATA + 'grace_regional_tws.csv')
for region in reg.region.unique():
    s = reg[reg.region == region]
    for label, sub in [(f'{region} 2002-2017', s[s.year <= 2017]), (f'{region} 2002-2024', s)]:
        series[label] = sub.dropna(subset=['tws']).sort_values('year')[['year', 'tws']].values.tolist()
g = pd.read_csv(DATA + 'grace_mascon_tws_raw.csv')
for label, sub in [('Barind MASCON 2002-2017', g[g.year <= 2017]), ('Barind MASCON 2002-2024', g)]:
    series[label] = sub.dropna(subset=['tws_anomaly']).sort_values('year')[['year', 'tws_anomaly']].values.tolist()
BARIND = ['Rajshahi', 'Naogaon', 'Natore', 'Nawabganj']
ch = pd.read_csv(DATA + 'chirps_aman_season_raw.csv')
ch = ch[ch.district.isin(BARIND)].groupby('year', as_index=False).rainfall_mm.mean()
series['CHIRPS Aman rainfall, Barind'] = ch.dropna().sort_values('year').values.tolist()
nd = pd.read_csv(DATA + 'modis_ndvi_aman_raw.csv')
nd = nd[nd.district.isin(BARIND)].groupby('year', as_index=False).ndvi_mean.mean()
series['MODIS NDVI Aman, Barind'] = nd.dropna().sort_values('year').values.tolist()

erfc_x = [float(v) for v in np.concatenate([np.linspace(-6, 6, 241), [1e-8, 0.4999, 0.5, 3.999, 4.0, 7.5, 9.0]])]

# ── run the page's code in Node ──────────────────────────────────────────
node_src = """
const T = require(process.argv[1]);
const inp = JSON.parse(require('fs').readFileSync(0, 'utf8'));
const out = { series: {}, erfc: inp.erfc.map(T.erfc) };
for (const [k, pts] of Object.entries(inp.series)) {
  const x = pts.map(p => p[0]), y = pts.map(p => p[1]);
  const a = T.analyse(x, y);
  out.series[k] = { slope: a.slope, lo: a.lo, hi: a.hi, p: a.p, ratio: a.ratio, n: a.n };
}
process.stdout.write(JSON.stringify(out));
"""
res = subprocess.run(['node', '-e', node_src, JS], input=json.dumps({'series': series, 'erfc': erfc_x}),
                     capture_output=True, text=True, encoding='utf-8')
if res.returncode:
    sys.exit('node failed:\n' + res.stderr)
js = json.loads(res.stdout)

fails = []
def check(label, got, want, rel=REL, absol=1e-12):
    if not (math.isclose(got, want, rel_tol=rel, abs_tol=absol)):
        fails.append(f'{label}: page {got!r} vs python {want!r}')

ref = pd.read_csv(OUT + 'robust_trend_stats.csv').set_index('series')
for k, pts in series.items():
    a, r = js['series'][k], ref.loc[k]
    check(f'{k} n', a['n'], r.n)
    check(f'{k} Sen slope', a['slope'], r.sens_slope)
    check(f'{k} Mann-Kendall p', a['p'], r.mk_p_autocorr_corrected)
    check(f'{k} variance ratio', a['ratio'], r.variance_inflation)
    x, y = np.array(pts).T
    ts = stats.theilslopes(y, x, alpha=0.95)
    check(f'{k} CI low', a['lo'], ts.low_slope)
    check(f'{k} CI high', a['hi'], ts.high_slope)
for x, got in zip(erfc_x, js['erfc']):
    check(f'erfc({x})', got, math.erfc(x), rel=1e-12, absol=1e-300)

print(f'{len(series)} series and {len(erfc_x)} erfc values compared')

# ── monthly -> January-May GRACE, as the page aggregates it ──────────────
mpath = DATA + 'detective_monthly.csv'
if os.path.exists(mpath):
    m = pd.read_csv(mpath)
    m = m[(m.variable == 'tws') & m.month.between(1, 5)]
    names = {'barind': 'Barind Tract (NW)', 'coastal': 'Coastal South (SW)',
             'haor': 'Haor Basin (NE)', 'dhaka': 'Central Floodplain'}
    got = (m.assign(w=m.value * m.n).groupby(['region', 'year'])
           .agg(w=('w', 'sum'), n=('n', 'sum')).reset_index())
    got['tws'] = got.w / got.n
    got['region'] = got.region.map(names)
    want = reg.dropna(subset=['tws'])
    cmp = want.merge(got.dropna(subset=['region']), on=['region', 'year'], suffixes=('_16', '_23'))
    worst = (cmp.tws_16 - cmp.tws_23).abs().max()
    print(f'GRACE Jan-May from monthly: {len(cmp)} region-years, largest difference {worst:.2e} cm')
    if len(cmp) != len(want):
        fails.append(f'GRACE Jan-May: {len(cmp)} region-years matched, script 16 has {len(want)}')
    if (cmp.n_images != cmp.n).any():
        fails.append('GRACE Jan-May: image counts differ from script 16')
    if worst > 1e-6:
        fails.append(f'GRACE Jan-May differs from script 16 by up to {worst:.3g} cm')
else:
    print('detective_monthly.csv not found; run script 23 for the aggregation check')

# ── groundwater estimate: page aggregation + page statistics vs script 22 ─
gpath, spath = DATA + 'gldas_regional_storage.csv', OUT + 'gldas_groundwater_stats.csv'
gstats = None
if os.path.exists(gpath) and os.path.exists(spath):
    gw = pd.read_csv(gpath)
    gw = gw[gw.month.between(1, 5)]
    yr = (gw.assign(w=gw.gws_cm * gw.n).groupby(['region', 'year'])
          .agg(w=('w', 'sum'), n=('n', 'sum'), months=('month', 'size')).reset_index())
    yr = yr[yr.months >= 2]
    yr['gws'] = yr.w / yr.n
    gseries = {}
    for rk, d in yr.groupby('region'):
        for label, sub in [('2002-2017', d[d.year <= 2017]), ('2002-2024', d)]:
            gseries[f'{rk}|{label}'] = sub.sort_values('year')[['year', 'gws']].values.tolist()
    res = subprocess.run(['node', '-e', node_src, JS], input=json.dumps({'series': gseries, 'erfc': []}),
                         capture_output=True, text=True, encoding='utf-8')
    if res.returncode:
        sys.exit('node failed:\n' + res.stderr)
    gjs = json.loads(res.stdout)['series']
    gstats = pd.read_csv(spath)
    want = gstats[gstats.column == 'gws_cm'].set_index(['region_key', 'period'])
    for k, a in gjs.items():
        rk, label = k.split('|')
        r = want.loc[(rk, label)]
        check(f'groundwater {k} Sen slope', a['slope'], r.sens_slope_cm_yr)
        check(f'groundwater {k} Mann-Kendall p', a['p'], r.mk_p)
        check(f'groundwater {k} CI low', a['lo'], r.ci_low)
        check(f'groundwater {k} CI high', a['hi'], r.ci_high)
    print(f'groundwater estimate: {len(gjs)} series compared')
else:
    print('gldas_groundwater_stats.csv not found; run script 22 for the groundwater check')

# ── the figures printed on the page ──────────────────────────────────────
html_path = OUT + 'PRAAN.html'
if os.path.exists(html_path):
    import re
    h = open(html_path, encoding='utf-8').read()
    h = re.sub(r'const (WARD_GEO|DETECTIVE|TREND) = .*', '', h)
    for ent, ch_ in [('&nbsp;', ' '), (' ', ' '), ('&minus;', '-'), ('−', '-'), ('&ndash;', '-'), ('–', '-')]:
        h = h.replace(ent, ch_)
    pf = lambda v: f'{v:.2g}'
    R = lambda name: ref.loc[name]
    b17, b24 = R('Barind Tract (NW) 2002-2017'), R('Barind Tract (NW) 2002-2024')
    c17, c24 = R('Coastal South (SW) 2002-2017'), R('Coastal South (SW) 2002-2024')
    h17, h24 = R('Haor Basin (NE) 2002-2017'), R('Haor Basin (NE) 2002-2024')
    bar = reg[reg.region == 'Barind Tract (NW)'].set_index('year').tws
    drop = bar.loc[2002:2004].mean() - bar.loc[2011:2017].mean()
    expect = [
        ('Barind 2002-2017 slope', f'-{abs(b17.sens_slope):.2f} cm/yr'),
        ('Barind 2002-2017 p', f'p = {pf(b17.mk_p_autocorr_corrected)}'),
        ('Barind 2002-2024 slope', f'-{abs(b24.sens_slope):.2f} cm/yr'),
        ('Barind 2002-2024 p', f'p = {pf(b24.mk_p_autocorr_corrected)}'),
        ('Coastal 2002-2017 slope', f'-{abs(c17.sens_slope):.2f} cm/yr'),
        ('Coastal 2002-2017 p', f'p = {pf(c17.mk_p_autocorr_corrected)}'),
        ('Coastal 2002-2024 slope', f'-{abs(c24.sens_slope):.2f} cm/yr'),
        ('Coastal 2002-2024 p', f'p = {pf(c24.mk_p_autocorr_corrected)}'),
        ('Haor 2002-2017 slope', f'-{abs(h17.sens_slope):.2f} cm/yr'),
        ('Haor 2002-2017 p', f'p = {pf(h17.mk_p_autocorr_corrected)}'),
        ('Haor 2002-2024 slope', f'+{h24.sens_slope:.2f} cm/yr'),
        ('Haor 2002-2024 p', f'p = {pf(h24.mk_p_autocorr_corrected)}'),
        ('Barind OLS p', f'p = {pf(b17.ols_p)}'),
        ('Barind lag-1 autocorrelation', f'+{b17.lag1_autocorr:.2f}'),
        ('dry-season drop', f'{drop:.0f} cm'),
    ]
    if gstats is not None:
        gb = gstats[(gstats.region_key == 'barind') & (gstats.column == 'gws_cm')].set_index('period')
        expect += [
            ('Barind groundwater 2002-2017 slope', f'-{abs(gb.sens_slope_cm_yr["2002-2017"]):.2f} cm/yr'),
            ('Barind groundwater 2002-2017 p', f'p = {pf(gb.mk_p["2002-2017"])}'),
            ('Barind groundwater 2002-2024 slope', f'-{abs(gb.sens_slope_cm_yr["2002-2024"]):.2f} cm/yr'),
            ('Barind groundwater 2002-2024 p', f'p = {pf(gb.mk_p["2002-2024"])}'),
        ]
    missing = [(k, v) for k, v in expect if v not in h]
    print(f'page text: {len(expect) - len(missing)} of {len(expect)} published figures found')
    for k, v in missing:
        fails.append(f'page text: {k} should read "{v}" and that string is not in PRAAN.html')

if fails:
    print('\nMISMATCHES:'); print('\n'.join('  ' + f for f in fails))
    sys.exit(1)
print('PASS: the page computes the same trend statistics as the Python pipeline, and prints its figures')
