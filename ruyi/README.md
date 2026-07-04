# ruyi/ — 如意二开层（RuyiDocsGPT）

本目录是 **RuyiDocsGPT（DocsGPT 纯二开）** 的如意专属层。所有如意自己新增的东西尽量放在这里，**与上游 `arc53/DocsGPT` 源码树隔离**，这样：

- 上游更新时改动清晰、易同步（见 `docs/UPSTREAM_SYNC.md`）；
- 教学 / 交付 / 评测资产集中一处，学员和客户一眼看懂。

## 目录

```text
ruyi/
├─ README.md                 本文件
├─ .env.example              如意默认配置模板(硅基流动 LLM + 本地向量; 只写变量名, 无密钥)
├─ scripts/
│  ├─ ruyi-setup.ps1         一键环境搭建(venv + 依赖 + 数据库检查)
│  ├─ ruyi-start.ps1         一键启动(后端 uvicorn + worker celery)
│  ├─ ruyi-stop.ps1          一键停止
│  └─ ruyi-sync-corpus.ps1   评测语料同步(书稿 13 章 → eval/corpus)
├─ docs/
│  ├─ UPSTREAM_SYNC.md       上游同步机制与二开改动清单(基线 arc53/DocsGPT v0.17.2)
│  └─ BOOK_RELEASE.md        书线版本与发行约定(公开主仓 + bk-chXX 章节标签)
└─ eval/
   ├─ README.md              评测集使用说明
   ├─ testset.json           中文回归评测集 v2(11 语料内 + 1 语料外测幻觉)
   ├─ run_eval.py            评测运行器(输出命中率/正确率/幻觉率)
   └─ corpus/                语料 = 《大鹏 RAG 实战：如意知识库工厂》13 章书稿("用这本书问这本书"; 不入库, 仅本地)
```

## 快速上手（Windows PowerShell）

```powershell
# 1. 搭环境(建 venv + 装依赖 + 检查 Redis/Postgres)
powershell -ExecutionPolicy Bypass -File .\ruyi\scripts\ruyi-setup.ps1

# 2. 配置(复制模板, 填入你自己的硅基流动 key)
Copy-Item .\ruyi\.env.example .\.env
#   然后编辑 .env, 把 API_KEY 换成你的硅基流动 key

# 3. 启动(后端 + worker)
powershell -ExecutionPolicy Bypass -File .\ruyi\scripts\ruyi-start.ps1
#   访问 http://127.0.0.1:7091/api/health 应返回 {"status":"ok"}

# 4. 跑评测(需先导入 ruyi/eval/corpus 得到 source_id, 见 eval/README.md)
.\.venv\Scripts\python.exe -X utf8 .\ruyi\eval\run_eval.py --active-docs <source_id>
```

## 边界

- 密钥只进 `.env`（已被 `.gitignore` 排除），本层任何文件不出现真实密钥。
- 本层不改上游核心逻辑；必须改源码的问题（如 bug 修复）单独记录在 `docs/UPSTREAM_SYNC.md`。
