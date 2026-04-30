# Plan v4.0 → v4.1 Changelog

**What this is.** Amendments agreed during WP1 discussions on top of `research_plan_v4.pdf` (v4.0, March 2026). The PDF is frozen. All changes live here. When docs disagree, the changelog wins over the plan; the data contract wins for interface matters.

**When an amendment lands here.** Plan §9.2 ("Scope control") requires supervisor sign-off for any change to research question, endpoint, validation strategy, or success criteria. Everything on this list has been discussed and approved.

---

## Amendments (in discussion order)

### 1. Data contract v1 defining interfaces between WP2/WP3/WP5 and WP6

`docs/data_contract_v1.md` specifies three parquet files (probability_table, labels, covariates) as the sole interface consumed by WP6. This was implicit in the plan (§3.2 states Student 3 builds "on top of" Student 2's classifier) but not formally schematized. Adding the contract lets WP6 begin before upstream WPs finish — see amendment 3.

The contract excludes EDA: the plan's §3.2 lists "EDA tonic level" as a base-classifier feature, but mcPHASES v1.0.0 ships no EDA table (see `dataset/README.txt`). EDA and the corresponding `has_eda` modality flag are dropped from v1 of the contract. If a future mcPHASES release adds EDA, this is a v2 amendment to the contract, not an error in v1.

### 2. Hero figure restructured from one panel to three panels

Plan §1.4 specified a single-panel problem figure (individual sufficiency curves). WP1 concluded this states the problem but not the contribution. The amended Figure 1 has three panels:

- **Panel A** — individual sufficiency trajectories with hero curves and one labelled non-converger (the original single-panel content, refined)
- **Panel B** — decision timelines for 4 representative participants under Fixed-5, Oracle-global-threshold, and Covariate-conditional strategies
- **Panel C** — τᵢ vs. a leading covariate with Mondrian stratum means

Specification in `docs/hero_figure_spec.md`. Correctness in Panel B comes from Student 4's LOSO-CV evaluation on real data, not simulation.

### 3. Emergency fast-track enabled for Student 3

Student 3 (WP6) begins productive work immediately using synthetic data, ahead of the plan's week-0–4 "synthetic pipelines" milestone. This is **not** a change to WP6's scope; it is a change to its start timing. The justification follows plan §7, which explicitly designed a synthetic-data track "S3: Conformal layer running on synthetic data" for weeks 1–2. We move that into week 0 so the longest-runway WP starts first. Milestone-ordered plan in `docs/onboarding_student3.md`.

### 4. Synthetic data generator promoted from "optional week 1–2" to Milestone-2 deliverable

Plan §11 ("Optional: Synthetic Simulation Study") framed a 200–1,000-participant simulation as optional. This amendment narrows the scope to a 42-participant **development harness** — smaller, deterministic, shaped to exercise the WP6 code path — and promotes it to a Milestone-2 deliverable in Student 3's onboarding, committed to `synthetic/v1/`. Reference implementation: `synthetic/generator.py` and `synthetic/validate_contract.py`. The larger §11 simulation study (200–1,000 synthetic users for "would this work at larger n?") remains optional and unchanged.

### 5. Claims boundary as a standalone document

Plan §1.2 listed five boundary-of-claims bullets. `docs/claims_boundary.md` expands each bullet into a short rationale. Enforcement is via supervisor review of every draft (abstract, captions, Discussion) and team members catching slips in each other's drafts — no formal signing ceremony.

### 6. All other sections of plan v4.0 remain in force

Unchanged: §1.3 (success/failure criteria), §2.1 (research question), §2.3 (formal definition of sufficiency), §2.4 (conformal-in-temporal-setting honesty), §2.5 (Kilungeja differentiation table — see amendment 7 below for the dataset correction), §3 all subsections, §4 all subsections, §5–§8, §9, §10 (risks), §12 (expected outputs), §13 (core message).

### 7. Kilungeja et al. 2025 dataset clarification (verified 2026-04-23)

Plan §1.5 note "Kilungeja et al. 2025 used same dataset" is **factually incorrect**. After reading the paper end-to-end (`docs/s44294-025-00078-8.pdf`), confirmed:

- Kilungeja's data: University of North Florida in-house collection, Empatica E4 + EmbracePlus wristbands, n=18 ovulatory subjects, 65 cycles, LH-strip ground truth.
- mcPHASES (our data): n=42, Fitbit Sense + Dexcom G6 + Mira Plus, full hormone panel for 20 R2 participants.

These are **different datasets**. Consequences:

- Plan §10 risk "Kilungeja differentiation unclear" downgraded from **High** to **Low**.
- Plan §2.5 differentiation table holds on every row; differentiation now stronger because dataset itself differs. Optional new "Dataset" row in the table makes this explicit.
- Plan §4 "Direct comparators" assignment for Kilungeja remains valid — it is still a direct comparator on the task (machine-learning menstrual phase classification from wearable signals), just not on the dataset.

Citation status in `docs/gap_statement.md` updated from UNVERIFIED to VERIFIED for this entry.

### 8. Conference-version scope (target: student conference 2026-05-07)

Before the journal-paper version (target submission: weeks 8–12 per plan §7), we ship a **conference-version subset** at a student conference. Scope on a 9-day budget:

- Restrict to Round-2 subcohort (n≈19) — clean LH + progesterone-metabolite endpoint, no tiered-confidence labeling needed.
- One figure (sufficiency curves), one table (Fixed-5 vs covariate-conditional), one short paper or poster.
- Skip Mondrian stratification, regression meta-model for τᵢ, longitudinal R1→R2 transfer, oracle-global and signal-quality baselines. Skip pre-registration deposit, Docker, CI/CD until after the conference.

Conference scope is documented in `docs/notatka_dla_zespolu_pl.md`. Journal-paper scope (plan §1.3 success criteria, plan §8 mandatory analyses) remains unchanged for the post-conference work.

---

## How to add a new amendment

1. Discuss with supervisor. Decisions about scope, endpoint, or success criteria are supervisor calls, not student calls (plan §9.2).
2. Append a numbered entry to this file with (a) what changed, (b) why, and (c) which plan section it touches.
3. If the amendment changes the data contract, also bump the contract version in `docs/data_contract_v1.md` §9 and update `synthetic/validate_contract.py`.
4. Email the diff to all four students before the change lands on main.
