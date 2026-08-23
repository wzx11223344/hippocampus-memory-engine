# 🧠 Hippocampus Memory Engine（海马体记忆流引擎）

以**海马体神经环路**为隐喻的 Agent 外部记忆引擎：把 LLM 当作"大脑皮层"（无持久记忆），把外部存储当作"海马体"（长期记忆中枢）。

> 灵感来自抖音「小克和世杰肝代码」的《从外部记忆机制入手给 Agent 搭建一个海马体》以及同源技术文章（CSDN 万字 Agent 记忆系统、2048ai 赋予 Agent 海马体、掘金 Hindsight）。

## ✨ 特性

- **三类记忆**：情景(episodic) / 语义(semantic) / 程序(procedural)
- **三级存储**：L1 滑窗（运行时）→ L2 向量库（numpy `.npy`）→ L3 SQLite（`memory.db`，事实源）
- **双写一致性**：写入同步落 L3 + L2，L2 仅存向量并引用 `mid`
- **RAG 检索**：感知 → 回忆 → 筛选 → 注入（余弦相似度 top-k）
- **自动蒸馏**：高价值记忆周期性蒸馏进 `knowledge.json` 的 `auto` 区
- **可视化**：依据 `knowledge.json` 重建海马体 SVG 的 `index.html`（可本地打开或部署 GitHub Pages）
- **流动知识图谱**：`flow.html` / `flowsite/index.html` 提供可交互的力导向图谱
- **Obsidian 同步**：一键导出 `knowledge.json` 为 Obsidian Vault 的 Markdown + 双链
- **零模型下载**：本地 TF-IDF 向量化（仅依赖 `numpy`），离线可跑、隐私友好
- **跨会话同步**：配合每日 `sync.py all` 定时任务，任何新任务/新对话的记忆当晚自动汇流进中枢
- **会话级增量**：`sync.py incremental --text` 可在每次新建任务/对话结束时实时追加，不重复灌入历史数据
- **Skill 化**：已封装为 WorkBuddy / Trae Skill，本地 SkillHub（~/.workbuddy/skills/ 或 ~/.trae-cn/skills/）已安装，并通过 ClawHub 外部发布

## 🚀 快速开始

```bash
# 1. 准备环境（Windows 用 Scripts/python.exe）
python -m venv venv
venv/Scripts/python.exe -m pip install numpy

# 2. 编辑 scripts/config.json，把 paths.sources 指向你的真实记忆源
#    memory_md / workspace_logs / archive_readme / trae_memory / knowledge / index_html

# 3. 运行整条流水线（reset→seed→distill→rebuild，幂等）
venv/Scripts/python.exe scripts/sync.py all
```

开箱示例：仓库自带 `scripts/knowledge.json`（海马体 5 区 + auto 区示例），不改任何配置直接 `python scripts/sync.py all` 即可生成 `index.html` 验证引擎可用。

## 🔄 自动迭代

| 场景 | 命令 | 说明 |
|------|------|------|
| 每日汇总 | `python sync.py all` | 清空 L3/L2，从所有静态源重新 consolidate，推荐配置定时任务 |
| 新建任务/对话结束 | `python sync.py incremental --text "本次核心结论..."` | 不重置引擎，追加本轮内容并刷新可视化/Obsidian |
| 单条记录 | `python sync.py ingest --text "关键事实" --type semantic --importance 0.8` | 直接写入一条记忆 |
| 只刷新可视化 | `python sync.py rebuild` | 依据当前 knowledge.json 重建 index.html |
| 只导出 Obsidian | `python sync.py obsidian` | 重新生成 Obsidian Vault 内容 |

## 📁 结构

```
hippocampus-memory-engine/
├── SKILL.md                       # Skill 说明（WorkBuddy/Trae 触发用）
├── _meta.json                     # Skill 元数据（ClawHub 发布用；本地 SkillHub 目录直接复制即可使用）
├── README.md                      # 本文件
├── docs/                          # 可视化站点（GitHub Pages 源）
│   ├── index.html                 # 海马体 SVG 可视化
│   ├── flow.html                  # 流动知识图谱
│   ├── flowsite/                  # 独立可部署站点
│   └── knowledge.json             # 真实知识库（示例请用 scripts/knowledge.json）
├── references/
│   ├── DESIGN.md                  # 海马体记忆架构设计
│   └── sync-automation.md         # 每日自动同步定时任务配置
└── scripts/
    ├── config.json                # 用户 ID、阈值、路径配置
    ├── embed.py                   # TfidfEmbedder（中文分词 + TF-IDF）
    ├── vectors.py                 # VectorStore（.npy 持久化 + 余弦检索）
    ├── db.py                      # SQLite L3
    ├── engine.py                  # HippocampusEngine（双写/检索/蒸馏）
    ├── sync.py                    # 入口 seed/distill/rebuild/incremental/ingest/all
    ├── build_index.py             # 海马体 SVG 可视化生成
    ├── build_flow.py              # 流动知识图谱生成
    ├── graph_builder.py           # 知识图谱构建
    ├── export_obsidian.py         # Obsidian Vault 导出
    └── knowledge.json             # 示例知识库
```

## 🔧 作为 Skill 使用

本仓库即一个标准 WorkBuddy / Trae Skill。安装方式：

**WorkBuddy**
1. 把整个 `hippocampus-memory-engine/` 目录放入 `~/.workbuddy/skills/`（用户级，跨项目可用），或放入项目 `.workbuddy/skills/`（项目级共享）。
2. 重启/刷新 WorkBuddy，即可通过自然语言触发（如"帮我搭建一个海马体记忆中枢"）。

**Trae**
1. 把 `SKILL.md` + `_meta.json` 放入 `~/.trae-cn/skills/hippocampus-memory-engine/`。
2. 重启 Trae 后即可通过自然语言触发（如"更新海马体知识库"）。

**ClawHub（外部安装）**
```bash
npx clawhub@latest skill install hippocampus-memory-engine
```

**SkillHub（官方市场）**
```text
请根据 https://skillhub.cn/install/skillhub.md，安装 hippocampus-memory-engine。
```
已发布页面：https://skillhub.cn/skills/user_053d27d0/hippocampus-memory-engine

**本地目录（备用）**
1. Trae: 复制本仓库到 `~/.trae-cn/skills/hippocampus-memory-engine/`
2. WorkBuddy: 复制本仓库到 `~/.workbuddy/skills/hippocampus-memory-engine/`
3. 重启后可通过自然语言触发。

## 🧪 检索示例

```python
from engine import HippocampusEngine
eng = HippocampusEngine("scripts/config.json")
hits = eng.retrieve("链主申报书 附件3 合并 Excel", top_k=3, threshold=0.05)
for h in hits:
    print(h["sim"], h["source"], h["content"][:50])
```

## 📜 License

MIT
