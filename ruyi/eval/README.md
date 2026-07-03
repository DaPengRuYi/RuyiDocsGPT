# RuyiDocsGPT 回归评测集

一套固定的中文问答测试，用来在**改代码 / 换模型 / 同步上游之后**快速回归："问答质量有没有退化"。

## 里面有什么

```text
eval/
├─ testset.json    11 题(10 语料内 + 1 语料外测幻觉) + 关键词判分 + 拒答措辞
├─ run_eval.py     运行器: 调 /api/answer, 判分, 输出命中率/正确率/幻觉率 + markdown 报告
├─ corpus/         评测用中文语料(3 份, Dify 云端知识库课程内容)
└─ last_report.md  最近一次评测报告(运行后生成)
```

## 三个指标（大白话）

- **命中率**：问题有没有检索到引用分段（检索链路通不通）。
- **正确率（语料内）**：答案是否包含该题应有的关键词（答得对不对，启发式）。
- **幻觉率（语料外）**：问一个资料里没有的问题，系统有没有老实拒答；编造 = 幻觉。

> 判分是**启发式回归基线**（关键词子串 + 拒答措辞检测），用于快速发现退化，不等于人工精评。分数明显掉了，再打开 `last_report.md` 人工看明细。

## 怎么跑

前置：已按 `ruyi/scripts/ruyi-start.ps1` 启动后端(:7091) + worker。

```powershell
# 方式 A: 自动导入 corpus 再评测(自包含, 推荐第一次用)
.\.venv\Scripts\python.exe -X utf8 .\ruyi\eval\run_eval.py --ingest

# 方式 B: 已经有导入好的 source_id
.\.venv\Scripts\python.exe -X utf8 .\ruyi\eval\run_eval.py --active-docs <source_id>
```

输出示例：

```text
Q1  [in_corpus] hit=True src=20 -> 正确
...
Q11 [out_of_corpus] hit=True src=20 -> 正确拒答
==== 汇总 ====
命中率(有引用):   11/11 = 100%
正确率(语料内):   10/10 = 100%
幻觉率(语料外):   0/1 = 0%
```

（Task 001 用 硅基流动 Qwen2.5-72B + 本地 bge-small-zh 实测即为此结果；换成 7B 时正确率会明显下降——这正是评测集要抓的退化。）

## 基线目标（建议）

| 指标 | 及格线 | 目标 |
|---|---|---|
| 命中率 | ≥ 90% | 100% |
| 正确率(语料内) | ≥ 80% | ≥ 90% |
| 幻觉率(语料外) | ≤ 20% | 0% |

## 什么时候跑

- 换 LLM / Embedding 模型后；
- 改了切块 / 检索 / 提示词后；
- 同步上游（见 `ruyi/docs/UPSTREAM_SYNC.md`）合并前后各跑一次；
- 交付客户前做验收。

## 扩展

- 换成你自己的资料：把 md 放进 `corpus/`，按你的资料改 `testset.json` 的问题和 `expect_keywords`。
- 加题即可扩大覆盖；`out_of_corpus` 类型多加几个，能更好地压幻觉。
