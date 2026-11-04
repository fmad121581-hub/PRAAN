# References

Every dataset, paper, tool and asset PRAAN draws on.

## NASA data

- **GRACE / GRACE-FO JPL Mascon RL06.3Mv04** (`NASA/GRACE/MASS_GRIDS_V04/MASCON_CRI`,
  band `lwe_thickness`), via Google Earth Engine. Scripts 11, 16–18.
  Watkins, M. M., Wiese, D. N., Yuan, D.-N., Boening, C., & Landerer, F. W. (2015).
  Improved methods for observing Earth's time variable mass distribution with GRACE
  using spherical cap mascons. *Journal of Geophysical Research: Solid Earth*, 120, 2648–2671.
  Wiese, D. N., Landerer, F. W., & Watkins, M. M. (2016). Quantifying and reducing
  leakage errors in the JPL RL05M GRACE mascon solution. *Water Resources Research*, 52, 7490–7502.
- **GRACE Tellus land grids** (`NASA/GRACE/MASS_GRIDS_V04/LAND`, band
  `lwe_thickness_csr`), via Google Earth Engine. Script 01, cross-check only.
- **MODIS Terra Vegetation Indices, monthly, 1 km (MOD13A3 v061)**, via Google Earth Engine.
  Scripts 01, 03, 18. Didan, K. (2021). NASA EOSDIS Land Processes DAAC.
- **GLDAS-2.1 Noah, 3-hourly, 0.25°** (`NASA/GLDAS/V021/NOAH/G025/T3H`), via Google
  Earth Engine. Script 22 (written, not yet run). Beaudoing, H., & Rodell, M. (2020). NASA GES DISC.
  Rodell, M., et al. (2004). The Global Land Data Assimilation System. *Bulletin of
  the American Meteorological Society*, 85(3), 381–394.

## Partner and third-party data

- **CHIRPS v2.0 pentad rainfall** (`UCSB-CHG/CHIRPS/PENTAD`). Funk, C., et al. (2015).
  The climate hazards infrared precipitation with stations — a new environmental
  record for monitoring extremes. *Scientific Data*, 2, 150066.
- **WorldPop 100 m population, 2000–2020** (`WorldPop/GP/100m/pop`). WorldPop,
  University of Southampton. doi:10.5258/SOTON/WP00645
- **JRC GHSL built-up surface P2023A** (`JRC/GHSL/P2023A/GHS_BUILT_S`). Pesaresi, M.,
  & Politis, P. (2023). European Commission, Joint Research Centre.
- **JRC Global Surface Water 1.4** (`JRC/GSW1_4/MonthlyHistory`). Pekel, J.-F.,
  Cottam, A., Gorelick, N., & Belward, A. S. (2016). High-resolution mapping of
  global surface water and its long-term changes. *Nature*, 540, 418–422.
- **Bangladesh Bureau of Statistics.** Population and Housing Census 2022, Urban
  Area Report (ward indicators); Population Census 2011; Population Monograph
  Vol. 06 (2015), Table 3.8 (migration destination shares).
- **GADM 4.1** administrative boundaries, level 4 (wards).
- **OCHA COD-AB Bangladesh (2025)** — DNCC and DSCC boundaries.

## Literature

- Aziz, M. A., Majumder, M. A. K., Kabir, M. S., Hossain, M. I., Rahman, N. M. F.,
  Rahman, F., & Hosen, S. (2015). Groundwater depletion with expansion of irrigation
  in Barind Tract: A case study of Rajshahi District of Bangladesh. *International
  Journal of Geology, Agriculture and Environmental Sciences*, 3(1).
- Khalily, M. A. B., Khandker, S. R., & Samad, H. A. (2006/07). *Seasonal Migration
  and Coping Strategies: The Monga Context in Bangladesh.* World Bank / BRAC.

## Statistical methods

- Mann, H. B. (1945). Nonparametric tests against trend. *Econometrica*, 13, 245–259.
- Kendall, M. G. (1975). *Rank Correlation Methods.* Griffin, London.
- Sen, P. K. (1968). Estimates of the regression coefficient based on Kendall's tau.
  *Journal of the American Statistical Association*, 63, 1379–1389.
- Hamed, K. H., & Rao, A. R. (1998). A modified Mann-Kendall trend test for
  autocorrelated data. *Journal of Hydrology*, 204, 182–196.

## Software and assets

- Google Earth Engine. Gorelick, N., et al. (2017). Google Earth Engine:
  Planetary-scale geospatial analysis for everyone. *Remote Sensing of Environment*, 202, 18–27.
- Python: NumPy, pandas, SciPy, Matplotlib, seaborn, GeoPandas, scikit-learn,
  statsmodels, pdfplumber, earthengine-api (see `requirements.txt`).
- Leaflet 1.9.4 (BSD-2-Clause), bundled in `deploy/vendor/leaflet/`.
- Archivo typeface (SIL Open Font License), bundled in `deploy/fonts/`.
- Hosting: Netlify.

AI tools used during development are listed in `docs/AI_USE.md`.
