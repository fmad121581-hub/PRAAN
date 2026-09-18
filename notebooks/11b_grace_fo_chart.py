"""
PRAAN — Phase 1 Extension: GRACE + GRACE-FO Chart (Revised Framing)
Script: 11b_grace_fo_chart.py

PURPOSE:
    Replot the GRACE + GRACE-FO data with honest framing:
    - Show early baseline (~2002-2004) as reference band
    - Annotate persistent depletion zone (post-2010)
    - Mark 2022 La Niña recharge as transient anomaly
    - Show GRACE trend line (2002-2017, statistically significant)
    - Do NOT draw a GRACE-FO trend line (p=0.903, not significant)
    - Emphasise "locked in depleted state" over "continuing decline"

INPUT:
    ../data/processed/grace_mascon_tws_raw.csv

OUTPUT:
    ../outputs/grace_fo_extended_trend.png  (overwrites)
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch
from scipy import stats
import os

# ─────────────────────────────────────────────
# 1. LOAD DATA
# ─────────────────────────────────────────────
csv_path = '../data/processed/grace_mascon_tws_raw.csv'
df = pd.read_csv(csv_path)
df_clean = df.dropna(subset=['tws_anomaly']).copy()

grace_df = df_clean[df_clean['year'] <= 2017]
fo_df    = df_clean[df_clean['year'] >= 2019]   # skip 2018 gap

years_grace = grace_df['year'].values
tws_grace   = grace_df['tws_anomaly'].values

slope, intercept, r, p, se = stats.linregress(years_grace, tws_grace)

# Early baseline: mean of first 3 GRACE years (2002-2004)
baseline_val  = df_clean[df_clean['year'] <= 2004]['tws_anomaly'].mean()
# Depletion floor: mean of 2011-2017 (stable depleted plateau)
depleted_mean = df_clean[
    (df_clean['year'] >= 2011) & (df_clean['year'] <= 2017)
]['tws_anomaly'].mean()

print(f"Early baseline (2002–2004): {baseline_val:.2f} cm")
print(f"Depleted plateau (2011–2017): {depleted_mean:.2f} cm")
print(f"GRACE trend: slope={slope:.4f}, r={r:.3f}, p={p:.4f}")

# ─────────────────────────────────────────────
# 2. PLOT
# ─────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(14, 7))
fig.patch.set_facecolor('#0d1117')
ax.set_facecolor('#0d1117')

ALL_YEARS = df['year'].values
Y_MIN, Y_MAX = -36, -4

# ── Background era bands ──
ax.axvspan(2001.5, 2017.5, alpha=0.07, color='#58a6ff', zorder=0)
ax.axvspan(2018.5, 2024.5, alpha=0.07, color='#3fb950', zorder=0)

# ── Early baseline band ──
ax.axhspan(baseline_val - 1.5, baseline_val + 1.5,
           alpha=0.18, color='#f0e68c', zorder=1)
ax.axhline(baseline_val, color='#f0e68c', lw=1.2, ls='--', alpha=0.7, zorder=2)
ax.text(2001.7, baseline_val + 0.5,
        f'Early baseline\n({baseline_val:.0f} cm, 2002–04)',
        color='#f0e68c', fontsize=8, va='bottom', ha='left')

# ── Persistent depletion zone shading (2011 onward, excluding 2022) ──
ax.axhspan(depleted_mean - 4, depleted_mean + 4,
           xmin=(2011 - 2001.5) / (2024.5 - 2001.5),
           alpha=0.10, color='#f85149', zorder=1)
ax.axhline(depleted_mean, color='#f85149', lw=1.0,
           ls=':', alpha=0.5, zorder=2,
           xmin=(2011 - 2001.5) / (2024.5 - 2001.5))

# ── Gap year vertical marker ──
ax.axvline(x=2018, color='#8b949e', lw=1, ls='--', alpha=0.5, zorder=2)
ax.text(2018.05, Y_MIN + 1.5, 'Satellite\ngap', color='#8b949e',
        fontsize=7.5, va='bottom', ha='left')

# ── GRACE data line ──
ax.plot(grace_df['year'], grace_df['tws_anomaly'],
        'o-', color='#58a6ff', lw=2.2, ms=5.5, zorder=4,
        label='GRACE TWS anomaly (2002–2017)')

# ── GRACE-FO data line ──
ax.plot(fo_df['year'], fo_df['tws_anomaly'],
        's-', color='#3fb950', lw=2.2, ms=5.5, zorder=4,
        label='GRACE-FO TWS anomaly (2019–2024)')

# ── GRACE trend line (significant) ──
x_fit = np.linspace(2002, 2017, 200)
y_fit = slope * x_fit + intercept
ax.plot(x_fit, y_fit, '--', color='#f78166', lw=2.2, alpha=0.9, zorder=3,
        label=f'GRACE trend: {slope:.3f} cm/yr  (r={r:.3f}, p={p:.3f})')

# ── Annotate 2022 La Nina rebound ──
val_2022 = df_clean[df_clean['year'] == 2022]['tws_anomaly'].values[0]
ax.annotate(
    'La Niña 2022\n(transient recharge)',
    xy=(2022, val_2022),
    xytext=(2020.3, val_2022 + 6.5),
    color='#ffa657',
    fontsize=8.5,
    arrowprops=dict(arrowstyle='->', color='#ffa657', lw=1.3),
    bbox=dict(boxstyle='round,pad=0.3', fc='#161b22',
              ec='#ffa657', alpha=0.9)
)

# ── Annotate persistent depletion post-2023 ──
val_2023 = df_clean[df_clean['year'] == 2023]['tws_anomaly'].values[0]
ax.annotate(
    'Returns to depleted\nstate in 2023–24',
    xy=(2023.5, (val_2023 + fo_df[fo_df['year'] == 2024]
                 ['tws_anomaly'].values[0]) / 2),
    xytext=(2021.2, -9),
    color='#3fb950',
    fontsize=8.5,
    arrowprops=dict(arrowstyle='->', color='#3fb950', lw=1.3),
    bbox=dict(boxstyle='round,pad=0.3', fc='#161b22',
              ec='#3fb950', alpha=0.9)
)

# ── Structural depletion depth arrow ──
ax.annotate('', xy=(2001.8, depleted_mean),
            xytext=(2001.8, baseline_val),
            arrowprops=dict(arrowstyle='<->', color='#ff7b72', lw=1.5))
depth = abs(depleted_mean - baseline_val)
ax.text(2002.2, (depleted_mean + baseline_val) / 2,
        f'~{depth:.0f} cm\nstructural\ndepletion',
        color='#ff7b72', fontsize=8, va='center', ha='left')

# ── Stats box ──
stats_text = (
    f"GRACE (2002–2017)\n"
    f"slope = {slope:.3f} cm/yr\n"
    f"r = {r:.3f},  p = {p:.4f}\n"
    f"Statistically significant ✓\n\n"
    f"GRACE-FO (2019–2024)\n"
    f"r = −0.065,  p = 0.903\n"
    f"No new trend detectable\n"
    f"(6 yrs, high variability)\n"
    f"But TWS remains depressed"
)
ax.text(0.985, 0.97, stats_text,
        transform=ax.transAxes,
        color='#e6edf3', fontsize=8.2,
        va='top', ha='right',
        bbox=dict(boxstyle='round,pad=0.55',
                  facecolor='#161b22',
                  edgecolor='#30363d', alpha=0.92))

# ── Era labels ──
ax.text(2009.5, Y_MIN + 1.2, 'GRACE', color='#58a6ff',
        fontsize=9, ha='center', alpha=0.7, style='italic')
ax.text(2021.5, Y_MIN + 1.2, 'GRACE-FO', color='#3fb950',
        fontsize=9, ha='center', alpha=0.7, style='italic')

# ── Zero line ──
ax.axhline(0, color='#8b949e', lw=0.7, alpha=0.4)

# ── Axes styling ──
ax.set_xlim(2001.5, 2024.8)
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
ax.legend(loc='lower left', fontsize=8.8,
          facecolor='#161b22', edgecolor='#30363d',
          labelcolor='#e6edf3', framealpha=0.92)

plt.tight_layout()

os.makedirs('../outputs', exist_ok=True)
out_path = 'C:/Users/user/OneDrive/Nasa_2026/PRAAN/outputs/grace_fo_extended_trend.png'
plt.savefig(out_path, dpi=150, bbox_inches='tight',
            facecolor='#0d1117')
plt.close()

print(f"\n✓ Chart saved → {out_path}")
print("\nFraming: 'Aquifer locked in depleted state' — not 'trend continues'")
print("This is the honest and scientifically stronger claim.")
