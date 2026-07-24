import argparse
from pathlib import Path

from .agent import ResearchAgent
from .providers import provider_from_environment


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a cited research report")
    parser.add_argument("question")
    parser.add_argument("--max-sources", type=int, default=8)
    parser.add_argument("--output", "-o", type=Path, default=Path("report.md"))
    args = parser.parse_args()
    report = ResearchAgent(provider_from_environment(), max_sources=args.max_sources).research(args.question)
    args.output.write_text(report.to_markdown(), encoding="utf-8")
    print(f"Wrote {len(report.sources)} sources to {args.output}")


if __name__ == "__main__":
    main()

