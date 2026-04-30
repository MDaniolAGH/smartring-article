# Onboarding — Student 3 (WP6)

You own the covariate-conditional sufficiency model — the journal paper's central contribution. The synthetic-data track in plan §7 was designed so you can build against the data contract before Students 1 and 2 finish their pieces; the three milestones below give you the foundation, after which you join the conference push.

**Two onboarding documents apply:**

- **This document (English, milestone-ordered)** — covers the foundation: reading, understanding split conformal, running the conformal layer on synthetic data. Work Milestones 1–3 in order.
- **`docs/notatka_dla_zespolu_pl.md` (Polish, day-by-day)** — once Milestone 3 is done, the conference push (deadline **2026-05-07**) follows the day-by-day schedule in that document. The notatka also covers the per-role plans for Students 1, 2, and 4.

**Two timelines apply:**

1. **Conference deadline 2026-05-07** — short paper or poster on the Round-2 subcohort (n≈19). Day-by-day plan in the notatka.
2. **Journal-paper plan** — full method (Mondrian stratification, regression meta-model, longitudinal transfer) on the full cohort. Post-conference; spec in `docs/student3_charter.md`.

Both timelines use the same code, contracts, and notebooks. The conference version is a focused subset of the journal version.

---

## Milestone 1 — Foundations

**Reading (in this order).**

1. `research_plan_v4.pdf` in full, paying close attention to:
   - §1.4 (Hero Figure — amended; see hero figure spec)
   - §2.2 (gap statement)
   - §2.3 (formal definition of sufficiency)
   - §2.4 (conformal prediction in a temporal setting — the single biggest reviewer risk)
   - §2.5 (differentiation from Kilungeja et al. 2025)
   - §3.3 (uncertainty quantification layer)
   - §3.4 (covariate-conditional sufficiency estimation — your core method)
2. `docs/student3_charter.md` — keep open while you read; it sets the role and the three language rules.
3. `docs/data_contract_v1.md` — this is your sole interface with upstream WPs. You will read nothing from the `dataset/` folder directly. If a column you want is not in the contract, that is a contract amendment conversation with supervisor, not a workaround.
4. Angelopoulos & Bates (2021), "A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification," arXiv:2107.07511. Read all of Sections 1–3; skim the rest.

**Deliverables.**

- One-page tutorial summary in `docs/tutorial_summaries/student3_angelopoulos_bates.md`, following `docs/tutorial_summaries/TEMPLATE.md`. Answer these three questions, one paragraph each:
  1. What does split conformal prediction formally guarantee?
  2. What assumption does the guarantee depend on?
  3. Why is that assumption only approximately satisfied in our setting? (Cite plan §2.4 and Stocker et al. 2025.)
- Hand-sketch the hero figure based on `docs/hero_figure_spec.md`. Photograph, commit the image under `docs/figures/hero_sketch_student3_m1.jpg`. The plan says the hero figure should be sketched before any modeling begins (plan §1.4, WP1 deliverable 2).

**Gate to Milestone 2.** You can explain, in your own words, why we refuse to claim formal coverage. Tutorial summary and hero sketch are committed.

---

## Milestone 2 — Understanding check + synthetic data

**Understanding check (async, via deliverable).**

The tutorial summary written in Milestone 1 is the understanding-check artefact. The supervisor reads it and replies with one of: "good, proceed", "rewrite section X", or "let's discuss before you continue." If the summary explains exchangeability and our setting's violation of it correctly (in your own words, with a citation back to plan §2.4 and Stocker et al. 2025), Milestone 2 work begins.

A second async artefact — a 10-line worked example showing split conformal on a toy binary classifier (calibration set → quantile of non-conformity scores → prediction set at α = 0.10) — can be added to the summary if you want to demonstrate hands-on understanding before touching the synthetic generator. Optional but recommended.

**Build the synthetic generator.**

- Implement (or fork the existing) `synthetic/generator.py` per spec in the docstring. Key requirements:
  - 42 participants, IDs `P001`–`P042`.
  - 25–40 nights per participant, drawn reproducibly.
  - Latent participant "signal strength" ~ Beta(2, 2) controls convergence speed; geometric mapping to slope keeps the weak-signal tail genuinely weak (so at least one non-converger appears at the default seed).
  - True ovulation day uniform over nights 12–18, hidden from output.
  - `p_post_ovulatory` = `sigmoid(signal_strength × (night_index − ovulation_day) + noise)`, calibrated by construction via `Bernoulli(p_post)` label sampling.
  - Labels: sampled from `Bernoulli(p_post)`, encoded as `"pre"` / `"post"`. `label_confidence` is `2 × |p_post − 0.5|` — low near the boundary, high elsewhere.
  - Covariates: `signal_completeness` noisily monotone in `signal_strength`; `cycle_regular` ~70% True; modality flags (`has_temperature`, `has_hr_hrv`, `has_cgm`, `has_self_report`) mostly True with ~10% missing; 20 participants have `has_round_2 = True`. (Note: `has_eda` is **not** in the schema — mcPHASES v1.0.0 ships no EDA table. See data contract §7.)
  - `fold_id` = `hash(participant_id) % 5`.
  - Reproducible with `--seed` (default 42).
  - `--validate` flag that runs `validate_contract.py` on the output.

- Commit outputs to `synthetic/v1/` (three parquet files matching the contract).
- Run `python synthetic/validate_contract.py --dir synthetic/v1` and confirm clean exit.

**Gate to Milestone 3.** Reproducible synthetic dataset that passes the contract validator. Regeneration is one command.

---

## Milestone 3 — First conformal layer on synthetic data (unblock gate)

This is the milestone that unblocks you for the rest of the project — both the conference deadline and the journal-paper work.

**Start here:** open `notebooks/04_wp6_conformal.ipynb`. It is the reference implementation of Milestone 3: loads the three input-contract files, runs split conformal with APS under LOSO and per-k calibration (recipe b), writes `prediction_sets.parquet` + `decisions/covariate_conditional.parquet` + τᵢ entries per the pipeline contract, and produces the |Cα|-vs-k plot. Run it, then re-implement it yourself.

Your Milestone 3 gate (what you send to supervisor):

1. Confirm you can explain, in your own words, *why* recipe (b) — per-cumulative-k calibration — was chosen over the pooled alternative (recipe a) and the final-k alternative (recipe c). See the notebook's §3 rationale and the pipeline contract's open-item list.
2. Produce the |Cα|-vs-k plot for ~10 representative participants spanning the signal-completeness range. Save to `docs/figures/student3_m3_sufficiency_curves.png`.
3. Report τᵢ distribution: median, IQR, number of non-convergers. Do values look visibly heterogeneous across participants? (If yes, you are on track. If not, the issue is either the generator parameters or the recipe — discuss before moving on.)
4. Send the plot + one-paragraph note to supervisor.

**What "sensible" looks like on the plot.**
- Most curves start at |C_α| = 2 (both classes plausible), drop to |C_α| = 1 at some k (sufficiency), and stay there.
- Some curves drop at k = 5, others at k = 12, others never drop within the observation window (non-convergers).
- Variation is visible, not subtle. If all curves converge at the same k, the generator's signal_strength distribution is too narrow and you regenerate with wider parameters.

**Gate to WP6 proper.** Supervisor reviews the plot and confirms you are unblocked. After Milestone 3, work splits along the two timelines:

- **Conference push (to 2026-05-07):** swap synthetic inputs for real-data stand-ins (LH-surge labels for the Round-2 subcohort, simple temperature-mean classifier), run the same conformal layer, ship the |Cα|-vs-k plot and the Fixed-5 comparison table. See `docs/notatka_dla_zespolu_pl.md` for the day-by-day plan.
- **Journal-paper plan:** build out Mondrian conformal (stratified by covariate group), the regression meta-model for τᵢ, and the full decision policy. Student 2's real base classifier arrives later in the journal-paper schedule; by then your code is tested, parameterized, and ready to swap inputs.

---

## Three hard rules for the project (not just these milestones)

1. **Do not wait for anyone.** Any upstream input you need that is not yet available is mocked using the synthetic pipeline. Build the fake version, document what you assumed, move on. Only flag as a blocker if the contract itself is ambiguous or if you need a scientific decision from supervisor. "Student 2 hasn't sent me the base classifier yet" is not a blocker in weeks 0–4; the synthetic `p_post_ovulatory` column is the stand-in.

2. **The synthetic data stays in the repo permanently.** It is your regression test suite. Every time you change the conformal layer, you run it against `synthetic/v1/` first and confirm outputs are stable. When the real data arrives, the synthetic suite is how you distinguish "my code is wrong" from "the real data looks different." Do not delete it after the conference, and do not delete it after the journal submission either.

3. **Never write "conformal guarantees coverage" — always "empirical coverage."** This rule appears in the charter, here, and in `docs/claims_boundary.md`. It is the single language slip that gets the paper rejected. If you catch yourself writing it in a docstring, a commit message, or a plot title, fix it before pushing.

---

Questions before or during the milestones go to supervisor by whatever async channel you use (email, Slack, shared doc). All gates are async — the supervisor reviews each milestone's deliverable and replies in writing. No scheduled meetings.
