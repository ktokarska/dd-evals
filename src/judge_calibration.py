"""Judge-vs-human agreement gate. Runs the judge on each operator-labelled
item, thresholds the score per rubric into pass/fail, compares to the
operator_label, and gates at >= 0.85 agreement.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

THRESHOLDS = {"geval": 0.80, "faithfulness": 0.98, "answer_relevancy": 0.80}
GATE = 0.85


def _judge_for(rubric: str, judge: Any):
    return {
        "geval": judge.run_geval,
        "faithfulness": judge.run_faithfulness,
        "answer_relevancy": judge.run_answer_relevancy,
    }[rubric]


def compute_agreement(items: List[Dict[str, Any]], judge: Any) -> Dict[str, Any]:
    per_item: Dict[str, Any] = {}
    agree = 0
    for it in items:
        case = {k: it.get(k, "") for k in ("input", "expected_output", "actual_output", "retrieval_context")}
        verdict = _judge_for(it["rubric"], judge)(case)
        judge_label = "pass" if verdict["score"] >= THRESHOLDS[it["rubric"]] else "fail"
        matched = judge_label == it["operator_label"].strip()
        agree += 1 if matched else 0
        per_item[it["id"]] = {"judge_label": judge_label, "operator_label": it["operator_label"].strip(),
                              "score": verdict["score"], "matched": matched}
    agreement = agree / len(items) if items else 0.0
    return {"agreement": agreement, "passed_gate": agreement >= GATE, "per_item": per_item}


def _load_jsonl(path: str) -> List[Dict[str, Any]]:
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


if __name__ == "__main__":  # pragma: no cover
    from judge_runner import AnthropicJudgeClient
    import judge_runner as jr

    class Adapter:
        def __init__(self, client):
            self.c = client
        def run_geval(self, case):
            return jr.run_geval(case, client=self.c)
        def run_faithfulness(self, case):
            return jr.run_faithfulness(case, client=self.c)
        def run_answer_relevancy(self, case):
            return jr.run_answer_relevancy(case, client=self.c)

    items = _load_jsonl("judge/calibration_set.jsonl")
    out = compute_agreement(items, Adapter(AnthropicJudgeClient()))
    Path("judge/calibration_result.json").write_text(json.dumps(out, indent=2))
    print(json.dumps({"agreement": out["agreement"], "passed_gate": out["passed_gate"]}, indent=2))
    sys.exit(0 if out["passed_gate"] else 1)
