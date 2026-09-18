"""
PRAAN — Phase 1: Satellite Signal Extraction
Script: 01_gee_chirps_extraction.py

PURPOSE:
    Extract Aman-season (June–November) rainfall anomalies
    from CHIRPS for Rajshahi Division districts, 1984–2022.
    Also extracts MODIS NDVI anomaly for the same period.

OUTPUT:
    data/processed/chirps_aman_season.csv
    data/processed/modis_ndvi_aman.csv

AUTHOR: PRAAN Team
"""

import ee
import pandas as pd
import numpy as np
import json
import os
import time

# ─────────────────────────────────────────────
# 0. INITIALISE EARTH ENGINE
# ─────────────────────────────────────────────
# First time: run `earthengine authenticate` in terminal
# Then initialise with your project ID

ee.Initialize(project='project-attempt-dhaka-heat')   # ← replace with yours

# ─────────────────────────────────────────────
# 1. DEFINE STUDY AREA
# ─────────────────────────────────────────────
# Rajshahi Division districts relevant to Barind Tract
# Using FAO GAUL Level 2 (district boundaries)
# Alternative: upload your own shapefile as GEE asset

BARIND_DISTRICTS = [
    'Rajshahi',
    'Naogaon',
    'Chapai Nawabganj',   # Also written as Chapainawabganj
    'Natore',
    'Nawabganj'           # Check exact name in GAUL
]

# Load Bangladesh district boundaries from FAO GAUL
# GEE dataset: FAO/GAUL/2015/level2
bangladesh_districts = (
    ee.FeatureCollection('FAO/GAUL/2015/level2')
    .filter(ee.Filter.eq('ADM0_NAME', 'Bangladesh'))
)

# Filter to Rajshahi Division districts
# NOTE: Check exact district names printed below before proceeding
rajshahi_div = bangladesh_districts.filter(
    ee.Filter.inList('ADM2_NAME', BARIND_DISTRICTS)
)

print("Districts loaded. Verifying names...")
# Run this to check exact names in GAUL dataset:
# district_names = bangladesh_districts.aggregate_array('ADM2_NAME').getInfo()
# print(sorted(district_names))
# Adjust BARIND_DISTRICTS list to match exactly.

# ─────────────────────────────────────────────
# 2. CHIRPS RAINFALL — AMAN SEASON EXTRACTION
# ─────────────────────────────────────────────
# CHIRPS: Climate Hazards Group InfraRed Precipitation with Station data
# Resolution: 0.05° (~5.5 km)
# Coverage: 1981–present
# Aman season: June (6) – November (11)
# This is the primary rainfed rice season in NW Bangladesh

AMAN_START_MONTH = 6   # June
AMAN_END_MONTH   = 11  # November
START_YEAR       = 1984
END_YEAR         = 2022

chirps = ee.ImageCollection('UCSB-CHG/CHIRPS/PENTAD')


def get_aman_rainfall(year):
    """
    Sum CHIRPS pentad precipitation over Aman season
    for a given year. Returns district-level mean (mm).
    """
    start = ee.Date.fromYMD(year, AMAN_START_MONTH, 1)
    end   = ee.Date.fromYMD(year, AMAN_END_MONTH, 30)

    seasonal_total = (
        chirps
        .filterDate(start, end)
        .select('precipitation')
        .sum()
    )

    def extract_district(feature):
        stats = seasonal_total.reduceRegion(
            reducer    = ee.Reducer.mean(),
            geometry   = feature.geometry(),
            scale      = 5500,     # ~CHIRPS native resolution
            maxPixels  = 1e9,
            bestEffort = True
        )
        return feature.set({
            'year'         : year,
            'rainfall_mm'  : stats.get('precipitation'),
            'district'     : feature.get('ADM2_NAME')
        })

    return rajshahi_div.map(extract_district)


# Run extraction for all years
print(f"Extracting CHIRPS rainfall {START_YEAR}–{END_YEAR}...")
print("This may take 5–15 minutes depending on GEE load.\n")

all_chirps_records = []

for year in range(START_YEAR, END_YEAR + 1):
    try:
        fc = get_aman_rainfall(year)
        records = fc.select(
            ['year', 'district', 'rainfall_mm']
        ).getInfo()

        for feat in records['features']:
            props = feat['properties']
            all_chirps_records.append({
                'year'        : int(props['year']),
                'district'    : props['district'],
                'rainfall_mm' : props.get('rainfall_mm', np.nan)
            })

        if year % 5 == 0:
            print(f"  ✓ {year} done")

        time.sleep(0.5)   # polite rate limiting

    except Exception as e:
        print(f"  ✗ {year} failed: {e}")
        all_chirps_records.append({
            'year'        : year,
            'district'    : 'ERROR',
            'rainfall_mm' : np.nan
        })

# Save raw output
chirps_df = pd.DataFrame(all_chirps_records)
chirps_df = chirps_df.sort_values(
    ['district', 'year']
).reset_index(drop=True)

os.makedirs('../data/processed', exist_ok=True)
chirps_df.to_csv(
    '../data/processed/chirps_aman_season_raw.csv',
    index=False
)
print(f"\nCHIRPS extraction complete. "
      f"{len(chirps_df)} records saved.")
print(chirps_df.head(10))


# ─────────────────────────────────────────────
# 3. MODIS NDVI — AMAN SEASON EXTRACTION
# ─────────────────────────────────────────────
# MODIS MOD13A3: Monthly NDVI at 1km resolution
# Available from 2000 — so NDVI series is 2000–2022 only
# CHIRPS covers full 1984–2022 period
# Use NDVI as a secondary/confirmatory signal

modis_ndvi = ee.ImageCollection('MODIS/061/MOD13A3').select('NDVI')

# MODIS NDVI scale factor: multiply by 0.0001
NDVI_SCALE = 0.0001


def get_aman_ndvi(year):
    """
    Mean NDVI over Aman season for a given year.
    NDVI peaks with healthy vegetation — drops signal drought stress.
    Compare against historical baseline (2000–2020 mean) to get anomaly.
    """
    start = ee.Date.fromYMD(year, AMAN_START_MONTH, 1)
    end   = ee.Date.fromYMD(year, AMAN_END_MONTH, 30)

    seasonal_mean = (
        modis_ndvi
        .filterDate(start, end)
        .mean()
        .multiply(NDVI_SCALE)
    )

    def extract_district(feature):
        stats = seasonal_mean.reduceRegion(
            reducer    = ee.Reducer.mean(),
            geometry   = feature.geometry(),
            scale      = 1000,
            maxPixels  = 1e9,
            bestEffort = True
        )
        return feature.set({
            'year'        : year,
            'ndvi_mean'   : stats.get('NDVI'),
            'district'    : feature.get('ADM2_NAME')
        })

    return rajshahi_div.map(extract_district)


NDVI_START_YEAR = 2000   # MODIS starts 2000

print(f"\nExtracting MODIS NDVI {NDVI_START_YEAR}–{END_YEAR}...")

all_ndvi_records = []

for year in range(NDVI_START_YEAR, END_YEAR + 1):
    try:
        fc = get_aman_ndvi(year)
        records = fc.select(
            ['year', 'district', 'ndvi_mean']
        ).getInfo()

        for feat in records['features']:
            props = feat['properties']
            all_ndvi_records.append({
                'year'      : int(props['year']),
                'district'  : props['district'],
                'ndvi_mean' : props.get('ndvi_mean', np.nan)
            })

        if year % 5 == 0:
            print(f"  ✓ {year} done")

        time.sleep(0.5)

    except Exception as e:
        print(f"  ✗ {year} failed: {e}")

ndvi_df = pd.DataFrame(all_ndvi_records)
ndvi_df = ndvi_df.sort_values(
    ['district', 'year']
) if 'district' in ndvi_df.columns else ndvi_df.sort_values(['year'])
ndvi_df = ndvi_df.reset_index(drop=True)

ndvi_df.to_csv(
    '../data/processed/modis_ndvi_aman_raw.csv',
    index=False
)
print(f"NDVI extraction complete. "
      f"{len(ndvi_df)} records saved.")


# ─────────────────────────────────────────────
# 4. SMAP SOIL MOISTURE — OPTIONAL THIRD SIGNAL
# ─────────────────────────────────────────────
# SMAP L3: 36km resolution, available from April 2015 only
# Short record — use as supplementary, not primary
# Uncomment if you want it

"""
smap = ee.ImageCollection('NASA/SMAP/SPL3SMP_E/005')\
         .select('soil_moisture_am')

def get_smap_moisture(year):
    start = ee.Date.fromYMD(year, AMAN_START_MONTH, 1)
    end   = ee.Date.fromYMD(year, AMAN_END_MONTH, 30)
    
    seasonal_mean = (
        smap
        .filterDate(start, end)
        .mean()
    )
    
    def extract_district(feature):
        stats = seasonal_mean.reduceRegion(
            reducer    = ee.Reducer.mean(),
            geometry   = feature.geometry(),
            scale      = 36000,
            maxPixels  = 1e9,
            bestEffort = True
        )
        return feature.set({
            'year'           : year,
            'soil_moisture'  : stats.get('soil_moisture_am'),
            'district'       : feature.get('ADM2_NAME')
        })
    
    return rajshahi_div.map(extract_district)
"""
# ── GRACE Terrestrial Water Storage ───────────────────────
grace = ee.ImageCollection("NASA/GRACE/MASS_GRIDS_V04/LAND")\
          .select('lwe_thickness_csr')

GRACE_START = 2002   # GRACE available from 2002

print(f"\nExtracting GRACE TWS {GRACE_START}–2022...")

all_grace_records = []

for year in range(GRACE_START, END_YEAR + 1):
    try:
        # Use pre-Aman season: Jan-May (groundwater drawn down by Boro irrigation)
        start = ee.Date.fromYMD(year, 1, 1)
        end   = ee.Date.fromYMD(year, 5, 31)

        tws_mean = grace.filterDate(start, end).mean()

        def extract_grace(feature):
            stats = tws_mean.reduceRegion(
                reducer    = ee.Reducer.mean(),
                geometry   = feature.geometry(),
                scale      = 50000,    # GRACE is coarse ~300km
                maxPixels  = 1e9,
                bestEffort = True
            )
            return feature.set({
                'year'         : year,
                'tws_anomaly'  : stats.get('lwe_thickness_csr'),
                'district'     : feature.get('ADM2_NAME')
            })

        fc      = rajshahi_div.map(extract_grace)
        records = fc.select(
            ['year', 'district', 'tws_anomaly']
        ).getInfo()

        for feat in records['features']:
            props = feat['properties']
            all_grace_records.append({
                'year'        : int(props['year']),
                'district'    : props['district'],
                'tws_anomaly' : props.get('tws_anomaly', np.nan)
            })

        print(f"  ✓ {year} done")
        time.sleep(0.5)

    except Exception as e:
        print(f"  ✗ {year} failed: {e}")

grace_df = pd.DataFrame(all_grace_records)
grace_df.to_csv(
    'C:/Users/user/OneDrive/Nasa_2026/PRAAN/data/processed/grace_tws_raw.csv',
    index=False
)
print(f"GRACE extraction complete. {len(grace_df)} records saved.")
print("\n✓ Script 01 complete.")
print("Next: run 02_bbs_yield_processing.py")
