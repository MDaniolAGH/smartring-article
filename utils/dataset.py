"""Unified mcPHASES data loader.

One entry point for the whole team. Hides three pieces of plumbing that have
been costing students time:

1. **Path discovery.** Works the same on a local clone and on Colab with the
   PhysioNet folder mounted on Drive. Falls through a list of candidate
   locations and uses the first one that exists.

2. **Format choice.** Small CSVs (≤10 MB) are loaded directly. Large tables
   (heart_rate 1.9 GB, calories 617 MB, wrist_temperature 302 MB, etc.) are
   loaded from ``dataset_parquet/`` produced by ``scripts/convert_raw_to_parquet.py``.
   Trying to load the raw heart_rate CSV on Colab free tier times out or
   crashes; this loader simply uses the parquet copy and returns in seconds.

3. **Column convention.** mcPHASES uses ``id`` for participant; the pipeline
   contract uses ``participant_id``. Column names also vary in case across
   tables. The loader lowercases all column names and renames ``id`` to
   ``participant_id`` by default, so downstream code is consistent.

Usage in a Colab notebook
-------------------------
::

    from utils.dataset import setup, load_mcphases

    setup()                     # mounts Drive on Colab; no-op locally
    data = load_mcphases()      # auto-detects path, loads small tables eagerly

    print(list(data.tables))    # ['active_minutes', 'computed_temperature', ...]

    # Eager small tables: dict access
    hormones = data['hormones_and_selfreport']
    subjects = data['subject_info']

    # Big tables: load lazily with column / participant filters
    hr_p17 = data.load('heart_rate', participant_id=17,
                       columns=['day_in_study', 'bpm'])

    # Or as a method on the accessor
    sleep_summary = data.load('sleep')

Returned DataFrames have ``participant_id`` as the participant column and
lower-snake-case names everywhere.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Sequence

import pandas as pd


# -- File classification ----------------------------------------------------

# Tables that ``scripts/convert_raw_to_parquet.py`` writes to dataset_parquet/.
# These should not be loaded from CSV — too big for Colab free tier.
LARGE_TABLES = {
    "heart_rate",
    "calories",
    "wrist_temperature",
    "distance",
    "steps",
    "estimated_oxygen_variation",
    "sleep",
    "heart_rate_variability_details",
    "glucose",
}

# Small tables are read directly from CSV; lower friction for inspection.
# Anything in ``dataset/*.csv`` not in LARGE_TABLES is treated as small.


# -- Path discovery ---------------------------------------------------------

_LOCAL_DEFAULTS: list[tuple[str, str]] = [
    # (csv_dir, parquet_dir) candidates to search in order
    ("dataset", "dataset_parquet"),
    ("../dataset", "../dataset_parquet"),
]

# Common Drive mount paths. Students name their copy in different ways.
_DRIVE_CANDIDATES: list[str] = [
    "/content/drive/MyDrive/mcphases-a-dataset-of-physiological-hormonal-and-self-reported-events-and-symptoms-for-menstrual-health-tracking-with-wearables-1.0.0",
    "/content/drive/MyDrive/mcphases-1.0.0",
    "/content/drive/MyDrive/mcphases",
    "/content/drive/MyDrive/mcPHASES",
    "/content/drive/MyDrive/dataset",
    # The user's local layout
    str(Path.home() / "SynologyDrive/AGH/Projekty/SmartRing-Article/dataset"),
]


def _running_on_colab() -> bool:
    return "COLAB_GPU" in os.environ or "COLAB_RELEASE_TAG" in os.environ


def setup() -> None:
    """Convenience for Colab notebooks: mount Drive and enable the
    interactive table renderer. No-op when run locally."""
    if not _running_on_colab():
        return
    try:
        from google.colab import drive  # type: ignore[import-not-found]
        drive.mount("/content/drive")
    except Exception:
        pass
    try:
        from google.colab import data_table  # type: ignore[import-not-found]
        data_table.enable_dataframe_formatter()
    except Exception:
        pass


def _autodetect_paths(
    data_dir: str | Path | None = None,
    parquet_dir: str | Path | None = None,
) -> tuple[Path, Path | None]:
    """Pick the first existing (csv_dir, parquet_dir) pair.

    If the user passes ``data_dir`` explicitly, that wins. ``parquet_dir``
    defaults to ``<data_dir>_parquet`` if not given.
    """
    if data_dir is not None:
        csv = Path(data_dir).expanduser().resolve()
        if not csv.is_dir():
            raise FileNotFoundError(f"data_dir does not exist: {csv}")
        parq = (
            Path(parquet_dir).expanduser().resolve()
            if parquet_dir is not None
            else csv.parent / f"{csv.name}_parquet"
        )
        return csv, parq if parq.is_dir() else None

    # Local layouts
    for csv_rel, parq_rel in _LOCAL_DEFAULTS:
        csv = Path(csv_rel).resolve()
        if csv.is_dir():
            parq = Path(parq_rel).resolve()
            return csv, parq if parq.is_dir() else None

    # Drive layouts (Colab)
    for cand in _DRIVE_CANDIDATES:
        csv = Path(cand)
        if csv.is_dir():
            parq = csv.parent / f"{csv.name}_parquet"
            return csv, parq if parq.is_dir() else None

    raise FileNotFoundError(
        "Could not locate the mcPHASES dataset. Pass data_dir explicitly:\n"
        "  load_mcphases(data_dir='/path/to/dataset')\n"
        "or place the dataset under one of:\n  - "
        + "\n  - ".join([d for d, _ in _LOCAL_DEFAULTS] + _DRIVE_CANDIDATES)
    )


# -- Loader -----------------------------------------------------------------


@dataclass
class McPhasesDataset:
    """Container for mcPHASES tables.

    Attributes
    ----------
    csv_dir
        Directory containing the raw CSV files.
    parquet_dir
        Directory containing parquet copies of the large tables. May be ``None``
        if conversion has not been run yet — in that case ``load(name)`` for a
        large table raises an informative error.
    rename_id
        If True (default), every loaded DataFrame has ``id`` renamed to
        ``participant_id`` to match the pipeline contract.
    tables
        Eager dict of small tables, keyed by stem (e.g. ``"hormones_and_selfreport"``).
        Populated by ``__post_init__``.
    """

    csv_dir: Path
    parquet_dir: Path | None = None
    rename_id: bool = True
    tables: dict[str, pd.DataFrame] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        for csv_path in sorted(self.csv_dir.glob("*.csv")):
            stem = csv_path.stem.replace("-", "_")
            if csv_path.stem in LARGE_TABLES or stem in LARGE_TABLES:
                continue  # large; load lazily from parquet
            try:
                df = pd.read_csv(csv_path, low_memory=False)
            except Exception as exc:  # noqa: BLE001
                print(f"  [skip] {csv_path.name}: {exc}")
                continue
            self.tables[stem] = self._normalize(df)

    # -- Public API ---------------------------------------------------------

    def __getitem__(self, name: str) -> pd.DataFrame:
        """Convenience: ``data['hormones_and_selfreport']`` for small tables."""
        key = name.replace("-", "_")
        if key in self.tables:
            return self.tables[key]
        if name in LARGE_TABLES or key in LARGE_TABLES:
            return self.load(name)
        raise KeyError(
            f"No table named {name!r}. Available: {sorted(self.tables) + sorted(LARGE_TABLES)}"
        )

    def __contains__(self, name: str) -> bool:
        key = name.replace("-", "_")
        return key in self.tables or name in LARGE_TABLES or key in LARGE_TABLES

    def load(
        self,
        name: str,
        participant_id: int | str | None = None,
        columns: Sequence[str] | None = None,
    ) -> pd.DataFrame:
        """Load a table, with optional participant or column filters.

        For large tables this reads parquet — column selection and participant
        filtering are pushed down to the file, so memory stays bounded.
        For small tables the filters are applied after loading.

        Parameters
        ----------
        name
            Table name (stem of the CSV file, e.g. ``"heart_rate"``).
        participant_id
            If given, return only rows for this participant.
        columns
            If given, return only these columns. Use the *pre-rename* names
            for the source file (typically ``id`` for participant id).
        """
        key = name.replace("-", "_")

        # Small tables — already in self.tables
        if key in self.tables:
            df = self.tables[key]
            if columns:
                # Map columns through rename
                want = list(columns)
                want = ["participant_id" if (self.rename_id and c == "id") else c for c in want]
                df = df[want]
            if participant_id is not None:
                df = df[df["participant_id"] == participant_id]
            return df.reset_index(drop=True)

        # Large tables — parquet
        if key in LARGE_TABLES or name in LARGE_TABLES:
            if self.parquet_dir is None or not self.parquet_dir.is_dir():
                raise FileNotFoundError(
                    f"Large table {name!r} requires parquet conversion. Run:\n"
                    f"  python scripts/convert_raw_to_parquet.py"
                )
            path = self.parquet_dir / f"{key}.parquet"
            if not path.is_file():
                raise FileNotFoundError(
                    f"Expected parquet file at {path}. Run:\n"
                    f"  python scripts/convert_raw_to_parquet.py --only {key}.csv"
                )
            filters = None
            if participant_id is not None:
                filters = [("id", "==", participant_id)]
            df = pd.read_parquet(path, columns=list(columns) if columns else None, filters=filters)
            return self._normalize(df)

        raise KeyError(
            f"No table named {name!r}. Available: {sorted(self.tables) + sorted(LARGE_TABLES)}"
        )

    def participants(self) -> list[int]:
        """List participant ids from subject-info if available, else from any
        small table that has them."""
        for key in ("subject_info", "subject-info"):
            if key.replace("-", "_") in self.tables:
                col = "participant_id" if self.rename_id else "id"
                return sorted(self.tables[key.replace("-", "_")][col].unique().tolist())
        # Fall back to any table
        for df in self.tables.values():
            col = "participant_id" if self.rename_id else "id"
            if col in df.columns:
                return sorted(df[col].dropna().unique().tolist())
        return []

    def summary(self) -> pd.DataFrame:
        """Return a one-row-per-table summary of what is loaded."""
        rows = []
        for stem, df in sorted(self.tables.items()):
            rows.append({
                "table": stem,
                "source": "csv",
                "rows": len(df),
                "cols": len(df.columns),
                "participants": int(df["participant_id"].nunique()) if "participant_id" in df.columns else None,
            })
        if self.parquet_dir is not None and self.parquet_dir.is_dir():
            for path in sorted(self.parquet_dir.glob("*.parquet")):
                rows.append({
                    "table": path.stem,
                    "source": "parquet (lazy)",
                    "rows": None,
                    "cols": None,
                    "participants": None,
                })
        return pd.DataFrame(rows)

    # -- Helpers ------------------------------------------------------------

    def _normalize(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df.columns = df.columns.str.lower().str.strip()
        if self.rename_id and "id" in df.columns:
            df = df.rename(columns={"id": "participant_id"})
        return df


def load_mcphases(
    data_dir: str | Path | None = None,
    parquet_dir: str | Path | None = None,
    rename_id: bool = True,
) -> McPhasesDataset:
    """Locate the mcPHASES dataset and return a loader.

    Parameters
    ----------
    data_dir
        Override path to the directory of raw CSV files. If ``None``, the
        function searches ``./dataset``, ``../dataset``, and a list of typical
        Colab Drive paths.
    parquet_dir
        Override path to the parquet conversions directory. If ``None``,
        defaults to ``<data_dir>_parquet`` next to the CSV directory.
    rename_id
        If True (default), rename the source ``id`` column to ``participant_id``
        on every loaded DataFrame, matching the pipeline contract.

    Returns
    -------
    McPhasesDataset
        A container with eagerly loaded small tables and lazy access to large
        ones.
    """
    csv_dir, parq_dir = _autodetect_paths(data_dir, parquet_dir)
    return McPhasesDataset(csv_dir=csv_dir, parquet_dir=parq_dir, rename_id=rename_id)
