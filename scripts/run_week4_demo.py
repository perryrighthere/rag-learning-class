from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ntu_rag_week4 import (
    ChunkingRequest,
    SUPPORTED_STRATEGIES,
    build_week4_chunking_report,
    default_week4_input_path,
    export_week4_chunking_artifacts,
    render_week4_report,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the Week 4 chunking comparison demo.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  PYTHONPATH=src .venv/bin/python scripts/run_week4_demo.py
  PYTHONPATH=src .venv/bin/python scripts/run_week4_demo.py --strategy fixed-window --strategy structure-aware
  PYTHONPATH=src .venv/bin/python scripts/run_week4_demo.py --json
  PYTHONPATH=src .venv/bin/python scripts/run_week4_demo.py \\
    --export-dir data/week4_chunking/compliance_ops
""",
    )
    parser.add_argument(
        "--input",
        default=str(default_week4_input_path()),
        help="Path to the Week 3 parsed JSONL file to chunk.",
    )
    parser.add_argument(
        "--strategy",
        action="append",
        choices=SUPPORTED_STRATEGIES,
        default=None,
        help="Chunking strategy to run. Repeat the flag to compare multiple strategies.",
    )
    parser.add_argument(
        "--fixed-chunk-size",
        type=int,
        default=3,
        help="Sentence window size for the fixed-window strategy.",
    )
    parser.add_argument(
        "--fixed-overlap",
        type=int,
        default=1,
        help="Sentence overlap for the fixed-window strategy.",
    )
    parser.add_argument(
        "--structure-max-chars",
        type=int,
        default=220,
        help="Maximum characters per chunk for the structure-aware strategy.",
    )
    parser.add_argument(
        "--structure-min-chars",
        type=int,
        default=80,
        help="Merge the last structure-aware chunk if it is shorter than this threshold.",
    )
    parser.add_argument(
        "--langchain-chunk-size",
        type=int,
        default=90,
        help="Chunk size for the LangChain RecursiveCharacterTextSplitter baseline.",
    )
    parser.add_argument(
        "--langchain-overlap",
        type=int,
        default=20,
        help="Chunk overlap for the LangChain baseline.",
    )
    parser.add_argument(
        "--preview-chunks",
        type=int,
        default=2,
        help="How many chunks to preview per strategy in human-readable mode.",
    )
    parser.add_argument(
        "--export-dir",
        default=None,
        help="Optional directory to save chunk_report.json and per-strategy JSONL outputs.",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_week4_chunking_report(
        ChunkingRequest(
            input_path=Path(args.input),
            strategies=args.strategy,
            fixed_chunk_size=args.fixed_chunk_size,
            fixed_overlap=args.fixed_overlap,
            structure_max_chars=args.structure_max_chars,
            structure_min_chunk_chars=args.structure_min_chars,
            langchain_chunk_size=args.langchain_chunk_size,
            langchain_chunk_overlap=args.langchain_overlap,
            preview_chunks=args.preview_chunks,
        )
    )

    if args.export_dir:
        export_week4_chunking_artifacts(report, Path(args.export_dir))

    if args.json:
        print(json.dumps(asdict(report), ensure_ascii=False, indent=2))
        return 0

    print(render_week4_report(report, preview_chunks=args.preview_chunks))
    if args.export_dir:
        print(f"\nexport_dir: {args.export_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
