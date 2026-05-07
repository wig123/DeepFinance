# AI 写作规则

> 本文件是 AI 写/改任何文档的「宪法」。
> **写任何文档前必读本文件**。

---

## 文档体系结构

```
docs/
├── _ai-rules.md          # 本文件（必读）
├── _scripts/             # 维护脚本
│   └── new.sh            # 新增文档
├── _templates/           # 文档模板
├── decisions/            # ADR（架构决策）
└── features/             # 功能文档
    ├── _archived/        # 已归档
    └── <name>/           # 每个功能一个目录
        ├── spec.md       # 功能规格（稳定，长期保留）
        ├── state.md      # 进度快照（替换更新，完成后删除）
        └── log.md        # 过程日志（增量追加，完成后精简或删除）
```

### 新增文档（强制使用脚本）

```bash
./docs/_scripts/new.sh feat <name>      # 新增功能（必须）
./docs/_scripts/new.sh adr <name>       # 新增 ADR（必须）
```

> ⚠️ **禁止手动创建** spec.md/state.md/log.md。脚本确保结构完整。

---

## 核心原则：高信噪比

### 三个自检问题

写任何内容前问：

1. **「这是世界知识吗？」** → AI 本来就知道 → **不写**
2. **「3个月后会被查吗？」** → 不确定 → **考虑是否必要**
3. **「去掉它损失什么？」** → 只损失"好看" → **删**

### 禁止内容

- 语言教程、HTTP 基础、SQL 基础
- "在现代软件开发中……" 等空话
- 大段复述官方文档
- 代码中一眼可见的信息

### 必须内容

- 项目特有的约束和规则
- 踩过的坑和绕法
- 关键决策的 rationale
- 非显而易见的配置

---

## 长度上限

| 类型 | Token上限 | 超限处理 |
|------|----------|---------|
| CLAUDE.md | ~1000 | 拆分到 docs/ |
| spec.md | ~800 | 按子功能拆分 |
| state.md | ~500 | 精简内容 |
| *.adr.md | ~1200 | 一文一决策 |

**超限时**：提出拆分方案 → 等待确认 → 执行。禁止继续追加。

---

## 文档生命周期

### features/\<name\>/spec.md
| 时机 | 触发条件 |
|------|---------|
| 创建 | `./docs/_scripts/new.sh feat <name>` |
| 更新 | 功能规格变化时 |
| 归档 | 功能废弃时整个目录移至 `_archived/` |

### features/\<name\>/state.md
| 时机 | 触发条件 |
|------|---------|
| 创建 | 同 spec.md 一起创建 |
| 更新 | 每次有实质进展时（**替换式**） |
| 删除 | **功能完成后删除** |

### features/\<name\>/log.md
| 时机 | 触发条件 |
|------|---------|
| 创建 | 同 spec.md 一起创建 |
| 更新 | 过程中记录关键事件（**增量追加**） |
| 删除 | 功能完成后，提炼关键经验到 spec.md 的 Learned，然后删除 |

### decisions/*.adr.md
| 时机 | 触发条件 |
|------|---------|
| 创建 | `./docs/_scripts/new.sh adr <name>` |
| 更新 | 状态变化：Proposed → Accepted → Deprecated |
| 归档 | 不删除，只标记状态 |

---

## 三文件更新原则

| 文件 | 更新方式 | 说明 |
|------|---------|------|
| spec.md | 规格变化时 | 稳定层 |
| state.md | **替换式** | 重写各 section 为当前状态 |
| log.md | **增量追加** | 按时间记录关键事件 |

**state.md 替换式示例**：
```markdown
## Status
- API 已完成，前端对接中
- 主要阻塞：认证问题
```

**log.md 增量式示例**：
```markdown
## 2025-12-07
### 14:00 - 完成 API
- 实现了 /api/auth 端点
- 发现 JWT 过期问题，改用 refresh token

### 16:00 - 新增条目（追加在这里，不修改上面的内容）
- ...
```

> ⚠️ **log.md 只追加不修改**：已有条目禁止编辑，只能在末尾追加新条目

---

## 多 Agent 协作（扁平结构）

任务需要拆分给子 agent 时，使用**命名约定**而非嵌套目录：

```bash
./docs/_scripts/new.sh feat auth        # 主任务
./docs/_scripts/new.sh feat auth.api    # 子任务
./docs/_scripts/new.sh feat auth.test   # 子任务
```

结构示例：
```
features/
├── auth/              # 主 agent 工作区
│   ├── spec.md
│   ├── state.md       # 包含 Subtasks section
│   └── log.md
├── auth.api/          # 子 agent 工作区（结构相同）
│   ├── spec.md        # 添加 Parent: [[auth]]
│   ├── state.md
│   └── log.md
└── auth.test/
    └── ...
```

### 关联方式

**子任务 spec.md 头部**：
```markdown
**Parent**: [[auth]]
```

**主任务 state.md**：
```markdown
## Subtasks
| 子任务 | 状态 |
|--------|------|
| [[auth.api]] | done |
| [[auth.test]] | in_progress |
```

> **优势**：主/子 agent 工作区结构完全相同，无额外概念。

---

## 换窗口接盘

新 AI 窗口接盘时：

1. 读 `CLAUDE.md` 了解项目
2. 读 `docs/_ai-rules.md` 了解写作规则
3. 查 `docs/features/` 找进行中的功能
4. 读 `spec.md` 了解功能规格
5. 读 `state.md` 了解当前进度
6. 必要时读 `log.md` 了解过程（可选）
7. 根据 Tasks 提议下一步
8. **等确认后执行**

---

## DeepFinance 特有规则

### 工具开发规范

```python
# src/tools/base.py 定义了 Tool 基类
class Tool:
    name: str           # 工具名称（唯一）
    description: str    # 工具描述（供 LLM 选择）
    parameters: dict    # JSON Schema 参数定义

    def execute(self, **kwargs) -> ToolResult:
        """执行工具，返回结构化结果"""
        pass
```

**必须遵守**：
- 每个工具返回 `ToolResult`，包含 `success`, `data`, `source`（来源信息）
- 所有外部数据必须携带来源 URL/API 标识
- 工具按 category 放置：`financial/`, `web/`, `parser/`

### Agent 状态定义

```python
# src/memory/research.py
class ResearchState(TypedDict):
    task: dict              # 任务描述
    source_docs: List[str]  # 解析后的源文档
    research_data: List[dict]  # 采集的数据（含来源）
    report_sections: List[str]
    sources: List[str]      # 引用来源列表
```

**状态更新原则**：
- 研究阶段可多次更新 `research_data`（动态回溯）
- 写作阶段每次输出必须更新 `sources`

### 引用格式

报告中所有数据引用使用统一格式：

```markdown
根据 Tesla Q3 2025 财报[^1]，营收达到...

[^1]: Tesla Q3 2025 Update, https://ir.tesla.com/...
```

### 禁止事项

- 禁止生成无来源的数据点
- 禁止在 Writer 阶段跳过 Reviewer
- 禁止直接输出未验证的爬虫结果
