from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import score_run as sr

SENTINEL = "Not found in the provided sources."


class FakeJudge:
    def __init__(self, score):
        self.score = score
    def run_geval(self, case):
        return {"score": self.score, "reason": "fake"}
    def run_faithfulness(self, case):
        return {"score": self.score, "reason": "fake"}
    def run_answer_relevancy(self, case):
        return {"score": self.score, "reason": "fake"}


QUESTIONS = {
    "q1": {"company": "Acme", "question": "reg number?", "gold_answer": "A-1", "gold_label": "A-1", "source_ref": "x"},
    "q2": {"company": "Acme", "question": "turnover?", "gold_answer": "1000000", "gold_label": "1000000", "source_ref": "x"},
    "q3": {"company": "Acme", "question": "summary?", "gold_answer": "sells credits", "gold_label": "sells credits", "source_ref": "x"},
    "q4": {"company": "Acme", "question": "directors?", "gold_answer": SENTINEL, "gold_label": SENTINEL, "source_ref": "x"},
    "q5": {"company": "Acme", "question": "sanctions?", "gold_answer": "no", "gold_label": "no", "source_ref": "x"},
}
FIELD_KEYS = {
    "q1": {"method": "exact", "gate_id": "G1"},
    "q2": {"method": "tolerance", "gate_id": "G1", "tolerance": {"kind": "numeric", "rel": 0.02}},
    "q3": {"method": "judge", "gate_id": "G2"},
    "q4": {"method": "absent", "gate_id": "G3"},
    "q5": {"method": "binary", "gate_id": "G4"},
}


def _answers(**over):
    base = {"q1": "A-1", "q2": "1000000", "q3": "sells credits", "q4": SENTINEL, "q5": "no"}
    base.update(over)
    return base


def test_perfect_run_passes_every_gate():
    rep = sr.score_run(QUESTIONS, FIELD_KEYS, _answers(), FakeJudge(1.0))
    assert rep["overall"] == "pass"
    assert set(rep["gates"]) == {"G1", "G2", "G3", "G4"}
    assert all(v == "pass" for v in rep["gates"].values())
    ids = {r["id"] for r in rep["per_field"]}
    assert ids == {"q1", "q2", "q3", "q4", "q5"}


def test_exact_mismatch_fails_g1():
    rep = sr.score_run(QUESTIONS, FIELD_KEYS, _answers(q1="A-2"), FakeJudge(1.0))
    assert rep["gates"]["G1"] == "fail" and rep["overall"] == "fail"
    rec = [r for r in rep["per_field"] if r["id"] == "q1"][0]
    assert rec["score"] == 0.0 and "A-1" in rec["reason"] and "A-2" in rec["reason"]


def test_tolerance_within_band_passes():
    rep = sr.score_run(QUESTIONS, FIELD_KEYS, _answers(q2="1015000"), FakeJudge(1.0))
    assert [r for r in rep["per_field"] if r["id"] == "q2"][0]["success"] is True


def test_tolerance_outside_band_fails():
    rep = sr.score_run(QUESTIONS, FIELD_KEYS, _answers(q2="1500000"), FakeJudge(1.0))
    assert [r for r in rep["per_field"] if r["id"] == "q2"][0]["success"] is False


def test_judge_score_below_threshold_fails_g2():
    rep = sr.score_run(QUESTIONS, FIELD_KEYS, _answers(), FakeJudge(0.5))
    rec = [r for r in rep["per_field"] if r["id"] == "q3"][0]
    assert rec["metric"] == "Faithfulness" and rec["success"] is False
    assert rep["gates"]["G2"] == "fail"


def test_absent_requires_exact_sentinel():
    rep = sr.score_run(QUESTIONS, FIELD_KEYS, _answers(q4="Jane Doe, director"), FakeJudge(1.0))
    rec = [r for r in rep["per_field"] if r["id"] == "q4"][0]
    assert rec["success"] is False and rec["score"] == 0.0
    assert rep["gates"]["G3"] == "fail"


def test_binary_false_no_on_a_yes_fails_g4():
    q = dict(QUESTIONS)
    q["q5"] = dict(QUESTIONS["q5"], gold_label="yes", gold_answer="yes")
    rep = sr.score_run(q, FIELD_KEYS, _answers(q5="no"), FakeJudge(1.0))
    rec = [r for r in rep["per_field"] if r["id"] == "q5"][0]
    assert rec["success"] is False
    assert rep["gates"]["G4"] == "fail"


def test_writes_report_files(tmp_path):
    sr.score_run(QUESTIONS, FIELD_KEYS, _answers(), FakeJudge(1.0), out_dir=str(tmp_path))
    rep = json.loads((tmp_path / "eval_report.json").read_text())
    assert rep["overall"] == "pass"
    assert (tmp_path / "eval_report.md").exists()


def test_binary_sentinel_answer_does_not_pass_a_no_gold():
    # A model refusal (sentinel string) on a G4 binary field with gold "no" must FAIL,
    # not be credited as a correct "no" answer.
    rep = sr.score_run(QUESTIONS, FIELD_KEYS, _answers(q5=SENTINEL), FakeJudge(1.0))
    rec = [r for r in rep["per_field"] if r["id"] == "q5"][0]
    assert rec["success"] is False
    assert rep["gates"]["G4"] == "fail"


def test_binary_none_answer_does_not_pass():
    # "None" starts with "no" but must not classify as a "no" answer.
    rep = sr.score_run(QUESTIONS, FIELD_KEYS, _answers(q5="None"), FakeJudge(1.0))
    rec = [r for r in rep["per_field"] if r["id"] == "q5"][0]
    assert rec["success"] is False
    assert rep["gates"]["G4"] == "fail"


def test_g5_relevancy_routes_to_answer_relevancy():
    # A G5 judge field must route to run_answer_relevancy and use threshold 0.90.
    questions_g5 = dict(QUESTIONS)
    questions_g5["q6"] = {
        "company": "Acme", "question": "what is the product?",
        "gold_answer": "carbon credits", "gold_label": "carbon credits", "source_ref": "x",
    }
    field_keys_g5 = dict(FIELD_KEYS)
    field_keys_g5["q6"] = {"method": "judge", "gate_id": "G5"}

    answers_g5_pass = _answers(q6="carbon credits")
    rep_pass = sr.score_run(questions_g5, field_keys_g5, answers_g5_pass, FakeJudge(0.95))
    rec_pass = [r for r in rep_pass["per_field"] if r["id"] == "q6"][0]
    assert rec_pass["metric"] == "Answer Relevancy"
    assert rec_pass["threshold"] == 0.90
    assert rec_pass["success"] is True

    rep_fail = sr.score_run(questions_g5, field_keys_g5, answers_g5_pass, FakeJudge(0.85))
    rec_fail = [r for r in rep_fail["per_field"] if r["id"] == "q6"][0]
    assert rec_fail["metric"] == "Answer Relevancy"
    assert rec_fail["success"] is False
    assert rep_fail["gates"]["G5"] == "fail"


def test_empty_field_keys_is_not_a_pass():
    rep = sr.score_run(QUESTIONS, {}, _answers(), FakeJudge(1.0))
    assert rep["overall"] == "fail"
