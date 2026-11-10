# PRAAN — judge Q&A prep

The rule that wins these rooms: **a known limitation stated first is a
strength; the same limitation found by a judge is a wound.** You now have
an unusually honest project. Lead with that, don't hide it.

---

## The seven hard questions

### 1. "GRACE resolves about 300 km. Your study area is smaller than one pixel. How is this a Barind Tract result?"

This is the sharpest question available and the most likely to be asked.
Answer it before they do — it is now in your Limitations section.

> "It isn't a Barind-specific measurement, and we don't claim it is. Mascon
> solutions resolve roughly 3 degrees, which is larger than our study area,
> so what GRACE gives us is a northwest-Bangladesh water-balance trend. We
> measured how bad that is rather than guessing: we ran the same variable,
> same season, same method over four regions of the country. Three are
> genuinely separate signals — every pair differs by 4 to 6.5 cm — but the
> northeast haor basin and the central floodplain come back identical,
> with a correlation of 1.000. Sylhet and Dhaka are inside one mascon cell.
> Bangladesh is about 400 km across and a mascon resolves about 300, so the
> country supports roughly three independent samples, not four, and we
> report three. The groundwater interpretation comes from two things.
> First, we subtract the soil, snow and canopy water in NASA's GLDAS model
> from GRACE, and the Barind's dry-season remainder still falls: −0.65 cm
> a year over 2002–2017, p = 0.017, about two-thirds of the decline.
> Second, we pair that with BWDB/BMDA tube-well records showing water-table
> decline averaging 0.2-0.4 m/yr across Rajshahi district (2000-2013), and
> over 0.6 m/yr in the fastest-depleting upazilas such as Tanore (Aziz et
> al. 2015). Satellite for the trend, a NASA model to take out the soil
> water, ground data for the cause."

If they ask what is left in the remainder: groundwater **plus surface
water**. GLDAS Noah has no rivers or wetlands and no irrigation, which is
why we use the dry season and call it an estimate.

Never say "GRACE proves groundwater depletion in the Barind Tract."

**If they press on significance**, you are on stronger ground than OLS:

> "OLS gives p = 0.0006, but it assumes each year is independent of the
> last. We publish a rank-based Mann-Kendall test instead: p = 0.0046,
> Sen's slope −1.04 cm/yr. We also ran the Hamed-Rao check for serial
> correlation. The raw series has lag-1 autocorrelation of +0.76, but
> almost all of that is the trend itself — once the trend is removed there
> is no significant autocorrelation left, so the correction changes
> nothing. We publish the more conservative number either way."

**If they ask why the haor basin's slope (−0.54 cm/yr) is "not
significant" when the coastal south's (−0.63) is, over 2002–2017:**

> "Significance depends on the noise as well as the slope. The haor basin is
> the wettest part of the country and its year-to-year swings are far
> larger, so a slope of that size can't be told apart from chance there
> (p = 0.26). Over the full record it even turns positive. The coastal
> series is much steadier, so a similar slope is clearly detectable
> (p = 0.017). We report the test result, not the slope alone — and
> that cuts both ways: once GRACE-FO is added the coastal decline is no
> longer significant (p = 0.54), and we say so."

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
> the 2006/07 baseline. Half the observed slope gives 798,000 arrivals, the
> observed slope 821,000, a 50% steeper slope 839,000. If the trend were
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

### 7. "The challenge asks for a tool. Where is it?"

> "Scroll to Be the trend detective. Pick any of seven variables — GRACE
> water storage, a groundwater estimate from GRACE minus GLDAS, GPM and
> CHIRPS rainfall, MODIS greenness and ground temperature, GLDAS soil
> moisture — any of five regions, a season and a
> range of years. It draws the record and runs Sen's slope with a 95%
> confidence interval and the Mann-Kendall test right in the page, with
> the same code as our Python pipeline, which script 24 checks against
> scipy. It works with the internet off. Case 3 is a null result on
> purpose: Dhaka's ground temperature shows no significant trend, and a
> detective should say so."

---

## Questions you should hope for

- **"What surprised you?"** → How much damage one join key did. DNCC and
  DSCC both number wards from 1, so a name-based merge produced wards
  appearing twice with two different stress scores. Worse, GADM splits some
  wards across thana boundaries into "(Part)" polygons that match no census
  record by name at all — that alone hid 14 real wards, including Kafrul
  Ward No-14, which now ranks first: it is the fifth most populous of the 75
  ranked wards and 15th on absorption stress, and no other ward ranks that
  high on both. BBS is indexed by (corporation, ward number), not by name. Keying on
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

- Don't quote the −1.013 / r = −0.763 OLS figures as the headline. The
  site leads with Sen's slope and Mann-Kendall (−1.04 cm/yr, p = 0.0046).
  `grace_mascon_tws_raw.csv` is committed and reproduces both; if a judge
  opens `phase2_summary.txt` (the older LAND product, r = −0.921), say which
  product the site uses. `14_reconcile_grace.py` shows the two side by side.
- Don't call any layer "validated" except Layer 1's trend detection.
- Don't say "prediction" anywhere. Say scenario, or mobility pressure.
- Don't let the demo open on the map. Open on the problem.

---

## The 30-second version

> Northwest Bangladesh is losing stored water, consistent with groundwater
> depletion — GRACE has watched it for 22 years and dry-season storage has
> not regained its 2002 level. When farming fails there, people move, and two-thirds of
> them go to Dhaka. PRAAN asks the question nobody has costed: which Dhaka
> wards can actually absorb them? We score every city-corporation ward on
> density, built-up land, flood risk and household crowding, cross it with
> projected arrivals, and get eleven wards where existing stress and
> incoming numbers combine most strongly. Kafrul Ward 14 is first.
> That's a list a planner can act on before the arrivals, not after.

Say the problem, then the number, then the name of one ward. Concrete
beats comprehensive.

---

## Before the event

- [x] Run `14_reconcile_grace.py`, commit the MASCON CSV
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
