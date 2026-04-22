# Hero Figure Specification — Figure 1

**This amends research plan v4.0 §1.4.** The plan's Figure 1 was a single-panel "problem figure" showing that sufficiency thresholds vary across users. During WP1 we concluded that is the wrong headline: it states the problem but not the contribution. The new Figure 1 is a three-panel **contribution figure** — individual sufficiency curves (Panel A), decision timelines under three strategies (Panel B), and τᵢ as a function of a leading covariate with Mondrian strata (Panel C).

Plan §9.2 requires any scope change after WP1 be signed off by supervisor and logged in the changelog. This amendment is logged in `docs/plan_v4.1_changelog.md` item 2.

---

## Panel A — Individual sufficiency trajectories

**What it shows.** The reason evidence sufficiency varies across individuals.

**Axes.**
- **X:** cumulative valid nights k, from 1 to max(N_i). Linear. Tick at 1, 5, 10, 15, 20, 25, 30.
- **Y:** uncertainty signal, in the same units as |C_α| for the plotted α=0.10 level. Y=1 means "singleton prediction set"; Y=2 means "both classes still plausible." Horizontal reference line at Y=1 (the sufficiency threshold).

**Curves.** One curve per participant shown, covering the full n=42 cohort but with differential emphasis:

- **Two hero curves** colored prominently (fast-converging participant, slow-converging participant) and annotated with their τᵢ values — these carry the narrative.
- **One non-converger** plotted with a dashed style and a labelled terminal state ("no convergence within observation window").
- **Remaining ~39 curves** as a faded background spaghetti, colored by convergence quartile on a sequential colormap (fast = dark blue; slow = light blue). Faded alpha (~0.25) so the hero curves read cleanly.

**Reference lines.**
- Vertical dashed lines at k=3, k=5, k=7 — the Fixed-3, Fixed-5, Fixed-7 baselines from plan §3.5. Labelled.

**Caption cue.** "Sufficiency threshold τᵢ = smallest k such that |C_α|=1 for 2 consecutive nights (plan §2.3). Horizontal line at |C_α|=1 marks the sufficiency level at α=0.10. Vertical lines mark fixed-rule baselines. Two hero trajectories (fast/slow) and one non-converger are labelled."

---

## Panel B — Decision timelines under three strategies

**What it shows.** The cost of fixed rules relative to the oracle and the covariate-conditional policy, on real example participants.

**Layout.** A 4×3 grid of miniature timelines. Rows = 4 representative participants (a fast converger, a slow converger, a non-converger, an average-case participant). Columns = 3 strategies:

1. **Fixed-5** — baseline (plan §3.5).
2. **Oracle global threshold** — single learned τ* minimizing expected loss on training set (plan §3.5, row "Oracle global threshold"). This is "the best anyone can do without adaptation."
3. **Covariate-conditional** — our proposed decision policy.

Each cell is a horizontal strip with one square per night. Square color encodes the per-night decision state:

- **Collect / defer** — light grey
- **Predict, correct** — dark green
- **Predict, incorrect** — dark red

**Row labels (left margin):** participant pseudonym ("Fast (P017)", "Slow (P024)", "Non-converger (P003)", "Average (P031)") and their τᵢ. The specific pseudonyms/IDs come from the week-8 results pass, not week 1.

**Column labels (top):** strategy name + summary metric across the 4 rows (e.g., "Fixed-5 — 3/4 correct, 0 defers, 12 wrong nights").

**Hard rule.** Correctness in Panel B comes from Student 4's actual LOSO-CV evaluation on real data. This panel is not generated from simulation, from synthetic data, or from any optimistic projection. If the panel is drawn before the real-data evaluation is complete, it is a placeholder and must be labelled as such in any draft.

---

## Panel C — τᵢ vs. a leading covariate

**What it shows.** That τᵢ is predictable from observable signal characteristics — the basis for the covariate-conditional model.

**Axes.**
- **X:** the covariate with the strongest association to τᵢ in Student 3's regression meta-model. **Placeholder:** `signal_completeness` (plan §3.4 bullet 1). The specific covariate is chosen during WP6 week 6–7 based on the regression meta-model's standardized coefficients. Candidates: `signal_completeness`, `mean_snr_temp`, `mean_snr_hr`, `cycle_regular` — see data contract §2.3.
- **Y:** τᵢ in nights. Non-convergers marked at the top of the plot (or with a broken-axis marker labelled "no convergence").

**Marks.**
- **Per-participant scatter:** one marker per participant (n=42), shaded by density if points overlap heavily.
- **Mondrian stratum means** plotted as **large diamonds** — one per stratum (plan §3.4, "Mondrian conformal prediction stratified by covariate groups"). Strata are the covariate groups used in Student 3's Mondrian conformal prediction (e.g., high/low signal completeness × regular/irregular cycles). Stratum labels printed next to each diamond.
- **Horizontal reference lines** at τ=3, τ=5, τ=7 — the Fixed-3, Fixed-5, Fixed-7 baselines, to let readers read "this covariate group beats Fixed-5 on median, that one does not" directly off the figure.

**Caption cue.** "τᵢ decreases with [covariate]. Diamonds show Mondrian stratum means (sample sizes annotated). Horizontal lines mark fixed-rule baselines. Non-convergers shown above the break."

---

## Figure-wide requirements

- **Format:** vector (PDF or SVG). Embedded fonts. Colour-blind-safe palette (viridis / cividis for sequential; ColorBrewer RdYlGn for binary decision states in Panel B).
- **Dimensions:** two-column width at target venues (≈7 inches wide). Height ≈ 5 inches to preserve Panel B's vertical grid.
- **Typography:** a single sans-serif family used throughout. Panel letters (A, B, C) in the upper-left of each panel, bold, same size as axis titles.
- **Caption budget:** ≤ 120 words. See plan §12.1 (4,000–5,000 word paper budget).
- **Panel-to-panel consistency:** same colours for "correct", "incorrect", "defer" across B and C where applicable. Same τᵢ values referenced in A must match Panel C's scatter.

---

## Pre-final QA checklist

Before submission, Figure 1 is signed off against this list:

- [ ] Panel A hero curves and non-converger labels match the actual computed τᵢ values (no round-number cherry-picks).
- [ ] Panel B states are derived from `prediction_sets.parquet` and `labels.parquet` under LOSO-CV, not any other source.
- [ ] Panel C's covariate is the one identified by the regression meta-model, not a visually-pleasing placeholder.
- [ ] Caption uses "empirical coverage" — never "guaranteed coverage."
- [ ] Caption uses "covariate-conditional" — never "personalized."
- [ ] Figure reproducible from `src/` with a single command (plan §9.3).
