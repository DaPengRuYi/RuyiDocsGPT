# Git 提交规范

> 本规范对本项目有效，**覆盖**全局默认与上游 AGENTS.md / CONTRIBUTING.md 里的英文提交约定。
> 注意：本仓库是开源项目 DocsGPT 的纯二开（基线 arc53/DocsGPT v0.17.2 main 快照），`upstream` 指向原作者仓库且已禁用 push。本规范只约束**我们自己产生的提交**；从 upstream 同步进来的提交保持其原貌，不改写。

## 分支模型（本仓库特有，先记住）
- 只有两个分支：`main`（稳定可交付）和 `dev`（日常开发 + 上游同步）。**不新开 feature/sync 等其它分支。**
- 日常提交都在 `dev`；跑过回归评测（`ruyi/eval/`）后才合并进 `main`。
- 详细同步 SOP 见 `ruyi/docs/UPSTREAM_SYNC.md`。

## 何时提交
- **完成一个功能 / 一个完整的改动单元后，立即提交，无需询问**（用户已长期授权）。
- 一次提交对应一个聚焦的主题，不要把多个不相关的改动堆在一起。
- **提交可以自动做；推送（push）仍需用户确认**（push 属对外动作）。
- **改了上游源码文件**（`application/` `frontend/` 等）必须同步登记到 `ruyi/docs/UPSTREAM_SYNC.md` 第 3 节改动清单，最好和代码同一个提交。

## 提交信息规范（详细中文）
所有提交信息**一律用简体中文**，要让人单看 `git log` 就能看懂每次提交干了什么、为什么这么做。

格式：

```
<类型>: <一句话概括这次改动>

- 具体改动点 1（改了什么文件/行为）
- 具体改动点 2
- 为什么这么改 / 带来的影响（必要时）

Co-Authored-By: <当前模型署名> <noreply@anthropic.com>
```

- **首行**：`<类型>: <概括>`，类型用 `feat`(新功能) / `fix`(修复) / `docs`(文档) / `refactor`(重构) / `chore`(杂项) / `test`(测试) 等；冒号后的概括用中文，一句话说清。
- **正文**：用中文条目列出具体改动和原因，让人能据此还原细节，不要写**优化代码**、**修改若干**这类含糊话。
- 结尾保留 `Co-Authored-By` 署名行（署当前实际干活的模型，如 `Claude Fable 5`）。

### 示例
```
feat: 评测语料换成书稿自指语料（用这本书问这本书）

- ruyi/eval/corpus/ 换成《大鹏 RAG 实战》13 章书稿，文件名转 ASCII
- 新增 ruyi/scripts/ruyi-sync-corpus.ps1 语料同步脚本
- testset.json 重写为 12 题 v2，全部改为问书稿内容
- 实测：命中率 100%，正确率 100%，幻觉率 0%

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
```

## 与上游同步的边界
- **不要把我们的中文提交直接推给 upstream**：若将来要向原作者回馈某个修复，单独整理一份英文 PR，不混用本仓库的中文提交历史。
- `upstream` 已禁用 push（remote 配置里 push URL 为 DISABLED_DO_NOT_PUSH_UPSTREAM），正常只 `fetch`/同步，避免误推。
- 合并上游前后各跑一次回归评测（`ruyi/eval/run_eval.py`），评测通过才进 `main`。
