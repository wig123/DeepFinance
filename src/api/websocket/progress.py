"""WebSocket 进度推送模块"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

router = APIRouter()


class ProgressMessage(BaseModel):
    """进度消息"""

    stage: str
    status: str  # pending/in_progress/completed/failed
    progress: float  # 0.0 - 1.0
    message: str
    details: dict[str, Any] | None = None
    error: dict[str, Any] | None = None
    timestamp: datetime = datetime.now()


class ProgressBroadcaster:
    """进度广播器"""

    def __init__(self):
        self.connections: dict[str, list[WebSocket]] = {}

    async def connect(self, project_id: str, websocket: WebSocket):
        """建立连接"""
        await websocket.accept()
        if project_id not in self.connections:
            self.connections[project_id] = []
        self.connections[project_id].append(websocket)
        print(f"[WS] 客户端连接: {project_id}, 当前连接数: {len(self.connections[project_id])}")

    def disconnect(self, project_id: str, websocket: WebSocket):
        """断开连接"""
        if project_id in self.connections:
            if websocket in self.connections[project_id]:
                self.connections[project_id].remove(websocket)
            if not self.connections[project_id]:
                del self.connections[project_id]
            print(f"[WS] 客户端断开: {project_id}")

    async def broadcast(self, project_id: str, message: dict | ProgressMessage):
        """广播消息到所有连接"""
        if project_id not in self.connections:
            return

        if isinstance(message, ProgressMessage):
            message_dict = message.model_dump(mode="json")
        else:
            message_dict = message

        dead_connections = []
        for ws in self.connections[project_id]:
            try:
                await ws.send_json(message_dict)
            except Exception as e:
                print(f"[WS] 发送失败: {e}")
                dead_connections.append(ws)

        # 清理断开的连接
        for ws in dead_connections:
            self.disconnect(project_id, ws)

    async def send_stage_start(self, project_id: str, stage: str, message: str):
        """发送阶段开始消息"""
        await self.broadcast(
            project_id,
            ProgressMessage(
                stage=stage,
                status="in_progress",
                progress=0.0,
                message=message,
            ),
        )

    async def send_stage_progress(
        self,
        project_id: str,
        stage: str,
        progress: float,
        message: str,
        details: dict[str, Any] | None = None,
    ):
        """发送阶段进度消息"""
        await self.broadcast(
            project_id,
            ProgressMessage(
                stage=stage,
                status="in_progress",
                progress=progress,
                message=message,
                details=details,
            ),
        )

    async def send_stage_complete(
        self,
        project_id: str,
        stage: str,
        message: str,
        details: dict[str, Any] | None = None,
    ):
        """发送阶段完成消息"""
        await self.broadcast(
            project_id,
            ProgressMessage(
                stage=stage,
                status="completed",
                progress=1.0,
                message=message,
                details=details,
            ),
        )

    async def send_error(self, project_id: str, stage: str, error_message: str, error_code: str = "UNKNOWN_ERROR"):
        """发送错误消息"""
        await self.broadcast(
            project_id,
            ProgressMessage(
                stage=stage,
                status="failed",
                progress=0.0,
                message="处理失败",
                error={
                    "code": error_code,
                    "message": error_message,
                },
            ),
        )


# 全局广播器实例
broadcaster = ProgressBroadcaster()


@router.websocket("/ws/projects/{project_id}")
async def websocket_endpoint(websocket: WebSocket, project_id: str):
    """WebSocket 端点"""
    import asyncio

    await broadcaster.connect(project_id, websocket)
    try:
        while True:
            try:
                # 使用超时接收消息，防止无限阻塞
                data = await asyncio.wait_for(websocket.receive_text(), timeout=60.0)
                # 处理客户端发送的消息，如 ping/pong
                if data == "ping":
                    await websocket.send_text("pong")
            except asyncio.TimeoutError:
                # 超时后发送心跳检测
                try:
                    await websocket.send_text("heartbeat")
                except Exception:
                    break  # 发送失败，连接已断开
    except WebSocketDisconnect:
        print(f"[WS] 客户端主动断开: {project_id}")
        broadcaster.disconnect(project_id, websocket)
    except Exception as e:
        print(f"[WS] 连接异常: {project_id}, 错误: {type(e).__name__}: {e}")
        broadcaster.disconnect(project_id, websocket)
