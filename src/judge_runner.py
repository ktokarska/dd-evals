"""Hand-rolled judge for dd-evals. The only network egress is the Anthropic
call in AnthropicJudgeClient. The judge sends explicit evaluation_steps from
rubrics.md verbatim, at temperature 0 on claude-sonnet-4-6, and parses back
{score, reason}. Unit tests inject a fake client and never touch the network.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

MODEL = "claude-sonnet-4-6"
TEMPERATURE = 0

_HERE = Path(__file__).resolve().parent
_JUDGE_DIR = _HERE.parent / "judge"
RUBRICS_PATH = _JUDGE_DIR / "rubrics.md"
PROMPT_PATH = _JUDGE_DIR / "judge_prompt.md"


class JudgeParseError(RuntimeError):
    """The judge returned output that could not be parsed as {score, reason}."""


class AnthropicJudgeClient:
    """Real client. Requires `pip install anthropic` and ANTHROPIC_API_KEY."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        import anthropic  # lazy so the harness loads without the SDK
        self._client = anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()

    def complete(self, *, model: str, temperature: float, system: str, user: str) -> str:
        resp = self._client.messages.create(
            model=model, max_tokens=512, temperature=temperature,
            system=system, messages=[{"role": "user", "content": user}],
        )
        return "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")


def _split_prompt(text: str) -> Tuple[str, str]:
    sys_m = re.search(r"## System\s*\n(.*?)\n## User", text, re.DOTALL)
    usr_m = re.search(r"## User\s*\n(.*)$", text, re.DOTALL)
    if not sys_m or not usr_m:
        raise JudgeParseError("judge_prompt.md missing ## System / ## User")
    return sys_m.group(1).strip(), usr_m.group(1).strip()


def _load_rubric(title: str) -> Dict[str, str]:
    text = RUBRICS_PATH.read_text(encoding="utf-8")
    pat = re.compile(r"## Rubric:\s*" + re.escape(title) + r".*?(?=\n## |\Z)", re.DOTALL)
    m = pat.search(text)
    if not m:
        raise JudgeParseError(f"rubric not found: {title}")
    block = m.group(0)
    steps_m = re.search(r"`evaluation_steps`:\s*\n(.*?)\n\s*\n", block, re.DOTALL)
    score_m = re.search(r"[Ss]core definition[^\n]*:\s*(.*?)\n\s*\n`reason`", block, re.DOTALL)
    if not steps_m or not score_m:
        raise JudgeParseError(f"rubric {title} missing steps or score definition")
    return {"steps": steps_m.group(1).strip(), "score_def": score_m.group(1).strip()}


def _build_user(rubric_name: str, rubric: Dict[str, str], case: Dict[str, Any], tpl: str) -> str:
    return (tpl
            .replace("{rubric_name}", rubric_name)
            .replace("{evaluation_steps}", rubric["steps"])
            .replace("{score_definition}", rubric["score_def"])
            .replace("{input}", str(case.get("input", "")))
            .replace("{expected_output}", str(case.get("expected_output", "")))
            .replace("{actual_output}", str(case.get("actual_output", "")))
            .replace("{retrieval_context}", str(case.get("retrieval_context", ""))))


def _parse(raw: str) -> Dict[str, Any]:
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if not m:
        raise JudgeParseError(f"no JSON object in judge reply: {raw[:120]!r}")
    obj = json.loads(m.group(0))
    if "score" not in obj or "reason" not in obj:
        raise JudgeParseError(f"judge reply missing score/reason: {obj}")
    score = max(0.0, min(1.0, float(obj["score"])))
    return {"score": score, "reason": str(obj["reason"])}


def _run(title: str, case: Dict[str, Any], client: Any) -> Dict[str, Any]:
    rubric = _load_rubric(title)
    system, user_tpl = _split_prompt(PROMPT_PATH.read_text(encoding="utf-8"))
    user = _build_user(title, rubric, case, user_tpl)
    last: Optional[Exception] = None
    for _ in range(2):
        raw = client.complete(model=MODEL, temperature=TEMPERATURE, system=system, user=user)
        try:
            return _parse(raw)
        except (JudgeParseError, ValueError, json.JSONDecodeError) as exc:
            last = exc
    raise JudgeParseError(f"judge output unparseable after retry: {last}")


def run_geval(case: Dict[str, Any], client: Any) -> Dict[str, Any]:
    return _run("G-Eval", case, client)


def run_faithfulness(case: Dict[str, Any], client: Any) -> Dict[str, Any]:
    return _run("Faithfulness", case, client)


def run_answer_relevancy(case: Dict[str, Any], client: Any) -> Dict[str, Any]:
    return _run("Answer Relevancy", case, client)
