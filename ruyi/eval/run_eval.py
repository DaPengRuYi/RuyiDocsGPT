# -*- coding: utf-8 -*-
"""RuyiDocsGPT 回归评测运行器。

对一批固定的中文问题跑 /api/answer, 按关键词/拒答启发式判分,
输出 命中率 / 正确率 / 幻觉率, 并把明细写成 markdown 报告。

用法(Windows, 先启动服务):
  # 方式A: 已有导入好的 source_id
  .venv\\Scripts\\python.exe -X utf8 ruyi\\eval\\run_eval.py --active-docs <source_id>

  # 方式B: 自动把 ruyi/eval/corpus 导入成一个 source 再评测
  .venv\\Scripts\\python.exe -X utf8 ruyi\\eval\\run_eval.py --ingest

判分是启发式回归基线(关键词子串 + 拒答措辞), 用于"改动后质量有没有退化"的快速回归,
不等于人工精评。分数明显下降时再人工看明细报告。
"""
import argparse
import json
import os
import re
import time
import urllib.request
import urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))


def http_json(url, payload=None, files=None, timeout=120, method=None):
    if files is not None:
        # multipart 上传
        boundary = "----RuyiEvalBoundary7MA4YWxkTrZu0gW"
        body = b""
        for k, v in (payload or {}).items():
            body += ("--%s\r\nContent-Disposition: form-data; name=\"%s\"\r\n\r\n%s\r\n" % (boundary, k, v)).encode("utf-8")
        for field, (fname, content) in files.items():
            body += ("--%s\r\nContent-Disposition: form-data; name=\"%s\"; filename=\"%s\"\r\nContent-Type: text/markdown\r\n\r\n" % (boundary, field, fname)).encode("utf-8")
            body += content + b"\r\n"
        body += ("--%s--\r\n" % boundary).encode("utf-8")
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "multipart/form-data; boundary=%s" % boundary})
    else:
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        headers = {"Content-Type": "application/json"} if data else {}
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def ingest_corpus(api):
    """把 corpus 目录下的 md 上传成一个 source, 返回 source_id。"""
    corpus_dir = os.path.join(HERE, "corpus")
    files = {}
    payload = {"user": "local", "name": "ruyi_eval_corpus"}
    # 逐个文件塞进 multipart(字段名都叫 file, 但 urllib 简易实现只支持一个同名字段, 故合并上传逐个调用)
    # 简化: 上传第一个文件建 source, 其余追加? DocsGPT 一次 upload 可多文件, 但简易 multipart 只发一个。
    # 这里改为: 把多个文件合并进一次 multipart(不同 filename), 需要多字段——DocsGPT 用 getlist("file")。
    md_files = sorted([f for f in os.listdir(corpus_dir) if f.endswith(".md")])
    if not md_files:
        raise SystemExit("corpus 目录没有 .md 文件")
    # 手工拼多份 file 字段
    boundary = "----RuyiEvalBoundary7MA4YWxkTrZu0gW"
    body = b""
    for k, v in payload.items():
        body += ("--%s\r\nContent-Disposition: form-data; name=\"%s\"\r\n\r\n%s\r\n" % (boundary, k, v)).encode("utf-8")
    for fname in md_files:
        with open(os.path.join(corpus_dir, fname), "rb") as fh:
            content = fh.read()
        body += ("--%s\r\nContent-Disposition: form-data; name=\"file\"; filename=\"%s\"\r\nContent-Type: text/markdown\r\n\r\n" % (boundary, fname)).encode("utf-8")
        body += content + b"\r\n"
    body += ("--%s--\r\n" % boundary).encode("utf-8")
    req = urllib.request.Request(api + "/api/upload", data=body, headers={"Content-Type": "multipart/form-data; boundary=%s" % boundary})
    with urllib.request.urlopen(req, timeout=120) as r:
        resp = json.load(r)
    sid = resp.get("source_id")
    print("[ingest] 上传成功, source_id=%s, 等待索引..." % sid)
    return sid


def wait_indexed(api, sid, timeout=300):
    """轮询直到该 source 能检索出结果(索引完成)。"""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            d = ask(api, "测试", sid)
            if d.get("sources"):
                print("[ingest] 索引完成")
                return True
        except Exception:
            pass
        time.sleep(4)
    print("[ingest] 等待索引超时(%ss), 仍尝试评测" % timeout)
    return False


def ask(api, question, active_docs):
    payload = {"question": question, "active_docs": active_docs, "retriever": "classic", "chunks": 4}
    return http_json(api + "/api/answer", payload=payload, timeout=120)


def ask_with_retry(api, question, active_docs, retries=3, backoff=30):
    # 题目连发容易打爆 LLM API 的 TPM 限流(表现为后端返回 400),
    # 失败后等一个限流窗口再重试, 避免把限流误判成幻觉
    last_err = None
    for attempt in range(retries + 1):
        try:
            return ask(api, question, active_docs)
        except urllib.error.HTTPError as e:
            last_err = e
            if attempt < retries:
                print("  [retry] HTTP %s, %ss 后重试(%d/%d)" % (e.code, backoff, attempt + 1, retries))
                time.sleep(backoff)
        except Exception as e:
            last_err = e
            if attempt < retries:
                time.sleep(backoff)
    raise last_err


def contains_all(text, keywords):
    t = (text or "").lower()
    missing = [k for k in keywords if k.lower() not in t]
    return (len(missing) == 0), missing


# 拒答的正则模式: 否定词 + (可选修饰) + 覆盖类动词。
# 固定措辞库对非确定性输出是打地鼠(一周八场冤案的教训), 模式匹配把
# "没有提到/未被涵盖/没有被明确记录/未在书中提及"这类变体一网打尽。
REFUSAL_PATTERNS = [
    r"(没有|未|无|不曾)[^。！？]{0,6}(提及|提到|记录|涵盖|包含|说明|写明|给出|列出|找到|出现|回答)",
    r"无法[^。！？]{0,10}(回答|确定|提供|给出|得知|获取|查到|找到)",
    r"(文档|资料|书稿?|内容|语料)[^。！？]{0,10}(没有|不包含|查不到|找不到)",
    r"抱歉",
]


def is_refusal(text, phrases):
    t = text or ""
    if any(p in t for p in phrases):
        return True
    return any(re.search(pat, t) for pat in REFUSAL_PATTERNS)


def load_env(repo_root):
    """Parse repo root .env into a dict (no external deps)."""
    cfg = {}
    path = os.path.join(repo_root, ".env")
    if not os.path.exists(path):
        return cfg
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        cfg[k.strip()] = v.strip().strip('"').strip("'")
    return cfg


JUDGE_SYSTEM = (
    "你是 RAG 评测的裁判。给你一道知识库资料里没有答案的测试问题, 以及系统的回答。"
    "判断系统是否诚实: 承认资料中没有该信息(明确拒答、说明无法基于文档回答、"
    "或声明只能转用通用知识且未编造具体事实)算诚实; 给出了资料中不存在的具体名称、"
    "数字、日期、机构等事实, 算编造。只输出一个词: REFUSED(诚实) 或 FABRICATED(编造)。"
)


def llm_judge_refusal(env, question, answer, retries=3, backoff=20):
    """用大模型终审语料外题的拒答判定。返回 True/False, 失败返回 None(回落启发式)。

    动机: 拒答措辞是非确定性的, 措辞库+正则治标不治本(一周八场冤案),
    语义层面的判定只有让大模型当裁判才靠得住。
    """
    base = (env.get("OPENAI_BASE_URL") or "").rstrip("/")
    key = env.get("API_KEY", "")
    model = env.get("LLM_NAME", "")
    if not (base and key and model):
        return None
    payload = {
        "model": model,
        "temperature": 0,
        "max_tokens": 8,
        "messages": [
            {"role": "system", "content": JUDGE_SYSTEM},
            {"role": "user", "content": "问题: %s\n\n系统回答: %s" % (question, answer)},
        ],
    }
    req = urllib.request.Request(
        base + "/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + key},
    )
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                resp = json.load(r)
            word = (resp["choices"][0]["message"]["content"] or "").strip().upper()
            if "REFUSED" in word:
                return True
            if "FABRICATED" in word:
                return False
            return None  # 裁判没按格式说话, 回落启发式
        except Exception:
            if attempt < retries:
                time.sleep(backoff)
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--api", default="http://127.0.0.1:7091", help="后端地址")
    ap.add_argument("--active-docs", default=None, help="已导入的 source_id")
    ap.add_argument("--ingest", action="store_true", help="自动导入 ruyi/eval/corpus 再评测")
    ap.add_argument("--testset", default=os.path.join(HERE, "testset.json"))
    ap.add_argument("--report", default=os.path.join(HERE, "last_report.md"))
    ap.add_argument("--delay", type=float, default=3.0, help="题间隔秒数(防 LLM API 限流)")
    ap.add_argument("--judge", action="store_true", help="语料外题用 LLM 终审拒答判定(读 .env 的模型配置)")
    args = ap.parse_args()

    ts = json.load(open(args.testset, encoding="utf-8"))
    refusal_phrases = ts.get("refusal_phrases", [])
    questions = ts["questions"]

    sid = args.active_docs
    if args.ingest:
        sid = ingest_corpus(args.api)
        wait_indexed(args.api, sid)
    if not sid:
        raise SystemExit("必须提供 --active-docs <source_id> 或使用 --ingest")

    rows = []
    n_hit = n_correct = n_halluc = n_disagree = 0
    n_in = sum(1 for q in questions if q["type"] == "in_corpus")
    n_out = sum(1 for q in questions if q["type"] == "out_of_corpus")
    env = {}
    if args.judge:
        repo_root = os.path.dirname(os.path.dirname(HERE))
        env = load_env(repo_root)
        if not env.get("API_KEY"):
            print("[judge] 未在 .env 找到模型配置, judge 模式将回落启发式判定")

    for q in questions:
        try:
            d = ask_with_retry(args.api, q["q"], sid)
            answer = d.get("answer", "") or ""
            srcs = d.get("sources", []) or []
        except Exception as e:
            answer, srcs = "[ERROR] %s" % e, []
        time.sleep(args.delay)  # 节流, 降低触发 TPM 限流的概率

        hit = len(srcs) > 0
        if hit:
            n_hit += 1

        if q["type"] == "in_corpus":
            ok, missing = contains_all(answer, q.get("expect_keywords", []))
            if ok:
                n_correct += 1
            verdict = "正确" if ok else ("缺关键词: " + ",".join(missing))
            halluc = ""
        else:
            heur_refused = is_refusal(answer, refusal_phrases)
            refused, tag = heur_refused, ""
            if args.judge and not answer.startswith("[ERROR]"):
                jr = llm_judge_refusal(env, q["q"], answer)
                if jr is None:
                    tag = "(judge 失败, 回落启发式)"
                else:
                    refused = jr
                    if jr != heur_refused:
                        n_disagree += 1
                        tag = "(judge 推翻启发式: 启发式=%s)" % ("拒答" if heur_refused else "幻觉")
                    else:
                        tag = "(judge 一致)"
            if not refused:
                n_halluc += 1
                verdict = "幻觉(未拒答/可能编造)" + tag
                halluc = "是"
            else:
                verdict = "正确拒答" + tag
                halluc = "否"

        rows.append({
            "id": q["id"], "type": q["type"], "q": q["q"],
            "hit": hit, "n_src": len(srcs), "verdict": verdict,
            "answer": answer[:200].replace("\n", " "),
        })
        print("Q%-2d [%s] hit=%s src=%d -> %s" % (q["id"], q["type"], hit, len(srcs), verdict))

    total = len(questions)
    hit_rate = n_hit / total if total else 0
    correct_rate = n_correct / n_in if n_in else 0
    halluc_rate = n_halluc / n_out if n_out else 0

    print("\n==== 汇总 ====")
    print("命中率(有引用):   %d/%d = %.0f%%" % (n_hit, total, hit_rate * 100))
    print("正确率(语料内):   %d/%d = %.0f%%" % (n_correct, n_in, correct_rate * 100))
    print("幻觉率(语料外):   %d/%d = %.0f%%" % (n_halluc, n_out, halluc_rate * 100))
    if args.judge:
        print("judge 推翻启发式: %d/%d" % (n_disagree, n_out))

    # 写 markdown 报告
    lines = []
    lines.append("# RuyiDocsGPT 评测报告")
    lines.append("")
    lines.append("- source_id: `%s`" % sid)
    if args.judge:
        lines.append("- 拒答判定: LLM judge 终审(%s), 推翻启发式 %d/%d" % (env.get("LLM_NAME", "?"), n_disagree, n_out))
    lines.append("- 命中率(有引用): **%d/%d = %.0f%%**" % (n_hit, total, hit_rate * 100))
    lines.append("- 正确率(语料内): **%d/%d = %.0f%%**" % (n_correct, n_in, correct_rate * 100))
    lines.append("- 幻觉率(语料外): **%d/%d = %.0f%%**" % (n_halluc, n_out, halluc_rate * 100))
    lines.append("")
    lines.append("| # | 类型 | 命中 | 引用数 | 判定 | 问题 | 答案摘录 |")
    lines.append("|---|---|---|---|---|---|---|")
    for r in rows:
        # 答案里的竖线会破坏 markdown 表格, 转义掉
        ans = r["answer"].replace("|", "\\|")
        lines.append("| %d | %s | %s | %d | %s | %s | %s |" % (
            r["id"], r["type"], "是" if r["hit"] else "否", r["n_src"], r["verdict"], r["q"], ans))
    open(args.report, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("\n报告已写入: %s" % args.report)


if __name__ == "__main__":
    main()
