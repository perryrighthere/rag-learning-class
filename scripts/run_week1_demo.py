from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ntu_rag_week1.pipeline import build_demo_pipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Week 1 minimal RAG demo.")
    parser.add_argument(
        "--question",
        default="RAG 的最小闭环包含哪些环节？",
        help="Question to ask the demo pipeline.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=3,
        help="How many chunks to retrieve.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print JSON instead of a human-readable report.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    pipeline = build_demo_pipeline()
    result = pipeline.ask(question=args.question, top_k=args.top_k)

    payload = {
        "question": result.question,
        "answer": result.answer,
        "evidence": [
            {
                "title": item.chunk.document_title,
                "path": item.chunk.document_path,
                "score": round(item.score, 4),
                "text": item.chunk.text,
            }
            for item in result.evidence
        ],
    }

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print(f"Question: {payload['question']}")
    print(f"Answer: {payload['answer']}")
    print("Evidence:")
    for index, item in enumerate(payload["evidence"], start=1):
        print(f"  [{index}] {item['title']} (score={item['score']})")
        print(f"      {item['text']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
