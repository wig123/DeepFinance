"""项目管理路由"""

import shutil
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile

from src.api.schemas.project import ProjectDetail, ProjectListResponse, ProjectResponse
from src.api.services.pipeline_service import get_pipeline_service
from src.api.services.project_service import project_service

router = APIRouter()

# 文件上传配置
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_EXTENSIONS = {".pdf"}
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


async def save_upload_file(file: UploadFile, project_id: str) -> Path:
    """保存上传的文件"""
    # 检查文件扩展名
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"不支持的文件格式: {file_ext}，仅支持 PDF")

    # 检查文件大小
    file.file.seek(0, 2)  # 移动到文件末尾
    file_size = file.file.tell()
    file.file.seek(0)  # 移回开头

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(413, f"文件过大: {file_size / 1024 / 1024:.1f}MB，最大允许 50MB")

    # 保存文件
    upload_path = UPLOAD_DIR / f"{project_id}{file_ext}"
    with open(upload_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return upload_path


async def run_pipeline_task(
    project_id: str,
    pdf_path: Path,
    output_dir: Path,
    user_query: str | None,
    mode: str,
):
    """后台运行流水线任务"""
    try:
        pipeline = get_pipeline_service(mode)
        await pipeline.run_with_progress(
            project_id=project_id,
            pdf_path=pdf_path,
            output_dir=output_dir,
            user_query=user_query,
        )
    except Exception as e:
        # 错误已在 pipeline_service 中处理
        print(f"流水线执行失败: {e}")


@router.post("", response_model=ProjectResponse)
async def create_project(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user_query: str | None = Form(None),
    mode: str = Form("full"),
):
    """创建新项目

    上传 PDF 文件并开始分析流程。

    Args:
        file: PDF 文件
        user_query: 用户侧重点描述（可选）
        mode: 运行模式（full/no-research/minimal）

    Returns:
        项目信息，包含 WebSocket URL 用于监听进度
    """
    # 验证模式
    if mode not in ("full", "no-research", "minimal"):
        raise HTTPException(400, f"无效的模式: {mode}，支持 full/no-research/minimal")

    # 生成项目ID
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    project_id = f"proj_{timestamp}"

    # 保存上传的文件
    pdf_path = await save_upload_file(file, project_id)

    # 创建项目
    output_dir = project_service.get_project_dir(project_id)
    project_service.create_project(project_id, user_query, mode)

    # 后台启动流水线
    background_tasks.add_task(
        run_pipeline_task,
        project_id=project_id,
        pdf_path=pdf_path,
        output_dir=output_dir,
        user_query=user_query,
        mode=mode,
    )

    return ProjectResponse(
        project_id=project_id,
        status="processing",
        created_at=datetime.now(),
        websocket_url=f"ws://localhost:8001/ws/projects/{project_id}",
    )


@router.get("", response_model=ProjectListResponse)
async def list_projects(limit: int = 20, offset: int = 0):
    """获取项目列表

    Args:
        limit: 每页数量（默认 20）
        offset: 偏移量

    Returns:
        项目列表
    """
    return project_service.list_projects(limit=limit, offset=offset)


@router.get("/{project_id}", response_model=ProjectDetail)
async def get_project(project_id: str):
    """获取项目详情

    Args:
        project_id: 项目ID

    Returns:
        项目详情，包含流水线状态和产出物路径
    """
    project = project_service.get_project(project_id)
    if project is None:
        raise HTTPException(404, f"项目不存在: {project_id}")
    return project


@router.delete("/{project_id}", status_code=204)
async def delete_project(project_id: str):
    """删除项目

    Args:
        project_id: 项目ID
    """
    if not project_service.delete_project(project_id):
        raise HTTPException(404, f"项目不存在: {project_id}")

    # 同时删除上传的文件
    for ext in ALLOWED_EXTENSIONS:
        upload_path = UPLOAD_DIR / f"{project_id}{ext}"
        if upload_path.exists():
            upload_path.unlink()
