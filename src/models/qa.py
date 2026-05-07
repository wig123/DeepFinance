"""
QA 功能的数据模型
"""
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class QAMessage(BaseModel):
    """单条 QA 消息"""
    role: str = Field(..., description="消息角色: 'user' 或 'assistant'")
    content: str = Field(..., description="消息内容")
    citations: List[str] = Field(default_factory=list, description="引用列表 (citation IDs)")
    context_used: List[str] = Field(default_factory=list, description="使用的上下文类型列表")
    timestamp: datetime = Field(default_factory=datetime.now, description="消息时间戳")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class QASession(BaseModel):
    """QA 会话"""
    session_id: str = Field(..., description="会话 ID")
    project_dir: str = Field(..., description="项目目录路径")
    target_name: str = Field(..., description="研究目标名称")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    messages: List[QAMessage] = Field(default_factory=list, description="消息历史")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class QARequest(BaseModel):
    """QA 请求"""
    question: str = Field(..., description="用户问题")
    context_mode: str = Field(default="basic", description="上下文模式: basic/enhanced/full")
    use_history: bool = Field(default=True, description="是否使用对话历史")


class QAStreamChunk(BaseModel):
    """流式响应块"""
    type: str = Field(..., description="块类型: text/citation/done")
    content: Optional[str] = Field(None, description="文本内容")
    citation_id: Optional[str] = Field(None, description="引用 ID")
    citations: Optional[List[str]] = Field(None, description="所有引用列表")
    context_used: Optional[List[str]] = Field(None, description="使用的上下文")
