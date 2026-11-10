// PRAAN trend statistics — the same tests as notebooks/18_robust_trends.py.
// Script 21 inlines this file into outputs/PRAAN.html; test_trend_stats.mjs
// checks it against outputs/robust_trend_stats.csv and scipy.
const TrendStats = (() => {
  // Complementary error function, W. J. Cody's rational approximations
  // (relative error below 1e-15), so p-values match scipy closely.
  function erfc(x) {
    const ax = Math.abs(x);
    let r;
    if (ax < 0.5) {
      const t = x * x;
      const p = [3.16112374387056560e00, 1.13864154151050156e02, 3.77485237685302021e02, 3.20937758913846947e03, 1.85777706184603153e-1];
      const q = [2.36012909523441209e01, 2.44024637934444173e02, 1.28261652607737228e03, 2.84423683343917062e03];
      const num = ((((p[4] * t + p[0]) * t + p[1]) * t + p[2]) * t + p[3]);
      const den = ((((t + q[0]) * t + q[1]) * t + q[2]) * t + q[3]);
      return 1 - x * num / den;
    } else if (ax < 4) {
      const p = [5.64188496988670089e-1, 8.88314979438837594e00, 6.61191906371416295e01, 2.98635138197400131e02, 8.81952221241769090e02, 1.71204761263407058e03, 2.05107837782607147e03, 1.23033935479799725e03, 2.15311535474403846e-8];
      const q = [1.57449261107098347e01, 1.17693950891312499e02, 5.37181101862009858e02, 1.62138957456669019e03, 3.29079923573345963e03, 4.36261909014324716e03, 3.43936767414372164e03, 1.23033935480374942e03];
      let num = p[8] * ax, den = ax;
      for (let i = 0; i < 7; i++) { num = (num + p[i]) * ax; den = (den + q[i]) * ax; }
      r = (num + p[7]) / (den + q[7]);
    } else {
      const p = [3.05326634961232344e-1, 3.60344899949804439e-1, 1.25781726111229246e-1, 1.60837851487422766e-2, 6.58749161529837803e-4, 1.63153871373020978e-2];
      const q = [2.56852019228982242e00, 1.87295284992346725e00, 5.27905102951428412e-1, 6.05183413124413191e-2, 2.33520497626869185e-3];
      const t = 1 / (ax * ax);
      let num = p[5] * t, den = t;
      for (let i = 0; i < 4; i++) { num = (num + p[i]) * t; den = (den + q[i]) * t; }
      r = t * (num + p[4]) / (den + q[4]);
      r = (0.56418958354775628695 - r) / ax;
    }
    const xsq = Math.trunc(ax * 16) / 16, del = (ax - xsq) * (ax + xsq);
    r = Math.exp(-xsq * xsq) * Math.exp(-del) * r;
    return x < 0 ? 2 - r : r;
  }
  // two-sided p for a standard normal Z: 2 * (1 - Phi(|Z|))
  const twoSidedP = z => erfc(Math.abs(z) / Math.SQRT2);

  // Median of all pairwise slopes over pairs with distinct x (script 18).
  function pairSlopes(y, x) {
    const s = [];
    for (let i = 0; i < y.length; i++)
      for (let j = i + 1; j < y.length; j++)
        if (x[j] !== x[i]) s.push((y[j] - y[i]) / (x[j] - x[i]));
    return s.sort((a, b) => a - b);
  }
  const median = a => {
    const b = [...a].sort((p, q) => p - q), m = b.length >> 1;
    return b.length % 2 ? b[m] : (b[m - 1] + b[m]) / 2;
  };
  const sensSlope = (y, x) => { const s = pairSlopes(y, x); return s.length ? median(s) : NaN; };

  // numpy.round: round half to even
  const roundHalfEven = v => {
    const f = Math.floor(v), d = v - f;
    if (d > 0.5) return f + 1;
    if (d < 0.5) return f;
    return f % 2 === 0 ? f : f + 1;
  };
  const tieTerm = a => {
    const c = new Map();
    a.forEach(v => c.set(v, (c.get(v) || 0) + 1));
    let t = 0;
    c.forEach(k => { if (k > 1) t += k * (k - 1) * (2 * k + 5); });
    return t;
  };

  // 95% confidence interval for Sen's slope, as scipy.stats.theilslopes.
  function sensCI(y, x) {
    const s = pairSlopes(y, x), n = y.length, nt = s.length;
    if (nt < 2) return [NaN, NaN];
    const z = -1.959963984540054;   // norm.ppf(0.025), as scipy
    const sig = Math.sqrt((n * (n - 1) * (2 * n + 5) - tieTerm(x) - tieTerm(y)) / 18);
    const ru = Math.min(roundHalfEven((nt - z * sig) / 2), nt - 1);
    const rl = Math.max(roundHalfEven((nt + z * sig) / 2) - 1, 0);
    return [s[rl], s[ru]];
  }

  // Mann-Kendall; with correct=true, Hamed-Rao variance inflation on the
  // ranks of the series detrended by Sen's slope over its index, floored
  // at 1 so the correction can never make the test less strict.
  function mannKendall(y, correct) {
    const n = y.length;
    let S = 0;
    for (let i = 0; i < n - 1; i++)
      for (let j = i + 1; j < n; j++) S += Math.sign(y[j] - y[i]);
    let v = (n * (n - 1) * (2 * n + 5) - tieTerm(y)) / 18;
    let ratio = 1;
    if (correct && n > 3) {
      const idx = y.map((_, i) => i);
      const sl = sensSlope(y, idx);
      const detr = y.map((val, i) => val - sl * i);
      // Ranks from 0, ties sharing their average rank (as tie_ranks in
      // script 18): detrending by Sen's slope always leaves two points
      // exactly level, and float noise must not decide their order.
      const order = idx.slice().sort((a, b) => detr[a] - detr[b] || a - b);
      const tol = 1e-9 * (Math.max(...detr) - Math.min(...detr));
      const r = new Array(n);
      for (let i = 0; i < n;) {
        let j = i;
        while (j + 1 < n && detr[order[j + 1]] - detr[order[j]] <= tol) j++;
        for (let k = i; k <= j; k++) r[order[k]] = (i + j) / 2;
        i = j + 1;
      }
      const rbar = (n - 1) / 2;
      const rvar = r.reduce((a, q) => a + (q - rbar) ** 2, 0) / n;
      let acc = 0;
      if (rvar > 0) {
        for (let lag = 1; lag < n; lag++) {
          let s = 0;
          for (let i = 0; i < n - lag; i++) s += (r[i] - rbar) * (r[i + lag] - rbar);
          const rho = s / ((n - lag) * rvar);
          if (Math.abs(rho) > 1.96 / Math.sqrt(n - lag))
            acc += (n - lag) * (n - lag - 1) * (n - lag - 2) * rho;
        }
      }
      ratio = Math.max(1 + (2 / (n * (n - 1) * (n - 2))) * acc, 1);
      v *= ratio;
    }
    const Z = S > 0 ? (S - 1) / Math.sqrt(v) : S < 0 ? (S + 1) / Math.sqrt(v) : 0;
    return { S, Z, p: twoSidedP(Z), ratio };
  }

  // Full analysis of a series of {year, value}; missing values dropped.
  function analyse(years, values) {
    const pts = years.map((yr, i) => [yr, values[i]]).filter(p => p[1] != null && isFinite(p[1]));
    const x = pts.map(p => p[0]), y = pts.map(p => p[1]);
    const n = y.length;
    if (n < 3) return { n };
    const slope = sensSlope(y, x);
    const [lo, hi] = sensCI(y, x);
    const intercept = median(y) - slope * median(x);
    const mk = mannKendall(y, true);
    return { n, x0: x[0], x1: x[n - 1], slope, lo, hi, intercept, p: mk.p, ratio: mk.ratio, S: mk.S };
  }

  return { erfc, sensSlope, sensCI, mannKendall, analyse };
})();
if (typeof module !== 'undefined') module.exports = TrendStats;
