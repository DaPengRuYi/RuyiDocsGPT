# 第十章 · 使用 Dify 云端知识库（真实 API 测试）

对应课程文档第十章。这里用 Dify 知识库 **Service API** 真实走通完整闭环：

> 建库 → 上传文档 → 等待索引 → 召回测试 → （可选）清理

✅ **本目录已于 2026-07-02 用真实的 Dify 云端工作区（SANDBOX 免费版）完整验证通过**，
运行结果见文末「真实运行记录」。

## 文件说明

- `dify_kb_client.py` — 知识库 API 极简客户端（建库/传文档/查索引状态/召回/删库）
- `test_cloud_kb.py` — 端到端冒烟测试脚本，跑通即证明云端知识库可用
- `demo_rag_vs_no_rag.py` — **对比实验**：同一私有问题，接不接知识库各问一遍，直观体现知识库的作用
- `sample_docs/dify_course_sample.md` — 召回测试样例文档（内含 4 个明确知识点）
- `.env.example` — 配置模板，复制为 `.env` 后填密钥

## 第一步：创建知识库 API 密钥（重要，容易点错）

- 1、登录 [cloud.dify.ai](https://cloud.dify.ai)，点左侧边栏 **「知识库」** 进入知识库列表页
- 2、看页面**右上角**，有两个入口：「外部知识库 API」和 **「服务 API」**（带绿点）
- 3、点 **「服务 API」** → 弹出「API 密钥」面板 → 点 **「创建密钥」**
- 4、复制生成的 `dataset-` 开头的 token，填进 `.env` 的 `DIFY_DATASET_API_KEY=`

⚠️ 三个易错点（都是真实踩过的坑）：

- **别点成「外部知识库 API」**：那是把 Dify 之外的第三方知识库接进 Dify 用的，方向相反；我们要的是「服务 API」
- **别用应用的 `app-` 密钥**：工作室里每个应用有自己的 API 密钥（`app-` 开头），和知识库的 `dataset-` 密钥不通用
- **`.env` 要写成 `变量名=值` 格式**：只把裸 token 贴进 `.env` 是读不出来的，必须写成 `DIFY_DATASET_API_KEY=dataset-xxxx`

## 第二步：确认 Embedding 模型

高质量索引需要 Embedding 模型。工作区右上角如果出现
**「Embedding 模型不可用」** 黄色警告，先去配置：

- 1、右上角头像 → **设置** → **模型供应商**
- 2、安装 **硅基流动（SiliconFlow）** 插件并填入 API Key（它家 BAAI/bge-m3 免费额度够测试用）

⚠️ 真实踩坑：即使某个已有知识库的 Embedding 可用，**通过 API 新建的库**仍可能
沿用工作区默认供应商（可能没配置），上传文档时报
`400 Invalid provider: langgenius/tongyi/tongyi`。
解法就是在 `.env` 里显式指定 Embedding 模型（见下），脚本会把它写进上传请求：

```ini
DIFY_EMBEDDING_MODEL=BAAI/bge-m3
DIFY_EMBEDDING_PROVIDER=langgenius/siliconflow/siliconflow
```

供应商标识可以先跑 `GET /datasets/{id}` 查一个能用的库，
看它的 `embedding_model_provider` 字段抄过来。

## 第三步：运行测试

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

copy .env.example .env
# 编辑 .env，填入 DIFY_DATASET_API_KEY 和 Embedding 配置

python test_cloud_kb.py
```

## 真实运行记录（2026-07-02，SANDBOX 免费版工作区）

```text
[step1] created dataset: 407b53d2-642a-48f2-b84c-7a90126edc0e (dapeng-dify-course-kb-test)
[step2] uploaded document: ff82933a-302a-4d4f-a9ae-abb1dba20857 batch=20260702094612297833
[step3] indexing completed: 2/2 segments

[step4] query: Dify 有哪几种应用类型？
  hit1 score=0.7185374: 大鹏 Dify 开发 AI 智能体 · 课程速览 ...
[step4] query: 知识库的 RAG 原理分哪四步？
  hit1 score=0.608925: ...
[step4] query: 私有化部署 Dify 推荐什么硬件配置？
  hit1 score=0.6428915: ...
[step4] query: 这门课程的主讲老师是谁？
  hit1 score=0.47234964: ...

[result] ALL QUERIES HIT
```

两点真实观察：

- **分段粒度影响召回精细度**：automatic 分段把样例文档只切成 2 段，所以每个问题命中的都是同样两个大段，只是得分排序不同；生产场景想要更精准的命中，应该用更细的分段规则或父子分段
- **得分能反映语义相关度**：与文档内容最贴合的问题（应用类型）得分 0.72，最泛的问题（主讲老师是谁）只有 0.47，score 可以作为设置召回阈值的参考

## 对比实验：知识库的作用一眼看懂（2026-07-02 实测）

`demo_rag_vs_no_rag.py` 用同一个模型（Qwen2.5-7B-Instruct，硅基流动）、
同一个私有问题（"这门课主讲老师是谁？哪个团队出品？"）做 A/B 对比：

```text
========== Round A: 不接知识库 ==========
您提供的课程名称可能存在一些拼写错误或信息不准确。
正确的课程名称应该是...公司是阿里云开发的一款多模态AI模型。
（随后输出退化成大段重复乱码，彻底崩坏——幻觉的真实案例）

========== Round B: 接知识库（RAG） ==========
[retrieved 2 chunks from knowledge base]
这门课程的主讲老师是张大鹏，由大鹏 AI 教育团队出品。
```

运行前在 `.env` 里额外配好 `SILICONFLOW_API_KEY`（可选 `LLM_MODEL` 换模型），然后：

```bash
python demo_rag_vs_no_rag.py
```

一句话结论：**大模型负责"会说话"，知识库负责"说得对"。**
