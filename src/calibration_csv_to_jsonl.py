"""Convert the operator-filled calibration CSV to JSONL, validating first.
Refuses to write unless every row has a candidate answer and a pass/fail
label, faithfulness rows carry context, and there are at least 4 pass and 4
fail. Drops the read-only design_note column.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Dict, List

VALID_RUBRICS = {"geval", "faithfulness", "answer_relevancy"}


def _validate(rows: List[Dict[str, str]]) -> None:
    if len(rows) < 10:
        raise ValueError(f"need at least 10 rows, got {len(rows)}")
    passes = sum(1 for r in rows if r["operator_label"].strip() == "pass")
    fails = sum(1 for r in rows if r["operator_label"].strip() == "fail")
    if passes < 4 or fails < 4:
        raise ValueError(f"need >= 4 pass and >= 4 fail, got {passes} pass / {fails} fail")
    for r in rows:
        rid = r.get("id", "?")
        if r["rubric"] not in VALID_RUBRICS:
            raise ValueError(f"{rid}: bad rubric {r['rubric']!r}")
        if not r["actual_output"].strip() or r["actual_output"].strip().lower().startswith("<"):
            raise ValueError(f"{rid}: empty/placeholder actual_output")
        if r["operator_label"].strip() not in {"pass", "fail"}:
            raise ValueError(f"{rid}: operator_label must be pass/fail")
        if r["rubric"] == "faithfulness" and not r["retrieval_context"].strip():
            raise ValueError(f"{rid}: faithfulness row needs retrieval_context")


def csv_to_jsonl(csv_path: str, out_path: str) -> int:
    with open(csv_path, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    _validate(rows)
    keep = ["id", "rubric", "input", "expected_output", "retrieval_context",
            "actual_output", "operator_label"]
    with open(out_path, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps({k: r[k] for k in keep}) + "\n")
    return len(rows)


if __name__ == "__main__":  # pragma: no cover
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="judge/calibration_set.csv")
    ap.add_argument("--out", default="judge/calibration_set.jsonl")
    a = ap.parse_args()
    n = csv_to_jsonl(a.csv, a.out)
    print(f"wrote {n} rows to {a.out}")
