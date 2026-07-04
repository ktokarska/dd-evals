from __future__ import annotations

import pytest

import judge_calibration as jc
import calibration_csv_to_jsonl as conv


class ScriptedJudge:
    """Returns a fixed score by rubric so agreement is deterministic."""
    def __init__(self, geval=1.0, faith=1.0, rel=1.0):
        self.s = {"geval": geval, "faithfulness": faith, "answer_relevancy": rel}
    def run_geval(self, case):
        return {"score": self.s["geval"], "reason": "x"}
    def run_faithfulness(self, case):
        return {"score": self.s["faithfulness"], "reason": "x"}
    def run_answer_relevancy(self, case):
        return {"score": self.s["answer_relevancy"], "reason": "x"}


def _items():
    # 4 pass, 1 fail labelled by the operator
    return [
        {"id": "c1", "rubric": "geval", "input": "q", "expected_output": "e",
         "actual_output": "a", "retrieval_context": "", "operator_label": "pass"},
        {"id": "c2", "rubric": "geval", "input": "q", "expected_output": "e",
         "actual_output": "a", "retrieval_context": "", "operator_label": "pass"},
        {"id": "c3", "rubric": "faithfulness", "input": "q", "expected_output": "e",
         "actual_output": "a", "retrieval_context": "ctx", "operator_label": "pass"},
        {"id": "c4", "rubric": "answer_relevancy", "input": "q", "expected_output": "e",
         "actual_output": "a", "retrieval_context": "", "operator_label": "pass"},
        {"id": "c5", "rubric": "geval", "input": "q", "expected_output": "e",
         "actual_output": "bad", "retrieval_context": "", "operator_label": "fail"},
    ]


def test_agreement_perfect_when_judge_matches_labels():
    judge = ScriptedJudge(geval=1.0, faith=1.0, rel=1.0)
    # c5 is labelled fail but judge scores 1.0 -> disagreement on 1 of 5
    out = jc.compute_agreement(_items(), judge)
    assert out["per_item"]["c5"]["judge_label"] == "pass"
    assert out["agreement"] == pytest.approx(0.8)
    assert out["passed_gate"] is False  # 0.8 < 0.85


def test_gate_passes_at_point_nine():
    items = _items()
    # Judge scores the one operator-fail item (c5, "bad") low and everything
    # else high, so it agrees with all 5 labels -> agreement 1.0, gate passes.
    judge = type("J", (), {
        "run_geval": lambda self, case: {"score": 0.2 if case["actual_output"] == "bad" else 1.0, "reason": "x"},
        "run_faithfulness": lambda self, case: {"score": 1.0, "reason": "x"},
        "run_answer_relevancy": lambda self, case: {"score": 1.0, "reason": "x"},
    })()
    out = jc.compute_agreement(items, judge)
    assert out["agreement"] == pytest.approx(1.0)
    assert out["passed_gate"] is True


def test_thresholds_are_rubric_specific():
    assert jc.THRESHOLDS["faithfulness"] == 0.98
    assert jc.THRESHOLDS["geval"] == 0.80


def test_converter_rejects_missing_label(tmp_path):
    csv_path = tmp_path / "cal.csv"
    csv_path.write_text(
        "id,rubric,input,expected_output,retrieval_context,actual_output,operator_label\n"
        "c1,geval,q,e,,a,\n", encoding="utf-8")
    with pytest.raises(ValueError):
        conv.csv_to_jsonl(str(csv_path), str(tmp_path / "out.jsonl"))
