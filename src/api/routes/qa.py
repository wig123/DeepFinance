"""QA API 路由"""
import os
import json
from pathlib import Path
from typing import Optional
from datetime import datetime
from urllib.parse import unquote

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from src.analyzers.qa import ReportQA, QASessionService
from src.models.qa import QAMessage, QARequest

router = APIRouter()

# 初始化 QA 服务
qa_session_service = QASessionService(base_output_dir=Path("outputs"))


class QASessionCreateRequest(BaseModel):
    """创建 QA 会话请求"""
    project_id: str


@router.post("/{project_id}/qa/sessions")
async def create_qa_session(project_id: str):
    """创建新的 QA 会话"""
    try:
        # 获取项目目录
        project_dir = Path("outputs") / project_id
        if not project_dir.exists():
            raise HTTPException(status_code=404, detail="Project not found")

        # 创建会话
        session = qa_session_service.create_session(
            project_dir=str(project_dir),
            target_name=project_id
        )
        return {
            "status": "success",
            "session": session.dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}/qa/sessions")
async def list_qa_sessions(project_id: str):
    """列出项目的所有 QA 会话"""
    try:
        project_dir = Path("outputs") / project_id
        if not project_dir.exists():
            raise HTTPException(status_code=404, detail="Project not found")

        sessions = qa_session_service.list_sessions(str(project_dir))
        return {
            "status": "success",
            "sessions": sessions
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}/qa/sessions/{session_id}")
async def get_qa_session(project_id: str, session_id: str):
    """获取 QA 会话详情"""
    try:
        project_dir = Path("outputs") / project_id

        session = qa_session_service.load_session(str(project_dir), session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")

        return {
            "status": "success",
            "session": session.dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{project_id}/qa/sessions/{session_id}")
async def delete_qa_session(project_id: str, session_id: str):
    """删除 QA 会话"""
    try:
        project_dir = Path("outputs") / project_id

        success = qa_session_service.delete_session(str(project_dir), session_id)
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")

        return {
            "status": "success",
            "message": f"Session {session_id} deleted"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}/qa/suggestions")
async def get_question_suggestions(project_id: str):
    """获取问题建议"""
    try:
        project_dir = Path("outputs") / project_id
        if not project_dir.exists():
            raise HTTPException(status_code=404, detail="Project not found")

        # 检查报告是否存在
        report_path = project_dir / "report.md"
        if not report_path.exists():
            raise HTTPException(
                status_code=404,
                detail="Report not found. Please generate the report first."
            )

        # 获取 LLM 配置
        base_url = os.getenv("CLOSEAI_OPENAI_BASE_URL", "https://api.openai-proxy.org/v1")
        api_key = os.getenv("CLOSEAI_API_KEY")
        model_name = "gemini-2.5-flash"

        if not api_key:
            raise HTTPException(
                status_code=500,
                detail="CLOSEAI_API_KEY not found in environment variables"
            )

        # 初始化 QA 引擎
        qa_engine = ReportQA(
            base_url=base_url,
            api_key=api_key,
            model_name=model_name
        )

        # 生成问题建议
        suggestions = await qa_engine.generate_suggestions(
            project_dir=project_dir,
            target_language="Chinese (中文)"
        )

        return {
            "status": "success",
            "suggestions": suggestions
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{project_id}/qa/sessions/{session_id}/ask")
async def ask_question(project_id: str, session_id: str, request: QARequest):
    """向 QA 系统提问"""
    try:
        project_dir = Path("outputs") / project_id
        if not project_dir.exists():
            raise HTTPException(status_code=404, detail="Project not found")

        # 加载会话
        session = qa_session_service.load_session(str(project_dir), session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")

        # 保存用户消息
        user_msg = QAMessage(
            role="user",
            content=request.question,
            timestamp=datetime.now()
        )
        qa_session_service.save_message(session, user_msg)

        # 获取 LLM 配置（使用项目的 CLOSEAI 配置）
        base_url = os.getenv("CLOSEAI_OPENAI_BASE_URL", "https://api.openai-proxy.org/v1")
        api_key = os.getenv("CLOSEAI_API_KEY")
        model_name = "gemini-2.5-flash"  # 使用 OpenAI 兼容模型

        if not api_key:
            raise HTTPException(
                status_code=500,
                detail="CLOSEAI_API_KEY not found in environment variables"
            )

        # 初始化 QA 引擎
        qa_engine = ReportQA(
            base_url=base_url,
            api_key=api_key,
            model_name=model_name
        )

        # 调用 QA 引擎
        result = await qa_engine.ask(
            question=request.question,
            project_dir=project_dir,
            session=session,
            context_mode=request.context_mode,
            target_language="Chinese (中文)"
        )

        # 保存助手消息
        assistant_msg = QAMessage(
            role="assistant",
            content=result["answer"],
            citations=result["citations"],
            context_used=result["context_used"],
            timestamp=datetime.now()
        )
        qa_session_service.save_message(session, assistant_msg)

        return {
            "status": "success",
            "answer": result["answer"],
            "citations": result["citations"],
            "context_used": result["context_used"]
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{project_id}/qa/sessions/{session_id}/ask-stream")
async def ask_question_stream(project_id: str, session_id: str, request: QARequest):
    """向 QA 系统提问（SSE 流式响应）"""

    async def event_generator():
        """SSE 事件生成器"""
        try:
            project_dir = Path("outputs") / project_id
            if not project_dir.exists():
                yield {
                    "event": "error",
                    "data": json.dumps({"error": "Project not found"})
                }
                return

            # 加载会话
            session = qa_session_service.load_session(str(project_dir), session_id)
            if session is None:
                yield {
                    "event": "error",
                    "data": json.dumps({"error": "Session not found"})
                }
                return

            # 保存用户消息
            user_msg = QAMessage(
                role="user",
                content=request.question,
                timestamp=datetime.now()
            )
            qa_session_service.save_message(session, user_msg)

            # 获取 LLM 配置（使用项目的 CLOSEAI 配置）
            base_url = os.getenv("CLOSEAI_OPENAI_BASE_URL", "https://api.openai-proxy.org/v1")
            api_key = os.getenv("CLOSEAI_API_KEY")
            model_name = "gemini-2.5-flash"  # 使用 OpenAI 兼容模型

            if not api_key:
                yield {
                    "event": "error",
                    "data": json.dumps({"error": "CLOSEAI_API_KEY not found in environment variables"})
                }
                return

            # 初始化 QA 引擎
            qa_engine = ReportQA(
                base_url=base_url,
                api_key=api_key,
                model_name=model_name
            )

            # 发送开始事件
            yield {
                "event": "start",
                "data": json.dumps({
                    "session_id": session_id,
                    "question": request.question
                })
            }

            # 流式生成答案
            full_answer = ""
            citations = []

            async for chunk in qa_engine.ask_stream(
                question=request.question,
                project_dir=project_dir,
                session=session,
                context_mode=request.context_mode,
                target_language="Chinese (中文)"
            ):
                if chunk.type == "text":
                    full_answer += chunk.content
                    yield {
                        "event": "message",
                        "data": json.dumps({
                            "type": "text",
                            "content": chunk.content
                        })
                    }

                elif chunk.type == "citation":
                    citations.append(chunk.citation_id)
                    yield {
                        "event": "citation",
                        "data": json.dumps({
                            "type": "citation",
                            "citation_id": chunk.citation_id
                        })
                    }

                elif chunk.type == "done":
                    citations = chunk.citations or citations

                    # 保存助手消息
                    assistant_msg = QAMessage(
                        role="assistant",
                        content=full_answer,
                        citations=citations,
                        context_used=chunk.context_used or [],
                        timestamp=datetime.now()
                    )
                    qa_session_service.save_message(session, assistant_msg)

                    yield {
                        "event": "done",
                        "data": json.dumps({
                            "type": "done",
                            "citations": citations,
                            "context_used": chunk.context_used
                        })
                    }

        except Exception as e:
            import traceback
            traceback.print_exc()
            yield {
                "event": "error",
                "data": json.dumps({
                    "error": str(e),
                    "traceback": traceback.format_exc()
                })
            }

    return EventSourceResponse(event_generator())
