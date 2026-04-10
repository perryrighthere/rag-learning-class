from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ntu_rag_week4 import (
    SUPPORTED_STRATEGIES,
    Week4LiveRAGPipeline,
    build_provider_config,
    default_week4_input_path,
    live_answer_to_payload,
    render_live_answer,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the Week 4 live RAG demo with a real LLM provider.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  SILICONFLOW_API_KEY=... PYTHONPATH=src .venv/bin/python scripts/run_week4_live_demo.py \\
    --provider siliconflow \\
    --model Qwen/Qwen3-32B

  OPENROUTER_API_KEY=... PYTHONPATH=src .venv/bin/python scripts/run_week4_live_demo.py \\
    --provider openrouter \\
    --model openai/gpt-4o-mini \\
    --question "临时访问权限开通后多久要完成第一次复核？"
""",
    )
    parser.add_argument(
        "--provider",
        choices=("siliconflow", "openrouter", "custom"),
        required=True,
        help="Which OpenAI-compatible provider to call.",
    )
    parser.add_argument(
        "--model",
        required=True,
        help="Provider model id, for example Qwen/Qwen3-32B or openai/gpt-4o-mini.",
    )
    parser.add_argument(
        "--question",
        default="临时访问权限开通后多久要完成第一次复核？",
        help="Question to ask against the Week 4 live RAG pipeline.",
    )
    parser.add_argument(
        "--input",
        default=str(default_week4_input_path()),
        help="Parsed JSONL source for chunking and retrieval.",
    )
    parser.add_argument(
        "--chunk-strategy",
        choices=SUPPORTED_STRATEGIES,
        default="structure-aware",
        help="Chunk strategy to index before retrieval.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=3,
        help="How many chunks to send to the model.",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.2,
        help="Sampling temperature for the provider call.",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=600,
        help="Max output tokens for the provider call.",
    )
    parser.add_argument(
        "--base-url",
        default=None,
        help="Optional custom OpenAI-compatible base URL. Required when provider=custom.",
    )
    parser.add_argument(
        "--api-key-env",
        default=None,
        help="Optional env var name to read the API key from.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=60,
        help="HTTP timeout for the provider request.",
    )
    parser.add_argument(
        "--referer",
        default=None,
        help="Optional HTTP-Referer for providers such as OpenRouter.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print JSON output.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    provider_config = build_provider_config(
        provider=args.provider,
        model=args.model,
        base_url=args.base_url,
        api_key_env=args.api_key_env,
        timeout_seconds=args.timeout_seconds,
        referer=args.referer,
    )
    pipeline = Week4LiveRAGPipeline(
        provider_config=provider_config,
        chunk_strategy=args.chunk_strategy,
        input_path=Path(args.input),
    )
    result = pipeline.ask(
        question=args.question,
        top_k=args.top_k,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
    )

    if args.json:
        print(json.dumps(live_answer_to_payload(result), ensure_ascii=False, indent=2))
        return 0

    print(render_live_answer(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
