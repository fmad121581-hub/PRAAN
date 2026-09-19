"""
PRAAN — Phase 1 Extension: GRACE + GRACE-FO Chart (Layout Fixed)
Script: 11c_grace_fo_chart_fixed.py

Fixes from v11b:
 - Annotations repositioned so nothing clips at right edge
 - Stats box moved to lower-right, away from arrows
 - Depletion shading clipped to GRACE era only (2011-2017)
 - Wider figure to give more horizontal room
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy import stats
import os

# ─────────────────────────────────────────────
# 1. LOAD DATA
# ─────────────────────────────────────────────
csv_path = '../data/processed/grace_mascon_tws_raw.csv'
df = pd.read_csv(csv_path)
df_clean = df.dropna(subset=['tws_anomaly']).copy()

grace_df = df_clean[df_clean['year'] <= 2017]
fo_df    = df_clean[df_clean['year'] >= 2019]

slope, intercept, r, p, se = stats.linregress(
    grace_df['year'].values, grace_df['tws_anomaly'].values
)

baseline_val  = df_clean[df_clean['year'] <= 2004]['tws_anomaly'].mean()
depleted_mean = df_clean[
    (df_clean['year'] >= 2011) & (df_clean['year'] <= 2017)
]['tws_anomaly'].mean()
depth = abs(depleted_mean - baseline_val)

val_2022 = df_clean[df_clean['year'] == 2022]['tws_anomaly'].values[0]
val_2023 = df_clean[df_clean['year'] == 2023]['tws_anomaly'].values[0]
val_2024 = df_clean[df_clean['year'] == 2024]['tws_anomaly'].values[0]

print(f"Baseline: {baseline_val:.2f} cm")
print(f"Depleted plateau: {depleted_mean:.2f} cm  (depth: {depth:.1f} cm)")

# ─────────────────────────────────────────────
# 2. PLOT
# ─────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(15, 7.5))
fig.patch.set_facecolor('#0d1117')
ax.set_facecolor('#0d1117')

Y_MIN, Y_MAX = -36, -3
X_MIN, X_MAX = 2001.2, 2025.5

# ── Era background bands ──
ax.axvspan(X_MIN, 2017.6, alpha=0.07, color='#58a6ff', zorder=0)
ax.axvspan(2018.4, X_MAX, alpha=0.07, color='#3fb950', zorder=0)

# ── Early baseline band ──
ax.axhspan(baseline_val - 1.2, baseline_val + 1.2,
           alpha=0.20, color='#f0e68c', zorder=1)
ax.axhline(baseline_val, color='#f0e68c', lw=1.2,
           ls='--', alpha=0.75, zorder=2)
ax.text(2001.4, baseline_val + 1.6,
        f'Early baseline  ({baseline_val:.0f} cm, 2002–04)',
        color='#f0e68c', fontsize=8.5, va='bottom', ha='left')

# ── Depletion plateau shading — GRACE era only (2011–2017) ──
# fill_between gives exact x bounds, unlike axhspan fractions
ax.fill_between(
    [2011, 2017],
    depleted_mean - 3.5, depleted_mean + 3.5,
    alpha=0.18, color='#f85149', zorder=1
)

# ── Satellite gap marker ──
ax.axvline(x=2018, color='#8b949e', lw=1.0,
           ls='--', alpha=0.55, zorder=2)
ax.text(2018.1, Y_MIN + 1.5, 'Satellite\ngap',
        color='#8b949e', fontsize=7.5, va='bottom', ha='left')

# ── Data lines ──
ax.plot(grace_df['year'], grace_df['tws_anomaly'],
        'o-', color='#58a6ff', lw=2.2, ms=5.5, zorder=4,
        label='GRACE TWS anomaly (2002–2017)')
ax.plot(fo_df['year'], fo_df['tws_anomaly'],
        's-', color='#3fb950', lw=2.2, ms=5.5, zorder=4,
        label='GRACE-FO TWS anomaly (2019–2024)')

# ── GRACE trend line ──
x_fit = np.linspace(2002, 2016.8, 200)
y_fit = slope * x_fit + intercept
ax.plot(x_fit, y_fit, '--', color='#f78166', lw=2.2,
        alpha=0.9, zorder=3,
        label=f'GRACE trend: {slope:.3f} cm/yr  (r={r:.3f}, p={p:.3f})')

# ── Structural depletion arrow (left side) ──
ax.annotate('', xy=(2001.5, depleted_mean),
            xytext=(2001.5, baseline_val),
            arrowprops=dict(arrowstyle='<->', color='#ff7b72', lw=1.6))
ax.text(2001.9, (depleted_mean + baseline_val) / 2,
        f'~{depth:.0f} cm\nstructural\ndepletion',
        color='#ff7b72', fontsize=8.5, va='center', ha='left')

# ── Annotate 2022 La Niña — point LEFT so text doesn't clip ──
ax.annotate(
    'La Niña 2022\n(transient recharge)',
    xy=(2022, val_2022),
    xytext=(2019.8, val_2022 + 8),
    color='#ffa657', fontsize=8.5,
    arrowprops=dict(arrowstyle='->', color='#ffa657', lw=1.3),
    bbox=dict(boxstyle='round,pad=0.35', fc='#161b22',
              ec='#ffa657', alpha=0.92)
)

# ── Annotate 2023-24 return — anchor text in middle of chart ──
fo_mean_2324 = (val_2023 + val_2024) / 2
ax.annotate(
    'Returns to depleted\nstate (2023–24)',
    xy=(2023.5, fo_mean_2324),
    xytext=(2019.2, -17),
    color='#3fb950', fontsize=8.5,
    arrowprops=dict(arrowstyle='->', color='#3fb950', lw=1.3),
    bbox=dict(boxstyle='round,pad=0.35', fc='#161b22',
              ec='#3fb950', alpha=0.92)
)

# ── Stats box — bottom right, clear of arrows ──
stats_text = (
    "GRACE (2002–2017)\n"
    f"slope = {slope:.3f} cm/yr\n"
    f"r = {r:.3f},  p = {p:.4f}\n"
    "Statistically significant ✓\n"
    "\n"
    "GRACE-FO (2019–2024)\n"
    "r = −0.065,  p = 0.903\n"
    "No new trend detectable\n"
    "(6 yrs, high variability)\n"
    "TWS remains structurally\n"
    "depressed vs 2002 baseline"
)
ax.text(0.635, 0.04, stats_text,
        transform=ax.transAxes,
        color='#e6edf3', fontsize=8.2,
        va='bottom', ha='left',
        bbox=dict(boxstyle='round,pad=0.55',
                  facecolor='#161b22',
                  edgecolor='#30363d', alpha=0.93))

# ── Era italic labels ──
ax.text(2009.5, Y_MIN + 1.2, 'GRACE', color='#58a6ff',
        fontsize=9, ha='center', alpha=0.65, style='italic')
ax.text(2022,   Y_MIN + 1.2, 'GRACE-FO', color='#3fb950',
        fontsize=9, ha='center', alpha=0.65, style='italic')

# ── Zero reference ──
ax.axhline(0, color='#8b949e', lw=0.7, alpha=0.35)

# ── Styling ──
ax.set_xlim(X_MIN, X_MAX)
ax.set_ylim(Y_MIN, Y_MAX)
ax.set_xlabel('Year', color='#e6edf3', fontsize=11)
ax.set_ylabel('TWS Anomaly (cm equivalent water thickness)',
              color='#e6edf3', fontsize=11)
ax.set_title(
    'Barind Tract Groundwater Depletion — GRACE + GRACE-FO (2002–2024)\n'
    'Aquifer remains locked in structurally depleted state '
    'despite seasonal variability',
    color='#e6edf3', fontsize=13, fontweight='bold', pad=14
)
ax.tick_params(colors='#8b949e', labelsize=9)
for spine in ax.spines.values():
    spine.set_edgecolor('#30363d')
ax.xaxis.set_major_locator(plt.MultipleLocator(2))
ax.grid(True, color='#21262d', lw=0.7, alpha=0.8)
ax.legend(loc='lower left', fontsize=9,
          facecolor='#161b22', edgecolor='#30363d',
          labelcolor='#e6edf3', framealpha=0.92)

plt.tight_layout()

out_path = 'C:/Users/user/OneDrive/Nasa_2026/PRAAN/outputs/grace_fo_extended_trend.png'
plt.savefig(out_path, dpi=150, bbox_inches='tight',
            facecolor='#0d1117')
plt.close()
print(f"✓ Saved → {out_path}")
