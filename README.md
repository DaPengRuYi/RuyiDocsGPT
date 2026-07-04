# 如意知识库工厂 RuyiDocsGPT

**私有知识库 RAG 问答系统**：上传你自己的资料，问出带引用来源的答案。本仓库是开源项目 [DocsGPT](https://github.com/arc53/DocsGPT) 的中文纯二开，也是图书**《大鹏 RAG 实战：如意知识库工厂》**的主线项目——书里教你做的，就是这个仓库里的东西。

> 出品：大鹏 AI 教育 · 张大鹏 ｜ 上游协议 MIT，本仓库同协议开放（见 [LICENSE](LICENSE)）

## 这个项目是什么

- **对使用者**：一套能私有部署的中文知识库问答系统，默认接国产模型（硅基流动 Qwen2.5-72B）+ 本地中文向量（bge-small-zh-v1.5）+ 本地 FAISS，资料不出你的机器。
- **对学习者**：一个"从跑通到二开到交付"的完整 RAG 实战载体，配套图书逐章带你走，每章对应仓库的一个可检出状态（见下方版本线）。
- **对二开研究者**：一个"纯二开不变孤儿分叉"的工程样板——二开资产全部隔离在 `ruyi/`，上游同步机制与改动清单见 [ruyi/docs/UPSTREAM_SYNC.md](ruyi/docs/UPSTREAM_SYNC.md)。

## 快速上手（Windows PowerShell）

```powershell
git clone https://github.com/DaPengRuYi/RuyiDocsGPT.git
cd RuyiDocsGPT

# 1. 一键搭环境(venv + 依赖 + 检查 Redis/Postgres)
powershell -ExecutionPolicy Bypass -File .\ruyi\scripts\ruyi-setup.ps1

# 2. 配置(复制模板, 填入你自己的硅基流动 key)
Copy-Item .\ruyi\.env.example .\.env

# 3. 一键启动(后端 :7091 + 索引 worker)
powershell -ExecutionPolicy Bypass -File .\ruyi\scripts\ruyi-start.ps1
```

`http://127.0.0.1:7091/api/health` 返回 `{"status":"ok"}` 即启动成功。详细说明与常见坑见 [ruyi/README.md](ruyi/README.md)。

## 与书的对照（版本线）

书的每一章正文定稿时，仓库会打一个 `bk-chXX` 标签。**照书操作时先检出对应标签**，保证你手里的代码和书完全一致：

```bash
git checkout bk-ch03   # 回到与书第 3 章一致的状态
```

| 书的阶段 | 章节 | 对应仓库内容 | 标签 |
|---|---|---|---|
| 理解 RAG | ch01–02 | 认知章，不碰代码 | - |
| 跑通系统 | ch03–04 | `ruyi/scripts/` 一键脚本、整体架构 | `bk-ch03` ✅ |
| 打通主链路 | ch05–08 | `application/`（解析/向量/检索/问答/模型接入）、`ruyi/.env.example` | 待发布 |
| 纯二开 | ch09 | `ruyi/` 二开层、`ruyi/docs/UPSTREAM_SYNC.md` | 待发布 |
| 部署交付 | ch10 | 部署脚本与交付文档 | 待发布 |
| 评测运维 | ch11 | `ruyi/eval/` 回归评测集 | 待发布 |
| 做成产品 | ch12 | 全仓库收口 | 待发布 |

版本线与发行约定详见 [ruyi/docs/BOOK_RELEASE.md](ruyi/docs/BOOK_RELEASE.md)。

## 特色：用这本书问这本书

本仓库的回归评测语料就是书稿本身（`ruyi/eval/corpus/`，**书稿内容不随仓库分发**，只在作者本地同步）：把 13 章书稿导入知识库，问"这本书的作者是谁"，它回答"张大鹏"并给出指向章节的引用；问书里没有的"纸质版售价"，它老实拒答。克隆本仓库的读者可以用自己的资料复现同样的玩法（见 `ruyi/eval/README.md`）。

2026-07-04 实测（硅基流动 Qwen2.5-72B + 本地 bge-small-zh-v1.5，31 题 v3 测试集）：

| 指标 | 结果 |
|---|---|
| 命中率（有引用） | 31/31 = 100% |
| 正确率（语料内） | 25/25 = 100% |
| 幻觉率（语料外） | 0/6 = 0% |

跑法见 [ruyi/eval/README.md](ruyi/eval/README.md)。

## 目录结构

```text
application/   上游主流程(Flask/uvicorn 后端、解析、检索、LLM、worker)
frontend/      上游前端(Vite + React)
extensions/    上游扩展(聊天挂件、Discord/Telegram 机器人等)
ruyi/          如意二开层(一键脚本、回归评测、上游同步与发行文档) ← 我们的东西都在这
```

## 分支与上游

- 只有两个分支：`main`（稳定，可交付）和 `dev`（日常开发 + 上游同步）。
- 基线为 arc53/DocsGPT v0.17.2（main 分支 2026-06-24 快照）；`upstream` 仅 fetch，永不向上游 push。
- 上游原版 README 留档在 [ruyi/docs/UPSTREAM_README.md](ruyi/docs/UPSTREAM_README.md)。感谢 [arc53/DocsGPT](https://github.com/arc53/DocsGPT) 团队的优秀工作。
