"""Synthetic data generator for the WP6 conformal-sufficiency pipeline.

Emits three parquet files matching ``docs/data_contract_v1.md``:

* ``probability_table.parquet`` — calibrated posteriors per participant-night
* ``labels.parquet`` — binary hormone-anchored phase labels + per-night confidence
* ``covariates.parquet`` — participant-level features

The synthetic suite is Student 3's permanent regression-test harness. It lets
WP6 development begin before Students 1 and 2 deliver the real pipeline, and
after real data arrives it distinguishes "my code is wrong" from "the real
data looks different." Do not delete it.

Simulation model (plan v4.0 §3.3–§3.4)
--------------------------------------
For each of 42 participants:

1. A latent signal_strength ~ Beta(2, 2) on [0, 1] is mapped geometrically to
   an effective logit slope s ∈ [0.02, 2.5]. High s = sharp pre/post separation
   = fast convergence (small τᵢ); low s = diffuse separation = slow or no
   convergence within the observation window. The geometric (not linear)
   mapping keeps the weak-signal tail genuinely weak, which is what produces
   the non-convergers that hero-figure Panel A calls for.
2. A hidden ovulation-onset night ov ~ Uniform{12, …, 18}. Nights are
   1-indexed over the participant's valid-night series.
3. For each night k ∈ {1, …, N_i} with N_i ~ Uniform{25, …, 40}:

     logit_k = s · (k − ov) + ε_k,   ε_k ~ N(0, σ_obs)
     p_post(k) = sigmoid(logit_k)

   σ_obs is a small constant (0.35) so the raw posterior is stably interpretable
   but not deterministic. The Beta signal_strength — not the noise — is the
   primary driver of heterogeneity in τᵢ.

4. Labels are sampled ``Bernoulli(p_post(k))``. This makes p_post calibrated
   *by construction*: across rows where p_post ≈ q, the empirical fraction of
   "post" labels equals q in expectation. Sampled labels align with the
   deterministic rule 1[k ≥ ov] everywhere the signal is clean, and are genuinely
   ambiguous in a ±2-night window around ov — which is exactly the behaviour
   plan §4.2 step 4 calls out for ``label_confidence``.

5. ``label_confidence`` = 2 · |p_post − 0.5|. Near the boundary this goes to
   zero (ambiguous); away from the boundary it saturates to one.

6. ``signal_completeness`` is a noisy monotone function of signal_strength,
   targeting Pearson r ≈ 0.6 per plan §3.4 bullet 1.

7. ``cycle_regular`` is Bernoulli(0.7).

8. ``mean_snr_temp`` and ``mean_snr_hr`` are noisy monotone functions of
   signal_strength (cleaner signal ↔ higher SNR), scaled to roughly [1, 5].

9. Modality flags (``has_temperature``, ``has_hr_hrv``, ``has_cgm``,
   ``has_self_report``) are Bernoulli(0.9). Per data contract §2.3 EDA is
   excluded — mcPHASES v1.0.0 ships no EDA table.

10. ``has_round_2`` is True for exactly 20 of 42 participants (plan §4.1).

11. ``fold_id`` = ``int(md5(participant_id)) % 5`` — stable across Python
    sessions, unlike the built-in ``hash``.

The generator produces visibly heterogeneous τᵢ across participants — the
paper's central empirical claim — so that WP6 code developed on synthetic
inputs exercises the same machinery the real data will require.

Usage
-----
::

    python synthetic/generator.py --out synthetic/v1 --seed 42
    python synthetic/generator.py --out synthetic/v1 --seed 42 --validate

Run with ``--validate`` to chain ``validate_contract.py`` automatically.
"""

from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


N_PARTICIPANTS = 42
MIN_NIGHTS = 25
MAX_NIGHTS = 40
OV_LOW = 12
OV_HIGH = 18
N_ROUND_2 = 20
OBS_NOISE_SIGMA = 0.45
SLOPE_MIN = 0.02
SLOPE_MAX = 2.5
MODALITY_PRESENT_PROB = 0.9
REGULAR_PROB = 0.7


@dataclass(frozen=True)
class Participant:
    pid: str
    signal_strength: float
    slope: float
    ovulation_day: int
    n_nights: int
    fold_id: int
    has_round_2: bool


def _sigmoid(z: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-z))


def _fold_of(pid: str) -> int:
    digest = hashlib.md5(pid.encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "big") % 5


def _build_participants(rng: np.random.Generator) -> list[Participant]:
    pids = [f"P{i:03d}" for i in range(1, N_PARTICIPANTS + 1)]
    signal_strengths = rng.beta(2.0, 2.0, size=N_PARTICIPANTS)
    # Geometric mapping so the weak-signal tail stays genuinely weak: a
    # participant at signal_strength=0 gets slope=SLOPE_MIN (0.05), and the
    # geometric midpoint signal_strength=0.5 gets slope ≈ sqrt(MIN*MAX). This
    # produces visible non-convergers (plan §1.4 "some users converge fast,
    # others slow", and hero-figure Panel A calls for 1 labeled non-converger).
    log_min = np.log(SLOPE_MIN)
    log_max = np.log(SLOPE_MAX)
    slopes = np.exp(log_min + signal_strengths * (log_max - log_min))
    ovulation_days = rng.integers(OV_LOW, OV_HIGH + 1, size=N_PARTICIPANTS)
    n_nights = rng.integers(MIN_NIGHTS, MAX_NIGHTS + 1, size=N_PARTICIPANTS)

    round_2_idx = rng.choice(N_PARTICIPANTS, size=N_ROUND_2, replace=False)
    has_round_2 = np.zeros(N_PARTICIPANTS, dtype=bool)
    has_round_2[round_2_idx] = True

    return [
        Participant(
            pid=pid,
            signal_strength=float(signal_strengths[i]),
            slope=float(slopes[i]),
            ovulation_day=int(ovulation_days[i]),
            n_nights=int(n_nights[i]),
            fold_id=_fold_of(pid),
            has_round_2=bool(has_round_2[i]),
        )
        for i, pid in enumerate(pids)
    ]


def _build_probability_and_labels(
    participants: list[Participant], rng: np.random.Generator
) -> tuple[pd.DataFrame, pd.DataFrame]:
    prob_rows: list[dict] = []
    label_rows: list[dict] = []

    for p in participants:
        k = np.arange(1, p.n_nights + 1, dtype=np.int32)
        noise = rng.normal(0.0, OBS_NOISE_SIGMA, size=p.n_nights)
        logit = p.slope * (k - p.ovulation_day) + noise
        p_post = _sigmoid(logit)

        labels_bin = rng.binomial(1, p_post).astype(bool)
        label_strs = np.where(labels_bin, "post", "pre")
        label_conf = 2.0 * np.abs(p_post - 0.5)

        for idx, night in enumerate(k):
            prob_rows.append(
                {
                    "participant_id": p.pid,
                    "night_index": int(night),
                    "cumulative_k": int(night),
                    "p_post_ovulatory": float(p_post[idx]),
                    "fold_id": int(p.fold_id),
                    "is_synthetic": True,
                }
            )
            label_rows.append(
                {
                    "participant_id": p.pid,
                    "night_index": int(night),
                    "binary_label": str(label_strs[idx]),
                    "label_confidence": float(label_conf[idx]),
                }
            )

    prob_df = pd.DataFrame(prob_rows)
    prob_df = prob_df.astype(
        {
            "participant_id": "string",
            "night_index": "int32",
            "cumulative_k": "int32",
            "p_post_ovulatory": "float32",
            "fold_id": "int8",
            "is_synthetic": "bool",
        }
    )

    label_df = pd.DataFrame(label_rows)
    label_df = label_df.astype(
        {
            "participant_id": "string",
            "night_index": "int32",
            "binary_label": "string",
            "label_confidence": "float32",
        }
    )

    return prob_df, label_df


def _build_covariates(
    participants: list[Participant], rng: np.random.Generator
) -> pd.DataFrame:
    n = len(participants)
    signal_strength = np.array([p.signal_strength for p in participants])

    completeness_noise = rng.normal(0.0, 0.25, size=n)
    signal_completeness = np.clip(signal_strength + completeness_noise, 0.3, 1.0)

    cycle_regular = rng.binomial(1, REGULAR_PROB, size=n).astype(bool)

    snr_base_temp = 1.5 + 3.0 * signal_strength + rng.normal(0.0, 0.4, size=n)
    snr_base_hr = 1.5 + 3.0 * signal_strength + rng.normal(0.0, 0.4, size=n)
    mean_snr_temp = np.clip(snr_base_temp, 0.5, 7.0)
    mean_snr_hr = np.clip(snr_base_hr, 0.5, 7.0)

    has_temperature = rng.binomial(1, MODALITY_PRESENT_PROB, size=n).astype(bool)
    has_hr_hrv = rng.binomial(1, MODALITY_PRESENT_PROB, size=n).astype(bool)
    has_cgm = rng.binomial(1, MODALITY_PRESENT_PROB, size=n).astype(bool)
    has_self_report = rng.binomial(1, MODALITY_PRESENT_PROB, size=n).astype(bool)

    cov = pd.DataFrame(
        {
            "participant_id": [p.pid for p in participants],
            "signal_completeness": signal_completeness.astype(np.float32),
            "cycle_regular": cycle_regular,
            "mean_snr_temp": mean_snr_temp.astype(np.float32),
            "mean_snr_hr": mean_snr_hr.astype(np.float32),
            "has_temperature": has_temperature,
            "has_hr_hrv": has_hr_hrv,
            "has_cgm": has_cgm,
            "has_self_report": has_self_report,
            "has_round_2": np.array([p.has_round_2 for p in participants]),
        }
    )
    cov = cov.astype({"participant_id": "string"})
    return cov


def _compute_tau(prob_df: pd.DataFrame) -> pd.DataFrame:
    """τᵢ = smallest k such that p_post is stably on one side of 0.5 for 2
    consecutive nights, and does not cross back within the observation window."""
    records = []
    for pid, group in prob_df.sort_values("night_index").groupby("participant_id"):
        p = group["p_post_ovulatory"].to_numpy()
        k = group["night_index"].to_numpy()
        side = p >= 0.5
        tau = None
        for i in range(len(p) - 1):
            if side[i] == side[i + 1]:
                if np.all(side[i:] == side[i]):
                    tau = int(k[i])
                    break
        records.append({"participant_id": pid, "tau_i": tau})
    return pd.DataFrame(records)


def generate(out_dir: Path, seed: int) -> dict[str, Path]:
    rng = np.random.default_rng(seed)
    participants = _build_participants(rng)
    prob_df, label_df = _build_probability_and_labels(participants, rng)
    cov_df = _build_covariates(participants, rng)

    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "probability_table": out_dir / "probability_table.parquet",
        "labels": out_dir / "labels.parquet",
        "covariates": out_dir / "covariates.parquet",
    }
    prob_df.to_parquet(paths["probability_table"], index=False)
    label_df.to_parquet(paths["labels"], index=False)
    cov_df.to_parquet(paths["covariates"], index=False)

    _print_diagnostics(prob_df, label_df, cov_df)
    return paths


def _print_diagnostics(
    prob_df: pd.DataFrame, label_df: pd.DataFrame, cov_df: pd.DataFrame
) -> None:
    tau_df = _compute_tau(prob_df)
    observed_tau = tau_df["tau_i"].dropna()
    n_convergers = len(observed_tau)
    n_non_convergers = int(tau_df["tau_i"].isna().sum())

    # Rough correlation check, for the Pearson-r ≈ 0.6 target on signal_completeness.
    cov_with_ss = cov_df.copy()
    cov_with_ss["_signal_strength_proxy"] = (
        prob_df.groupby("participant_id")["p_post_ovulatory"].mean().reindex(cov_with_ss["participant_id"]).to_numpy()
    )
    # Per-participant label-positive rate vs signal_completeness — not a direct test of r
    # on latent signal_strength, but a visible-smoke-test that the covariates carry signal.

    n_rows = len(prob_df)
    n_pids = prob_df["participant_id"].nunique()
    median_nights = int(prob_df.groupby("participant_id").size().median())
    frac_post = float((label_df["binary_label"] == "post").mean())
    frac_round_2 = int(cov_df["has_round_2"].sum())

    print(f"[generator] participants={n_pids}, rows={n_rows}, median_nights/participant={median_nights}")
    print(f"[generator] fraction of 'post' labels = {frac_post:.3f}")
    print(f"[generator] participants with has_round_2=True: {frac_round_2} (target 20)")
    print(
        f"[generator] τᵢ convergers: {n_convergers}/{n_pids}"
        f" (min={int(observed_tau.min()) if n_convergers else 'NA'},"
        f" median={int(observed_tau.median()) if n_convergers else 'NA'},"
        f" max={int(observed_tau.max()) if n_convergers else 'NA'})"
    )
    print(f"[generator] non-convergers: {n_non_convergers}")
    if n_convergers:
        iqr = int(observed_tau.quantile(0.75) - observed_tau.quantile(0.25))
        print(f"[generator] τᵢ IQR: {iqr} nights (plan §1.3 secondary-success target: > 2)")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("synthetic/v1"),
        help="Output directory (default: synthetic/v1)",
    )
    parser.add_argument(
        "--seed", type=int, default=42, help="RNG seed (default: 42)"
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="After writing, run validate_contract.py on the output directory",
    )
    args = parser.parse_args(argv)

    paths = generate(args.out, args.seed)
    for name, path in paths.items():
        print(f"[generator] wrote {name}: {path}")

    if args.validate:
        validator = Path(__file__).parent / "validate_contract.py"
        print(f"[generator] running validator: {validator}")
        result = subprocess.run(
            [sys.executable, str(validator), "--dir", str(args.out)],
            check=False,
        )
        return result.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
