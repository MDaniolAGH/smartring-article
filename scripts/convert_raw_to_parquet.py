"""One-off conversion of large mcPHASES CSV files to parquet.

Why
---
Raw mcPHASES CSVs are too large for Google Colab's free tier (12 GB RAM):
``heart_rate.csv`` alone is 1 GB on disk and balloons to ~3–4 GB in pandas.
Parquet stores the same data in ~20–30% of the disk footprint and loads
in seconds rather than minutes, with selective column reads.

Each team member must run this script themselves after obtaining their own
PhysioNet mcPHASES access. The outputs live under ``dataset_parquet/`` and
are git-ignored per the PhysioNet Restricted Health Data License, clause 3
(no redistribution of derivatives).

Which files are converted
-------------------------
All CSVs in ``dataset/`` whose size exceeds ``--min-size-mb`` (default 10 MB).
Smaller files stay as CSV — they are short enough that beginners can open
them in a text editor or spreadsheet, and the parquet speedup does not
justify losing readability.

Usage
-----
::

    python scripts/convert_raw_to_parquet.py
    python scripts/convert_raw_to_parquet.py --src dataset --dst dataset_parquet --min-size-mb 10
    python scripts/convert_raw_to_parquet.py --only heart_rate.csv sleep.csv

The script is idempotent; re-running skips files whose parquet counterpart
already exists (pass ``--force`` to override).
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq


DEFAULT_CHUNK_ROWS = 500_000


def _human_bytes(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def _iter_csv_chunks(src: Path, chunk_rows: int):
    # low_memory=False makes pandas scan each chunk fully for dtype inference,
    # which is what we want — consistent dtypes across the whole file.
    return pd.read_csv(src, chunksize=chunk_rows, low_memory=False)


def _unify_schema(first_chunk: pd.DataFrame) -> dict[str, str]:
    """Infer a stable dtype map from the first chunk and apply it to later chunks."""
    return {c: str(first_chunk[c].dtype) for c in first_chunk.columns}


def _cast(df: pd.DataFrame, schema: dict[str, str]) -> pd.DataFrame:
    for col, dtype in schema.items():
        if col not in df.columns:
            continue
        if str(df[col].dtype) == dtype:
            continue
        try:
            df[col] = df[col].astype(dtype)
        except (ValueError, TypeError):
            # Later chunks may contain nulls that pandas handles differently;
            # fall back to a permissive cast via object.
            pass
    return df


def convert_file(src: Path, dst: Path, chunk_rows: int) -> dict:
    t0 = time.perf_counter()
    src_bytes = src.stat().st_size
    dst.parent.mkdir(parents=True, exist_ok=True)

    writer: pq.ParquetWriter | None = None
    schema: dict[str, str] | None = None
    total_rows = 0

    try:
        for i, chunk in enumerate(_iter_csv_chunks(src, chunk_rows)):
            if schema is None:
                schema = _unify_schema(chunk)
            else:
                chunk = _cast(chunk, schema)

            table = pa.Table.from_pandas(chunk, preserve_index=False, safe=False)

            if writer is None:
                writer = pq.ParquetWriter(dst, table.schema, compression="snappy")

            writer.write_table(table)
            total_rows += len(chunk)
            print(f"    chunk {i+1:>3}: {len(chunk):>9,} rows  (running total {total_rows:>11,})")
    finally:
        if writer is not None:
            writer.close()

    dst_bytes = dst.stat().st_size
    elapsed = time.perf_counter() - t0
    return {
        "src_bytes": src_bytes,
        "dst_bytes": dst_bytes,
        "rows": total_rows,
        "seconds": elapsed,
        "ratio": dst_bytes / src_bytes if src_bytes else 0,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--src", type=Path, default=Path("dataset"),
                    help="Directory containing raw CSV files (default: dataset)")
    ap.add_argument("--dst", type=Path, default=Path("dataset_parquet"),
                    help="Output directory (default: dataset_parquet)")
    ap.add_argument("--min-size-mb", type=float, default=10.0,
                    help="Only convert CSVs larger than this (default: 10)")
    ap.add_argument("--chunk-rows", type=int, default=DEFAULT_CHUNK_ROWS,
                    help=f"Rows per chunk (default: {DEFAULT_CHUNK_ROWS:,})")
    ap.add_argument("--force", action="store_true",
                    help="Overwrite existing parquet files")
    ap.add_argument("--only", nargs="*", default=None,
                    help="Convert only these filenames (e.g. --only heart_rate.csv)")
    args = ap.parse_args(argv)

    if not args.src.is_dir():
        print(f"ERROR: source directory {args.src} not found")
        return 2

    args.dst.mkdir(parents=True, exist_ok=True)

    candidates = sorted(args.src.glob("*.csv"))
    if args.only:
        requested = set(args.only)
        candidates = [p for p in candidates if p.name in requested]
        missing = requested - {p.name for p in candidates}
        if missing:
            print(f"WARNING: requested but not found: {sorted(missing)}")

    threshold = int(args.min_size_mb * 1024 * 1024)
    to_convert = [p for p in candidates if p.stat().st_size >= threshold]
    skipped_small = [p for p in candidates if p.stat().st_size < threshold]

    if skipped_small:
        names = ", ".join(p.name for p in skipped_small)
        print(f"Skipping (smaller than {args.min_size_mb} MB, stay as CSV): {names}")
        print()

    summaries = []
    for src in to_convert:
        dst = args.dst / f"{src.stem}.parquet"
        if dst.exists() and not args.force:
            print(f"SKIP  {src.name}: output exists ({_human_bytes(dst.stat().st_size)}); pass --force to rebuild\n")
            continue

        print(f"Converting {src.name} ({_human_bytes(src.stat().st_size)})")
        try:
            s = convert_file(src, dst, args.chunk_rows)
        except Exception as exc:
            print(f"  FAILED: {exc}\n")
            continue

        print(
            f"  -> {dst.name}: {_human_bytes(s['dst_bytes'])} "
            f"({s['ratio']*100:.1f}% of CSV, {s['rows']:,} rows, {s['seconds']:.1f}s)\n"
        )
        summaries.append((src.name, s))

    # Summary
    print("=" * 72)
    print(f"Converted {len(summaries)} file(s)")
    if summaries:
        total_src = sum(s[1]["src_bytes"] for s in summaries)
        total_dst = sum(s[1]["dst_bytes"] for s in summaries)
        total_rows = sum(s[1]["rows"] for s in summaries)
        total_secs = sum(s[1]["seconds"] for s in summaries)
        print(f"Total CSV: {_human_bytes(total_src)}")
        print(f"Total parquet: {_human_bytes(total_dst)} ({total_dst/total_src*100:.1f}% of CSV)")
        print(f"Total rows: {total_rows:,}")
        print(f"Elapsed: {total_secs:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
