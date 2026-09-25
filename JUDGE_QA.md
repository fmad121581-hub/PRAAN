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
> solutions resolve roughly 3 degrees, which is larger than our study area,
> so what GRACE gives us is a northwest-Bangladesh water-balance trend. We
> measured how bad that is rather than guessing: we ran the same variable,
> same season, same method over four regions of the country. Three are
> genuinely separate signals — every pair differs by 5 to 6 cm — but the
> northeast haor basin and the central floodplain come back 0.05 cm apart
> with a correlation of 1.000. Sylhet and Dhaka are inside one mascon cell.
> Bangladesh is about 400 km across and a mascon resolves about 300, so the
> country supports roughly three independent samples, not four, and we
> report three. The groundwater interpretation then comes from pairing the
> regional trend with BWDB/BMDA tube-well records showing water-table
> decline averaging 0.2-0.4 m/yr across Rajshahi district (2000-2013), and
> over 0.6 m/yr in the fastest-depleting upazilas such as Tanore (Aziz et
> al. 2015). Satellite for the trend, ground data for the cause."

Never say "GRACE proves groundwater depletion in the Barind Tract."

**If they press on significance**, you are on stronger ground than OLS:

> "The series has lag-1 autocorrelation of +0.72, so ordinary least squares
> overstates the certainty — its p of 0.0039 assumes each year is
> independent of the last, and water storage isn't. We publish the
> Mann-Kendall result with the Hamed-Rao variance correction instead:
> p = 0.0103, Sen's slope −0.905 cm/yr. The trend survives the stricter
> test, which is why we're willing to lead with it."

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

Make sure you can show this:

> "It drives it. The mobility rate scales with the GRACE deficit relative to
> the 2006/07 baseline. Half the observed slope gives 835,000 arrivals, the
> observed slope 869,000, a 50% steeper slope 890,000. If the trend were
> different, the planning output would be different."

Have `phase2_coupled_summary.txt` open in a tab.

### 4. "How do you decide which ward a migrant goes to?"

> "On population alone — and that's the result of a test we failed, which
> is the more interesting answer. We used to distribute arrivals as
> population times one minus the stress index, more arrivals to wards with
> spare capacity. That was an assumption nobody had checked, so we checked
> it against what actually happened: WorldPop and GHSL growth per ward,
> 2000 to 2020.
>
> The naive test says we had it backwards — stress correlates with growth at
> rho = +0.267, p = 0.020. We don't use that number, because it's circular.
> The index's biggest component is present-day density, and a ward is dense
> today partly *because* it grew; the outcome is sitting inside the
> predictor. So we rebuilt the index from year-2000 inputs only, where
> nothing in the predictor can have been caused by the outcome. It predicts
> nothing: rho = −0.154, p = 0.19 over the full period, and null in both
> sub-periods, with no single component significant.
>
> So the honest conclusion is that our index measures stress, not
> attraction. We allocate on population alone and we say that on the site.
> And the ranking barely cares: Kafrul Ward 14 is first under all three
> rules, and ten of the top thirteen are shared."

Volunteering the weakness, showing you tested it, and reporting a **null
against your own index** is the single most credibility-building move you
have. Very few teams will have failed a test in public. Do not soften it.

### 5. "How sensitive is this ranking to weights you chose yourself?"

> "The top of the ranking is stable, the bottom isn't. Across 625 weight
> combinations at plus or minus 10 points per indicator, the top-ranked ward
> is unchanged 77% of the time and the top five overlap by 4.0 of 5. The
> exact top-13 set only reproduces 11% of the time, though mean overlap is
> 11.6 of 13. So we present the top wards as robust and the exact boundary
> of the list as indicative."

Do **not** say "the top 9–12 wards are consistent." That was the old,
wrong claim.

### 6. "Why only 75 of the wards?"

> "Because we won't rank a ward on a population we made up. GADM 4.1 predates
> the ward expansion, so 55 census wards have no polygon at all, and 23
> polygons carry union names with no ward number. We tested substituting
> satellite population and rejected it — WorldPop is a density, and it
> correlates negatively with census counts; density times ward area gives rank
> agreement of only 0.20 with 47% median error. Those wards are on the map,
> scored for absorption stress, and explicitly not ranked."

---

## Questions you should hope for

- **"What surprised you?"** → How much damage one join key did. DNCC and
  DSCC both number wards from 1, so a name-based merge produced wards
  appearing twice with two different stress scores. Worse, GADM splits some
  wards across thana boundaries into "(Part)" polygons that match no census
  record by name at all — that alone hid 14 real wards, including Kafrul
  Ward No-14, which has the largest population in our city set and now ranks
  first. BBS is indexed by (corporation, ward number), not by name. Keying on
  that took us from 61 rankable wards to 75 and corrected a corporation
  mislabelling: DNCC only has wards 1–54, so Ward No-55 can only be DSCC.
- **"What would you do with more time?"** → Find a stress index that
  actually predicts arrivals — ours doesn't, and we now know that rather
  than assuming it; replace the assumed elasticity with one estimated from
  historical district-level migration series; and get ward boundaries that
  match the current census, since GADM 4.1 predates the ward expansion and
  55 BBS wards have no polygon at all.
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
> projected arrivals, and get eleven wards that are already stressed and are
> about to receive disproportionate pressure. Kafrul Ward 14 is first.
> That's a list a planner can act on before the arrivals, not after.

Say the problem, then the number, then the name of one ward. Concrete
beats comprehensive.

---

## Before the event

- [ ] Run `14_reconcile_grace.py`, commit the MASCON CSV
- [ ] Have `predictive_validation.txt` open too — the failed ASI test is
      your strongest answer, not your weakest, and you want the file
- [x] Team member names and roles are on the site. Each person owns a named
      part of the project and can be questioned on it:
      Fahim Ahmed (technical lead), Arshil Azim (validation and domain
      research), Nawar Noor Nusaiba (video), Mahin Haider (pitch and demo),
      Md. Fardeen Al Mahin (design and submission)
- [ ] Each member rehearses the one question their role owns, out loud
- [ ] Check the live map on a phone; most judges will look on one
- [ ] Have `sensitivity_summary.txt` and `phase2_coupled_summary.txt` open
      in tabs — being able to show the file when challenged is worth more
      than any slide
- [ ] Decide who answers the GRACE resolution question, and let them
      practise it out loud twice
