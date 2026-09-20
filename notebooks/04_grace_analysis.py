import os
import pandas as pd
import numpy as np
from scipy import stats

# Load data
panel = pd.read_csv(
    _R + 'data/processed/merged_panel.csv'
)

grace_df = pd.read_csv(
    _R + 'data/processed/grace_tws_raw.csv'
)

# Average GRACE across districts to division level
grace_div = (
    grace_df.groupby('year')['tws_anomaly']
    .mean()
    .reset_index()
)

# Compute z-score anomaly
mu  = grace_div['tws_anomaly'].mean()
sig = grace_div['tws_anomaly'].std()
grace_div['tws_z'] = (grace_div['tws_anomaly'] - mu) / sig

# Merge with panel
panel = panel.merge(grace_div[['year', 'tws_anomaly', 'tws_z']],
                    on='year', how='left')

# Test: GRACE TWS vs yield anomaly
test = panel.dropna(subset=['tws_z', 'z_score'])

print(f"Overlapping years for GRACE test: {len(test)}")
print(f"Years: {sorted(test['year'].tolist())}")

r, p = stats.pearsonr(test['tws_z'], test['z_score'])
print(f"\nGRACE TWS anomaly → yield z-score:")
print(f"  r = {r:.3f}, p = {p:.3f} {'✓ significant' if p < 0.05 else '✗ not significant'}")

print("\n=== GRACE TWS in deficit years ===")
deficit_years = [1987, 1988, 1995, 1996, 1997]
print(panel[panel['year'].isin(deficit_years)][
    ['year', 'tws_anomaly', 'tws_z', 'z_score', 'deficit']
].to_string(index=False))

print("\n=== ALL YEARS WITH GRACE DATA ===")
print(panel[panel['tws_anomaly'].notna()][
    ['year', 'tws_anomaly', 'tws_z', 'z_score', 'deficit']
].to_string(index=False))
# Test GRACE declining trend
from scipy import stats
grace_trend = grace_div.sort_values('year')
slope, intercept, r, p, se = stats.linregress(
    grace_trend['year'], grace_trend['tws_anomaly']
)
print(f"\n=== GRACE TREND 2002-2017 ===")
print(f"Slope: {slope:.4f} cm/year")
print(f"r = {r:.3f}, p = {p:.3f}")
print(f"Total decline: {slope * 15:.3f} cm over 15 years")
import matplotlib.pyplot as plt

# Paths resolve from this file's own location, so the scripts run unchanged
# on any machine. _R is the project root; _R2 its parent.
_R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace('\\', '/') + '/'
_R2 = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))).replace('\\', '/') + '/'

fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(grace_trend['year'], grace_trend['tws_anomaly'],
        'b-o', linewidth=2, markersize=8, label='GRACE TWS')

# Trend line
trend_line = slope * grace_trend['year'] + intercept
ax.plot(grace_trend['year'], trend_line, 'r--',
        linewidth=2, label=f'Trend: {slope:.4f} cm/yr (r={r:.3f}, p<0.001)')

ax.axhline(0, color='grey', linewidth=0.8, linestyle='--')
ax.fill_between(grace_trend['year'], grace_trend['tws_anomaly'], 0,
                alpha=0.3, color='blue')
ax.set_title('Rajshahi Division — Groundwater Storage Anomaly\n'
             'NASA GRACE 2002–2017', fontsize=12, fontweight='bold')
ax.set_xlabel('Year')
ax.set_ylabel('Terrestrial Water Storage Anomaly (cm)')
ax.legend()
ax.grid(alpha=0.3)

plt.tight_layout()
plt.savefig(
    _R + 'outputs/grace_trend.png',
    dpi=150, bbox_inches='tight'
)
print("Chart saved.")
plt.show()