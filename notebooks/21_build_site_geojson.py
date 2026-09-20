"""
PRAAN — rebuild the map data embedded in the site
Script: 21_build_site_geojson.py

WHY
    outputs/PRAAN.html carries its ward polygons inline as `const WARD_GEO`,
    so the page is one self-contained file with no fetch and no CORS. That
    block has to be regenerated every time the ranking changes, and doing it
    by hand is how a site ends up showing numbers its own CSVs disagree with.
    This script rebuilds it from the committed outputs, so the page can never
    drift from the pipeline.

WHAT IT DOES
    - reads the dissolved ward geometry and the current ranking
    - simplifies to 0.001 degrees (~100 m) and rounds to 5 decimals, which
      keeps the page around 180 KB instead of several megabytes while the
      vertex count stays within a few percent of the original
    - writes the block back into outputs/PRAAN.html and mirrors the file to
      deploy/index.html, which is what Netlify publishes

NO EARTH ENGINE NEEDED.

OUTPUT
    outputs/PRAAN.html   (WARD_GEO block replaced)
    deploy/index.html    (copy)
"""
import geopandas as gpd, pandas as pd, json, shutil, os, re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + os.sep
DATA, OUT = BASE + 'data/processed/', BASE + 'outputs/'
DEPLOY = BASE + 'deploy/'
SIMPLIFY_DEG = 0.001
DECIMALS = 5

g = gpd.read_file(DATA + 'dhaka_wards_dissolved.geojson').to_crs(epsg=4326)
prim = pd.read_csv(OUT + 'crisis_index_primary.csv')
ext = pd.read_csv(OUT + 'crisis_index_extended.csv')
scores = pd.read_csv(OUT + 'phase3_ward_scores_v4_dissolved.csv')

rank = prim.set_index('GID_4')
extra = ext.set_index('GID_4')
sc = scores.set_index('GID_4')

g['geometry'] = g.geometry.simplify(SIMPLIFY_DEG, preserve_topology=True)

feats = []
for _, row in g.iterrows():
    gid = row.GID_4
    s = sc.loc[gid] if gid in sc.index else None
    r = rank.loc[gid] if gid in rank.index else None
    e = extra.loc[gid] if gid in extra.index else None
    src = r if r is not None else e
    props = {
        'GID_4': gid,
        'NAME_2': 'Dhaka',
        'NAME_3': (s.NAME_3 if s is not None else None),
        'NAME_4': (s.NAME_4 if s is not None else None),
        # ASI comes from the ranking when the ward is ranked, and otherwise
        # from the ward-score table, so the 65 unranked polygons still carry
        # a stress value and still colour on the stress layer.
        'asi': (round(float(src.ASI), 4) if src is not None and pd.notna(src.ASI)
                else round(float(s.ASI), 4) if s is not None and pd.notna(s.ASI) else None),
        'stress_tier': (s.stress_tier if s is not None and pd.notna(s.stress_tier) else None),
        # city_corp is only filled where a BBS record matched; corp_spatial is
        # the spatial assignment and covers every city polygon.
        'city_corp': (s.city_corp if s is not None and pd.notna(s.city_corp)
                      else s.corp_spatial if s is not None and pd.notna(s.corp_spatial)
                      else None),
        'in_city': bool(s is not None and pd.notna(s.corp_spatial)),
    }
    if s is not None and pd.notna(s.pop_total):
        props['population'] = int(s.pop_total)
    if r is not None:
        props.update({
            'crisis_index': round(float(r.crisis_index), 4),
            'crisis_tier': r.crisis_tier,
            'arrivals_central': int(r.arrivals_central),
        })
        for k in ('low', 'high'):
            col = f'arrivals_{k}'
            if col in prim.columns and pd.notna(r.get(col)):
                props[col] = int(r[col])
    geom = json.loads(gpd.GeoSeries([row.geometry]).to_json())['features'][0]['geometry']

    def rnd(o):
        if isinstance(o, list):
            return [rnd(x) for x in o]
        return round(o, DECIMALS) if isinstance(o, float) else o
    geom['coordinates'] = rnd(geom['coordinates'])
    feats.append({'type': 'Feature', 'properties': props, 'geometry': geom})

fc = {'type': 'FeatureCollection', 'name': 'dhaka_wards', 'features': feats}
blob = 'const WARD_GEO = ' + json.dumps(fc, separators=(',', ':')) + ';'

html_path = OUT + 'PRAAN.html'
s = open(html_path, encoding='utf-8').read()
start = s.find('const WARD_GEO')
if start < 0:
    raise SystemExit('WARD_GEO block not found in ' + html_path)
end = s.find('};', start) + 2
s = s[:start] + blob + s[end:]
open(html_path, 'w', encoding='utf-8').write(s)

os.makedirs(DEPLOY, exist_ok=True)
shutil.copyfile(html_path, DEPLOY + 'index.html')

ranked = sum(1 for f in feats if f['properties'].get('crisis_index') is not None)
high = sum(1 for f in feats if f['properties'].get('crisis_tier') == 'High concern')
verts = sum(len(json.dumps(f['geometry'])) for f in feats)
print(f'polygons {len(feats)} | ranked {ranked} | high concern {high}')
print(f'page size {os.path.getsize(html_path)/1024:.0f} KB  '
      f'(geometry {verts/1024:.0f} KB)')
print(f'wrote {html_path} and {DEPLOY}index.html')
