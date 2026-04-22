# Student 3 — Charter (WP6: Covariate-Conditional Sufficiency Model)

**Pin this above your desk. Everything else is negotiable. This is not.**

---

## Your role, in one sentence

**Build the system that knows when it doesn't know yet.**

You are not building the best classifier. Student 2 delivers the calibrated base classifier. Your contribution is the conformal sufficiency layer and the decision policy that sits on top of it. The paper is publishable if and only if this layer produces a defensible "predict / defer / collect more" decision and shows that the sufficiency threshold τᵢ varies meaningfully across participants.

See research plan v4.0, §6 ("What Student 3 must understand"), and the changelog at `docs/plan_v4.1_changelog.md` for week-1 amendments.

---

## Your deliverables (from plan §6)

1. **Split conformal prediction layer with APS** on top of Student 2's calibrated base classifier.
2. **Individual sufficiency curves** |C_α(x_i^{1:k})| vs. k for every participant — the raw material for Figure 1.
3. **τᵢ estimation** per participant: first k at which |C_α| = 1 for 2 consecutive nights.
4. **Mondrian conformal prediction**, stratified by covariate groups from `docs/data_contract_v1.md` (signal completeness, cycle regularity, modality flags). Report within-stratum sample sizes.
5. **Regression meta-model** predicting τᵢ from covariates — sensitivity analysis for §3.4.
6. **Full decision policy**: predict / defer / collect-more, implemented per plan §2.3.
7. **Hero figure (Figure 1)** with real data — three panels per `docs/hero_figure_spec.md`. Covariate in Panel C is chosen based on which predictor has the strongest association in your regression meta-model.
8. **Main comparison table** contributions: you own the rows for the covariate-conditional method; Student 2 owns the fixed-rule and oracle rows; Student 4 assembles.
9. **Covariate-association analysis** (plan §8 row M).

---

## Your handoff inputs (what you receive)

From **Student 2 (WP5)**, via `probability_table.parquet` and a reliability-diagram check:

- `p_post_ovulatory` per (participant_id, night_index), calibrated via isotonic regression on an inner fold.
- Verified calibration (reliability diagram acceptable — if not, you flag and Student 2 re-calibrates before you build on it).
- `fold_id` for the 5-fold grouped-CV fallback.

From **Student 1 (WP2/WP3)**, via `labels.parquet` and `covariates.parquet`:

- `binary_label` per night, hormone-anchored, reconstructed from raw Mira LH/E3G/PdG (not from the derived mcPHASES `phase` column).
- `label_confidence` per night.
- Participant-level covariates: `signal_completeness`, `cycle_regular`, `mean_snr_temp`, `mean_snr_hr`, modality flags, `has_round_2`.

Schemas are frozen in `docs/data_contract_v1.md`. If Student 1 or 2 emits a file that fails `synthetic/validate_contract.py`, the problem is upstream — you do not work around it. You flag, they fix.

---

## Your handoff outputs (what Student 4 consumes)

For every participant-night in `probability_table.parquet`:

- **Prediction set** C_α(x_i^{1:k}) — stored as `{"pre"}`, `{"post"}`, or `{"pre", "post"}`.
- **|C_α|** as the calibrated uncertainty signal.
- **Decision** ∈ {predict, defer, collect-more} under the full policy (plan §2.3).

Per participant:

- **τᵢ** — your per-participant sufficiency threshold, or `None` if no convergence within the observation window (these are the "non-convergers" on Figure 1 Panel A).
- **Mondrian stratum assignment** and within-stratum quantiles q̂.

Format: one parquet file per output class (e.g., `prediction_sets.parquet`, `tau_per_participant.parquet`). Schema fixed in week 3 once the synthetic pipeline is running end-to-end; Student 4 is informed before it freezes.

---

## Three non-negotiable rules

### Rule 1 — Language of coverage

**Never write "conformal guarantees coverage." Always write "empirical coverage, validated via LOSO-CV."**

**Why:** Formal conformal guarantees require exchangeability of calibration and test data (Vovk et al. 2005). In our setting, observations accumulate sequentially within a cycle, consecutive nights are autocorrelated, and partial-cycle test users differ structurally from complete-cycle calibration users. Stocker et al. (2025) explicitly caution against naive application of conformal methods to temporally dependent data. Plan §2.4 is the single biggest reviewer risk in the paper. One slip of "guaranteed" in the draft and the paper is rejected.

**How to apply:** in code comments, docstrings, commit messages, plots, slides, and the manuscript. If you're not sure whether a statement is "guaranteed" or "empirical," assume empirical.

### Rule 2 — Framing of adaptation

**Never say "individual-level personalization." Always say "covariate-conditional sufficiency estimation."**

**Why:** At n=42, true individual-level adaptation is not statistically defensible (plan §3.4 "Why not 'personalization'"). What we are doing is adjusting the sufficiency threshold based on observable covariates — exactly what a real product would do during onboarding, before it knows anything about the specific user. This framing is honest. "Personalization" overclaims and is exactly the kind of language the ethics papers we cite (Punzi & Thuis 2025) call out.

**How to apply:** everywhere, same as Rule 1. In particular, your regression meta-model for τᵢ is "covariate-conditional sufficiency estimation," not "personalized sufficiency prediction."

### Rule 3 — Scope

**No new baselines, no new methods, no new datasets. Mondrian conformal + APS + a simple regression meta-model. That is the entire methodological toolkit for WP6.**

**Why:** Plan §9.2 freezes scope after WP1. n=42 cannot support a model zoo; adding methods inflates multiple-comparison burden and weakens every remaining claim. Plan §10 lists "scope creep" as High severity.

**How to apply:** if you are tempted to try X ("it would only take an afternoon"), send the request to supervisor before writing any code. The answer is almost always no; the rare yes is logged in the changelog. Scope-creep ideas that are genuinely good become future work for the discussion section, not experiments for this paper.

---

## What success looks like

- **Primary success (plan §1.3):** your covariate-conditional model achieves ≥ correct-prediction rate at ≤ median τ compared to the best fixed rule AND the oracle global threshold, with subject-level bootstrap significance p < 0.05.
- **Secondary success:** even if the comparison fails, IQR of τᵢ across participants > 2 nights is a publishable negative-result-with-a-finding: "sufficiency varies; fixed rules ignore this."
- **Clean failure:** no adaptive strategy beats Fixed-5. The paper reframes as "at the resolution of mcPHASES (n=42), fixed rules are sufficient." Still publishable — plan §1.3.

You should be okay with any of these outcomes before you start. If any of them feels unacceptable, talk to supervisor now, not in week 8.

---

**Signed:** ______________________  **Date:** __________

Student 3, WP6 owner
