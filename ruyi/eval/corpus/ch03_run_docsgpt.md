# 第 3 章　跑通 DocsGPT：先把完整 RAG 产品跑起来

> 本章你会亲手做出：一套在你自己机器上能访问的 DocsGPT，外加第一个"带出处"的答案。
> 难度：进阶　｜　对应仓库脚本：`ruyi/scripts/ruyi-setup.ps1`、`ruyi/scripts/ruyi-start.ps1`

## 开篇：我一上来就被 Docker 卡住了

讲个我自己的真实经历。

我准备跑 DocsGPT 那天，信心满满。因为它官方文档写得清清楚楚：装好 Docker，一句 `docker compose up` 就全起来了。我心想这有什么难的。结果打开终端敲下去，第一行就红了：

```text
docker: command not found
```

**我这台机器压根没装 Docker。**

这时候你有两条路。一条是老老实实去装 Docker Desktop，下载、配 WSL、重启，折腾半小时起步；另一条，是搞清楚 DocsGPT 到底依赖什么，绕过 Docker，直接在本机把它原生跑起来。

我选了第二条。为什么？因为**跑通一个东西的过程，本身就是理解它的过程**。Docker 把所有零件打包好了，方便是方便，但你也就失去了看清楚"它到底由哪几个零件组成"的机会。而这本书后面要二开它、部署它，这些零件你迟早得一个个认识。

所以这一章，我带你走两条路都看一遍：官方的 Docker 路我讲清楚思路，本机原生这条路我们一步步真跑通。**不管你有没有 Docker，读完都能把它跑起来。**

## 本章目标

- 无论有没有 Docker，都能把 DocsGPT 在本机跑起来；
- 认识本地原生运行的"四件套"：后端、索引 worker、Redis+Postgres、FAISS；
- 上传第一份资料，问出第一个带引用来源的答案。

## 本章小节

1. 两条路先讲明白：Docker Compose 版 vs 本地原生版
2. 环境盘点：Python、Redis、Postgres 够不够
3. 官方 Docker 路线长什么样
4. 没有 Docker，我为什么敢走原生
5. 本地原生启动后端：uvicorn 起在 7091
6. 启动索引 worker：Celery，Windows 为什么必须 solo 池
7. 给它一个隔离的数据库，绝不碰你别的数据
8. 第一个大坑：中文 Windows 把它整崩了
9. 健康检查：返回 ok 才算真起来
10. 上传第一份资料，问出第一个带出处的答案

## 核心概念（大白话）

正式动手前，先花两分钟认识一下 DocsGPT 跑起来到底要几个"零件"。很多人以为跑一个 AI 应用就是 `python app.py` 一下，其实一套完整的 RAG 产品没那么简单。DocsGPT 本地原生跑起来，至少要同时转四样东西：

- **后端（backend）**：接住你的网页请求、问答请求，是整个系统的门面。它跑在 7091 端口。
- **索引 worker**：你上传一份文档，它不会当场卡着给你处理，而是丢给后台一个"工人"慢慢做——解析、切块、转向量、建索引。这个工人就是 worker。**没有它，你传的文档永远索引不出来。**
- **Redis + Postgres**：Redis 是后端和 worker 之间传话的"中转站"和缓存；Postgres 存用户数据（会话、资料信息这些）。
- **FAISS**：向量库，就是文档转成向量之后存的地方。DocsGPT 默认用它，好处是本地文件、不用额外部署。

你可以把它想象成一家小工厂：后端是前台接单，worker 是车间工人，Redis 是车间和前台之间的传送带，Postgres 是账本，FAISS 是仓库。**四样都转起来，工厂才真正开工。** Docker 的作用，就是把这四样一次性打包启动；我们没 Docker，就自己一样一样把它们点着。

## 实战步骤

好，开始动手。这本书配套的仓库里，我已经把下面这些步骤写成了脚本，你可以直接用；但我建议你第一次跟着**手动走一遍**，看清楚每一步在干嘛，之后再用脚本图省事。

### 第 1 步：盘点环境

先确认三样东西在不在。打开 PowerShell：

```powershell
python --version    # 需要 Python 3.11
```

Redis 和 Postgres 我这台机器本来就装着在跑（很多做开发的机器都有）。你可以这样看它们在不在监听：

```powershell
Get-NetTCPConnection -State Listen -LocalPort 6379,5432 | Select-Object LocalPort
```

能看到 6379（Redis）和 5432（Postgres）就说明两个大件都在。**这是个好消息**——DocsGPT 后端真正依赖的两个重家伙，我本机原生就有，压根不用 Docker 帮我拉。要是你机器上没有，这两个装一下即可，它们都是很成熟的东西，网上教程一大把。

### 第 2 步：建虚拟环境、装依赖

进到项目目录，建一个干净的 Python 虚拟环境，把依赖装进去：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r application\requirements.txt
```

先跟你打个预防针：这个 `requirements.txt` **很重**，里面有 torch、docling、transformers、faiss 这些大块头，加起来好几个 G，首次装十几分钟很正常，网速不好还会更久。泡杯茶等它。

（我把建环境这一整套写进了 `ruyi/scripts/ruyi-setup.ps1`，以后你直接 `powershell -ExecutionPolicy Bypass -File .\ruyi\scripts\ruyi-setup.ps1` 一句话搞定，它还会顺手帮你检查 Redis/Postgres 在不在。）

### 第 3 步：配置——模型和数据库怎么填

依赖装好，接下来告诉它"用什么模型、连哪个数据库"。这些都写在项目根目录的 `.env` 文件里。我准备了一份如意默认模板，复制一份改改就行：

```powershell
Copy-Item .\ruyi\.env.example .\.env
```

打开 `.env`，关键几行是这样（这里我只给你看结构，密钥一律用变量名占位，**真实的 key 绝不能写进任何会提交到 git 的地方**）：

```ini
# 大模型: 硅基流动(国产, OpenAI 兼容端点)
LLM_PROVIDER=openai
LLM_NAME=Qwen/Qwen2.5-72B-Instruct
OPENAI_BASE_URL=https://api.siliconflow.cn/v1
API_KEY=<你的硅基流动_API_KEY>

# 向量: 本地中文模型(512 维, 中文友好)
EMBEDDINGS_NAME=BAAI/bge-small-zh-v1.5

# 数据库: 本机 Postgres 上的隔离库 docsgpt
POSTGRES_URI=postgresql://docsgpt:docsgpt@127.0.0.1:5432/docsgpt

# 向量库用本地 FAISS
VECTOR_STORE=faiss
```

模型为什么这么选、能不能换别的，是第 8 章一整章的内容，这里你先照着填、先跑通。**把 `API_KEY` 换成你自己的硅基流动 key** 就行。

### 第 4 步：给它一个隔离的数据库

这一步特别重要，我要专门讲。DocsGPT 要往 Postgres 里存数据，但**我绝不让它去碰我机器上已有的其它数据库**。正确做法是给它单开一个专用的、隔离的库。用你的 Postgres 管理员账号执行两句（密码你自己填，别写进任何脚本）：

```sql
CREATE ROLE docsgpt LOGIN PASSWORD 'docsgpt' CREATEDB;
CREATE DATABASE docsgpt OWNER docsgpt;
```

这样 DocsGPT 就只在它自己的 `docsgpt` 库里折腾，跟你别的数据井水不犯河水。**在自己机器上跑开源项目，这条隔离的习惯一定要有**，不然哪天它把你别的数据搅乱了，哭都来不及。至于表结构，你不用手动建——后端第一次启动时会自动跑数据库迁移，把该建的表都建好。

### 第 5 步：启动后端和 worker

万事俱备。启动其实就两条命令：一条起后端，一条起 worker。我把它们连同"强制 UTF-8""等健康检查"都封进了 `ruyi/scripts/ruyi-start.ps1`，直接跑它：

```powershell
powershell -ExecutionPolicy Bypass -File .\ruyi\scripts\ruyi-start.ps1
```

顺利的话，你会看到这样一段（这是我真机跑出来的输出）：

```text
== 启动后端 uvicorn :7091 ==
== 启动 worker celery(solo 池) ==
== 等待后端就绪(最多 ~60s, 首次含迁移可能稍久) ==

== 已启动 ==
   后端: http://127.0.0.1:7091/api/health  -> {"status":"ok"}
```

脚本背后其实就是这两条命令，你想手动跑也可以：

```powershell
# 后端(ASGI)
.\.venv\Scripts\python.exe -X utf8 -m uvicorn application.asgi:asgi_app --host 127.0.0.1 --port 7091

# 索引 worker(注意 --pool=solo)
.\.venv\Scripts\python.exe -X utf8 -m celery -A application.app.celery worker --loglevel=INFO --pool=solo --concurrency=1
```

这里有个 Windows 专属的小讲究：worker 那条命令的 `--pool=solo` **不能省**。Celery 默认用的多进程模式在 Windows 上跑不起来，必须换成 solo 池它才肯干活。这个坑不提醒，你能卡半天。

后端第一次启动会自动跑数据库迁移，日志里会刷一长串：

```text
Running upgrade  -> 0001_initial ...
Running upgrade 0001_initial -> 0002_app_metadata ...
...
Running upgrade 0023_wiki_pages -> 0024_wiki_pages_updated_via ...
```

从 0001 一路跑到 0024，全绿，就说明表建好了。

### 第 6 步：健康检查

服务起没起来，别靠感觉，问它一句：

```powershell
Invoke-WebRequest http://127.0.0.1:7091/api/health -UseBasicParsing | Select-Object -Expand Content
```

返回这个，才算真起来了：

```json
{"status":"ok"}
```

### 第 7 步：传第一份资料，问第一个问题

最后见真章。上传一份中文资料建索引，然后问它一个资料里有答案的问题。上传成功后，worker 会在后台把它切块、转向量、建索引，日志里出现 `Task ...ingest[...] succeeded` 就代表索引好了。然后你问一句"RAG 的四个步骤分别是什么"，它会这样回你（我真机的结果）：

```text
RAG（检索增强生成）的四个步骤分别是：
1. 切分：把文档按规则切成一个个分段（chunk）。
2. 索引：用 Embedding 模型把每个分段转成向量，存进向量数据库。
3. 检索：用户提问时，把问题也转成向量，找出语义最相近的几个分段。
4. 生成：把命中的分段拼进提示词，交给大模型生成最终回答。
（来源: doc3_sample.md ...）
```

看到最后那个**来源**没有？这就是我们要的东西——答案不是模型自己编的，是**从你的资料里查出来的，还告诉你出自哪份文档**。到这一步，你机器上这座"知识库工厂"就算真正开工了。

## 关键代码 / 命令 / 配置（速查）

```powershell
# 一键搭环境(venv + 装依赖 + 查 Redis/Postgres)
powershell -ExecutionPolicy Bypass -File .\ruyi\scripts\ruyi-setup.ps1

# 配置(复制模板, 填你自己的 key)
Copy-Item .\ruyi\.env.example .\.env

# 一键启动(后端 + worker, 自动等健康检查)
powershell -ExecutionPolicy Bypass -File .\ruyi\scripts\ruyi-start.ps1

# 健康检查
Invoke-WebRequest http://127.0.0.1:7091/api/health -UseBasicParsing | Select-Object -Expand Content

# 一键停止
powershell -ExecutionPolicy Bypass -File .\ruyi\scripts\ruyi-stop.ps1
```

## 常见坑（都是我真踩过的）

**坑一：没有 Docker，官方那条路直接走不通。**
现象：`docker: command not found`。解决：别急着装 Docker，先看本机有没有 Redis 和 Postgres，有的话直接走本地原生这条路，反而让你把每个零件看得更清楚。

**坑二：中文 Windows 把它整崩了（GBK 编码）。**
现象：后端一启动就报 `UnicodeDecodeError: 'gbk' codec can't decode byte 0x94`，压根起不来。根子在于：它读一个配置文件（`alembic.ini`）时，非要用系统的 GBK 编码去读，而文件里有个 UTF-8 的长破折号（`—`），GBK 读不了，一读就炸；更坑的是你设 UTF-8 环境变量都盖不住它。解决：把那个配置文件里的长破折号 `—` 改成两个普通减号 `--`，纯注释改动、功能不变，就过了。**老 Windows 用户对这类编码坑不会陌生，这本书里它还会换个马甲再出现一次。**

**坑三：脚本里的中文乱码，脚本直接跑不了。**
这就是坑二的"马甲"。我把启动步骤写成 `.ps1` 脚本，第一次跑 `ruyi-stop.ps1` 直接一堆红字报语法错误，脚本里的中文全变成了乱码。原因还是 GBK：Windows PowerShell 5.1 读 `.ps1` 文件时，如果文件是"UTF-8 但没带 BOM 标记"，它就默认按 GBK 读，中文全废，全角标点还会把语法解析搞崩。解决：把 `.ps1` 存成**带 BOM 的 UTF-8**，PowerShell 认了 BOM 就会按 UTF-8 正确读。**记住这个规律：在中文 Windows 上，凡是带中文的配置和脚本，编码不对就会翻车。**

**坑四：中文文件名一上传就丢。**
现象：传一个中文名的文件（比如 `10 使用Dify云端知识库.md`），后端却报"没有文件"，400 错误。原因是中文文件名在上传时被解析成了空。解决：先把文件名改成英文（ASCII），传上去就好了。这也提醒我们，将来二开时上传这块要专门处理中文名。

## 本章小结

这一章我们干了一件事：**在没有 Docker 的情况下，把一整套 DocsGPT 在本机原生跑通了。**

我想让你记住三点。第一，跑通一个项目的过程就是认识它的过程，别怕麻烦走原生，四个零件（后端、worker、Redis+Postgres、FAISS）你现在都见过面了。第二，中文 Windows 环境的编码坑会反复出现，配置和脚本该用 UTF-8 就得用对，`--pool=solo` 这种平台专属的讲究该加就得加。第三，也是最重要的——**别每次都手敲这一堆命令**。我已经把它固化成了 `ruyi/scripts` 里的三个脚本，setup、start、stop，以后一句话的事。能一键跑起来，这本身就是这个项目最值钱的资产之一，尤其是当你以后要把它交给学员和客户的时候。

下一章，我们不动手了，坐下来把这座工厂的图纸摊开，看看 DocsGPT 内部到底是怎么组织的。

## PPT 转化提示

- 一页：两条启动路线对比图（Docker 版 vs 本地原生版）。
- 一页：本地原生"四件套"架构图（后端 + worker + Redis/PG + FAISS），配工厂类比。
- 一页：GBK 报错截图 与 修复对照（左错右对）。
- **演示页**：实机跑 `ruyi-start.ps1` → 健康检查 ok → 上传资料 → 问出带来源的答案。

## 课堂练习

在你自己的机器上，把服务跑起来，然后跑一次健康检查，把返回的 `{"status":"ok"}` 截图发到学习群里，和大家对齐进度。谁卡住了，把报错也发出来，多半是本章那几个坑之一。

## 课后作业

写一份《我的启动实录》：记录你选了哪条路（Docker 还是原生）、中间卡在哪一步、报了什么错、最后怎么解决的。这份实录以后就是你自己的"避坑笔记"。

## 章末交付物

- 一套在你本机能访问的 DocsGPT（`/api/health` 返回 ok）；
- 一张"第一个带来源的答案"的截图。
