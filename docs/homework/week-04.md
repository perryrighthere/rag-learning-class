# Week 04 作业

这周主要做两件事：

- 用你自己的已解析文档跑一遍 chunking 对比。
- 把其中一种 chunk 策略真正接进一家供应商的 LLM API，跑通一条 live RAG 问答链。

## 必做

1. 准备一份你自己的 `parsed_documents.jsonl`。
   可以沿用 Week 3 的解析结果，也可以新补一个小样例，但格式要和老师的 Week 3 产物一致。

2. 跑老师的三种策略，先拿到一份 baseline。

```bash
PYTHONPATH=src .venv/bin/python scripts/run_week4_demo.py \
  --input <your_parsed_documents.jsonl> \
  --export-dir submissions/week-04/<your_slug>/baseline
```

3. 选定一个 live path：
   - `siliconflow`
   - `openrouter`
   - 你自己的兼容端点

4. 跑通老师的 live demo：

```bash
SILICONFLOW_API_KEY=your_key PYTHONPATH=src .venv/bin/python scripts/run_week4_live_demo.py \
  --provider siliconflow \
  --model <your_model> \
  --input <your_parsed_documents.jsonl> \
  --question "<your_question>"
```

5. 在下面两项里二选一，只做一项就够：
   - 给 `StructureAwareChunker` 增加一条你自己的领域化规则
   - 给 `live_rag.py` 的 evidence prompt 增加一条你自己的约束规则

6. 把你的改动跑一次 before / after，对比 live answer 或 chunk 变化。

```bash
PYTHONPATH=src .venv/bin/python scripts/run_week4_demo.py \
  --input <your_parsed_documents.jsonl> \
  --export-dir submissions/week-04/<your_slug>/chunks-after \
  --json
```

```bash
SILICONFLOW_API_KEY=your_key PYTHONPATH=src .venv/bin/python scripts/run_week4_live_demo.py \
  --provider siliconflow \
  --model <your_model> \
  --input <your_parsed_documents.jsonl> \
  --question "<your_question>" \
  --json
```

7. 写一段不超过 300 字的说明，回答三件事：
   - 你接的是哪家供应商和哪个模型
   - 你改了哪条 chunking 或 prompt 规则
   - 为什么这件事仍然属于 Week 4，而不是后面的 retrieval 或 evaluation

## 本周不做什么

- 不要改 Week 1-3 的主逻辑。
- 不要接 embedding、BM25、向量库、rerank。
- 不要只交截图，不交可运行结果。
- 不要把作业做成“重写一套新的 RAG 系统”。

## 提交目录与命名

提交目录统一放：

`submissions/week-04/<your_slug>/`

允许改动的触点：

- `src/ntu_rag_week4/`
- `scripts/run_week4_demo.py`
- `scripts/run_week4_live_demo.py`
- `submissions/week-04/<your_slug>/`

不要动的触点：

- `src/ntu_rag_week1/`
- `src/ntu_rag_week2/`
- `src/ntu_rag_week3/`
- `tests/` 里已有老师测试

## 提交物

- 你的 `parsed_documents.jsonl`
- chunk baseline / after 导出结果
- 一次 live RAG 输出
- 代码改动
- `README.md` 或 `notes.md`
- 一段不超过 300 字的说明
