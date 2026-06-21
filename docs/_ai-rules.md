# AI Writing Rules

> This file is the "constitution" for AI writing/editing any document.
> **Must read this file before writing any document**.

---

## Documentation System Structure

```
docs/
├── _ai-rules.md          # This file (required reading)
├── _scripts/             # Maintenance scripts
│   └── new.sh            # Add new document
├── _templates/           # Document templates
├── decisions/            # ADR (Architecture Decision Records)
└── features/             # Feature documentation
    ├── _archived/        # Archived
    └── <name>/           # One directory per feature
        ├── spec.md       # Feature specification (stable, long-term retention)
        ├── state.md      # Progress snapshot (replacement updates, delete after completion)
        └── log.md        # Process log (incremental append, simplify or delete after completion)
```

### Adding New Documents (Script Required)

```bash
./docs/_scripts/new.sh feat <name>      # Add new feature (required)
./docs/_scripts/new.sh adr <name>       # Add new ADR (required)
```

> ⚠️ **Manual creation prohibited** for spec.md/state.md/log.md. Scripts ensure structural integrity.

---

## Core Principle: High Signal-to-Noise Ratio

### Three Self-Check Questions

Before writing any content, ask:

1. **"Is this world knowledge?"** → AI already knows it → **Don't write**
2. **"Will this be referenced in 3 months?"** → Uncertain → **Consider if necessary**
3. **"What's lost by removing it?"** → Only "looks nice" → **Delete**

### Prohibited Content

- Language tutorials, HTTP basics, SQL basics
- Empty phrases like "In modern software development..."
- Long paraphrases of official documentation
- Information obvious from code

### Required Content

- Project-specific constraints and rules
- Pitfalls encountered and workarounds
- Rationale for key decisions
- Non-obvious configurations

---

## Length Limits

| Type | Token Limit | Overflow Handling |
|------|-------------|-------------------|
| CLAUDE.md | ~1000 | Split into docs/ |
| spec.md | ~800 | Split by sub-feature |
| state.md | ~500 | Condense content |
| *.adr.md | ~1200 | One decision per file |

**When exceeding limit**: Propose split plan → Wait for confirmation → Execute. Do not continue appending.

---

## Document Lifecycle

### features/\<name\>/spec.md
| Timing | Trigger Condition |
|--------|-------------------|
| Create | `./docs/_scripts/new.sh feat <name>` |
| Update | When feature specification changes |
| Archive | Move entire directory to `_archived/` when feature is deprecated |

### features/\<name\>/state.md
| Timing | Trigger Condition |
|--------|-------------------|
| Create | Created together with spec.md |
| Update | On substantial progress (**replacement-style**) |
| Delete | **Delete after feature completion** |

### features/\<name\>/log.md
| Timing | Trigger Condition |
|--------|-------------------|
| Create | Created together with spec.md |
| Update | Record key events during process (**incremental append**) |
| Delete | After feature completion, distill key learnings into spec.md's Learned section, then delete |

### decisions/*.adr.md
| Timing | Trigger Condition |
|--------|-------------------|
| Create | `./docs/_scripts/new.sh adr <name>` |
| Update | Status changes: Proposed → Accepted → Deprecated |
| Archive | Do not delete, only mark status |

---

## Three-File Update Principles

| File | Update Method | Description |
|------|---------------|-------------|
| spec.md | On specification changes | Stable layer |
| state.md | **Replacement-style** | Rewrite each section to current state |
| log.md | **Incremental append** | Record key events chronologically |

**state.md replacement-style example**:
```markdown
## Status
- API completed, frontend integration in progress
- Main blocker: authentication issue
```

**log.md incremental-style example**:
```markdown
## 2025-12-07
### 14:00 - Completed API
- Implemented /api/auth endpoint
- Discovered JWT expiration issue, switched to refresh token

### 16:00 - New entry (append here, do not modify above content)
- ...
```

> ⚠️ **log.md append-only**: Existing entries must not be edited, only append new entries at the end

---

## Multi-Agent Collaboration (Flat Structure)

When tasks need to be split to sub-agents, use **naming conventions** instead of nested directories:

```bash
./docs/_scripts/new.sh feat auth        # Main task
./docs/_scripts/new.sh feat auth.api    # Subtask
./docs/_scripts/new.sh feat auth.test   # Subtask
```

Structure example:
```
features/
├── auth/              # Main agent workspace
│   ├── spec.md
│   ├── state.md       # Contains Subtasks section
│   └── log.md
├── auth.api/          # Sub-agent workspace (same structure)
│   ├── spec.md        # Add Parent: [[auth]]
│   ├── state.md
│   └── log.md
└── auth.test/
    └── ...
```

### Association Method

**Sub-task spec.md header**:
```markdown
**Parent**: [[auth]]
```

**Main task state.md**:
```markdown
## Subtasks
| Subtask | Status |
|---------|--------|
| [[auth.api]] | done |
| [[auth.test]] | in_progress |
```

> **Advantage**: Main/sub agent workspace structures are identical, no additional concepts.

---

## Handoff to New Window

When a new AI window takes over:

1. Read `CLAUDE.md` to understand the project
2. Read `docs/_ai-rules.md` to understand writing rules
3. Check `docs/features/` to find in-progress features
4. Read `spec.md` to understand feature specification
5. Read `state.md` to understand current progress
6. If necessary, read `log.md` to understand process (optional)
7. Propose next steps based on Tasks
8. **Wait for confirmation before executing**

---

## DeepFinance-Specific Rules

### Tool Development Standards

```python
# src/tools/base.py defines the Tool base class
class Tool:
    name: str           # Tool name (unique)
    description: str    # Tool description (for LLM selection)
    parameters: dict    # JSON Schema parameter definition

    def execute(self, **kwargs) -> ToolResult:
        """Execute tool, return structured result"""
        pass
```

**Must comply**:
- Each tool returns `ToolResult`, containing `success`, `data`, `source` (source information)
- All external data must carry source URL/API identifier
- Tools placed by category: `financial/`, `web/`, `parser/`

### Agent State Definitions

```python
# src/memory/research.py
class ResearchState(TypedDict):
    task: dict              # Task description
    source_docs: List[str]  # Parsed source documents
    research_data: List[dict]  # Collected data (with sources)
    report_sections: List[str]
    sources: List[str]      # Reference source list
```

**State update principles**:
- Research phase can update `research_data` multiple times (dynamic backtracking)
- Writing phase must update `sources` with each output

### Citation Format

All data citations in reports use unified format:

```markdown
According to Tesla Q3 2025 earnings report[^1], revenue reached...

[^1]: Tesla Q3 2025 Update, https://ir.tesla.com/...
```

### Prohibited Actions

- Generating data points without sources
- Skipping Reviewer during Writer phase
- Directly outputting unverified scraper results
