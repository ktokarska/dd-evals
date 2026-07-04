from __future__ import annotations

import json

from metric_record import MetricRecord, record_to_dict, passed


def test_record_has_the_standard_fields():
    r = MetricRecord(metric="Faithfulness", gate_id="G2", score=0.96,
                     threshold=0.98, success=False,
                     reason="2 of 25 claims unsupported")
    d = record_to_dict(r)
    assert set(d) == {"metric", "gate_id", "score", "threshold", "success", "reason"}
    assert d["score"] == 0.96 and d["success"] is False and d["reason"]


def test_score_is_clamped():
    assert MetricRecord("deterministic", "G1", 1.4, 1.0, True, "x").score == 1.0
    assert MetricRecord("deterministic", "G1", -0.2, 1.0, False, "x").score == 0.0


def test_empty_reason_is_rejected():
    try:
        MetricRecord("deterministic", "G1", 1.0, 1.0, True, "")
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_include_id_serialises():
    r = MetricRecord("deterministic", "G1", 1.0, 1.0, True, "match", field_id="q01")
    d = record_to_dict(r, include_id=True)
    assert d["id"] == "q01"
    assert json.dumps(d)


def test_passed_helper():
    assert passed(0.98, 0.98) is True
    assert passed(0.97, 0.98) is False
