# DeepFinance API 设计文档

## 概述

DeepFinance 的 Web API 设计，用于连接前端 UI 和现有的 Python 后端流水线。

**技术栈**：
- **后端框架**：FastAPI 3.0+
- **WebSocket**：用于流水线进度推送
- **数据验证**：Pydantic（复用现有模型）
- **文件存储**：本地文件系统（outputs/ 目录）

---

## 架构设计

### 服务层次

```
前端（React）
    ↓ HTTP/WebSocket
FastAPI 服务层（新增）
    ↓ Python API
现有流水线（ReportPipeline）
```

### 目录结构（新增）

```
DeepFinance/
├── src/
│   ├── api/                    # 新增：API 层
│   │   ├── __init__.py
│   │   ├── main.py            # FastAPI 应用入口
│   │   ├── routes/            # 路由模块
│   │   │   ├── __init__.py
│   │   │   ├── projects.py    # 项目管理
│   │   │   ├── reports.py     # 报告生成
│   │   │   ├── citations.py   # 引用查询
│   │   │   └── files.py       # 文件服务
│   │   ├── schemas/           # API 数据模型
│   │   │   ├── __init__.py
│   │   │   ├── project.py
│   │   │   ├── report.py
│   │   │   └── citation.py
│   │   ├── services/          # 业务逻辑
│   │   │   ├── __init__.py
│   │   │   ├── project_service.py
│   │   │   └── pipeline_service.py
│   │   ├── websocket/         # WebSocket 处理
│   │   │   ├── __init__.py
│   │   │   └── progress.py
│   │   └── middleware/        # 中间件
│   │       ├── __init__.py
│   │       └── cors.py
│   └── ...
```

---

## API 端点设计

### 1. 项目管理 API

#### 1.1 创建新项目

```http
POST /api/projects
Content-Type: multipart/form-data

# Request Body
{
  "file": <PDF文件>,
  "user_query": "重点分析利润率变化"  # 可选
  "mode": "full"  # full/no-research/minimal
}

# Response 200
{
  "project_id": "proj_20260109_143022",
  "status": "processing",
  "created_at": "2026-01-09T14:30:22Z",
  "websocket_url": "ws://localhost:8000/ws/projects/proj_20260109_143022"
}
```

**实现**：
```python
# src/api/routes/projects.py

@router.post("/projects")
async def create_project(
    file: UploadFile,
    user_query: str | None = Form(None),
    mode: str = Form("full"),
    background_tasks: BackgroundTasks
):
    # 1. 保存上传的文件
    project_id = f"proj_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    pdf_path = await save_upload_file(file, project_id)

    # 2. 后台启动流水线
    background_tasks.add_task(
        run_pipeline_with_progress,
        project_id=project_id,
        pdf_path=pdf_path,
        user_query=user_query,
        mode=mode
    )

    # 3. 返回项目信息
    return {
        "project_id": project_id,
        "status": "processing",
        "created_at": datetime.now(),
        "websocket_url": f"ws://localhost:8000/ws/projects/{project_id}"
    }
```

---

#### 1.2 获取项目列表

```http
GET /api/projects?limit=20&offset=0

# Response 200
{
  "total": 42,
  "items": [
    {
      "project_id": "proj_20260109_143022",
      "title": "Tesla Q3 2025 Earnings Report",
      "status": "completed",  # processing/completed/failed
      "created_at": "2026-01-09T14:30:22Z",
      "updated_at": "2026-01-09T14:35:10Z",
      "metadata": {
        "company": "Tesla",
        "period": "Q3 2025",
        "document_type": "earnings_report"
      }
    }
  ]
}
```

---

#### 1.3 获取项目详情

```http
GET /api/projects/{project_id}

# Response 200
{
  "project_id": "proj_20260109_143022",
  "title": "Tesla Q3 2025 Earnings Report",
  "status": "completed",
  "created_at": "2026-01-09T14:30:22Z",
  "updated_at": "2026-01-09T14:35:10Z",

  # 流水线进度
  "pipeline": {
    "current_stage": "completed",
    "stages": [
      {
        "name": "parsing",
        "status": "completed",
        "started_at": "2026-01-09T14:30:25Z",
        "completed_at": "2026-01-09T14:32:01Z",
        "duration": 96.3,
        "details": {
          "pages_extracted": 42,
          "figures_count": 17,
          "tables_count": 8
        }
      },
      {
        "name": "analysis",
        "status": "completed",
        "started_at": "2026-01-09T14:32:02Z",
        "completed_at": "2026-01-09T14:33:15Z",
        "duration": 73.2,
        "details": {
          "sections_completed": 8,
          "total_sections": 8,
          "metrics_extracted": 25
        }
      },
      {
        "name": "research",
        "status": "completed",
        "started_at": "2026-01-09T14:33:16Z",
        "completed_at": "2026-01-09T14:34:05Z",
        "duration": 49.1,
        "details": {
          "queries_executed": 13,
          "results_found": 48
        }
      },
      {
        "name": "generation",
        "status": "completed",
        "started_at": "2026-01-09T14:34:06Z",
        "completed_at": "2026-01-09T14:35:10Z",
        "duration": 64.5
      }
    ]
  },

  # 文档元数据
  "metadata": {
    "company": "Tesla",
    "period": "Q3 2025",
    "document_type": "earnings_report",
    "publish_date": "2025-10-22"
  },

  # 生成的文件
  "artifacts": {
    "report_md": "/api/projects/proj_20260109_143022/files/report.md",
    "report_html": "/api/projects/proj_20260109_143022/files/report.html",
    "analysis_json": "/api/projects/proj_20260109_143022/files/01_analysis.json",
    "research_json": "/api/projects/proj_20260109_143022/files/02_research.json"
  }
}
```

---

#### 1.4 删除项目

```http
DELETE /api/projects/{project_id}

# Response 204 No Content
```

---

### 2. 报告查看 API

#### 2.1 获取报告内容

```http
GET /api/projects/{project_id}/report?format=markdown

# Query Parameters
# - format: markdown/html/json (默认 markdown)

# Response 200
{
  "content": "## 执行摘要\n\nTesla Q3 2025...",
  "format": "markdown",
  "metadata": {
    "title": "Tesla Q3 2025 Earnings Analysis",
    "generated_at": "2026-01-09T14:35:10Z",
    "model": "claude-sonnet-4-5-20250929"
  }
}
```

---

#### 2.2 获取分析结果

```http
GET /api/projects/{project_id}/analysis

# Response 200
{
  "analysis_id": "analysis_20260109_143315",
  "document_metadata": {
    "document_type": "earnings_report",
    "company": "Tesla",
    "period": "Q3 2025"
  },
  "content_summary": [
    {
      "section_id": "financial_performance",
      "section_title": "Financial Performance",
      "content": "...",
      "key_metrics": [...],
      "insights": [...]
    }
  ],
  "key_takeaways": [...],
  "supplementary_research_needs": {...},
  "charts_analysis": [...]
}
```

---

### 3. 引用查询 API

#### 3.1 获取引用详情

```http
GET /api/projects/{project_id}/citations/{citation_id}

# 示例请求
GET /api/projects/proj_20260109_143022/citations/doc-p5

# Response 200 - 文档引用
{
  "type": "document",
  "id": "doc-p5",
  "location": "page-5",
  "source": "page-5#table-2"
}

# Response 200 - 图表引用
{
  "type": "chart",
  "figure_id": "p10_fig_004.png",
  "figure_path": "images/p10_fig_004.png",
  "figure_url": "/api/projects/proj_20260109_143022/files/source/images/p10_fig_004.png",
  "figure_analysis": {
    "type": "chart",
    "title": "Revenue Trend",
    "analysis": {
      "图表构成": "柱状图 + 折线图",
      "数据关系": "收入与利润率对比",
      "核心洞察": "利润率持续下降"
    }
  }
}

# Response 200 - 外部引用
{
  "type": "web",
  "title": "Tesla Q4 2025 Production Outlook",
  "url": "https://example.com/article",
  "content": "According to recent reports...",
  "published_date": "2025-12-15",
  "relevance_score": 0.95
}
```

**实现**：
```python
# src/api/routes/citations.py

@router.get("/projects/{project_id}/citations/{citation_id}")
async def get_citation(project_id: str, citation_id: str):
    project_dir = Path(f"outputs/{project_id}")

    # 文档引用
    if citation_id.startswith("doc-"):
        page = citation_id.replace("doc-p", "")
        return {
            "type": "document",
            "id": citation_id,
            "location": f"page-{page}",
            "source": f"page-{page}"
        }

    # 图表引用
    elif citation_id.startswith("fig_") or ".png" in citation_id:
        metadata = load_json(project_dir / "source" / "metadata.json")
        for fig in metadata.get("figures", []):
            if citation_id in fig["path"]:
                return {
                    "type": "chart",
                    "figure_id": Path(fig["path"]).name,
                    "figure_path": fig["path"],
                    "figure_url": f"/api/projects/{project_id}/files/source/{fig['path']}",
                    "figure_analysis": fig.get("analysis")
                }
        raise HTTPException(404, "图表未找到")

    # 外部引用
    elif citation_id.startswith("gap-"):
        research = load_json(project_dir / "02_research.json")
        parts = citation_id.split("-")
        gap_id = f"{parts[0]}-{parts[1]}"
        result_index = int(parts[2]) if len(parts) > 2 else 0

        for query in research["queries"]:
            if query["source_gap"] == gap_id:
                result = query["results"][result_index]
                return {
                    "type": "web",
                    "title": result["title"],
                    "url": result["url"],
                    "content": result["content"][:500],
                    "published_date": result.get("published_date"),
                    "relevance_score": result.get("relevance_score")
                }
        raise HTTPException(404, "外部引用未找到")

    raise HTTPException(400, "无效的引用ID格式")
```

---

### 4. 文件服务 API

#### 4.1 获取文件

```http
GET /api/projects/{project_id}/files/{file_path}

# 示例
GET /api/projects/proj_20260109_143022/files/source/images/p10_fig_004.png
GET /api/projects/proj_20260109_143022/files/report.md
GET /api/projects/proj_20260109_143022/files/01_analysis.json
```

**实现**：
```python
# src/api/routes/files.py

@router.get("/projects/{project_id}/files/{file_path:path}")
async def get_file(project_id: str, file_path: str):
    """静态文件服务"""
    file = Path(f"outputs/{project_id}/{file_path}")

    if not file.exists():
        raise HTTPException(404, "文件不存在")

    return FileResponse(file)
```

---

### 5. WebSocket 进度推送

#### 5.1 连接 WebSocket

```javascript
// 前端连接示例
const ws = new WebSocket(`ws://localhost:8000/ws/projects/${projectId}`);

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data);
};
```

#### 5.2 消息格式

**解析阶段**：
```json
{
  "stage": "parsing",
  "status": "in_progress",
  "progress": 0.45,
  "message": "正在提取文档内容...",
  "details": {
    "pages_extracted": 19,
    "total_pages": 42
  },
  "timestamp": "2026-01-09T14:30:45Z"
}
```

**分析阶段**：
```json
{
  "stage": "analysis",
  "status": "in_progress",
  "progress": 0.625,
  "message": "正在分析财务指标...",
  "details": {
    "sections_completed": 5,
    "total_sections": 8,
    "current_section": "financial_performance"
  },
  "timestamp": "2026-01-09T14:32:30Z"
}
```

**研究阶段**：
```json
{
  "stage": "research",
  "status": "in_progress",
  "progress": 0.77,
  "message": "正在搜索补充数据...",
  "details": {
    "queries_completed": 10,
    "total_queries": 13,
    "current_query": "Tesla Q4 2025 production guidance"
  },
  "timestamp": "2026-01-09T14:33:45Z"
}
```

**完成**：
```json
{
  "stage": "generation",
  "status": "completed",
  "progress": 1.0,
  "message": "报告生成完成",
  "details": {
    "report_url": "/api/projects/proj_20260109_143022/report"
  },
  "timestamp": "2026-01-09T14:35:10Z"
}
```

**错误**：
```json
{
  "stage": "analysis",
  "status": "failed",
  "progress": 0.4,
  "message": "分析失败",
  "error": {
    "code": "LLM_API_ERROR",
    "message": "Gemini API rate limit exceeded",
    "details": "请稍后重试"
  },
  "timestamp": "2026-01-09T14:32:30Z"
}
```

---

#### 5.3 WebSocket 实现

```python
# src/api/websocket/progress.py

from fastapi import WebSocket
from typing import Dict
import asyncio

class ProgressBroadcaster:
    """进度广播器"""

    def __init__(self):
        self.connections: Dict[str, list[WebSocket]] = {}

    async def connect(self, project_id: str, websocket: WebSocket):
        """建立连接"""
        await websocket.accept()
        if project_id not in self.connections:
            self.connections[project_id] = []
        self.connections[project_id].append(websocket)

    def disconnect(self, project_id: str, websocket: WebSocket):
        """断开连接"""
        if project_id in self.connections:
            self.connections[project_id].remove(websocket)

    async def broadcast(self, project_id: str, message: dict):
        """广播消息到所有连接"""
        if project_id in self.connections:
            for ws in self.connections[project_id]:
                try:
                    await ws.send_json(message)
                except Exception:
                    self.disconnect(project_id, ws)

# 全局实例
broadcaster = ProgressBroadcaster()


# WebSocket 路由
@app.websocket("/ws/projects/{project_id}")
async def websocket_endpoint(websocket: WebSocket, project_id: str):
    await broadcaster.connect(project_id, websocket)
    try:
        while True:
            # 保持连接
            await websocket.receive_text()
    except Exception:
        broadcaster.disconnect(project_id, websocket)
```

---

#### 5.4 流水线集成

```python
# src/api/services/pipeline_service.py

from src.api.websocket.progress import broadcaster

async def run_pipeline_with_progress(
    project_id: str,
    pdf_path: Path,
    user_query: str | None,
    mode: str
):
    """运行流水线并推送进度"""

    try:
        # 1. 解析阶段
        await broadcaster.broadcast(project_id, {
            "stage": "parsing",
            "status": "in_progress",
            "progress": 0.0,
            "message": "开始解析PDF文档..."
        })

        # 运行解析器（需要修改为支持进度回调）
        parser = DoclingParser()
        result = await parser.execute(
            pdf_path=pdf_path,
            progress_callback=lambda p: asyncio.create_task(
                broadcaster.broadcast(project_id, {
                    "stage": "parsing",
                    "status": "in_progress",
                    "progress": p,
                    "message": "正在提取文档内容..."
                })
            )
        )

        # 2. 分析阶段
        await broadcaster.broadcast(project_id, {
            "stage": "analysis",
            "status": "in_progress",
            "progress": 0.0,
            "message": "开始分析文档..."
        })

        # ... 类似地处理其他阶段

        # 完成
        await broadcaster.broadcast(project_id, {
            "stage": "generation",
            "status": "completed",
            "progress": 1.0,
            "message": "报告生成完成",
            "details": {
                "report_url": f"/api/projects/{project_id}/report"
            }
        })

    except Exception as e:
        # 错误处理
        await broadcaster.broadcast(project_id, {
            "stage": "error",
            "status": "failed",
            "message": str(e),
            "error": {
                "code": "PIPELINE_ERROR",
                "message": str(e)
            }
        })
```

---

## 数据模型（API Schemas）

### ProjectCreate

```python
# src/api/schemas/project.py

from pydantic import BaseModel, Field

class ProjectCreate(BaseModel):
    """创建项目请求"""
    user_query: str | None = Field(None, description="用户侧重点")
    mode: str = Field("full", description="运行模式：full/no-research/minimal")

class ProjectResponse(BaseModel):
    """项目响应"""
    project_id: str
    status: str  # processing/completed/failed
    created_at: str
    updated_at: str
    title: str | None = None
    metadata: dict | None = None

class ProjectDetail(ProjectResponse):
    """项目详情"""
    pipeline: dict
    artifacts: dict
```

### CitationResponse

```python
# src/api/schemas/citation.py

class CitationResponse(BaseModel):
    """引用响应"""
    type: str  # document/chart/web
    id: str | None = None
    location: str | None = None
    source: str | None = None

    # 图表引用
    figure_id: str | None = None
    figure_path: str | None = None
    figure_url: str | None = None
    figure_analysis: dict | None = None

    # 外部引用
    title: str | None = None
    url: str | None = None
    content: str | None = None
```

---

## 错误处理

### 标准错误响应

```json
{
  "detail": {
    "code": "PROJECT_NOT_FOUND",
    "message": "项目不存在",
    "timestamp": "2026-01-09T14:35:10Z"
  }
}
```

### 错误码

| 错误码 | HTTP状态码 | 说明 |
|-------|-----------|------|
| `PROJECT_NOT_FOUND` | 404 | 项目不存在 |
| `CITATION_NOT_FOUND` | 404 | 引用不存在 |
| `FILE_NOT_FOUND` | 404 | 文件不存在 |
| `INVALID_FILE_FORMAT` | 400 | 无效的文件格式 |
| `FILE_TOO_LARGE` | 413 | 文件过大 |
| `PIPELINE_ERROR` | 500 | 流水线运行错误 |
| `LLM_API_ERROR` | 502 | LLM API 错误 |

---

## 安全性

### CORS 配置

```python
# src/api/middleware/cors.py

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # 前端地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 文件上传限制

```python
# src/api/main.py

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1"]
)

# 文件大小限制
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
```

---

## 性能优化

### 1. 文件缓存

使用 ETag 和 Last-Modified 头优化图片/文件响应。

### 2. 异步处理

所有流水线操作均通过后台任务异步执行，避免阻塞 API 响应。

### 3. 分页

项目列表使用 limit/offset 分页，默认 20 条/页。

---

## 部署

### 开发环境

```bash
# 启动 API 服务器
uv run uvicorn src.api.main:app --reload --port 8000
```

### 生产环境

```bash
# 使用 Gunicorn + Uvicorn workers
gunicorn src.api.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

---

## 依赖更新

需要在 `pyproject.toml` 中添加：

```toml
[project.dependencies]
# 现有依赖...
fastapi = ">=0.115.0"
uvicorn = {extras = ["standard"], version = ">=0.32.0"}
python-multipart = ">=0.0.20"  # 文件上传
websockets = ">=14.0"
```
