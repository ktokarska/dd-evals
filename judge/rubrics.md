# dd-evals judge rubrics

Pinned rubrics for the hand-rolled judge. Model: `claude-sonnet-4-6`,
temperature 0. The `evaluation_steps` are sent verbatim; the judge does not
generate its own steps. Every rubric returns `{score, reason}` with score in
0.0..1.0 and a mandatory reason.

## Rubric: G-Eval

Compares the agent answer against the golden answer for the same question.

`evaluation_steps`:
1. Read the question, the golden answer, and the agent answer.
2. Check factual agreement: the agent answer asserts the same material facts,
   with nothing contradicted or invented.
3. Check completeness: every material point in the golden answer is covered.
4. Check honesty: if the golden answer is "Not found in the provided sources.",
   the agent answer must be that exact sentinel; any invented content scores 0.0.

Score definition: 1.0 equivalent to golden; 0.75 minor non-material drift;
0.5 one material point missing; 0.25 multiple missing or one clear error;
0.0 contradicts golden, invents content, or fails the honesty check.

`reason`: one or two sentences naming the deciding factor.

## Rubric: Faithfulness

Claim-decomposition over the cited source.

`evaluation_steps`:
1. Decompose the agent answer into atomic claims (one assertion each).
2. For each claim, locate the supporting passage in the cited context.
3. Mark each claim Supported, Contradicted, or Unsupported.
4. Use only the supplied context; no outside knowledge.

Score definition: score = supported_claims / total_claims; any Contradicted
claim forces score = 0.0.

`reason`: list the unsupported or contradicted claims, or state "all N claims
supported by cited context".

## Rubric: Answer Relevancy

`evaluation_steps`:
1. Read the question and the agent answer.
2. Decompose the answer into statements.
3. Mark each statement Relevant or Irrelevant to the question.
4. A "Not found in the provided sources." answer is Relevant when the fact is
   genuinely absent.

Score definition: score = relevant_statements / total_statements.

`reason`: name the irrelevant statements, or state "answer fully on-topic".
