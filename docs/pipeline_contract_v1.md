# Pipeline Contract v1

**Scope.** All file interfaces between WPs 2, 3, 5, 6, 7. Extends `docs/data_contract_v1.md` (which froze the three WP5/WP3/WP2 → WP6 files). Everything below is added.

**Status.** v1 — synthetic compatibility target. Every schema here is exercised by a starter notebook under `notebooks/` running against `synthetic/v1/`. Real-data validation deferred to weeks 2–4.

**Authority.** Same rules as the input contract: amendments require supervisor sign-off, version bump, and an update to whichever validator covers the schema. The pipeline contract wins over plan prose when they disagree.

---

## 1. Data flow

```
                             dataset/          dataset_parquet/
                             (raw CSVs)        (large raw as parquet)
                                   \                 /
                                    \               /
                                     v             v
                            +--------------------------+
                            |  WP2  (Student 1)        |
                            |   preprocessing          |
                            +--------------------------+
                                      |
                                      | preprocessing/cohort.parquet
                                      | preprocessing/valid_nights.parquet
                                      | preprocessing/missingness_report.parquet
                                      | preprocessing/loso_folds.parquet
                                      | covariates.parquet   (input contract)
                                      |
                                      v
                            +--------------------------+
                            |  WP3  (Student 1)        |
                            |   endpoint               |
                            +--------------------------+
                                      |
                                      | endpoint/cycle_boundaries.parquet
                                      | labels.parquet        (input contract)
                                      |
                                      v
                            +--------------------------+
                            |  WP5  (Student 2)        |
                            |   base classifier + 6    |
                            |   baselines              |
                            +--------------------------+
                                      |
                                      | probability_table.parquet   (input contract)
                                      | decisions/fixed_3.parquet
                                      | decisions/fixed_5.parquet
                                      | decisions/fixed_7.parquet
                                      | decisions/always_predict.parquet
                                      | decisions/oracle_global.parquet
                                      | decisions/signal_quality.parquet
                                      | tau_per_strategy.parquet    (appended to by WP5 and WP6)
                                      |
                                      v
                            +--------------------------+
                            |  WP6  (Student 3)        |
                            |   conformal + mondrian   |
                            +--------------------------+
                                      |
                                      | prediction_sets.parquet
                                      | decisions/covariate_conditional.parquet
                                      | tau_per_strategy.parquet  (appended — covariate_conditional rows)
                                      |
                                      v
                            +--------------------------+
                            |  WP7  (Student 4)        |
                            |   evaluation             |
                            +--------------------------+
                                      |
                                      | evaluation/metrics.parquet
                                      | evaluation/reliability.parquet
                                      | figures/*.png / *.pdf
```

Only one cross-cutting file, `tau_per_strategy.parquet`, is appended to by multiple WPs. Everything else is single-writer.

## 2. Storage layout on disk

```
preprocessing/
  cohort.parquet
  valid_nights.parquet
  missingness_report.parquet
  loso_folds.parquet
endpoint/
  cycle_boundaries.parquet
labels.parquet                      # input contract
covariates.parquet                  # input contract
probability_table.parquet           # input contract
decisions/
  fixed_3.parquet
  fixed_5.parquet
  fixed_7.parquet
  always_predict.parquet
  oracle_global.parquet
  signal_quality.parquet
  covariate_conditional.parquet
prediction_sets.parquet
tau_per_strategy.parquet
evaluation/
  metrics.parquet
  reliability.parquet
figures/                            # *.png / *.pdf
```

Synthetic bundle: root prefix `synthetic/v1/`. Real bundle: root prefix `real/v1/` (created when real pipeline lands; naming keeps versions side-by-side).

## 3. WP2 preprocessing outputs

### 3.1 `preprocessing/cohort.parquet`

One row per participant, grain `participant_id`.

| Column | Type | Description |
|---|---|---|
| `participant_id` | str | As in input contract §5 |
| `included` | bool | True iff the participant clears WP2 inclusion/exclusion |
| `exclusion_reason` | str, nullable | Populated when `included` is False; free text |
| `has_round_1` | bool | ≥1 valid night in 2022 interval |
| `has_round_2` | bool | ≥1 valid night in 2024 interval |
| `r1_total_days` | int32 | Calendar days observed in Round 1 (0 if none) |
| `r2_total_days` | int32 | Calendar days observed in Round 2 (0 if none) |
| `r1_valid_nights` | int32 | Nights passing the WP2 valid-night filter in Round 1 |
| `r2_valid_nights` | int32 | Nights passing the WP2 valid-night filter in Round 2 |

### 3.2 `preprocessing/valid_nights.parquet`

One row per participant × study-day in the observation window. Grain `(participant_id, day_in_study)`. This is the authoritative table for "what is a valid night"; every downstream WP refers here.

| Column | Type | Description |
|---|---|---|
| `participant_id` | str | |
| `study_interval` | int16 | 2022 or 2024 |
| `day_in_study` | int32 | Native mcPHASES day index |
| `is_valid_night` | bool | True iff the WP2 validity rule is satisfied |
| `exclusion_reason` | str, nullable | Populated when `is_valid_night` is False |
| `night_index` | int32, nullable | Within-participant 1-indexed running count of valid nights; null on invalid rows |
| `quality_flag` | str, nullable | One of `"ok"`, `"low_signal"`, `"dropout"` — per-night signal quality (feeds decision-policy "collect more" branch per plan §2.3) |

### 3.3 `preprocessing/missingness_report.parquet`

Modality coverage per participant. Grain `(participant_id, modality)`.

| Column | Type | Description |
|---|---|---|
| `participant_id` | str | |
| `modality` | str | One of `"temperature"`, `"hr"`, `"hrv"`, `"glucose"`, `"self_report"`, `"hormones_lh"`, `"hormones_e3g"`, `"hormones_pdg"` |
| `days_total` | int32 | Observation window days |
| `days_available` | int32 | Days with ≥1 record for this modality |
| `coverage_pct` | float32 | `days_available / days_total` |

### 3.4 `preprocessing/loso_folds.parquet`

Grouped-CV fallback fold assignment (plan §3.6). Grain `participant_id`.

| Column | Type | Description |
|---|---|---|
| `participant_id` | str | |
| `fold_id_5fold` | int8 | 0–4; for 5-fold grouped CV fallback if nested LOSO exceeds 24 h walltime |

Primary LOSO-CV uses `participant_id` directly as the fold key; no explicit LOSO column needed.

## 4. WP3 endpoint outputs

### 4.1 `endpoint/cycle_boundaries.parquet`

One row per detected menstrual cycle. Feeds the labeling rule; Student 4 references for sensitivity analyses.

| Column | Type | Description |
|---|---|---|
| `participant_id` | str | |
| `cycle_number` | int8 | 1-indexed within participant |
| `study_interval` | int16 | 2022 or 2024 |
| `cycle_start_day` | int32 | `day_in_study` of menstrual flow onset (cycle day 1) |
| `cycle_end_day` | int32 | `day_in_study` of the last day before next cycle start |
| `lh_surge_day` | int32, nullable | Day of detected LH surge; null if not detected |
| `pdg_rise_confirmed` | bool | True iff the surge is followed by ≥2 days of elevated progesterone metabolite in Round 2 |
| `ovulatory` | bool | Consensus ovulation call: `(lh_surge_day is not null) and (pdg_rise_confirmed or study_interval == 2022)` |
| `confidence_tier` | str | `"gold"` (LH + progesterone rise), `"silver"` (LH only, R1), `"bronze"` (peri-ovulatory), `"charcoal"` (LH surge without progesterone confirmation in R2 — likely anovulatory) |

### 4.2 `labels.parquet` — input contract, already frozen

See `docs/data_contract_v1.md` §2.2. No change. The `label_confidence` column is derived from `cycle_boundaries.confidence_tier` via a tier → confidence map specified in the WP3 endpoint protocol doc (to be written in Milestone 1 of WP3).

## 5. Strategy decision files — universal schema

Every strategy (six WP5 baselines + WP6 covariate-conditional) writes one file under `decisions/<strategy_name>.parquet`. All share the **same schema**. This lets WP7 ingest all seven files with one loader and one metrics loop.

Grain `(participant_id, night_index)`; one row per decision that the strategy emits.

| Column | Type | Description |
|---|---|---|
| `participant_id` | str | |
| `night_index` | int32 | As in input contract §2.1 |
| `cumulative_k` | int32 | Equals `night_index`; kept for symmetry with `probability_table` |
| `strategy_name` | str | Constant within file; one of `"fixed_3"`, `"fixed_5"`, `"fixed_7"`, `"always_predict"`, `"oracle_global"`, `"signal_quality"`, `"covariate_conditional"` |
| `decision` | str | `"predict"`, `"defer"`, or `"collect_more"` |
| `predicted_label` | str, nullable | `"pre"` / `"post"` when `decision == "predict"`; null otherwise |
| `prediction_set_size` | int8, nullable | 1 or 2 for strategies that compute conformal sets (covariate_conditional); null for fixed-rule baselines |
| `mondrian_stratum` | str, nullable | Populated only for covariate_conditional; stratum label (e.g., `"high_completeness_regular"`) |
| `is_synthetic` | bool | Constant within file |

**Consistency rules (validator-enforced).**
- `strategy_name` is constant within the file.
- If `decision != "predict"`, `predicted_label` is null.
- If `decision == "predict"`, `predicted_label` is one of `"pre"` / `"post"`.
- `prediction_set_size`, when present, is ≥1.
- Every `(participant_id, night_index)` in the file has a matching row in `probability_table.parquet` and `labels.parquet`.

**Fixed-rule baseline semantics (WP5 reference implementation).**
- `fixed_K`: rows have `decision = "defer"` for `night_index < K`, `decision = "predict"` for `night_index == K`. No rows emitted for `night_index > K` — the strategy commits at k=K and stops. Exactly one prediction per participant.
- `always_predict`: `decision = "predict"` at every night_index.
- `oracle_global`: `decision = "predict"` at `night_index == τ*`, `"defer"` before, nothing after. `τ*` is learned on training data.
- `signal_quality`: `decision = "predict"` at the first night where `mean_snr_temp` exceeds a learned threshold; `"defer"` before, nothing after.

**Covariate-conditional semantics (WP6).**
- `decision = "predict"` at the first night_index where `prediction_set_size == 1` and the previous row's `prediction_set_size == 1`.
- `decision = "defer"` when `prediction_set_size == 2`.
- `decision = "collect_more"` when `valid_nights.quality_flag` is `"low_signal"` or `"dropout"` (requires joining to `preprocessing/valid_nights.parquet`). If the WP2 quality flag is not yet populated, `collect_more` is never emitted in v1; document this in the WP6 notebook.

## 6. `tau_per_strategy.parquet`

One row per `(participant_id, strategy_name)`. Written by WP5 for its six strategies and **appended to** by WP6 for covariate_conditional. Consumers (WP7) read the unified file.

| Column | Type | Description |
|---|---|---|
| `participant_id` | str | |
| `strategy_name` | str | Same set as the decisions schema |
| `tau_i` | int32, nullable | Number of cumulative nights at which the strategy commits to a prediction; null for non-convergers |
| `convergence_status` | str | `"converged"`, `"non_converger"`, or `"single_flip"` (converged but flipped once mid-trajectory) |
| `is_synthetic` | bool | |

**Fixed-rule strategies:** `tau_i` is constant (3, 5, or 7); `convergence_status` is always `"converged"`.

**Append protocol.** WP6 reads the existing file, appends its rows, writes it back. Duplicates on `(participant_id, strategy_name)` are a validator error.

## 7. WP6 prediction sets

### 7.1 `prediction_sets.parquet`

One row per participant × cumulative_k. Needed for Figure 1 Panel A (|C_α| vs k curves) and for the Mondrian analysis.

| Column | Type | Description |
|---|---|---|
| `participant_id` | str | |
| `night_index` | int32 | |
| `cumulative_k` | int32 | Equals `night_index` |
| `alpha` | float32 | Miscoverage level used (plan §2.3 fixes 0.10) |
| `contains_pre` | bool | True iff `"pre"` is in the prediction set at this k |
| `contains_post` | bool | True iff `"post"` is in the prediction set at this k |
| `set_size` | int8 | Derived: `contains_pre + contains_post`; always 1 or 2 |
| `nonconformity_score_pre` | float32 | `1 − p̂(pre | x)` |
| `nonconformity_score_post` | float32 | `1 − p̂(post | x)` |
| `conformal_quantile` | float32 | Stratum-specific q̂ used to build the set |
| `mondrian_stratum` | str | Stratum assignment |
| `is_synthetic` | bool | |

## 8. WP7 evaluation outputs

### 8.1 `evaluation/metrics.parquet`

Wide table of per-strategy metrics with bootstrap confidence intervals. Grain `(strategy_name, metric_name)`.

| Column | Type | Description |
|---|---|---|
| `strategy_name` | str | |
| `metric_name` | str | One of `"median_tau"`, `"empirical_coverage"`, `"selective_accuracy"`, `"deferral_rate"`, `"iqr_tau"`, `"iqr_tau_convergers_only"`, plus any secondary metrics from plan §3.7 |
| `point_estimate` | float32 | |
| `ci_low` | float32 | BCa 95% lower bound, 10,000 bootstrap iterations (plan §3.6) |
| `ci_high` | float32 | BCa 95% upper bound |
| `n_bootstrap` | int32 | Number of successful resamples (equals target unless a resample is degenerate) |

### 8.2 `evaluation/reliability.parquet`

Per-bin reliability-diagram data for the base classifier (Figure 3). Grain `(bin_low, bin_high)`.

| Column | Type | Description |
|---|---|---|
| `bin_low` | float32 | Left edge of probability bin |
| `bin_high` | float32 | Right edge |
| `predicted_mean` | float32 | Mean of `p_post_ovulatory` in bin |
| `observed_fraction_post` | float32 | Fraction of bin rows with `binary_label == "post"` |
| `n` | int32 | Rows in bin |

## 9. Universal field conventions

- **`participant_id`**: string, see input contract §5.
- **`is_synthetic`**: appears on every output table for traceability. Constant within a file.
- **Null encoding**: parquet native null. No sentinel values like `-1` or `"NA"`.
- **Column order in schemas above**: informational only; parquet is column-addressed. Writers can emit in any order; readers select by name.
- **Dtype drift**: if the writer emits a less-strict dtype than the schema (e.g., `int64` instead of `int32`), that is a warning, not an error. The validator upcasts. Nullability mismatches are errors.

## 10. Versioning and amendments

This contract is v1. Amendments follow `docs/data_contract_v1.md` §9:

1. Justification recorded in the change log below.
2. Schemas updated.
3. Validators updated (`synthetic/validate_contract.py` for input contract; new `synthetic/validate_pipeline.py` for the additional files — write when first amendment lands).
4. Affected synthetic bundles regenerated.
5. Team email before the change lands on main.

### Change log

| Version | Date | Change | Approved by |
|---|---|---|---|
| v1 | 2026-04-23 | Initial pipeline contract covering WP2 preprocessing, WP3 cycle boundaries, universal decision files, tau file, prediction sets, WP7 evaluation outputs. | M. Danioł (pending) |

## 11. Open items (do not block v1)

These are acknowledged gaps that will be filled via amendment rather than held against v1:

1. **Quality flag taxonomy** (`valid_nights.quality_flag`) — the `"ok"` / `"low_signal"` / `"dropout"` categories are placeholders; WP2 picks the operational rule and documents it before week 4.
2. **Confidence-tier → confidence-score map** (`cycle_boundaries.confidence_tier` → `labels.label_confidence`) — the exact mapping (e.g., gold=1.0, silver=0.7, bronze=0.3, charcoal=0.1) waits on the Option-1 endpoint decision and the WP3 protocol doc.
3. **Mondrian stratum label vocabulary** — `decisions.mondrian_stratum` and `prediction_sets.mondrian_stratum` are free-text; vocabulary will be locked once Student 3 picks the 2×2 covariate strata in Milestone 4.
4. **Oracle loss function** — `oracle_global`'s `τ*` learning objective is not yet specified; Student 2's WP5 protocol doc pins this.
5. **Signal-quality heuristic threshold** — the `mean_snr_temp` cutoff is a WP5 hyperparameter; learned on training data and reported in the experiment log.

All five items are documented separately; none of them change any schema column above.
