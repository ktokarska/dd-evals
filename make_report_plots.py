"""Regenerate the two committed result plots (confusion matrix, judge
reliability curve) from a scored run plus ground-truth labels.

The replay path in run_eval marks every field gold_pass=True, which is the
right default when you do not know which answers are sound. For the committed
demo run we do know: results/raw/ground_truth.json records that every
system-under-test answer is sound except q13 (a fabricated B Corp award year
and score). This script uses those labels so the confusion matrix shows the
harness verdict against ground truth, and the reliability curve shows judge
confidence against whether the judge agreed with ground truth.

Usage:
    python make_report_plots.py [results_dir]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

import metrics  # noqa: E402


def main(results_dir: str = "results") -> None:
    rdir = Path(results_dir)
    report = json.loads((rdir / "eval_report.json").read_text(encoding="utf-8"))
    verdicts = json.loads((rdir / "raw" / "judge_verdicts.json").read_text(encoding="utf-8"))
    labels = json.loads((rdir / "raw" / "ground_truth.json").read_text(encoding="utf-8"))["labels"]

    # Confusion: harness verdict vs ground truth across every field.
    records = [
        {"success": r["success"], "gold_pass": bool(labels[r["id"]])}
        for r in report["per_field"]
    ]
    cm = metrics.confusion(records)
    metrics.plot_confusion(cm, str(rdir / "confusion.png"))

    # Reliability: judge confidence vs whether the verdict agreed with truth.
    success_by_id = {r["id"]: r["success"] for r in report["per_field"]}
    points = [
        (float(v["score"]), success_by_id[qid] == bool(labels[qid]))
        for qid, v in verdicts.items()
    ]
    metrics.plot_reliability(metrics.reliability_bins(points, n_bins=5), str(rdir / "reliability.png"))

    print("confusion:", cm)
    print("reliability points:", points)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "results")
