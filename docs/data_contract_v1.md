# Data Contract v1

**Status:** v1 — synthetic compatibility target; real-data validation deferred to week 2 when mcPHASES preview is available.
**Scope:** the interface between WP2/WP3/WP5 (data, endpoint, base classifier) and WP6 (conformal sufficiency layer).
**Consumers:** Student 3 (WP6) treats the three tables below as her only inputs. Student 4 (WP7) consumes her outputs plus these tables for evaluation.
**Authority:** this contract supersedes ad-hoc schema decisions. Any amendment requires supervisor sign-off and a bump to v2 (see change log at the bottom).

---

## 1. Overview

Three parquet files form the contract:

| File | Grain (unique row key) | Produced by | Consumed by |
|---|---|---|---|
| `probability_table.parquet` | `(participant_id, night_index)` | WP5 (Student 2) | WP6 (Student 3) |
| `labels.parquet` | `(participant_id, night_index)` | WP3 (Student 1) | WP5, WP6, WP7 |
| `covariates.parquet` | `participant_id` | WP2 (Student 1) | WP6, WP7 |

All three are parquet with default compression (`snappy`). The synthetic generator and the real-data pipeline both emit files with these exact schemas. Student 3 never reads raw mcPHASES tables.

---

## 2. Schemas

### 2.1 `probability_table.parquet`

Output of the calibrated base classifier. One row per participant-night.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `participant_id` | str | non-null; appears in `labels.parquet` AND `covariates.parquet` | Opaque participant identifier. Real data: stringified integer id from mcPHASES `subject-info.csv` (e.g., "1", "42"). Synthetic: "P001"–"P042". See §5. |
| `night_index` | int32 | ≥ 1; strictly increasing within `participant_id`; no gaps | 1-indexed position among the participant's valid nights, after the WP2 valid-night filter. Not `day_in_study`. |
| `cumulative_k` | int32 | ≥ 1; equals `night_index` | Number of valid nights observed up to and including this one. Equal to `night_index` by construction (the table contains only valid nights); kept as a separate column for semantic clarity — conformal formulas reference `k`, row identification references `night_index`. |
| `p_post_ovulatory` | float32 | in [0, 1]; non-null | Calibrated posterior for the post-ovulatory class, produced by the base classifier trained under nested LOSO-CV with isotonic calibration on an inner fold (plan §3.2). |
| `fold_id` | int8 | in {0, 1, 2, 3, 4}; constant within `participant_id` | 5-fold grouped CV assignment (fallback if nested LOSO exceeds 24h walltime, plan §3.6). For primary LOSO-CV, use `participant_id` directly as the fold key — no separate LOSO fold column is needed. |
| `is_synthetic` | bool | non-null | `True` for synthetic rows, `False` for mcPHASES-derived rows. All rows within a single file must share the same value. |

**Notes.**
- `p_post_ovulatory` must reflect the classifier's output when trained with participant `participant_id` held out. Leakage is auditable by Student 4 (plan §9.1).
- `p_post_ovulatory` and `1 − p_post_ovulatory` are the two class probabilities fed to APS non-conformity scoring (plan §3.3). Do not clip to (0, 1) — APS handles the endpoints.

### 2.2 `labels.parquet`

Output of the endpoint construction pipeline (WP3). One row per participant-night, same grain as `probability_table.parquet`.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `participant_id` | str | non-null; matches `probability_table.parquet` | See §5. |
| `night_index` | int32 | ≥ 1; matches `probability_table.parquet` | See §2.1. |
| `binary_label` | str | in {"pre", "post"}; non-null | Binary hormone-anchored phase: `"pre"` = pre-ovulatory (before LH surge day); `"post"` = post-ovulatory (LH surge day onward through end of luteal phase), confirmed by ≥2 days of elevated PdG. Reconstructed from raw Mira LH / E3G / PdG values (plan §4.2), not taken from the mcPHASES derived `phase` column. |
| `label_confidence` | float32 | in [0, 1]; non-null | Per-night confidence of the assignment. `0` = ambiguous (e.g., within ±2 days of the LH surge without PdG confirmation, or PdG rise ambiguous); `1` = unambiguous assignment with clear hormonal signature. Not a probability. Used by WP7 for sensitivity analysis (plan §4.2 step 4). |

**Notes.**
- Every `(participant_id, night_index)` in `probability_table.parquet` **must** have exactly one matching row here.
- If >30% of cycle-days fall below a confidence threshold (to be fixed in WP3), escalate to supervisor per plan §4.2 step 5.

### 2.3 `covariates.parquet`

Output of WP2 feature extraction. One row per participant (grain: `participant_id`).

| Column | Type | Constraints | Description |
|---|---|---|---|
| `participant_id` | str | non-null; unique; covers every id in `probability_table.parquet` | See §5. |
| `signal_completeness` | float32 | in [0, 1]; non-null | Proportion of observation-window nights that passed the WP2 valid-night filter. Denominator is the total nights in the participant's Round-1 observation window (or Round-1+Round-2 if applicable). Plan §3.4. |
| `cycle_regular` | bool | non-null | `True` iff the coefficient of variation of the participant's cycle lengths is below a threshold fixed in WP2. If fewer than 2 full cycles are available, defaults to `False` (the conservative choice — treats unknown as irregular). |
| `mean_snr_temp` | float32 | non-null; NaN permitted if `has_temperature` is False | Mean nightly signal-to-noise ratio of skin-temperature readings, averaged over valid nights. Numerator/denominator definition fixed in WP2 (candidate: mean nightly temperature divided by `baseline_relative_nightly_standard_deviation` from `computed_temperature.csv`). |
| `mean_snr_hr` | float32 | non-null; NaN permitted if `has_hr_hrv` is False | Mean nightly SNR of heart-rate / HRV readings, averaged over valid nights. Candidate: derived from `full_sleep_signal_to_noise` in `respiratory_rate_summary.csv` or computed from `heart_rate.csv` confidence values. WP2 chooses one and freezes. |
| `has_temperature` | bool | non-null | `True` iff the participant has ≥1 valid nightly temperature record in `computed_temperature.csv`. |
| `has_hr_hrv` | bool | non-null | `True` iff the participant has ≥1 HRV record in `heart_rate_variability_details.csv` AND ≥1 continuous HR record in `heart_rate.csv`. |
| `has_cgm` | bool | non-null | `True` iff the participant has ≥1 glucose record in `glucose.csv`. |
| `has_self_report` | bool | non-null | `True` iff the participant has ≥1 daily-survey response in `hormones_and_selfreport.csv` with at least one Likert item populated. |
| `has_round_2` | bool | non-null | `True` iff the participant has ≥1 row with `study_interval == 2` in the mcPHASES source (Interval 2 = July–October 2024). Plan §4.1 implies 20 of 42 participants. |

**Notes.**
- Every `participant_id` that appears in `probability_table.parquet` **must** have a row here.
- If a covariate is genuinely unknown for a participant (e.g., regularity with <2 cycles observed), use the conservative default documented in the column description rather than `NaN`. The `has_*` flags are the only mechanism for "modality not present."

---

## 3. Rationale — why these columns and no others

This contract is the narrowest interface that lets WP6 produce every deliverable listed in plan §6 (sufficiency curves, τᵢ estimation, Mondrian conformal with covariate strata, regression meta-model for τᵢ, decision policy). Each column earns its place:

| Column(s) | WP6 use | Plan reference |
|---|---|---|
| `probability_table.p_post_ovulatory` | Base input for APS non-conformity scores `s(x,y) = 1 − p̂(y\|x)` | §3.3 step 1 |
| `probability_table.cumulative_k` | Independent variable for \|C_α\| vs. k curves (Figure 1) | §1.4, §6 step 3 |
| `labels.binary_label` | Target for calibration/evaluation; defines whether C_α contains the true label | §3.1, §3.7 |
| `labels.label_confidence` | Sensitivity analysis (WP7 analysis J: endpoint definitions) | §4.2 step 4 |
| `covariates.signal_completeness` | Primary covariate for Mondrian stratification; leading candidate predictor of τᵢ | §3.4 bullet 1, §3.4 regression meta-model |
| `covariates.cycle_regular` | Mondrian stratum; regularity → faster convergence hypothesis | §3.4 bullet 2 |
| `covariates.mean_snr_temp`, `mean_snr_hr` | "Nocturnal signal quality" covariate | §3.4 bullet 4 |
| `covariates.has_temperature`, `has_hr_hrv`, `has_cgm`, `has_self_report` | Modality availability covariates; used in modality-ablation sensitivity (WP7 analysis K) | §3.4 bullet 3, plan §8 row K |
| `covariates.has_round_2` | Longitudinal transfer (Figure 4); identifies the n=20 subset | §3.6, §6 step 8 |
| `probability_table.fold_id` | 5-fold grouped CV fallback if nested LOSO >24h | §3.6 |
| `*.is_synthetic` | Lets Student 3 run identical code against synthetic and real inputs without renaming | WP1 amendment §3 (changelog) |

Columns NOT in the contract and why:
- **Raw features** (skin temperature, HR, HRV, glucose, etc.) live in WP2 pipeline state and never cross this boundary. Student 3 works with the probability output only (plan §3.2: "Student 2 builds the base classifier; Student 3 builds the sufficiency layer on top").
- **Raw hormone values** (LH, E3G, PdG) live in WP3 pipeline state. Student 3 sees only `binary_label`.
- **Cycle identifiers** (cycle number, day-within-cycle) are out of scope for WP6; the sufficiency model operates on cumulative nights regardless of cycle boundaries.
- **Demographic fields** (age, ethnicity, education from `subject-info.csv`) are not on the covariate list in plan §3.4 and are not covariates of interest for sufficiency. Adding them would be scope creep.

---

## 4. Referential integrity rules

Enforced by `synthetic/validate_contract.py` and (from week 2) by the real-data pipeline's tests:

1. **`probability_table` ⊆ `labels` on (participant_id, night_index).** Every probability row has a matching label row. One-to-one, not one-to-many.
2. **`probability_table.participant_id` ⊆ `covariates.participant_id`.** Every participant with predictions has a covariate row.
3. **`covariates.participant_id` is unique.** No duplicate participant rows.
4. **`night_index` is dense per participant in `probability_table`.** For a given participant, `night_index` starts at 1 and increases by 1 with each row; no gaps.
5. **`fold_id` is constant within `participant_id`.** A participant belongs to exactly one fold.
6. **`is_synthetic` is constant within a file.** All rows in a given parquet are either synthetic or real; the three files in a bundle share the same value.
7. **Row counts:** no upper bound on rows per participant, but `5 ≤ nights_per_participant ≤ 200` is the expected range (mcPHASES observation windows are ~90 days × ≤1 valid night/day; synthetic uses 25–40).

A contract violation is a hard failure. The validator exits non-zero and prints the first offending rows.

---

## 5. Participant ID convention

Opaque string. Two formats coexist:

- **Real (mcPHASES):** `str(id)` where `id` is the integer from `dataset/subject-info.csv` — e.g., `"1"`, `"42"`, `"50"`. IDs are not contiguous (the integers 5, 17, 21, 25, 28, 31, 35, 36 are absent from the 42-participant cohort; this is upstream, not our doing).
- **Synthetic:** `"P001"` through `"P042"`, zero-padded.

The `is_synthetic` flag disambiguates. Consumer code treats `participant_id` as opaque and uses `is_synthetic` (not string shape) when behavior must differ.

---

## 6. Valid-night definition — deferred to WP2

This contract assumes "valid night" is a frozen, documented rule owned by WP2 (plan §4.3: proposed ≥4 hours of continuous Fitbit recording during 22:00–06:00). Until WP2 publishes the final rule:

- The synthetic generator treats every simulated night as valid.
- The real-data pipeline applies the WP2 rule before emitting `probability_table` and `labels`.
- `covariates.signal_completeness` is computed against the same rule.

If the WP2 definition changes, all three files are regenerated; there is no partial re-derivation.

---

## 7. Known open items

Tracked here for visibility. Resolution does not block v1.

1. **SNR definitions.** `mean_snr_temp` and `mean_snr_hr` have candidate definitions (see §2.3) but are not frozen. WP2 picks one formula per column and documents it before week 4.
2. **`cycle_regular` threshold.** The plan mentions CV-of-cycle-length without specifying a cutoff. WP2 picks a value (literature candidate: CV < 0.10) and documents it.
3. **`label_confidence` scale.** Step-function or continuous — to be specified in WP3 (plan §4.2 step 4).
4. **Round 2 observation window.** For `has_round_2 == True` participants, whether `night_index` spans both rounds contiguously or resets at the round boundary. Defaulting to "contiguous across rounds" for now; WP3 may override.

### Modalities deliberately excluded

The plan's §3.2 lists "EDA tonic level" as a base-classifier feature. mcPHASES v1.0.0 ships no EDA table (see `dataset/README.txt`), so EDA is excluded from both the feature set and the covariates. The modality flag `has_eda` is **not** in the schema. If a future mcPHASES release adds EDA, this is a v2 amendment, not an error in v1.

---

## 8. Synthetic compatibility

`synthetic/generator.py` and `synthetic/validate_contract.py` are the reference implementation of this contract. If the generator's output and a real-data output differ in schema, the real data is wrong (not the contract), and WP2/WP3/WP5 must reconcile.

The generator produces visibly heterogeneous τᵢ across participants — the paper's central empirical claim — so that WP6 can develop against outputs with the same structural properties the real data is expected to have.

---

## 9. Change log

| Version | Date | Change | Approved by |
|---|---|---|---|
| v1 | 2026-04-22 | Initial contract; synthetic compatibility target. | M. Danioł (pending) |

Amendments require:
1. A short justification in this table.
2. Updated sections in this document.
3. Updated `synthetic/validate_contract.py`.
4. A regenerated `synthetic/v1/` bundle, OR a new `synthetic/v2/` bundle if the break is non-trivial.
5. Slack/email notice to all four students before the change lands on main.
