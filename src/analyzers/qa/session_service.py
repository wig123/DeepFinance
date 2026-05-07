"""
QA 会话管理服务
"""
import json
import uuid
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from src.models.qa import QASession, QAMessage


class QASessionService:
    """QA 会话管理服务"""

    def __init__(self, base_output_dir: Path):
        """
        初始化服务

        Args:
            base_output_dir: 基础输出目录（例如 outputs/）
        """
        self.base_output_dir = Path(base_output_dir)

    def create_session(self, project_dir: str, target_name: str) -> QASession:
        """
        创建新会话

        Args:
            project_dir: 项目目录路径
            target_name: 研究目标名称

        Returns:
            QASession: 新创建的会话
        """
        session_id = str(uuid.uuid4())[:8]  # 短 ID
        session = QASession(
            session_id=session_id,
            project_dir=project_dir,
            target_name=target_name,
            created_at=datetime.now(),
            messages=[]
        )

        # 保存会话
        self._save_session(session)
        return session

    def load_session(self, project_dir: str, session_id: str) -> Optional[QASession]:
        """
        加载会话

        Args:
            project_dir: 项目目录路径
            session_id: 会话 ID

        Returns:
            Optional[QASession]: 会话对象，如果不存在则返回 None
        """
        session_file = self._get_session_path(project_dir, session_id)
        if not session_file.exists():
            return None

        with open(session_file, 'r', encoding='utf-8') as f:
            session_data = json.load(f)

        return QASession(**session_data)

    def save_message(
        self,
        session: QASession,
        message: QAMessage
    ):
        """
        保存消息到会话

        Args:
            session: 会话对象
            message: 消息对象
        """
        session.messages.append(message)
        self._save_session(session)

    def list_sessions(self, project_dir: str) -> List[dict]:
        """
        列出项目的所有会话

        Args:
            project_dir: 项目目录路径

        Returns:
            List[dict]: 会话信息列表
        """
        qa_sessions_dir = Path(project_dir) / "qa_sessions"
        if not qa_sessions_dir.exists():
            return []

        sessions = []
        for session_file in qa_sessions_dir.glob("session_*.json"):
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                sessions.append({
                    "session_id": session_data["session_id"],
                    "target_name": session_data.get("target_name", "Unknown"),
                    "created_at": session_data["created_at"],
                    "message_count": len(session_data.get("messages", []))
                })
            except Exception as e:
                print(f"Error loading session {session_file}: {e}")
                continue

        # 按创建时间降序排序
        sessions.sort(key=lambda x: x["created_at"], reverse=True)
        return sessions

    def delete_session(self, project_dir: str, session_id: str) -> bool:
        """
        删除会话

        Args:
            project_dir: 项目目录路径
            session_id: 会话 ID

        Returns:
            bool: 是否删除成功
        """
        session_file = self._get_session_path(project_dir, session_id)
        if not session_file.exists():
            return False

        session_file.unlink()
        return True

    def _save_session(self, session: QASession):
        """
        保存会话到文件

        Args:
            session: 会话对象
        """
        qa_sessions_dir = Path(session.project_dir) / "qa_sessions"
        qa_sessions_dir.mkdir(parents=True, exist_ok=True)

        session_file = qa_sessions_dir / f"session_{session.session_id}.json"

        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(session.dict(), f, indent=2, ensure_ascii=False, default=str)

    def _get_session_path(self, project_dir: str, session_id: str) -> Path:
        """
        获取会话文件路径

        Args:
            project_dir: 项目目录路径
            session_id: 会话 ID

        Returns:
            Path: 会话文件路径
        """
        return Path(project_dir) / "qa_sessions" / f"session_{session_id}.json"
