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
