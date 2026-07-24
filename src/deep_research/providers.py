from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Protocol


USER_AGENT = "DeepResearchAgent/0.1 (https://github.com/mrsddq/deep-research-agent)"


@dataclass(frozen=True)
class SearchResult:
    title: str
    url: str
    snippet: str


class SearchProvider(Protocol):
    def search(self, query: str, limit: int = 5) -> list[SearchResult]: ...


def _get_json(url: str, headers: dict[str, str] | None = None, data: bytes | None = None) -> dict:
    request = urllib.request.Request(url, data=data, headers={"User-Agent": USER_AGENT, **(headers or {})})
    with urllib.request.urlopen(request, timeout=15) as response:
        if response.headers.get_content_type() != "application/json":
            raise ValueError("Search provider returned a non-JSON response")
        return json.loads(response.read(2 * 1024 * 1024))


class WikipediaProvider:
    """Zero-configuration search provider backed by the public Wikipedia API."""

    endpoint = "https://en.wikipedia.org/w/api.php"

    def search(self, query: str, limit: int = 5) -> list[SearchResult]:
        params = urllib.parse.urlencode({
            "action": "query", "list": "search", "srsearch": query,
            "srlimit": limit, "format": "json", "utf8": 1,
        })
        payload = _get_json(f"{self.endpoint}?{params}")
        results = []
        for item in payload.get("query", {}).get("search", []):
            title = item["title"]
            results.append(SearchResult(
                title=title,
                url=f"https://en.wikipedia.org/wiki/{urllib.parse.quote(title.replace(' ', '_'))}",
                snippet=_strip_tags(item.get("snippet", "")),
            ))
        return results


class TavilyProvider:
    endpoint = "https://api.tavily.com/search"

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.getenv("TAVILY_API_KEY")
        if not self.api_key:
            raise ValueError("TAVILY_API_KEY is required for Tavily search")

    def search(self, query: str, limit: int = 5) -> list[SearchResult]:
        body = json.dumps({
            "api_key": self.api_key,
            "query": query,
            "max_results": limit,
            "search_depth": "advanced",
            "include_answer": False,
        }).encode()
        payload = _get_json(
            self.endpoint,
            headers={"Content-Type": "application/json"},
            data=body,
        )
        return [
            SearchResult(item.get("title", "Untitled"), item["url"], item.get("content", ""))
            for item in payload.get("results", [])
            if item.get("url")
        ]


def provider_from_environment() -> SearchProvider:
    return TavilyProvider() if os.getenv("TAVILY_API_KEY") else WikipediaProvider()


def _strip_tags(value: str) -> str:
    import re

    return re.sub(r"<[^>]+>", "", value).replace("&quot;", '"').replace("&#039;", "'")

