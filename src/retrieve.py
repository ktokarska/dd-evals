"""Lexical retrieval over the frozen corpus. No embeddings: a transparent
token-overlap score keeps v1 dependency-free and fully reproducible.
"""
from __future__ import annotations

import math
import re
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional, Tuple

_TOKEN = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> List[str]:
    return _TOKEN.findall(text.lower())


def load_corpus(corpus_dir) -> Dict[str, str]:
    base = Path(corpus_dir)
    out: Dict[str, str] = {}
    for p in sorted(base.rglob("*.md")):
        out[str(p.relative_to(base))] = p.read_text(encoding="utf-8")
    return out


def _score(q_tokens: List[str], doc_tokens: List[str]) -> float:
    if not doc_tokens:
        return 0.0
    doc_counts = Counter(doc_tokens)
    # tf weighting with a log dampener; overlap of distinct query tokens
    overlap = 0.0
    for t in set(q_tokens):
        if t in doc_counts:
            overlap += 1.0 + math.log(doc_counts[t])
    return overlap


def retrieve(question: str, corpus: Dict[str, str],
             company: Optional[str] = None, k: int = 3) -> List[Tuple[str, str]]:
    q_tokens = _tokens(question)
    items = corpus.items()
    if company:
        items = [(p, t) for p, t in items if p.startswith(f"{company}/")]
    scored = [(self_path, text, _score(q_tokens, _tokens(text))) for self_path, text in items]
    scored.sort(key=lambda r: r[2], reverse=True)
    return [(p, t) for p, t, _ in scored[:k]]
