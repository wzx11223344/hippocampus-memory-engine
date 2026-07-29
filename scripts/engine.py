"""海马体记忆流引擎：双写(L3 SQLite + L2 向量) + RAG 检索 + 蒸馏到知识库。"""
import json, os, time
from db import init_db, insert, get_by_id, update_access, list_all, count, clear as db_clear
from vectors import VectorStore
from embed import TfidfEmbedder

class HippocampusEngine:
    def __init__(self, cfg_path="config.json"):
        with open(cfg_path, encoding="utf-8") as f:
            self.cfg = json.load(f)
        p = self.cfg["paths"]
        base = os.path.dirname(os.path.abspath(cfg_path))
        self.user_id = self.cfg["user_id"]
        self.threshold = self.cfg.get("similarity_threshold", 0.10)
        self.top_k = self.cfg.get("top_k", 5)
        self.db_path = os.path.join(base, p["db"])
        self.vec_path = os.path.join(base, p["vectors"])
        self.vocab_path = os.path.join(base, p["vocab"])
        self.knowledge_path = os.path.normpath(os.path.join(base, p["knowledge"]))
        self.con = init_db(self.db_path)
        self.store = VectorStore(self.vec_path)
        self.embedder = TfidfEmbedder(self.vocab_path)
        # 若词表为空，先以现有语料 fit 一次
        if self.embedder.dim == 0:
            self._fit_from_db()

    # ---------- 写入（双写） ----------
    def add_memory(self, content, memory_type="episodic", source="agent", importance=0.5):
        mid = insert(self.con, self.user_id, content, memory_type, source, importance)
        vec = self.embedder.embed(content)
        self.store.add(mid, vec)
        self.store.save()
        return mid

    def _fit_from_db(self):
        rows = list_all(self.con)
        corpus = [r[1] for r in rows if isinstance(r[1], str)]
        if corpus:
            self.embedder.fit(corpus)

    def reset(self):
        """清空 L3 + L2，准备从静态源重新 consolidate。"""
        db_clear(self.con)
        self.store.clear()

    # ---------- 检索（RAG） ----------
    def retrieve(self, query, top_k=None, threshold=None):
        top_k = top_k or self.top_k
        threshold = threshold if threshold is not None else self.threshold
        qvec = self.embedder.embed(query)
        hits = self.store.search(qvec, top_k=top_k, threshold=threshold)
        out = []
        for mid, sim in hits:
            row = get_by_id(self.con, mid)
            if row:
                update_access(self.con, mid)
                out.append({
                    "id": row[0], "content": row[2], "type": row[3],
                    "source": row[4], "importance": row[5], "sim": round(sim, 3)
                })
        return out

    # ---------- 蒸馏：引擎记忆 -> knowledge.json（海马体知识库） ----------
    def distill_to_knowledge(self, max_items=12):
        """把高 importance / 近期访问的引擎记忆，并入 knowledge.json 作为「自动沉淀」区。"""
        rows = list_all(self.con)
        if not rows:
            return
        scored = []
        now = time.time()
        for r in rows:
            mid, content, mtype, source, imp, created = r
            recency = 1.0 / (1.0 + (now - created) / 86400.0)
            score = 0.6 * (imp or 0.5) + 0.4 * recency
            scored.append((score, content, mtype, source))
        scored.sort(key=lambda x: x[0], reverse=True)
        picked = scored[:max_items]

        kb = {}
        if os.path.exists(self.knowledge_path):
            with open(self.knowledge_path, encoding="utf-8") as f:
                kb = json.load(f)
        regions = kb.get("regions", [])
        # 找或建「自动沉淀」区
        auto = next((r for r in regions if r["id"] == "auto"), None)
        if not auto:
            auto = {"id": "auto", "name": "自动沉淀 (Auto Consolidation)",
                    "role": "引擎自动蒸馏的记忆", "color": "#37474F",
                    "summary": "由记忆流引擎从会话/日志中自动提取并巩固的知识点。", "items": []}
            regions.append(auto)
        auto["items"] = [
            {"title": f"[{mtype}] {source}", "detail": content,
             "source": f"记忆流引擎 memory.db (#{i + 1})"}
            for i, (_, content, mtype, source) in enumerate(picked)
        ]
        kb["regions"] = regions
        with open(self.knowledge_path, "w", encoding="utf-8") as f:
            json.dump(kb, f, ensure_ascii=False, indent=2)
        return len(picked)

    def stats(self):
        return {"total_memories": count(self.con), "vector_dim": self.embedder.dim}
