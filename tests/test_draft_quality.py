import json
from pathlib import Path

import pytest

from litreview_construct.draft_quality import validate_working_draft_claim_language
from litreview_construct.project import init_project


def _write_evidence(root: Path, source_basis: str = "abstract") -> None:
    (root / ".litreview" / "data" / "evidence.jsonl").write_text(
        json.dumps({"evidence_id": "e1", "paper_id": "p1", "source_basis": source_basis}) + "\n",
        encoding="utf-8",
    )


def _submission(root: Path, text: str) -> Path:
    path = root / "draft.json"
    path.write_text(
        json.dumps(
            {
                "sections": [
                    {
                        "section_id": "s1",
                        "title": "Section",
                        "fragments": [{"draft_text": text, "evidence_ids": ["e1"]}],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    return path


def test_abstract_support_cannot_be_called_established(tmp_path: Path) -> None:
    init_project(tmp_path)
    _write_evidence(tmp_path, "abstract")
    with pytest.raises(ValueError, match="claim-strength QA failed"):
        validate_working_draft_claim_language(
            tmp_path, _submission(tmp_path, "The relationship is established in the literature.")
        )


def test_unbounded_absence_claim_is_rejected(tmp_path: Path) -> None:
    init_project(tmp_path)
    _write_evidence(tmp_path, "abstract")
    with pytest.raises(ValueError, match="universal absence"):
        validate_working_draft_claim_language(
            tmp_path, _submission(tmp_path, "No direct study examines this relationship in Vietnam.")
        )


def test_corpus_bounded_gap_and_provisional_wording_pass(tmp_path: Path) -> None:
    init_project(tmp_path)
    _write_evidence(tmp_path, "abstract")
    result = validate_working_draft_claim_language(
        tmp_path,
        _submission(
            tmp_path,
            "Within the reviewed corpus, no direct study was identified; available evidence suggests the relationship remains underexplored.",
        ),
    )
    assert result["status"] == "pass"


def test_full_text_basis_may_describe_study_finding_without_researcher_verification(tmp_path: Path) -> None:
    init_project(tmp_path)
    _write_evidence(tmp_path, "full_text")
    result = validate_working_draft_claim_language(
        tmp_path, _submission(tmp_path, "The study demonstrates a statistically significant association in its reported model.")
    )
    assert result["status"] == "pass"
