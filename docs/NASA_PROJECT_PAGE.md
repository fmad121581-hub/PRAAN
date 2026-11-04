# NASA project page — text for each field

Copy each block into the matching field on spaceappschallenge.org.
Replace the two video links once the videos are uploaded, then test every
link in a private browser window before pressing Submit.

**Challenge:** Be An Earth System Trend Detective!
**Team:** Urban Alchemists, BUET Department of Urban & Regional Planning, Dhaka
**Members and roles:** Fahim Ahmed (technical lead) · Arshil Azim (validation
and domain research) · Nawar Noor Nusaiba (video) · Mahin Haider (pitch and
demo) · Md. Fardeen Al Mahin (design and submission)

---

## High-Level Summary

PRAAN is a trend detective for Bangladesh's groundwater. Using NASA GRACE and
GRACE-FO, we measured dry-season water storage from 2002 to 2024 in three
regions of Bangladesh with the same extraction and the same trend test. The
Barind Tract in the northwest is falling by 0.90 cm a year (Mann-Kendall
p = 0.010), the coastal south by 0.56 cm a year (p = 0.0079), while the haor
basin in the northeast shows no significant trend and tilts upward over the
full record. Over the same Barind districts and season, MODIS vegetation is
rising significantly and CHIRPS rainfall shows no significant trend: the land
is getting greener while the water under it runs down, which points to
irrigation pumping rather than drought.

We then follow that trend to where its consequences may land. Using census
data, we score all 75 matchable Dhaka city-corporation wards on how much
strain they could absorb from rural arrivals, and identify 11 high-concern
wards, with Kafrul Ward 14 first. Every figure is reproducible from the
public repository, and the limits of the method (GRACE's ~300 km resolution,
scenario-based migration numbers) are stated on the site.

- 240-second video: [ADD YOUTUBE LINK]
- Live site: https://praan-urban-alchemists.netlify.app
- GitHub: https://github.com/fmad121581-hub/PRAAN

## Project Demo

30-second video: [ADD YOUTUBE OR VIMEO LINK]

## Final Project

https://github.com/fmad121581-hub/PRAAN — code, data, outputs and full
documentation. Start with `README.md`; `notebooks/PIPELINE.md` gives the run
order, and `python notebooks/18_robust_trends.py` reproduces the published
trend statistics offline from committed data.

## Project Details

### The why, the what, the how

The challenge asks what is changing, where, by how much, and whether the
change is significant. We answered all four for terrestrial water storage
over Bangladesh.

*What and where.* Dry-season (January to May) water-storage anomaly from the
JPL GRACE/GRACE-FO mascon product, extracted identically over the Barind
Tract, the coastal south and the haor basin. A fourth region around Dhaka
returned the same series as the haor basin (correlation 1.000), so we report
three independent regions, which is what GRACE's resolution supports.

*How much and how significant.* Sen's slope and the Mann-Kendall test, with
a Hamed-Rao check for serial correlation that is only ever allowed to make a
p-value larger. Barind: −0.90 cm/yr, p = 0.010 (2002–2017) and −0.57 cm/yr,
p = 0.018 (2002–2024). Coastal south: −0.56 cm/yr, p = 0.0079. Haor basin:
not significant in either window.

*Why.* MODIS NDVI over the same districts and season rises significantly,
and CHIRPS rainfall shows no significant trend over 39 years. Together these
point to irrigation extraction, consistent with Bangladesh Water Development
Board tube-well records (Aziz et al. 2015). GRACE measures total water
storage, not groundwater alone; a GLDAS-2.1 step that subtracts soil
moisture, snow and canopy water is written (script 22) but not yet run, so
we make no groundwater-only claim.

*So what.* Using BBS census data, a migration scenario and an Absorption
Stress Index built from WorldPop density, JRC built-up surface, JRC flood
history and household crowding, we rank 75 Dhaka wards. 11 are high concern.
We tested whether the stress index predicts where people actually moved; it
does not, and the site says so.

### Community involvement

PRAAN is built for Dhaka's two city corporations, urban planners and the
NGOs that work with low-income arrivals. A trend that is visible from space
years before it shows up in a city gives planners lead time: the ward list
says where services, drainage and housing pressure are most likely to build
first. The site works in a browser with no installation, on a phone, and
offline, and the key results link to the CSVs behind them. We want the method to
be reused for other Bangladeshi cities, and the code is open for that.

Highlights: identical trend tests across three regions; a three-satellite
explanation of cause; an interactive ward map; and a full public log of the
errors we found in our own work and how we fixed them (`CORRECTIONS.md`).

### Tools and technologies

Google Earth Engine for data extraction; Python (NumPy, pandas, SciPy,
statsmodels, GeoPandas, scikit-learn, Matplotlib, seaborn) for analysis; a
single-file HTML site with Leaflet 1.9.4 and the Archivo typeface, hosted on
Netlify; Git and GitHub. Full credits in `docs/REFERENCES.md`.

## Use of AI

PRAAN itself contains no AI: every number on the site comes from
deterministic Python scripts reading committed data. During development we
used Claude (Anthropic) extensively to draft and debug analysis scripts,
review our statistical methods, build the website and edit documentation;
commits it helped write are marked "Co-Authored-By: Claude" in the git
history. We used Perplexity lightly to find literature and data sources. The
AI worked only on open datasets and our own derived files. The team chose
the problem, data and methods, ran and checked every script, and decided
what to claim. Details and example prompts: `docs/AI_USE.md`.

## NASA data sources used

- GRACE / GRACE-FO JPL Mascon RL06.3Mv04 — the core signal: dry-season water
  storage trends in three regions, 2002–2024.
- GRACE Tellus land grids — cross-check of the mascon result.
- MODIS Terra NDVI (MOD13A3 v061) — vegetation trend over the same districts
  and season, used to explain the decline.
- GLDAS-2.1 Noah — the next step: subtracting soil moisture, snow and
  canopy water from GRACE to separate groundwater. The script (22) is
  written but not yet run, so no result from it is claimed.

Other sources on top of NASA data: CHIRPS rainfall, WorldPop, JRC GHSL, JRC
Global Surface Water, BBS census 2011 and 2022, GADM and OCHA boundaries.

## References

See `docs/REFERENCES.md` in the repository for the full list with citations.
