# 海马体记忆架构设计

> 以海马体神经环路为隐喻的 Agent 外部记忆系统。LLM = 大脑皮层（无持久记忆），外部存储 = 海马体（长期记忆中枢）。

## 一、三类记忆（Memory Types）

| 类型 | 含义 | 引擎中的 source 示例 |
|---|---|---|
| 情景 Episodic | 何时何地发生了什么（会话日志、每日记录） | `log:2026-07-29.md`、`trae:session` |
| 语义 Semantic | 事实、偏好、身份、项目约定 | `MEMORY.md`、`knowledge:ec`、`trae:user_profile` |
| 程序 Procedural | 怎么做某事的流程/经验 | `trae:session`（学到的方法） |

## 二、三级存储（Three-Tier Storage）

| 层 | 介质 | 角色 | 生命周期 |
|---|---|---|---|
| L1 热 | 运行时内存 / 滑窗（window=20） | 当前上下文最直接可用的近因记忆 | 会话级，滑动淘汰 |
| L2 温 | 向量库（numpy `.npy`） | 余弦检索索引，引用 `mid` | 持久，随 L3 重建 |
| L3 冷 | SQLite（`memory.db`） | 事实源（source of truth） | 持久，唯一权威 |

**双写一致性**：写入时 `insert(L3)` + `store.add(L2)`，L2 只存向量与 `mid` 引用，避免两处内容漂移。

## 三、RAG 调度流程

```
感知 perceive → 回忆 recall → 筛选 filter → 注入 inject
     │              │              │              │
  新记忆入L3      query 向量化   余弦 top-k     命中文档拼进 prompt
                  L2 余弦检索     + 阈值/用户隔离
```

- **用户隔离**：`user_id` 字段，多用户场景按 `user_id` 过滤。
- **阈值护栏**：`similarity_threshold`（默认 0.10，中文稀疏 TF-IDF 可调到 0.03–0.05）。
- **衰减保留**：`importance_score` + `last_accessed_at`，蒸馏与召回时参与打分。

## 四、海马体分区映射（可视化）

| 脑区 | 记忆角色 | knowledge.json region id |
|---|---|---|
| 内嗅皮层 EC | 感知入口 / 编码 | `ec` |
| 齿状回 DG | 模式分离 / 去重 | `dg` |
| CA3 | 联想检索 / 召回 | `ca3` |
| CA1 | 整合 / 巩固 | `ca1` |
| 下托 Subiculum | 输出 / 导出 | `subiculum` |
| 自动沉淀 | 引擎蒸馏区 | `auto` |

## 五、生命周期

1. **编码**：新记忆经分词 → TF-IDF 向量 → 双写 L3+L2。
2. **巩固**：高频/高重要度记忆经 `distill` 进入 `knowledge.json` 的 `auto` 区，成为结构化知识。
3. **检索**：查询走 L2 余弦召回 → L3 取全文 → 注入上下文。
4. **衰减**：低重要度且长期未访问的记忆在蒸馏打分中自然下沉（不被选入 auto 区）。

## 六、为何用本地 TF-IDF 而非向量数据库

- **零模型下载**：numpy 即可，适合离线/隐私环境。
- **可解释**：词表可 inspect，相似度来源清晰。
- **足够用**：个人记忆规模（数百~数千条）下，TF-IDF 余弦召回质量可接受。
- 若需更强语义，可把 `embed.py` 的 `TfidfEmbedder` 替换为句向量模型，接口保持一致（`embed(text)->np.vector`）。
