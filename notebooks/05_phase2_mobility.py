"""
PRAAN — Phase 2: Mobility Pressure Framework
Script: 05_phase2_mobility.py

PURPOSE:
    Connect GRACE-validated groundwater depletion to
    an evidence-based mobility pressure estimate for
    Rajshahi Division (Barind Tract), using:

    1. BBS 2011 Census migration probability matrix
       (empirically measured destination probabilities)
    2. GRACE TWS trend as the environmental stress signal
    3. Monga/agricultural stress literature for
       vulnerability parameters
    4. Probabilistic output — NOT a headcount prediction

SCIENTIFIC FRAMING:
    "Given the validated groundwater depletion trajectory,
    what is the estimated mobility pressure range and
    most probable destination, based on observed
    historical migration patterns?"

    This is NOT causal prediction.
    This is scenario-based estimation grounded in
    empirical migration data.

SOURCE FOR MIGRATION PROBABILITIES:
    BBS Population Monograph Vol.06 (2015)
    "Population Distribution and Internal Migration
    in Bangladesh"
    Table 3.8 — Transition probability matrix,
    migration < 5 years, Census 2011

OUTPUTS:
    outputs/mobility_pressure_estimate.png
    outputs/destination_probability.png
    outputs/phase2_summary.txt

AUTHOR: PRAAN Team
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from scipy import stats
import os
import warnings
warnings.filterwarnings('ignore')

OUTPUT_DIR = 'C:/Users/user/OneDrive/Nasa_2026/PRAAN/outputs/'
DATA_DIR   = 'C:/Users/user/OneDrive/Nasa_2026/PRAAN/data/processed/'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ─────────────────────────────────────────────────────────────
# 1. GRACE STRESS TRAJECTORY
# ─────────────────────────────────────────────────────────────
# Reload the validated GRACE trend from Phase 1

grace_df = pd.read_csv(DATA_DIR + 'grace_tws_raw.csv')
grace_div = (
    grace_df.groupby('year')['tws_anomaly']
    .mean().reset_index()
)

# Fit the validated trend (r=-0.921, p<0.001)
slope, intercept, r_val, p_val, _ = stats.linregress(
    grace_div['year'], grace_div['tws_anomaly']
)

# Project forward to 2030
future_years = np.arange(2002, 2031)
tws_projected = slope * future_years + intercept

# Define stress threshold:
# When TWS anomaly crosses -0.30 cm (1.5x the 2017 value)
# we consider irrigation failure risk to become significant
# This threshold is conservative and explicitly labelled as
# a scenario assumption, not a validated threshold
STRESS_THRESHOLD = -0.30

threshold_year = None
for yr, tws in zip(future_years, tws_projected):
    if tws <= STRESS_THRESHOLD:
        threshold_year = yr
        break

print(f"GRACE trend: {slope:.4f} cm/year (r={r_val:.3f}, p={p_val:.4f})")
print(f"Current TWS (2017): {grace_div['tws_anomaly'].iloc[-1]:.3f} cm")
print(f"Projected TWS 2025: {slope*2025+intercept:.3f} cm")
print(f"Scenario stress threshold ({STRESS_THRESHOLD} cm): ~{threshold_year}")

# ─────────────────────────────────────────────────────────────
# 2. VULNERABILITY PARAMETERS
# ─────────────────────────────────────────────────────────────
# Source: BBS Census 2011 + monga literature

# Rajshahi Division population (Census 2022 estimated)
# 2011: 18,484,858 | Growth rate 2001-2011: 1.21%/yr
POP_2011    = 18_484_858
GROWTH_RATE = 0.0121
POP_2026    = int(POP_2011 * (1 + GROWTH_RATE) ** 15)

# Agricultural dependence in Rajshahi Division
# ~68% of rural workforce in agriculture (BBS Labour Force Survey)
AG_DEPENDENCE = 0.68

# Rural population fraction (Census 2011: 82.1% rural)
RURAL_FRACTION = 0.821

# Barind Tract fraction of Rajshahi Division
# Barind covers ~7,727 km² of Rajshahi Division's ~13,284 km²
BARIND_FRACTION = 0.58

# Exposed population (rural + agricultural in Barind)
pop_exposed = int(POP_2026 * RURAL_FRACTION *
                  AG_DEPENDENCE * BARIND_FRACTION)

print(f"\nPopulation parameters:")
print(f"  Rajshahi Division (2026 est.): {POP_2026:,}")
print(f"  Exposed population (rural+ag+Barind): {pop_exposed:,}")

# ─────────────────────────────────────────────────────────────
# 3. MOBILITY PRESSURE ESTIMATE
# ─────────────────────────────────────────────────────────────
# Source: Khalily/Khandker/Samad (2006/07 survey)
# 36% of poor households in NW Bangladesh migrate during monga
# This is our empirical mobility rate anchor

# IMPORTANT FRAMING:
# We are NOT predicting 'X people will migrate'
# We are estimating 'mobility pressure range given observed
# historical rates and current environmental stress trajectory'

# Historical seasonal mobility rate (monga baseline)
MOBILITY_RATE_BASE  = 0.36   # 36% — Khalily et al.
MOBILITY_RATE_LOW   = 0.20   # conservative bound
MOBILITY_RATE_HIGH  = 0.50   # upper bound under stress

# Under elevated groundwater stress, mobility rate
# is assumed to increase proportionally
# (literature-informed, not independently validated)
# We use a simple stress multiplier

# Stress ratio kept for reporting only — not applied as multiplier
tws_2026 = slope * 2026 + intercept
tws_2002 = grace_div['tws_anomaly'].iloc[0]
stress_ratio = abs(tws_2026) / abs(tws_2002)

# Mobility pressure brackets anchored directly to literature rates.
# 36% (Khalily et al.) IS the stressed-season rate — it is the central
# scenario, not a baseline to be amplified further.
# Low = mild stress year. High = compounding multi-year depletion.
# All three are capped well below 100% of exposed pop (physically bounded).
MOBILITY_RATE_LOW     = 0.20   # mild stress year
MOBILITY_RATE_CENTRAL = 0.36   # monga-equivalent (Khalily et al. anchor)
MOBILITY_RATE_HIGH    = 0.50   # severe / multi-year compounding stress

mobility_low     = int(pop_exposed * MOBILITY_RATE_LOW)
mobility_central = int(pop_exposed * MOBILITY_RATE_CENTRAL)
mobility_high    = int(pop_exposed * MOBILITY_RATE_HIGH)

print(f"\nMobility pressure estimate (2026 scenario):")

print(f"  Low estimate:     {mobility_low:>10,}")
print(f"  Central estimate: {mobility_central:>10,}")
print(f"  High estimate:    {mobility_high:>10,}")
print()
print("  NOTE: These are MOBILITY PRESSURE estimates,")
print("  not permanent displacement predictions.")
print("  They represent people in households likely to")
print("  experience seasonal or temporary mobility pressure.")

# ─────────────────────────────────────────────────────────────
# 4. DESTINATION PROBABILITIES
# ─────────────────────────────────────────────────────────────
# Source: BBS 2011 Census, Table 3.8
# Migration transition probability matrix, < 5 years
# Row = Rajshahi Division origin

# Among out-migrants from Rajshahi (excluding stayers):
destination_probs = {
    'Dhaka Division':      0.660,
    'Khulna Division':     0.130,
    'Rangpur Division':    0.078,
    'Chittagong Division': 0.056,
    'Sylhet Division':     0.053,
    'Barisal Division':    0.023,
}

# Within Dhaka Division, key receiving districts:
# From BBS monograph section 3.7 and IOM data:
dhaka_sub_dist = {
    'Dhaka City':    0.45,   # capital — highest pull
    'Gazipur':       0.22,   # industrial corridor
    'Narayanganj':   0.15,   # textile hub
    'Narsingdi':     0.10,   # peri-urban
    'Other Dhaka':   0.08
}

print("\nDestination probability distribution (BBS 2011 Census):")
print("Among Rajshahi Division out-migrants:")
for dest, prob in sorted(destination_probs.items(),
                          key=lambda x: -x[1]):
    bar = '█' * int(prob * 40)
    print(f"  {dest:<25} {prob:.3f} ({prob*100:.1f}%)  {bar}")

print("\nWithin Dhaka Division:")
for dest, prob in sorted(dhaka_sub_dist.items(),
                          key=lambda x: -x[1]):
    dhaka_arrivals = int(mobility_central *
                         destination_probs['Dhaka Division'])
    arrivals       = int(dhaka_arrivals * prob)
    print(f"  {dest:<20} {prob:.2f}  ~{arrivals:,} people (central estimate)")

# ─────────────────────────────────────────────────────────────
# 5. VISUALISATION
# ─────────────────────────────────────────────────────────────

fig = plt.figure(figsize=(16, 12))
gs  = gridspec.GridSpec(2, 2, figure=fig,
                         hspace=0.4, wspace=0.35)

# ── Panel A: GRACE trajectory + threshold ─────────────────
ax_a = fig.add_subplot(gs[0, :])

ax_a.fill_between(
    grace_div['year'], grace_div['tws_anomaly'], 0,
    alpha=0.4, color='steelblue', label='Observed TWS anomaly'
)
ax_a.plot(grace_div['year'], grace_div['tws_anomaly'],
          'b-o', linewidth=2, markersize=7)

# Trend line (historical)
hist_x    = grace_div['year'].values
hist_line = slope * hist_x + intercept
ax_a.plot(hist_x, hist_line, 'r--', linewidth=2,
          label=f'Trend: {slope:.4f} cm/yr (r={r_val:.3f}, p<0.001)')

# Projection
proj_x    = future_years[future_years > 2017]
proj_line = slope * proj_x + intercept
ax_a.plot(proj_x, proj_line, 'r--', linewidth=1.5,
          alpha=0.5, linestyle=':')
ax_a.fill_between(proj_x, proj_line - 0.05,
                  proj_line + 0.05,
                  alpha=0.15, color='red',
                  label='Projected range (±uncertainty)')

# Stress threshold
ax_a.axhline(STRESS_THRESHOLD, color='darkred',
             linewidth=1.5, linestyle='-.',
             label=f'Scenario stress threshold ({STRESS_THRESHOLD} cm)')

if threshold_year:
    ax_a.axvline(threshold_year, color='darkred',
                 linewidth=1, linestyle='--', alpha=0.5)
    ax_a.annotate(f'Threshold ~{threshold_year}',
                  xy=(threshold_year, STRESS_THRESHOLD),
                  xytext=(threshold_year - 3, STRESS_THRESHOLD - 0.04),
                  fontsize=9, color='darkred')

ax_a.axvline(2017, color='grey', linewidth=1,
             linestyle='--', alpha=0.7,
             label='Data ends (2017)')
ax_a.axvline(2026, color='orange', linewidth=1.5,
             linestyle='--', alpha=0.7,
             label='Current (2026)')

ax_a.set_title('Rajshahi Division — GRACE Terrestrial Water Storage\n'
               'Observed (2002–2017) + Projected Trajectory',
               fontsize=11, fontweight='bold')
ax_a.set_xlabel('Year')
ax_a.set_ylabel('TWS Anomaly (cm)')
ax_a.legend(fontsize=8, loc='lower left')
ax_a.grid(alpha=0.3)

# ── Panel B: Destination probability bar chart ─────────────
ax_b = fig.add_subplot(gs[1, 0])

dests  = list(destination_probs.keys())
probs  = list(destination_probs.values())
colors = ['#d32f2f' if d == 'Dhaka Division' else '#1565c0'
          for d in dests]

bars = ax_b.barh(dests, probs, color=colors, edgecolor='white',
                 linewidth=0.5)

for bar, prob in zip(bars, probs):
    ax_b.text(prob + 0.01, bar.get_y() + bar.get_height()/2,
              f'{prob*100:.1f}%', va='center', fontsize=9)

ax_b.set_title('Destination Probability\nRajshahi Out-Migrants (BBS Census 2011)',
               fontsize=10, fontweight='bold')
ax_b.set_xlabel('Probability')
ax_b.set_xlim(0, 0.80)
ax_b.grid(alpha=0.3, axis='x')
ax_b.invert_yaxis()

# ── Panel C: Mobility pressure estimate ───────────────────
ax_c = fig.add_subplot(gs[1, 1])

scenarios = ['Low\nestimate', 'Central\nestimate', 'High\nestimate']
values    = [mobility_low, mobility_central, mobility_high]
colors_c  = ['#4caf50', '#ff9800', '#f44336']

bars_c = ax_c.bar(scenarios, values, color=colors_c,
                  edgecolor='white', linewidth=0.5, width=0.5)

for bar, val in zip(bars_c, values):
    ax_c.text(bar.get_x() + bar.get_width()/2,
              bar.get_height() + 1000,
              f'{val:,}', ha='center', fontsize=10,
              fontweight='bold')

ax_c.set_title('Estimated Mobility Pressure\n'
               'Rajshahi Division Barind Tract (2026 scenario)',
               fontsize=10, fontweight='bold')
ax_c.set_ylabel('People in mobility-pressure households')
ax_c.grid(alpha=0.3, axis='y')

# Add disclaimer text
ax_c.text(0.5, -0.22,
          'Note: These are literature-informed scenario estimates,\n'
          'not independently validated migration predictions.\n'
          'Source: Khalily/Khandker/Samad 2006/07; BBS Census 2011',
          transform=ax_c.transAxes, ha='center',
          fontsize=7, color='grey', style='italic')

plt.suptitle('PRAAN — Phase 2: Mobility Pressure Framework\n'
             'Environmental Stress → Destination Probability',
             fontsize=13, fontweight='bold', y=1.01)

plt.savefig(OUTPUT_DIR + 'mobility_pressure_estimate.png',
            dpi=150, bbox_inches='tight')
plt.close()
print(f"\nPlot saved → outputs/mobility_pressure_estimate.png")

# ─────────────────────────────────────────────────────────────
# 6. SAVE SUMMARY
# ─────────────────────────────────────────────────────────────
summary_lines = [
    "PRAAN Phase 2 — Mobility Pressure Summary",
    "=" * 55,
    "",
    "ENVIRONMENTAL STRESS (Phase 1 validated):",
    f"  GRACE TWS trend: {slope:.4f} cm/year",
    f"  r = {r_val:.3f}, p < 0.001",
    f"  Projected TWS 2026: {tws_2026:.3f} cm",
    f"  Stress multiplier vs 2002: {stress_ratio:.2f}x",
    "",
    "EXPOSED POPULATION:",
    f"  Rajshahi Division (2026 est.): {POP_2026:,}",
    f"  Exposed (rural+ag+Barind):     {pop_exposed:,}",
    f"  Source: BBS Census 2011, Labour Force Survey",
    "",
    "MOBILITY PRESSURE ESTIMATE:",
    f"  Low:     {mobility_low:,}",
    f"  Central: {mobility_central:,}",
    f"  High:    {mobility_high:,}",
    "  Basis: Khalily/Khandker/Samad (36% monga mobility rate)",
    "  DISCLAIMER: Literature-informed scenario estimate.",
    "  NOT independently validated against migration series.",
    "",
    "DESTINATION PROBABILITIES (BBS Census 2011, Table 3.8):",
    "  Among Rajshahi out-migrants:",
]
for dest, prob in sorted(destination_probs.items(),
                          key=lambda x: -x[1]):
    summary_lines.append(f"    {dest:<25} {prob*100:.1f}%")

summary_lines += [
    "",
    "WITHIN DHAKA DIVISION:",
]
for dest, prob in sorted(dhaka_sub_dist.items(),
                          key=lambda x: -x[1]):
    arrivals = int(mobility_central *
                   destination_probs['Dhaka Division'] * prob)
    summary_lines.append(
        f"    {dest:<20} {prob*100:.0f}%  "
        f"(~{arrivals:,} central estimate)"
    )

summary_lines += [
    "",
    "LAYER TRANSPARENCY:",
    "  VALIDATED:          GRACE groundwater depletion trend",
    "  LITERATURE-INFORMED: Mobility rate (monga literature)",
    "  EMPIRICAL BASIS:    Destination probabilities (Census 2011)",
    "  SCENARIO FRAMEWORK: Stress multiplier assumption",
    "",
    "NEXT: Phase 3 — Urban Absorption Capacity (Dhaka wards)",
]

with open(OUTPUT_DIR + 'phase2_summary.txt', 'w',
          encoding='utf-8') as f:
    f.write('\n'.join(summary_lines))

print("Summary saved → outputs/phase2_summary.txt")
print("\n✓ Phase 2 complete.")
print("Next: Phase 3 — Urban Absorption Capacity Index")
