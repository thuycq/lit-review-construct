from litreview_construct.bibliography import (
    detect_relations,
    normalize_doi,
    normalize_title,
)


def _paper(
    paper_id: str,
    title: str,
    *,
    doi: str | None = None,
    authors: list[str] | None = None,
    year: int | None = None,
) -> dict[str, object]:
    return {
        "paper_id": paper_id,
        "title": title,
        "doi": doi,
        "authors": authors or [],
        "year": year,
    }


def test_normalize_doi() -> None:
    assert normalize_doi("https://doi.org/10.1234/ABC.5") == "10.1234/abc.5"
    assert normalize_doi("doi: 10.5555/Test-1.") == "10.5555/test-1"


def test_normalize_title_is_conservative() -> None:
    assert normalize_title("ESG & Firm Performance: Evidence") == (
        "esg and firm performance evidence"
    )


def test_same_doi_is_high_confidence_same_work() -> None:
    records = [
        _paper("a", "Title A", doi="10.1234/ABC", authors=["Jane Smith"]),
        _paper("b", "A revised title", doi="https://doi.org/10.1234/abc", authors=["J. Smith"]),
    ]
    relations = detect_relations(records)
    assert len(relations) == 1
    assert relations[0]["relation"] == "same_work"
    assert relations[0]["confidence"] == "high"
    assert relations[0]["resolution"] == "unresolved"


def test_exact_normalized_title_becomes_probable_duplicate() -> None:
    records = [
        _paper(
            "a",
            "Working Capital and Firm Performance",
            authors=["Anh Nguyen", "John Lee"],
            year=2024,
        ),
        _paper(
            "b",
            "Working Capital & Firm Performance",
            authors=["A. Nguyen", "J. Lee"],
            year=2024,
        ),
    ]
    relations = detect_relations(records)
    assert len(relations) == 1
    assert relations[0]["relation"] == "probable_duplicate"


def test_similar_title_can_be_possible_version() -> None:
    records = [
        _paper(
            "a",
            "Working Capital Management and Firm Performance",
            authors=["Anh Nguyen"],
            year=2022,
        ),
        _paper(
            "b",
            "Working Capital Management and Firm Performance: New Evidence",
            authors=["Anh Nguyen"],
            year=2024,
        ),
    ]
    relations = detect_relations(records)
    assert len(relations) == 1
    assert relations[0]["relation"] == "possible_version"
