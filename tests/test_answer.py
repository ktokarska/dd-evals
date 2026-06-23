from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import answer


class FakeClient:
    def __init__(self, reply="A-1"):
        self.reply = reply
        self.calls = []
    def complete(self, *, model, system, user):
        self.calls.append({"system": system, "user": user})
        return self.reply


def test_retrieval_prompt_includes_context():
    sysmsg, user = answer.build_prompt("reg number?", [("registry.md", "Number: A-1.")])
    assert "Number: A-1." in user
    assert "registry.md" in user


def test_baseline_prompt_omits_context():
    sysmsg, user = answer.build_prompt("reg number?", [("registry.md", "Number: A-1.")], baseline=True)
    assert "Number: A-1." not in user


def test_answer_question_returns_text():
    c = FakeClient("A-1")
    out = answer.answer_question("reg number?", [("registry.md", "Number: A-1.")], client=c)
    assert out == "A-1"
    assert "Number: A-1." in c.calls[0]["user"]


def test_prompt_instructs_sentinel_for_absent():
    sysmsg, user = answer.build_prompt("directors?", [("registry.md", "no directors listed")])
    assert "Not found in the provided sources." in sysmsg
