"""Every corpus document is fictional-stamped, and MANIFEST lists every file."""
from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "corpus"
STAMP = "Fictional entity, for testing only. No real entity is described."


def _doc_paths():
    return sorted(p for p in CORPUS.rglob("*.md"))


def test_corpus_has_four_companies():
    companies = sorted(d.name for d in CORPUS.iterdir() if d.is_dir())
    assert companies == [
        "atlas_offset_holdings",
        "meridian_carbon_partners",
        "northwind_restoration",
        "verdant_capital_ltd",
    ]


def test_every_doc_carries_the_fictional_stamp():
    docs = _doc_paths()
    assert docs, "no corpus documents found"
    for p in docs:
        assert STAMP in p.read_text(encoding="utf-8"), f"missing stamp: {p}"


def test_manifest_lists_every_doc():
    manifest = yaml.safe_load((CORPUS / "MANIFEST.yaml").read_text(encoding="utf-8"))
    listed = {entry["path"] for entry in manifest["documents"]}
    on_disk = {str(p.relative_to(CORPUS)) for p in _doc_paths()}
    assert listed == on_disk
    for entry in manifest["documents"]:
        assert entry["source_type"] in {"registry", "adverse_media", "press_release", "sanctions_check"}
        assert entry["retrieved"]  # a date string


def test_atlas_has_a_sanctions_match_and_northwind_does_not():
    atlas = (CORPUS / "atlas_offset_holdings" / "sanctions_check.md").read_text(encoding="utf-8")
    northwind = (CORPUS / "northwind_restoration" / "sanctions_check.md").read_text(encoding="utf-8")
    assert "Match found" in atlas
    assert "No matches found" in northwind
