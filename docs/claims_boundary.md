# Claims Boundary

> **Scope.** The five boundaries below apply to **every output** of the project — conference paper / poster (deadline 2026-05-07), journal-paper version, and any intermediate writeup.

**Purpose.** Single reference for what the paper does and does not claim. Read once before writing any abstract, figure caption, or commit message. When a draft overclaims, the supervisor points at this page.

**Authority.** Derived from research plan v4.0 §1.2 ("Boundary of claims").

---

## What we do NOT claim

### 1. This is not clinical validation.

We demonstrate a methodological framework on a single publicly available dataset. Clinical validation requires prospective studies on multiple independent cohorts, regulatory registration, and outcome data over months to years. We have none of these. Any paragraph that reads as if a clinician could act on our output is wrong and must be rewritten.

### 2. All claims are conditional on a single dataset (mcPHASES, n=42).

mcPHASES v1.0.0 (Lin et al. 2026) is one dataset, one device family (Fitbit Sense + Dexcom G6 + Mira Plus), one population (young Canadian adults). Signal characteristics, adherence patterns, and cycle distributions from a different cohort could move every number in the paper. We report results *at the resolution of mcPHASES* — not as population-level estimates.

### 3. We do not claim formal conformal coverage guarantees.

Split conformal prediction provides distribution-free coverage under exchangeability (Vovk et al. 2005). In a temporal wearable setting, the assumption is violated: observations accumulate sequentially within a cycle, consecutive nights are autocorrelated, and a test scenario (partial cycle from a new user) differs structurally from the calibration scenario (complete cycles from other users). Stocker et al. (2025) is explicit about this. **We report empirical coverage, validated via LOSO-CV.** Anywhere the word "guaranteed" appears next to "coverage" in a draft, it is wrong.

### 4. We do not claim individual-level personalization.

At n=42, individual-level adaptation is not statistically defensible. What we do is adjust the sufficiency threshold based on observable covariates (signal completeness, cycle regularity, modality availability, nocturnal signal quality) — which is what a real product would do during onboarding, before knowing anything about the specific user. **We call this covariate-conditional sufficiency estimation.** "Personalized" is a word with a specific statistical meaning that we cannot earn at this sample size, and the ethics literature we cite (Punzi & Thuis 2025) calls out exactly this kind of overclaim.

### 5. This is not contraception guidance and must not be interpreted as such.

No reader — reviewer, clinician, or consumer — should come away thinking any output of this system is safe to use as a contraceptive signal. Mira Plus urinalysis is not blood-draw quality (plan §8 Limitations). Hormone ground truth has uncertainty. Inference is retrospective. Framing as decision support for contraception is medically and ethically off-limits.

---

## What we DO claim

A principled framework for evidence sufficiency that produces safer wearable menstrual-phase inference than fixed-window rules, with empirical evidence that the sufficiency threshold varies meaningfully across users in ways predictable from observable signal characteristics. That is the paper. That is enough.

---

## Non-negotiable language rules

These three phrases come from plan §2.4, §3.4, and §9.2. They appear verbatim in the charter and onboarding for Student 3 because Student 3 builds the layer that most tempts overclaim. Everyone else holds the same line.

1. **Empirical coverage, not formal conformal coverage guarantees.** Always write "empirical coverage, validated via LOSO-CV" (plan §2.4; Stocker et al. 2025).
2. **Covariate-conditional sufficiency estimation, not individual-level personalization.** Always write "covariate-conditional" (plan §3.4).
3. **Mondrian conformal + APS + regression meta-model. No new methods.** Scope-creep requests go to supervisor (plan §9.2).

If a team member catches a slip in another team member's draft, the correction happens immediately — not at the end of WP8. This is an in-group norm, not a supervisor-only duty.

---

## How this document is enforced

No signing ceremony. The boundaries above are enforced through (a) supervisor review of every abstract, figure caption, and Discussion paragraph before submission, and (b) team members catching slips in each other's drafts. Anyone can flag a violation; the response is a quick edit, not a meeting.
