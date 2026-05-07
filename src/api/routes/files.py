"""文件服务路由"""

import mimetypes
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from src.api.services.project_service import project_service

router = APIRouter()

# 初始化 mimetypes
mimetypes.init()


@router.get("/{project_id}/files/{file_path:path}")
async def get_file(project_id: str, file_path: str):
    """获取项目文件

    提供项目目录下的静态文件访问。

    Args:
        project_id: 项目ID
        file_path: 文件路径（相对于项目目录或 uploads 目录）

    Returns:
        文件内容
    """
    # 检查项目是否存在
    if not project_service.project_exists(project_id):
        raise HTTPException(404, f"项目不存在: {project_id}")

    # 特殊处理：如果路径以 uploads/ 开头，直接从 uploads 目录读取
    if file_path.startswith("uploads/"):
        full_path = Path(file_path).resolve()  # 转换为绝对路径
        # 安全检查：确保文件名与项目ID相关（防止访问其他项目的文件）
        # 支持两种情况：
        # 1. 项目ID直接在文件名中: proj_xxx.pdf
        # 2. 项目ID是带时间戳的版本: proj_xxx_timestamp 对应 proj_xxx.pdf
        file_name = full_path.name
        is_allowed = project_id in file_name
        if not is_allowed:
            # 检查是否是带时间戳的项目ID访问原始文件
            # proj_20260123_011313_20260123_180814 → proj_20260123_011313
            if "_20" in project_id:
                parts = project_id.split("_")
                if len(parts) >= 3:
                    base_id = "_".join(parts[:3])
                    is_allowed = base_id in file_name
        if not is_allowed:
            raise HTTPException(403, "禁止访问其他项目的文件")
        # 验证路径在 uploads 目录内
        uploads_dir = Path("uploads").resolve()
        if not str(full_path).startswith(str(uploads_dir)):
            raise HTTPException(403, "禁止访问 uploads 目录外的文件")
    else:
        # 正常流程：从项目目录读取
        project_dir = project_service.get_project_dir(project_id)
        full_path = project_dir / file_path

        # 安全检查：防止路径遍历攻击
        try:
            full_path = full_path.resolve()
            project_dir = project_dir.resolve()
            if not str(full_path).startswith(str(project_dir)):
                raise HTTPException(403, "禁止访问项目目录外的文件")
        except Exception:
            raise HTTPException(400, "无效的文件路径")

    # 检查文件是否存在
    if not full_path.exists():
        # 智能查找：仅对项目目录内的文件进行智能查找（非 uploads）
        if not file_path.startswith("uploads/"):
            project_dir = project_service.get_project_dir(project_id)
            if file_path.startswith("source/") and (file_path.endswith(".png") or file_path.endswith(".jpg")):
                file_name = Path(file_path).name
                # 搜索项目目录下所有匹配的图片
                for img in project_dir.glob(f"**/{file_name}"):
                    if img.is_file():
                        full_path = img
                        break
                else:
                    # 尝试模糊匹配（文件名可能略有不同）
                    base_name = file_name.rsplit("_", 1)[-1] if "_" in file_name else file_name
                    for img in project_dir.glob(f"**/*{base_name}"):
                        if img.is_file():
                            full_path = img
                            break
                    else:
                        raise HTTPException(404, f"文件不存在: {file_path}")
            else:
                raise HTTPException(404, f"文件不存在: {file_path}")
        else:
            raise HTTPException(404, f"文件不存在: {file_path}")

    if not full_path.is_file():
        raise HTTPException(400, f"不是文件: {file_path}")

    # 重新验证路径安全性（智能查找后）
    if not file_path.startswith("uploads/"):
        full_path = full_path.resolve()
        project_dir = project_service.get_project_dir(project_id).resolve()
        if not str(full_path).startswith(str(project_dir)):
            raise HTTPException(403, "禁止访问项目目录外的文件")

    # 获取 MIME 类型
    mime_type, _ = mimetypes.guess_type(str(full_path))
    if mime_type is None:
        # 根据扩展名推断
        ext = full_path.suffix.lower()
        mime_map = {
            ".md": "text/markdown",
            ".json": "application/json",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".pdf": "application/pdf",
            ".html": "text/html",
            ".txt": "text/plain",
        }
        mime_type = mime_map.get(ext, "application/octet-stream")

    return FileResponse(
        path=full_path,
        media_type=mime_type,
        filename=full_path.name,
    )
