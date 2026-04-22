# Onboarding — Student 3 (WP6)

Welcome to the project. You are being fast-tracked to start on Monday, three weeks ahead of most WP6 plans, because your contribution — the covariate-conditional sufficiency model — has the longest runway in the paper (plan §7, weeks 0–8). The synthetic-data track in plan §7 ("WP1 + WP2 + synthetic pipelines, weeks 1–2") was designed exactly for this: you build against a contract, not against the real data, so you do not wait for Students 1 and 2 to finish. By the end of Wednesday you should be unblocked for five-plus weeks of productive work independent of upstream delays. Read the research plan, the charter, and the data contract in that order before you write any code.

---

## Day 1 — Monday

**Reading (morning):**
1. `research_plan_v4.pdf` in full, paying close attention to:
   - §1.4 (Hero Figure — amended; see hero figure spec)
   - §2.2 (gap statement)
   - §2.3 (formal definition of sufficiency)
   - §2.4 (conformal prediction in a temporal setting — the single biggest reviewer risk)
   - §2.5 (differentiation from Kilungeja et al. 2025)
   - §3.3 (uncertainty quantification layer)
   - §3.4 (covariate-conditional sufficiency estimation — your core method)
2. `docs/student3_charter.md` — pin it above your desk.
3. `docs/data_contract_v1.md` — this is your sole interface with upstream WPs. You will read nothing from the `dataset/` folder directly. If a column you want is not in the contract, that is a contract amendment conversation with supervisor, not a workaround.
4. Angelopoulos & Bates (2021), "A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification," arXiv:2107.07511. Read all of Sections 1–3; skim the rest.

**Deliverable (afternoon):**
- One-page tutorial summary in `docs/tutorial_summaries/student3_angelopoulos_bates.md`, following `docs/tutorial_summaries/TEMPLATE.md`. Answer these three questions, one paragraph each:
  1. What does split conformal prediction formally guarantee?
  2. What assumption does the guarantee depend on?
  3. Why is that assumption only approximately satisfied in our setting? (Cite plan §2.4 and Stocker et al. 2025.)
- Hand-sketch the hero figure based on `docs/hero_figure_spec.md`. Photograph, commit the image under `docs/figures/hero_sketch_student3_day1.jpg`. This matters — the plan says the hero figure must be sketched before any modeling begins (plan §1.4, WP1 deliverable 2).

End Monday having read the plan cover to cover and understood, in your own words, why we refuse to claim formal coverage.

---

## Day 2 — Tuesday

**Meeting with supervisor — 20:30 (1 hour):**
- You present a toy conformal-prediction example at the whiteboard (pen and paper is fine — 10 minutes, three slides or one diagram).
  - Show split conformal on a trivial binary classification task: calibration set → quantile of non-conformity scores → prediction set construction at α = 0.10.
  - State, in a single sentence, the exchangeability assumption and why our setting violates it.
- Supervisor confirms you can explain it. This is the gate for the rest of the week. If the explanation is shaky, we slow down and re-read Angelopoulos & Bates §2–§3 together before Wednesday.

**Building the synthetic generator (afternoon + evening):**

- Implement `synthetic/generator.py` per spec in the prompt and in the docstring stub. Key requirements:
  - 42 participants, IDs `P001`–`P042`.
  - 25–40 nights per participant, drawn reproducibly.
  - Latent participant "signal strength" ~ Beta(2, 2) controls convergence speed.
  - True ovulation day uniform over nights 12–18, hidden from output.
  - `p_post_ovulatory` = `logistic(signal_strength × (night_index − ovulation_day) + noise)`, calibrated by construction (if p ≈ 0.7 for a slice, the fraction post in that slice is ≈ 0.7).
  - Labels: `"pre"` before ovulation, `"post"` from ovulation onward. `label_confidence` is low near the boundary (±2 nights), high elsewhere.
  - Covariates: `signal_completeness` ~ 0.6-correlated with `signal_strength` via noisy mapping; `cycle_regular` ~70% True; modality flags (`has_temperature`, `has_hr_hrv`, `has_cgm`, `has_self_report`) mostly True with ~10% missing; 20 participants have `has_round_2 = True`. (Note: `has_eda` is **not** in the schema — mcPHASES v1.0.0 ships no EDA table. See data contract §7.)
  - `fold_id` = `hash(participant_id) % 5`.
  - Reproducible with `--seed` (default 42).
  - `--validate` flag that runs `validate_contract.py` on the output.

- Commit outputs to `synthetic/v1/` (three parquet files matching the contract).
- Run `python synthetic/validate_contract.py --dir synthetic/v1` and confirm clean exit.

End Tuesday with a reproducible synthetic dataset that passes the contract validator. You can regenerate it at will with `python synthetic/generator.py --out synthetic/v1 --seed 42`.

---

## Day 3 — Wednesday

**Milestone day — this is what unblocks you for five-plus weeks.**

**First conformal layer on synthetic data:**

1. Load `synthetic/v1/probability_table.parquet` and `labels.parquet`.
2. For each held-out participant (LOSO on the synthetic 42):
   - Compute APS non-conformity scores s(x, y) = 1 − p̂(y|x) on the remaining 41 participants' (all nights, last cumulative-k only, to start — refine later).
   - Compute the conformal quantile q̂ at level ⌈(n+1)(1−α)⌉ / n with α = 0.10.
   - For each cumulative night k in the held-out participant's trajectory, construct the prediction set C_α(x_i^{1:k}) = { y : p̂(y | x_i^{1:k}) ≥ 1 − q̂ }.
   - Record |C_α| at each k.
3. Plot |C_α| vs. cumulative-k for a representative sample of ~10 participants chosen to span the signal-strength Beta distribution (low / medium / high).
4. Save to `docs/figures/student3_day3_sufficiency_curves.png`.
5. Send the plot to supervisor by end of day with a one-paragraph note: do τᵢ values look visibly heterogeneous across participants? (If yes, you are on track. If no, the generator is wrong — fix it before writing the real conformal code.)

**What "sensible" looks like on the plot:**
- Most curves start at |C_α| = 2 (both classes plausible), drop to |C_α| = 1 at some k (sufficiency), and stay there.
- Some curves drop at k = 5, others at k = 12, others never drop within the observation window (non-convergers).
- Variation is visible, not subtle. If all curves converge at the same k, the generator's signal_strength distribution is too narrow and you regenerate with wider Beta parameters.

If the Wednesday plot looks right, you are officially unblocked. The next five weeks are building out Mondrian conformal (stratified by covariate group), the regression meta-model for τᵢ, and the decision policy — all against the same synthetic data. Student 2's real base classifier arrives around week 5; by then your code will be tested, parameterized, and ready to swap inputs.

---

## Three hard rules for the week (and the rest of the project)

1. **Do not wait for anyone.** Any upstream input you need that is not yet available is mocked using the synthetic pipeline. Build the fake version, document what you assumed, move on. Only flag as a blocker if the contract itself is ambiguous or if you need a scientific decision from supervisor. "Student 2 hasn't sent me the base classifier yet" is not a blocker in weeks 0–4; the synthetic `p_post_ovulatory` column is the stand-in.

2. **The synthetic data stays in the repo permanently.** It is your regression test suite. Every time you change the conformal layer, you run it against `synthetic/v1/` first and confirm outputs are stable. When the real data arrives, the synthetic suite is how you distinguish "my code is wrong" from "the real data looks different." Do not delete it after week 5.

3. **Never write "conformal guarantees coverage" — always "empirical coverage."** This rule appears in the charter, here, and in `docs/claims_boundary.md`. It is the single language slip that gets the paper rejected. If you catch yourself writing it in a docstring, a commit message, or a plot title, fix it before pushing.

---

See you Monday. Read the plan first. Questions before then go to supervisor by email or Slack — do not sit on them.
