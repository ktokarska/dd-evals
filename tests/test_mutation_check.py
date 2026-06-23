from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import mutation_check as mc


class FakeJudge:
    def run_geval(self, case):
        # judge mirrors whether the answer is non-empty and matches expected
        ok = case["actual_output"].strip() and case["actual_output"] == case["expected_output"]
        return {"score": 1.0 if ok else 0.0, "reason": "fake"}
    def run_faithfulness(self, case):
        ok = case["actual_output"].strip() and case["actual_output"] == case["expected_output"]
        return {"score": 1.0 if ok else 0.0, "reason": "fake"}
    def run_answer_relevancy(self, case):
        return {"score": 1.0 if case["actual_output"].strip() else 0.0, "reason": "fake"}


QUESTIONS = {
    "g1": {"company": "Acme", "question": "reg?", "gold_answer": "A-1", "gold_label": "A-1", "source_ref": "x"},
    "g2": {"company": "Acme", "question": "summary?", "gold_answer": "sells credits", "gold_label": "sells credits", "source_ref": "x"},
    "g4": {"company": "Acme", "question": "sanctions?", "gold_answer": "yes", "gold_label": "yes", "source_ref": "x"},
}
FIELD_KEYS = {
    "g1": {"method": "exact", "gate_id": "G1"},
    "g2": {"method": "judge", "gate_id": "G2"},
    "g4": {"method": "binary", "gate_id": "G4"},
}
CLEAN = {"g1": "A-1", "g2": "sells credits", "g4": "yes"}


def test_clean_answers_pass_first():
    # sanity: the clean set must pass, else the mutation check is meaningless
    out = mc.run_mutation_check(QUESTIONS, FIELD_KEYS, CLEAN, FakeJudge())
    assert out["baseline_overall"] == "pass"


def test_all_three_mutations_are_caught():
    out = mc.run_mutation_check(QUESTIONS, FIELD_KEYS, CLEAN, FakeJudge())
    assert {m["gate_id"] for m in out["mutations"]} == {"G1", "G2", "G4"}
    assert all(m["caught"] for m in out["mutations"])
    assert out["all_caught"] is True
