# 书线版本与发行约定（RuyiDocsGPT ×《大鹏 RAG 实战：如意知识库工厂》)

> 本仓库是这本书的主线项目。读者照书操作时拿到的代码，必须和书写作时的仓库状态**完全一致**。
> 本文档定义怎么做到这一点。决策日期：2026-07-03。

## 1. 发行方式：公开主仓

- 仓库 `github.com/DaPengRuYi/RuyiDocsGPT` **公开开源**（2026-07-03 起），读者直接 clone，无需任何邀请。
- 上游 DocsGPT 为 MIT 协议，本仓库保留其 `LICENSE`；我们的二开层（`ruyi/`、`.claude/`）随仓库同协议开放。
- 仓库 GitHub Actions 已禁用（上游 workflows 在本仓库缺少 secrets，会刷失败记录；如需 CI 另建自己的 workflow 再开）。
- 对完全不会 git 的学员，可从 tag 一键导出 zip 随课分发：
  ```bash
  git archive bk-ch03 -o RuyiDocsGPT-bk-ch03.zip
  ```

## 2. 版本线：每章一个 tag

书的每一章正文定稿时，给当时的 `main` 打一个**附注标签**：

```text
bk-ch03   第 3 章(跑通 DocsGPT)定稿时的仓库状态   ← 已建(2026-07-03)
bk-ch05   第 5 章定稿时的仓库状态
bk-chXX.1 某章 tag 的修订版(仅当该状态发现严重 bug 需给读者修复时)
```

规则：

- **tag 打在 `main` 上**（main = 跑过回归评测的稳定状态），命令：
  ```bash
  git switch main
  git tag -a bk-chXX -m "书线标签: 第 XX 章对应的仓库状态(要点列表)"
  git push origin bk-chXX
  ```
- **tag 一旦推出永不移动、永不删除**——读者的书上印着它。
- 书中每章开头标注"本章基于 `bk-chXX`"；读者操作：
  ```bash
  git clone https://github.com/DaPengRuYi/RuyiDocsGPT.git
  cd RuyiDocsGPT
  git checkout bk-ch03    # 回到与书第 3 章完全一致的状态
  ```

## 3. 分支纪律不变

- 仍然只有 `main` / `dev` 两个长期分支（见 `ruyi/docs/UPSTREAM_SYNC.md`）。
- **不预建 book 分支**。唯一例外：某个已发布 tag 发现严重 bug、且不能让读者吞下 main 的全部新改动时，才从该 tag 拉 `book/v1`，cherry-pick 修复后打 `bk-chXX.1`，事后在本文档登记。

## 4. 上游同步与书线的关系

- 上游同步、新功能开发照常走 `dev` → 评测 → `main`，**对已打的 tag 零影响**——这就是书"不依赖上游"的机制保障。
- 同步上游后若书中命令/行为发生变化，新章节用新 tag；旧章节旧 tag 依旧可跑，不返工。

## 5. 开源内容边界（注意）

- 密钥永远只进 `.env`（已被 gitignore），任何提交不得出现真实密钥；公开前已做过全历史扫描（2026-07-03，无泄露）。
- `ruyi/eval/corpus/` 是书稿的同步副本，**开源即意味着书稿内容随仓库公开**。
- **同步策略已确认（2026-07-03，Afra 拍板）：A 方案，全量同步**——书稿全部章节随仓库开源，书即开源内容当引流，课程/服务收费；`ruyi-sync-corpus.ps1` 可随书稿更新直接跑，无需再逐次确认。唯一保留的限制：**现役钓鱼题原文不写进书稿**（评测自指污染教训，见书 ch11）。
