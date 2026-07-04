# 上游同步机制（RuyiDocsGPT ← arc53/DocsGPT）

> 目的：让 RuyiDocsGPT 纯二开**不变成孤儿分叉**。上游有安全补丁/新功能时，能可控地同步进来。
> 纪律：只 `fetch` 上游，**永不向上游 push**（已在 git 配置里禁用）。

## 0. 分支模型（重要）

本仓库**只有两个分支**：

```text
main   稳定分支(可交付/演示的版本)
dev    集成/日常工作分支(开发、上游同步都在这里做)
```

**不要新开 feature/sync/* 等其它分支。** 所有开发和上游同步都在 `dev` 上进行，评测通过后再合并到 `main`。

## 1. 远程配置（已就绪）

```text
origin    git@github.com:DaPengRuYi/RuyiDocsGPT.git   (我们的私有仓库, 可 push)
upstream  git@github.com:arc53/DocsGPT.git            (上游, 仅 fetch; push 已禁用)
```

验证：
```bash
git remote -v
# upstream 的 push 应显示 DISABLED_DO_NOT_PUSH_UPSTREAM
```

## 2. 基线说明（重要）

- 本仓库初始化时的源码，是上游 **`main` 分支的一个快照（约 2026-06-24）**，`application/version.py` 自报 `0.17.2`。
- 注意：它**不是** tag `0.17.2`（`836c26a`）那个较早的发布——相对该 tag 差异达 620 文件。**真正的基线是 main 分支**，不要拿 tag 0.17.2 做对比。
- 截至写这份文档时，`upstream/main` 已到 `46b7bb7`（2026-06-30），相对我们 HEAD 有约 **47 个文件**的差异，其中：
  - **上游领先的更新**（约 45 个）：docs 增删、`worker.py`、`embedding_pipeline.py`、`version.py`、`api/internal/routes.py` 等——这些是可同步进来的上游改动。
  - **我们自己的二开改动**（见下节）：目前只有 2 个源码文件 + 删 1 个大文件 + 新增 `ruyi/` 层。
- **2026-07-04 同步核查**：`upstream/main` 仍停在 `46b7bb7`，仅新增 `0.17.3`/`0.18.0` 两个 tag。重点核查的 remote embedding 两修复（`df5582db` remote embeds、`1acb8363` 维度截断护栏 + remote_worker 切块丢弃 bug）**均已包含在我们的基线快照中**（快照晚于两提交合并，`_remote_instance`/`EMBEDDINGS_MAX_INPUT_TOKENS` 在代码中均可验证）。基线之后的上游增量只有 0.18 文档革新、版本号 chore、Docker 下 Vite HMR 开发态修复——无安全补丁、无运行时修复，**本轮无需同步**。

## 3. 当前二开改动清单（相对上游）

保持这份清单最新，是可控二开的关键。每次改上游文件都登记一行。

| 文件 | 类型 | 改动 | 原因 | 可回滚 |
|---|---|---|---|---|
| `application/alembic.ini` | 改源码 | 两处 UTF-8 em dash(`—`) 改 ASCII `--` | 中文(GBK) Windows 下 alembic 读配置崩溃 | 是 |
| `.gitignore` | 配置 | 追加排除 `tests/e2e/fixtures/docs/oversize.pdf` | 上游自带 55MB 测试大文件, 二开不需要 | 是 |
| `tests/e2e/fixtures/docs/oversize.pdf` | 删除 | 从仓库移除(55MB) | 同上 | 是(可从上游取回) |
| `ruyi/` | 新增 | 如意二开层(脚本/评测/文档/配置模板) | 教学与交付资产, 与上游隔离 | 是(独立目录) |
| `README.md` | 改源码 | 整体替换为中文门面(书对照表/快速上手/评测跑分), 原版留档 `ruyi/docs/UPSTREAM_README.md` | 仓库已公开, 是书的读者入口 | 是(留档可还原) |
| `frontend/index.html` | 改源码 | `<title>` 改「如意知识库工厂 RuyiDocsGPT」, `lang` 改 zh-CN | 品牌化/中文化 | 是 |
| `frontend/src/Hero.tsx` | 改源码 | 首页主标题 DocsGPT → 如意知识库工厂(logo 图暂保留) | 品牌化 | 是 |
| `frontend/src/locale/i18n.ts` | 改源码 | `fallbackLng` en→zh, 加 `load:'languageOnly'`(zh-CN 浏览器命中 zh 包) | 默认中文 | 是 |
| `frontend/src/locale/zh.json` | 改源码 | 中文语言包内品牌名 DocsGPT → 如意知识库工厂(14 处) | 品牌化 | 是 |
| `.github/dependabot.yml` | 删除 | 停用 dependabot 自动依赖 PR | 机器人 PR 从旧历史切分支, 妨碍书稿历史清除; 且本仓库 Actions 已禁用, 依赖升级随上游同步走 | 是(可从上游取回) |

> 原则：**能走配置就不改源码**。默认模型、品牌、中文文案优先进 `.env` / `ruyi/`，不散改核心逻辑。必须改源码的（如上面 alembic.ini 这类 bug 适配）单独登记在本表。

## 4. 同步 SOP（推荐流程）

```bash
# 1. 取最新上游(只 fetch, 不动工作区)
git fetch upstream

# 2. 看上游有哪些新提交
git log --oneline HEAD..upstream/main | head -50

# 3. 切到 dev(同步/开发都在 dev 上做, 不新开分支; main 保持稳定)
git switch dev

# 4a. 只要某个安全补丁 / 具体修复 → cherry-pick(推荐, 影响面小)
git cherry-pick <upstream_commit_sha>

# 4b. 或者要整体跟进上游 → 合并(冲突多时逐文件解, 保住第3节清单里的二开改动)
git merge upstream/main

# 5. 关键: 跑回归评测, 确认没跑坏(见 ruyi/eval/README.md)
#    先启动服务, 导入 ruyi/eval/corpus, 再:
#    .venv\Scripts\python.exe -X utf8 ruyi\eval\run_eval.py --active-docs <source_id>

# 6. 评测通过 → 合到 main → 推送两个分支
git switch main && git merge --no-ff dev
git push origin main dev
```

## 5. 冲突处理要点

- 冲突集中在第 3 节清单里的文件时，**保住我们的二开改动**（比如 alembic.ini 的 ASCII 破折号别被上游覆盖回 em dash）。
- `ruyi/` 是独立目录，几乎不会和上游冲突——这就是把二开资产隔离出来的价值。
- 拿不准的上游改动，先在 `dev` 上验证 + 跑评测，别直接进 `main`。

## 6. 什么时候值得同步

- **安全补丁 / 明确 bug 修复**：优先 cherry-pick，尽快跟进。
- **大版本功能跃迁**：先评估对我们二开（中文化/默认模型/部署）的影响，评测通过再进。
- **纯 docs / CI 改动**：可选，按需。

## 7. 一次性可选：把历史锚定到上游（进阶）

本仓库是全新 `git init` 的单条提交，和上游历史不连。若将来想要**真正干净的 merge 能力**，可以做一次性重锚（在上游对应的 main 基线提交上重放我们的二开改动），但那是历史重写 + 强推，需单独评估、单独授权后再做。当前用第 4 节的 cherry-pick / merge 流程已足够应付日常同步。
