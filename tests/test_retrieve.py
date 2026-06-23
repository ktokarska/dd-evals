from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import retrieve

CORPUS_DIR = Path(__file__).resolve().parents[1] / "corpus"


def test_load_corpus_returns_relpaths():
    corpus = retrieve.load_corpus(CORPUS_DIR)
    assert "northwind_restoration/registry_extract.md" in corpus
    assert corpus["northwind_restoration/registry_extract.md"].strip()


def test_retrieve_surfaces_the_sanctions_doc_for_a_sanctions_question():
    corpus = retrieve.load_corpus(CORPUS_DIR)
    hits = retrieve.retrieve("Is there a sanctions match?", corpus,
                             company="atlas_offset_holdings", k=2)
    paths = [p for p, _ in hits]
    assert any("sanctions_check" in p for p in paths)
    assert all(p.startswith("atlas_offset_holdings/") for p in paths)


def test_retrieve_respects_k():
    corpus = retrieve.load_corpus(CORPUS_DIR)
    hits = retrieve.retrieve("directors of record", corpus, k=1)
    assert len(hits) == 1
