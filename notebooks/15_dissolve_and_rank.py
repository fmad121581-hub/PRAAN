"""
PRAAN — dissolve GADM ward fragments, then rank
Script: 15_dissolve_and_rank.py

WHY
    GADM 4.1 splits a single city-corporation ward across thana boundaries,
    producing polygons like "Ward No-63 (Part)" under both Bangshal and
    Chak Bazar. Joining BBS 2022 to those polygons BY NAME fails, so 77 of
    138 city polygons carried no census record and could not be ranked.

    BBS is keyed by (city_corp, ward_no), not by name. Parsing the ward
    number out of the polygon name and dissolving the fragments back into
    whole wards recovers 74 rankable wards instead of 61.

WHAT IT DOES NOT DO
    It does not invent population. Two other routes were tested and
    rejected: WorldPop density correlates NEGATIVELY with census population
    (it is a density, not a count), and density x ward area gives rank
    agreement of only rho = 0.20 with a 47% median error. 55 BBS wards have
    no GADM polygon at all - GADM 4.1 predates the ward expansion - and
    23 polygons carry union names with no ward number. Those stay unranked.

OUTPUT
    outputs/phase3_ward_scores_v4_dissolved.csv
    outputs/crisis_index_primary.csv        (overwritten - 74 wards)
    outputs/crisis_index_extended.csv
    outputs/crisis_index_altallocation.csv
    outputs/sensitivity_results.csv / sensitivity_summary.txt
    data/processed/dhaka_wards_dissolved.geojson
"""
import pandas as pd, numpy as np, geopandas as gpd, itertools, re, os

BASE = r"C:/Users/user/OneDrive/Nasa_2026/PRAAN/"
OUT, DATA = BASE + "outputs/", BASE + "data/processed/"
GADM = BASE + "data/raw/shapefiles/gadm41_BGD_4.shp"

MOB = {'low': 1_433_763, 'central': 2_580_774, 'high': 3_584_408}
ARR = {k: int(v * 0.660 * 0.450) for k, v in MOB.items()}
W4 = {'pop_norm': .35, 'builtup_norm': .25, 'flood_norm': .20, 'hh_size_norm': .20}

# Arrival allocation. This used to be 'inverse' - more arrivals to LESS
# stressed wards, on the assumption that low stress meant spare capacity.
# 19_validate_asi.py tested that against what actually happened. A density
# index built from year-2000 data alone predicts 2000-2020 population growth
# with Spearman rho = +0.324 (p = 0.005): wards already dense in 2000 grew
# FASTER, not slower. Median growth rises monotonically across baseline
# density quartiles (+94%, +106%, +111%, +113%). Density attracts arrivals.
# The assumption was backwards, so the published rule is now 'direct'.
# The effect is real but modest, and the ranking barely moves: Kafrul Ward
# No-14 is top under inverse, direct and population-only weighting, and the
# top 13 shares 9-10 wards across all three.
ALLOCATION = 'direct'
W3 = {'pop_norm': .40, 'builtup_norm': .35, 'flood_norm': .25}
mm = lambda s: (s - s.min()) / (s.max() - s.min())
wno = lambda s: (lambda m: int(m.group(1)) if m else None)(
    re.search(r'Ward No[-\s]*0*(\d+)', str(s), re.I))

# ── 1. LOAD ──────────────────────────────────────────────────
w = pd.read_csv(OUT + 'phase3_ward_scores_v3_deduped.csv')
bbs = pd.read_csv(DATA + 'bbs_2022_ward_final.csv')
gdf = gpd.read_file(GADM)
gdf = gdf[gdf.NAME_2 == 'Dhaka'][['GID_4', 'geometry']].to_crs(epsg=4326)
areas = gdf.to_crs(epsg=32646)
areas['area_km2'] = areas.area / 1e6
w = w.merge(areas[['GID_4', 'area_km2']], on='GID_4', how='left')

city = w[w.corp_spatial.isin(['DNCC', 'DSCC'])].copy()
rest = w[~w.corp_spatial.isin(['DNCC', 'DSCC'])].copy()
city['wno'] = city.NAME_4.map(wno)
bbs['key'] = list(zip(bbs.city_corp, bbs.ward_no))
city['key'] = [(c, int(n)) if pd.notna(n) else (c, None)
               for c, n in zip(city.corp_spatial, city.wno)]
city['matched'] = city.key.isin(set(bbs.key)) & city.wno.notna()
print(f'city polygons {len(city)} | matching a BBS ward {city.matched.sum()} '
      f'| distinct wards {city[city.matched].key.nunique()}')

# ── 2. DISSOLVE MATCHED FRAGMENTS INTO WHOLE WARDS ───────────
# pop is a density and builtup/flood are fractions, so they recombine as
# area-weighted means, not sums.
m = city[city.matched].copy()
m['_a'] = m.area_km2.fillna(m.area_km2.median())
agg = {}
for k, g in m.groupby('key'):
    a = g._a.sum()
    agg[k] = {
        'city_corp': k[0], 'ward_no': k[1],
        'pop':     np.average(g['pop'],     weights=g._a),
        'builtup': np.average(g['builtup'], weights=g._a),
        'flood':   np.average(g['flood'],   weights=g._a),
        'area_km2': a, 'n_fragments': len(g),
        'GID_4': '+'.join(sorted(g.GID_4)),
        'NAME_3': g.NAME_3.iloc[0],
        'NAME_4': f'Ward No-{k[1]:02d}',
    }
dis = pd.DataFrame(agg.values())
dis = dis.merge(bbs[['city_corp', 'ward_no', 'hh_total', 'pop_total',
                     'hh_size', 'elec_coverage']], on=['city_corp', 'ward_no'])
dis['corp_spatial'] = dis.city_corp
print(f'dissolved into {len(dis)} whole wards '
      f'({(dis.n_fragments>1).sum()} were split across thanas)')

unmatched = city[~city.matched].copy()
unmatched['ward_no'] = np.nan
unmatched['n_fragments'] = 1

# ── 3. REBUILD THE DIVISION TABLE AND RE-NORMALISE ───────────
keep = ['GID_4','NAME_3','NAME_4','pop','builtup','flood','city_corp',
        'corp_spatial','hh_total','pop_total','hh_size','elec_coverage',
        'area_km2','ward_no','n_fragments']
for d in (rest, unmatched):
    for c_ in keep:
        if c_ not in d: d[c_] = np.nan
allw = pd.concat([dis[keep], unmatched[keep], rest[keep]], ignore_index=True)
for src, dst in [('pop','pop_norm'), ('builtup','builtup_norm'), ('flood','flood_norm')]:
    allw[dst] = mm(allw[src])
hm = allw.hh_size.notna()
allw.loc[hm, 'hh_size_norm'] = mm(allw.loc[hm, 'hh_size'])

a3 = sum(allw[k] * v for k, v in W3.items())
allw['ASI'] = a3
bb = allw.hh_size_norm.notna()
allw.loc[bb, 'ASI'] = sum(allw.loc[bb, k] * v for k, v in W4.items())
allw['stress_tier'] = pd.cut(allw.ASI, [-.001,.33,.66,1.001],
                             labels=['Low stress','Moderate stress','High stress'])
allw.to_csv(OUT + 'phase3_ward_scores_v4_dissolved.csv', index=False)
print(f'division table rebuilt: {len(allw)} wards')

# ── 4. RANK ──────────────────────────────────────────────────
cc = allw[allw.corp_spatial.isin(['DNCC','DSCC'])].copy()
cc['observed'] = cc.pop_total.notna() & cc.hh_size.notna()
print(f'city wards {len(cc)} | observed {cc.observed.sum()} | unranked {(~cc.observed).sum()}')

def jenks_breaks(v, k):
    """Jenks natural breaks. The old 0.33/0.66 cut-points were arbitrary;
    these minimise within-class variance, which is the standard basis for a
    choropleth classification and can be defended as derived, not chosen."""
    v = np.sort(np.asarray(v, float)); n = len(v)
    m1 = np.zeros((n+1, k+1)); m2 = np.full((n+1, k+1), np.inf)
    m1[1:,1] = 1; m2[1:,1] = 0; m2[0,:] = 0
    for l in range(2, n+1):
        s1 = s2 = w = 0.0
        for m in range(1, l+1):
            i3 = l-m+1; val = v[i3-1]
            s2 += val*val; s1 += val; w += 1
            var = s2 - (s1*s1)/w
            i4 = i3-1
            if i4 != 0:
                for j in range(2, k+1):
                    if m2[l,j] >= var + m2[i4,j-1]:
                        m1[l,j] = i3; m2[l,j] = var + m2[i4,j-1]
        m1[l,1] = 1; m2[l,1] = var
    kk = n; brk = [v[-1]]*(k+1); brk[0] = v[0]; cnt = k
    while cnt > 1:
        brk[cnt-1] = v[int(m1[kk,cnt])-2]; kk = int(m1[kk,cnt])-1; cnt -= 1
    return brk


def build(df, w4=W4, alloc=ALLOCATION):
    d = df.copy()
    a = sum(d[k] * v for k, v in W3.items())
    b = d.hh_size_norm.notna()
    if b.any(): a.loc[b] = sum(d.loc[b, k] * v for k, v in w4.items())
    d['ASI'] = a
    pop = d.pop_total.fillna(d.pop_total.median())
    wt = pop * (1 - d.ASI) if alloc == 'inverse' else pop * d.ASI
    d['pop_share'] = wt / wt.sum()
    for k, v in ARR.items(): d[f'arrivals_{k}'] = (d.pop_share * v).astype(int)
    d['load_ratio_central'] = d.arrivals_central / pop
    d['asi_rank'] = d.ASI.rank(pct=True)
    d['arrival_rank'] = d.arrivals_central.rank(pct=True)
    rp = d.asi_rank * d.arrival_rank
    d['crisis_index'] = (rp - rp.min()) / (rp.max() - rp.min())
    b = jenks_breaks(d.crisis_index.values, 3)
    d['crisis_tier'] = pd.cut(d.crisis_index, [-.001, b[1], b[2], 1.001],
                              labels=['Low concern','Moderate concern','High concern'])
    d.attrs['breaks'] = b
    return d.sort_values('crisis_index', ascending=False)

COLS = ['GID_4','NAME_3','NAME_4','city_corp','ward_no','n_fragments','observed',
        'pop_total','ASI','arrivals_central','load_ratio_central','asi_rank',
        'arrival_rank','crisis_index','crisis_tier']
primary  = build(cc[cc.observed])
extended = build(cc)
alt      = build(cc[cc.observed], alloc='direct')
for n, d in [('PRIMARY', primary), ('EXTENDED', extended), ('ALT ALLOC (old inverse rule)', alt)]:
    print('\n' + '='*70); print(n); print('='*70)
    print(d.head(13)[['NAME_3','NAME_4','city_corp','ASI','arrivals_central',
                      'crisis_index','crisis_tier']].to_string(index=False))
    print('tiers:', d.crisis_tier.value_counts().to_dict())
    assert d.head(13).GID_4.nunique() == 13
ov = len(set(primary.head(13).GID_4) & set(alt.head(13).GID_4))
print(f'\nallocation-rule overlap: {ov}/13')
primary[COLS].to_csv(OUT + 'crisis_index_primary.csv', index=False)
extended[COLS].to_csv(OUT + 'crisis_index_extended.csv', index=False)
alt[COLS].to_csv(OUT + 'crisis_index_altallocation.csv', index=False)

# ── 5. SENSITIVITY ───────────────────────────────────────────
base = primary; b13 = list(base.head(13).GID_4); b5 = set(b13[:5])
br = {g: i for i, g in enumerate(base.GID_4)}
sub = cc[cc.observed]
rows = []
for dd in itertools.product([-.10,-.05,0,.05,.10], repeat=4):
    ww = {k: W4[k]+x for k, x in zip(W4, dd)}
    if any(v <= 0 for v in ww.values()): continue
    t = sum(ww.values()); ww = {k: v/t for k, v in ww.items()}
    r = build(sub, w4=ww); t13 = list(r.head(13).GID_4)
    rows.append({**{f'w_{k.replace("_norm","")}': round(v,3) for k,v in ww.items()},
        'overlap_top13': len(set(t13)&set(b13)), 'exact_top13': set(t13)==set(b13),
        'overlap_top5': len(set(t13[:5])&b5), 'top1_same': t13[0]==b13[0],
        'max_shift_top13': max(abs(br[g]-list(r.GID_4).index(g)) for g in b13)})
s = pd.DataFrame(rows); n = len(s)
s.to_csv(OUT + 'sensitivity_results.csv', index=False)
txt = f"""PRAAN — ASI Weight Sensitivity Analysis
{'='*64}

SETUP
  Ward set     : {len(sub)} city-corporation wards with BBS 2022 records,
                 after dissolving GADM "(Part)" fragments into whole wards
  Formula      : 4-indicator ASI (the one that generates the ranking)
  Base weights : pop {W4['pop_norm']} / builtup {W4['builtup_norm']} / flood {W4['flood_norm']} / household size {W4['hh_size_norm']}
  Variation    : +/-10pp per indicator, 5pp steps, renormalised to sum 1
  Combinations : {n}

RESULTS
  Highest-ranked ward unchanged   : {int(s.top1_same.sum())}/{n} ({s.top1_same.mean()*100:.1f}%)
  Mean top-5 overlap              : {s.overlap_top5.mean():.1f}/5
  Mean top-13 overlap             : {s.overlap_top13.mean():.1f}/13 (min {s.overlap_top13.min()})
  Exact top-13 set reproduced     : {int(s.exact_top13.sum())}/{n} ({s.exact_top13.mean()*100:.1f}%)
  Median worst-case rank shift    : {s.max_shift_top13.median():.0f} places
"""
open(OUT + 'sensitivity_summary.txt','w').write(txt)
print(txt)

# ── 6. DISSOLVED GEOJSON FOR THE MAP ─────────────────────────
gdf2 = gdf.merge(w[['GID_4','NAME_3','NAME_4','corp_spatial']], on='GID_4', how='left')
gdf2['wno'] = gdf2.NAME_4.map(wno)
gdf2['key'] = [(c, int(n)) if pd.notna(n) else (c, None)
               for c, n in zip(gdf2.corp_spatial, gdf2.wno)]
ok = set(dis.set_index(['city_corp','ward_no']).index)
gdf2['dkey'] = gdf2.key.map(lambda k: k if k in ok else None)
part = gdf2[gdf2.dkey.notna()].dissolve(by='dkey', aggfunc='first').reset_index()
part['GID_4'] = part.dkey.map(lambda k: '+'.join(sorted(
    gdf2[gdf2.dkey == k].GID_4)))
part['NAME_4'] = part.dkey.map(lambda k: f'Ward No-{k[1]:02d}')
keepgeo = pd.concat([part[['GID_4','NAME_3','NAME_4','geometry']],
                     gdf2[gdf2.dkey.isna()][['GID_4','NAME_3','NAME_4','geometry']]],
                    ignore_index=True)
gpd.GeoDataFrame(keepgeo, crs='EPSG:4326').to_file(
    DATA + 'dhaka_wards_dissolved.geojson', driver='GeoJSON')
print(f'\ngeojson: {len(keepgeo)} polygons (was {len(gdf2)})')
print('done')
