"""
PRAAN — Phase 3: Urban Absorption Stress Index
Script: 06_phase3_absorption.py
FIXED: Upload local shapefile in batches to avoid payload limit
"""

import os
import ee
import json
import numpy as np
import pandas as pd
import geopandas as gpd
import warnings

# Paths resolve from this file's own location, so the scripts run unchanged
# on any machine. _R is the project root; _R2 its parent.
_R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace('\\', '/') + '/'
_R2 = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))).replace('\\', '/') + '/'
warnings.filterwarnings('ignore')

SHP_PATH   = _R + "data/raw/shapefiles/gadm41_BGD_4.shp"
OUTPUT_DIR = _R + "outputs/"
DATA_DIR   = _R + "data/processed/"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ─────────────────────────────────────────────────────────────
# 1. INITIALIZE GEE
# ─────────────────────────────────────────────────────────────
print("Initializing GEE...")
ee.Initialize(project='project-attempt-dhaka-heat')

# ─────────────────────────────────────────────────────────────
# 2. LOAD LOCAL SHAPEFILE — Dhaka Division only
# ─────────────────────────────────────────────────────────────
print("Loading shapefile...")
gdf = gpd.read_file(SHP_PATH)
dhaka = gdf[gdf['NAME_1'] == 'Dhaka'].copy().reset_index(drop=True)
dhaka = dhaka.to_crs(epsg=4326)
print(f"Dhaka Division wards: {len(dhaka)}")

# ─────────────────────────────────────────────────────────────
# 3. LOAD INDICATOR IMAGES
# ─────────────────────────────────────────────────────────────
print("Loading indicator images...")

worldpop = ee.ImageCollection("WorldPop/GP/100m/pop") \
    .filter(ee.Filter.eq('country', 'BGD')) \
    .filter(ee.Filter.eq('year', 2020)) \
    .first().rename('pop')

ghsl = ee.ImageCollection("JRC/GHSL/P2023A/GHS_BUILT_S") \
    .mosaic() \
    .select('built_surface') \
    .divide(10000).rename('builtup')

flood = ee.Image("JRC/GSW1_4/GlobalSurfaceWater") \
    .select('occurrence').gt(10).rename('flood')

# Verify all three images loaded correctly
print("  Verifying images...")
test_point = ee.Geometry.Point([90.4125, 23.8103])
indicators = worldpop.addBands(ghsl).addBands(flood)
val = indicators.reduceRegion(
    reducer=ee.Reducer.mean(),
    geometry=test_point.buffer(1000),
    scale=250
).getInfo()
print(f"  Test values: {val}")
print("  Images OK" if any(v is not None for v in val.values()) else "  WARNING: all null")

# ─────────────────────────────────────────────────────────────
# 4. PROCESS IN BATCHES OF 50 WARDS
# ─────────────────────────────────────────────────────────────
BATCH_SIZE = 50
all_results = []
n_batches = int(np.ceil(len(dhaka) / BATCH_SIZE))

print(f"Processing {len(dhaka)} wards in {n_batches} batches of {BATCH_SIZE}...")

for i in range(n_batches):
    batch = dhaka.iloc[i*BATCH_SIZE : (i+1)*BATCH_SIZE]

    # Convert batch to GEE FeatureCollection
    features = []
    for _, row in batch.iterrows():
        try:
            geom = row.geometry.__geo_interface__
            feat = ee.Feature(
                ee.Geometry(geom),
                {
                    'GID_4':  str(row['GID_4']),
                    'NAME_2': str(row['NAME_2']),
                    'NAME_3': str(row['NAME_3']),
                    'NAME_4': str(row['NAME_4']),
                }
            )
            features.append(feat)
        except Exception:
            continue

    fc = ee.FeatureCollection(features)

    # Reduce regions for this batch
    stats = indicators.reduceRegions(
        collection=fc,
        reducer=ee.Reducer.mean(),
        scale=250
    )

    # Pull results locally (getInfo — works for small batches)
    try:
        result = stats.getInfo()
        for feat in result['features']:
            props = feat['properties']
            all_results.append({
                'GID_4':  props.get('GID_4', ''),
                'NAME_2': props.get('NAME_2', ''),
                'NAME_3': props.get('NAME_3', ''),
                'NAME_4': props.get('NAME_4', ''),
                'pop':    props.get('pop', np.nan),
                'builtup':props.get('builtup', np.nan),
                'flood':  props.get('flood', np.nan),
            })
        print(f"  Batch {i+1}/{n_batches} done — {len(result['features'])} wards")
    except Exception as e:
        print(f"  Batch {i+1}/{n_batches} FAILED: {e}")
        continue

# ─────────────────────────────────────────────────────────────
# 5. SAVE CSV LOCALLY — no Drive export needed
# ─────────────────────────────────────────────────────────────
df = pd.DataFrame(all_results)
out_csv = DATA_DIR + 'praan_phase3_indicators.csv'
df.to_csv(out_csv, index=False)

print(f"\nSaved {len(df)} wards → {out_csv}")
print(f"Columns: {df.columns.tolist()}")
print(df[['NAME_2','NAME_4','pop','builtup','flood']].head(10).to_string())
print("\n✓ Phase 3 indicators complete. Ready for Part 2.")