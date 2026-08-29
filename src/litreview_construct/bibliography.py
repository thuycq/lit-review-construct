from __future__ import annotations

import re
import unicodedata
from collections import defaultdict
from itertools import combinations
from typing import Iterable

from rapidfuzz.fuzz import ratio

_DOI_RE = re.compile(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.IGNORECASE)
_NON_WORD_RE = re.compile(r"[^a-z0-9]+")
_BLOCK_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "by",
    "for",
    "from",
    "in",
    "is",
    "of",
    "on",
    "the",
    "to",
    "using",
    "with",
}
_MAX_APPROX_BLOCK = 250


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


def _content_tokens(title: object) -> list[str]:
    normalized = normalize_title(str(title or ""))
    return [token for token in normalized.split() if token not in _BLOCK_STOPWORDS]


def _record_block_keys(record: dict[str, object]) -> set[tuple[str, str]]:
    """Build conservative candidate-generation keys for bibliographic relations.

    DOI and exact-title blocks are lossless for those identifiers. Approximate title blocks are
    only a candidate-generation optimization; final relation decisions still use the stricter
    similarity/author/year rules below.
    """
    keys: set[tuple[str, str]] = set()
    doi = normalize_doi(str(record.get("doi"))) if record.get("doi") else None
    if doi:
        keys.add(("doi", doi))

    normalized = normalize_title(str(record.get("title") or ""))
    if normalized:
        keys.add(("exact_title", normalized))

    tokens = _content_tokens(record.get("title"))
    if len(tokens) >= 3:
        width = min(4, len(tokens))
        keys.add(("prefix", " ".join(tokens[:width])))
        keys.add(("suffix", " ".join(tokens[-width:])))
        if len(tokens) >= 4:
            keys.add(("edges", " ".join(tokens[:2] + tokens[-2:])))

        authors = record.get("authors") if isinstance(record.get("authors"), list) else []
        surnames = sorted(author_tokens(str(value) for value in authors))
        if surnames:
            keys.add(("author_prefix", surnames[0] + "|" + " ".join(tokens[:2])))
    return keys


def _candidate_pairs(records: list[dict[str, object]]) -> set[tuple[int, int]]:
    """Generate likely duplicate/version pairs without all-pairs comparison."""
    blocks: dict[tuple[str, str], list[int]] = defaultdict(list)
    for index, record in enumerate(records):
        for key in _record_block_keys(record):
            blocks[key].append(index)

    pairs: set[tuple[int, int]] = set()
    for (kind, _), indices in blocks.items():
        if len(indices) < 2:
            continue
        # Exact identifiers remain exhaustive. Approximate blocks that become extremely broad
        # are intentionally ignored because they no longer provide useful candidate blocking.
        if kind not in {"doi", "exact_title"} and len(indices) > _MAX_APPROX_BLOCK:
            continue
        for left, right in combinations(indices, 2):
            pairs.add((left, right) if left < right else (right, left))
    return pairs


def detect_relations(records: list[dict[str, object]]) -> list[dict[str, object]]:
    """Detect non-file bibliographic relationships without deleting records.

    Candidate pairs are generated through bibliographic blocking instead of comparing every
    record with every other record. Relation confidence remains intentionally conservative:
    - same DOI => same_work / high confidence;
    - exact normalized title + compatible authors/year => probable_duplicate;
    - very similar title + author overlap => possible_version.

    Ambiguous candidates remain reviewable rather than being silently merged.
    """
    relations: list[dict[str, object]] = []
    for left_index, right_index in sorted(_candidate_pairs(records)):
        left = records[left_index]
        right = records[right_index]
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
