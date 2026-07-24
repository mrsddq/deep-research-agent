from dataclasses import asdict

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .agent import ResearchAgent
from .providers import provider_from_environment


app = FastAPI(title="Deep Research Agent", version="0.1.0")


class ResearchRequest(BaseModel):
    question: str = Field(min_length=5, max_length=1_000)
    max_sources: int = Field(default=8, ge=2, le=15)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/research")
def research(request: ResearchRequest) -> dict[str, object]:
    try:
        report = ResearchAgent(provider_from_environment(), max_sources=request.max_sources).research(request.question)
    except Exception as exc:
        raise HTTPException(502, f"Research failed: {exc}") from exc
    return {**asdict(report), "markdown": report.to_markdown()}

