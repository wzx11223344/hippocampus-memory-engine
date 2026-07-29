"""L2 温记忆：向量索引（numpy 持久化，零依赖）。"""
import numpy as np, os

class VectorStore:
    def __init__(self, path):
        # np.save 会自动补 .npy，这里统一强制扩展名，避免 save/load 文件名不一致
        if not path.endswith(".npy"):
            path = path + ".npy"
        self.path = path
        self.vectors = {}
        self._load()

    def _load(self):
        if os.path.exists(self.path):
            try:
                d = np.load(self.path, allow_pickle=True)
                # np.save(dict) -> 0维 object 数组，需用 .item() 还原
                obj = d.item() if (hasattr(d, "dtype") and d.dtype == object) else d
                self.vectors = {int(k): v for k, v in obj["vectors"].items()}
            except Exception as e:
                print(f"[VectorStore] load failed: {e}")
                self.vectors = {}

    def add(self, mid, vec):
        self.vectors[int(mid)] = np.asarray(vec, dtype=np.float32).tolist()

    def save(self):
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        np.save(self.path, {"vectors": self.vectors})

    def clear(self):
        self.vectors = {}
        self.save()

    def search(self, query_vec, top_k=5, threshold=0.10):
        q = np.asarray(query_vec, dtype=np.float32)
        res = []
        for mid, v in self.vectors.items():
            vv = np.asarray(v, dtype=np.float32)
            denom = np.linalg.norm(q) * np.linalg.norm(vv)
            sim = float(np.dot(q, vv) / denom) if denom > 0 else 0.0
            if sim >= threshold:
                res.append((mid, sim))
        res.sort(key=lambda x: x[1], reverse=True)
        return res[:top_k]
