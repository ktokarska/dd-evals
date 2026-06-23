# Calibrating the judge (operator runbook)

The judged gates (G2 Faithfulness, G5 Answer Relevancy, and any G-Eval prose
field) do not count toward a release decision until the judge is shown to
agree with a human. That human is you.

## The one rule that makes it valid

Write and lock all ten `operator_label` values in `calibration_set.csv` BEFORE
you run the judge. If you change a label after seeing the judge score, you are
fitting yourself to the judge, which defeats the purpose.

## Steps

1. Open `judge/calibration_set.csv`. For each row, read `actual_output` and
   decide yourself whether you would accept it. Put `pass` or `fail` in
   `operator_label`. Keep the two honesty traps (c09 and one other) as fail
   unless you genuinely disagree. Aim for a roughly even split (the converter
   needs at least 4 pass and 4 fail). You may overwrite any `actual_output`
   you find unrealistic; `design_note` is a hint only and is dropped on
   conversion.
2. Convert and validate:
   `python src/calibration_csv_to_jsonl.py --csv judge/calibration_set.csv --out judge/calibration_set.jsonl`
   It refuses to write if anything is missing and names the offending row.
3. Run the judge (the only step that calls the API):
   `export ANTHROPIC_API_KEY=...`
   `python src/judge_calibration.py`
   It writes `judge/calibration_result.json` and prints the agreement.
4. If `agreement >= 0.85`, the judge is calibrated to your standard and the
   judged gates may count. If below, inspect each disagreement: tune the rubric
   in `judge/rubrics.md` where the judge is wrong, or sharpen a borderline
   candidate where your label was genuinely ambiguous. Never relabel an item
   just to raise agreement.
