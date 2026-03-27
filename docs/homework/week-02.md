# Week 02 作业

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