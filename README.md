# How Much Data Is Enough? — Abstention-Aware Menstrual Cycle Inference from Wearable Sensors

A conformal-prediction framework with reject option for hormone-anchored menstrual phase inference, built on the mcPHASES dataset (Lin et al. 2026).

## Team

- **Supervisor:** M. Danioł
- **Student 1:** WP2 / WP3 — Data audit, preprocessing, endpoint construction
- **Student 2:** WP5 — Base classifier and fixed-rule / oracle baselines
- **Student 3:** WP6 — Covariate-conditional sufficiency model (core contribution)
- **Student 4:** WP7 — Statistics, calibration, robustness

Roles are assigned from: U. Dulak, P. Rogala, M. Kuśnierz, M. Szmigiel.

## Scientific question

How much wearable data is sufficient for stable hormone-anchored menstrual cycle phase inference, and does the sufficiency threshold vary across individuals in ways that can be predicted from observable signal characteristics?

See `research_plan_v4.pdf` Section 2.1. The central claim is that an uncertainty-aware framework with abstention improves menstrual phase inference compared with fixed-window rules.

## Target venues

- JMIR mHealth and uHealth (best fit)
- npj Women's Health
- J Biomedical Informatics
- ML4H / ACM CHIL (workshop backup)

## Repository layout

```
docs/                         WP1 documents (read these first)
  data_contract_v1.md         Interface between WP2/WP3/WP5 and WP6
  student3_charter.md         Student 3's one-page role card
  onboarding_student3.md      Day-1 to Day-3 plan for Student 3
  claims_boundary.md          What we claim and what we do not claim
  hero_figure_spec.md         Three-panel contribution figure (Figure 1)
  gap_statement.md            Literature gap paragraph + citation audit
  plan_v4.1_changelog.md      WP1 amendments on top of plan v4.0
  tutorial_summaries/         Template for Angelopoulos & Bates summaries
src/                          Real analysis code (populated from week 2)
synthetic/                    Synthetic data generator (Student 3's regression suite)
  generator.py                Produces three parquet files matching the contract
  validate_contract.py        Schema / referential-integrity validator
  v1/                         Generated outputs (created on first run)
tests/                        Unit tests (populated from week 2)
dataset/                      mcPHASES raw tables (PhysioNet, read-only)
research_plan_v4.pdf          Source of truth — all decisions trace back here
```

## Authoritative documents

- **`research_plan_v4.pdf`** — plan v4.0 (March 2026). Frozen; amendments live in the changelog.
- **`docs/plan_v4.1_changelog.md`** — amendments agreed during WP1.
- **`docs/data_contract_v1.md`** — Student 3 builds against this for 8 weeks.

When those three disagree, the changelog wins over the plan, and the data contract wins for interface matters.

## Running the synthetic generator

```bash
pip install --break-system-packages pandas numpy pyarrow
python synthetic/generator.py --out synthetic/v1 --seed 42
python synthetic/validate_contract.py --dir synthetic/v1
```

The generator produces `probability_table.parquet`, `labels.parquet`, and `covariates.parquet` in `synthetic/v1/`. The validator exits non-zero on any contract violation.

Student 3 uses these outputs to build the conformal layer before real data is available, and keeps them permanently as a regression test suite.

## Real data

The mcPHASES raw CSVs live in `dataset/` (PhysioNet v1.0.0, n=42). Access is in progress; WP2/WP3 will build a reproducible pipeline from these tables in weeks 0–4. Until then, synthetic data is the development target.

## Three non-negotiable language rules

These appear verbatim in the charter, onboarding, and claims boundary. They matter because the paper will be read by reviewers who have seen overclaimed conformal-prediction papers before.

1. Never write "conformal guarantees coverage" — always "empirical coverage, validated via LOSO-CV."
2. Never say "individual-level personalization" — always "covariate-conditional sufficiency estimation."
3. No new baselines or methods beyond Mondrian conformal + APS + regression meta-model. Scope-creep requests go to supervisor.

## Reproducibility

Every result in the final paper must be reproducible from this repo with a single command. Seeds fixed. LOSO folds generated once (WP2) and never re-split. Experiments logged with date, config hash, metrics, and responsible person.
