---
name: hippocampus-memory-engine
description: "以海马体神经环路为隐喻的 Agent 外部记忆引擎（情景/语义/程序三类记忆 + L1/L2/L3 三级存储 + RAG 检索 + 自动蒸馏）。当需要为 Agent 搭建持久化记忆中枢、把分散的日志/MEMORY.md/知识库/TRAE 记忆统一向量化检索、或生成海马体 SVG 可视化知识库时使用本 skill。内置 TF-IDF 本地向量化（无需下载大模型），离线可跑，适合个人知识管理与跨会话记忆同步。"
agent_created: true
---

# 海马体记忆流引擎 (Hippocampus Memory Engine)

## 概览

把 LLM 当作"大脑皮层"、把外部存储当作"海马体"。本 skill 提供一套**离线、零模型下载**的 Python 引擎，把分散在各处的记忆（会话日志、账号级 `MEMORY.md`、知识库 `knowledge.json`、归档 README、以及 TRAE 的记忆工作流）统一向量化、持久化，并支持：

- **RAG 检索**：`感知→回忆→筛选→注入`，余弦相似度召回 top-k。
- **三类记忆**：情景(episodic) / 语义(semantic) / 程序(procedural)。
- **三级存储**：L1 滑窗（运行时）、L2 向量库（numpy `.npy`）、L3 SQLite（`memory.db`，事实源）。
- **双写一致性**：写入时同步落 L3 与 L2，L2 仅存向量并引用 `mid`。
- **自动蒸馏**：高价值记忆周期性蒸馏进 `knowledge.json` 的 `auto` 区。
- **可视化**：依据 `knowledge.json` 重建海马体 SVG 的 `index.html`，可作为本地文件或 GitHub Pages 网站。

适用场景示例：
- "帮我把 WorkBuddy 的 MEMORY.md 和 TRAE 记忆合并成一个可检索的记忆库"
- "做一个海马体形式的知识库网站"
- "让新会话能自动回忆之前的偏好与项目约定"

## 何时使用

- 用户要求搭建/维护 Agent 的"外部记忆""海马体记忆""记忆中枢"。
- 用户有多个记忆源（日志、MEMORY.md、知识库、TRAE/其他工具备份）需要统一检索。
- 用户要生成海马体结构的可视化知识库或静态网站。

## 快速开始（一次性部署）

引擎脚本位于本 skill 的 `scripts/`。按以下步骤在任意工作目录部署（路径相对 `config.json` 所在目录解析，故可整体复制迁移）：

1. **复制脚本**：把 `scripts/` 整体复制到工作目录，例如 `~/hippocampus-engine/`。
2. **准备 Python 环境**（Windows 用 `Scripts/python.exe`，Linux/macOS 用 `bin/python`）：
   ```bash
   python -m venv venv
   venv/Scripts/python.exe -m pip install numpy   # 唯一依赖
   ```
3. **编辑 `config.json`**：把 `paths.sources` 指向真实记忆源。所有路径相对 `config.json` 所在目录；缺失的源会被安全跳过。
   - `memory_md`：账号级 `MEMORY.md`（如 `~/.workbuddy/MEMORY.md`）
   - `workspace_logs`：工作区每日日志目录（含 `*.md`）
   - `archive_readme`：归档索引 `README.md`
   - `trae_memory`：TRAE 记忆备份目录（含 `user_profile.md` / `project_memory.md` / `topics.md` / `session_memory_*.jsonl`）
   - `knowledge` / `index_html`：知识库 JSON 与输出可视化 HTML
4. **运行整条流水线**：
   ```bash
   venv/Scripts/python.exe sync.py all
   ```
   `all` = `reset`（清空 L3/L2，保证幂等）→ `seed`（灌入并向量化）→ `distill`（蒸馏进 `auto` 区）→ `rebuild`（重建 `index.html`）。

开箱示例：本 skill 已附带 `scripts/knowledge.json`（海马体 5 区 + auto 区示例），不改任何配置直接 `python sync.py all` 即可生成 `index.html` 验证引擎可用。

## 核心能力

### 1. 检索（RAG recall）
```python
from engine import HippocampusEngine
eng = HippocampusEngine("config.json")
hits = eng.retrieve("链主申报书 附件3 合并 Excel", top_k=3, threshold=0.05)
# hits: [{"id","content","type","source","importance","sim"}, ...]
```
`threshold` 默认 0.10；中文稀疏 TF-IDF 下可调低到 0.03–0.05 提升召回。

### 2. 增量写入（双写）
```python
eng.add_memory("新的偏好：表格必须带状态指示与计数", memory_type="semantic",
               source="agent", importance=0.8)
```

### 3. 蒸馏到知识库
`eng.distill_to_knowledge(max_items=12)` 按 `0.6*importance + 0.4*recency` 给记忆打分，取 top-k 写入 `knowledge.json` 的 `auto` 区。

### 4. 自动同步（跨会话）
每个 WorkBuddy 会话本就会向每日日志与 `MEMORY.md` 写入；用一个定时任务每天跑 `sync.py all`，即可把**任何新任务/新对话**当晚汇流进中枢。参考 `references/sync-automation.md`。

### 5. 可视化重建
`build_index.build(knowledge_path, out_html)` 依据 `knowledge.json` 重建自包含的 `index.html`（数据内联，可直接打开或部署到 GitHub Pages）。

## 文件清单（scripts/）

| 文件 | 职责 |
|---|---|
| `config.json` | 用户 ID、相似度阈值、top_k、各路径配置 |
| `embed.py` | `TfidfEmbedder`：中文单/双字 + 拉丁分词，TF-IDF 向量化 |
| `vectors.py` | `VectorStore`：numpy `.npy` 持久化、余弦检索、阈值过滤 |
| `db.py` | SQLite L3：`init_db/insert/get_by_id/update_access/list_all/count/clear` |
| `engine.py` | `HippocampusEngine`：双写、检索、蒸馏、统计 |
| `sync.py` | 入口：`seed/distill/rebuild/all` 四种模式 |
| `build_index.py` | 依据 `knowledge.json` 生成海马体 SVG 可视化 `index.html` |

## 关键实现注意（避免踩坑）

- **向量文件后缀**：`np.save(path, obj)` 会自动补 `.npy`。`config.json` 里的 `vectors` 路径必须显式以 `.npy` 结尾，且 `_load` 必须用 `np.load(...).item()["vectors"]` 反序列化（不是 `d["vectors"]`）。
- **先 fit 再 add**：`seed()` 必须先把全部语料 `embedder.fit(corpus)` 建好词表，再逐条 `add_memory`，否则会存进零向量。
- **路径相对 config 目录**：`base = dirname(abspath(cfg_path))`，复制整套脚本到新目录即可迁移，无需改绝对路径。
- **幂等**：`sync.py all` 先 `reset()` 再 `seed()`，可反复运行不重复。

## 参考

- `references/DESIGN.md`：海马体记忆架构设计（EC/DG/CA3/CA1/Subiculum 映射、L1/L2/L3、RAG 流程、生命周期）。
- `references/sync-automation.md`：每天 23:00 自动 consolidate 的定时任务配置示例（使新会话记忆自动汇流）。
