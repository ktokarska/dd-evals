"""Field-class-aware scorer. Dispatches each field by its method
(exact|tolerance|judge|absent|binary), emits one metric record per field,
aggregates per-gate verdicts and one overall verdict, writes the report.
The judge is injected so aggregation is tested offline.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
from metric_record import MetricRecord, record_to_dict  # noqa: E402

SENTINEL = "Not found in the provided sources."

GATE_THRESHOLDS = {"G1": 1.0, "G2": 0.98, "G3": 1.0, "G4": 1.0, "G5": 0.90}
GATE_METRIC_NAME = {"G2": "Faithfulness", "G5": "Answer Relevancy"}


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", str(s)).strip().casefold()


def _as_number(s: str) -> Optional[float]:
    cleaned = re.sub(r"[,$£€%\s]", "", str(s))
    try:
        return float(cleaned)
    except ValueError:
        return None


def _score_exact(qid, spec, gold, ans) -> MetricRecord:
    g = spec["gate_id"]
    ok = _norm(gold) == _norm(ans)
    reason = "match" if ok else f"{qid} expected {gold!r} got {ans!r}"
    return MetricRecord("deterministic", g, 1.0 if ok else 0.0, GATE_THRESHOLDS[g], ok, reason, field_id=qid)


def _score_tolerance(qid, spec, gold, ans) -> MetricRecord:
    g = spec["gate_id"]
    tol = spec.get("tolerance", {}) or {}
    gv, av = _as_number(gold), _as_number(ans)
    if gv is None or av is None:
        ok = _norm(gold) == _norm(ans)
        reason = "match" if ok else f"{qid} expected {gold!r} got {ans!r} (non-numeric)"
        return MetricRecord("deterministic", g, 1.0 if ok else 0.0, GATE_THRESHOLDS[g], ok, reason, field_id=qid)
    allowed = max(float(tol.get("abs", 0.0)), abs(gv) * float(tol.get("rel", 0.0)))
    ok = abs(av - gv) <= allowed
    reason = "within tolerance" if ok else f"{qid} expected {gold} got {ans} (delta {abs(av-gv):g} > {allowed:g})"
    return MetricRecord("deterministic", g, 1.0 if ok else 0.0, GATE_THRESHOLDS[g], ok, reason, field_id=qid)


def _score_absent(qid, spec, gold, ans) -> MetricRecord:
    g = spec["gate_id"]
    ok = _norm(ans) == _norm(SENTINEL)
    reason = "rendered the not-found sentinel" if ok else f"{qid} must render the sentinel but rendered {ans!r}"
    return MetricRecord("deterministic", g, 1.0 if ok else 0.0, GATE_THRESHOLDS[g], ok, reason, field_id=qid)


_YESNO = re.compile(r"(yes|no)\b")


def _yesno(s: str) -> Optional[str]:
    m = _YESNO.match(_norm(s))
    return m.group(1) if m else None


def _score_binary(qid, spec, gold, ans) -> MetricRecord:
    g = spec["gate_id"]
    gold_yn, ans_yn = _yesno(gold), _yesno(ans)
    ok = gold_yn is not None and gold_yn == ans_yn
    reason = "binary match" if ok else f"{qid} expected {gold_yn!r} got {ans_yn!r} (high-stakes)"
    return MetricRecord("deterministic", g, 1.0 if ok else 0.0, GATE_THRESHOLDS[g], ok, reason, field_id=qid)


def _score_judge(qid, spec, gold, ans, question, context, judge) -> MetricRecord:
    g = spec["gate_id"]
    metric = GATE_METRIC_NAME.get(g, "G-Eval")
    case = {"input": question or qid, "expected_output": gold,
            "actual_output": ans, "retrieval_context": context or ""}
    if metric == "Faithfulness":
        v = judge.run_faithfulness(case)
    elif metric == "Answer Relevancy" or spec.get("relevancy"):
        v = judge.run_answer_relevancy(case)
        metric = "Answer Relevancy"
    else:
        v = judge.run_geval(case)
    score = float(v["score"])
    ok = score >= GATE_THRESHOLDS[g]
    return MetricRecord(metric, g, score, GATE_THRESHOLDS[g], ok, v["reason"], field_id=qid)


def _score_one(qid, spec, gold, ans, question, context, judge) -> MetricRecord:
    method = spec["method"]
    if method == "exact":
        return _score_exact(qid, spec, gold, ans)
    if method == "tolerance":
        return _score_tolerance(qid, spec, gold, ans)
    if method == "absent":
        return _score_absent(qid, spec, gold, ans)
    if method == "binary":
        return _score_binary(qid, spec, gold, ans)
    if method == "judge":
        return _score_judge(qid, spec, gold, ans, question, context, judge)
    raise ValueError(f"unknown method for {qid}: {method!r}")


def score_run(questions: Dict[str, dict], field_keys: Dict[str, dict],
              answers: Dict[str, str], judge: Any,
              contexts: Optional[Dict[str, str]] = None,
              out_dir: Optional[str] = None) -> Dict[str, Any]:
    contexts = contexts or {}
    per_field: List[dict] = []
    gate_results: Dict[str, List[bool]] = {}
    for qid, spec in field_keys.items():
        q = questions[qid]
        gold = q.get("gold_label", q.get("gold_answer", ""))
        ans = answers.get(qid, "")
        rec = _score_one(qid, spec, gold, ans, q.get("question"), contexts.get(qid), judge)
        per_field.append(record_to_dict(rec, include_id=True))
        gate_results.setdefault(spec["gate_id"], []).append(rec.success)

    gates = {g: ("pass" if all(v) else "fail") for g, v in sorted(gate_results.items())}
    overall = "pass" if gates and all(v == "pass" for v in gates.values()) else "fail"
    report = {"per_field": per_field, "gates": gates, "overall": overall}

    if out_dir:
        target = Path(out_dir)
        target.mkdir(parents=True, exist_ok=True)
        (target / "eval_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        (target / "eval_report.md").write_text(_render_md(report), encoding="utf-8")
    return report


def _render_md(report: Dict[str, Any]) -> str:
    lines = [
        "# dd-evals report", "",
        f"**overall: {report['overall']}**", "",
        "## Gates", "", "| Gate | Verdict |", "|------|---------|",
    ]
    for g, v in report["gates"].items():
        lines.append(f"| {g} | {v} |")
    lines += ["", "## Fields", "",
              "| id | metric | gate | score | threshold | success | reason |",
              "|----|--------|------|-------|-----------|---------|--------|"]
    for r in report["per_field"]:
        reason = r["reason"].replace("|", "\\|")
        lines.append(f"| {r['id']} | {r['metric']} | {r['gate_id']} | "
                     f"{r['score']:.2f} | {r['threshold']:.2f} | {r['success']} | {reason} |")
    return "\n".join(lines) + "\n"
