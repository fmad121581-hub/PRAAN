"""
PRAAN — regional trend comparison, corrected
Script: 17_regional_trends_final.py

Runs on the CSV written by 16_regional_trend_comparison.py. No Earth Engine
needed, so it is cheap to re-run.

WHAT 16 FOUND, AND WHAT WAS WRONG WITH REPORTING IT
    Four regions were extracted. Three carry genuinely separate signals:
    every pair differs by 5.4-6.0 cm on average. But Haor Basin (NE) and
    Central Floodplain differ by 0.052 cm with a correlation of 1.000 —
    they are the same signal, because Sylhet and Dhaka sit inside the same
    GRACE mascon cell. Presenting them as two findings would be reporting
    one number twice.

    Script 16's verdict averaged over all pairs and so missed that. This
    script tests each PAIR, drops the redundant region, and says why.

THE RESULT
    Same satellite, same season, same method, three regions:
      Barind Tract (NW)   significant depletion
      Coastal South (SW)  significant depletion
      Haor Basin (NE)     no significant trend

    That is the challenge's regional-contrast question answered with data,
    and the collapsed pair is itself a measured statement about what GRACE
    can resolve over a country only ~400 km across.

OUTPUT
    outputs/regional_trend_comparison.png
    outputs/regional_trend_summary.txt
"""
import pandas as pd, numpy as np, itertools, os
from scipy import stats
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt

BASE = r"C:/Users/user/OneDrive/Nasa_2026/PRAAN/"
DATA, OUT = BASE + "data/processed/", BASE + "outputs/"
COLLAPSE_CM = 0.5          # below this two regions are the same signal
KEEP_ON_COLLAPSE = 'Haor Basin (NE)'   # the hydrologically distinct one
COLORS = {'Barind Tract (NW)': '#f85149', 'Haor Basin (NE)': '#3fb950',
          'Coastal South (SW)': '#58a6ff', 'Central Floodplain': '#ffa657'}

df = pd.read_csv(DATA + 'grace_regional_tws.csv')
piv = df.pivot(index='year', columns='region', values='tws').dropna()

# ── 1. WHICH REGIONS ARE ACTUALLY SEPARATE SIGNALS? ──────────
pairs, collapsed = [], []
for a, b in itertools.combinations(piv.columns, 2):
    d = (piv[a] - piv[b]).abs().mean()
    c = piv[a].corr(piv[b])
    pairs.append({'pair': f'{a} vs {b}', 'mean_abs_diff_cm': d, 'correlation': c})
    if d < COLLAPSE_CM:
        collapsed.append((a, b))
pp = pd.DataFrame(pairs)

drop = set()
for a, b in collapsed:
    drop.add(b if a == KEEP_ON_COLLAPSE else a)
keep = [r for r in piv.columns if r not in drop]

print('=' * 78)
print('PAIRWISE SEPARATION — can GRACE tell these regions apart?')
print('=' * 78)
print(pp.to_string(index=False, float_format=lambda x: f'{x:.3f}'))
for a, b in collapsed:
    print(f'\n  COLLAPSED: "{a}" and "{b}" differ by '
          f'{(piv[a]-piv[b]).abs().mean():.3f} cm — one signal, not two.')
print(f'\n  Reporting {len(keep)} regions: ' + ', '.join(keep))
if drop:
    print(f'  Dropped as redundant: ' + ', '.join(sorted(drop)))

# ── 2. TRENDS ────────────────────────────────────────────────
rows = []
for region in keep:
    s = df[df.region == region].dropna(subset=['tws'])
    for label, sub in [('2002-2017', s[s.year <= 2017]), ('2002-2024', s)]:
        sl, ic, r, p, se = stats.linregress(sub.year, sub.tws)
        rows.append({'region': region, 'period': label, 'n': len(sub),
                     'slope_cm_yr': sl, 'r': r, 'p': p,
                     'verdict': ('significant decline' if (p < .05 and sl < 0)
                                 else 'significant increase' if p < .05
                                 else 'no significant trend')})
rt = pd.DataFrame(rows)
print('\n' + '=' * 78)
print('TREND BY REGION')
print('=' * 78)
print(rt.to_string(index=False, float_format=lambda x: f'{x:.4f}'))

# ── 3. CHART ─────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(13, 6.5))
fig.patch.set_facecolor('#0d1117'); ax.set_facecolor('#0d1117')
for region in keep:
    s = df[df.region == region].dropna(subset=['tws']).sort_values('year')
    sl, ic, r, p, _ = stats.linregress(s[s.year <= 2017].year, s[s.year <= 2017].tws)
    sig = p < .05
    lab = (f'{region}:  {sl:+.2f} cm/yr, p={p:.3f}'
           + ('  ✓ significant' if sig else '  — not significant'))
    ax.plot(s.year, s.tws, 'o-', color=COLORS[region],
            lw=2.2 if sig else 1.4, ms=4,
            alpha=1 if sig else .75, label=lab, zorder=3)
    x = np.linspace(2002, 2017, 50)
    ax.plot(x, sl * x + ic, '--', color=COLORS[region],
            lw=2 if sig else 1, alpha=.85 if sig else .4, zorder=2)
ax.axvline(2017.5, color='#8b949e', lw=1, ls=':', alpha=.5)
ax.text(2017.7, ax.get_ylim()[1] - 1, 'GRACE → GRACE-FO',
        color='#8b949e', fontsize=8)
ax.set_xlabel('Year', color='#e6edf3', fontsize=11)
ax.set_ylabel('TWS anomaly (cm)', color='#e6edf3', fontsize=11)
ax.set_title('One satellite, three regions, different answers\n'
             'GRACE/GRACE-FO pre-Aman (Jan–May) water storage · '
             'dashed lines are 2002–2017 trends',
             color='#e6edf3', fontsize=13, fontweight='bold', pad=14)
ax.tick_params(colors='#8b949e'); ax.grid(True, color='#21262d', lw=.7)
for sp in ax.spines.values(): sp.set_edgecolor('#30363d')
ax.legend(loc='lower left', fontsize=9, facecolor='#161b22',
          edgecolor='#30363d', labelcolor='#e6edf3')
note = ('Sylhet (NE) and Dhaka (Central) returned series differing by 0.05 cm — '
        'one GRACE mascon cell, not two — so Central is not shown separately.')
ax.text(.5, -.13, note, transform=ax.transAxes, ha='center',
        fontsize=8, color='#8b949e', style='italic')
plt.tight_layout()
os.makedirs(OUT, exist_ok=True)
plt.savefig(OUT + 'regional_trend_comparison.png', dpi=150,
            bbox_inches='tight', facecolor='#0d1117')
plt.close()

# ── 4. SUMMARY ───────────────────────────────────────────────
with open(OUT + 'regional_trend_summary.txt', 'w', encoding='utf-8') as f:
    f.write('PRAAN — regional trend comparison\n' + '=' * 70 + '\n\n')
    f.write('Variable : GRACE/GRACE-FO MASCON_CRI, lwe_thickness (cm)\n'
            'Season   : pre-Aman, January-May\n'
            'Question : does the same variable trend differently by region?\n\n')
    f.write('PAIRWISE SEPARATION\n' + '-' * 70 + '\n')
    f.write(pp.to_string(index=False, float_format=lambda x: f'{x:.3f}') + '\n\n')
    for a, b in collapsed:
        f.write(f'"{a}" and "{b}" differ by {(piv[a]-piv[b]).abs().mean():.3f} cm '
                f'(correlation {piv[a].corr(piv[b]):.3f}). They fall inside the same\n'
                f'GRACE mascon cell and are one signal, not two. Only '
                f'{KEEP_ON_COLLAPSE} is reported.\n\n')
    f.write('TRENDS\n' + '-' * 70 + '\n')
    f.write(rt.to_string(index=False, float_format=lambda x: f'{x:.4f}') + '\n\n')
    f.write('HOW TO STATE THIS\n' + '-' * 70 + '\n')
    f.write(
      'Over the GRACE era (2002-2017) the Barind Tract loses water storage at\n'
      '-0.90 cm/yr (p = 0.004) and the coastal southwest at -0.57 cm/yr\n'
      '(p = 0.002), while the northeastern haor basin shows no significant\n'
      'trend (p = 0.40). Same satellite, same season, same method - the\n'
      'direction and significance depend on the region, which is what the\n'
      'challenge asks us to detect.\n\n'
      'Do NOT say water is increasing in the northeast. Over 2002-2024 that\n'
      'slope turns positive (+0.36 cm/yr) but p = 0.12, so the honest\n'
      'statement is "no significant trend", not "rising".\n\n'
      'The collapsed pair is a result, not a failure: Bangladesh is roughly\n'
      '400 km across and a GRACE mascon resolves about 300 km, so the country\n'
      'supports about three independent samples, not four. Saying so shows we\n'
      'know what the instrument can and cannot do.\n')

print(f'\nWrote {OUT}regional_trend_comparison.png and regional_trend_summary.txt')
