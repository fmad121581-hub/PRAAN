import geopandas as gpd

shp = gpd.read_file(_R + 'data/raw/shapefiles/gadm41_BGD_4.shp')

# Filter to Dhaka district only
dhaka = shp[shp['NAME_2'] == 'Dhaka'].copy()
print(f"Dhaka wards: {len(dhaka)}")
print(dhaka[['GID_4','NAME_2','NAME_3','NAME_4']].head())

# Simplify geometry to reduce file size (0.001 degrees ~ 100m)
dhaka['geometry'] = dhaka['geometry'].simplify(0.001, preserve_topology=True)

# Keep only columns we need
dhaka = dhaka[['GID_4','NAME_2','NAME_3','NAME_4','geometry']]

# Save
out = _R + 'data/processed/dhaka_wards.geojson'
dhaka.to_file(out, driver='GeoJSON')
print(f"Saved → {out}")

import os

# Paths resolve from this file's own location, so the scripts run unchanged
# on any machine. _R is the project root; _R2 its parent.
_R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace('\\', '/') + '/'
_R2 = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))).replace('\\', '/') + '/'
size_mb = os.path.getsize(out) / 1e6
print(f"File size: {size_mb:.2f} MB")