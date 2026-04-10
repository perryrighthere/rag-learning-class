# Week 02 作业

这周的作业有两件事：

- 把你自己的领域范围定下来。
- 在老师给的 Week 2 代码上，做一次很小但真实的 LangChain 入门练习。

先说清边界：这周只允许用 `langchain-core` 的 `runnables`。不要接 Prompt、LLM、Retriever、向量库，也不要提前做 Week 3 的解析工程。

## 要做什么

1. 选一个你准备做到学期末的领域，写一段不超过 200 字的说明。
   这段话要回答两件事：
   - 为什么这个领域适合做“基于证据的回答”
   - 为什么它不是主要靠经验、预测或开放式建议来回答

2. 仿照 `data/week2_scope/compliance_ops/`，给你自己的领域建一个 scope 目录，例如 `data/week2_scope/<your_scope>/`。
   里面至少要有：
   - `domain_brief.json`
   - `corpus_manifest.json`
   - `sources/` 目录
   - `6` 篇本地样例文件
   - 至少 `2` 种格式，推荐 `md`、`html`、`txt`

3. `corpus_manifest.json` 里的每条语料都要写清楚：
   - 标题
   - 来源
   - 日期
   - 格式
   - 为什么要纳入

4. 准备一个问题文件，至少 `12` 题。
   这 `12` 题里要有三类：
   - `in_scope`
   - `out_of_scope`
   - `needs_clarification`

5. 新写一个脚本，名字你自己定，例如：
   - `scripts/run_week2_batch_compare.py`
   - `scripts/run_week2_<your_scope>_compare.py`

   这个脚本要做三件事：
   - 读取你的问题文件
   - 用纯 Python 路径跑一次边界判定
   - 用 LangChain `batch()` 再跑一次同样的判定，并输出每题结果和最后的 mismatch 数量

6. 再做一个小增强，三选一：
   - 给 `manifest.py` 增加至少 `2` 条审计规则
   - 给 `boundary.py` 增加至少 `2` 条边界规则
   - 增加一个导出功能，比如 `--json-out`、`--report-out`、`--summary-only`

7. 在 `verification/` 目录里放至少 `4` 份可复现结果：
   - 一次 `python` 路径输出
   - 一次 `langchain` 路径输出
   - 一次批量问题对比输出
   - 一次你新增功能的输出，或者 before / after 对比

8. 最后写一段不超过 300 字的说明，讲清楚：
   - 你做了什么
   - 你的 LangChain 包装和纯 Python 路径是什么关系
   - 你做的增强为什么还属于 Week 2，而不是后面的内容

## 这周不要做什么

- 不要做 PDF 正式解析。
- 不要接 `MinerU`、`trafilatura`、`BeautifulSoup`。
- 不要接向量库、Retriever、LLM API。
- 不要用 Prompt、ChatModel、TextSplitter、VectorStore。
- 不要只交截图、表格或 Notebook。
- 不要只改老师样例里的文案，假装是你自己的领域。

## 提交目录

建议你把作业放在：

`submissions/week-02/<your_slug>/`

这个目录下至少有：

- `README.md`
- `scope/`
- `questions/`
- `verification/`

`README.md` 里至少写 3 条老师可以直接运行的命令：

- 一条 `python` 路径命令
- 一条 `langchain` 路径命令
- 一条批量对比命令

## 提交物

- 领域说明
- 你的 scope 目录
- 问题文件
- 对比脚本
- 你做的一个小增强
- 验证输出
- 一张截图或一段不超过 2 分钟的录屏
- 300 字以内说明

## 老师怎么验收

- 先看你的领域是不是说得清楚。
- 再看你的 scope 文件是不是完整，字段是不是齐。
- 然后运行你 README 里的 3 条命令。
- 重点看两件事：
  - 同一批问题，`python` 和 `langchain` 两条路径是不是基本一致
  - 你做的那个小增强是不是确实有用，不只是改了输出文案

理想情况下，mismatch 应该是 `0`。如果不是 `0`，你要在说明里解释原因。

## 自查

- 别人拿到你的 scope 目录，能不能直接看懂你这个项目问什么、不问什么？
- 你的 LangChain 包装，是不是复用了现有业务逻辑，而不是偷偷重写了一套？
- 你的问题文件里，有没有故意放一些需要澄清的灰区题？
- 你做的增强，是不是真的在增强“边界治理 / 语料审计 / 可复现性”？
- 你的作业有没有提前跑到 Week 3 以后？

## 选做

- 在批量对比结果里顺手输出一下 `python` 和 `langchain` 的耗时。
- 再挑 `2` 个候选领域，简单写一下为什么它们更难做。
