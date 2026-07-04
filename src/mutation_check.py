"""A grader that passes everything is worthless. Seed three known-bad
mutations into a clean (passing) answer set and require each to flip its gate
to fail. Proves the scorer is discriminative.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from score_run import score_run


def _first_qid_for_gate(field_keys: Dict[str, dict], gate_id: str, method: str = None):
    for qid, spec in field_keys.items():
        if spec["gate_id"] == gate_id and (method is None or spec["method"] == method):
            return qid
    return None


def run_mutation_check(questions: Dict[str, dict], field_keys: Dict[str, dict],
                       clean_answers: Dict[str, str], judge: Any) -> Dict[str, Any]:
    baseline = score_run(questions, field_keys, clean_answers, judge)

    mutations = []

    # 1) flip a G1 exact field
    g1 = _first_qid_for_gate(field_keys, "G1", "exact")
    if g1:
        ans = dict(clean_answers)
        ans[g1] = clean_answers[g1] + "_WRONG"
        rep = score_run(questions, field_keys, ans, judge)
        mutations.append({"name": f"flip exact field {g1}", "gate_id": "G1",
                          "caught": rep["gates"].get("G1") == "fail"})

    # 2) blank a G2 judged answer
    g2 = _first_qid_for_gate(field_keys, "G2", "judge")
    if g2:
        ans = dict(clean_answers)
        ans[g2] = ""
        rep = score_run(questions, field_keys, ans, judge)
        mutations.append({"name": f"blank judged answer {g2}", "gate_id": "G2",
                          "caught": rep["gates"].get("G2") == "fail"})

    # 3) flip a G4 binary from yes to no (a missed sanctions hit)
    g4 = _first_qid_for_gate(field_keys, "G4", "binary")
    if g4:
        ans = dict(clean_answers)
        ans[g4] = "no"
        rep = score_run(questions, field_keys, ans, judge)
        mutations.append({"name": f"flip binary {g4} yes->no", "gate_id": "G4",
                          "caught": rep["gates"].get("G4") == "fail"})

    return {"baseline_overall": baseline["overall"], "mutations": mutations,
            "all_caught": all(m["caught"] for m in mutations) and len(mutations) == 3}


class _ReferenceJudge:
    """Deterministic stand-in judge for the mutation check. The mutation check
    exercises the *scorer's* gate wiring, not judge quality, so a reference
    judge that credits an answer only when it exactly matches the gold (and is
    non-empty) is sufficient and keeps the check offline and reproducible. It
    scores the clean set 1.0 and any blanked/altered judged answer 0.0.
    """
    @staticmethod
    def _score(case):
        a = case["actual_output"].strip()
        return {"score": 1.0 if a and case["actual_output"] == case["expected_output"] else 0.0,
                "reason": "reference"}
    def run_geval(self, case):
        return self._score(case)
    def run_faithfulness(self, case):
        return self._score(case)
    def run_answer_relevancy(self, case):
        return {"score": 1.0 if case["actual_output"].strip() else 0.0, "reason": "reference"}


def main() -> None:
    """Regenerate results/mutation_check.json against the committed eval set.

    The clean answer set is the gold answer for every field (so the baseline
    passes); the reference judge above stands in for the LLM judge. This is a
    grader self-test — it proves the scorer flips the right gate when a known-bad
    answer is injected — and is fully deterministic, so the committed JSON is
    reproducible with no API key.
    """
    import json
    import yaml

    root = Path(__file__).resolve().parents[1]
    questions = yaml.safe_load((root / "eval_set" / "questions.yaml").read_text(encoding="utf-8"))
    field_keys = yaml.safe_load((root / "eval_set" / "field_keys.yaml").read_text(encoding="utf-8"))
    clean = {qid: str(questions[qid].get("gold_label", questions[qid].get("gold_answer", "")))
             for qid in field_keys}
    result = run_mutation_check(questions, field_keys, clean, _ReferenceJudge())
    out = root / "results" / "mutation_check.json"
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out} — all_caught={result['all_caught']}, baseline={result['baseline_overall']}")


if __name__ == "__main__":  # pragma: no cover
    main()
