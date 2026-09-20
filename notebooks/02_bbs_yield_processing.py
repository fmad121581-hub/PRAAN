"""
PRAAN — Phase 1: BBS Yield Processing & Detrending
Script: 02_bbs_yield_processing.py

PURPOSE:
    1. Load BBS district Aman yield data (manually entered Excel)
    2. Calculate yield rate from area + production
    3. Detrend using multiple methods — compare robustness
    4. Compute standardised anomaly (z-score) per district
    5. Flag deficit years (z < -1.0)

INPUT:
    data/raw/bbs/aman_district_raw.xlsx
    Columns: year | district | area_acres | production_mton

OUTPUT:
    data/processed/bbs_yield_anomaly.csv
    outputs/detrending_comparison.png

AUTHOR: PRAAN Team
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from scipy import stats
from statsmodels.nonparametric.smoothers_lowess import lowess
import warnings
import os

# Paths resolve from this file's own location, so the scripts run unchanged
# on any machine. _R is the project root; _R2 its parent.
_R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace('\\', '/') + '/'
_R2 = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))).replace('\\', '/') + '/'

warnings.filterwarnings('ignore')
os.makedirs('../data/processed', exist_ok=True)
os.makedirs('../outputs', exist_ok=True)

# ─────────────────────────────────────────────
# 1. LOAD AND VALIDATE BBS DATA
# ─────────────────────────────────────────────

df = pd.read_excel(
    _R + 'data/raw/bbs/PRAAN_BBS_Aman_FIXED_v2.xlsx',
    sheet_name='division_aggregate'
)

# Validate expected columns
expected_cols = {'year_end', 'yield_tons_per_ha'}
assert expected_cols.issubset(df.columns), \
    f"Missing columns: {expected_cols - set(df.columns)}"

print(f"Loaded {len(df)} records")
print(f"Year range: {df['year_end'].min()} – {df['year_end'].max()}")
print(f"Missing values:\n{df.isnull().sum()}\n")

# ─────────────────────────────────────────────
# 2. CALCULATE YIELD RATE
# ─────────────────────────────────────────────
# yield (M.ton/ha) = production (M.ton) / area (ha)
# 1 acre = 0.404686 hectares

ACRE_TO_HA = 0.404686

# Yield already calculated in fixed Excel
df['yield_mton_ha'] = df['yield_tons_per_ha']
df['district']      = 'Rajshahi Division'

# Exclude flagged rows
df = df[~df['exclude'].fillna(False)].copy()

yield_min = df['yield_mton_ha'].min()
yield_max = df['yield_mton_ha'].max()
print(f"Yield range: {yield_min:.3f} – {yield_max:.3f} t/ha")
print(f"Usable rows after exclusions: {len(df)}")

# ─────────────────────────────────────────────
# 3. DETRENDING — PER DISTRICT
# ─────────────────────────────────────────────
# Test three methods. Use LOESS as primary — it makes
# no assumptions about functional form of trend.
# Check that residuals are consistent across methods.

LOESS_FRAC = 0.4     # smoothing bandwidth — 40% of data
                      # adjust if trend looks over/under-smoothed

districts = df['district'].unique()
results   = []

fig = plt.figure(figsize=(16, 5 * len(districts)))
gs  = gridspec.GridSpec(len(districts), 3, figure=fig)
gs.update(hspace=0.4, wspace=0.35)

for i, district in enumerate(sorted(districts)):

    d = df[df['district'] == district].sort_values('year_end').copy()
    years  = d['year_end'].values.astype(float)
    yields = d['yield_mton_ha'].values

    # Skip districts with < 10 observations
    if len(d) < 10:
        print(f"⚠ Skipping {district}: only {len(d)} observations")
        continue

    # ── Method 1: Linear OLS ──────────────────
    slope, intercept, r_val, p_val, _ = stats.linregress(years, yields)
    linear_trend    = slope * years + intercept
    linear_residual = yields - linear_trend

    # ── Method 2: Quadratic polynomial ────────
    poly_coeffs     = np.polyfit(years, yields, deg=2)
    poly_trend      = np.polyval(poly_coeffs, years)
    poly_residual   = yields - poly_trend

    # ── Method 3: LOESS (primary) ─────────────
    loess_out       = lowess(yields, years, frac=LOESS_FRAC,
                             return_sorted=True)
    loess_trend     = loess_out[:, 1]
    loess_residual  = yields - loess_trend

    # ── Standardise LOESS residual to z-score ──
    loess_mean = loess_residual.mean()
    loess_std  = loess_residual.std(ddof=1)
    z_scores   = (loess_residual - loess_mean) / loess_std

    # ── Collect results ────────────────────────
    for j, year in enumerate(years):
        results.append({
            'year'             : int(year),
            'district'         : district,
            'yield_mton_ha'    : yields[j],
            'linear_residual'  : linear_residual[j],
            'poly_residual'    : poly_residual[j],
            'loess_residual'   : loess_residual[j],
            'z_score'          : z_scores[j],
            'deficit'          : z_scores[j] < -1.0    # flag
        })

    # ── Plots ──────────────────────────────────
    # Panel A: Raw yield + all three trends
    ax_a = fig.add_subplot(gs[i, 0])
    ax_a.plot(years, yields, 'k-o', ms=4, lw=1.5, label='Actual')
    ax_a.plot(years, linear_trend, 'b--', lw=1.5, label='Linear')
    ax_a.plot(years, poly_trend,   'g--', lw=1.5, label='Poly')
    ax_a.plot(years, loess_trend,  'r-',  lw=2,   label='LOESS')
    ax_a.set_title(f'{district}\nRaw Yield + Trends', fontsize=9)
    ax_a.set_ylabel('M.ton/ha')
    ax_a.legend(fontsize=7)
    ax_a.grid(alpha=0.3)

    # Panel B: LOESS residual
    ax_b = fig.add_subplot(gs[i, 1])
    colors = ['#d73027' if z < -1.0 else
              '#4575b4' if z > 1.0 else
              '#ffffbf' for z in z_scores]
    ax_b.bar(years, loess_residual, color=colors, edgecolor='grey',
             linewidth=0.3)
    ax_b.axhline(0,    color='k',   lw=1)
    ax_b.axhline(-loess_std, color='r', lw=1, ls='--',
                 label='−1σ threshold')
    ax_b.set_title('LOESS Residual', fontsize=9)
    ax_b.set_ylabel('Residual (M.ton/ha)')
    ax_b.legend(fontsize=7)
    ax_b.grid(alpha=0.3)

    # Panel C: Z-score timeline
    ax_c = fig.add_subplot(gs[i, 2])
    ax_c.fill_between(years, z_scores, 0,
                      where=(z_scores < 0), color='#d73027',
                      alpha=0.6, label='Below trend')
    ax_c.fill_between(years, z_scores, 0,
                      where=(z_scores > 0), color='#4575b4',
                      alpha=0.6, label='Above trend')
    ax_c.axhline(-1.0, color='r', lw=1.5, ls='--',
                 label='Deficit threshold (z=−1)')
    ax_c.set_title('Standardised Anomaly (z-score)', fontsize=9)
    ax_c.set_ylabel('z-score')
    ax_c.legend(fontsize=7)
    ax_c.grid(alpha=0.3)

    # Print deficit years to console
    deficit_yrs = [int(years[j]) for j in range(len(years))
                   if z_scores[j] < -1.0]
    print(f"{district}: deficit years = {deficit_yrs}")

plt.savefig(_R + 'outputs/detrending_comparison.png',
            dpi=150, bbox_inches='tight')
plt.close()
print("\nPlot saved → outputs/detrending_comparison.png")

# ─────────────────────────────────────────────
# 4. SAVE PROCESSED YIELD ANOMALY TABLE
# ─────────────────────────────────────────────

results_df = pd.DataFrame(results)
results_df = results_df.sort_values(
    ['district', 'year']
).reset_index(drop=True)

results_df.to_csv(
    _R + 'data/processed/bbs_yield_anomaly.csv',
    index=False
)

print(f"\nSaved {len(results_df)} records → "
      f"data/processed/bbs_yield_anomaly.csv")

# ─────────────────────────────────────────────
# 5. QUICK SUMMARY TABLE
# ─────────────────────────────────────────────

print("\n=== DEFICIT YEARS BY DISTRICT ===")
print("(LOESS residual z-score < −1.0)\n")

summary = (
    results_df[results_df['deficit'] == True]
    .groupby('district')['year']
    .apply(list)
)
print(summary.to_string())

print("\n=== CROSS-DISTRICT DEFICIT YEARS ===")
print("Years where MULTIPLE districts show deficit simultaneously")
print("(These are your strongest validation candidates)\n")

deficit_counts = (
    results_df[results_df['deficit'] == True]
    .groupby('year')['district']
    .count()
    .reset_index()
    .rename(columns={'district': 'n_districts_in_deficit'})
    .sort_values('year')
)
print(deficit_counts[
    deficit_counts['n_districts_in_deficit'] >= 2
].to_string(index=False))

print("\n✓ Script 02 complete.")
print("Next: run 03_signal_validation.py")
