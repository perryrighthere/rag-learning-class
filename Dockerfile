FROM python:3.11-slim

WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH=/app/src

CMD ["python", "scripts/run_week1_demo.py", "--question", "RAG 的最小闭环包含哪些环节？"]
