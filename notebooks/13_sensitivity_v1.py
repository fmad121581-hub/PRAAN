"""
PRAAN — ASI Weight Sensitivity Analysis  [CORRECTED]
Script: 13_sensitivity_analysis.py

WHAT WAS WRONG IN THE PREVIOUS VERSION
 1. IT TESTED THE WRONG FORMULA. It varied the 3-indicator weights
    (pop 0.40 / builtup 0.35 / flood 0.25). Every ranked city-corporation
    ward with BBS data uses the 4-indicator ASI_updated
    (pop 0.35 / builtup 0.25 / flood 0.20 / household size 0.20), so the
    sensitivity test did not perturb the numbers that produce the ranking.
 2. IT RAN ON DUPLICATED DATA (184 rows for 138 wards), so percentile
    ranks and the top-13 list were distorted.
 3. ITS OUTPUT WAS REPORTED BACKWARDS. sensitivity_summary.txt said
    "Top-13 unchanged: 1/25 (4.0%) ... VERDICT: Top 13 changed in 24
    combinations", while the README and website said the top 9-12 wards
    were "consistent" and "robust". The overlap COUNT was 9-12 of 13;
    that is not the same as the top 9-12 wards being stable.

WHAT THIS VERSION DOES
    Perturbs the 4-indicator weights by +/-10pp in 5pp steps, renormalises
    to sum to 1, rebuilds ASI -> allocation -> rank-product Crisis Index on
    the deduplicated, fully-observed ward set, and reports rank stability
    at several depths so the claim written up is the claim measured.

OUTPUT
    outputs/sensitivity_results.csv
    outputs/sensitivity_summary.txt
"""
import pandas as pd, numpy as np, itertools, os

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
OUT = BASE + "outputs/"
PRIMARY = OUT + "crisis_index_primary_v1.csv"   # from 10_supply_demand.py (fixed)
SCORES = OUT + "phase3_ward_scores_v3_deduped.csv"   # written by script 10

MOB_CENTRAL = 2_580_774
ARR = int(MOB_CENTRAL * 0.660 * 0.450)
W4 = {'pop_norm': .35, 'builtup_norm': .25, 'flood_norm': .20, 'hh_size_norm': .20}
W3 = {'pop_norm': .40, 'builtup_norm': .35, 'flood_norm': .25}

# Use the deduplicated frame written by 10_supply_demand.py so that
# hh_size_norm has the identical normalisation base. Do NOT re-derive it
# from phase3_ward_scores_v2.csv: a naive drop_duplicates('GID_4') there
# picks the WRONG BBS record for 29 of the 61 wards.
prim = pd.read_csv(PRIMARY)
scores = pd.read_csv(SCORES)
assert scores.GID_4.is_unique, 'run 10_supply_demand.py first'
c = scores[scores.GID_4.isin(prim.GID_4)].copy().reset_index(drop=True)
assert len(c) == len(prim), f'expected {len(prim)} wards, matched {len(c)}' 
print(f'Sensitivity set: {len(c)} fully-observed wards')


def build(df, w4):
    d = df.copy()
    d['ASI'] = sum(d[k] * v for k, v in w4.items())
    wt = d.pop_total * (1 - d.ASI)
    d['arrivals'] = (wt / wt.sum() * ARR).astype(int)
    rp = d.ASI.rank(pct=True) * d.arrivals.rank(pct=True)
    d['ci'] = (rp - rp.min()) / (rp.max() - rp.min())
    return d.sort_values('ci', ascending=False)


base = build(c, W4)
b13 = list(base.head(13).GID_4); b5 = set(b13[:5])
brank = {g: i for i, g in enumerate(base.GID_4)}

rows = []
for d_ in itertools.product([-.10, -.05, 0, .05, .10], repeat=4):
    ww = {k: W4[k] + dv for k, dv in zip(W4, d_)}
    if any(v <= 0 for v in ww.values()):
        continue
    t = sum(ww.values()); ww = {k: v / t for k, v in ww.items()}
    r = build(c, ww)
    t13 = list(r.head(13).GID_4)
    rows.append({**{f'w_{k.replace("_norm","")}': round(v, 3) for k, v in ww.items()},
                 'overlap_top13': len(set(t13) & set(b13)),
                 'exact_top13': set(t13) == set(b13),
                 'overlap_top5': len(set(t13[:5]) & b5),
                 'top1_same': t13[0] == b13[0],
                 'max_shift_top13': max(abs(brank[g] - list(r.GID_4).index(g))
                                        for g in b13)})

s = pd.DataFrame(rows); n = len(s)
os.makedirs(OUT, exist_ok=True)
s.to_csv(OUT + 'sensitivity_results_v1.csv', index=False)

txt = f"""PRAAN — ASI Weight Sensitivity Analysis
{'=' * 64}

SETUP
  Ward set     : {len(c)} fully-observed city-corporation wards
                 (deduplicated; wards without a BBS match excluded)
  Formula      : 4-indicator ASI, the one that generates the ranking
  Base weights : pop {W4['pop_norm']} / builtup {W4['builtup_norm']} / """ \
f"""flood {W4['flood_norm']} / household size {W4['hh_size_norm']}
  Variation    : +/-10pp per indicator, 5pp steps, renormalised to sum 1
  Combinations : {n}

RESULTS
  Highest-ranked ward unchanged   : {int(s.top1_same.sum())}/{n} ({s.top1_same.mean()*100:.1f}%)
  Mean top-5 overlap              : {s.overlap_top5.mean():.1f}/5
  Mean top-13 overlap             : {s.overlap_top13.mean():.1f}/13 (min {s.overlap_top13.min()})
  Exact top-13 set reproduced     : {int(s.exact_top13.sum())}/{n} ({s.exact_top13.mean()*100:.1f}%)
  Median worst-case rank shift
  of a top-13 ward                : {s.max_shift_top13.median():.0f} places

HOW TO STATE THIS
  Accurate:
    "The highest-concern wards are robust to weighting. The top-ranked ward
     is unchanged in {s.top1_same.mean()*100:.0f}% of {n} weight combinations (+/-10pp per
     indicator) and the top five overlap by {s.overlap_top5.mean():.1f} of 5 on average.
     Membership at the boundary of the top 13 is weighting-dependent
     (exact set reproduced in {s.exact_top13.mean()*100:.0f}% of combinations, mean overlap
     {s.overlap_top13.mean():.1f} of 13) and should be read as indicative."

  Do NOT write "the top 9-12 wards are consistent". Overlap COUNT is not
  rank stability, and the previous summary file said the opposite of the
  previous website text.
"""
open(OUT + 'sensitivity_summary_v1.txt', 'w').write(txt)
print(txt)
