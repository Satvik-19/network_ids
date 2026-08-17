"""
inspect_dataset.py — Minimal, reusable inspection of HF lacg030175/CICIDS2017.

Design: does NOT materialise full row data. Reads only parquet metadata and
the two label columns (Label, label) via remote + column projection, so it is
fast and works without downloading the full dataset.

Reports, per parquet file (config/split):
- num_rows (from parquet footer metadata)
- full label distribution (Label string column)
- int label distribution (label int column)
- the int -> string pairing discovered

Also reports repo revision SHA, last_modified, and file sizes, and compares
the duplicated CICFlowMeter column "Fwd Header Length" vs
"Fwd Header Length.1" on a small sample.

Usage:
    python ml/preprocessing/inspect_dataset.py
Output:
    stdout summary + data/processed/dataset_inspection_{config}.json (JSON)
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import fsspec
import pyarrow.parquet as pq
from huggingface_hub import HfApi

REPO_ID = "lacg030175/CICIDS2017"
OUT_DIR = Path("data/processed")


def open_pf(filename: str, revision: str) -> pq.ParquetFile:
    url = f"hf://datasets/{REPO_ID}@{revision}/{filename}"
    return pq.ParquetFile(fsspec.open(url).open())


def read_column(pf: pq.ParquetFile, name: str) -> list:
    t = pf.read(columns=[name])
    return t.column(name).to_pylist()


def main() -> int:
    api = HfApi()
    info = api.dataset_info(REPO_ID, files_metadata=True)
    revision = info.sha
    print(f"Repo: {REPO_ID}")
    print(f"Revision (sha): {revision}")
    print(f"Last modified: {getattr(info, 'last_modified', None)}")

    files = sorted(
        (s.rfilename, (getattr(s, "size", None) or 0))
        for s in info.siblings
        if s.rfilename.endswith(".parquet")
    )
    print(f"\nParquet files:")
    for fn, size in files:
        print(f"  {fn:60s} {size / 1e6:8.1f} MB")

    # Group files by config (path prefix before first '/')
    report: dict = {
        "repo": REPO_ID,
        "revision": revision,
        "last_modified": str(getattr(info, "last_modified", None)),
        "files": {},
        "configs": {},
    }

    dup_checked = False
    dup_equal = None
    dup_sample_rows = 0

    for fn, size in files:
        config = fn.split("/")[0]
        split = fn.split("/")[1].split("-")[0] if "/" in fn else "?"
        print(f"\n=== {fn} (config={config}, split={split}) ===")
        pf = open_pf(fn, revision)
        md = pf.metadata
        schema_names = list(pf.schema_arrow.names)
        print(f"rows: {md.num_rows:,}  columns: {len(schema_names)}")

        file_info = {
            "num_rows": md.num_rows,
            "num_columns": len(schema_names),
            "size_bytes": size,
        }

        # Label columns
        if "Label" in schema_names:
            str_col = read_column(pf, "Label")
            int_col = read_column(pf, "label") if "label" in schema_names else []
            str_counts = Counter(str_col)
            int_counts = Counter(int_col)
            file_info["label_distribution"] = dict(
                str_counts.most_common()
            )
            file_info["int_label_distribution"] = {
                str(k): v for k, v in int_counts.most_common()
            }
            # int -> string pairing
            pairing = {}
            for s, i in zip(str_col[: len(int_col)], int_col):
                pairing.setdefault(i, set()).add(s)
            file_info["int_to_string"] = {
                str(k): sorted(v) for k, v in pairing.items()
            }
            # Check pairing is consistent (1:1)
            multi = {k: v for k, v in pairing.items() if len(v) > 1}
            file_info["pairing_consistent"] = not multi
            file_info["pairing_conflicts"] = {str(k): sorted(v) for k, v in multi.items()}
            print("label distribution:")
            for lbl, cnt in str_counts.most_common():
                print(f"  {lbl:25s} {cnt:>9,}")
            print(f"int->string: {file_info['int_to_string']}")
            print(f"pairing consistent: {file_info['pairing_consistent']}")

        # One-time duplicate-column check on the first file that has both
        if (not dup_checked
                and "Fwd Header Length" in schema_names
                and "Fwd Header Length.1" in schema_names):
            sample_n = min(md.num_rows, 2000000)
            a = read_column(pf, "Fwd Header Length")
            b = read_column(pf, "Fwd Header Length.1")
            dup_sample_rows = len(a)
            dup_equal = a == b
            dup_checked = True
            print(f"Duplicate-column check: 'Fwd Header Length' == 'Fwd Header Length.1'? {dup_equal} (n={dup_sample_rows:,})")

        report["files"][fn] = {
            "config": config,
            "split": split,
            **file_info,
        }
        cfg_acc = report["configs"].setdefault(
            config, {"splits": {}, "total_rows": 0}
        )
        cfg_acc["splits"].setdefault(split, 0)
        cfg_acc["splits"][split] += md.num_rows
        cfg_acc["total_rows"] += md.num_rows

    report["dup_fwd_header_length_equal"] = dup_equal
    report["dup_check_rows"] = dup_sample_rows

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / "dataset_inspection_cicids2017.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nWrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
