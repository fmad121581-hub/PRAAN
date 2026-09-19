# PRAAN — judge Q&A prep

The rule that wins these rooms: **a known limitation stated first is a
strength; the same limitation found by a judge is a wound.** You now have
an unusually honest project. Lead with that, don't hide it.

---

## The five hard questions

### 1. "GRACE resolves about 300 km. Your study area is smaller than one pixel. How is this a Barind Tract result?"

This is the sharpest question available and the most likely to be asked.
Answer it before they do — it is now in your Limitations section.

> "It isn't a Barind-specific measurement, and we don't claim it is. Mascon
> solutions resolve roughly 3 degrees, which is larger than our study area —
> in fact our four districts return values within 0.013 of each other while
> the temporal range is 0.16, so they're effectively sampling one cell. What
> GRACE gives us is a northwest-Bangladesh water-balance trend. The
> groundwater interpretation comes from pairing that with BWDB tube-well
> records showing 0.5–1 m/yr water-table decline in Rajshahi. Satellite for
> the regional trend, ground data for the attribution."

Never say "GRACE proves groundwater depletion in the Barind Tract."

### 2. "Your mobility rate comes from a famine survey. Why does that transfer to slow groundwater decline?"

> "It doesn't transfer cleanly, and that's why we call it a scenario
> parameter rather than a prediction. Monga is a fast-onset income shock;
> groundwater depletion is slow-onset. What the 36% gives us is an observed
> ceiling on how households in this exact region respond to agricultural
> income loss. We bracket it 20–50% and we couple it to the GRACE deficit
> through an elasticity we state openly as assumed. If a judge thinks the
> elasticity should be different, they can change one number and see the
> answer move — that's the point of building it that way."

### 3. "Does the satellite data actually change your output, or is it decoration?"

Until today the honest answer was "it's decoration." Now it isn't — make
sure you can show this:

> "It drives it. The mobility rate scales with the GRACE deficit relative to
> the 2006/07 baseline. Half the observed slope gives 835,000 arrivals, the
> observed slope 869,000, a 50% steeper slope 890,000. If the trend were
> different, the planning output would be different."

Have `phase2_coupled_summary.txt` open in a tab.

### 4. "How do you decide which ward a migrant goes to?"

> "Arrivals are distributed as population times one minus the stress index —
> more arrivals to wards with more spare capacity. That's an assumption, and
> arguably the wrong direction, because Dhaka's low-income in-migrants have
> historically clustered in dense, high-stress areas like Korail and
> Bhashantek. So we ran it both ways. Ten of the thirteen highest-concern
> wards are the same either way, so the headline doesn't rest on that
> choice."

Volunteering the weakness and then showing you tested it is the single
most credibility-building move you have.

### 5. "How sensitive is this ranking to weights you chose yourself?"

> "The top of the ranking is stable, the bottom isn't. Across 625 weight
> combinations at plus or minus 10 points per indicator, the top-ranked ward
> is unchanged 90.7% of the time and the top five overlap by 4.2 of 5. The
> exact top-13 set only reproduces 21.9% of the time. So we present the top
> wards as robust and the boundary of the list as indicative."

Do **not** say "the top 9–12 wards are consistent." That was the old,
wrong claim.

---

## Questions you should hope for

- **"What surprised you?"** → The duplicate-ward bug. DNCC and DSCC both
  number wards from 1, so a name-based merge silently produced a ward
  appearing twice with two different stress scores. It inflated our
  high-concern count from 7 to 13. We caught it, fixed it, and the
  corrected number is smaller and real.
- **"What would you do with more time?"** → Ground-truth the ASI against
  observed settlement growth; replace the assumed elasticity with one
  estimated from historical district-level migration series; get BBS records
  for the 77 unmatched ward fragments.
- **"Who is this for?"** → Named users are already on the site: RAJUK and
  the city corporations for pre-positioning, disaster managers for the
  Jan–May drawdown signal, aid agencies for triage.

---

## Do not do these

- Don't publish the −0.898 / r = −0.678 figures until
  `grace_mascon_tws_raw.csv` is committed and reproduces them. A judge who
  opens `phase2_summary.txt` and sees different numbers has found a
  contradiction you handed them. Run `14_reconcile_grace.py` first.
- Don't call any layer "validated" except Layer 1's trend detection.
- Don't say "prediction" anywhere. Say scenario, or mobility pressure.
- Don't let the demo open on the map. Open on the problem.

---

## The 30-second version

> Northwest Bangladesh is losing groundwater and it isn't coming back —
> GRACE has watched it for 22 years and the aquifer has never recovered to
> its 2002 level. When farming fails there, people move, and two-thirds of
> them go to Dhaka. PRAAN asks the question nobody has costed: which Dhaka
> wards can actually absorb them? We score every city-corporation ward on
> density, built-up land, flood risk and household crowding, cross it with
> projected arrivals, and get seven wards that are already stressed and are
> about to receive disproportionate pressure. Rampura Ward 22 is first.
> That's a list a planner can act on before the arrivals, not after.

Say the problem, then the number, then the name of one ward. Concrete
beats comprehensive.

---

## Before the event

- [ ] Run `14_reconcile_grace.py`, commit the MASCON CSV
- [ ] Put team member names and roles on the site — judges reward knowing
      who did what, and right now the page says only "Team Voyagers"
- [ ] Check the live map on a phone; most judges will look on one
- [ ] Have `sensitivity_summary.txt` and `phase2_coupled_summary.txt` open
      in tabs — being able to show the file when challenged is worth more
      than any slide
- [ ] Decide who answers the GRACE resolution question, and let them
      practise it out loud twice
