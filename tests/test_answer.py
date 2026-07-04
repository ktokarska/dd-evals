from __future__ import annotations

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


class ModelCapturingClient:
    def __init__(self, reply="ok"):
        self.reply = reply
        self.calls = []
    def complete(self, *, model, system, user):
        self.calls.append({"model": model, "system": system, "user": user})
        return self.reply


def test_answer_question_defaults_to_pinned_model():
    c = ModelCapturingClient()
    answer.answer_question("q?", [("s.md", "ctx")], client=c)
    assert c.calls[0]["model"] == answer.MODEL


def test_answer_question_threads_model_override():
    c = ModelCapturingClient()
    answer.answer_question("q?", [("s.md", "ctx")], client=c, model="claude-haiku-4-5-20251001")
    assert c.calls[0]["model"] == "claude-haiku-4-5-20251001"


def test_answer_question_baseline_withholds_context_from_client():
    c = ModelCapturingClient()
    answer.answer_question("q?", [("s.md", "SECRET-CTX")], client=c, baseline=True)
    assert "SECRET-CTX" not in c.calls[0]["user"]
