from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import metrics


def test_confusion_counts():
    records = [
        {"success": True, "gold_pass": True},    # tp
        {"success": True, "gold_pass": False},   # fp
        {"success": False, "gold_pass": False},  # tn
        {"success": False, "gold_pass": True},   # fn
        {"success": True, "gold_pass": True},    # tp
    ]
    cm = metrics.confusion(records)
    assert cm == {"tp": 2, "fp": 1, "tn": 1, "fn": 1}


def test_reliability_bins_group_by_confidence():
    points = [(0.1, False), (0.2, False), (0.9, True), (0.95, True), (0.5, True)]
    bins = metrics.reliability_bins(points, n_bins=5)
    assert len(bins) == 5
    # the lowest bin holds the two low-confidence, incorrect points
    low = bins[0]
    assert low["n"] == 2 and low["empirical_accuracy"] == 0.0
    high = bins[-1]
    assert high["n"] == 2 and high["empirical_accuracy"] == 1.0


def test_plots_write_png(tmp_path):
    cm = {"tp": 2, "fp": 1, "tn": 1, "fn": 1}
    cpath = tmp_path / "confusion.png"
    metrics.plot_confusion(cm, str(cpath))
    assert cpath.exists() and cpath.stat().st_size > 0
    bins = metrics.reliability_bins([(0.1, False), (0.9, True)], n_bins=2)
    rpath = tmp_path / "reliability.png"
    metrics.plot_reliability(bins, str(rpath))
    assert rpath.exists() and rpath.stat().st_size > 0
