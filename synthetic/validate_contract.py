"""Validate a parquet bundle against ``docs/data_contract_v1.md``.

Checks, in order:

1. All three parquet files present in the target directory.
2. Column presence and dtypes for each file.
3. Value-range and null constraints for every column.
4. Referential integrity:
   * probability_table ↔ labels one-to-one on (participant_id, night_index)
   * probability_table.participant_id ⊆ covariates.participant_id
   * covariates.participant_id unique
5. Per-participant night_index is dense (starts at 1, strictly +1).
6. fold_id constant within participant.
7. is_synthetic constant within each file.

Exit codes
----------
0  all checks pass
1  at least one violation (first violation is printed; subsequent ones are not
   necessarily reported — re-run after fixing)

Usage
-----
::

    python synthetic/validate_contract.py --dir synthetic/v1
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd


REQUIRED_FILES = {
    "probability_table": "probability_table.parquet",
    "labels": "labels.parquet",
    "covariates": "covariates.parquet",
}

PROB_COLUMNS = {
    "participant_id": "string",
    "night_index": "int32",
    "cumulative_k": "int32",
    "p_post_ovulatory": "float32",
    "fold_id": "int8",
    "is_synthetic": "bool",
}

LABEL_COLUMNS = {
    "participant_id": "string",
    "night_index": "int32",
    "binary_label": "string",
    "label_confidence": "float32",
}

COV_COLUMNS = {
    "participant_id": "string",
    "signal_completeness": "float32",
    "cycle_regular": "bool",
    "mean_snr_temp": "float32",
    "mean_snr_hr": "float32",
    "has_temperature": "bool",
    "has_hr_hrv": "bool",
    "has_cgm": "bool",
    "has_self_report": "bool",
    "has_round_2": "bool",
}


class ContractViolation(RuntimeError):
    """Raised on the first schema / integrity violation."""


def _fail(msg: str) -> None:
    raise ContractViolation(msg)


def _check_columns(df: pd.DataFrame, expected: dict[str, str], name: str) -> None:
    missing = [c for c in expected if c not in df.columns]
    extra = [c for c in df.columns if c not in expected]
    if missing:
        _fail(f"{name}: missing columns {missing}")
    if extra:
        _fail(f"{name}: unexpected columns {extra}")

    for col, dtype in expected.items():
        actual = str(df[col].dtype)
        if dtype == "string":
            ok = actual in ("string", "object")
        elif dtype == "bool":
            ok = actual in ("bool", "boolean")
        else:
            ok = actual == dtype
        if not ok:
            _fail(f"{name}.{col}: expected dtype {dtype}, got {actual}")


def _check_nonnull(df: pd.DataFrame, cols: list[str], name: str) -> None:
    for c in cols:
        n_null = int(df[c].isna().sum())
        if n_null:
            _fail(f"{name}.{c}: {n_null} null values (column is non-nullable)")


def _check_prob(df: pd.DataFrame) -> None:
    _check_columns(df, PROB_COLUMNS, "probability_table")
    _check_nonnull(df, list(PROB_COLUMNS.keys()), "probability_table")

    if (df["night_index"] < 1).any():
        _fail("probability_table.night_index: contains values < 1")
    if (df["cumulative_k"] != df["night_index"]).any():
        _fail("probability_table: cumulative_k must equal night_index (contract §2.1)")
    p = df["p_post_ovulatory"].to_numpy()
    if (p < 0).any() or (p > 1).any():
        _fail("probability_table.p_post_ovulatory: values outside [0, 1]")
    if not df["fold_id"].isin([0, 1, 2, 3, 4]).all():
        _fail("probability_table.fold_id: values outside {0,1,2,3,4}")

    for pid, group in df.groupby("participant_id"):
        folds = group["fold_id"].unique()
        if len(folds) != 1:
            _fail(f"probability_table: participant {pid} has multiple fold_id values {folds}")
        k = group.sort_values("night_index")["night_index"].to_numpy()
        if k[0] != 1:
            _fail(f"probability_table: participant {pid} night_index does not start at 1 (starts at {k[0]})")
        if not (k[1:] - k[:-1] == 1).all():
            _fail(f"probability_table: participant {pid} has non-dense night_index (gaps or duplicates)")

    if df["is_synthetic"].nunique() != 1:
        _fail("probability_table.is_synthetic: mixed True/False in single file")


def _check_labels(df: pd.DataFrame) -> None:
    _check_columns(df, LABEL_COLUMNS, "labels")
    _check_nonnull(df, list(LABEL_COLUMNS.keys()), "labels")

    if (df["night_index"] < 1).any():
        _fail("labels.night_index: contains values < 1")
    if not df["binary_label"].isin(["pre", "post"]).all():
        bad = set(df["binary_label"].unique()) - {"pre", "post"}
        _fail(f"labels.binary_label: unexpected values {bad}")
    lc = df["label_confidence"].to_numpy()
    if (lc < 0).any() or (lc > 1).any():
        _fail("labels.label_confidence: values outside [0, 1]")


def _check_covariates(df: pd.DataFrame) -> None:
    _check_columns(df, COV_COLUMNS, "covariates")
    _check_nonnull(df, ["participant_id", "signal_completeness", "cycle_regular",
                        "has_temperature", "has_hr_hrv", "has_cgm",
                        "has_self_report", "has_round_2"], "covariates")

    if df["participant_id"].duplicated().any():
        dupes = df.loc[df["participant_id"].duplicated(), "participant_id"].tolist()
        _fail(f"covariates.participant_id: duplicates {dupes}")

    sc = df["signal_completeness"].to_numpy()
    if (sc < 0).any() or (sc > 1).any():
        _fail("covariates.signal_completeness: values outside [0, 1]")

    # SNR columns may be NaN only if the corresponding modality flag is False.
    _check_snr_gating(df, "mean_snr_temp", "has_temperature")
    _check_snr_gating(df, "mean_snr_hr", "has_hr_hrv")


def _check_snr_gating(df: pd.DataFrame, snr_col: str, flag_col: str) -> None:
    present = df[flag_col]
    snr_present_nan = df.loc[present, snr_col].isna()
    if snr_present_nan.any():
        bad = df.loc[present & df[snr_col].isna(), "participant_id"].tolist()
        _fail(
            f"covariates.{snr_col}: NaN for participants with {flag_col}=True: {bad}"
        )


def _check_referential_integrity(
    prob: pd.DataFrame, labels: pd.DataFrame, cov: pd.DataFrame
) -> None:
    prob_keys = set(zip(prob["participant_id"], prob["night_index"]))
    label_keys = set(zip(labels["participant_id"], labels["night_index"]))
    if prob_keys != label_keys:
        missing_in_labels = list(prob_keys - label_keys)[:5]
        extra_in_labels = list(label_keys - prob_keys)[:5]
        _fail(
            "referential integrity: probability_table and labels disagree on (participant_id, night_index).\n"
            f"  sample missing from labels: {missing_in_labels}\n"
            f"  sample extra in labels: {extra_in_labels}"
        )

    prob_pids = set(prob["participant_id"].unique())
    cov_pids = set(cov["participant_id"].unique())
    missing = prob_pids - cov_pids
    if missing:
        _fail(f"referential integrity: participants with predictions but no covariates: {sorted(missing)[:5]}")


def validate(target_dir: Path) -> None:
    for name, fname in REQUIRED_FILES.items():
        path = target_dir / fname
        if not path.is_file():
            _fail(f"missing file: {path}")

    prob = pd.read_parquet(target_dir / REQUIRED_FILES["probability_table"])
    labels = pd.read_parquet(target_dir / REQUIRED_FILES["labels"])
    cov = pd.read_parquet(target_dir / REQUIRED_FILES["covariates"])

    _check_prob(prob)
    _check_labels(labels)
    _check_covariates(cov)
    _check_referential_integrity(prob, labels, cov)

    print(
        f"[validator] OK: {len(prob)} probability rows, {len(labels)} label rows, "
        f"{len(cov)} covariate rows; {cov['participant_id'].nunique()} participants"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--dir",
        type=Path,
        default=Path("synthetic/v1"),
        help="Directory containing the three parquet files (default: synthetic/v1)",
    )
    args = parser.parse_args(argv)

    try:
        validate(args.dir)
    except ContractViolation as exc:
        print(f"[validator] FAIL: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
