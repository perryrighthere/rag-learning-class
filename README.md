# NTU RAG Week 1 Teaching Repo

## Project Structure

- `src/ntu_rag_week1/`: minimal RAG pipeline for teaching Week 1
- `data/week1_corpus/`: small local corpus used by the demo
- `scripts/run_week1_demo.py`: CLI entrypoint
- `tests/`: `unittest` verification
- `docs/teaching-scripts/`: teacher-only teaching notes
- `docs/homework/`: homework only

## Requirements

- Python 3.11+
- Docker Desktop or Docker Engine (optional)

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
```

This Week 1 demo uses only the Python standard library, so no extra package install is required.

## Run Locally

```bash
PYTHONPATH=src .venv/bin/python scripts/run_week1_demo.py \
  --question "RAG 的最小闭环包含哪些环节？"
```

Try another question:

```bash
PYTHONPATH=src .venv/bin/python scripts/run_week1_demo.py \
  --question "为什么不能只看回答像不像样？"
```

## Run with Docker

Build the image:

```bash
docker build -t ntu-rag-week1 .
```

Run the demo:

```bash
docker run --rm ntu-rag-week1
```

Or use Docker Compose:

```bash
QUESTION="为什么 RAG 要基于证据回答？" docker compose run --rm rag-demo
```

## Verification

```bash
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
```
