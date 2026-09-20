"""
PRAAN — Phase 3 Update: Add BBS 2022 to ASI
Script: 09_phase3_update.py
"""

import pandas as pd
import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.patches import Patch
import warnings
warnings.filterwarnings('ignore')

SHP_PATH   = _R + "data/raw/shapefiles/gadm41_BGD_4.shp"
ASI_CSV    = _R + "outputs/phase3_ward_scores.csv"
BBS_CSV    = _R + "data/processed/bbs_2022_ward_final.csv"
OUTPUT_DIR = _R + "outputs/"

# ─────────────────────────────────────────────────────────────
# 1. LOAD DATA
# ─────────────────────────────────────────────────────────────
print("Loading data...")
gdf    = gpd.read_file(SHP_PATH)
dhaka  = gdf[gdf['NAME_1'] == 'Dhaka'].copy().reset_index(drop=True)
dhaka  = dhaka.to_crs(epsg=4326)
asi    = pd.read_csv(ASI_CSV)
bbs    = pd.read_csv(BBS_CSV)

print(f"Shapefile wards: {len(dhaka)}")
print(f"ASI wards: {len(asi)}")
print(f"BBS wards: {len(bbs)}")

# ─────────────────────────────────────────────────────────────
# 2. MERGE BBS INTO ASI
# BBS NAME_4 format: 'Ward No-01'
# GADM NAME_4 format: 'Ward No-01', 'Ward No-69' etc.
# Match on NAME_4 only within Dhaka District (NAME_2 == 'Dhaka')
# ─────────────────────────────────────────────────────────────
print("\nMerging BBS data...")

# BBS already has NAME_4 column
merged = asi.merge(
    bbs[['NAME_4', 'city_corp', 'hh_total',
         'pop_total', 'hh_size', 'elec_coverage']],
    on='NAME_4',
    how='left'
)

matched = merged['hh_total'].notna().sum()
print(f"BBS matched: {matched} / {len(merged)} wards")
print(f"Unmatched (will use ASI only): {len(merged) - matched}")

# ─────────────────────────────────────────────────────────────
# 3. COMPUTE OVERCROWDING PROXY
# High household size = more people per unit = less capacity
# ─────────────────────────────────────────────────────────────
def minmax(series):
    mn, mx = series.min(), series.max()
    return (series - mn) / (mx - mn)

# For matched wards: add hh_size as stress indicator
# Higher hh_size = more crowded = more stress
merged['hh_size_norm'] = np.nan
mask = merged['hh_size'].notna()
merged.loc[mask, 'hh_size_norm'] = minmax(merged.loc[mask, 'hh_size'])

# ─────────────────────────────────────────────────────────────
# 4. RECOMPUTE ASI WITH BBS INDICATOR WHERE AVAILABLE
# For wards with BBS data: 4 indicators
# For wards without: original 3-indicator ASI unchanged
# ─────────────────────────────────────────────────────────────
WEIGHTS_4 = {
    'pop_norm':     0.35,
    'builtup_norm': 0.25,
    'flood_norm':   0.20,
    'hh_size_norm': 0.20,
}

WEIGHTS_3 = {
    'pop_norm':     0.40,
    'builtup_norm': 0.35,
    'flood_norm':   0.25,
}

# Start with original ASI
merged['ASI_updated'] = merged['ASI']

# Update where BBS data available
bbs_mask = merged['hh_size_norm'].notna()
merged.loc[bbs_mask, 'ASI_updated'] = (
    merged.loc[bbs_mask, 'pop_norm']      * WEIGHTS_4['pop_norm']     +
    merged.loc[bbs_mask, 'builtup_norm']  * WEIGHTS_4['builtup_norm'] +
    merged.loc[bbs_mask, 'flood_norm']    * WEIGHTS_4['flood_norm']   +
    merged.loc[bbs_mask, 'hh_size_norm']  * WEIGHTS_4['hh_size_norm']
)

print(f"\nASI comparison (matched wards only):")
print(f"  Original ASI mean:  {merged.loc[bbs_mask,'ASI'].mean():.3f}")
print(f"  Updated ASI mean:   {merged.loc[bbs_mask,'ASI_updated'].mean():.3f}")

# Stress tiers
merged['stress_tier'] = pd.cut(
    merged['ASI_updated'],
    bins=[0, 0.33, 0.66, 1.01],
    labels=['Low stress', 'Moderate stress', 'High stress']
)

tier_counts = merged['stress_tier'].value_counts()
print(f"\nStress tiers (updated):")
for tier, count in tier_counts.items():
    print(f"  {tier}: {count} wards ({count/len(merged)*100:.1f}%)")

print(f"\nTop 10 most stressed wards:")
top10 = merged.nlargest(10, 'ASI_updated')[
    ['NAME_2','NAME_3','NAME_4','ASI_updated','stress_tier','city_corp']
]
print(top10.to_string(index=False))

# ─────────────────────────────────────────────────────────────
# 5. SAVE UPDATED SCORES
# ─────────────────────────────────────────────────────────────
merged.to_csv(OUTPUT_DIR + 'phase3_ward_scores_v2.csv', index=False)
print(f"\nSaved → phase3_ward_scores_v2.csv")

# ─────────────────────────────────────────────────────────────
# 6. UPDATE MAP
# ─────────────────────────────────────────────────────────────
print("\nGenerating updated map...")
from matplotlib.patches import Patch

# Merge back to shapefile
geo_merged = dhaka.merge(
    merged[['GID_4','ASI_updated','stress_tier','city_corp']],
    on='GID_4', how='left'
)
asi_lookup = merged.drop_duplicates('GID_4').set_index('GID_4')['ASI']
geo_merged['ASI_updated'] = geo_merged['ASI_updated'].fillna(
    geo_merged['GID_4'].map(asi_lookup)
)

fig, ax = plt.subplots(1, 1, figsize=(16, 16))
fig.patch.set_facecolor('white')

dhaka_dist = geo_merged[geo_merged['NAME_2'] == 'Dhaka'].copy()
dhaka_dist.plot(
    column='ASI_updated',
    cmap='RdYlGn_r',
    vmin=0, vmax=1,
    linewidth=0.4,
    edgecolor='#ffffff',
    legend=False,
    ax=ax
)

dhaka_dist.dissolve(by='NAME_3').boundary.plot(
    ax=ax, color='#333333', linewidth=1.0, alpha=0.6
)

ax.set_xlim(90.30, 90.60)
ax.set_ylim(23.63, 23.92)

# Label top 3
top3 = dhaka_dist.nlargest(3, 'ASI_updated').copy()
top3['centroid'] = top3.geometry.centroid
offsets = {0: (0.04, 0.02), 1: (0.05, -0.02), 2: (-0.05, 0.03)}
for i, (_, row) in enumerate(top3.iterrows()):
    cx, cy = row['centroid'].x, row['centroid'].y
    dx, dy = offsets.get(i, (0.03, 0.03))
    ax.annotate(
        f"{row['NAME_4']}  ASI: {row['ASI_updated']:.2f}",
        xy=(cx, cy), xytext=(cx + dx, cy + dy),
        fontsize=9, fontweight='bold', color='#1a1a1a',
        arrowprops=dict(arrowstyle='->', color='#333333', lw=1),
        bbox=dict(boxstyle='round,pad=0.3', fc='white',
                  alpha=0.85, ec='#aaaaaa', lw=0.8)
    )

sm = plt.cm.ScalarMappable(
    cmap='RdYlGn_r', norm=mcolors.Normalize(vmin=0, vmax=1)
)
sm.set_array([])
cbar = fig.colorbar(sm, ax=ax, fraction=0.025, pad=0.01, shrink=0.7)
cbar.set_label('Absorption Stress Index (ASI)', fontsize=11)
cbar.set_ticks([0, 0.33, 0.66, 1.0])
cbar.set_ticklabels(['0.0\n(No stress)', '0.33', '0.66', '1.0\n(Max stress)'])

legend_elements = [
    Patch(facecolor='#1a9850', edgecolor='white', label='Low stress  (ASI < 0.33)'),
    Patch(facecolor='#fee08b', edgecolor='white', label='Moderate    (0.33 – 0.66)'),
    Patch(facecolor='#d73027', edgecolor='white', label='High stress (ASI > 0.66)'),
]
ax.legend(handles=legend_elements, loc='lower left',
          fontsize=10, frameon=True, framealpha=0.9,
          title='Stress Tier', title_fontsize=10)

ax.annotate('', xy=(0.97, 0.97), xytext=(0.97, 0.92),
            xycoords='axes fraction',
            arrowprops=dict(arrowstyle='->', color='black', lw=2.5))
ax.text(0.97, 0.98, 'N', transform=ax.transAxes,
        ha='center', fontsize=13, fontweight='bold')

ax.set_title(
    'PRAAN — Urban Absorption Stress Index (Updated)\n'
    'Dhaka District Ward-Level Analysis\n'
    'Indicators: WorldPop · GHSL · JRC Flood Risk · BBS 2022 Household Size',
    fontsize=13, fontweight='bold', pad=15
)
ax.text(0.5, -0.03,
        'Sources: WorldPop 2020 · GHSL 2020 · JRC GSW · '
        'BBS Population & Housing Census 2022 (Urban Area Report)\n'
        'GADM 4.1 admin boundaries · Index normalized 0–1 within Dhaka Division',
        transform=ax.transAxes, ha='center',
        fontsize=8, color='#666666', style='italic')

ax.set_axis_off()
plt.tight_layout()
plt.savefig(OUTPUT_DIR + 'phase3_asi_map_v2.png',
            dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print("Map saved → phase3_asi_map_v2.png")
print("\n✓ Phase 3 update complete.")
import os

# Paths resolve from this file's own location, so the scripts run unchanged
# on any machine. _R is the project root; _R2 its parent.
_R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace('\\', '/') + '/'
_R2 = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))).replace('\\', '/') + '/'
OUTPUT_DIR = _R + "outputs/"
for f in os.listdir(OUTPUT_DIR):
    print(f)