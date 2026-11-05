"""
PRAAN — the one way GRACE seasonal means are computed
Imported by scripts 11 and 16. Script 23 builds the same numbers month by
month for the Trend Detective, and script 24 checks that they agree.

TWO RULES (CORRECTIONS.md section 12)
    1. Image dates. MASCON_CRI images are stamped with the last day of the
       previous month (the January 2005 image starts 2004-12-31). An image
       belongs to the month that contains its midpoint, not its start, so
       "January-May" really means January to May.
    2. Native grid. Averaging images drops their projection, and reducing
       the composite at a nominal scale resamples it onto a grid with a
       different alignment. The mean is taken on the product's own 0.5 degree
       grid, so each region uses the pixels the product actually has.
"""
import ee

MASCON_ID = 'NASA/GRACE/MASS_GRIDS_V04/MASCON_CRI'


def mascon():
    """lwe_thickness (cm) with a `mid` property: the image's midpoint in ms."""
    col = ee.ImageCollection(MASCON_ID).select('lwe_thickness')
    return col.map(lambda i: i.set('mid', ee.Number(i.get('system:time_start')).add(
        ee.Number(i.get('system:time_end')).subtract(i.get('system:time_start')).divide(2))))


def season_images(col, year, m0=1, m1=5):
    """Images whose midpoint falls in months m0..m1 of `year`."""
    start = ee.Date.fromYMD(year, m0, 1)
    end = ee.Date.fromYMD(year, m1, 1).advance(1, 'month')
    return col.filter(ee.Filter.gte('mid', start.millis())).filter(ee.Filter.lt('mid', end.millis()))


def season_mean(col, geom, year, m0=1, m1=5):
    """(mean cm over geom on the native grid, number of images) for one season."""
    sub = season_images(col, year, m0, m1)
    n = sub.size().getInfo()
    if n == 0:
        return float('nan'), 0
    native = ee.Image(col.first()).projection()
    # reduceRegions with these arguments, exactly as script 23: regions that
    # straddle mascon cells depend on how boundary pixels are weighted, and
    # reduceRegion weights them differently by up to 0.7 cm
    fc = sub.mean().reduceRegions(collection=ee.FeatureCollection([ee.Feature(geom)]),
                                  reducer=ee.Reducer.mean(), crs=native, tileScale=4)
    v = ee.Feature(fc.first()).get('mean').getInfo()
    return (float('nan') if v is None else v), n
