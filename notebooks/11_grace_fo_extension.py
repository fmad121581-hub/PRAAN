"""
PRAAN — Phase 1 Extension: GRACE + GRACE-FO Combined Trend (2002–2024)
Script: 11_grace_fo_extension.py

PURPOSE:
    Replace the LAND product (ends 2017) with MASCON_CRI (2002–2024),
    which seamlessly bridges GRACE and GRACE-FO in a single collection.
    Re-runs the same trend analysis and produces an updated chart
    showing the signal continues post-2017.

UPGRADE NOTE:
    MASCON_CRI (JPL RL06.3Mv04) is a higher-quality product than
    MASS_GRIDS_V04/LAND — lower noise, better spatial resolution.
    Band: lwe_thickness (cm equivalent water thickness)

OUTPUT:
    data/processed/grace_mascon_tws_raw.csv
    outputs/grace_fo_extended_trend.png   ← replaces grace_trend.png

AUTHOR: PRAAN Team
"""

import ee
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from scipy import stats
import os
import time

# ─────────────────────────────────────────────
# 0. INITIALISE EARTH ENGINE
# ─────────────────────────────────────────────
ee.Initialize(project='project-attempt-dhaka-heat')

# ─────────────────────────────────────────────
# 1. STUDY AREA — same as Script 01
# ─────────────────────────────────────────────
BARIND_DISTRICTS = [
    'Rajshahi',
    'Naogaon',
    'Chapai Nawabganj',
    'Natore',
    'Nawabganj'
]

bangladesh_districts = (
    ee.FeatureCollection('FAO/GAUL/2015/level2')
    .filter(ee.Filter.eq('ADM0_NAME', 'Bangladesh'))
)

rajshahi_div = bangladesh_districts.filter(
    ee.Filter.inList('ADM2_NAME', BARIND_DISTRICTS)
)

study_area = rajshahi_div.geometry()

# ─────────────────────────────────────────────
# 2. GRACE + GRACE-FO MASCON EXTRACTION
# ─────────────────────────────────────────────
# MASCON_CRI: JPL RL06.3Mv04 — covers 2002-03 to present (2024+)
# Single collection, no stitching needed — GEE handles GRACE/GRACE-FO
# Band: lwe_thickness (cm) — equivalent water thickness anomaly
# Scale: 0.5° (~55 km) but mascon resolution is effectively ~300 km

mascon = ee.ImageCollection('NASA/GRACE/MASS_GRIDS_V04/MASCON_CRI') \
           .select('lwe_thickness')

GRACE_START = 2002
GRACE_END   = 2024   # update this each year

print("=" * 60)
print("PRAAN — GRACE + GRACE-FO Extended Extraction")
print(f"Collection: NASA/GRACE/MASS_GRIDS_V04/MASCON_CRI")
print(f"Period:     {GRACE_START}–{GRACE_END}")
print(f"Season:     Jan–May (pre-Aman, captures Boro drawdown)")
print("=" * 60)

all_records = []

for year in range(GRACE_START, GRACE_END + 1):
    try:
        # Pre-Aman season: Jan–May captures groundwater drawdown
        # from Boro (dry season) irrigation — same window as Script 01
        start = ee.Date.fromYMD(year, 1, 1)
        end   = ee.Date.fromYMD(year, 5, 31)

        # Mean TWS anomaly over the season
        seasonal_mean = mascon.filterDate(start, end).mean()

        # Check if images exist for this period
        count = mascon.filterDate(start, end).size().getInfo()

        if count == 0:
            print(f"  – {year}: no GRACE images for Jan–May (gap year)")
            all_records.append({
                'year'        : year,
                'tws_anomaly' : np.nan,
                'image_count' : 0
            })
            continue

        # Extract mean over study area
        stats_dict = seasonal_mean.reduceRegion(
            reducer   = ee.Reducer.mean(),
            geometry  = study_area,
            scale     = 55000,    # ~MASCON resolution
            maxPixels = 1e9,
            bestEffort= True
        ).getInfo()

        tws_val = stats_dict.get('lwe_thickness', np.nan)

        all_records.append({
            'year'        : year,
            'tws_anomaly' : tws_val,
            'image_count' : count
        })

        mission = "GRACE-FO" if year >= 2018 else "GRACE   "
        print(f"  ✓ {year} [{mission}]  TWS = {tws_val:.3f} cm  "
              f"({count} images)")

        time.sleep(0.3)

    except Exception as e:
        print(f"  ✗ {year} failed: {e}")
        all_records.append({
            'year'        : year,
            'tws_anomaly' : np.nan,
            'image_count' : 0
        })

# ─────────────────────────────────────────────
# 3. SAVE RAW OUTPUT
# ─────────────────────────────────────────────
df = pd.DataFrame(all_records)
df = df.sort_values('year').reset_index(drop=True)

os.makedirs('../data/processed', exist_ok=True)
csv_path = '../data/processed/grace_mascon_tws_raw.csv'
df.to_csv(csv_path, index=False)
print(f"\nRaw data saved → {csv_path}")
print(df.to_string(index=False))

# ─────────────────────────────────────────────
# 4. TREND ANALYSIS — FULL PERIOD + SUB-PERIODS
# ─────────────────────────────────────────────
# Drop gap years (2017-06 to 2018-06 — GRACE ended, GRACE-FO not yet)
df_clean = df.dropna(subset=['tws_anomaly']).copy()

years_all = df_clean['year'].values
tws_all   = df_clean['tws_anomaly'].values

# Full trend (2002–2024)
slope_all, intercept_all, r_all, p_all, se_all = stats.linregress(
    years_all, tws_all
)

# Legacy period (2002–2017) — should match Script 03 results
df_legacy = df_clean[df_clean['year'] <= 2017]
slope_leg, intercept_leg, r_leg, p_leg, se_leg = stats.linregress(
    df_legacy['year'].values, df_legacy['tws_anomaly'].values
)

# GRACE-FO period only (2018–2024)
df_fo = df_clean[df_clean['year'] >= 2018]
if len(df_fo) >= 3:
    slope_fo, intercept_fo, r_fo, p_fo, se_fo = stats.linregress(
        df_fo['year'].values, df_fo['tws_anomaly'].values
    )
else:
    slope_fo = r_fo = p_fo = np.nan

print("\n" + "=" * 60)
print("TREND RESULTS")
print("=" * 60)
print(f"Full period  (2002–{GRACE_END}): "
      f"slope={slope_all:.4f} cm/yr, r={r_all:.3f}, p={p_all:.4f}")
print(f"Legacy GRACE (2002–2017):    "
      f"slope={slope_leg:.4f} cm/yr, r={r_leg:.3f}, p={p_leg:.4f}")
if not np.isnan(slope_fo):
    print(f"GRACE-FO     (2018–{GRACE_END}):  "
          f"slope={slope_fo:.4f} cm/yr, r={r_fo:.3f}, p={p_fo:.4f}")
print("=" * 60)

# ─────────────────────────────────────────────
# 5. PLOT — EXTENDED TREND CHART
# ─────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(13, 6))
fig.patch.set_facecolor('#0d1117')
ax.set_facecolor('#0d1117')

# — Color bands: GRACE vs GRACE-FO era —
ax.axvspan(2002, 2017.5, alpha=0.06, color='#58a6ff', zorder=0)
ax.axvspan(2017.5, GRACE_END + 0.5, alpha=0.06, color='#3fb950', zorder=0)

# — Gap annotation (2017 mid-year) —
ax.axvline(x=2017.5, color='#8b949e', lw=1, ls='--', alpha=0.6)
ax.text(2017.55, ax.get_ylim()[0] if ax.get_ylim()[0] != 0 else -4,
        '← GRACE    GRACE-FO →', color='#8b949e',
        fontsize=7.5, va='bottom', ha='left')

# — TWS anomaly line —
grace_data = df_clean[df_clean['year'] <= 2017]
fo_data    = df_clean[df_clean['year'] >= 2018]

ax.plot(grace_data['year'], grace_data['tws_anomaly'],
        'o-', color='#58a6ff', lw=2, ms=5,
        label='GRACE TWS anomaly (2002–2017)', zorder=3)
ax.plot(fo_data['year'], fo_data['tws_anomaly'],
        's-', color='#3fb950', lw=2, ms=5,
        label='GRACE-FO TWS anomaly (2018–present)', zorder=3)

# Mark gap years
gap_years = df[df['tws_anomaly'].isna()]['year'].values
for gy in gap_years:
    ax.axvline(x=gy, color='#f85149', lw=0.8, ls=':', alpha=0.5)

# — Full period trend line —
x_fit = np.linspace(years_all.min(), years_all.max(), 200)
y_fit = slope_all * x_fit + intercept_all
ax.plot(x_fit, y_fit, '--', color='#f78166', lw=2.2, alpha=0.9,
        label=f'Trend 2002–{GRACE_END}: {slope_all:.4f} cm/yr '
              f'(r={r_all:.3f}, p={p_all:.3f})', zorder=4)

# — Zero reference —
ax.axhline(0, color='#8b949e', lw=0.8, ls='-', alpha=0.5)

# — Labels —
ax.set_xlabel('Year', color='#e6edf3', fontsize=11)
ax.set_ylabel('TWS Anomaly (cm equivalent water)', color='#e6edf3', fontsize=11)
ax.set_title(
    'Barind Tract Groundwater Depletion — GRACE + GRACE-FO (2002–2024)\n'
    'Pre-Aman Season (Jan–May) Terrestrial Water Storage Anomaly',
    color='#e6edf3', fontsize=13, fontweight='bold', pad=15
)

# — Trend stats box —
stats_text = (
    f"Full period trend\n"
    f"slope = {slope_all:.4f} cm/yr\n"
    f"r = {r_all:.3f},  p = {p_all:.4f}\n\n"
    f"Legacy GRACE (–2017)\n"
    f"slope = {slope_leg:.4f} cm/yr\n"
    f"r = {r_leg:.3f},  p = {p_leg:.4f}"
)
ax.text(0.02, 0.97, stats_text,
        transform=ax.transAxes,
        color='#e6edf3', fontsize=8.5,
        va='top', ha='left',
        bbox=dict(boxstyle='round,pad=0.5',
                  facecolor='#161b22',
                  edgecolor='#30363d', alpha=0.9))

# — GRACE-FO stats box (bottom right) —
if not np.isnan(slope_fo):
    fo_text = (
        f"GRACE-FO (2018–{GRACE_END})\n"
        f"slope = {slope_fo:.4f} cm/yr\n"
        f"r = {r_fo:.3f},  p = {p_fo:.4f}"
    )
    ax.text(0.98, 0.04, fo_text,
            transform=ax.transAxes,
            color='#3fb950', fontsize=8.5,
            va='bottom', ha='right',
            bbox=dict(boxstyle='round,pad=0.5',
                      facecolor='#161b22',
                      edgecolor='#30363d', alpha=0.9))

# Styling
ax.tick_params(colors='#8b949e', labelsize=9)
for spine in ax.spines.values():
    spine.set_edgecolor('#30363d')
ax.set_xlim(2001, GRACE_END + 1)
ax.xaxis.set_major_locator(plt.MultipleLocator(2))
ax.grid(True, color='#21262d', lw=0.7, alpha=0.8)
ax.legend(loc='upper right', fontsize=8.5,
          facecolor='#161b22', edgecolor='#30363d',
          labelcolor='#e6edf3')

plt.tight_layout()

os.makedirs('../outputs', exist_ok=True)
out_path = '../outputs/grace_fo_extended_trend.png'
plt.savefig(out_path, dpi=150, bbox_inches='tight',
            facecolor='#0d1117')
plt.close()

print(f"\n✓ Chart saved → {out_path}")
print("\nKey question: does the declining trend continue post-2017?")
print("Check the slope and r-value for GRACE-FO period above.")
print("\nNext: if trend continues, update website Layer 1 chart.")
print("      run: 03_signal_validation.py with new CSV for updated stats.")
