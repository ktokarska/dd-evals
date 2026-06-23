"""The one metric record shape every gate emits.

score is normalised 0.0..1.0 (deterministic gates emit 1.0 or 0.0). reason is
always populated: for deterministic gates it names the concrete failure; for
judged gates it is the judge rationale.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Dict


@dataclass
class MetricRecord:
    metric: str
    gate_id: str
    score: float
    threshold: float
    success: bool
    reason: str
    field_id: Optional[str] = field(default=None)

    def __post_init__(self) -> None:
        if self.score < 0.0:
            self.score = 0.0
        elif self.score > 1.0:
            self.score = 1.0
        if not self.reason:
            raise ValueError(f"MetricRecord for {self.gate_id} has empty reason")


def record_to_dict(r: MetricRecord, include_id: bool = False) -> Dict:
    d = {
        "metric": r.metric,
        "gate_id": r.gate_id,
        "score": r.score,
        "threshold": r.threshold,
        "success": r.success,
        "reason": r.reason,
    }
    if include_id:
        d["id"] = r.field_id
    return d


def passed(score: float, threshold: float) -> bool:
    """A field passes when its score meets or exceeds the threshold."""
    return score >= threshold
