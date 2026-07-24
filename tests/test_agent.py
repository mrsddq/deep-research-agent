from deep_research.agent import ResearchAgent
from deep_research.providers import SearchResult


class FakeProvider:
    def search(self, query, limit=5):
        return [
            SearchResult("Solar evidence", "https://example.com/solar", "Solar costs fell."),
            SearchResult("Grid study", "https://example.com/grid", "Storage helps electricity grids."),
        ][:limit]


PAGES = {
    "https://example.com/solar": "Solar panel costs fell sharply over the last decade. Installation accelerated.",
    "https://example.com/grid": "Battery storage helps electricity grids integrate variable solar generation.",
}


def test_report_deduplicates_and_cites_sources():
    agent = ResearchAgent(FakeProvider(), fetcher=PAGES.__getitem__)
    report = agent.research("How have solar costs affected electricity grids?")
    assert len(report.queries) == 4
    assert len(report.sources) == 2
    assert "[1]" in report.summary
    assert "## Sources" in report.to_markdown()


def test_plan_includes_counter_evidence_query():
    queries = ResearchAgent.plan("Does remote work improve productivity?")
    assert any("limitations" in query for query in queries)
    assert any("evidence" in query for query in queries)

