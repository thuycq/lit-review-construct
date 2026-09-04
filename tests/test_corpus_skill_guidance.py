from pathlib import Path


def test_corpus_skill_requires_explainable_checkpoint_guidance() -> None:
    text = Path("skills/litreview-corpus/SKILL.md").read_text(encoding="utf-8")

    required = [
        "Mandatory checkpoint explanation contract",
        "How papers will be reduced",
        "Coverage safeguard",
        "What happens to non-selected papers",
        "A recommendation with a reason",
        "Research relevance",
        "Capped citation/anchor value",
        "Research-stream coverage",
        "Adaptive reduction size",
        "Retained -> Evidence Candidates",
        "Evidence Candidates -> Core Papers",
        "metadata/abstract is not full-text analysis",
    ]
    for phrase in required:
        assert phrase in text


def test_corpus_skill_explains_nonselected_papers_are_preserved() -> None:
    text = Path("skills/litreview-corpus/SKILL.md").read_text(encoding="utf-8")
    assert "they are not deleted" in text
    assert "can be revisited later" in text
