from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

import httpx
from pypdf import PdfReader

from .activity import append_activity
from .project import PROJECT_DIR, _atomic_write_text, _write_json

OPENALEX_BASE_URL = "https://api.openalex.org"
S2_BASE_URL = "https://api.semanticscholar.org/graph/v1"
UNPAYWALL_BASE_URL = "https://api.unpaywall.org/v2"
VERSION_RANK = {"publishedVersion": 0, "acceptedVersion": 1, "submittedVersion": 2}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_json(path: Path) -> dict[str, object] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _load_jsonl(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    _atomic_write_text(path, "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows))


def _project_root(root: Path) -> Path:
    root = root.expanduser().resolve()
    if not (root / PROJECT_DIR / "project.yaml").exists():
        raise FileNotFoundError(f"No Lit Review Construct project found at {root}")
    return root


def _has_local_full_text(row: dict[str, object]) -> bool:
    return bool(row.get("file_reference") or row.get("file_hash"))


def _priority_ids(root: Path, records: list[dict[str, object]], explicit: list[str] | None, max_papers: int) -> list[str]:
    known = {str(row.get("paper_id")) for row in records if row.get("paper_id")}
    if explicit:
        unknown = sorted(set(explicit) - known)
        if unknown:
            raise ValueError("Unknown paper IDs for full-text acquisition: " + ", ".join(unknown))
        return list(dict.fromkeys(explicit))[:max_papers]

    state_root = root / PROJECT_DIR
    ordered: list[str] = []
    seen: set[str] = set()

    def add(values: Any) -> None:
        for value in values or []:
            paper_id = str(value)
            if paper_id in known and paper_id not in seen:
                seen.add(paper_id)
                ordered.append(paper_id)

    blueprint = _load_json(state_root / "data" / "blueprint.json")
    if blueprint:
        for section in blueprint.get("sections") or []:
            if isinstance(section, dict):
                add(section.get("anchor_paper_ids"))
                add(section.get("supporting_paper_ids"))
                add(section.get("conflicting_paper_ids"))

    direction = _load_json(state_root / "data" / "selected_direction.json")
    if direction:
        add(direction.get("supporting_paper_ids"))
        add(direction.get("anchor_paper_ids"))

    landscape = _load_json(state_root / "data" / "landscape.json")
    if landscape:
        add(landscape.get("anchor_paper_ids"))
        for stream in landscape.get("streams") or []:
            if isinstance(stream, dict):
                add(stream.get("anchor_paper_ids"))
                add(stream.get("paper_ids"))

    priority_rank = {"core_candidate": 0, "high": 1, "medium": 2, "low": 3}
    fallback = sorted(
        (
            row
            for row in records
            if row.get("triage_label") in {"relevant", "background", "adjacent"}
        ),
        key=lambda row: (
            priority_rank.get(str(row.get("triage_priority") or "medium"), 9),
            -(int(row.get("citation_count") or 0)),
            -(int(row.get("year") or 0)),
        ),
    )
    add([row.get("paper_id") for row in fallback])
    return ordered[:max_papers]


def _candidate(
    *,
    provider: str,
    pdf_url: str | None,
    landing_url: str | None,
    version: str | None,
    license_value: str | None,
    host_type: str | None = None,
) -> dict[str, object] | None:
    if not pdf_url and not landing_url:
        return None
    return {
        "provider": provider,
        "pdf_url": pdf_url,
        "landing_url": landing_url,
        "version": version,
        "license": license_value,
        "host_type": host_type,
    }


def _openalex_candidates(client: httpx.Client, row: dict[str, object]) -> tuple[list[dict[str, object]], str | None]:
    api_key = os.getenv("OPENALEX_API_KEY")
    params: dict[str, object] = {}
    if api_key:
        params["api_key"] = api_key
    work: dict[str, object] | None = None
    openalex_id = str(row.get("openalex_id") or "")
    if openalex_id:
        identifier = openalex_id.rsplit("/", 1)[-1]
        response = client.get(f"{OPENALEX_BASE_URL}/works/{identifier}", params=params)
        response.raise_for_status()
        work = response.json()
    elif row.get("doi"):
        params["filter"] = f"doi:https://doi.org/{row['doi']}"
        params["per_page"] = 1
        response = client.get(f"{OPENALEX_BASE_URL}/works", params=params)
        response.raise_for_status()
        results = response.json().get("results") or []
        if results:
            work = results[0]
    if not work:
        return [], None

    candidates: list[dict[str, object]] = []
    locations = []
    best = work.get("best_oa_location")
    if isinstance(best, dict):
        locations.append(best)
    for location in work.get("locations") or []:
        if isinstance(location, dict) and location.get("is_oa"):
            locations.append(location)
    seen: set[tuple[str | None, str | None]] = set()
    for location in locations:
        if not isinstance(location, dict):
            continue
        pdf_url = str(location.get("pdf_url")) if location.get("pdf_url") else None
        landing = str(location.get("landing_page_url")) if location.get("landing_page_url") else None
        key = (pdf_url, landing)
        if key in seen:
            continue
        seen.add(key)
        source = location.get("source") if isinstance(location.get("source"), dict) else {}
        item = _candidate(
            provider="openalex",
            pdf_url=pdf_url,
            landing_url=landing,
            version=str(location.get("version")) if location.get("version") else None,
            license_value=str(location.get("license")) if location.get("license") else None,
            host_type=str(source.get("type")) if isinstance(source, dict) and source.get("type") else None,
        )
        if item:
            candidates.append(item)
    resolved_id = str(work.get("id")) if work.get("id") else None
    return candidates, resolved_id


def _s2_candidates(client: httpx.Client, row: dict[str, object]) -> tuple[list[dict[str, object]], str | None]:
    identifier = str(row.get("s2_paper_id") or "")
    if not identifier and row.get("doi"):
        identifier = f"DOI:{row['doi']}"
    if not identifier:
        return [], None
    headers: dict[str, str] = {}
    api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY")
    if api_key:
        headers["x-api-key"] = api_key
    encoded = quote(identifier, safe=":")
    response = client.get(
        f"{S2_BASE_URL}/paper/{encoded}",
        params={"fields": "title,isOpenAccess,openAccessPdf,externalIds"},
        headers=headers,
    )
    if response.status_code == 404:
        return [], None
    response.raise_for_status()
    payload = response.json()
    oa = payload.get("openAccessPdf") if isinstance(payload.get("openAccessPdf"), dict) else {}
    if not payload.get("isOpenAccess") and not oa:
        return [], str(payload.get("paperId")) if payload.get("paperId") else None
    url = str(oa.get("url")) if isinstance(oa, dict) and oa.get("url") else None
    status = str(oa.get("status")) if isinstance(oa, dict) and oa.get("status") else None
    item = _candidate(
        provider="semantic_scholar",
        pdf_url=url,
        landing_url=None,
        version=status,
        license_value=None,
    )
    return ([item] if item else []), str(payload.get("paperId")) if payload.get("paperId") else None


def _unpaywall_candidates(client: httpx.Client, row: dict[str, object]) -> list[dict[str, object]]:
    doi = str(row.get("doi") or "")
    email = os.getenv("UNPAYWALL_EMAIL") or os.getenv("CROSSREF_MAILTO")
    if not doi or not email:
        return []
    response = client.get(f"{UNPAYWALL_BASE_URL}/{quote(doi, safe='')}", params={"email": email})
    if response.status_code in {404, 422}:
        return []
    response.raise_for_status()
    payload = response.json()
    if not payload.get("is_oa"):
        return []
    locations = []
    best = payload.get("best_oa_location")
    if isinstance(best, dict):
        locations.append(best)
    locations.extend(location for location in payload.get("oa_locations") or [] if isinstance(location, dict))
    candidates: list[dict[str, object]] = []
    seen: set[tuple[str | None, str | None]] = set()
    for location in locations:
        pdf_url = str(location.get("url_for_pdf")) if location.get("url_for_pdf") else None
        landing = str(location.get("url_for_landing_page")) if location.get("url_for_landing_page") else None
        key = (pdf_url, landing)
        if key in seen:
            continue
        seen.add(key)
        item = _candidate(
            provider="unpaywall",
            pdf_url=pdf_url,
            landing_url=landing,
            version=str(location.get("version")) if location.get("version") else None,
            license_value=str(location.get("license")) if location.get("license") else None,
            host_type=str(location.get("host_type")) if location.get("host_type") else None,
        )
        if item:
            candidates.append(item)
    return candidates


def _sort_candidates(candidates: list[dict[str, object]]) -> list[dict[str, object]]:
    provider_rank = {"openalex": 0, "unpaywall": 1, "semantic_scholar": 2}
    return sorted(
        candidates,
        key=lambda item: (
            0 if item.get("pdf_url") else 1,
            VERSION_RANK.get(str(item.get("version") or ""), 9),
            0 if item.get("license") else 1,
            provider_rank.get(str(item.get("provider") or ""), 9),
        ),
    )


def _download_pdf(client: httpx.Client, url: str, target: Path, max_bytes: int) -> dict[str, object]:
    tmp = target.with_suffix(".tmp")
    total = 0
    first = b""
    with client.stream("GET", url, follow_redirects=True) as response:
        response.raise_for_status()
        content_type = str(response.headers.get("content-type") or "").lower()
        with tmp.open("wb") as handle:
            for chunk in response.iter_bytes(1024 * 256):
                if not chunk:
                    continue
                if not first:
                    first = chunk[:8]
                total += len(chunk)
                if total > max_bytes:
                    raise ValueError(f"OA PDF exceeds the configured maximum size of {max_bytes} bytes.")
                handle.write(chunk)
    if "pdf" not in content_type and not first.startswith(b"%PDF-"):
        tmp.unlink(missing_ok=True)
        raise ValueError("Resolved OA URL did not return a PDF document.")
    tmp.replace(target)
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    try:
        page_count = len(PdfReader(str(target)).pages)
        parse_status = "ok"
        parse_error = None
    except Exception as exc:
        page_count = None
        parse_status = "metadata_error"
        parse_error = str(exc)
    return {
        "file_hash": digest,
        "page_count": page_count,
        "parse_status": parse_status,
        "parse_error": parse_error,
        "bytes": total,
    }


def acquire_open_access_full_text(
    root: Path,
    *,
    paper_ids: list[str] | None = None,
    max_papers: int = 30,
    download: bool = True,
    timeout: float = 45.0,
    max_pdf_mb: int = 50,
) -> dict[str, object]:
    if not 1 <= max_papers <= 100:
        raise ValueError("max_papers must be between 1 and 100.")
    if not 1 <= max_pdf_mb <= 200:
        raise ValueError("max_pdf_mb must be between 1 and 200.")
    root = _project_root(root)
    state_root = root / PROJECT_DIR
    papers_file = state_root / "data" / "papers.jsonl"
    records = _load_jsonl(papers_file)
    by_id = {str(row.get("paper_id")): row for row in records if row.get("paper_id")}
    selected_ids = _priority_ids(root, records, paper_ids, max_papers)
    cache_root = state_root / "cache" / "fulltext"
    cache_root.mkdir(parents=True, exist_ok=True)

    outcomes: list[dict[str, object]] = []
    provider_failures: list[dict[str, object]] = []
    downloaded = 0
    already_local = 0
    resolved_pdf = 0
    resolved_landing = 0
    unresolved = 0

    with httpx.Client(
        timeout=timeout,
        follow_redirects=True,
        headers={"User-Agent": "LitReviewConstruct/0.1 (lawful OA full-text resolver)"},
    ) as client:
        for paper_id in selected_ids:
            row = by_id[paper_id]
            if _has_local_full_text(row):
                already_local += 1
                outcomes.append({"paper_id": paper_id, "status": "already_local"})
                continue

            candidates: list[dict[str, object]] = []
            for provider, resolver in (
                ("openalex", _openalex_candidates),
                ("semantic_scholar", _s2_candidates),
            ):
                try:
                    found, resolved_id = resolver(client, row)
                    candidates.extend(found)
                    if provider == "openalex" and resolved_id and not row.get("openalex_id"):
                        row["openalex_id"] = resolved_id
                    if provider == "semantic_scholar" and resolved_id and not row.get("s2_paper_id"):
                        row["s2_paper_id"] = resolved_id
                except httpx.HTTPError as exc:
                    provider_failures.append({"paper_id": paper_id, "provider": provider, "error": str(exc)})
            try:
                candidates.extend(_unpaywall_candidates(client, row))
            except httpx.HTTPError as exc:
                provider_failures.append({"paper_id": paper_id, "provider": "unpaywall", "error": str(exc)})

            ordered = _sort_candidates(candidates)
            row["oa_candidates"] = ordered[:12]
            row["oa_resolved_at"] = _now()
            best_pdf = next((item for item in ordered if item.get("pdf_url")), None)
            best_any = ordered[0] if ordered else None

            if best_pdf:
                resolved_pdf += 1
                row["oa_resolution_status"] = "resolved_pdf"
                row["oa_best_location"] = best_pdf
                if download:
                    target = cache_root / f"{paper_id}.pdf"
                    try:
                        meta = _download_pdf(
                            client,
                            str(best_pdf["pdf_url"]),
                            target,
                            max_bytes=max_pdf_mb * 1024 * 1024,
                        )
                        reference = str(target.relative_to(root))
                        row["file_reference"] = reference
                        row["location_type"] = "managed"
                        row["file_instances"] = [{"file_reference": reference, "location_type": "managed"}]
                        row["file_hash"] = meta["file_hash"]
                        row["page_count"] = meta["page_count"]
                        row["parse_status"] = meta["parse_status"]
                        row["parse_error"] = meta["parse_error"]
                        row["full_text_provenance"] = {
                            "access": "open_access",
                            "provider": best_pdf.get("provider"),
                            "pdf_url": best_pdf.get("pdf_url"),
                            "landing_url": best_pdf.get("landing_url"),
                            "version": best_pdf.get("version"),
                            "license": best_pdf.get("license"),
                            "acquired_at": _now(),
                        }
                        downloaded += 1
                        outcomes.append({"paper_id": paper_id, "status": "downloaded", "provider": best_pdf.get("provider"), "file_reference": reference})
                        continue
                    except (httpx.HTTPError, OSError, ValueError) as exc:
                        row["oa_download_error"] = str(exc)
                        outcomes.append({"paper_id": paper_id, "status": "resolved_pdf_download_failed", "provider": best_pdf.get("provider"), "error": str(exc)})
                        continue
                outcomes.append({"paper_id": paper_id, "status": "resolved_pdf", "provider": best_pdf.get("provider"), "pdf_url": best_pdf.get("pdf_url")})
            elif best_any:
                resolved_landing += 1
                row["oa_resolution_status"] = "resolved_landing"
                row["oa_best_location"] = best_any
                outcomes.append({"paper_id": paper_id, "status": "resolved_landing", "provider": best_any.get("provider"), "landing_url": best_any.get("landing_url")})
            else:
                unresolved += 1
                row["oa_resolution_status"] = "unresolved_or_closed"
                outcomes.append({"paper_id": paper_id, "status": "unresolved_or_closed"})
            row["updated_at"] = _now()

    _write_jsonl(papers_file, records)
    report = {
        "schema_version": 1,
        "timestamp": _now(),
        "selected_papers": len(selected_ids),
        "download_requested": download,
        "already_local": already_local,
        "resolved_pdf": resolved_pdf,
        "downloaded": downloaded,
        "resolved_landing": resolved_landing,
        "unresolved_or_closed": unresolved,
        "unpaywall_enabled": bool(os.getenv("UNPAYWALL_EMAIL") or os.getenv("CROSSREF_MAILTO")),
        "provider_failures": provider_failures,
        "outcomes": outcomes,
        "policy_note": "Only provider-reported open/public locations are resolved. The toolkit does not bypass paywalls, logins, CAPTCHAs, or access controls.",
    }
    _write_json(state_root / "data" / "fulltext_resolution.json", report)
    append_activity(
        root,
        category="source_verification",
        actor="toolkit",
        inputs={"action": "oa_fulltext_acquisition", "paper_ids": selected_ids, "download": download},
        outputs=[".litreview/data/fulltext_resolution.json", ".litreview/data/papers.jsonl", ".litreview/cache/fulltext/"],
        source_ids=selected_ids,
        notes=(
            f"Resolved OA availability for {len(selected_ids)} priority papers and downloaded {downloaded} PDFs. "
            "Only open/public locations reported by configured scholarly services were used."
        ),
    )
    return report
