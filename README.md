# Deep Research Agent

A multi-query web research pipeline that searches, deduplicates, reads sources concurrently, ranks relevant evidence, and writes a citation-linked Markdown report.

## How it works

1. Expands a question into general, evidence, limitation, and recent-development queries.
2. Searches Wikipedia by default, or diverse web sources through Tavily when `TAVILY_API_KEY` is set.
3. Deduplicates URLs and fetches source pages concurrently.
4. Selects relevant evidence and produces numbered inline citations.
5. Exports a readable report and structured API response.

## Run

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

deep-research "How is battery storage changing electricity grids?" -o report.md
uvicorn deep_research.api:app --reload
```

For broader web coverage:

```bash
export TAVILY_API_KEY=your_key
deep-research "How is battery storage changing electricity grids?"
```

API request:

```bash
curl -X POST http://localhost:8000/v1/research \
  -H "Content-Type: application/json" \
  -d '{"question":"What evidence supports four-day work weeks?","max_sources":8}'
```

## Important limitation

The default synthesis is extractive and intentionally auditable; it is a research baseline, not an oracle. Verify material claims against the linked sources. Production deployments should add source-quality scoring, date awareness, a robust outbound URL policy, and a grounded LLM synthesis stage.

```bash
pytest
ruff check .
docker build -t deep-research .
```

MIT licensed.

## Reliability contract

`max_sources` caps fetched pages across all queries (1–15 for the library, 2–15 for the API).
Candidates are selected round-robin across the four planned queries. Equal relevance scores
use URL ordering, so concurrent completion does not change citation IDs. Irrelevant pages with
zero lexical overlap are omitted. Failed page fetches can use provider snippets, but every source
labels `evidence_type` as `page` or `search_snippet`; `warnings` expose search/fetch failures
without exception internals. A snippet is not a verified reading of the page.

Source fetches validate public HTTP(S) destinations before the request and every redirect,
ignore ambient proxies, and enforce a 2 MB response budget. DNS rebinding still requires network
egress controls. The tests use fake providers and pages: no API key, paid call, model download,
or live-web accuracy claim. The pipeline is extractive; it does not train or invoke an LLM.
