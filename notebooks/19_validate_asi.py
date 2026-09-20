"""
PRAAN — validate the Absorption Stress Index against observed growth
Script: 19_validate_asi.py

THE GAP THIS CLOSES
    The ASI has never been checked against anything that actually happened.
    It is a weighted index we invented; nothing in the project shows it
    corresponds to how Dhaka really absorbed people. A judge is entitled to
    ask "how do you know this index means anything?" and at present the
    honest answer is "we don't".

    It also settles, with evidence rather than assumption, the arrival
    allocation rule. PRAAN currently distributes arrivals as
    population x (1 - ASI): more arrivals to LESS stressed wards, assuming
    low stress means spare capacity. The opposite is arguable — Dhaka's
    low-income in-migrants have historically packed into dense, high-stress
    settlements. That disagreement has been flagged all along but never
    resolved.

    Observed ward-level growth resolves it. If high-ASI wards grew faster,
    the current rule is backwards and should be inverted. If low-ASI wards
    grew faster, the rule is supported. Either way the answer replaces an
    assumption with a measurement.

WHAT IT EXTRACTS
    WorldPop annual population, 2000-2020, per ward
    JRC GHSL built-up surface, 2000 / 2010 / 2020, per ward

    Both are already used elsewhere in PRAAN and both are free in Earth
    Engine, so this needs no new data source - only a new question.

HOW TO READ THE RESULT
    This script measures the association between the present-day ASI and
    observed growth. It does NOT settle the allocation rule, because the
    ASI's largest component is present-day density and a ward is dense today
    partly because it grew: the outcome is inside the predictor.

    Run 20_predictive_validation.py for the question that can be answered -
    does an index built from year-2000 inputs alone predict what followed?
    It does not, in any window, so arrivals are allocated on population only.

    A null result is a real finding and must be reported, not buried.

OUTPUT
    data/processed/ward_observed_growth.csv
    outputs/asi_validation.txt
    outputs/asi_validation.png
"""
import pandas as pd, numpy as np, json, time, os, sys
from scipy import stats
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Earth Engine is only needed to (re)extract the observed growth. Once
# ward_observed_growth.csv is committed, the analysis re-runs offline, so a
# reviewer can reproduce the numbers without a Google account. Pass
# --refresh to pull from Earth Engine again.
REFRESH = '--refresh' in sys.argv
# Project root resolved from this file's location, so the script runs
# unchanged on any machine.
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + os.sep
DATA, OUT = BASE + "data/processed/", BASE + "outputs/"
GEOJSON = DATA + 'dhaka_wards_dissolved.geojson'
POP_YEARS = [2000, 2005, 2010, 2015, 2020]
BUILT_EPOCHS = [2000, 2010, 2020]

prim = pd.read_csv(OUT + 'crisis_index_primary.csv')
CACHE = DATA + 'ward_observed_growth.csv'

if not REFRESH and os.path.exists(CACHE):
    g = pd.read_csv(CACHE)
    print(f'Using committed {CACHE} ({len(g)} wards). Pass --refresh to re-extract.')
else:
    import ee
    ee.Initialize(project='project-attempt-dhaka-heat')
    gj = json.load(open(GEOJSON))
    wanted = set(prim.GID_4)
    feats = [f for f in gj['features'] if f['properties'].get('GID_4') in wanted]
    print(f'Validating {len(feats)} ranked wards against observed growth')

    rows = []
    for i, f in enumerate(feats, 1):
        gid = f['properties']['GID_4']
        geom = ee.Geometry(f['geometry'])
        rec = {'GID_4': gid}
        try:
            for y in POP_YEARS:
                img = (ee.ImageCollection('WorldPop/GP/100m/pop')
                       .filter(ee.Filter.eq('year', y))
                       .filter(ee.Filter.eq('country', 'BGD')).mosaic())
                rec[f'pop_{y}'] = img.reduceRegion(
                    reducer=ee.Reducer.sum(), geometry=geom, scale=100,
                    maxPixels=1e9, bestEffort=True).getInfo().get('population')
            for y in BUILT_EPOCHS:
                img = ee.Image(f'JRC/GHSL/P2023A/GHS_BUILT_S/{y}').select('built_surface')
                rec[f'built_{y}'] = img.reduceRegion(
                    reducer=ee.Reducer.sum(), geometry=geom, scale=100,
                    maxPixels=1e9, bestEffort=True).getInfo().get('built_surface')
            rows.append(rec)
            if i % 10 == 0:
                print(f'  {i}/{len(feats)}')
            time.sleep(0.1)
        except Exception as e:
            print(f'  {gid} failed: {e}')

    g = pd.DataFrame(rows)
    os.makedirs(DATA, exist_ok=True)
    g.to_csv(DATA + 'ward_observed_growth.csv', index=False)

    g = pd.DataFrame(rows)
    os.makedirs(DATA, exist_ok=True)
    g.to_csv(CACHE, index=False)

d = prim.merge(g, on='GID_4', how='inner')
d = d[(d.pop_2000 > 0) & (d.built_2000 > 0)].copy()
d['pop_growth_pct'] = 100 * (d.pop_2020 - d.pop_2000) / d.pop_2000
d['built_growth_pct'] = 100 * (d.built_2020 - d.built_2000) / d.built_2000
print(f'\n{len(d)} wards with usable baselines')

lines = []
def test(xcol, ycol, xlabel, ylabel):
    s = d[[xcol, ycol]].dropna()
    rho, p = stats.spearmanr(s[xcol], s[ycol])
    r, pp = stats.pearsonr(s[xcol], s[ycol])
    # Report significance, not a hand-picked effect-size threshold. An
    # earlier version called anything with |rho| < 0.3 "no relationship",
    # which labelled a significant result (rho = +0.267, p = 0.02) a null.
    # No allocation verdict is issued here: the present-day ASI contains the
    # outcome (a ward is dense today partly BECAUSE it grew), so this
    # correlation cannot settle the rule. 20_predictive_validation.py does
    # that, using an index built from year-2000 inputs only.
    verdict = (f'{"higher" if rho > 0 else "lower"}-stress wards grew faster; '
               f'{"significant" if p < 0.05 else "not significant"} at p < 0.05. '
               'Endogenous - see 20_predictive_validation.py'
               if p < 0.05 else
               'no significant association')
    txt = (f'{xlabel} vs {ylabel}\n'
           f'  n = {len(s)}   Spearman rho = {rho:+.3f} (p = {p:.4f})   '
           f'Pearson r = {r:+.3f}\n  -> {verdict}\n')
    print(txt); lines.append(txt)
    return rho, p

print('=' * 78); print('DOES THE ASI CORRESPOND TO WHAT ACTUALLY HAPPENED?'); print('=' * 78)
r1 = test('ASI', 'pop_growth_pct', 'ASI', 'observed population growth 2000-2020')
r2 = test('ASI', 'built_growth_pct', 'ASI', 'observed built-up growth 2000-2020')
r3 = test('crisis_index', 'pop_growth_pct', 'Crisis Index', 'observed population growth')

fig, axes = plt.subplots(1, 2, figsize=(13, 5.4))
fig.patch.set_facecolor('#0d1117')
for ax, (yc, t, rr) in zip(axes, [('pop_growth_pct', 'Population growth 2000–2020 (%)', r1),
                                  ('built_growth_pct', 'Built-up growth 2000–2020 (%)', r2)]):
    ax.set_facecolor('#0d1117')
    ax.scatter(d.ASI, d[yc], c='#58a6ff', s=34, alpha=.8, edgecolors='none')
    s = d[['ASI', yc]].dropna()
    if len(s) > 2:
        m, b = np.polyfit(s.ASI, s[yc], 1)
        xs = np.linspace(s.ASI.min(), s.ASI.max(), 50)
        ax.plot(xs, m * xs + b, '--', color='#f85149', lw=2)
    ax.set_xlabel('Absorption Stress Index', color='#e6edf3')
    ax.set_ylabel(t, color='#e6edf3')
    ax.set_title(f'rho = {rr[0]:+.3f}, p = {rr[1]:.3f}', color='#e6edf3', fontsize=11)
    ax.tick_params(colors='#8b949e'); ax.grid(True, color='#21262d', lw=.7)
    for sp in ax.spines.values(): sp.set_edgecolor('#30363d')
fig.suptitle('Does the Absorption Stress Index match observed growth?',
             color='#e6edf3', fontsize=13, fontweight='bold')
plt.tight_layout()
plt.savefig(OUT + 'asi_validation.png', dpi=150, bbox_inches='tight', facecolor='#0d1117')
plt.close()

with open(OUT + 'asi_validation.txt', 'w', encoding='utf-8') as f:
    f.write('PRAAN - ASI validation against observed growth\n' + '=' * 78 + '\n\n')
    f.write('Question: does the Absorption Stress Index correspond to how Dhaka\n'
            'wards actually grew between 2000 and 2020?\n\n')
    f.write('Observed data: WorldPop annual population and JRC GHSL built-up\n'
            'surface, extracted per ward over the same boundaries used for the\n'
            'ranking.\n\n')
    f.writelines(lines)
    f.write('\nWHY THIS DOES NOT SETTLE THE ALLOCATION RULE\n' + '-' * 78 + '\n')
    f.write('These correlations use the PRESENT-DAY ASI, whose largest component\n'
            'is present-day population density. A ward is dense today partly\n'
            'BECAUSE it grew over this very period, so the outcome sits inside\n'
            'the predictor and a positive rho here is not evidence that stress\n'
            'attracts arrivals.\n\n'
            'The allocation rule is decided by 20_predictive_validation.py, which\n'
            'rebuilds the index from year-2000 inputs only. It finds no predictive\n'
            'relationship in any window, so arrivals are allocated on population\n'
            'alone. An index that fails its own validation, reported honestly, is\n'
            'worth more than one that was never tested.\n')
print(f'Wrote {OUT}asi_validation.txt and asi_validation.png')
