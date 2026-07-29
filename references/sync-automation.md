# 自动同步：让任何新会话的记忆汇入中枢

## 目标

用户要求："无论是开一个新的任务，还是新的对话，它都可以同步更新到这里面来。"

WorkBuddy 每个会话本就会写入两个地方：
- **工作区每日日志** `工作区/.workbuddy/memory/YYYY-MM-DD.md`
- **账号级记忆** `~/.workbuddy/MEMORY.md`

因此只需一个**定时 consolidate 任务**每天跑一次 `sync.py all`，即可把当天所有会话产生的记忆自动汇流进中枢（L3 + L2 + knowledge.json `auto` 区 + `index.html`）。

## 定时任务配置（WorkBuddy automation）

在 WorkBuddy 中创建一个每日定时任务（示例每天 23:00）：

- **名称**：海马体记忆流自动同步
- **调度**：`FREQ=DAILY;BYHOUR=23;BYMINUTE=0`
- **状态**：ACTIVE
- **提示词（prompt）核心**：

```
切换目录到 <引擎工作目录>
用托管 Python 运行：sync.py all
（best-effort）把刷新后的 index.html 重推到乐享 entry（force_write=true）
完成后报告：total_memories / vector_dim / 蒸馏条数 / 乐享同步是否成功
不要修改任何静态源文件内容，只运行 sync.py。
```

## 幂等保证

`sync.py all` 内部先 `eng.reset()`（清空 L3 `memory.db` 与 L2 `vectors`）再 `seed()` 重灌，配合 `embedder.fit(corpus)` 在灌入前建好词表 → 可每天重复运行而**不累积重复**。

## 扩展：即时写入（可选）

若希望会话结束立即写入而非等每晚，可在会话收尾时直接调用：

```python
from engine import HippocampusEngine
eng = HippocampusEngine("config.json")
eng.add_memory("本会话学到：xxx", memory_type="episodic", source="agent", importance=0.6)
```

或在 automation 之外加一个更密集的调度（如每小时 `sync.py distill` + `rebuild`）做轻量刷新。
