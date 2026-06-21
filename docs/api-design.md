# DeepFinance API Design Document

## Overview

Web API design for DeepFinance, connecting the frontend UI with the existing Python backend pipeline.

**Tech Stack**:
- **Backend Framework**: FastAPI 3.0+
- **WebSocket**: For pipeline progress streaming
- **Data Validation**: Pydantic (reusing existing models)
- **File Storage**: Local filesystem (outputs/ directory)

---

## Architecture Design

### Service Layers

```
Frontend (React)
    ↓ HTTP/WebSocket
FastAPI Service Layer (New)
    ↓ Python API
Existing Pipeline (ReportPipeline)
```

### Directory Structure (New)

```
DeepFinance/
├── src/
│   ├── api/                    # New: API layer
│   │   ├── __init__.py
│   │   ├── main.py            # FastAPI application entry
│   │   ├── routes/            # Route modules
│   │   │   ├── __init__.py
│   │   │   ├── projects.py    # Project management
│   │   │   ├── reports.py     # Report generation
│   │   │   ├── citations.py   # Citation queries
│   │   │   └── files.py       # File service
│   │   ├── schemas/           # API data models
│   │   │   ├── __init__.py
│   │   │   ├── project.py
│   │   │   ├── report.py
│   │   │   └── citation.py
│   │   ├── services/          # Business logic
│   │   │   ├── __init__.py
│   │   │   ├── project_service.py
│   │   │   └── pipeline_service.py
│   │   ├── websocket/         # WebSocket handling
│   │   │   ├── __init__.py
│   │   │   └── progress.py
│   │   └── middleware/        # Middleware
│   │       ├── __init__.py
│   │       └── cors.py
│   └── ...
```

---

## API Endpoint Design

### 1. Project Management API

#### 1.1 Create New Project

```http
POST /api/projects
Content-Type: multipart/form-data

# Request Body
{
  "file": <PDF file>,
  "user_query": "Focus on profit margin changes"  # Optional
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

**Implementation**:
```python
# src/api/routes/projects.py

@router.post("/projects")
async def create_project(
    file: UploadFile,
    user_query: str | None = Form(None),
    mode: str = Form("full"),
    background_tasks: BackgroundTasks
):
    # 1. Save uploaded file
    project_id = f"proj_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    pdf_path = await save_upload_file(file, project_id)

    # 2. Start pipeline in background
    background_tasks.add_task(
        run_pipeline_with_progress,
        project_id=project_id,
        pdf_path=pdf_path,
        user_query=user_query,
        mode=mode
    )

    # 3. Return project information
    return {
        "project_id": project_id,
        "status": "processing",
        "created_at": datetime.now(),
        "websocket_url": f"ws://localhost:8000/ws/projects/{project_id}"
    }
```

---

#### 1.2 Get Project List

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

#### 1.3 Get Project Details

```http
GET /api/projects/{project_id}

# Response 200
{
  "project_id": "proj_20260109_143022",
  "title": "Tesla Q3 2025 Earnings Report",
  "status": "completed",
  "created_at": "2026-01-09T14:30:22Z",
  "updated_at": "2026-01-09T14:35:10Z",

  # Pipeline progress
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

  # Document metadata
  "metadata": {
    "company": "Tesla",
    "period": "Q3 2025",
    "document_type": "earnings_report",
    "publish_date": "2025-10-22"
  },

  # Generated files
  "artifacts": {
    "report_md": "/api/projects/proj_20260109_143022/files/report.md",
    "report_html": "/api/projects/proj_20260109_143022/files/report.html",
    "analysis_json": "/api/projects/proj_20260109_143022/files/01_analysis.json",
    "research_json": "/api/projects/proj_20260109_143022/files/02_research.json"
  }
}
```

---

#### 1.4 Delete Project

```http
DELETE /api/projects/{project_id}

# Response 204 No Content
```

---

### 2. Report Viewing API

#### 2.1 Get Report Content

```http
GET /api/projects/{project_id}/report?format=markdown

# Query Parameters
# - format: markdown/html/json (default markdown)

# Response 200
{
  "content": "## Executive Summary\n\nTesla Q3 2025...",
  "format": "markdown",
  "metadata": {
    "title": "Tesla Q3 2025 Earnings Analysis",
    "generated_at": "2026-01-09T14:35:10Z",
    "model": "claude-sonnet-4-5-20250929"
  }
}
```

---

#### 2.2 Get Analysis Results

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

### 3. Citation Query API

#### 3.1 Get Citation Details

```http
GET /api/projects/{project_id}/citations/{citation_id}

# Example request
GET /api/projects/proj_20260109_143022/citations/doc-p5

# Response 200 - Document citation
{
  "type": "document",
  "id": "doc-p5",
  "location": "page-5",
  "source": "page-5#table-2"
}

# Response 200 - Chart citation
{
  "type": "chart",
  "figure_id": "p10_fig_004.png",
  "figure_path": "images/p10_fig_004.png",
  "figure_url": "/api/projects/proj_20260109_143022/files/source/images/p10_fig_004.png",
  "figure_analysis": {
    "type": "chart",
    "title": "Revenue Trend",
    "analysis": {
      "chart_composition": "Bar chart + Line chart",
      "data_relationship": "Revenue vs profit margin comparison",
      "key_insight": "Profit margin continues to decline"
    }
  }
}

# Response 200 - External citation
{
  "type": "web",
  "title": "Tesla Q4 2025 Production Outlook",
  "url": "https://example.com/article",
  "content": "According to recent reports...",
  "published_date": "2025-12-15",
  "relevance_score": 0.95
}
```

**Implementation**:
```python
# src/api/routes/citations.py

@router.get("/projects/{project_id}/citations/{citation_id}")
async def get_citation(project_id: str, citation_id: str):
    project_dir = Path(f"outputs/{project_id}")

    # Document citation
    if citation_id.startswith("doc-"):
        page = citation_id.replace("doc-p", "")
        return {
            "type": "document",
            "id": citation_id,
            "location": f"page-{page}",
            "source": f"page-{page}"
        }

    # Chart citation
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
        raise HTTPException(404, "Chart not found")

    # External citation
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
        raise HTTPException(404, "External citation not found")

    raise HTTPException(400, "Invalid citation ID format")
```

---

### 4. File Service API

#### 4.1 Get File

```http
GET /api/projects/{project_id}/files/{file_path}

# Examples
GET /api/projects/proj_20260109_143022/files/source/images/p10_fig_004.png
GET /api/projects/proj_20260109_143022/files/report.md
GET /api/projects/proj_20260109_143022/files/01_analysis.json
```

**Implementation**:
```python
# src/api/routes/files.py

@router.get("/projects/{project_id}/files/{file_path:path}")
async def get_file(project_id: str, file_path: str):
    """Static file service"""
    file = Path(f"outputs/{project_id}/{file_path}")

    if not file.exists():
        raise HTTPException(404, "File not found")

    return FileResponse(file)
```

---

### 5. WebSocket Progress Streaming

#### 5.1 Connect WebSocket

```javascript
// Frontend connection example
const ws = new WebSocket(`ws://localhost:8000/ws/projects/${projectId}`);

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data);
};
```

#### 5.2 Message Format

**Parsing Phase**:
```json
{
  "stage": "parsing",
  "status": "in_progress",
  "progress": 0.45,
  "message": "Extracting document content...",
  "details": {
    "pages_extracted": 19,
    "total_pages": 42
  },
  "timestamp": "2026-01-09T14:30:45Z"
}
```

**Analysis Phase**:
```json
{
  "stage": "analysis",
  "status": "in_progress",
  "progress": 0.625,
  "message": "Analyzing financial metrics...",
  "details": {
    "sections_completed": 5,
    "total_sections": 8,
    "current_section": "financial_performance"
  },
  "timestamp": "2026-01-09T14:32:30Z"
}
```

**Research Phase**:
```json
{
  "stage": "research",
  "status": "in_progress",
  "progress": 0.77,
  "message": "Searching for supplementary data...",
  "details": {
    "queries_completed": 10,
    "total_queries": 13,
    "current_query": "Tesla Q4 2025 production guidance"
  },
  "timestamp": "2026-01-09T14:33:45Z"
}
```

**Completion**:
```json
{
  "stage": "generation",
  "status": "completed",
  "progress": 1.0,
  "message": "Report generation completed",
  "details": {
    "report_url": "/api/projects/proj_20260109_143022/report"
  },
  "timestamp": "2026-01-09T14:35:10Z"
}
```

**Error**:
```json
{
  "stage": "analysis",
  "status": "failed",
  "progress": 0.4,
  "message": "Analysis failed",
  "error": {
    "code": "LLM_API_ERROR",
    "message": "Gemini API rate limit exceeded",
    "details": "Please retry later"
  },
  "timestamp": "2026-01-09T14:32:30Z"
}
```

---

#### 5.3 WebSocket Implementation

```python
# src/api/websocket/progress.py

from fastapi import WebSocket
from typing import Dict
import asyncio

class ProgressBroadcaster:
    """Progress broadcaster"""

    def __init__(self):
        self.connections: Dict[str, list[WebSocket]] = {}

    async def connect(self, project_id: str, websocket: WebSocket):
        """Establish connection"""
        await websocket.accept()
        if project_id not in self.connections:
            self.connections[project_id] = []
        self.connections[project_id].append(websocket)

    def disconnect(self, project_id: str, websocket: WebSocket):
        """Disconnect"""
        if project_id in self.connections:
            self.connections[project_id].remove(websocket)

    async def broadcast(self, project_id: str, message: dict):
        """Broadcast message to all connections"""
        if project_id in self.connections:
            for ws in self.connections[project_id]:
                try:
                    await ws.send_json(message)
                except Exception:
                    self.disconnect(project_id, ws)

# Global instance
broadcaster = ProgressBroadcaster()


# WebSocket route
@app.websocket("/ws/projects/{project_id}")
async def websocket_endpoint(websocket: WebSocket, project_id: str):
    await broadcaster.connect(project_id, websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except Exception:
        broadcaster.disconnect(project_id, websocket)
```

---

#### 5.4 Pipeline Integration

```python
# src/api/services/pipeline_service.py

from src.api.websocket.progress import broadcaster

async def run_pipeline_with_progress(
    project_id: str,
    pdf_path: Path,
    user_query: str | None,
    mode: str
):
    """Run pipeline and push progress updates"""

    try:
        # 1. Parsing phase
        await broadcaster.broadcast(project_id, {
            "stage": "parsing",
            "status": "in_progress",
            "progress": 0.0,
            "message": "Starting PDF document parsing..."
        })

        # Run parser (needs modification to support progress callback)
        parser = DoclingParser()
        result = await parser.execute(
            pdf_path=pdf_path,
            progress_callback=lambda p: asyncio.create_task(
                broadcaster.broadcast(project_id, {
                    "stage": "parsing",
                    "status": "in_progress",
                    "progress": p,
                    "message": "Extracting document content..."
                })
            )
        )

        # 2. Analysis phase
        await broadcaster.broadcast(project_id, {
            "stage": "analysis",
            "status": "in_progress",
            "progress": 0.0,
            "message": "Starting document analysis..."
        })

        # ... Handle other phases similarly

        # Completion
        await broadcaster.broadcast(project_id, {
            "stage": "generation",
            "status": "completed",
            "progress": 1.0,
            "message": "Report generation completed",
            "details": {
                "report_url": f"/api/projects/{project_id}/report"
            }
        })

    except Exception as e:
        # Error handling
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

## Data Models (API Schemas)

### ProjectCreate

```python
# src/api/schemas/project.py

from pydantic import BaseModel, Field

class ProjectCreate(BaseModel):
    """Create project request"""
    user_query: str | None = Field(None, description="User focus area")
    mode: str = Field("full", description="Run mode: full/no-research/minimal")

class ProjectResponse(BaseModel):
    """Project response"""
    project_id: str
    status: str  # processing/completed/failed
    created_at: str
    updated_at: str
    title: str | None = None
    metadata: dict | None = None

class ProjectDetail(ProjectResponse):
    """Project details"""
    pipeline: dict
    artifacts: dict
```

### CitationResponse

```python
# src/api/schemas/citation.py

class CitationResponse(BaseModel):
    """Citation response"""
    type: str  # document/chart/web
    id: str | None = None
    location: str | None = None
    source: str | None = None

    # Chart citation
    figure_id: str | None = None
    figure_path: str | None = None
    figure_url: str | None = None
    figure_analysis: dict | None = None

    # External citation
    title: str | None = None
    url: str | None = None
    content: str | None = None
```

---

## Error Handling

### Standard Error Response

```json
{
  "detail": {
    "code": "PROJECT_NOT_FOUND",
    "message": "Project not found",
    "timestamp": "2026-01-09T14:35:10Z"
  }
}
```

### Error Codes

| Error Code | HTTP Status | Description |
|------------|-------------|-------------|
| `PROJECT_NOT_FOUND` | 404 | Project not found |
| `CITATION_NOT_FOUND` | 404 | Citation not found |
| `FILE_NOT_FOUND` | 404 | File not found |
| `INVALID_FILE_FORMAT` | 400 | Invalid file format |
| `FILE_TOO_LARGE` | 413 | File too large |
| `PIPELINE_ERROR` | 500 | Pipeline execution error |
| `LLM_API_ERROR` | 502 | LLM API error |

---

## Security

### CORS Configuration

```python
# src/api/middleware/cors.py

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend address
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### File Upload Restrictions

```python
# src/api/main.py

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1"]
)

# File size limit
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
```

---

## Performance Optimization

### 1. File Caching

Use ETag and Last-Modified headers to optimize image/file responses.

### 2. Asynchronous Processing

All pipeline operations are executed asynchronously via background tasks to avoid blocking API responses.

### 3. Pagination

Project list uses limit/offset pagination, default 20 items per page.

---

## Deployment

### Development Environment

```bash
# Start API server
uv run uvicorn src.api.main:app --reload --port 8000
```

### Production Environment

```bash
# Use Gunicorn + Uvicorn workers
gunicorn src.api.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

---

## Dependency Updates

Add to `pyproject.toml`:

```toml
[project.dependencies]
# Existing dependencies...
fastapi = ">=0.115.0"
uvicorn = {extras = ["standard"], version = ">=0.32.0"}
python-multipart = ">=0.0.20"  # File upload
websockets = ">=14.0"
```
