"""
PRAAN — robust trend statistics
Script: 18_robust_trends.py

WHY
    Every trend in this project so far used ordinary least squares. OLS
    assumes each year is independent of the last. Terrestrial water storage
    is not: a depleted year is followed by a depleted year. That serial
    correlation inflates the effective sample size, so OLS p-values come
    out smaller than they should be — the trend looks more certain than
    the data supports.

    Hydrology uses Mann-Kendall with Sen's slope instead. Mann-Kendall is
    non-parametric (no normality assumption), Sen's slope is robust to
    outliers, and the Hamed-Rao variant corrects the variance for serial
    correlation. This script runs all three against every series PRAAN
    relies on, so the published claims can be stated on the stricter test.

    If a trend survives Hamed-Rao, it is real. If it only survives OLS,
    it should be reported far more cautiously.

NO EARTH ENGINE NEEDED — reads committed CSVs.

OUTPUT
    outputs/robust_trend_stats.csv
    outputs/robust_trend_summary.txt
"""
import pandas as pd, numpy as np, os
from scipy import stats

# Project root resolved from this file's location, so the script runs
# unchanged on any machine.
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + os.sep
DATA, OUT = BASE + "data/processed/", BASE + "outputs/"


def sens_slope(y, x):
    """Median of all pairwise slopes. Robust to outliers."""
    s = [(y[j] - y[i]) / (x[j] - x[i])
         for i in range(len(y)) for j in range(i + 1, len(y)) if x[j] != x[i]]
    return float(np.median(s)) if s else np.nan


def mann_kendall(y, autocorr_correction=True):
    """Mann-Kendall trend test. With autocorr_correction, applies the
    Hamed-Rao variance inflation for serially correlated data."""
    y = np.asarray(y, float)
    n = len(y)
    S = sum(np.sign(y[j] - y[i]) for i in range(n - 1) for j in range(i + 1, n))

    # tie-aware variance
    _, counts = np.unique(y, return_counts=True)
    tie = sum(c * (c - 1) * (2 * c + 5) for c in counts if c > 1)
    var = (n * (n - 1) * (2 * n + 5) - tie) / 18.0

    n_star_ratio = 1.0
    if autocorr_correction and n > 3:
        # Hamed & Rao (1998): inflate variance using the autocorrelation of
        # the de-trended ranks.
        x = np.arange(n)
        slope = sens_slope(y, x)
        detr = y - slope * x
        r = np.argsort(np.argsort(detr))
        rbar, rvar = r.mean(), r.var()
        acc = 0.0
        if rvar > 0:
            for lag in range(1, n):
                rho = np.sum((r[:-lag] - rbar) * (r[lag:] - rbar)) / ((n - lag) * rvar)
                # keep only lags significant at 95%
                if abs(rho) > 1.96 / np.sqrt(n - lag):
                    acc += (n - lag) * (n - lag - 1) * (n - lag - 2) * rho
        n_star_ratio = 1 + (2.0 / (n * (n - 1) * (n - 2))) * acc
        n_star_ratio = max(n_star_ratio, 1e-6)
        var *= n_star_ratio

    if S > 0:   Z = (S - 1) / np.sqrt(var)
    elif S < 0: Z = (S + 1) / np.sqrt(var)
    else:       Z = 0.0
    p = 2 * (1 - stats.norm.cdf(abs(Z)))
    return S, Z, p, n_star_ratio


def lag1(y):
    y = np.asarray(y, float)
    if len(y) < 3: return np.nan
    return float(np.corrcoef(y[:-1], y[1:])[0, 1])


def analyse(label, sub, ycol):
    sub = sub.dropna(subset=[ycol]).sort_values('year')
    x, y = sub.year.values.astype(float), sub[ycol].values.astype(float)
    if len(y) < 5:
        return None
    sl, ic, r, p_ols, se = stats.linregress(x, y)
    S, Z, p_mk, ratio = mann_kendall(y, autocorr_correction=False)
    S2, Z2, p_hr, ratio2 = mann_kendall(y, autocorr_correction=True)
    return {
        'series': label, 'n': len(y),
        'lag1_autocorr': lag1(y),
        'ols_slope': sl, 'ols_p': p_ols,
        'sens_slope': sens_slope(y, x),
        'mk_p': p_mk,
        'mk_p_autocorr_corrected': p_hr,
        'variance_inflation': ratio2,
        'survives_strict_test': p_hr < 0.05,
    }


rows = []

# ── GRACE by region ──────────────────────────────────────────
reg = pd.read_csv(DATA + 'grace_regional_tws.csv')
for region in reg.region.unique():
    s = reg[reg.region == region]
    for label, sub in [(f'{region} 2002-2017', s[s.year <= 2017]),
                       (f'{region} 2002-2024', s)]:
        r = analyse(label, sub, 'tws')
        if r: rows.append(r)

# ── Barind GRACE (the headline series) ───────────────────────
g = pd.read_csv(DATA + 'grace_mascon_tws_raw.csv')
for label, sub in [('Barind MASCON 2002-2017', g[g.year <= 2017]),
                   ('Barind MASCON 2002-2024', g)]:
    r = analyse(label, sub, 'tws_anomaly')
    if r: rows.append(r)

# ── the other NASA variables, Barind districts ───────────────
BARIND = ['Rajshahi', 'Naogaon', 'Natore', 'Nawabganj']
ch = pd.read_csv(DATA + 'chirps_aman_season_raw.csv')
ch = ch[ch.district.isin(BARIND)].groupby('year', as_index=False).rainfall_mm.mean()
r = analyse('CHIRPS Aman rainfall, Barind', ch, 'rainfall_mm')
if r: rows.append(r)

nd = pd.read_csv(DATA + 'modis_ndvi_aman_raw.csv')
nd = nd[nd.district.isin(BARIND)].groupby('year', as_index=False).ndvi_mean.mean()
r = analyse('MODIS NDVI Aman, Barind', nd, 'ndvi_mean')
if r: rows.append(r)

df = pd.DataFrame(rows)
os.makedirs(OUT, exist_ok=True)
df.to_csv(OUT + 'robust_trend_stats.csv', index=False)

pd.set_option('display.width', 200)
show = df[['series', 'n', 'lag1_autocorr', 'ols_slope', 'ols_p', 'sens_slope',
           'mk_p', 'mk_p_autocorr_corrected', 'survives_strict_test']]
print('=' * 118)
print('ROBUST TREND TESTS — does each trend survive a test that allows for serial correlation?')
print('=' * 118)
print(show.to_string(index=False, float_format=lambda x: f'{x:.4f}'))

head = df[df.series.str.contains('Barind MASCON 2002-2017')]
print('\n' + '=' * 78)
print('HEADLINE SERIES — Barind Tract, 2002-2017')
print('=' * 78)
if len(head):
    h = head.iloc[0]
    print(f'  lag-1 autocorrelation      : {h.lag1_autocorr:+.3f}')
    print(f'  OLS slope / p              : {h.ols_slope:+.3f} cm/yr,  p = {h.ols_p:.4f}')
    print(f"  Sen's slope                : {h.sens_slope:+.3f} cm/yr")
    print(f'  Mann-Kendall p             : {h.mk_p:.4f}')
    print(f'  Mann-Kendall p, corrected  : {h.mk_p_autocorr_corrected:.4f}')
    print(f'  variance inflation applied : x{h.variance_inflation:.2f}')
    print(f"\n  VERDICT: {'holds under the strict test' if h.survives_strict_test else 'DOES NOT hold once serial correlation is allowed for'}")

with open(OUT + 'robust_trend_summary.txt', 'w', encoding='utf-8') as f:
    f.write('PRAAN — robust trend statistics\n' + '=' * 78 + '\n\n')
    f.write('OLS assumes independent years. Water storage is serially correlated,\n'
            'so OLS p-values are optimistic. Mann-Kendall is non-parametric and\n'
            "Sen's slope is outlier-robust; the Hamed-Rao variant corrects the\n"
            'variance for that serial correlation.\n\n')
    f.write(show.to_string(index=False, float_format=lambda x: f'{x:.4f}') + '\n\n')
    f.write('READING THIS TABLE\n' + '-' * 78 + '\n')
    f.write('survives_strict_test = True means the trend is still significant at\n'
            'p < 0.05 after the autocorrelation correction. Those are the claims\n'
            'that can be made without qualification. Anything False should be\n'
            'reported as suggestive, not established.\n')
print(f'\nWrote {OUT}robust_trend_stats.csv and robust_trend_summary.txt')
