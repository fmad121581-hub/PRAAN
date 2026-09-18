"""
PRAAN — Phase 1: Signal Validation
Script: 03_signal_validation.py

PURPOSE:
    Core scientific question:
    Does satellite-observed Aman-season environmental stress
    (CHIRPS rainfall anomaly + MODIS NDVI anomaly) significantly
    improve prediction of detrended Aman yield anomaly compared
    to a trend-only baseline?

    Tests:
    1. Contemporaneous correlation (rainfall_t vs yield_t)
    2. Lagged correlation (rainfall_t-1 vs yield_t) — less relevant
       for same-season crop, but check anyway
    3. Baseline model: trend-only prediction
    4. Satellite model: trend + CHIRPS + NDVI
    5. Out-of-sample validation: train on 70%, test on 30%
    6. Feature importance

INPUT:
    data/processed/bbs_yield_anomaly.csv
    data/processed/chirps_aman_season_raw.csv
    data/processed/modis_ndvi_aman_raw.csv

OUTPUT:
    data/processed/merged_panel.csv
    outputs/correlation_heatmap.png
    outputs/scatter_rainfall_vs_yield.png
    outputs/model_comparison.png
    outputs/validation_results.txt

AUTHOR: PRAAN Team
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
from scipy import stats
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_absolute_error
from sklearn.model_selection import LeaveOneOut, cross_val_score
import warnings
import os

warnings.filterwarnings('ignore')
os.makedirs('../outputs', exist_ok=True)

# ─────────────────────────────────────────────
# 1. LOAD ALL THREE DATASETS
# ─────────────────────────────────────────────

yield_df  = pd.read_csv('C:/Users/user/OneDrive/Nasa_2026/PRAAN/data/processed/bbs_yield_anomaly.csv')
chirps_df = pd.read_csv('C:/Users/user/OneDrive/Nasa_2026/PRAAN/data/processed/chirps_aman_season_raw.csv')
ndvi_df   = pd.read_csv('C:/Users/user/OneDrive/Nasa_2026/PRAAN/data/processed/modis_ndvi_aman_raw.csv')

print("Loaded datasets:")
print(f"  Yield:  {yield_df.shape}  | years {yield_df['year'].min()}–{yield_df['year'].max()}")
print(f"  CHIRPS: {chirps_df.shape} | years {chirps_df['year'].min()}–{chirps_df['year'].max()}")
print(f"  NDVI:   {ndvi_df.shape}   | years {ndvi_df['year'].min()}–{ndvi_df['year'].max()}")

print("\nYield columns:", yield_df.columns.tolist())
print("Yield district values:", yield_df['district'].unique())
print("\nCHIRPS columns:", chirps_df.columns.tolist())
print("CHIRPS district values:", chirps_df['district'].unique())
print("\nYield year sample:", sorted(yield_df['year'].unique())[:5])
print("CHIRPS year sample:", sorted(chirps_df['year'].unique())[:5])

# ─────────────────────────────────────────────
# 2. COMPUTE SATELLITE ANOMALIES
# ─────────────────────────────────────────────
# Anomaly = z-score against full historical baseline
# This matches the critique's requirement:
# "NDVI is 1.8 std deviations below expected" not "NDVI dropped 20%"

def compute_anomaly(df, value_col, group_col='district'):
    """
    Compute z-score anomaly relative to district-level baseline.
    Returns df with new column: {value_col}_anomaly
    """
    df = df.copy()
    baseline = df.groupby(group_col)[value_col].agg(['mean', 'std'])

    def z_score(row):
        mu  = baseline.loc[row[group_col], 'mean']
        sig = baseline.loc[row[group_col], 'std']
        if sig > 0:
            return (row[value_col] - mu) / sig
        return np.nan

    df[f'{value_col}_anomaly'] = df.apply(z_score, axis=1)
    return df

print("\nAnomalies computed.")

# ─────────────────────────────────────────────
# 3. MERGE INTO PANEL DATASET
# ─────────────────────────────────────────────

# Rename year_end to year for merging
yield_df = yield_df.rename(columns={'year_end': 'year'})

# CHIRPS has 4 individual districts; yield has division aggregate
# Average the 4 districts into one division-level rainfall value
chirps_df = (
    chirps_df.groupby('year')['rainfall_mm']
    .mean()
    .reset_index()
)
chirps_df['district'] = 'Rajshahi Division'

# Same for NDVI
ndvi_df = (
    ndvi_df.groupby('year')['ndvi_mean']
    .mean()
    .reset_index()
)
ndvi_df['district'] = 'Rajshahi Division'

chirps_df = compute_anomaly(chirps_df, 'rainfall_mm')
ndvi_df   = compute_anomaly(ndvi_df,   'ndvi_mean')

# CHIRPS covers 1984-2022, yield goes back to 1970
# Merge on overlapping years only
# Rename year_end to year for merging
yield_df = yield_df.rename(columns={'year_end': 'year'})

# CHIRPS covers 1984-2022, yield goes back to 1970
# Merge on overlapping years only
panel = (
    yield_df[['year', 'district', 'yield_mton_ha',
               'loess_residual', 'z_score', 'deficit']]
    .merge(
        chirps_df[['year', 'district',
                   'rainfall_mm', 'rainfall_mm_anomaly']],
        on=['year', 'district'], how='left'
    )
    .merge(
        ndvi_df[['year', 'district',
                 'ndvi_mean', 'ndvi_mean_anomaly']],
        on=['year', 'district'], how='left'
    )
    .sort_values(['district', 'year'])
    .reset_index(drop=True)
)

print(f"\nMerged panel: {panel.shape}")
print(f"Missing values:\n{panel.isnull().sum()}")

panel.to_csv('C:/Users/user/OneDrive/Nasa_2026/PRAAN/data/processed/merged_panel.csv', index=False)

# ─────────────────────────────────────────────
# 4. CONTEMPORANEOUS CORRELATIONS
# ─────────────────────────────────────────────

print("\n=== CONTEMPORANEOUS CORRELATIONS ===")
print("Pearson r: satellite anomaly vs yield z-score\n")

corr_results = []

for district in sorted(panel['district'].unique()):
    d = panel[panel['district'] == district].dropna(
        subset=['rainfall_mm_anomaly', 'z_score']
    )

    if len(d) < 5:
        continue

    # CHIRPS vs yield
    r_rain, p_rain = stats.pearsonr(
        d['rainfall_mm_anomaly'], d['z_score']
    )

    # NDVI vs yield (shorter series — 2000 onwards)
    d_ndvi = d.dropna(subset=['ndvi_mean_anomaly'])
    if len(d_ndvi) >= 5:
        r_ndvi, p_ndvi = stats.pearsonr(
            d_ndvi['ndvi_mean_anomaly'], d_ndvi['z_score']
        )
    else:
        r_ndvi, p_ndvi = np.nan, np.nan

    corr_results.append({
        'district'       : district,
        'n_rainfall'     : len(d),
        'r_rainfall'     : round(r_rain, 3),
        'p_rainfall'     : round(p_rain, 3),
        'sig_rainfall'   : '✓' if p_rain < 0.05 else '✗',
        'n_ndvi'         : len(d_ndvi),
        'r_ndvi'         : round(r_ndvi, 3) if not np.isnan(r_ndvi) else '—',
        'p_ndvi'         : round(p_ndvi, 3) if not np.isnan(p_ndvi) else '—',
        'sig_ndvi'       : '✓' if (not np.isnan(p_ndvi) and p_ndvi < 0.05) else '✗'
    })

    print(f"{district}:")
    print(f"  CHIRPS rainfall → yield: r={r_rain:.3f}, p={p_rain:.3f} "
          f"{'✓ significant' if p_rain < 0.05 else '✗ not significant'}")
    if not np.isnan(r_ndvi):
        print(f"  MODIS NDVI     → yield: r={r_ndvi:.3f}, p={p_ndvi:.3f} "
              f"{'✓ significant' if p_ndvi < 0.05 else '✗ not significant'}")

corr_df = pd.DataFrame(corr_results)

# ─────────────────────────────────────────────
# 5. SCATTER PLOTS — RAINFALL ANOMALY VS YIELD
# ─────────────────────────────────────────────

districts = sorted(panel['district'].unique())
ncols = 2
nrows = int(np.ceil(len(districts) / ncols))

fig, axes = plt.subplots(nrows, ncols,
                          figsize=(12, 4 * nrows))
axes = axes.flatten()

for idx, district in enumerate(districts):
    d = panel[panel['district'] == district].dropna(
        subset=['rainfall_mm_anomaly', 'z_score']
    )
    ax = axes[idx]

    # Colour by deficit/surplus
    colors = ['#d73027' if def_ else '#4575b4'
              for def_ in d['deficit']]

    ax.scatter(d['rainfall_mm_anomaly'], d['z_score'],
               c=colors, s=60, edgecolors='grey',
               linewidths=0.5, zorder=3)

    # Regression line
    if len(d) >= 5:
        m, b, r, p, _ = stats.linregress(
            d['rainfall_mm_anomaly'], d['z_score']
        )
        x_line = np.linspace(
            d['rainfall_mm_anomaly'].min(),
            d['rainfall_mm_anomaly'].max(), 100
        )
        ax.plot(x_line, m * x_line + b, 'k-', lw=1.5,
                label=f'r={r:.2f}, p={p:.3f}')
        ax.legend(fontsize=8)

    # Label deficit years
    for _, row in d[d['deficit']].iterrows():
        ax.annotate(str(int(row['year'])),
                    (row['rainfall_mm_anomaly'], row['z_score']),
                    fontsize=7, ha='left', va='bottom',
                    xytext=(3, 3), textcoords='offset points')

    ax.axhline(0, color='grey', lw=0.8, ls='--')
    ax.axvline(0, color='grey', lw=0.8, ls='--')
    ax.axhline(-1, color='red', lw=0.8, ls=':', alpha=0.7)

    ax.set_title(f'{district}', fontsize=10, fontweight='bold')
    ax.set_xlabel('CHIRPS Rainfall Anomaly (z-score)', fontsize=8)
    ax.set_ylabel('Yield Anomaly (z-score)',           fontsize=8)
    ax.grid(alpha=0.3)

# Hide unused subplots
for idx in range(len(districts), len(axes)):
    axes[idx].set_visible(False)

plt.suptitle(
    'Aman-Season Rainfall Anomaly vs Detrended Yield Anomaly\n'
    'Rajshahi Division Districts | Red = deficit year (z < −1)',
    fontsize=11, fontweight='bold', y=1.01
)
plt.tight_layout()
plt.savefig('../outputs/scatter_rainfall_vs_yield.png',
            dpi=150, bbox_inches='tight')
plt.close()
print("\nScatter plot saved → outputs/scatter_rainfall_vs_yield.png")

# ─────────────────────────────────────────────
# 6. MODEL COMPARISON: BASELINE vs SATELLITE
# ─────────────────────────────────────────────
# Key question for NASA judges:
# Does adding satellite variables improve prediction
# over a trend-only baseline?

# Use Rajshahi district for this demonstration
# (replicate for all districts in final version)

TARGET_DISTRICT = 'Rajshahi Division'

d_model = (
    panel[panel['district'] == TARGET_DISTRICT]
    .dropna(subset=['rainfall_mm_anomaly', 'z_score'])
    .sort_values('year')
    .reset_index(drop=True)
)

print(f"Available districts in panel: {panel['district'].unique()}")
print(f"Rows with rainfall data: {panel['rainfall_mm_anomaly'].notna().sum()}")
print(f"Filtered to {TARGET_DISTRICT}: {len(d_model)} rows")

print(f"\n=== MODEL COMPARISON: {TARGET_DISTRICT} ===")
print(f"n = {len(d_model)} observations\n")

# Feature sets
X_baseline  = d_model[['year']].values             # trend only
X_satellite = d_model[[
    'year', 'rainfall_mm_anomaly'
]].values                                            # trend + CHIRPS

# Add NDVI where available
d_ndvi_model = d_model.dropna(subset=['ndvi_mean_anomaly'])
X_full = d_ndvi_model[[
    'year', 'rainfall_mm_anomaly', 'ndvi_mean_anomaly'
]].values

y_all  = d_model['z_score'].values
y_ndvi = d_ndvi_model['z_score'].values

# Leave-One-Out Cross-Validation
# (appropriate for small samples — each year held out once)
loo = LeaveOneOut()

def loo_r2(X, y):
    """LOO cross-validated R² for Linear Regression."""
    preds = []
    for train_idx, test_idx in loo.split(X):
        model = LinearRegression()
        model.fit(X[train_idx], y[train_idx])
        preds.append(model.predict(X[test_idx])[0])
    preds = np.array(preds)
    ss_res = np.sum((y - preds) ** 2)
    ss_tot = np.sum((y - y.mean()) ** 2)
    return 1 - ss_res / ss_tot

r2_baseline  = loo_r2(X_baseline,  y_all)
r2_satellite = loo_r2(X_satellite, y_all)

print("Leave-One-Out Cross-Validated R²:")
print(f"  Baseline  (trend only)        : {r2_baseline:.3f}")
print(f"  Satellite (trend + CHIRPS)    : {r2_satellite:.3f}")

if len(d_ndvi_model) >= 10:
    r2_full = loo_r2(X_full, y_ndvi)
    print(f"  Full      (trend + CHIRPS + NDVI): {r2_full:.3f}")

print()

# Interpretation
delta = r2_satellite - r2_baseline
print(f"ΔR² from adding CHIRPS: {delta:+.3f}")

if delta > 0.10:
    print("✓ CHIRPS meaningfully improves prediction (ΔR² > 0.10)")
    print("  → Satellite signal is useful for this district")
elif delta > 0:
    print("~ CHIRPS improves prediction marginally")
    print("  → Investigate further; may need additional signals")
else:
    print("✗ CHIRPS does NOT improve prediction")
    print("  → Reconsider signal choice for this district")

# ─────────────────────────────────────────────
# 7. VISUAL: PREDICTED vs ACTUAL ANOMALY
# ─────────────────────────────────────────────

# Fit final satellite model on all data (for plotting)
sat_model = LinearRegression()
sat_model.fit(X_satellite, y_all)
y_pred = sat_model.predict(X_satellite)

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Left: time series comparison
axes[0].plot(d_model['year'], y_all,   'ko-', ms=5,
             lw=1.5, label='Actual yield anomaly')
axes[0].plot(d_model['year'], y_pred,  'r--', ms=4,
             lw=2, label='Satellite model prediction')
axes[0].axhline(-1, color='red', ls=':', lw=1, alpha=0.7,
                label='Deficit threshold')
axes[0].fill_between(d_model['year'], y_all, y_pred,
                      alpha=0.2, color='grey')
axes[0].set_title(f'{TARGET_DISTRICT}: Actual vs Predicted\n'
                  f'Satellite model (CHIRPS + trend)',
                  fontsize=10)
axes[0].set_xlabel('Year')
axes[0].set_ylabel('Yield z-score')
axes[0].legend(fontsize=8)
axes[0].grid(alpha=0.3)

# Right: actual vs predicted scatter
axes[1].scatter(y_all, y_pred, c='#4575b4',
                edgecolors='grey', s=60)
lim = max(abs(y_all).max(), abs(y_pred).max()) + 0.3
axes[1].plot([-lim, lim], [-lim, lim], 'k--', lw=1)
axes[1].set_xlim(-lim, lim)
axes[1].set_ylim(-lim, lim)
axes[1].set_xlabel('Actual yield anomaly (z-score)')
axes[1].set_ylabel('Predicted yield anomaly (z-score)')
axes[1].set_title(f'Actual vs Predicted\nLOO R² = {r2_satellite:.3f}',
                  fontsize=10)
axes[1].grid(alpha=0.3)

plt.tight_layout()
plt.savefig('../outputs/model_comparison.png',
            dpi=150, bbox_inches='tight')
plt.close()
print("\nModel comparison plot saved → outputs/model_comparison.png")

# ─────────────────────────────────────────────
# 8. SAVE VALIDATION RESULTS
# ─────────────────────────────────────────────

with open('C:/Users/user/OneDrive/Nasa_2026/PRAAN/outputs/validation_results.txt', 'w', encoding='utf-8') as f:
    f.write("PRAAN Phase 1 — Signal Validation Results\n")
    f.write("=" * 50 + "\n\n")

    f.write("CORRELATION RESULTS:\n")
    f.write(corr_df.to_string(index=False))
    f.write("\n\n")

    f.write(f"MODEL COMPARISON ({TARGET_DISTRICT}):\n")
    f.write(f"  LOO R² Baseline  (trend only)     : {r2_baseline:.3f}\n")
    f.write(f"  LOO R² Satellite (trend + CHIRPS)  : {r2_satellite:.3f}\n")
    f.write(f"  Delta R²                           : {delta:+.3f}\n\n")

    f.write("DEFICIT YEARS IDENTIFIED:\n")
    deficit_summary = (
        panel[panel['deficit'] == True]
        .groupby('district')['year']
        .apply(list)
        .to_string()
    )
    f.write(deficit_summary)

print("\nFull results saved → outputs/validation_results.txt")
print("\n✓ Script 03 complete.")
print("\nREAD THE RESULTS CAREFULLY BEFORE PROCEEDING.")
print("If ΔR² > 0.10 for most districts → Phase 2 is justified.")
print("If ΔR² ≈ 0 or negative → stop and redesign the signal.")
