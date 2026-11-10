"""
PRAAN — the link-preview image (deploy/og.png)
Script: 25_og_card.py

WHY THIS EXISTS
    The image shown when the site's link is shared carried figures typed in
    by hand, and they went stale when the analysis was corrected. This
    script draws the card from the committed CSVs, so it cannot disagree
    with the site.

WHAT IT DOES
    Builds a 1200 x 630 HTML card (the site's palette and Archivo typeface,
    the Barind dry-season series with its Sen's slope line, the headline
    statistics from outputs/robust_trend_stats.csv) and screenshots it with
    headless Chrome or Edge.

RUN
    cd notebooks
    python 25_og_card.py
    Needs Chrome or Edge. Set the CHROME environment variable if it is not
    in a standard location.

OUTPUT
    deploy/og.png
"""
import os, shutil, subprocess, sys, tempfile
import numpy as np, pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + os.sep
DATA, OUT, DEPLOY = BASE + 'data/processed/', BASE + 'outputs/', BASE + 'deploy/'

CANDIDATES = [os.environ.get('CHROME'),
              r'C:\Program Files\Google\Chrome\Application\chrome.exe',
              r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
              r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
              '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
              shutil.which('google-chrome'), shutil.which('chromium'), shutil.which('chromium-browser')]
chrome = next((c for c in CANDIDATES if c and os.path.exists(c)), None)
if not chrome:
    sys.exit('Chrome or Edge not found; set the CHROME environment variable to its path.')

reg = pd.read_csv(DATA + 'grace_regional_tws.csv')
b = reg[reg.region == 'Barind Tract (NW)'].dropna(subset=['tws']).sort_values('year')
st = pd.read_csv(OUT + 'robust_trend_stats.csv').set_index('series').loc['Barind Tract (NW) 2002-2017']
slope, p = float(st.sens_slope), float(st.mk_p_autocorr_corrected)
drop = b[b.year.between(2002, 2004)].tws.mean() - b[b.year.between(2011, 2017)].tws.mean()
g = b[b.year <= 2017]
icpt = float(np.median(g.tws) - slope * np.median(g.year))

# chart geometry
W, H, x0, x1 = 470, 185, 2001.5, 2024.5
lo, hi = float(b.tws.min()) - 2, float(b.tws.max()) + 2
X = lambda v: (v - x0) / (x1 - x0) * W
Y = lambda v: (hi - v) / (hi - lo) * H
seg = lambda d: ' '.join(f"{'M' if i == 0 else 'L'}{X(r.year):.1f} {Y(r.tws):.1f}" for i, r in enumerate(d.itertuples()))
path = seg(b[b.year <= 2017]) + ' ' + seg(b[b.year >= 2019])
trend = f'M{X(2002):.1f} {Y(slope * 2002 + icpt):.1f} L{X(2017):.1f} {Y(slope * 2017 + icpt):.1f}'
font = 'file:///' + (DEPLOY + 'fonts/archivo-var.woff2').replace('\\', '/')
pfmt = f'{p:.2g}' if p >= 0.001 else '< 0.001'

html = f"""<!doctype html><meta charset="utf-8"><style>
@font-face{{font-family:Archivo;src:url('{font}') format('woff2');font-weight:100 900;font-stretch:62% 125%;}}
*{{margin:0;box-sizing:border-box}}
body{{width:1200px;height:630px;background:#0e2730;color:#eaf3f2;font-family:Archivo,sans-serif;padding:58px 68px;position:relative;overflow:hidden}}
.k{{color:#e2c26f;font-size:22px;font-weight:600}}
h1{{font-size:118px;font-weight:830;font-stretch:70%;letter-spacing:.01em;line-height:1;margin-top:18px}}
.t{{font-size:36px;font-weight:700;font-stretch:85%;line-height:1.15;margin-top:10px;max-width:600px}}
.s{{display:flex;gap:52px;margin-top:46px}}
.s b{{display:block;font-size:54px;font-weight:820;font-stretch:72%;line-height:1}}
.s span{{display:block;color:#9db7bb;font-size:19px;margin-top:8px;max-width:210px;line-height:1.3}}
.f{{position:absolute;left:68px;bottom:44px;color:#9db7bb;font-size:20px}}
.c{{position:absolute;right:62px;top:122px}}
.c p{{color:#9db7bb;font-size:16px;margin-top:8px}}
</style>
<div class="k">NASA Space Apps Challenge 2026 &middot; Be An Earth System Trend Detective!</div>
<h1>PRAAN</h1>
<div class="t">A trend detective for Bangladesh&rsquo;s water</div>
<div class="s">
  <div><b style="color:#f85149">&minus;{abs(slope):.2f} cm/yr</b><span>Barind dry-season water storage, 2002&ndash;2017</span></div>
  <div><b>p = {pfmt}</b><span>a significant decline (Mann-Kendall)</span></div>
  <div><b style="color:#62d0dd">{drop:.0f} cm</b><span>below its 2002&ndash;04 level by 2011&ndash;17</span></div>
</div>
<div class="c"><svg width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <rect x="{X(2017.5):.1f}" y="0" width="{X(2018.5) - X(2017.5):.1f}" height="{H}" fill="rgba(157,183,187,.09)"/>
  <path d="{path}" fill="none" stroke="#62d0dd" stroke-width="4" stroke-linejoin="round" stroke-linecap="round"/>
  <path d="{trend}" fill="none" stroke="#f85149" stroke-width="3.5" stroke-dasharray="9 7"/>
</svg><p>Barind Tract, NASA GRACE / GRACE-FO, January&ndash;May, 2002&ndash;2024</p></div>
<div class="f">Urban Alchemists &middot; BUET Urban &amp; Regional Planning &middot; praan-urban-alchemists.netlify.app</div>
"""
tmp = tempfile.mkdtemp(prefix='praan-og-')
page = os.path.join(tmp, 'card.html')
open(page, 'w', encoding='utf-8').write(html)
out = DEPLOY + 'og.png'
subprocess.run([chrome, '--headless=new', '--disable-gpu', '--no-first-run', '--hide-scrollbars',
                f'--user-data-dir={os.path.join(tmp, "profile")}', '--window-size=1200,630',
                '--force-device-scale-factor=1', '--allow-file-access-from-files',
                '--virtual-time-budget=3000', f'--screenshot={out}', 'file:///' + page.replace('\\', '/')],
               check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
shutil.rmtree(tmp, ignore_errors=True)
print(f'wrote {out}: slope {slope:.2f} cm/yr, p = {pfmt}, drop {drop:.0f} cm')
