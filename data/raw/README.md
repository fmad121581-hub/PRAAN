# data/raw — how to obtain it

These inputs are **not in the repository**. GADM's level-4 shapefile alone is
124 MB, over GitHub's 100 MB per-file limit, and the OCHA boundaries add
another 61 MB. Everything here is open-access; download it into these paths
and the pipeline runs unchanged.

| path | source | used by |
|---|---|---|
| `shapefiles/gadm41_BGD_4.*` | [GADM 4.1, Bangladesh, level 4](https://gadm.org/download_country.html) — choose Bangladesh, shapefile | 10, 12, 15 |
| `ocha/bgd_admin3.*` | [OCHA COD-AB Bangladesh](https://data.humdata.org/dataset/cod-ab-bgd) — admin level 3, DNCC/DSCC boundaries | 10, 15 |
| `bbs/PRAAN_BBS_Aman_FIXED_v2.xlsx` | **included in the repo** — Aman yield series compiled from BBS agricultural statistics | 02 |

Everything under `data/processed/` **is** committed, including
`grace_mascon_tws_raw.csv` and `dhaka_wards_dissolved.geojson`, so the
Phase 1 and Phase 2 results reproduce without downloading anything. Only the
Phase 3 scripts that rebuild ward geometry (10, 12, 15) need the shapefiles.

Google Earth Engine assets (GRACE, CHIRPS, MODIS, WorldPop, JRC GHSL, JRC
Global Surface Water) are pulled directly by script 01 and 11 and need an
authenticated Earth Engine account, not a local download.
