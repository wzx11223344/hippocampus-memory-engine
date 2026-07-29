"""离线 TF-IDF 嵌入（无需联网下载模型）。可替换为 chromadb/miniLM 等语义嵌入。"""
import json, re, math
import numpy as np

class TfidfEmbedder:
    def __init__(self, vocab_path):
        self.vocab_path = vocab_path
        self.vocab = {}
        self.idf = {}
        self.dim = 0
        self._load()

    def _load(self):
        try:
            with open(self.vocab_path, encoding="utf-8") as f:
                d = json.load(f)
            self.vocab = d.get("vocab", {})
            self.idf = d.get("idf", {})
            self.dim = len(self.vocab)
        except Exception:
            self.vocab, self.idf, self.dim = {}, {}, 0

    def _save(self):
        with open(self.vocab_path, "w", encoding="utf-8") as f:
            json.dump({"vocab": self.vocab, "idf": self.idf}, f, ensure_ascii=False)

    @staticmethod
    def _tokenize(text):
        text = (text or "").lower()
        toks = re.findall(r"[a-z0-9]+", text)
        cjk = "".join(re.findall(r"[一-鿿]", text))
        for i in range(len(cjk)):
            toks.append(cjk[i])                      # 单字
            if i + 1 < len(cjk):
                toks.append(cjk[i:i + 2])            # 双字（提升中文区分度）
        return toks

    def fit(self, corpus):
        df = {}
        for doc in corpus:
            for t in set(self._tokenize(doc)):
                df[t] = df.get(t, 0) + 1
        n = max(len(corpus), 1)
        self.vocab = {t: i for i, t in enumerate(sorted(df.keys()))}
        self.idf = {t: math.log((n + 1) / (c + 1)) + 1 for t, c in df.items()}
        self.dim = len(self.vocab)
        self._save()

    def embed(self, text):
        vec = np.zeros(self.dim, dtype=np.float32)
        toks = self._tokenize(text)
        if not toks:
            return vec
        tf = {}
        for t in toks:
            tf[t] = tf.get(t, 0) + 1
        for t, c in tf.items():
            if t in self.vocab:
                vec[self.vocab[t]] = (c / len(toks)) * self.idf.get(t, 1.0)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec
