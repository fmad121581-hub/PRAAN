"""
PRAAN — Phase 3 Part 2: Absorption Stress Index + Map
Script: 07_phase3_part2.py
"""

import os
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.patches import Patch
import warnings
warnings.filterwarnings('ignore')

SHP_PATH   = _R + "data/raw/shapefiles/gadm41_BGD_4.shp"
CSV_PATH   = _R + "data/processed/praan_phase3_indicators.csv"
OUTPUT_DIR = _R + "outputs/"

# ─────────────────────────────────────────────────────────────
# 1. LOAD DATA
# ─────────────────────────────────────────────────────────────
print("Loading data...")
df = pd.read_csv(CSV_PATH)
gdf = gpd.read_file(SHP_PATH)
dhaka = gdf[gdf['NAME_1'] == 'Dhaka'].copy().reset_index(drop=True)
dhaka = dhaka.to_crs(epsg=4326)

# Merge indicators onto shapefile
merged = dhaka.merge(df[['GID_4','pop','builtup','flood']],
                     on='GID_4', how='left')
print(f"Merged: {len(merged)} wards")
print(f"NaN counts: pop={merged['pop'].isna().sum()}, "
      f"builtup={merged['builtup'].isna().sum()}, "
      f"flood={merged['flood'].isna().sum()}")

# ─────────────────────────────────────────────────────────────
# 2. NORMALIZE INDICATORS (min-max, 0-1)
#    Higher normalized value = more stress in all cases
# ─────────────────────────────────────────────────────────────
print("Normalizing indicators...")

def minmax(series):
    s = series.copy()
    mn, mx = s.min(), s.max()
    return (s - mn) / (mx - mn)

# Fill NaN with median before normalizing
for col in ['pop', 'builtup', 'flood']:
    merged[col] = merged[col].fillna(merged[col].median())

merged['pop_norm']     = minmax(merged['pop'])      # dense = stressed
merged['builtup_norm'] = minmax(merged['builtup'])  # built-up = stressed
merged['flood_norm']   = minmax(merged['flood'])    # flood-prone = stressed

# ─────────────────────────────────────────────────────────────
# 3. ABSORPTION STRESS INDEX
#    Weighted sum — weights must sum to 1.0
# ─────────────────────────────────────────────────────────────
WEIGHTS = {
    'pop':     0.40,   # crowding — strongest signal
    'builtup': 0.35,   # land already consumed
    'flood':   0.25,   # environmental vulnerability
}

merged['ASI'] = (
    merged['pop_norm']     * WEIGHTS['pop']     +
    merged['builtup_norm'] * WEIGHTS['builtup'] +
    merged['flood_norm']   * WEIGHTS['flood']
)

print(f"\nASI summary:")
print(f"  Min:    {merged['ASI'].min():.3f}")
print(f"  Max:    {merged['ASI'].max():.3f}")
print(f"  Mean:   {merged['ASI'].mean():.3f}")
print(f"  Median: {merged['ASI'].median():.3f}")

# Classify into stress tiers
merged['stress_tier'] = pd.cut(
    merged['ASI'],
    bins=[0, 0.33, 0.66, 1.01],
    labels=['Low stress', 'Moderate stress', 'High stress']
)

tier_counts = merged['stress_tier'].value_counts()
print(f"\nStress tiers:")
for tier, count in tier_counts.items():
    print(f"  {tier}: {count} wards ({count/len(merged)*100:.1f}%)")

# Top 10 most stressed wards
print(f"\nTop 10 most stressed wards:")
top10 = merged.nlargest(10, 'ASI')[['NAME_2','NAME_3','NAME_4','ASI','stress_tier']]
print(top10.to_string(index=False))

# ─────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────
# 4. MAP
# ─────────────────────────────────────────────────────────────
print("\nGenerating map...")
from matplotlib.patches import Patch

# Paths resolve from this file's own location, so the scripts run unchanged
# on any machine. _R is the project root; _R2 its parent.
_R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace('\\', '/') + '/'
_R2 = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))).replace('\\', '/') + '/'

fig, ax = plt.subplots(1, 1, figsize=(16, 16))
fig.patch.set_facecolor('white')

# Dhaka District only
dhaka_dist = merged[merged['NAME_2'] == 'Dhaka'].copy()

# Plot
dhaka_dist.plot(
    column='ASI',
    cmap='RdYlGn_r',
    vmin=0, vmax=1,
    linewidth=0.4,
    edgecolor='#ffffff',
    legend=False,
    ax=ax
)

# Upazila boundaries
dhaka_dist.dissolve(by='NAME_3').boundary.plot(
    ax=ax, color='#333333', linewidth=1.0, alpha=0.6
)

# Zoom to urban core — exclude Gazipur's extent
ax.set_xlim(90.30, 90.60)
ax.set_ylim(23.63, 23.92)

# Label only top 3 — manual offsets to avoid overlap
top3 = dhaka_dist.nlargest(3, 'ASI').copy()
top3['centroid'] = top3.geometry.centroid

# Manual label offsets [dx, dy] in degrees
offsets = {
    0: ( 0.04,  0.02),
    1: ( 0.05, -0.02),
    2: (-0.05,  0.03),
}

for i, (_, row) in enumerate(top3.iterrows()):
    cx, cy = row['centroid'].x, row['centroid'].y
    dx, dy = offsets.get(i, (0.03, 0.03))
    ax.annotate(
        f"{row['NAME_4']}  ASI: {row['ASI']:.2f}",
        xy=(cx, cy),
        xytext=(cx + dx, cy + dy),
        fontsize=9, fontweight='bold', color='#1a1a1a',
        arrowprops=dict(arrowstyle='->', color='#333333', lw=1),
        bbox=dict(boxstyle='round,pad=0.3', fc='white',
                  alpha=0.85, ec='#aaaaaa', lw=0.8)
    )

# ── Colorbar ──────────────────────────────────────────────────
sm = plt.cm.ScalarMappable(
    cmap='RdYlGn_r',
    norm=mcolors.Normalize(vmin=0, vmax=1)
)
sm.set_array([])
cbar = fig.colorbar(sm, ax=ax, fraction=0.025, pad=0.01, shrink=0.7)
cbar.set_label('Absorption Stress Index (ASI)', fontsize=11)
cbar.set_ticks([0, 0.33, 0.66, 1.0])
cbar.set_ticklabels(['0.0\n(No stress)', '0.33', '0.66', '1.0\n(Max stress)'])

# ── Stress tier legend ────────────────────────────────────────
legend_elements = [
    Patch(facecolor='#1a9850', edgecolor='white',
          label='Low stress  (ASI < 0.33)'),
    Patch(facecolor='#fee08b', edgecolor='white',
          label='Moderate    (0.33 – 0.66)'),
    Patch(facecolor='#d73027', edgecolor='white',
          label='High stress (ASI > 0.66)'),
]
ax.legend(handles=legend_elements, loc='lower left',
          fontsize=10, frameon=True, framealpha=0.9,
          title='Stress Tier', title_fontsize=10)

# ── North arrow ───────────────────────────────────────────────
ax.annotate('', xy=(0.97, 0.97), xytext=(0.97, 0.92),
            xycoords='axes fraction',
            arrowprops=dict(arrowstyle='->', color='black', lw=2.5))
ax.text(0.97, 0.98, 'N', transform=ax.transAxes,
        ha='center', fontsize=13, fontweight='bold')

# ── Title and source note ─────────────────────────────────────
ax.set_title(
    'PRAAN — Urban Absorption Stress Index\nDhaka District Ward-Level Analysis',
    fontsize=15, fontweight='bold', pad=15
)
ax.text(0.5, -0.03,
        'Indicators: WorldPop 2020 (population density) · '
        'GHSL 2020 (built-up fraction) · '
        'JRC Global Surface Water (flood risk)\n'
        'Weights: density 0.40 · built-up 0.35 · flood 0.25 · '
        'GADM 4.1 admin boundaries · Index normalized 0–1',
        transform=ax.transAxes, ha='center',
        fontsize=8, color='#666666', style='italic')

ax.set_axis_off()
plt.tight_layout()
plt.savefig(OUTPUT_DIR + 'phase3_asi_map.png',
            dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print("Map saved → outputs/phase3_asi_map.png")
with open(_R + "notebooks/07_phase3_part2.py") as f:
    for i, line in enumerate(f, 1):
        if i >= 100:
            print(f"{i:3}: {line}", end='')
  # ── Save CSV ──────────────────────────────────────────────────
out_cols = ['GID_4','NAME_2','NAME_3','NAME_4',
            'pop','builtup','flood',
            'pop_norm','builtup_norm','flood_norm',
            'ASI','stress_tier']
merged[out_cols].to_csv(OUTPUT_DIR + 'phase3_ward_scores.csv', index=False)
print("Scores saved → outputs/phase3_ward_scores.csv")          