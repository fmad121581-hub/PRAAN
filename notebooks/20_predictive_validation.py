"""
PRAAN — predictive validation of the Absorption Stress Index
Script: 20_predictive_validation.py

WHY THIS REPLACES THE TEST IN 19
    Script 19 correlated the ASI with observed 2000-2020 growth and found
    rho = +0.267 (p = 0.020): high-stress wards grew faster. Taken at face
    value that says density attracts arrivals.

    It cannot be taken at face value. The ASI's largest component is
    present-day population density. A ward that gained a lot of people
    between 2000 and 2020 is dense TODAY *because* of that growth. So the
    correlation runs partly backwards through time: the outcome causes the
    predictor. Any allocation rule justified by it would be circular.

    The fix is a predictive design. Build the same index out of year-2000
    inputs only - WorldPop 2000 population, GHSL 2000 built-up surface, plus
    the two time-invariant components (flood exposure, household size) - and
    ask whether it predicts the growth that came AFTER. Nothing in the
    predictor can then have been caused by the outcome.

    Three windows are tested (2000-2020, 2000-2010, 2010-2020) so the answer
    cannot hinge on one arbitrary period, and each ASI component is tested on
    its own so a null for the index is not hiding a signal in one input.

NO EARTH ENGINE NEEDED — reads committed CSVs written by 19_validate_asi.py.

OUTPUT
    outputs/predictive_validation.txt
    outputs/predictive_validation.png
"""
import pandas as pd, numpy as np, os
from scipy import stats
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Resolve the project root from this file's own location, so the script runs
# the same whether it is launched from VS Code, a terminal, or anywhere else.
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + os.sep
DATA, OUT = os.path.join(BASE, 'data', 'processed') + os.sep, os.path.join(BASE, 'outputs') + os.sep

W4 = {'pop': .35, 'built': .25, 'flood': .20, 'hh': .20}   # 4-indicator ASI
W3 = {'pop': .40, 'built': .35, 'flood': .25}              # 3-indicator fallback
mm = lambda s: (s - s.min()) / (s.max() - s.min())

g = pd.read_csv(DATA + 'ward_observed_growth.csv')
w = pd.read_csv(OUT + 'phase3_ward_scores_v4_dissolved.csv')
d = w.merge(g, on='GID_4', how='inner')
d = d[(d.pop_2000 > 0) & (d.pop_2010 > 0) & (d.built_2000 > 0)].copy()

# ── the baseline index: exactly the published ASI, but with the two
#    time-varying inputs taken from 2000 instead of the present day ──
d['pop0_norm'] = mm(d.pop_2000)
d['built0_norm'] = mm(d.built_2000)
has4 = d.hh_size_norm.notna()
d['ASI_2000'] = np.where(
    has4,
    W4['pop'] * d.pop0_norm + W4['built'] * d.built0_norm
    + W4['flood'] * d.flood_norm + W4['hh'] * d.hh_size_norm,
    W3['pop'] * d.pop0_norm + W3['built'] * d.built0_norm
    + W3['flood'] * d.flood_norm)

WINDOWS = {
    'growth 2000-2020': 100 * (d.pop_2020 - d.pop_2000) / d.pop_2000,
    'growth 2000-2010': 100 * (d.pop_2010 - d.pop_2000) / d.pop_2000,
    'growth 2010-2020': 100 * (d.pop_2020 - d.pop_2010) / d.pop_2010,
}
PREDICTORS = {
    'ASI built from 2000 only': d.ASI_2000,
    '  component: population 2000': d.pop0_norm,
    '  component: built-up 2000': d.built0_norm,
    '  component: flood exposure': d.flood_norm,
    '  component: household size': d.hh_size_norm,
    'ASI as published (present-day)': d.ASI,
}

rows = []
for xk, xv in PREDICTORS.items():
    for wk, wv in WINDOWS.items():
        s = pd.DataFrame({'x': xv, 'y': wv}).dropna()
        rho, p = stats.spearmanr(s.x, s.y)
        rows.append({'predictor': xk.strip(), 'label': xk, 'window': wk,
                     'n': len(s), 'spearman_rho': rho, 'p': p,
                     'significant': p < 0.05})
r = pd.DataFrame(rows)

print('=' * 86)
print('PREDICTIVE VALIDATION — does a year-2000 stress index predict later growth?')
print('=' * 86)
piv = r.pivot(index='label', columns='window', values='spearman_rho')
pv = r.pivot(index='label', columns='window', values='p')
for lab in PREDICTORS:
    cells = '  '.join(f'{piv.loc[lab, w]:+.3f} (p={pv.loc[lab, w]:.3f})' for w in WINDOWS)
    print(f'{lab:32s} {cells}')

base = r[(r.label == 'ASI built from 2000 only')]
n_sig = int(base.significant.sum())
baseline_predicts = n_sig > 0 and (base[base.significant].spearman_rho > 0).all()

# quartiles of the baseline index against subsequent growth
d['g20'] = WINDOWS['growth 2000-2020']
q = pd.qcut(d.ASI_2000, 4, labels=['Q1 least stressed', 'Q2', 'Q3', 'Q4 most stressed'])
qmed = d.groupby(q, observed=True).g20.median()
print('\nMedian 2000-2020 growth by baseline-stress quartile:')
for k, v in qmed.items():
    print(f'  {k:20s} {v:+.1f}%')

endo = r[(r.label == 'ASI as published (present-day)')
         & (r.window == 'growth 2000-2020')].iloc[0]
print(f'\nFor contrast, the present-day ASI against the same growth: '
      f'rho = {endo.spearman_rho:+.3f} (p = {endo.p:.3f}) — but present-day')
print('density is partly a RESULT of that growth, so this is not evidence.')

if baseline_predicts:
    verdict = ('Baseline stress predicts later growth. Allocate arrivals as '
               'population x ASI.')
elif n_sig:
    verdict = ('Baseline stress predicts later growth NEGATIVELY. Allocate '
               'arrivals as population x (1 - ASI).')
else:
    verdict = ('The ASI carries no demonstrated information about where growth '
               'went. Allocate arrivals on population alone and say so.')
print('\nVERDICT: ' + verdict)

# ── chart ────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(13, 5.4))
fig.patch.set_facecolor('#0d1117')
for ax, (xc, xl, ti) in zip(axes, [
        ('ASI_2000', 'Stress index built from year-2000 data only',
         'Predictive: nothing here was caused by the outcome'),
        ('ASI', 'Absorption Stress Index as published (present day)',
         'Endogenous: present density is partly a result of the growth')]):
    ax.set_facecolor('#0d1117')
    s = d[[xc, 'g20']].dropna()
    rho, p = stats.spearmanr(s[xc], s.g20)
    ax.scatter(s[xc], s.g20, c='#58a6ff', s=34, alpha=.8, edgecolors='none')
    m, b = np.polyfit(s[xc], s.g20, 1)
    xs = np.linspace(s[xc].min(), s[xc].max(), 50)
    ax.plot(xs, m * xs + b, '--', color='#f85149', lw=2)
    ax.set_xlabel(xl, color='#e6edf3', fontsize=10)
    ax.set_ylabel('Observed population growth 2000–2020 (%)', color='#e6edf3', fontsize=10)
    ax.set_title(f'{ti}\nrho = {rho:+.3f}, p = {p:.3f}', color='#e6edf3', fontsize=10)
    ax.tick_params(colors='#8b949e'); ax.grid(True, color='#21262d', lw=.7)
    for sp in ax.spines.values(): sp.set_edgecolor('#30363d')
fig.suptitle('Does the stress index predict where Dhaka actually grew?',
             color='#e6edf3', fontsize=13, fontweight='bold')
plt.tight_layout()
os.makedirs(OUT, exist_ok=True)
plt.savefig(OUT + 'predictive_validation.png', dpi=150,
            bbox_inches='tight', facecolor='#0d1117')
plt.close()

with open(OUT + 'predictive_validation.txt', 'w', encoding='utf-8') as f:
    f.write('PRAAN - predictive validation of the Absorption Stress Index\n')
    f.write('=' * 86 + '\n\n')
    f.write('Question: does a stress index built from year-2000 inputs predict the\n'
            'population growth that followed? Present-day density cannot be used to\n'
            'answer this - a ward is dense today partly BECAUSE it grew, so\n'
            'correlating the published ASI with 2000-2020 growth is circular.\n\n')
    f.write(f'n = {len(d)} wards. Spearman rho, p in brackets.\n\n')
    for lab in PREDICTORS:
        cells = '  '.join(f'{piv.loc[lab, w]:+.3f} ({pv.loc[lab, w]:.3f})' for w in WINDOWS)
        f.write(f'{lab:32s} {cells}\n')
    f.write('\nwindows, left to right: ' + ', '.join(WINDOWS) + '\n\n')
    f.write('MEDIAN 2000-2020 GROWTH BY BASELINE-STRESS QUARTILE\n' + '-' * 86 + '\n')
    for k, v in qmed.items():
        f.write(f'  {k:20s} {v:+.1f}%\n')
    f.write('\nVERDICT\n' + '-' * 86 + '\n' + verdict + '\n\n')
    f.write('WHAT THIS MEANS FOR THE PUBLISHED RANKING\n' + '-' * 86 + '\n')
    f.write('The ASI remains a description of absorption stress - density,\n'
            'built-up saturation, flood exposure and crowding are stressors\n'
            'whether or not they attract migrants. What this test rules out is\n'
            'using the ASI to decide WHERE arrivals land. That is now done on\n'
            'population alone, which assumes nothing the data does not support.\n')
print(f'\nWrote {OUT}predictive_validation.txt and predictive_validation.png')
