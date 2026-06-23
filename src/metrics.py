"""Confusion matrix and judge reliability (calibration) curve. Matplotlib uses
the Agg backend so plots render without a display.
"""
from __future__ import annotations

from typing import Dict, List, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


def confusion(records: List[dict]) -> Dict[str, int]:
    cm = {"tp": 0, "fp": 0, "tn": 0, "fn": 0}
    for r in records:
        pred, gold = bool(r["success"]), bool(r["gold_pass"])
        if pred and gold:
            cm["tp"] += 1
        elif pred and not gold:
            cm["fp"] += 1
        elif not pred and not gold:
            cm["tn"] += 1
        else:
            cm["fn"] += 1
    return cm


def reliability_bins(points: List[Tuple[float, bool]], n_bins: int = 5) -> List[dict]:
    bins = []
    width = 1.0 / n_bins
    for i in range(n_bins):
        lo, hi = i * width, (i + 1) * width
        if i == n_bins - 1:
            members = [c for conf, c in points if lo <= conf <= hi]
        else:
            members = [c for conf, c in points if lo <= conf <= hi]
        n = len(members)
        acc = (sum(1 for c in members if c) / n) if n else 0.0
        bins.append({"lo": lo, "hi": hi, "n": n, "empirical_accuracy": acc})
    return bins


def plot_confusion(cm: Dict[str, int], out_path: str) -> None:
    grid = [[cm["tp"], cm["fn"]], [cm["fp"], cm["tn"]]]
    fig, ax = plt.subplots(figsize=(4, 4))
    ax.imshow(grid, cmap="Blues")
    ax.set_xticks([0, 1]); ax.set_xticklabels(["gold pass", "gold fail"])
    ax.set_yticks([0, 1]); ax.set_yticklabels(["scored pass", "scored fail"])
    for (i, j), v in [((0, 0), grid[0][0]), ((0, 1), grid[0][1]), ((1, 0), grid[1][0]), ((1, 1), grid[1][1])]:
        ax.text(j, i, str(v), ha="center", va="center", fontsize=14)
    ax.set_title("dd-evals confusion (scored vs gold)")
    fig.tight_layout(); fig.savefig(out_path, dpi=120); plt.close(fig)


def plot_reliability(bins: List[dict], out_path: str) -> None:
    xs = [(b["lo"] + b["hi"]) / 2 for b in bins]
    ys = [b["empirical_accuracy"] for b in bins]
    fig, ax = plt.subplots(figsize=(4, 4))
    ax.plot([0, 1], [0, 1], "--", color="grey", label="perfect calibration")
    ax.plot(xs, ys, "o-", color="C0", label="judge")
    ax.set_xlabel("judge confidence"); ax.set_ylabel("empirical accuracy")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.legend()
    ax.set_title("Judge reliability curve")
    fig.tight_layout(); fig.savefig(out_path, dpi=120); plt.close(fig)
