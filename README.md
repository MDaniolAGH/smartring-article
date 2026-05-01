# How Much Data Is Enough?

**Abstention-aware menstrual cycle inference from wearable sensors** — a conformal-prediction framework with reject option, built on the [mcPHASES](https://physionet.org/content/mcphases/1.0.0/) dataset.

---

## Status

- **Conference deadline: 2026-05-07** — student conference. Scope: Round-2 subcohort (n≈19), one figure, one comparison table.
- **Journal target: weeks 8–12 of plan v4.0** — JMIR mHealth, npj Women's Health, J Biomedical Informatics. Full cohort (n=42), full method.

The conference version is a focused subset of the journal version. Both share the same code, contracts, and pipeline.

---

## Start here

### If you are joining the team

1. **Read the onboarding note** (Polish): [`docs/notatka_dla_zespolu_pl.md`](docs/notatka_dla_zespolu_pl.md). It is the single document the whole team reads first. It explains the method, lists what is in the repo, gives a procedure for the first two hours of work, and lists per-role tasks for the May 7 deadline.
2. **Set up the environment** (commands below).
3. **Run two notebooks** to confirm everything works:
   - `notebooks/00_getting_started.ipynb` — orientation
   - `notebooks/06_dataset_loading.ipynb` — the unified data loader
4. **Open the notebook for your role**:
   - `01_wp2_preprocessing.ipynb` — preprocessing, valid-night filter, cohort, LOSO folds
   - `02_wp3_endpoint.ipynb` — hormone-anchored endpoint, tiered-confidence labels
   - `03_wp5_baselines.ipynb` — base classifier + fixed-rule baselines
   - `04_wp6_conformal.ipynb` — conformal prediction (the paper's core contribution)
   - `05_wp7_evaluation.ipynb` — metrics, bootstrap CIs, calibration

You should not need to read every document in `docs/` to start. The notebooks point you at the docs you need when you need them.

### Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python synthetic/generator.py --out synthetic/v1 --seed 42 --validate
```

The third command verifies the install: it generates the synthetic bundle and runs the contract validator. Exit 0 means everything is wired correctly.

For real data, see "Data" below.

---

## Repository layout

```
README.md                       This file
research_plan_v4.pdf            Project plan (frozen; amendments in docs/plan_v4.1_changelog.md)
requirements.txt                Pinned Python dependencies

docs/                           Documentation
  notatka_dla_zespolu_pl.md     Polish onboarding note (start here)
  data_contract_v1.md           Schemas of the three input parquet files
  pipeline_contract_v1.md       Schemas of every parquet file in the pipeline
  student3_charter.md           Conformal-prediction role specification
  onboarding_student3.md        Milestone-ordered plan for the conformal role
  claims_boundary.md            What we claim and what we do not claim
  gap_statement.md              Literature gap + citation audit
  hero_figure_spec.md           Figure 1 design (three panels)
  plan_v4.1_changelog.md        Amendments to the frozen plan
  tutorial_summaries/           Conformal-prediction tutorial template
  s44294-025-00078-8.pdf        Kilungeja et al. 2025 (direct comparator)
  s41597-026-06805-3-1.pdf      Lin et al. 2026 (mcPHASES dataset paper)

notebooks/                      Per-role starter notebooks (all run end-to-end)
  00_getting_started.ipynb      Environment + data_table + peek/summary helpers
  01_wp2_preprocessing.ipynb    Preprocessing pipeline starter
  02_wp3_endpoint.ipynb         Endpoint construction starter
  03_wp5_baselines.ipynb        Base classifier + baselines starter
  04_wp6_conformal.ipynb        Conformal sufficiency layer (working reference)
  05_wp7_evaluation.ipynb       Evaluation harness starter
  06_dataset_loading.ipynb      Unified data loader tutorial
  07_convert_dataset.ipynb      One-off raw-CSV → parquet conversion (Colab-friendly)

utils/                          Library code
  dataset.py                    load_mcphases() — the team-wide data loader
  preview.py                    peek() and summary() helpers

synthetic/                      Synthetic data generator + validator
  generator.py                  Deterministic synthetic bundle (seed=42)
  validate_contract.py          Schema and referential-integrity validator
  v1/                           Generated bundle (committed; regression test fixture)

scripts/
  convert_raw_to_parquet.py     One-off raw-CSV → parquet conversion (Colab-friendly)

src/                            Real-pipeline production code (populated as WPs progress)
tests/                          Test suite (populated alongside src/)

dataset/                        mcPHASES raw CSVs (gitignored — see Data below)
dataset_parquet/                Parquet conversions of large CSVs (gitignored)
```

---

## Data

The mcPHASES dataset is on PhysioNet under the **Restricted Health Data License**. Each team member must obtain their own access through the PhysioNet project page; the data **must not be redistributed**.

**Place raw CSVs in `dataset/`, then convert the large ones once. Two ways to run it:**

- **Locally (CLI):** `python scripts/convert_raw_to_parquet.py`
- **On Colab (recommended):** open `notebooks/07_convert_dataset.ipynb`, edit the `DATASET_DIR` line if your Drive path differs, run all cells.

Both produce `dataset_parquet/` — ~340 MB of compressed parquet (down from 3.4 GB of CSV) for the nine files >10 MB. Smaller CSVs stay as CSV. The conversion runs in ~30 seconds on a laptop, 1–2 minutes on Colab, and is idempotent (re-running skips already-converted files; pass `--force` to rebuild).

After conversion, `utils/dataset.py` finds the parquet copies automatically. Loading the raw `heart_rate.csv` (1.9 GB) directly will exceed Colab's free-tier RAM — that's the whole reason this conversion step exists.

`dataset/` and `dataset_parquet/` are gitignored.

---

## Loading data — one pattern for everyone

```python
from utils.dataset import setup, load_mcphases

setup()                  # mounts Google Drive on Colab; no-op locally
data = load_mcphases()   # auto-detects path; loads small tables eagerly

hormones = data['hormones_and_selfreport']     # small table
hr_p18 = data.load('heart_rate',
                   participant_id=18,
                   columns=['day_in_study', 'bpm'])  # large; columns + filter pushed to disk
```

The loader normalizes column names to lowercase and renames `id` to `participant_id` to match the pipeline contract. Full walkthrough in `notebooks/06_dataset_loading.ipynb`.

---

## Three rules that appear in every draft

These are non-negotiable. They appear verbatim in the role charters and the claims boundary because the most common reviewer attack is a sloppy claim about coverage or personalization.

1. **"Empirical coverage, validated via LOSO-CV"** — never "conformal guarantees coverage."
2. **"Covariate-conditional sufficiency estimation"** — never "individual-level personalization."
3. **No new methods.** Mondrian conformal + APS + a regression meta-model is the entire methodological toolkit. Scope-creep requests go to the supervisor.

---

## Authoritative documents

When two documents disagree:

- `docs/pipeline_contract_v1.md` wins on file schemas
- `docs/plan_v4.1_changelog.md` wins over `research_plan_v4.pdf` (the PDF is frozen)
- `docs/claims_boundary.md` wins on what we say in the paper

---

## Reproducibility

- Single command per result. Seeds fixed.
- LOSO folds frozen once in WP2, never re-split.
- Synthetic bundle (`synthetic/v1/`) committed and used as a regression fixture.
- Conference-version reproducibility package shipped at submission time.

The PhysioNet license forbids redistributing data, so reproducing the *real* results requires the consumer to register and download mcPHASES themselves. Reproducing on synthetic data needs only this repository plus `requirements.txt`.

---

## Asking for help

Technical questions (something does not run, an error message, a path issue) go to whichever async channel the team uses. Methodological questions (whether to add a method, how to interpret a result, how to frame a claim) go to the supervisor before any code is written.

The most common first-day issues and their fixes are at the bottom of `docs/notatka_dla_zespolu_pl.md`.
