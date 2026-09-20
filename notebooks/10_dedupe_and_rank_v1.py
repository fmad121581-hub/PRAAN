"""
PRAAN — Supply vs Demand Gap / Crisis Index  [CORRECTED]
Script: 10_supply_demand.py

WHAT WAS WRONG IN THE PREVIOUS VERSION
 1. DUPLICATE WARDS. DNCC and DSCC both number their wards 1..N, so NAME_4
    ("Ward No-43") is not unique. Merging BBS onto GADM by name produced a
    cartesian match: 1,124 rows for 1,078 wards upstream, and 184 rows for
    138 city-corporation wards here. The published "13 high-concern wards"
    contained only 10 distinct wards — Rampura 22, Tejgaon 39 and Mirpur 12
    each appeared twice, with DIFFERENT ASI values, meaning one copy of each
    carried the wrong BBS record. Percentile ranks were computed over the
    duplicated frame, so every crisis_index value was distorted.
    FIX: the spatial join (ward centroid within corp polygon) is
    authoritative; keep the BBS record whose city_corp agrees with it.

 2. THE SCRIPT DID NOT PRODUCE ITS OWN COMMITTED OUTPUT. The old script
    computed gap_score = ASI * load_ratio, but the committed CSV contained
    crisis_index = normalised rank product. FIX: this script computes the
    rank product, which is what the write-up describes.

 3. IMPUTED POPULATION WAS RANKED SILENTLY. 77 of 138 city-corporation
    wards have no BBS match (mostly GADM "(Part)" fragments). They were
    given the MEDIAN population and the MEAN ASI and then ranked alongside
    real data. FIX: 'observed' flag, and a primary result restricted to the
    61 fully-observed wards. The extended table is still produced, with the
    flag, but the primary table is what should be published.

 4. ASI FALLBACK. Wards without BBS data now use the 3-indicator ASI
    (real data) rather than a mean fill.

NOTE ON THE ALLOCATION RULE — read this before quoting any result.
    Arrivals are distributed as pop * (1 - ASI): more arrivals go to LESS
    stressed wards, on the assumption that low stress means spare capacity.
    Observed behaviour in Dhaka is arguably the opposite — climate migrants
    cluster in dense, low-income settlements (Korail, Sattola, Bhashantek),
    which are high-ASI. ALLOCATION = 'direct' runs that counterfactual.
    On the 61-ward primary set the two rules share 10 of 13 top wards, so
    the headline is reasonably robust to this choice — but the assumption
    must be stated on the website, because it is currently invisible there.

OUTPUT
    outputs/crisis_index_primary.csv     <- publish this one
    outputs/crisis_index_extended.csv
    outputs/crisis_index_altallocation.csv
    outputs/phase3_gap_map.png
"""
import pandas as pd, numpy as np, geopandas as gpd
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt, matplotlib.colors as mcolors
from matplotlib.patches import Patch
import warnings, os
warnings.filterwarnings('ignore')

# ─────────────────────────────────────────────────────────────
#  SUPERSEDED FOR RANKING BY 15_dissolve_and_rank.py
#  This script ranks 61 wards by joining BBS to GADM on ward NAME, which
#  fails for every "(Part)" fragment. Script 15 dissolves those fragments
#  and joins on (city_corp, ward_no) — the key BBS actually uses — giving
#  75 ranked wards, and it writes the SAME output filenames.
#  This script is STILL REQUIRED: it writes phase3_ward_scores_v3_deduped.csv,
#  which script 15 reads. Its own ranking outputs are written with a _v1
#  suffix so they cannot overwrite the published result.
# ─────────────────────────────────────────────────────────────
# Project root resolved from this file's location, so the script runs
# unchanged on any machine.
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + os.sep
OCHA_SHP = BASE + "data/raw/ocha/bgd_admin3.shp"
GADM_SHP = BASE + "data/raw/shapefiles/gadm41_BGD_4.shp"
ASI_CSV = BASE + "outputs/phase3_ward_scores_v2.csv"
OUT = BASE + "outputs/"

ALLOCATION = 'inverse'          # 'inverse' (published) or 'direct' (counterfactual)
MOB = {'low': 1_433_763, 'central': 2_580_774, 'high': 3_584_408}
DIV_SHARE, CITY_SHARE = 0.660, 0.450
ARR = {k: int(v * DIV_SHARE * CITY_SHARE) for k, v in MOB.items()}
W4 = {'pop_norm': .35, 'builtup_norm': .25, 'flood_norm': .20, 'hh_size_norm': .20}
W3 = {'pop_norm': .40, 'builtup_norm': .35, 'flood_norm': .25}

print('Arrivals to Dhaka City:', {k: f'{v:,}' for k, v in ARR.items()})

# ── 1. SPATIAL ASSIGNMENT (authoritative) ────────────────────
ocha = gpd.read_file(OCHA_SHP).to_crs(epsg=4326)
corp = ocha[ocha.adm3_name.isin(['Dhaka North City Corporation',
                                 'Dhaka South City Corporation'])].copy()
corp['city_corp'] = corp.adm3_name.map({'Dhaka North City Corporation': 'DNCC',
                                        'Dhaka South City Corporation': 'DSCC'})

gadm = gpd.read_file(GADM_SHP).to_crs(epsg=4326)
dhaka = gadm[gadm.NAME_2 == 'Dhaka'].copy()
cent = gpd.GeoDataFrame(dhaka[['GID_4']], geometry=dhaka.geometry.centroid,
                        crs='EPSG:4326')
sp = (gpd.sjoin(cent, corp[['city_corp', 'geometry']], how='left', predicate='within')
      [['GID_4', 'city_corp']].rename(columns={'city_corp': 'corp_spatial'})
      .drop_duplicates('GID_4'))
assert sp.GID_4.is_unique, 'a ward centroid fell in two corporation polygons'

# ── 2. DEDUPE ────────────────────────────────────────────────
asi = pd.read_csv(ASI_CSV)
n_before = len(asi)
w = asi.merge(sp, on='GID_4', how='left')
w['keep'] = (w.city_corp == w.corp_spatial) | w.corp_spatial.isna()
dupids = w.GID_4[w.GID_4.duplicated(keep=False)].unique()
w = (pd.concat([w[~w.GID_4.isin(dupids)], w[w.GID_4.isin(dupids) & w.keep]])
     .drop_duplicates('GID_4').drop(columns='keep').reset_index(drop=True))
print(f'Dedupe: {n_before} rows -> {len(w)} unique wards '
      f'({n_before - len(w)} duplicate rows removed)')
assert w.GID_4.is_unique

# hh_size_norm was min-maxed over the duplicated frame; redo it
mm = lambda s: (s - s.min()) / (s.max() - s.min())
m = w.hh_size.notna()
w.loc[m, 'hh_size_norm'] = mm(w.loc[m, 'hh_size'])

# persist the deduplicated frame so 13_sensitivity_analysis.py uses the
# identical hh_size_norm base and cannot drift from this script
w.to_csv(OUT + 'phase3_ward_scores_v3_deduped.csv', index=False)

c = w[w.corp_spatial.isin(['DNCC', 'DSCC'])].copy()
c['city_corp'] = c.corp_spatial
c['observed'] = c.pop_total.notna() & c.hh_size.notna()
print(f'City-corporation wards: {len(c)}  '
      f'(observed {c.observed.sum()}, population imputed {(~c.observed).sum()})')


# ── 3. ASI + CRISIS INDEX ────────────────────────────────────
def build(df, w4=W4, w3=W3, alloc=ALLOCATION):
    d = df.copy()
    a = sum(d[k] * v for k, v in w3.items())
    bb = d.hh_size_norm.notna()
    a.loc[bb] = sum(d.loc[bb, k] * v for k, v in w4.items())
    d['ASI'] = a
    pop = d.pop_total.fillna(d.pop_total.median())
    wt = pop * (1 - d.ASI) if alloc == 'inverse' else pop * d.ASI
    d['pop_share'] = wt / wt.sum()
    for k, v in ARR.items():
        d[f'arrivals_{k}'] = (d.pop_share * v).astype(int)
    d['load_ratio_central'] = d.arrivals_central / pop
    d['asi_rank'] = d.ASI.rank(pct=True)
    d['arrival_rank'] = d.arrivals_central.rank(pct=True)
    rp = d.asi_rank * d.arrival_rank
    d['crisis_index'] = (rp - rp.min()) / (rp.max() - rp.min())
    d['crisis_tier'] = pd.cut(d.crisis_index, [-.001, .33, .66, 1.001],
                              labels=['Low concern', 'Moderate concern', 'High concern'])
    return d.sort_values('crisis_index', ascending=False)


COLS = ['GID_4', 'NAME_3', 'NAME_4', 'city_corp', 'observed', 'pop_total', 'ASI',
        'arrivals_central', 'load_ratio_central', 'asi_rank', 'arrival_rank',
        'crisis_index', 'crisis_tier']

primary = build(c[c.observed])
extended = build(c)
altalloc = build(c[c.observed], alloc='direct')

for name, df in [('PRIMARY (61 observed wards) — PUBLISH THIS', primary),
                 ('EXTENDED (138 wards, 77 population-imputed)', extended),
                 ("ALT ALLOCATION (arrivals -> more stressed wards)", altalloc)]:
    print('\n' + '=' * 74); print(name); print('=' * 74)
    print(df.head(13)[['NAME_3', 'NAME_4', 'city_corp', 'ASI',
                       'arrivals_central', 'crisis_index', 'crisis_tier']]
          .to_string(index=False))
    print('Tiers:', df.crisis_tier.value_counts().to_dict())
    assert df.head(13).GID_4.nunique() == 13, 'duplicate ward in top 13'

ov = len(set(primary.head(13).GID_4) & set(altalloc.head(13).GID_4))
print(f'\nTop-13 overlap, inverse vs direct allocation: {ov}/13')

os.makedirs(OUT, exist_ok=True)
primary[COLS].to_csv(OUT + 'crisis_index_primary_v1.csv', index=False)
extended[COLS].to_csv(OUT + 'crisis_index_extended_v1.csv', index=False)
altalloc[COLS].to_csv(OUT + 'crisis_index_altallocation_v1.csv', index=False)
print(f'\nWrote corrected CSVs to {OUT}')

# ── 4. MAP (primary) ─────────────────────────────────────────
gm = dhaka.merge(primary[['GID_4', 'crisis_index', 'crisis_tier',
                          'arrivals_central', 'ASI']], on='GID_4', how='left')
fig, ax = plt.subplots(figsize=(16, 16)); fig.patch.set_facecolor('white')
gm.plot(column='crisis_index', cmap='OrRd', vmin=0, vmax=1, linewidth=.4,
        edgecolor='#fff', ax=ax,
        missing_kwds={'color': 'lightgrey', 'label': 'Not ranked'})
corp.boundary.plot(ax=ax, color='navy', linewidth=2, alpha=.7)
ax.set_xlim(90.30, 90.60); ax.set_ylim(23.63, 23.92)
sm = plt.cm.ScalarMappable(cmap='OrRd', norm=mcolors.Normalize(0, 1)); sm.set_array([])
cb = fig.colorbar(sm, ax=ax, fraction=.025, pad=.01, shrink=.7)
cb.set_label('Crisis Index (0–1)', fontsize=11)
ax.legend(handles=[Patch(facecolor='#fdcc8a', label='Low concern (<0.33)'),
                   Patch(facecolor='#fc8d59', label='Moderate (0.33–0.66)'),
                   Patch(facecolor='#d7301f', label='High concern (>0.66)'),
                   Patch(facecolor='lightgrey', label='Not ranked (no BBS match)')],
          loc='lower left', fontsize=10, title='Crisis Tier')
ax.set_title('PRAAN — Crisis Index (corrected)\n'
             f'{len(primary)} fully-observed Dhaka city-corporation wards · '
             'Central scenario', fontsize=13, fontweight='bold', pad=15)
ax.text(.5, -.03, f'Crisis Index = normalised rank(ASI) x rank(arrivals) · '
                  f'central estimate {ARR["central"]:,} arrivals\n'
                  f'Arrivals allocated by pop x (1 - ASI) · '
                  f'{(~c.observed).sum()} wards without a BBS match are excluded',
        transform=ax.transAxes, ha='center', fontsize=8, color='#666', style='italic')
ax.set_axis_off(); plt.tight_layout()
plt.savefig(OUT + 'phase3_gap_map_v1.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print('Map saved -> phase3_gap_map.png')
