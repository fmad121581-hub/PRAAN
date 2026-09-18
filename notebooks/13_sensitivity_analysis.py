"""
PRAAN — Sensitivity Analysis: ASI Weight Robustness
Script: 13_sensitivity_analysis.py
"""

import pandas as pd
import numpy as np
import os

BASE = r'C:/Users/user/OneDrive/Nasa_2026/PRAAN'

scores = pd.read_csv(f'{BASE}/outputs/phase3_ward_scores_v2.csv')
gap    = pd.read_csv(f'{BASE}/outputs/phase3_supply_demand_gap.csv')

scores_dedup = scores.sort_values('ASI_updated', ascending=False)\
                     .drop_duplicates(subset='GID_4', keep='first').copy()
gap_dedup    = gap.sort_values('crisis_index', ascending=False)\
                  .drop_duplicates(subset='GID_4', keep='first').copy()

df = scores_dedup.merge(
    gap_dedup[['GID_4','arrivals_low','arrivals_central','arrivals_high','pop_total']],
    on='GID_4', how='left'
)
print(f"Wards loaded: {len(df)}, with arrivals: {df['arrivals_central'].notna().sum()}")

W_BASE = {'pop': 0.40, 'builtup': 0.35, 'flood': 0.25}

def compute_asi(df, w):
    return (
        df['pop_norm']     * w['pop'] +
        df['builtup_norm'] * w['builtup'] +
        df['flood_norm']   * w['flood']
    )

def compute_crisis(df, asi_series):
    tmp = df.copy()
    tmp['ASI_test'] = asi_series
    mask = tmp['arrivals_central'].notna()
    tmp.loc[mask, 'asi_rank']     = tmp.loc[mask, 'ASI_test'].rank(pct=True)
    tmp.loc[mask, 'arrival_rank'] = tmp.loc[mask, 'arrivals_central'].rank(pct=True)
    tmp.loc[mask, 'ci_raw']       = tmp.loc[mask, 'asi_rank'] * tmp.loc[mask, 'arrival_rank']
    ci_min = tmp.loc[mask, 'ci_raw'].min()
    ci_max = tmp.loc[mask, 'ci_raw'].max()
    tmp.loc[mask, 'crisis_index_test'] = (tmp.loc[mask, 'ci_raw'] - ci_min) / (ci_max - ci_min)
    return tmp['crisis_index_test']

base_asi    = compute_asi(df, W_BASE)
base_crisis = compute_crisis(df, base_asi)
base_top13  = set(df.assign(ci=base_crisis).nlargest(13, 'ci')['GID_4'].values)
print(f"Base top 13 identified: {len(base_top13)} wards")

STEP = 0.05
weight_combos = []
for dp in np.arange(-0.10, 0.11, STEP):
    for db in np.arange(-0.10, 0.11, STEP):
        wp = round(W_BASE['pop']     + dp, 4)
        wb = round(W_BASE['builtup'] + db, 4)
        wf = round(1.0 - wp - wb,          4)
        if wp > 0 and wb > 0 and wf > 0 and abs(wp + wb + wf - 1.0) < 0.001:
            weight_combos.append({'pop': wp, 'builtup': wb, 'flood': wf})

print(f"Weight combinations to test: {len(weight_combos)}")

results = []
for w in weight_combos:
    asi    = compute_asi(df, w)
    crisis = compute_crisis(df, asi)
    top13  = set(df.assign(ci=crisis).nlargest(13, 'ci')['GID_4'].values)
    match  = (top13 == base_top13)
    results.append({
        'w_pop'        : w['pop'],
        'w_builtup'    : w['builtup'],
        'w_flood'      : w['flood'],
        'top13_match'  : match,
        'overlap_count': len(top13 & base_top13),
        'new_entries'  : str(top13 - base_top13) if top13 != base_top13 else '',
        'dropped'      : str(base_top13 - top13) if top13 != base_top13 else '',
    })

results_df = pd.DataFrame(results)
n_combos   = len(results_df)
n_match    = results_df['top13_match'].sum()
n_mismatch = n_combos - n_match
pct_match  = 100 * n_match / n_combos

summary = f"""
PRAAN — ASI Weight Sensitivity Analysis
========================================
Base weights: pop={W_BASE['pop']} / builtup={W_BASE['builtup']} / flood={W_BASE['flood']}
Variation: ±10pp per indicator, 5pp steps
Combinations tested: {n_combos}

RESULTS:
  Top-13 unchanged : {n_match} / {n_combos}  ({pct_match:.1f}%)
  Top-13 changed   : {n_mismatch} / {n_combos}

VERDICT: {'Top 13 STABLE across all weight combinations. Website claim VERIFIED.' if n_mismatch == 0 else f'Top 13 changed in {n_mismatch} combinations — review sensitivity_results.csv'}
"""

if n_mismatch > 0:
    mismatches = results_df[~results_df['top13_match']]
    summary += "\nCombinations where top 13 changed:\n"
    summary += mismatches[['w_pop','w_builtup','w_flood','overlap_count','new_entries','dropped']].to_string()

print(summary)

out = f'{BASE}/outputs'
os.makedirs(out, exist_ok=True)
results_df.to_csv(f'{out}/sensitivity_results.csv', index=False)
with open(f'{out}/sensitivity_summary.txt', 'w') as f:
    f.write(summary)

print(f"✓ sensitivity_results.csv → {out}")
print(f"✓ sensitivity_summary.txt → {out}")
