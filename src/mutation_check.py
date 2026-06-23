"""A grader that passes everything is worthless. Seed three known-bad
mutations into a clean (passing) answer set and require each to flip its gate
to fail. Proves the scorer is discriminative.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict

sys.path.insert(0, str(Path(__file__).resolve().parent))
from score_run import score_run  # noqa: E402


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
