from __future__ import annotations

import re
import unicodedata
from itertools import combinations
from typing import Iterable

from rapidfuzz.fuzz import ratio

_DOI_RE = re.compile(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.IGNORECASE)
_NON_WORD_RE = re.compile(r"[^a-z0-9]+")


def normalize_doi(value: str | None) -> str | None:
    """Return a canonical DOI string when a DOI can be recognized."""
    if not value:
        return None
    text = value.strip()
    text = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^doi:\s*", "", text, flags=re.IGNORECASE)
    match = _DOI_RE.search(text)
    if not match:
        return None
    return match.group(0).rstrip(".,;)]}").lower()


def extract_doi(text: str | None) -> str | None:
    if not text:
        return None
    match = _DOI_RE.search(text)
    return normalize_doi(match.group(0)) if match else None


def normalize_title(value: str | None) -> str:
    """Normalize titles for comparison without changing the displayed title."""
    if not value:
        return ""
    text = unicodedata.normalize("NFKD", value)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower().replace("&", " and ")
    return " ".join(_NON_WORD_RE.sub(" ", text).split())


def normalize_author(value: str) -> str:
    text = unicodedata.normalize("NFKD", value)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = _NON_WORD_RE.sub(" ", text.lower())
    return " ".join(text.split())


def author_tokens(authors: Iterable[str]) -> set[str]:
    """Create conservative author identity tokens from normalized names."""
    tokens: set[str] = set()
    for author in authors:
        normalized = normalize_author(author)
        if not normalized:
            continue
        parts = normalized.split()
        # Surname/last-token works reasonably for both `Given Family` metadata
        # and abbreviated author lists while remaining intentionally conservative.
        tokens.add(parts[-1])
    return tokens


def author_overlap(left: Iterable[str], right: Iterable[str]) -> float | None:
    a = author_tokens(left)
    b = author_tokens(right)
    if not a or not b:
        return None
    return len(a & b) / max(1, min(len(a), len(b)))


def title_similarity(left: str | None, right: str | None) -> float:
    a = normalize_title(left)
    b = normalize_title(right)
    if not a or not b:
        return 0.0
    return ratio(a, b) / 100.0


def _year_compatible(left: object, right: object) -> bool:
    if left is None or right is None:
        return True
    try:
        return abs(int(left) - int(right)) <= 1
    except (TypeError, ValueError):
        return True


def detect_relations(records: list[dict[str, object]]) -> list[dict[str, object]]:
    """Detect non-file bibliographic relationships without deleting records.

    Relation confidence is intentionally conservative:
    - same DOI => same_work / high confidence;
    - exact normalized title + compatible authors/year => probable_duplicate;
    - very similar title + author overlap => possible_version.

    Ambiguous candidates remain reviewable rather than being silently merged.
    """
    relations: list[dict[str, object]] = []
    for left, right in combinations(records, 2):
        left_id = str(left.get("paper_id"))
        right_id = str(right.get("paper_id"))
        left_doi = normalize_doi(left.get("doi") if isinstance(left.get("doi"), str) else None)
        right_doi = normalize_doi(right.get("doi") if isinstance(right.get("doi"), str) else None)
        similarity = title_similarity(
            left.get("title") if isinstance(left.get("title"), str) else None,
            right.get("title") if isinstance(right.get("title"), str) else None,
        )
        overlap = author_overlap(
            [str(x) for x in left.get("authors", [])] if isinstance(left.get("authors"), list) else [],
            [str(x) for x in right.get("authors", [])] if isinstance(right.get("authors"), list) else [],
        )
        year_ok = _year_compatible(left.get("year"), right.get("year"))

        relation_type: str | None = None
        confidence: str | None = None
        basis: list[str] = []

        if left_doi and right_doi and left_doi == right_doi:
            relation_type = "same_work"
            confidence = "high"
            basis.append("same_doi")
        elif similarity == 1.0 and year_ok and (overlap is None or overlap >= 0.5):
            relation_type = "probable_duplicate"
            confidence = "medium"
            basis.append("same_normalized_title")
            if overlap is not None:
                basis.append("author_overlap")
            if left.get("year") is not None and right.get("year") is not None:
                basis.append("compatible_year")
        elif similarity >= 0.92 and (overlap is None or overlap >= 0.5):
            relation_type = "possible_version"
            confidence = "medium" if overlap is not None else "low"
            basis.append("high_title_similarity")
            if overlap is not None:
                basis.append("author_overlap")

        if relation_type:
            relations.append(
                {
                    "left_paper_id": left_id,
                    "right_paper_id": right_id,
                    "relation": relation_type,
                    "confidence": confidence,
                    "basis": basis,
                    "title_similarity": round(similarity, 4),
                    "author_overlap": round(overlap, 4) if overlap is not None else None,
                    "resolution": "unresolved",
                }
            )

    return relations
