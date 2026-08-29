import json
from pathlib import Path

import pytest

from litreview_construct.discovery import search_openalex
from litreview_construct.intent import accept_intent, set_intent
from litreview_construct.project import init_project


class FakeResponse:
    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, object]:
        return {
            "meta": {"count": 2, "page": 1, "per_page": 25, "cost_usd": 0.0001},
            "results": [
                {
                    "id": "https://openalex.org/W1",
                    "display_name": "Green Finance and Firm Performance",
                    "doi": "https://doi.org/10.1234/GREEN.1",
                    "publication_year": 2024,
                    "language": "en",
                    "cited_by_count": 12,
                    "type": "article",
                    "authorships": [
                        {"author": {"display_name": "Anh Nguyen"}},
                    ],
                    "primary_location": {"source": {"display_name": "Finance Journal"}},
                    "abstract_inverted_index": {
                        "Green": [0],
                        "finance": [1],
                        "matters": [2],
                    },
                },
                {
                    "id": "https://openalex.org/W2",
                    "display_name": "Tai chinh xanh",
                    "doi": "https://doi.org/10.1234/GREEN.2",
                    "publication_year": 2024,
                    "language": "vi",
                    "cited_by_count": 3,
                    "type": "article",
                    "authorships": [],
                    "primary_location": {"source": {"display_name": "Journal B"}},
                    "abstract_inverted_index": None,
                },
            ],
        }


class FakeClient:
    def __init__(self, *args: object, **kwargs: object) -> None:
        self.last_params: dict[str, object] | None = None

    def __enter__(self) -> "FakeClient":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def get(self, url: str, params: dict[str, object]) -> FakeResponse:
        assert url.endswith("/works")
        self.last_params = params
        assert "from_publication_date:2018-01-01" in str(params["filter"])
        assert "to_publication_date:2026-12-31" in str(params["filter"])
        return FakeResponse()


def _accepted_project(tmp_path: Path) -> None:
    init_project(tmp_path)
    set_intent(
        tmp_path,
        topic="Green finance",
        publication_from=2018,
        publication_to=2026,
        languages=["en"],
    )
    accept_intent(tmp_path)


def test_discovery_requires_accepted_intent(tmp_path: Path) -> None:
    init_project(tmp_path)
    with pytest.raises(ValueError):
        search_openalex(tmp_path, "green finance")


def test_openalex_search_applies_scope_and_persists_run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _accepted_project(tmp_path)
    monkeypatch.setattr("litreview_construct.discovery.httpx.Client", FakeClient)
    monkeypatch.delenv("OPENALEX_API_KEY", raising=False)

    result = search_openalex(tmp_path, "green finance")

    assert result["provider_results"] == 2
    assert result["scope_results"] == 1
    assert result["imported"] == 1
    assert result["cost_usd"] == 0.0001
    assert result["api_key_used"] is False

    papers_file = tmp_path / ".litreview" / "data" / "papers.jsonl"
    papers = [json.loads(line) for line in papers_file.read_text(encoding="utf-8").splitlines()]
    assert len(papers) == 1
    assert papers[0]["doi"] == "10.1234/green.1"
    assert papers[0]["abstract"] == "Green finance matters"
    assert papers[0]["status"] == "unresolved"

    run_file = Path(str(result["search_run_file"]))
    run = json.loads(run_file.read_text(encoding="utf-8"))
    assert run["filters"]["languages"] == ["en"]
    assert run["api_key_used"] is False
