from __future__ import annotations

import html
import re
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Callable

from .providers import SearchProvider, SearchResult


WORD_RE = re.compile(r"[A-Za-z][A-Za-z'-]+")
STOP_WORDS = {
    "about", "after", "also", "and", "are", "been", "being", "but", "can", "for", "from",
    "had", "has", "have", "into", "its", "more", "not", "of", "on", "that", "the", "their",
    "there", "these", "they", "this", "to", "was", "were", "which", "who", "will", "with",
}


@dataclass(frozen=True)
class Source:
    id: int
    title: str
    url: str
    excerpt: str


@dataclass(frozen=True)
class ResearchReport:
    question: str
    summary: str
    findings: tuple[str, ...]
    sources: tuple[Source, ...]
    queries: tuple[str, ...]

    def to_markdown(self) -> str:
        findings = "\n".join(f"- {finding}" for finding in self.findings)
        sources = "\n".join(f"{source.id}. [{source.title}]({source.url})" for source in self.sources)
        return (
            f"# Research report\n\n**Question:** {self.question}\n\n"
            f"## Executive summary\n\n{self.summary}\n\n"
            f"## Key findings\n\n{findings}\n\n## Sources\n\n{sources}\n"
        )


class TextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.ignored = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "nav", "footer", "svg", "noscript"}:
            self.ignored += 1
        elif tag in {"p", "li", "h1", "h2", "h3"} and not self.ignored:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "nav", "footer", "svg", "noscript"} and self.ignored:
            self.ignored -= 1

    def handle_data(self, data: str) -> None:
        if not self.ignored:
            self.parts.append(data)


def fetch_text(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "DeepResearchAgent/0.1"})
    with urllib.request.urlopen(request, timeout=12) as response:
        if response.headers.get_content_type() not in {"text/html", "text/plain"}:
            return ""
        raw = response.read(2 * 1024 * 1024)
        charset = response.headers.get_content_charset() or "utf-8"
    parser = TextParser()
    parser.feed(raw.decode(charset, errors="replace"))
    return " ".join(html.unescape("".join(parser.parts)).split())


def _tokens(text: str) -> list[str]:
    return [word.lower() for word in WORD_RE.findall(text) if word.lower() not in STOP_WORDS]


class ResearchAgent:
    def __init__(
        self,
        provider: SearchProvider,
        fetcher: Callable[[str], str] = fetch_text,
        max_sources: int = 8,
    ) -> None:
        self.provider = provider
        self.fetcher = fetcher
        self.max_sources = max_sources

    @staticmethod
    def plan(question: str) -> list[str]:
        clean = " ".join(question.split()).rstrip("?")
        return [
            clean,
            f"{clean} evidence data",
            f"{clean} limitations criticism",
            f"{clean} recent developments",
        ]

    def research(self, question: str) -> ResearchReport:
        if len(question.strip()) < 5:
            raise ValueError("Research question is too short")
        queries = self.plan(question)
        candidates: dict[str, SearchResult] = {}
        for query in queries:
            for result in self.provider.search(query, limit=4):
                candidates.setdefault(result.url, result)
                if len(candidates) >= self.max_sources:
                    break

        documents: list[tuple[SearchResult, str]] = []
        with ThreadPoolExecutor(max_workers=min(6, len(candidates) or 1)) as executor:
            future_map = {executor.submit(self.fetcher, item.url): item for item in candidates.values()}
            for future in as_completed(future_map):
                item = future_map[future]
                try:
                    text = future.result()
                except Exception:
                    text = ""
                documents.append((item, text or item.snippet))

        terms = Counter(_tokens(question))
        ranked: list[tuple[float, SearchResult, str]] = []
        for result, text in documents:
            sentences = re.split(r"(?<=[.!?])\s+", text)
            best = max(sentences, key=lambda sentence: self._relevance(sentence, terms), default=result.snippet)
            score = self._relevance(best, terms)
            if best.strip():
                ranked.append((score, result, best.strip()[:500]))
        ranked.sort(key=lambda item: item[0], reverse=True)

        sources = tuple(
            Source(index, result.title, result.url, excerpt)
            for index, (_, result, excerpt) in enumerate(ranked[:self.max_sources], 1)
        )
        findings = tuple(f"{source.excerpt} [{source.id}]" for source in sources[:6])
        summary = " ".join(findings[:3]) or "No accessible sources produced relevant evidence."
        return ResearchReport(question, summary, findings, sources, tuple(queries))

    @staticmethod
    def _relevance(text: str, terms: Counter[str]) -> float:
        words = Counter(_tokens(text))
        return sum(min(words[term], 3) * weight for term, weight in terms.items()) / max(len(words) ** 0.5, 1)

