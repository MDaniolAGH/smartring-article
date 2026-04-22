# Gap Statement — Verbatim from Plan v4.0 §2.2

This paragraph is the paper's novelty anchor. It must be writable before WP5 begins (plan §2.2 header). It is reproduced here verbatim and tracked for citation verification; any edit to the paragraph requires a v4.1 amendment to the plan.

---

> Existing work on menstrual phase classification from wearable data evaluates predictive accuracy assuming data completeness or after excluding cycles with missing data (Goodale et al. 2019; Kilungeja et al. 2025; Masuda et al. 2025; Thigpen et al. 2025). None addresses a prior question: how many observation nights are sufficient for a specific individual before a prediction should be made at all? This omission matters because (a) wearable health products must decide during onboarding when to deliver a first prediction, (b) real-world adherence varies across users, and (c) regulatory frameworks for software as a medical device increasingly require uncertainty quantification under data limitations (EU MDR 2017/745). In sleep research, Lau et al. (2022) showed that the number of actigraphy nights needed for reliable estimates varies by metric, establishing a minimum-data precedent that has not been transferred to menstrual inference. In machine learning, selective prediction (Swaminathan et al. 2024) and conformal prediction (Romano et al. 2020) provide formal tools for abstention-aware classification. Punzi and Thuis (2025) have raised ethical concerns about algorithmic overconfidence in fertility tracking, motivating mechanisms that allow the system to say "I don't know yet." This study bridges these strands.

---

## Citation audit

Every citation in the paragraph above is listed below. Until an entry is marked **VERIFIED** by a student who has read the cited paper and confirmed the paragraph's claim against the paper's content, that citation is load-bearing but unchecked. **Verification is a week-2 task.**

Assigned reviewer (from plan §4 "Required citations by role"): S = student index owning the domain.

| # | Citation | Claim anchored in gap statement | Status | Reviewer | Notes |
|---|---|---|---|---|---|
| 1 | Goodale et al. 2019 | Prior work evaluates accuracy assuming data completeness or excluding cycles with missing data | UNVERIFIED | S1 (dataset/endpoint) | Referenced in plan §4 row "Background." Confirm: does Goodale et al. exclude missing-data cycles? |
| 2 | Kilungeja et al. 2025 | Same as above; and dataset overlap — Kilungeja used mcPHASES | UNVERIFIED | **S2 (direct comparator)** — **HIGH PRIORITY** | Same dataset as this study. The plan §2.5 differentiation table must be verified line-by-line against Kilungeja et al.'s actual methods, outputs, endpoints, and evaluation — not against what we assume they did. If the table is wrong, the novelty claim is wrong. Block all other work on this citation until verified. |
| 3 | Masuda et al. 2025 | Prior work evaluates accuracy assuming data completeness | UNVERIFIED | S2 (direct comparator) | Referenced in plan §4 row "Direct comparators." |
| 4 | Thigpen et al. 2025 | Same; published in JMIR mHealth (our target venue) | UNVERIFIED | S2 (direct comparator) | Referenced in plan §1.5 target venues and §4. |
| 5 | Lau et al. 2022 | Sleep-research precedent for per-metric minimum-data thresholds | UNVERIFIED | S3 (abstention/sufficiency framing) | Confirm: does Lau et al. 2022 actually vary the number-of-nights threshold by metric, or is this an inference? |
| 6 | Swaminathan et al. 2024 | Selective prediction as formal tool for abstention | UNVERIFIED | S3 (abstention/sufficiency framing) | |
| 7 | Romano et al. 2020 | APS (Adaptive Prediction Sets) as the conformal method used | UNVERIFIED | S3 (methods) | Method reference, not a claim-support citation. Confirm algorithm details match plan §3.3. |
| 8 | Punzi & Thuis 2025 | Ethics of algorithmic overconfidence in fertility tracking, motivating "I don't know yet" | UNVERIFIED | S3 (abstention/sufficiency framing) | Confirm: does this paper explicitly call for abstention mechanisms, or is it a general ethics critique? |
| 9 | Vovk et al. 2005 | Conformal prediction distribution-free guarantee under exchangeability (referenced in plan §2.4) | UNVERIFIED | S3 (methods) | Foundational. Referenced in claims boundary §3. |
| 10 | Stocker et al. 2025 | Caution against naive application of conformal prediction to temporally dependent data | UNVERIFIED | S3 (methods) | Load-bearing for the "we report empirical coverage" disclaimer in plan §2.4. If Stocker et al. does not actually make this caution explicit, the disclaimer needs a different anchor. |
| 11 | Lin et al. 2026 | mcPHASES dataset paper | UNVERIFIED | S1 (dataset/endpoint) | Base reference. Confirm citation details (venue, authors, year) against the PhysioNet dataset page. |

Additional citations in plan §4 that do not appear in the gap statement but that the paper cites elsewhere (for completeness): Lyzwinski et al. 2024, Shi et al. 2026, Wang et al. 2025. These are tracked in the literature matrix (plan §4 row "Background"), not here.

---

## Workflow

1. By end of week 2: every row in the table above is either **VERIFIED** (with a one-sentence note confirming the paper supports the claim) or **BROKEN** (with a note on what is actually in the paper versus what we said).
2. Any **BROKEN** row triggers a revision of the gap paragraph (not the other way around — we do not bend the paragraph to fit a citation).
3. Kilungeja et al. 2025 (row 2) is the single citation most capable of sinking the paper. If the plan §2.5 differentiation table is wrong, we either rewrite it or drop the paper and change venue. The student assigned to S2 does this verification first.
4. The verified table at end of week 2 is attached to the Introduction draft (plan §8, WP8 delivery) as the citation-support log.
