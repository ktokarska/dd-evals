# Run provenance

Every artifact committed under `results/` and the command that regenerates it.
Deterministic artifacts (report, plots, mutation check) are reproducible with no
API key; the raw model/judge outputs are the recorded inputs the rest derive from.

| Artifact | How it was produced | Regenerate with |
|----------|--------------------|-----------------|
| `raw/answers.json` | System-under-test answers, model `claude-sonnet-4-6`, temperature 0, retrieval-on. Recorded demo run, committed 2026-06-23 (`8a0214f`). | Live only: `python run_eval.py --mode live --out-dir results` (overwrites raw/) |
| `raw/judge_verdicts.json` | Judge verdicts, model `claude-sonnet-4-6`, temperature 0, rubrics in `judge/rubrics.md`. Same demo run. | Live only (as above) |
| `raw/ground_truth.json` | Hand-authored per-field labels for the demo run: every answer sound except `q13` (fabricated B Corp award). | Manual reference labels |
| `eval_report.json`, `eval_report.md` | Deterministic scoring of `raw/` in replay mode. Byte-identical on re-run. | `python run_eval.py --mode replay --out-dir results` |
| `confusion.png` | Harness verdict vs ground truth. | `python make_report_plots.py results` |
| `reliability.png` | Judge confidence vs agreement with ground truth (9 verdicts, populated bins only). | `python make_report_plots.py results` |
| `mutation_check.json` | Grader self-test: 3 seeded mutations vs the eval set, reference judge, clean answers = gold. Deterministic. | `python src/mutation_check.py` |

**Notes**
- `mode` is `replay` for the committed `eval_report.*` (no network). `live` mode
  is what originally produced `raw/`, and re-running it will overwrite `raw/`.
- The mutation check uses a deterministic reference judge (see
  `src/mutation_check.py`), not the LLM judge, it tests the scorer's gate
  wiring, so it is intentionally offline and reproducible.
- Model id `claude-sonnet-4-6` is recorded as used by the demo run. Verify the
  current id against the API docs before any new live run.
