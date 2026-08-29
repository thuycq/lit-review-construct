from litreview_construct.bibliography import (
    _candidate_pairs,
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
            "Working Capital Management and Firms Performance",
            authors=["Anh Nguyen"],
            year=2024,
        ),
    ]
    relations = detect_relations(records)
    assert len(relations) == 1
    assert relations[0]["relation"] == "possible_version"


def test_candidate_blocking_avoids_all_pairs_on_large_corpus() -> None:
    records = [
        _paper(
            f"p{index}",
            f"Topic{index:04d} evidence on corporate finance outcome{index:04d}",
            authors=[f"Author Surname{index:04d}"],
            year=2020 + (index % 6),
        )
        for index in range(2000)
    ]
    # A strong DOI match must still be generated even when the corpus is large.
    records.extend(
        [
            _paper(
                "doi-a",
                "Liquidity policy in manufacturing firms",
                doi="10.9999/scale-test",
                authors=["A. Researcher"],
                year=2023,
            ),
            _paper(
                "doi-b",
                "A differently titled accepted manuscript",
                doi="https://doi.org/10.9999/SCALE-TEST",
                authors=["A. Researcher"],
                year=2024,
            ),
        ]
    )

    pairs = _candidate_pairs(records)
    all_pairs = len(records) * (len(records) - 1) // 2

    assert all_pairs > 2_000_000
    assert len(pairs) < 100
    assert (2000, 2001) in pairs

    relations = detect_relations(records)
    doi_relation = next(row for row in relations if row["relation"] == "same_work")
    assert {doi_relation["left_paper_id"], doi_relation["right_paper_id"]} == {
        "doi-a",
        "doi-b",
    }
