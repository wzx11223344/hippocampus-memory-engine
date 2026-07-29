"""sync.py —— 海马体记忆流同步入口。
模式：
  seed    把现有资产(知识库/knowledge.json + MEMORY.md + 工作区日志 + 归档README)灌入引擎
  distill 把引擎高价值记忆蒸馏进 knowledge.json（海马体知识库）
  rebuild 依据 knowledge.json 重建 index.html（可视化同步）
  all     依次执行 seed -> distill -> rebuild
用法：python sync.py all
"""
import json, os, glob, sys
from engine import HippocampusEngine
import build_index

def _read_lines(path):
    try:
        with open(path, encoding="utf-8") as f:
            return [l.strip() for l in f if l.strip()]
    except Exception:
        return []

def seed(eng: HippocampusEngine):
    p = eng.cfg["paths"]
    base = os.path.dirname(os.path.abspath("config.json"))
    added = 0

    # 先收集全部语料，fit 词表（保证向量非零）
    corpus = []
    kp = os.path.normpath(os.path.join(base, p["knowledge"]))
    if os.path.exists(kp):
        with open(kp, encoding="utf-8") as f:
            kb = json.load(f)
        for reg in kb.get("regions", []):
            for it in reg.get("items", []):
                corpus.append(f"{it.get('title','')}：{it.get('detail','')}")
    mm = p["sources"]["memory_md"]
    if os.path.exists(mm):
        corpus += [c for c in _read_lines(mm) if len(c) > 6]
    wl = os.path.normpath(os.path.join(base, p["sources"]["workspace_logs"]))
    if os.path.isdir(wl):
        for fp in glob.glob(os.path.join(wl, "*.md")):
            corpus += [l for l in _read_lines(fp) if len(l) > 10]
    ar = os.path.normpath(os.path.join(base, p["sources"]["archive_readme"]))
    if os.path.exists(ar):
        corpus += [l for l in _read_lines(ar) if len(l) > 10]
    # TRAE 记忆（user_profile / project_memory / topics / session jsonl）
    trae_dir = os.path.normpath(os.path.join(base, p["sources"]["trae_memory"]))
    for fp in glob.glob(os.path.join(trae_dir, "**", "*.md"), recursive=True):
        corpus += [l for l in _read_lines(fp) if len(l) > 6]
    for fp in glob.glob(os.path.join(trae_dir, "**", "session_memory_*.jsonl"), recursive=True):
        try:
            with open(fp, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        o = json.loads(line)
                    except Exception:
                        continue
                    learned = o.get("learned", [])
                    if isinstance(learned, list):
                        learned = "；".join(learned)
                    txt = f"{o.get('intent','')} {learned} {o.get('outcome','')}".strip()
                    if len(txt) > 8:
                        corpus.append(txt)
        except Exception:
            pass
    if corpus:
        eng.embedder.fit(corpus)

    # 1) knowledge.json 现有结构化知识点（语义/情景）
    kp = os.path.normpath(os.path.join(base, p["knowledge"]))
    if os.path.exists(kp):
        with open(kp, encoding="utf-8") as f:
            kb = json.load(f)
        for reg in kb.get("regions", []):
            for it in reg.get("items", []):
                txt = f"{it.get('title','')}：{it.get('detail','')}"
                eng.add_memory(txt, memory_type="semantic", source=f"knowledge:{reg['id']}", importance=0.7)
                added += 1

    # 2) 账号级 MEMORY.md（语义/偏好）
    mm = p["sources"]["memory_md"]
    if os.path.exists(mm):
        txt = "\n".join(_read_lines(mm))
        # 按空行/标题分块
        for chunk in [c for c in txt.split("\n") if len(c) > 6]:
            eng.add_memory(chunk, memory_type="semantic", source="MEMORY.md", importance=0.8)
            added += 1

    # 3) 工作区日志（情景）
    wl = os.path.normpath(os.path.join(base, p["sources"]["workspace_logs"]))
    if os.path.isdir(wl):
        for fp in glob.glob(os.path.join(wl, "*.md")):
            for line in _read_lines(fp):
                if len(line) > 10:
                    eng.add_memory(line, memory_type="episodic", source=f"log:{os.path.basename(fp)}", importance=0.5)
                    added += 1

    # 4) 归档 README（索引）
    ar = os.path.normpath(os.path.join(base, p["sources"]["archive_readme"]))
    if os.path.exists(ar):
        for line in _read_lines(ar):
            if len(line) > 10:
                eng.add_memory(line, memory_type="semantic", source="导入归档/README.md", importance=0.6)
                added += 1

    # 5) 本机 TRAE 记忆工作流（user_profile / project_memory / topics / session jsonl）
    added += _seed_trae(eng)

    print(f"[seed] 已灌入 {added} 条记忆；引擎统计 {eng.stats()}")
    return added


def _seed_trae(eng: HippocampusEngine):
    """把 TRAE 的记忆工作流灌入引擎：偏好/项目记忆/主题/会话学到的经验。"""
    p = eng.cfg["paths"]
    base = os.path.dirname(os.path.abspath("config.json"))
    tp = os.path.normpath(os.path.join(base, p["sources"]["trae_memory"]))
    added = 0
    if not os.path.isdir(tp):
        return 0
    # user_profile.md + 各 project_memory.md + topics.md（按行）
    for fp in glob.glob(os.path.join(tp, "**", "*.md"), recursive=True):
        tag = "trae:user_profile" if os.path.basename(fp) == "user_profile.md" else (
            "trae:project_memory" if os.path.basename(fp) == "project_memory.md" else "trae:topics")
        for line in _read_lines(fp):
            if len(line) > 6:
                eng.add_memory(line, memory_type="semantic", source=tag, importance=0.7)
                added += 1
    # session_memory_*.jsonl：每条 = 一次会话学到的经验（情景/程序记忆）
    for fp in glob.glob(os.path.join(tp, "**", "session_memory_*.jsonl"), recursive=True):
        try:
            with open(fp, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        o = json.loads(line)
                    except Exception:
                        continue
                    intent = o.get("intent", "")
                    learned = o.get("learned", [])
                    if isinstance(learned, list):
                        learned = "；".join(learned)
                    outcome = o.get("outcome", "")
                    text = f"意图：{intent}｜学到：{learned}｜结果：{outcome}".strip("｜")
                    if len(text) > 8:
                        eng.add_memory(text, memory_type="episodic", source="trae:session", importance=0.6)
                        added += 1
        except Exception:
            pass
    print(f"[seed:trae] 已灌入 {added} 条 TRAE 记忆")
    return added

def distill(eng: HippocampusEngine):
    n = eng.distill_to_knowledge()
    print(f"[distill] 已蒸馏 {n} 条进 knowledge.json")

def rebuild(eng: HippocampusEngine):
    ih = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath('config.json')), eng.cfg["paths"]["index_html"]))
    build_index.build(eng.knowledge_path, ih)
    print(f"[rebuild] 已重建 {ih}")

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    eng = HippocampusEngine("config.json")
    if mode in ("seed", "all"):
        if mode == "all":
            eng.reset()  # consolidation：先清空再重灌，保证幂等
        seed(eng)
    if mode in ("distill", "all"):
        distill(eng)
    if mode in ("rebuild", "all"):
        rebuild(eng)
    print("DONE.")

if __name__ == "__main__":
    main()
