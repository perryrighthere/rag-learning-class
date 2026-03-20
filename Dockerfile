FROM python:3.11-slim

WORKDIR /app
COPY . /app

ENV PYTHONPATH=/app/src

CMD ["python", "scripts/run_week1_demo.py", "--question", "RAG 的最小闭环包含哪些环节？"]
