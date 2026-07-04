from __future__ import annotations

import json

import run_eval


def _seed_raw(raw_dir: Path):
    raw_dir.mkdir(parents=True, exist_ok=True)
    (raw_dir / "answers.json").write_text(json.dumps({
        "q01": "NW-4471203",
        "q03": "Yes. A controlling shareholder is listed.",
        "q04": "Not found in the provided sources.",
    }))
    (raw_dir / "judge_verdicts.json").write_text(json.dumps({}))


def test_replay_scores_without_network(tmp_path, monkeypatch):
    # point run_eval at a tiny synthetic eval set + field keys
    out = tmp_path / "results"
    raw = tmp_path / "raw"
    _seed_raw(raw)
    questions = {
        "q01": {"company": "Northwind", "question": "reg?", "gold_answer": "NW-4471203", "gold_label": "NW-4471203", "source_ref": "x"},
        "q03": {"company": "Atlas", "question": "sanctions?", "gold_answer": "yes", "gold_label": "yes", "source_ref": "x"},
        "q04": {"company": "Verdant", "question": "directors?", "gold_answer": "Not found in the provided sources.", "gold_label": "Not found in the provided sources.", "source_ref": "x"},
    }
    field_keys = {
        "q01": {"method": "exact", "gate_id": "G1"},
        "q03": {"method": "binary", "gate_id": "G4"},
        "q04": {"method": "absent", "gate_id": "G3"},
    }
    rep = run_eval.run(mode="replay", out_dir=str(out), raw_dir=str(raw),
                       questions=questions, field_keys=field_keys)
    assert rep["overall"] == "pass"
    assert (out / "eval_report.json").exists()
    assert (out / "confusion.png").exists()
    assert (out / "reliability.png").exists()


def test_baseline_refuses_to_clobber_default_results():
    # A baseline run pointed at the default results/ dir must raise before doing
    # anything, so it can never overwrite the committed retrieval-on results.
    import pytest
    with pytest.raises(ValueError):
        run_eval.run(mode="live", out_dir="results", baseline=True)


def test_model_run_refuses_to_clobber_default_results():
    import pytest
    with pytest.raises(ValueError):
        run_eval.run(mode="live", out_dir="results", model="claude-haiku-4-5-20251001")


def test_baseline_allowed_with_separate_out_dir(tmp_path, monkeypatch):
    # With a separate out-dir the guard passes; we stop before any network call
    # by making the answer client raise, proving the guard is not the blocker.
    import answer as answer_mod
    class BoomClient:
        def __init__(self, *a, **k): raise RuntimeError("would call network")
    monkeypatch.setattr(answer_mod, "AnthropicAnswerClient", BoomClient)
    import pytest
    with pytest.raises(RuntimeError, match="network"):
        run_eval.run(mode="live", out_dir=str(tmp_path / "baseline"), baseline=True)


def test_replay_empty_field_keys_is_not_a_pass(tmp_path):
    out = tmp_path / "results"
    raw = tmp_path / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    (raw / "answers.json").write_text(json.dumps({}))
    (raw / "judge_verdicts.json").write_text(json.dumps({}))
    rep = run_eval.run(mode="replay", out_dir=str(out), raw_dir=str(raw),
                       questions={}, field_keys={})
    assert rep["overall"] == "fail"
