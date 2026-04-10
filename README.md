# NTU RAG Teaching Repo

## Project Structure

- `src/ntu_rag_week1/`: Week 1 minimal RAG pipeline
- `src/ntu_rag_week2/`: Week 2 domain scoping, corpus audit, boundary demo, and LangChain intro
- `src/ntu_rag_week3/`: Week 3 standalone PDF parser service
- `src/ntu_rag_week4/`: Week 4 chunking comparison and LangChain TextSplitter baseline
- `data/week1_corpus/`: small local corpus used by the demo
- `data/week2_scope/`: Week 2 domain candidates, manifest, and local sample sources
- `data/week3_parsing/`: sample PDFs for Week 3 manual checks
- `data/week4_chunking/`: Week 4 exported chunk comparison artifacts
- `scripts/run_week1_demo.py`: CLI entrypoint
- `scripts/run_week2_demo.py`: Week 2 CLI entrypoint
- `scripts/run_week3_demo.py`: Week 3 CLI entrypoint
- `scripts/run_week4_demo.py`: Week 4 CLI entrypoint
- `scripts/run_week4_live_demo.py`: Week 4 live LLM-backed RAG entrypoint
- `tests/`: `unittest` verification
- `docs/teaching-scripts/`: teacher-only teaching notes
- `docs/homework/`: homework only

## Requirements

- Python 3.11+
- `uv` or another virtualenv workflow
- Docker Desktop or Docker Engine (optional)
- `langchain-core` for the Week 2 LangChain intro
- `pypdf` for the Week 3 local PDF fallback path
- `langchain-text-splitters` for the Week 4 LangChain chunking baseline
- a provider API key for the Week 4 live LLM path, such as `SILICONFLOW_API_KEY` or `OPENROUTER_API_KEY`
- Optional: a deployed MinerU API service for the Week 3 primary path

## Setup

```bash
uv venv .venv
source .venv/bin/activate
uv pip install --python .venv/bin/python -r requirements.txt
```

Week 1 uses only the Python standard library. Week 2 adds `langchain-core` to
demonstrate simple runnable composition. Week 3 is intentionally small: it only ships a
standalone `pdf_parser` service. If `MinerU API` is available, the service returns raw
MinerU JSON. If not, it falls back to `pypdf` or `pymupdf`. The cleanup/extraction step is
left for students. Week 4 consumes the Week 3 parsed JSONL export and compares three
chunking routes: fixed window, structure aware, and a `LangChain` recursive text splitter
baseline. Week 4 also adds a practical bridge path: simple chunk retrieval plus a real
OpenAI-compatible provider call through SiliconFlow, OpenRouter, or a custom endpoint.

## Run Locally

Week 1 demo:

```bash
PYTHONPATH=src .venv/bin/python scripts/run_week1_demo.py \
  --question "RAG 的最小闭环包含哪些环节？"
```

Week 2 demo:

```bash
PYTHONPATH=src .venv/bin/python scripts/run_week2_demo.py
```

Week 2 orchestration comparison:

```bash
PYTHONPATH=src .venv/bin/python scripts/run_week2_demo.py --engine python --json
PYTHONPATH=src .venv/bin/python scripts/run_week2_demo.py --engine langchain --json
```

Week 2 demo examples:

Default compliance scope:

```bash
PYTHONPATH=src .venv/bin/python scripts/run_week2_demo.py
```

Test multiple boundary questions:

```bash
PYTHONPATH=src .venv/bin/python scripts/run_week2_demo.py \
  --question "涉及个人信息的临时访问申请需要谁审批？" \
  --question "怎样设计一套最受欢迎的数据商业化产品？"
```

Run the higher-complexity EU AI Act scope:

```bash
PYTHONPATH=src .venv/bin/python scripts/run_week2_demo.py --scope eu_ai_governance
```

Run the higher-complexity cybersecurity incident scope:

```bash
PYTHONPATH=src .venv/bin/python scripts/run_week2_demo.py --scope cyber_incident_ops
```

Ask targeted questions against the EU AI Act scope:

```bash
PYTHONPATH=src .venv/bin/python scripts/run_week2_demo.py --scope eu_ai_governance \
  --question "高风险 AI 系统提供者需要建立什么样的质量管理体系？" \
  --question "这家 AI 公司未来三年一定会不会因为 AI Act 被重罚？"
```

Ask targeted questions against the cybersecurity incident scope:

```bash
PYTHONPATH=src .venv/bin/python scripts/run_week2_demo.py --scope cyber_incident_ops \
  --question "日志管理指南建议保留哪些类型的安全日志以支持事件分析？" \
  --question "我们现在最应该买哪一家的 EDR 产品？"
```

Print JSON:

```bash
PYTHONPATH=src .venv/bin/python scripts/run_week2_demo.py --scope eu_ai_governance --json
```

Save JSON to a file:

```bash
PYTHONPATH=src .venv/bin/python scripts/run_week2_demo.py --scope cyber_incident_ops --json \
  > /tmp/week2-cyber-incident-report.json
```

Week 3 with MinerU API:

```bash
PYTHONPATH=src .venv/bin/python scripts/run_week3_demo.py \
  --pdf /path/to/file.pdf \
  --mineru-api-url http://127.0.0.1:18000 \
  --json
```

Week 3 with local fallback:

```bash
PYTHONPATH=src .venv/bin/python scripts/run_week3_demo.py \
  --pdf /path/to/file.pdf \
  --parser pypdf \
  --json
```

Week 4 chunking comparison:

```bash
PYTHONPATH=src .venv/bin/python scripts/run_week4_demo.py
```

Week 4 export artifacts:

```bash
PYTHONPATH=src .venv/bin/python scripts/run_week4_demo.py \
  --export-dir data/week4_chunking/compliance_ops \
  --json
```

Week 4 live RAG with SiliconFlow:

```bash
SILICONFLOW_API_KEY=your_key PYTHONPATH=src .venv/bin/python scripts/run_week4_live_demo.py \
  --provider siliconflow \
  --model Qwen/Qwen3-32B \
  --question "临时访问权限开通后多久要完成第一次复核？"
```

Week 4 live RAG with OpenRouter:

```bash
OPENROUTER_API_KEY=your_key PYTHONPATH=src .venv/bin/python scripts/run_week4_live_demo.py \
  --provider openrouter \
  --model openai/gpt-4o-mini \
  --question "DSAR 工单进入队列后第一步要做什么？"
```

## Run with Docker

Build the image:

```bash
docker build -t ntu-rag-teaching .
```

Run the default demo:

```bash
docker run --rm ntu-rag-teaching
```

Or use Docker Compose:

```bash
QUESTION="为什么 RAG 要基于证据回答？" docker compose run --rm rag-demo
```

## Verification

```bash
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
```
