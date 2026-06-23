from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import judge_runner as jr


class FakeClient:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def complete(self, *, model, temperature, system, user):
        self.calls.append({"model": model, "temperature": temperature,
                           "system": system, "user": user})
        return self.payload


CASE = {
    "input": "What is the business of the company?",
    "expected_output": "Nature-based carbon restoration.",
    "actual_output": "The company does nature-based carbon restoration.",
    "retrieval_context": "",
}


def test_geval_returns_score_and_reason():
    c = FakeClient('{"score": 0.75, "reason": "same fact, minor drift"}')
    out = jr.run_geval(CASE, client=c)
    assert out["score"] == 0.75 and out["reason"] == "same fact, minor drift"


def test_judge_pins_model_and_temperature():
    c = FakeClient('{"score": 1.0, "reason": "ok"}')
    jr.run_geval(CASE, client=c)
    assert c.calls[0]["model"] == "claude-sonnet-4-6"
    assert c.calls[0]["temperature"] == 0


def test_judge_sends_explicit_steps_and_the_answer():
    c = FakeClient('{"score": 1.0, "reason": "ok"}')
    jr.run_geval(CASE, client=c)
    user = c.calls[0]["user"]
    assert "Evaluation steps" in user and "1." in user
    assert CASE["actual_output"] in user


def test_faithfulness_includes_context():
    case = dict(CASE, retrieval_context="Registry: State of Delaware.")
    c = FakeClient('{"score": 1.0, "reason": "all 1 claims supported"}')
    jr.run_faithfulness(case, client=c)
    assert "State of Delaware" in c.calls[0]["user"]


def test_malformed_output_retries_once_then_raises():
    class Flaky:
        def __init__(self):
            self.n = 0
        def complete(self, **kw):
            self.n += 1
            return "not json"
    f = Flaky()
    try:
        jr.run_geval(CASE, client=f)
        assert False
    except jr.JudgeParseError:
        pass
    assert f.n == 2


def test_parses_json_in_a_wrapper():
    c = FakeClient('Verdict: {"score": 0.5, "reason": "one point missing"} done')
    assert jr.run_geval(CASE, client=c)["score"] == 0.5


def test_score_is_clamped_into_range():
    c = FakeClient('{"score": 1.5, "reason": "over"}')
    assert jr.run_geval(CASE, client=c)["score"] == 1.0


def test_null_score_retries_then_raises():
    c = FakeClient('{"score": null, "reason": "uncertain"}')
    try:
        jr.run_geval(CASE, client=c)
        assert False, "expected JudgeParseError"
    except jr.JudgeParseError:
        pass
    assert len(c.calls) == 2
