"""Format-agnostic preview helpers for Colab / Jupyter.

The ``peek`` function is the project's equivalent of ``!head file.csv``:
it prints a quick summary (row count, column names with dtypes) and
returns the first N rows as a pandas DataFrame, which Colab renders as
an interactive searchable/sortable table if
``google.colab.data_table.enable_dataframe_formatter()`` has been called.

Works for parquet and CSV transparently — the student writes::

    from utils.preview import peek
    peek('synthetic/v1/labels.parquet')
    peek('dataset/hormones_and_selfreport.csv')

and the same pattern works for both formats.

In a Colab notebook, once per session::

    from google.colab import data_table
    data_table.enable_dataframe_formatter()

makes every returned DataFrame an interactive table.
"""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

import pandas as pd


def peek(
    path: str | Path,
    n: int = 10,
    columns: Sequence[str] | None = None,
) -> pd.DataFrame:
    """Print a one-line summary and return the first ``n`` rows.

    Parameters
    ----------
    path
        Path to a ``.parquet`` or ``.csv`` file.
    n
        Number of rows to return (default 10).
    columns
        Optional subset of columns. For parquet this is pushed down and only
        those columns are read from disk — useful for large files on Colab.
        For CSV this is applied after read.
    """
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(p)

    suffix = p.suffix.lower()
    if suffix == ".parquet":
        df = pd.read_parquet(p, columns=list(columns) if columns else None)
    elif suffix == ".csv":
        df = pd.read_csv(p)
        if columns:
            df = df[list(columns)]
    else:
        raise ValueError(f"Unsupported file type {suffix!r}; expected .parquet or .csv")

    print(f"{p} — {len(df):,} rows × {len(df.columns)} cols")
    dtypes = ", ".join(f"{c}: {t}" for c, t in df.dtypes.items())
    print(f"  dtypes: {dtypes}")
    return df.head(n)


def summary(path: str | Path) -> pd.DataFrame:
    """Per-column summary: dtype, null count, unique count, min/max for numerics.

    Useful as a second-line follow-up to ``peek``. Reads the full file.
    """
    p = Path(path)
    suffix = p.suffix.lower()
    if suffix == ".parquet":
        df = pd.read_parquet(p)
    elif suffix == ".csv":
        df = pd.read_csv(p)
    else:
        raise ValueError(f"Unsupported file type {suffix!r}")

    rows = []
    for col in df.columns:
        s = df[col]
        entry = {
            "column": col,
            "dtype": str(s.dtype),
            "non_null": int(s.notna().sum()),
            "null": int(s.isna().sum()),
            "unique": int(s.nunique(dropna=True)),
        }
        if pd.api.types.is_numeric_dtype(s):
            entry["min"] = s.min()
            entry["max"] = s.max()
        else:
            entry["min"] = None
            entry["max"] = None
        rows.append(entry)
    return pd.DataFrame(rows)
