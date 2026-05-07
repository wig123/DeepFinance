"""项目管理服务"""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from src.api.schemas.project import (
    PipelineInfo,
    PipelineStage,
    ProjectArtifacts,
    ProjectDetail,
    ProjectListResponse,
    ProjectMetadata,
    ProjectResponse,
)


class ProjectService:
    """项目管理服务"""

    def __init__(self, output_base: str = "outputs"):
        self.output_base = Path(output_base)
        self.output_base.mkdir(parents=True, exist_ok=True)

    def get_project_dir(self, project_id: str) -> Path:
        """获取项目目录"""
        return self.output_base / project_id

    def project_exists(self, project_id: str) -> bool:
        """检查项目是否存在"""
        return self.get_project_dir(project_id).exists()

    def load_project_state(self, project_id: str) -> dict[str, Any] | None:
        """加载项目状态"""
        state_file = self.get_project_dir(project_id) / "project_state.json"
        if not state_file.exists():
            return None
        return json.loads(state_file.read_text(encoding="utf-8"))

    def save_project_state(self, project_id: str, state: dict[str, Any]):
        """保存项目状态"""
        state_file = self.get_project_dir(project_id) / "project_state.json"
        state_file.write_text(json.dumps(state, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    def create_project(self, project_id: str, user_query: str | None, mode: str) -> dict[str, Any]:
        """创建新项目"""
        project_dir = self.get_project_dir(project_id)
        project_dir.mkdir(parents=True, exist_ok=True)

        # 初始化项目状态
        state = {
            "project_id": project_id,
            "status": "processing",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "user_query": user_query,
            "mode": mode,
            "title": None,
            "metadata": None,
            "pipeline": {
                "current_stage": "pending",
                "stages": [
                    {"name": "parsing", "status": "pending"},
                    {"name": "analysis", "status": "pending"},
                    {"name": "research", "status": "pending"},
                    {"name": "generation", "status": "pending"},
                ],
            },
        }
        self.save_project_state(project_id, state)
        return state

    def update_project_status(
        self,
        project_id: str,
        status: str | None = None,
        title: str | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        """更新项目状态"""
        state = self.load_project_state(project_id)
        if state is None:
            return

        state["updated_at"] = datetime.now().isoformat()
        if status:
            state["status"] = status
        if title:
            state["title"] = title
        if metadata:
            state["metadata"] = metadata

        self.save_project_state(project_id, state)

    def update_pipeline_stage(
        self,
        project_id: str,
        stage_name: str,
        status: str,
        started_at: datetime | None = None,
        completed_at: datetime | None = None,
        duration: float | None = None,
        details: dict[str, Any] | None = None,
        error: str | None = None,
    ):
        """更新流水线阶段状态"""
        state = self.load_project_state(project_id)
        if state is None:
            return

        state["updated_at"] = datetime.now().isoformat()
        state["pipeline"]["current_stage"] = stage_name

        for stage in state["pipeline"]["stages"]:
            if stage["name"] == stage_name:
                stage["status"] = status
                if started_at:
                    stage["started_at"] = started_at.isoformat()
                if completed_at:
                    stage["completed_at"] = completed_at.isoformat()
                if duration is not None:
                    stage["duration"] = duration
                if details:
                    stage["details"] = details
                if error:
                    stage["error"] = error
                break

        self.save_project_state(project_id, state)

    def get_project(self, project_id: str) -> ProjectDetail | None:
        """获取项目详情"""
        state = self.load_project_state(project_id)
        if state is None:
            return None

        project_dir = self.get_project_dir(project_id)

        # 构建产出物路径
        artifacts = None
        if state["status"] == "completed":
            artifacts = ProjectArtifacts(
                report_md=f"/api/projects/{project_id}/files/report.md"
                if (project_dir / "report.md").exists()
                else None,
                report_html=f"/api/projects/{project_id}/files/report.html"
                if (project_dir / "report.html").exists()
                else None,
                analysis_json=f"/api/projects/{project_id}/files/01_analysis.json"
                if (project_dir / "01_analysis.json").exists()
                else None,
                research_json=f"/api/projects/{project_id}/files/02_research.json"
                if (project_dir / "02_research.json").exists()
                else None,
            )

        # 构建流水线信息
        pipeline = PipelineInfo(
            current_stage=state["pipeline"]["current_stage"],
            stages=[PipelineStage(**stage) for stage in state["pipeline"]["stages"]],
        )

        # 构建元数据
        metadata = None
        if state.get("metadata"):
            metadata = ProjectMetadata(**state["metadata"])

        return ProjectDetail(
            project_id=state["project_id"],
            status=state["status"],
            created_at=datetime.fromisoformat(state["created_at"]),
            updated_at=datetime.fromisoformat(state["updated_at"]) if state.get("updated_at") else None,
            title=state.get("title"),
            metadata=metadata,
            pipeline=pipeline,
            artifacts=artifacts,
            user_query=state.get("user_query"),
            mode=state.get("mode"),
        )

    def list_projects(self, limit: int = 20, offset: int = 0) -> ProjectListResponse:
        """获取项目列表"""
        projects = []

        # 遍历输出目录
        for project_dir in sorted(self.output_base.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
            if not project_dir.is_dir():
                continue
            if not (project_dir / "project_state.json").exists():
                continue

            state = self.load_project_state(project_dir.name)
            if state is None:
                continue

            metadata = None
            if state.get("metadata"):
                metadata = ProjectMetadata(**state["metadata"])

            projects.append(
                ProjectResponse(
                    project_id=state["project_id"],
                    status=state["status"],
                    created_at=datetime.fromisoformat(state["created_at"]),
                    updated_at=datetime.fromisoformat(state["updated_at"]) if state.get("updated_at") else None,
                    title=state.get("title"),
                    metadata=metadata,
                )
            )

        total = len(projects)
        items = projects[offset : offset + limit]

        return ProjectListResponse(total=total, items=items)

    def delete_project(self, project_id: str) -> bool:
        """删除项目"""
        project_dir = self.get_project_dir(project_id)
        if not project_dir.exists():
            return False

        shutil.rmtree(project_dir)
        return True


# 全局服务实例
project_service = ProjectService()
