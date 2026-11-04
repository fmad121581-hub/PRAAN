"""
PRAAN — monthly series for the Trend Detective tool
Script: 23_detective_monthly.py

WHY THIS EXISTS
    The challenge asks for a tool that lets a user SELECT a variable and a
    region, see how it changes, and test whether the change is significant.
    PRAAN's own analysis fixed both choices (GRACE, Barind Tract, Jan-May).
    This script extracts the monthly regional mean of six variables over
    five regions, so the page can aggregate any season and any range of
    years itself and run the same trend test as script 18.

VARIABLES
    tws    GRACE/GRACE-FO JPL mascon RL06.3Mv04, lwe_thickness        cm
    gpm    GPM IMERG V07 monthly precipitation                       mm/month
    chirps CHIRPS v2.0 pentad precipitation, summed per month        mm/month
    ndvi   MODIS Terra MOD13A3 v061 monthly NDVI                     unitless
    lst    MODIS Terra MOD11A2 v061 8-day daytime land surface temp  deg C
    soil   GLDAS-2.1 Noah root-zone soil moisture (RootMoist_inst)   mm

REGIONS (GAUL 2015 level 2 districts, as script 16)
    barind  Rajshahi, Naogaon, Natore, Nawabganj
    coastal Khulna, Satkhira, Bagerhat
    haor    Sylhet, Sunamganj, Habiganj, Maulvibazar
    dhaka   Dhaka, Gazipur, Narayanganj, Manikganj
    bd      Bangladesh (GAUL level 0)

GRACE MONTHS
    MASCON_CRI images are stamped with the LAST day of the previous month
    (the January 2005 image starts 2004-12-31, the May image 2005-04-30), so
    filtering by start date shifts every month by one. Each GRACE image is
    therefore placed in the calendar month that contains its midpoint, and n
    is the number of images in that month. The page takes an n-weighted mean
    over a season, which equals the mean of all images in it.

    Script 16 filtered by start date over 1 January - 31 May, so its
    "January-May" series is really February-May. Script 24 checks that the
    February-May means rebuilt from this file match script 16 exactly.

NATIVE GRID
    Averaging images in Earth Engine drops their projection, and a reduction
    at a nominal `scale` then resamples onto a grid with a different
    alignment. For GRACE over the small coastal region that moved values by
    several centimetres (script 16 had this). Every monthly image here is
    reduced on its source dataset's own grid (crs and transform of the first
    image), so each region's mean uses the pixels the product actually has.

RUN ONE VARIABLE
    python 23_detective_monthly.py tws    re-extracts only tws and replaces
                                          its rows in the existing CSV

RUN
    cd notebooks
    python 23_detective_monthly.py        (needs `earthengine authenticate`)

OUTPUT
    data/processed/detective_monthly.csv  variable, region, year, month, value, n
"""
import os, sys, time
import pandas as pd
import ee

ee.Initialize(project='project-attempt-dhaka-heat')

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + os.sep
OUT_CSV = BASE + 'data/processed/detective_monthly.csv'

DISTRICTS = {
    'barind':  ['Rajshahi', 'Naogaon', 'Natore', 'Nawabganj'],
    'coastal': ['Khulna', 'Satkhira', 'Bagerhat'],
    'haor':    ['Sylhet', 'Sunamganj', 'Habiganj', 'Maulvibazar'],
    'dhaka':   ['Dhaka', 'Gazipur', 'Narayanganj', 'Manikganj'],
}
gaul2 = ee.FeatureCollection('FAO/GAUL/2015/level2').filter(ee.Filter.eq('ADM0_NAME', 'Bangladesh'))
missing = [d for ds in DISTRICTS.values() for d in ds
           if d not in set(gaul2.aggregate_array('ADM2_NAME').getInfo())]
if missing:
    raise SystemExit(f'GAUL names not found: {missing}')
regions = ee.FeatureCollection(
    [ee.Feature(gaul2.filter(ee.Filter.inList('ADM2_NAME', ds)).geometry(), {'region': k})
     for k, ds in DISTRICTS.items()]
    + [ee.Feature(ee.FeatureCollection('FAO/GAUL/2015/level0')
                  .filter(ee.Filter.eq('ADM0_NAME', 'Bangladesh')).geometry(), {'region': 'bd'})])


def monthly(col, reducer, prep, by_mid=False):
    """One image per calendar month of `col`, reduced with `reducer` after
    `prep`; property n = number of source images in that month. With
    by_mid, an image belongs to the month containing its midpoint."""
    if by_mid:
        col = col.map(lambda i: i.set('mid', ee.Number(i.get('system:time_start')).add(
            ee.Number(i.get('system:time_end')).subtract(i.get('system:time_start')).divide(2))))

    def per_month(start):
        start = ee.Date(start)
        sub = (col.filter(ee.Filter.And(ee.Filter.gte('mid', start.millis()),
                                        ee.Filter.lt('mid', start.advance(1, 'month').millis())))
               if by_mid else col.filterDate(start, start.advance(1, 'month')))
        # an empty month (past the end of a record) has no bands to do
        # arithmetic on; give it a masked placeholder, dropped below by n > 0
        img = ee.Image(ee.Algorithms.If(sub.size().gt(0),
                                        prep(sub.reduce(reducer), start).rename('v'),
                                        ee.Image.constant(0).rename('v').updateMask(0)))
        return img.set({'year': start.get('year'), 'month': start.get('month'), 'n': sub.size()})
    return per_month


VARS = {
    'tws': dict(col='NASA/GRACE/MASS_GRIDS_V04/MASCON_CRI', band='lwe_thickness',
                years=(2002, 2024), reducer=ee.Reducer.mean(),
                prep=lambda img, d: img, by_mid=True),
    'gpm': dict(col='NASA/GPM_L3/IMERG_MONTHLY_V07', band='precipitation',
                years=(2001, 2025), reducer=ee.Reducer.mean(),
                # mm/hr averaged over the month -> mm in the month
                prep=lambda img, d: img.multiply(d.advance(1, 'month').difference(d, 'hour'))),
    'chirps': dict(col='UCSB-CHG/CHIRPS/PENTAD', band='precipitation',
                   years=(1981, 2025), reducer=ee.Reducer.sum(),
                   prep=lambda img, d: img),
    'ndvi': dict(col='MODIS/061/MOD13A3', band='NDVI',
                 years=(2001, 2025), reducer=ee.Reducer.mean(),
                 prep=lambda img, d: img.multiply(0.0001)),
    'lst': dict(col='MODIS/061/MOD11A2', band='LST_Day_1km',
                years=(2001, 2025), reducer=ee.Reducer.mean(),
                prep=lambda img, d: img.multiply(0.02).subtract(273.15)),
    'soil': dict(col='NASA/GLDAS/V021/NOAH/G025/T3H', band='RootMoist_inst',
                 years=(2001, 2025), reducer=ee.Reducer.mean(),
                 prep=lambda img, d: img),
}

ONLY = sys.argv[1:]
rows = []
for var, cfg in VARS.items():
    if ONLY and var not in ONLY:
        continue
    col = ee.ImageCollection(cfg['col']).select(cfg['band'])
    native = col.first().projection()
    fn = monthly(col, cfg['reducer'], cfg['prep'], cfg.get('by_mid', False))
    print(f'{var}: {cfg["years"][0]}-{cfg["years"][1]}', flush=True)
    for year in range(cfg['years'][0], cfg['years'][1] + 1):
        starts = ee.List.sequence(0, 11).map(lambda m: ee.Date.fromYMD(year, 1, 1).advance(m, 'month'))
        imgs = ee.ImageCollection(starts.map(fn)).filter(ee.Filter.gt('n', 0))
        fc = imgs.map(lambda img: img.reduceRegions(
            collection=regions, reducer=ee.Reducer.mean(), crs=native, tileScale=4)
            # geometry dropped: otherwise every month ships the full boundaries back
            .map(lambda f: ee.Feature(None, {'region': f.get('region'), 'mean': f.get('mean'),
                                             'year': img.get('year'), 'month': img.get('month'),
                                             'n': img.get('n')}))).flatten()
        for attempt in range(3):
            try:
                feats = fc.getInfo()['features']
                break
            except Exception as e:
                print(f'  {year} attempt {attempt + 1} failed: {str(e)[:120]}', flush=True)
                time.sleep(5)
        else:
            raise SystemExit(f'{var} {year} failed three times')
        for f in feats:
            p = f['properties']
            if p.get('mean') is None:
                continue
            rows.append({'variable': var, 'region': p['region'], 'year': int(p['year']),
                         'month': int(p['month']), 'value': p['mean'], 'n': int(p['n'])})
    print(f'  {sum(1 for r in rows if r["variable"] == var)} region-months', flush=True)

df = pd.DataFrame(rows)
if ONLY and os.path.exists(OUT_CSV):
    old = pd.read_csv(OUT_CSV)
    df = pd.concat([old[~old.variable.isin(ONLY)], df], ignore_index=True)
df = df.sort_values(['variable', 'region', 'year', 'month'])
df.to_csv(OUT_CSV, index=False)
print(f'wrote {OUT_CSV}: {len(df)} rows')
