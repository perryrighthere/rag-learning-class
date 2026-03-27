# NTU RAG Teaching Repo

## Project Structure

- `src/ntu_rag_week1/`: Week 1 minimal RAG pipeline
- `src/ntu_rag_week2/`: Week 2 domain scoping, corpus audit, boundary demo, and LangChain intro
- `data/week1_corpus/`: small local corpus used by the demo
- `data/week2_scope/`: Week 2 domain candidates, manifest, and local sample sources
- `scripts/run_week1_demo.py`: CLI entrypoint
- `scripts/run_week2_demo.py`: Week 2 CLI entrypoint
- `tests/`: `unittest` verification
- `docs/teaching-scripts/`: teacher-only teaching notes
- `docs/homework/`: homework only

## Requirements

- Python 3.11+
- Docker Desktop or Docker Engine (optional)
- `langchain-core` for the Week 2 LangChain intro

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
.venv/bin/pip install langchain-core
```

Week 1 uses only the Python standard library. Week 2 additionally uses `langchain-core`
to demonstrate simple runnable composition while keeping the actual domain, audit, and
boundary logic in local Python modules.

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
