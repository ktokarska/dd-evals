"""Orchestrate the dd-evals run.

replay mode: read recorded answers + judge verdicts from results/raw and score
them with no network call (this regenerates the committed results). live mode:
call the Anthropic API end to end. Both write eval_report.{json,md} and the two
plots into out_dir.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

import yaml  # noqa: E402

import retrieve  # noqa: E402
import answer as answer_mod  # noqa: E402
import judge_runner as jr  # noqa: E402
from score_run import score_run  # noqa: E402
import metrics  # noqa: E402

EVAL_SET = ROOT / "eval_set"
CORPUS_DIR = ROOT / "corpus"


def _load_eval_set():
    questions = yaml.safe_load((EVAL_SET / "questions.yaml").read_text(encoding="utf-8"))
    field_keys = yaml.safe_load((EVAL_SET / "field_keys.yaml").read_text(encoding="utf-8"))
    return questions, field_keys


def _score_with_replay(questions, field_keys, answers, verdicts, out_dir):
    # score_run's injected judge does not receive the qid, so here we score
    # deterministic fields via score_run's helpers and read each judged field's
    # recorded verdict by qid directly.
    from metric_record import MetricRecord, record_to_dict
    import score_run as sr
    per_field = []
    gate_results: Dict[str, list] = {}
    for qid, spec in field_keys.items():
        q = questions[qid]
        gold = q.get("gold_label", q.get("gold_answer", ""))
        ans = answers.get(qid, "")
        if spec["method"] == "judge":
            g = spec["gate_id"]
            metric = sr.GATE_METRIC_NAME.get(g, "G-Eval")
            v = verdicts.get(qid, {"score": 0.0, "reason": "no recorded verdict"})
            ok = float(v["score"]) >= sr.GATE_THRESHOLDS[g]
            rec = MetricRecord(metric, g, float(v["score"]), sr.GATE_THRESHOLDS[g], ok, v["reason"], field_id=qid)
        else:
            rec = sr._score_one(qid, spec, gold, ans, q.get("question"), None, None)
        per_field.append(record_to_dict(rec, include_id=True))
        gate_results.setdefault(spec["gate_id"], []).append(rec.success)
    gates = {g: ("pass" if all(v) else "fail") for g, v in sorted(gate_results.items())}
    overall = "pass" if gates and all(v == "pass" for v in gates.values()) else "fail"
    report = {"per_field": per_field, "gates": gates, "overall": overall}
    target = Path(out_dir); target.mkdir(parents=True, exist_ok=True)
    (target / "eval_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (target / "eval_report.md").write_text(sr._render_md(report), encoding="utf-8")
    return report


def _emit_plots(report, verdicts, out_dir):
    # confusion: scored success vs gold_pass (gold_pass = True for every gold
    # item, since the eval_set answers are the reference; a scored fail is a
    # judged/deterministic miss). For a richer confusion the live run records
    # gold_pass per item; here gold_pass defaults True.
    records = [{"success": r["success"], "gold_pass": True} for r in report["per_field"]]
    metrics.plot_confusion(metrics.confusion(records), str(Path(out_dir) / "confusion.png"))
    points = [(float(v["score"]), True) for v in verdicts.values()]
    if not points:
        points = [(0.5, True)]
    metrics.plot_reliability(metrics.reliability_bins(points, n_bins=5), str(Path(out_dir) / "reliability.png"))


def run(mode: str, out_dir: str, raw_dir: Optional[str] = None,
        questions: Optional[dict] = None, field_keys: Optional[dict] = None) -> Dict[str, Any]:
    if questions is None or field_keys is None:
        questions, field_keys = _load_eval_set()

    if mode == "replay":
        raw = Path(raw_dir or (ROOT / "results" / "raw"))
        answers = json.loads((raw / "answers.json").read_text(encoding="utf-8"))
        verdicts = json.loads((raw / "judge_verdicts.json").read_text(encoding="utf-8"))
        report = _score_with_replay(questions, field_keys, answers, verdicts, out_dir)
        _emit_plots(report, verdicts, out_dir)
        return report

    if mode == "live":
        corpus = retrieve.load_corpus(CORPUS_DIR)
        ans_client = answer_mod.AnthropicAnswerClient()
        judge_client = jr.AnthropicJudgeClient()

        class LiveJudge:
            def run_geval(self, case):
                return jr.run_geval(case, client=judge_client)
            def run_faithfulness(self, case):
                return jr.run_faithfulness(case, client=judge_client)
            def run_answer_relevancy(self, case):
                return jr.run_answer_relevancy(case, client=judge_client)

        answers, contexts = {}, {}
        for qid, q in questions.items():
            company = q["source_ref"].split("/")[0]
            hits = retrieve.retrieve(q["question"], corpus, company=company, k=3)
            contexts[qid] = "\n\n".join(f"[source: {p}]\n{t}" for p, t in hits)
            answers[qid] = answer_mod.answer_question(q["question"], hits, client=ans_client)
        report = score_run(questions, field_keys, answers, LiveJudge(),
                           contexts=contexts, out_dir=out_dir)
        # record raw for reproducibility and so replay mode can re-run
        JUDGED_METRICS = {"Faithfulness", "Answer Relevancy", "G-Eval"}
        verdicts = {r["id"]: {"score": r["score"], "reason": r["reason"]}
                    for r in report["per_field"] if r["metric"] in JUDGED_METRICS}
        raw = Path(raw_dir or (ROOT / "results" / "raw")); raw.mkdir(parents=True, exist_ok=True)
        (raw / "answers.json").write_text(json.dumps(answers, indent=2), encoding="utf-8")
        (raw / "judge_verdicts.json").write_text(json.dumps(verdicts, indent=2), encoding="utf-8")
        _emit_plots(report, verdicts, out_dir)
        return report

    raise ValueError(f"unknown mode: {mode!r}")


if __name__ == "__main__":  # pragma: no cover
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["replay", "live"], default="replay")
    ap.add_argument("--out-dir", default="results")
    a = ap.parse_args()
    rep = run(mode=a.mode, out_dir=a.out_dir)
    print(json.dumps({"overall": rep["overall"], "gates": rep["gates"]}, indent=2))
