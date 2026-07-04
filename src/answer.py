"""The system-under-test: answers a DD question from cited context. The client
is injected; AnthropicAnswerClient is the live path. In baseline mode the
context is withheld (closed-book) so we can measure the lift from retrieval.
"""
from __future__ import annotations

from typing import Any, List, Optional, Tuple

MODEL = "claude-sonnet-4-6"
SENTINEL = "Not found in the provided sources."

SYSTEM = (
    "You answer counterparty due-diligence questions using only the cited "
    "sources provided. Cite the source filename for each claim. If the answer "
    f"is not in the sources, reply exactly: {SENTINEL} "
    "For a yes/no question, begin with Yes or No."
)


class AnthropicAnswerClient:
    def __init__(self, api_key: Optional[str] = None) -> None:
        import anthropic
        self._client = anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()

    def complete(self, *, model: str, system: str, user: str) -> str:
        resp = self._client.messages.create(
            model=model, max_tokens=512, temperature=0,
            system=system, messages=[{"role": "user", "content": user}],
        )
        return "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")


def build_prompt(question: str, contexts: List[Tuple[str, str]],
                 baseline: bool = False) -> Tuple[str, str]:
    if baseline:
        user = f"Question: {question}\n\n(No sources provided.)"
    else:
        blocks = "\n\n".join(f"[source: {path}]\n{text}" for path, text in contexts)
        user = f"Sources:\n{blocks}\n\nQuestion: {question}"
    return SYSTEM, user


def answer_question(question: str, contexts: List[Tuple[str, str]],
                    client: Any, baseline: bool = False,
                    model: str = MODEL) -> str:
    system, user = build_prompt(question, contexts, baseline=baseline)
    return client.complete(model=model, system=system, user=user).strip()
