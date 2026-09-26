import urllib.request
from unittest.mock import Mock

import pytest

from deep_research.agent import ResearchAgent
from deep_research.network import PublicRedirectHandler, validate_public_url
from deep_research.providers import SearchResult


class DiverseProvider:
    def search(self, query, limit=4):
        return [SearchResult(query, f"https://example.com/{query}/{i}", "Solar evidence.")
                for i in range(limit)]


def test_fetch_budget_applies_across_all_queries():
    fetch = Mock(return_value="Solar evidence supports deployment.")
    report = ResearchAgent(DiverseProvider(), fetcher=fetch, max_sources=2).research("Solar deployment?")
    assert fetch.call_count == 2
    assert len(report.sources) == 2


@pytest.mark.parametrize("value", [0, 16, -1, 1.5, True])
def test_invalid_source_budget_rejected(value):
    with pytest.raises(ValueError):
        ResearchAgent(DiverseProvider(), max_sources=value)


def test_failed_pages_are_explicit_search_snippets():
    fetch = Mock(side_effect=OSError("private network detail"))
    report = ResearchAgent(DiverseProvider(), fetcher=fetch, max_sources=2).research("Solar evidence?")
    assert all(source.evidence_type == "search_snippet" for source in report.sources)
    assert len(report.warnings) == 2
    assert "private network detail" not in str(report)


def test_irrelevant_documents_do_not_become_evidence():
    report = ResearchAgent(DiverseProvider(), fetcher=lambda url: "Pasta tastes delicious.").research("Solar deployment?")
    assert report.sources == ()
    assert "No accessible" in report.summary


def test_equal_scores_get_stable_url_order():
    report = ResearchAgent(DiverseProvider(), fetcher=lambda url: "Solar evidence.").research("Solar evidence?")
    assert [source.url for source in report.sources] == sorted(source.url for source in report.sources)


def test_provider_outage_is_visible_and_yields_no_evidence():
    provider = Mock()
    provider.search.side_effect = OSError("secret")
    report = ResearchAgent(provider).research("Solar deployment?")
    assert report.sources == ()
    assert len(report.warnings) == 4
    markdown = report.to_markdown()
    assert all(warning in markdown for warning in report.warnings)
    assert "secret" not in markdown


def test_private_and_redirect_targets_are_blocked(monkeypatch):
    monkeypatch.setattr("deep_research.network.socket.getaddrinfo", lambda *a: [(0, 0, 0, "", ("127.0.0.1", 80))])
    with pytest.raises(ValueError):
        validate_public_url("https://internal.example")
    with pytest.raises(ValueError):
        PublicRedirectHandler().redirect_request(urllib.request.Request("https://example.com"),
            None, 302, "Found", {}, "http://internal.example")
