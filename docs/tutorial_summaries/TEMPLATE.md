# Tutorial Summary — Angelopoulos & Bates (2021)

**Paper.** Angelopoulos, A. N., & Bates, S. (2021). *A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification.* arXiv:2107.07511.

**Why this summary exists.** Every student on this project reads the same conformal-prediction primer in week 1 and writes a one-page summary against the same three questions. The summaries are how the supervisor confirms that the team has a shared mental model before WP6 code is written, and how each author builds a paragraph they can defend in the Methods section.

**Instructions.**
1. Read Sections 1–3 of the paper (skim the rest).
2. Copy this file to `docs/tutorial_summaries/<your_name_or_student_index>_angelopoulos_bates.md`.
3. Answer each question in one paragraph. Not one sentence, not three — a single, self-contained paragraph per question.
4. Cite back to the paper with `(§X.Y)` or `(Eq. N)` references where useful.
5. Sign and date at the bottom.
6. Submit by Day 1 end-of-day (for Student 3 on the fast-track) or by end of week 1 (everyone else).

---

## 1. What does split conformal prediction formally guarantee?

> *(One paragraph. State the guarantee precisely — the theorem's marginal coverage statement for a new exchangeable test point at a chosen miscoverage level α. Make clear whether coverage is marginal or conditional, and what population the guarantee is over. Reference the relevant construction (calibration set → non-conformity scores → quantile → prediction set). Cite the paper's equation or section.)*

## 2. What assumption does the guarantee depend on?

> *(One paragraph. Name the exchangeability assumption precisely — what it says about the joint distribution of the calibration and test points, what weaker conditions would be insufficient, what stronger conditions are not required. Note the connection to i.i.d. data as a sufficient special case. Be explicit that this is a property of the joint distribution, not of any single observation.)*

## 3. Why is that assumption only approximately satisfied in our setting?

> *(One paragraph. Ground this in our specific temporal-wearable setting. Discuss at least: (a) sequential accumulation of observations within a cycle violates exchangeability at the cycle level; (b) consecutive nights are autocorrelated, so even within a participant observations are not exchangeable; (c) the test scenario — a partial cycle from a new user — differs structurally from the calibration scenario (complete cycles from other users), which is a distribution-shift issue on top of the exchangeability failure. Cite plan §2.4 and Stocker et al. 2025. Close with the consequence: we report empirical coverage, validated via LOSO-CV, not formal coverage guarantees.)*

---

## Declaration

I have read Sections 1–3 of Angelopoulos & Bates (2021) and written the above in my own words. I understand that the paper's claim is a *marginal empirical coverage* validated via LOSO-CV, not a formal conformal guarantee, and I will not describe the claim using the word "guarantee" in any draft, plot, or commit message.

| Field | Value |
|---|---|
| Name | ______________________________ |
| Student role / WP | ______________________________ |
| Date | __________________ |
| Signature | ______________________________ |
