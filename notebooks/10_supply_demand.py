"""
PRAAN — Supply vs Demand Gap Analysis (Fixed)
Script: 10_supply_demand.py
"""

import pandas as pd
import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.patches import Patch
import warnings
warnings.filterwarnings('ignore')

OCHA_SHP   = r"C:/Users/user/OneDrive/Nasa_2026/PRAAN/data/raw/ocha/bgd_admin3.shp"
GADM_SHP   = r"C:/Users/user/OneDrive/Nasa_2026/PRAAN/data/raw/shapefiles/gadm41_BGD_4.shp"
ASI_CSV    = r"C:/Users/user/OneDrive/Nasa_2026/PRAAN/outputs/phase3_ward_scores_v2.csv"
BBS_CSV    = r"C:/Users/user/OneDrive/Nasa_2026/PRAAN/data/processed/bbs_2022_ward_final.csv"
OUTPUT_DIR = r"C:/Users/user/OneDrive/Nasa_2026/PRAAN/outputs/"

# ─────────────────────────────────────────────────────────────
# 1. MOBILITY PRESSURE PARAMETERS
# ─────────────────────────────────────────────────────────────
MOBILITY_LOW     = 1_433_763
MOBILITY_CENTRAL = 2_580_774
MOBILITY_HIGH    = 3_584_408

DHAKA_DIV_SHARE  = 0.660
DHAKA_CITY_SHARE = 0.450

arrivals_low     = int(MOBILITY_LOW     * DHAKA_DIV_SHARE * DHAKA_CITY_SHARE)
arrivals_central = int(MOBILITY_CENTRAL * DHAKA_DIV_SHARE * DHAKA_CITY_SHARE)
arrivals_high    = int(MOBILITY_HIGH    * DHAKA_DIV_SHARE * DHAKA_CITY_SHARE)

print("Arrivals to Dhaka City:")
print(f"  Low:     {arrivals_low:>10,}")
print(f"  Central: {arrivals_central:>10,}")
print(f"  High:    {arrivals_high:>10,}")

# ─────────────────────────────────────────────────────────────
# 2. LOAD OCHA CITY CORPORATION BOUNDARIES
# ─────────────────────────────────────────────────────────────
print("\nLoading OCHA boundaries...")
ocha = gpd.read_file(OCHA_SHP).to_crs(epsg=4326)
dncc = ocha[ocha['adm3_name'] == 'Dhaka North City Corporation']
dscc = ocha[ocha['adm3_name'] == 'Dhaka South City Corporation']
print(f"DNCC polygon: {len(dncc)} feature")
print(f"DSCC polygon: {len(dscc)} feature")

# ─────────────────────────────────────────────────────────────
# 3. SPATIAL JOIN — assign each GADM ward to DNCC or DSCC
# ─────────────────────────────────────────────────────────────
print("\nSpatially assigning GADM wards to city corporations...")
gadm = gpd.read_file(GADM_SHP).to_crs(epsg=4326)
dhaka_wards = gadm[gadm['NAME_2'] == 'Dhaka'].copy()
dhaka_wards['centroid'] = dhaka_wards.geometry.centroid

# Create point GDF from centroids
centroids = gpd.GeoDataFrame(
    dhaka_wards[['GID_4','NAME_3','NAME_4']],
    geometry=dhaka_wards['centroid'],
    crs='EPSG:4326'
)

# City corp polygons combined
corp_polys = ocha[ocha['adm3_name'].isin([
    'Dhaka North City Corporation',
    'Dhaka South City Corporation'
])][['adm3_name','geometry']].copy()
corp_polys['city_corp'] = corp_polys['adm3_name'].map({
    'Dhaka North City Corporation': 'DNCC',
    'Dhaka South City Corporation': 'DSCC'
})

# Spatial join
joined = gpd.sjoin(centroids, corp_polys[['city_corp','geometry']],
                   how='left', predicate='within')
joined = joined[['GID_4','NAME_3','NAME_4','city_corp']].copy()

print(f"Wards assigned to DNCC: {(joined['city_corp']=='DNCC').sum()}")
print(f"Wards assigned to DSCC: {(joined['city_corp']=='DSCC').sum()}")
print(f"Unassigned (outside corp): {joined['city_corp'].isna().sum()}")

# ─────────────────────────────────────────────────────────────
# 4. MERGE ASI + BBS + CORP ASSIGNMENT
# ─────────────────────────────────────────────────────────────
print("\nMerging datasets...")
print(f"Joined columns: {joined.columns.tolist()}")
print(joined.head(3).to_string())
asi = pd.read_csv(ASI_CSV)
bbs = pd.read_csv(BBS_CSV)

# Merge corp assignment into ASI
# Drop existing city_corp from ASI if present — use spatial join result instead
if 'city_corp' in asi.columns:
    asi = asi.drop(columns=['city_corp'])

asi_corp = asi.merge(
    joined[['GID_4','city_corp']].drop_duplicates('GID_4'),
    on='GID_4', how='left'
)

print(f"city_corp assigned in ASI: {asi_corp['city_corp'].notna().sum()}")

# Merge BBS — use NAME_4 + city_corp but only where city_corp is known
bbs_merged = asi_corp.merge(
    bbs[['NAME_4','city_corp','pop_total','hh_total','hh_size','elec_coverage']],
    on=['NAME_4','city_corp'],
    how='left'
)

city_wards = bbs_merged[bbs_merged['city_corp'].isin(['DNCC','DSCC'])].copy()

# Rename suffixed columns from double merge
for col in ['pop_total','hh_total','hh_size','elec_coverage']:
    if f'{col}_y' in city_wards.columns:
        city_wards[col] = city_wards[f'{col}_y']
    elif f'{col}_x' in city_wards.columns:
        city_wards[col] = city_wards[f'{col}_x']

print(f"City corporation wards: {len(city_wards)}")
print(f"BBS population matched: {city_wards['pop_total'].notna().sum()}")

# ─────────────────────────────────────────────────────────────
# 5. DISTRIBUTE ARRIVALS BY INVERSE ASI WEIGHT
# ─────────────────────────────────────────────────────────────
city_wards['ASI_updated'] = city_wards['ASI_updated'].fillna(
    city_wards['ASI_updated'].mean()
)
city_wards['pop_total'] = city_wards['pop_total'].fillna(
    city_wards['pop_total'].median()
)

# Less stressed = more absorption capacity = more arrivals routed there
city_wards['absorb_weight'] = (
    city_wards['pop_total'] * (1 - city_wards['ASI_updated'])
)
total_weight = city_wards['absorb_weight'].sum()
city_wards['pop_share'] = city_wards['absorb_weight'] / total_weight

city_wards['arrivals_low']     = (city_wards['pop_share'] * arrivals_low).astype(int)
city_wards['arrivals_central'] = (city_wards['pop_share'] * arrivals_central).astype(int)
city_wards['arrivals_high']    = (city_wards['pop_share'] * arrivals_high).astype(int)

city_wards['load_ratio_central'] = (
    city_wards['arrivals_central'] / city_wards['pop_total']
)

# ─────────────────────────────────────────────────────────────
# 6. GAP SCORE
# ─────────────────────────────────────────────────────────────
city_wards['gap_score'] = (
    city_wards['ASI_updated'] * city_wards['load_ratio_central']
)
city_wards['gap_score'] = (
    city_wards['gap_score'] / city_wards['gap_score'].max()
)

city_wards['gap_tier'] = pd.cut(
    city_wards['gap_score'],
    bins=[0, 0.33, 0.66, 1.01],
    labels=['Manageable', 'At risk', 'Critical']
)

print(f"\nGap tier summary:")
print(city_wards['gap_tier'].value_counts())

print(f"\nTop 10 critical wards:")
top10 = city_wards.nlargest(10, 'gap_score')[[
    'city_corp','NAME_3','NAME_4','pop_total',
    'arrivals_central','load_ratio_central',
    'ASI_updated','gap_score','gap_tier'
]].copy()
top10['load_pct'] = (top10['load_ratio_central'] * 100).round(1)
print(top10[['city_corp','NAME_3','NAME_4','pop_total',
             'arrivals_central','load_pct',
             'ASI_updated','gap_tier']].to_string(index=False))

# ─────────────────────────────────────────────────────────────
# 7. SAVE
# ─────────────────────────────────────────────────────────────
city_wards.to_csv(OUTPUT_DIR + 'phase3_supply_demand_gap.csv', index=False)
print(f"\nSaved → phase3_supply_demand_gap.csv")

# ─────────────────────────────────────────────────────────────
# 8. MAP
# ─────────────────────────────────────────────────────────────
print("\nGenerating gap map...")

gadm_dhaka = gadm[gadm['NAME_2'] == 'Dhaka'].copy()
gadm_dhaka = gadm_dhaka.merge(
    city_wards[['GID_4','gap_score','gap_tier',
                'arrivals_central','load_ratio_central','ASI_updated']],
    on='GID_4', how='left'
)

fig, ax = plt.subplots(1, 1, figsize=(16, 16))
fig.patch.set_facecolor('white')

gadm_dhaka.plot(
    column='gap_score',
    cmap='OrRd',
    vmin=0, vmax=1,
    linewidth=0.4,
    edgecolor='#ffffff',
    legend=False,
    ax=ax,
    missing_kwds={'color': 'lightgrey', 'label': 'Outside city corp'}
)

gadm_dhaka.dissolve(by='NAME_3').boundary.plot(
    ax=ax, color='#333333', linewidth=1.0, alpha=0.6
)

# DNCC/DSCC boundary overlay
corp_polys.boundary.plot(ax=ax, color='navy', linewidth=2, alpha=0.7)

ax.set_xlim(90.30, 90.60)
ax.set_ylim(23.63, 23.92)

# Label top 3
top3 = gadm_dhaka.nlargest(3, 'gap_score').copy()
top3['centroid'] = top3.geometry.centroid
offsets = {0: (0.04, 0.02), 1: (0.05, -0.02), 2: (-0.05, 0.03)}
for i, (_, row) in enumerate(top3.iterrows()):
    if pd.isna(row['gap_score']):
        continue
    cx, cy = row['centroid'].x, row['centroid'].y
    dx, dy = offsets.get(i, (0.03, 0.03))
    ax.annotate(
        f"{row['NAME_4']}\n+{int(row['arrivals_central']):,} arrivals\n"
        f"Load: +{row['load_ratio_central']*100:.1f}%",
        xy=(cx, cy), xytext=(cx+dx, cy+dy),
        fontsize=8, fontweight='bold', color='#1a1a1a',
        arrowprops=dict(arrowstyle='->', color='#333333', lw=1),
        bbox=dict(boxstyle='round,pad=0.3', fc='white',
                  alpha=0.85, ec='#aaaaaa', lw=0.8)
    )

sm = plt.cm.ScalarMappable(
    cmap='OrRd', norm=mcolors.Normalize(vmin=0, vmax=1)
)
sm.set_array([])
cbar = fig.colorbar(sm, ax=ax, fraction=0.025, pad=0.01, shrink=0.7)
cbar.set_label('Supply-Demand Gap Score (0–1)', fontsize=11)
cbar.set_ticks([0, 0.33, 0.66, 1.0])
cbar.set_ticklabels(['0.0\n(Manageable)', '0.33', '0.66', '1.0\n(Critical)'])

legend_elements = [
    Patch(facecolor='#fdcc8a', edgecolor='white', label='Manageable (< 0.33)'),
    Patch(facecolor='#fc8d59', edgecolor='white', label='At risk    (0.33–0.66)'),
    Patch(facecolor='#d7301f', edgecolor='white', label='Critical   (> 0.66)'),
    Patch(facecolor='lightgrey', edgecolor='white', label='Outside city corporation'),
]
ax.legend(handles=legend_elements, loc='lower left',
          fontsize=10, frameon=True, framealpha=0.9,
          title='Gap Tier', title_fontsize=10)

ax.annotate('', xy=(0.97, 0.97), xytext=(0.97, 0.92),
            xycoords='axes fraction',
            arrowprops=dict(arrowstyle='->', color='black', lw=2.5))
ax.text(0.97, 0.98, 'N', transform=ax.transAxes,
        ha='center', fontsize=13, fontweight='bold')

ax.set_title(
    'PRAAN — Supply vs Demand Gap\n'
    'Incoming Mobility Pressure × Existing Absorption Stress\n'
    'Dhaka City Corporation Wards — Central Scenario (2026)',
    fontsize=13, fontweight='bold', pad=15
)
ax.text(0.5, -0.03,
        'Gap Score = ASI × Incoming Load Ratio · Central estimate: 766,489 arrivals\n'
        'Distribution weighted by absorption capacity (inverse ASI) · '
        'BBS 2022 · Khalily et al. 2006/07 · BBS Census 2011\n'
        'City corporation boundaries: OCHA COD-AB Bangladesh 2025',
        transform=ax.transAxes, ha='center',
        fontsize=8, color='#666666', style='italic')

ax.set_axis_off()
plt.tight_layout()
plt.savefig(OUTPUT_DIR + 'phase3_gap_map.png',
            dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print("Gap map saved → phase3_gap_map.png")
print("\n✓ Supply-demand analysis complete.")




