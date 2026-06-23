"""questions.yaml and field_keys.yaml are consistent and cover every gate."""
from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
ES = ROOT / "eval_set"
SENTINEL = "Not found in the provided sources."
METHODS = {"exact", "tolerance", "judge", "absent", "binary"}
GATES = {"G1", "G2", "G3", "G4", "G5"}


def _load():
    q = yaml.safe_load((ES / "questions.yaml").read_text(encoding="utf-8"))
    fk = yaml.safe_load((ES / "field_keys.yaml").read_text(encoding="utf-8"))
    return q, fk


def test_keys_match_across_files():
    q, fk = _load()
    assert set(q) == set(fk)
    assert len(q) >= 20


def test_every_question_is_well_formed():
    q, _ = _load()
    for qid, item in q.items():
        assert item["company"]
        assert item["question"]
        assert "gold_answer" in item
        assert "gold_label" in item
        assert item["source_ref"]


def test_field_keys_use_known_methods_and_gates():
    _, fk = _load()
    for qid, spec in fk.items():
        assert spec["method"] in METHODS, qid
        assert spec["gate_id"] in GATES, qid


def test_all_gates_are_covered():
    _, fk = _load()
    covered = {spec["gate_id"] for spec in fk.values()}
    assert covered == GATES


def test_g3_uses_the_sentinel_and_g4_is_binary():
    q, fk = _load()
    for qid, spec in fk.items():
        if spec["method"] == "absent":
            assert q[qid]["gold_label"] == SENTINEL, qid
        if spec["method"] == "binary":
            assert q[qid]["gold_label"] in {"yes", "no"}, qid


def test_atlas_sanctions_binary_is_yes():
    q, fk = _load()
    binary_atlas = [
        qid for qid, spec in fk.items()
        if spec["method"] == "binary" and "atlas" in q[qid]["company"].lower()
    ]
    assert binary_atlas
    assert all(q[qid]["gold_label"] == "yes" for qid in binary_atlas)
