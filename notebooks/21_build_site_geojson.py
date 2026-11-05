"""
PRAAN — rebuild the data embedded in the site
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
    - inlines notebooks/site/trend_stats.js (the Trend Detective's
      statistics, checked by script 24) between the TREND_STATS markers
    - rebuilds `const DETECTIVE` from data/processed/detective_monthly.csv
      (script 23), if that file exists

NO EARTH ENGINE NEEDED.

OUTPUT
    outputs/PRAAN.html   (WARD_GEO, TREND_STATS and DETECTIVE replaced)
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
        'asi': (round(float(src.ASI), 6) if src is not None and pd.notna(src.ASI)
                else round(float(s.ASI), 6) if s is not None and pd.notna(s.ASI) else None),
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
            'crisis_index': round(float(r.crisis_index), 6),
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

# ── hero chart: Barind dry-season GRACE series (script 16) ────────────────
reg = pd.read_csv(DATA + 'grace_regional_tws.csv')
b = reg[reg.region == 'Barind Tract (NW)'].set_index('year').sort_index()
years = list(range(int(b.index.min()), int(b.index.max()) + 1))
trend = {'years': years,
         'series': {'barind': {'tws': [None if pd.isna(b.tws.get(y)) else round(float(b.tws[y]), 2) for y in years],
                               'n': [int(b.n_images.get(y, 0)) for y in years]}},
         'barind_baseline': round(float(b.loc[2002:2004, 'tws'].mean()), 2),
         'barind_plateau': round(float(b.loc[2011:2017, 'tws'].mean()), 2)}
start = s.find('const TREND = ')
if start < 0:
    raise SystemExit('TREND block not found in ' + html_path)
end = s.find(';\n', start) + 1
s = s[:start] + 'const TREND = ' + json.dumps(trend, separators=(',', ':')) + ';' + s[end:]
print(f"hero: Barind 2002-04 {trend['barind_baseline']} cm, 2011-17 {trend['barind_plateau']} cm, "
      f"drop {trend['barind_baseline'] - trend['barind_plateau']:.2f} cm")

# ── Trend Detective: statistics code and monthly data ─────────────────────
a, b = '/* TREND_STATS:BEGIN */\n', '/* TREND_STATS:END */'
i, j = s.find(a), s.find(b)
if i < 0 or j < 0:
    raise SystemExit('TREND_STATS markers not found in ' + html_path)
js = open(BASE + 'notebooks/site/trend_stats.js', encoding='utf-8').read()
s = s[:i + len(a)] + js + s[j:]

DET_DP = {'tws': 4, 'gpm': 1, 'chirps': 1, 'ndvi': 4, 'lst': 2, 'soil': 2}
det_path = DATA + 'detective_monthly.csv'
if os.path.exists(det_path):
    m = pd.read_csv(det_path)
    det = {}
    for (var, reg), d in m.groupby(['variable', 'region']):
        y0, y1 = int(d.year.min()), int(d.year.max())
        idx = (d.year - y0) * 12 + d.month - 1
        v = [None] * ((y1 - y0 + 1) * 12)
        n = [0] * len(v)
        for k, val, cnt in zip(idx, d.value, d.n):
            v[k] = round(float(val), DET_DP[var])
            n[k] = int(cnt)
        entry = {'y0': y0, 'v': v}
        if var == 'tws':      # GRACE seasons are image-weighted means, as script 16
            entry['n'] = n
        det.setdefault(var, {})[reg] = entry
    det_blob = 'const DETECTIVE = ' + json.dumps({'data': det}, separators=(',', ':')) + ';'
    start = s.find('const DETECTIVE = ')
    if start < 0:
        raise SystemExit('DETECTIVE block not found in ' + html_path)
    end = s.find(';\n', start) + 1
    s = s[:start] + det_blob + s[end:]
    print(f'detective: {len(m)} region-months, {len(det)} variables')
else:
    print('detective_monthly.csv not found; run script 23 to fill the Trend Detective')

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
