# ============================================================
# RuyiDocsGPT 评测语料同步 (书稿 -> ruyi/eval/corpus)
#   powershell -ExecutionPolicy Bypass -File .\ruyi\scripts\ruyi-sync-corpus.ps1
# 把《大鹏 RAG 实战：如意知识库工厂》中文版 13 章复制为评测语料,
# 实现"用这本书问这本书"的自指演示闭环。
# 文件名转成 ASCII(chNN_xxx.md), 规避中文文件名上传被解析为空的坑(见书 ch03 坑四)。
# 没有书稿的机器不用跑本脚本: 仓库内 corpus/ 已自带同步好的副本。
# ============================================================
$ErrorActionPreference = "Stop"

$BookDir = "D:\notes\RuyiBookCourse\图书\AI 开发\大鹏 RAG 实战：如意知识库工厂\中文版"
$RepoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$CorpusDir = Join-Path $RepoRoot "ruyi\eval\corpus"

if (-not (Test-Path $BookDir)) {
  Write-Host "[X] 未找到书稿目录: $BookDir" -ForegroundColor Red
  Write-Host "    本脚本只在有书稿的机器上用来刷新语料; 仓库内 corpus/ 已有现成副本。" -ForegroundColor Yellow
  exit 1
}

# 章节文件名映射: 书稿中文名 -> 语料 ASCII 名(顺序即章节顺序)
$Map = [ordered]@{
  "00_前言与导读.md"        = "ch00_preface.md"
  "01_RAG解决什么问题.md"   = "ch01_rag_problem.md"
  "02_如意知识库工厂总览.md" = "ch02_factory_overview.md"
  "03_跑通DocsGPT.md"       = "ch03_run_docsgpt.md"
  "04_DocsGPT架构拆解.md"   = "ch04_architecture.md"
  "05_文档入库流水线.md"    = "ch05_ingest_pipeline.md"
  "06_Embedding与向量检索.md" = "ch06_embedding_retrieval.md"
  "07_问答链路与引用来源.md" = "ch07_qa_citations.md"
  "08_模型接入实战.md"      = "ch08_model_integration.md"
  "09_RuyiDocsGPT纯二开.md" = "ch09_ruyi_fork.md"
  "10_部署交付.md"          = "ch10_deployment.md"
  "11_质量评测与运维.md"    = "ch11_eval_ops.md"
  "12_做成可交付项目.md"    = "ch12_deliverable.md"
}

New-Item -ItemType Directory -Force -Path $CorpusDir | Out-Null

# 先清掉 corpus 里的旧 md, 保证语料 = 书稿的干净镜像
Get-ChildItem -Path $CorpusDir -Filter "*.md" | Remove-Item -Force

$n = 0
foreach ($src in $Map.Keys) {
  $srcPath = Join-Path $BookDir $src
  if (-not (Test-Path $srcPath)) {
    Write-Host "[!] 书稿缺章, 跳过: $src" -ForegroundColor Yellow
    continue
  }
  Copy-Item $srcPath (Join-Path $CorpusDir $Map[$src]) -Force
  $n++
}

Write-Host "[ok] 已同步 $n 章书稿到 $CorpusDir" -ForegroundColor Green
Write-Host "     下一步: .\.venv\Scripts\python.exe -X utf8 .\ruyi\eval\run_eval.py --ingest"
