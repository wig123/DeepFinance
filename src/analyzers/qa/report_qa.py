"""
报告 QA 引擎核心
"""
import json
import re
import yaml
from pathlib import Path
from typing import Dict, List, AsyncIterator, Optional
from datetime import datetime

from openai import AsyncOpenAI
from src.models.qa import QASession, QAMessage, QAStreamChunk


class ReportQA:
    """报告问答引擎"""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model_name: str = "deepseek-chat",
        generation_params: Optional[Dict] = None
    ):
        """
        初始化 QA 引擎

        Args:
            base_url: LLM API 基础 URL
            api_key: API 密钥
            model_name: 模型名称（支持 OpenAI 兼容的 API）
            generation_params: 生成参数
        """
        self.client = AsyncOpenAI(base_url=base_url, api_key=api_key)
        self.model_name = model_name
        self.generation_params = generation_params or {
            "temperature": 0.7,
            "max_tokens": 4096
        }

        # 加载 prompts
        prompts_path = Path(__file__).parents[2] / "prompts" / "qa" / "qa_prompts.yaml"
        with open(prompts_path, 'r', encoding='utf-8') as f:
            self.prompts = yaml.safe_load(f)

    async def ask_stream(
        self,
        question: str,
        project_dir: Path,
        session: QASession,
        context_mode: str = "basic",
        target_language: str = "Chinese (中文)"
    ) -> AsyncIterator[QAStreamChunk]:
        """
        流式问答

        Args:
            question: 用户问题
            project_dir: 项目目录路径
            session: QA 会话对象
            context_mode: 上下文模式 (basic/enhanced/full)
            target_language: 目标语言

        Yields:
            QAStreamChunk: 流式响应块
        """
        # 1. 构建上下文
        context = await self._build_context(project_dir, context_mode)

        # 2. 构建对话历史
        conversation_history = self._build_conversation_context(session)

        # 3. 构建 prompt
        prompt = self._build_qa_prompt(
            question=question,
            context=context,
            conversation_history=conversation_history,
            target_language=target_language
        )

        # 4. 调用 LLM 生成答案
        messages = [{"role": "user", "content": prompt}]

        try:
            # 使用 AsyncOpenAI 流式 API
            stream = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                stream=True,
                **self.generation_params
            )

            full_answer = ""
            async for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if delta.content:
                        content = delta.content
                        full_answer += content
                        yield QAStreamChunk(
                            type="text",
                            content=content
                        )

            # 5. 提取引用
            citations = self._extract_citations(full_answer)

            # 6. 返回完成信号
            yield QAStreamChunk(
                type="done",
                citations=citations,
                context_used=list(context.keys())
            )

        except Exception as e:
            yield QAStreamChunk(
                type="error",
                content=f"生成答案时出错: {str(e)}"
            )

    async def ask(
        self,
        question: str,
        project_dir: Path,
        session: QASession,
        context_mode: str = "basic",
        target_language: str = "Chinese (中文)"
    ) -> Dict:
        """
        非流式问答（用于简单测试）

        Returns:
            Dict: {"answer": str, "citations": List[str], "context_used": List[str]}
        """
        context = await self._build_context(project_dir, context_mode)
        conversation_history = self._build_conversation_context(session)

        prompt = self._build_qa_prompt(
            question=question,
            context=context,
            conversation_history=conversation_history,
            target_language=target_language
        )

        messages = [{"role": "user", "content": prompt}]
        response = await self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            **self.generation_params
        )
        answer = response.choices[0].message.content
        citations = self._extract_citations(answer)

        return {
            "answer": answer,
            "citations": citations,
            "context_used": list(context.keys())
        }

    async def generate_suggestions(
        self,
        project_dir: Path,
        target_language: str = "Chinese (中文)"
    ) -> List[str]:
        """
        生成问题建议

        Args:
            project_dir: 项目目录路径
            target_language: 目标语言

        Returns:
            List[str]: 建议问题列表
        """
        # 1. 加载报告内容
        report_path = project_dir / "report.md"
        if not report_path.exists():
            return [
                "请总结报告的核心内容",
                "报告中有哪些关键发现?",
                "有哪些值得关注的数据指标?"
            ]

        report_content = report_path.read_text(encoding='utf-8')

        # 2. 生成报告摘要（前3000字符）
        report_summary = report_content[:3000]

        # 3. 构建 prompt
        prompt_template = self.prompts["qa_question_suggestions"]
        prompt = prompt_template.format(
            report_summary=report_summary,
            target_language=target_language
        )

        # 4. 调用 LLM 生成问题
        try:
            messages = [{"role": "user", "content": prompt}]
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )
            answer = response.choices[0].message.content.strip()

            # 5. 解析 JSON
            # 移除可能的 markdown 代码块标记
            if answer.startswith("```"):
                answer = answer.split("\n", 1)[1]
            if answer.endswith("```"):
                answer = answer.rsplit("\n", 1)[0]

            questions = json.loads(answer)
            if isinstance(questions, list) and len(questions) > 0:
                return questions[:5]  # 返回前5个

        except Exception as e:
            print(f"生成问题建议失败: {e}")

        # 6. 失败时返回默认问题
        return [
            "请总结报告的核心内容",
            "报告中有哪些关键发现?",
            "有哪些值得关注的数据指标?",
            "报告对未来的展望如何?",
            "有哪些潜在的风险因素?"
        ]

    async def _build_context(
        self,
        project_dir: Path,
        mode: str
    ) -> Dict[str, str]:
        """
        分层构建上下文

        Args:
            project_dir: 项目目录
            mode: 上下文模式 (basic/enhanced/full)

        Returns:
            Dict: 上下文字典
        """
        context = {}

        # 基础上下文：报告内容
        report_path = project_dir / "report.md"
        if report_path.exists():
            context["report"] = report_path.read_text(encoding='utf-8')

        # 基础上下文：分析摘要
        analysis_path = project_dir / "memory" / "memory.pkl"
        if analysis_path.exists():
            # 尝试加载 memory（包含分析结果）
            # 注意：这里需要访问 memory 对象，但为了简化，我们先跳过
            # 后续可以传入 memory 对象
            pass

        # 增强上下文：研究数据摘要
        if mode in ["enhanced", "full"]:
            # 可以添加更多上下文
            pass

        # 全量上下文：原始文档内容
        if mode == "full":
            source_content_path = project_dir / "source" / "content.md"
            if source_content_path.exists():
                context["original_content"] = source_content_path.read_text(encoding='utf-8')

        return context

    def _build_conversation_context(self, session: QASession, max_history: int = 5) -> str:
        """
        构建对话历史上下文（滑动窗口）

        Args:
            session: QA 会话
            max_history: 最大历史轮数

        Returns:
            str: 格式化的对话历史
        """
        if not session.messages:
            return "No previous conversation."

        # 取最近的 N 轮对话
        recent_messages = session.messages[-(max_history * 2):]

        history_lines = []
        for msg in recent_messages:
            role_label = "User" if msg.role == "user" else "Assistant"
            history_lines.append(f"{role_label}: {msg.content}")

        return "\n".join(history_lines)

    def _build_qa_prompt(
        self,
        question: str,
        context: Dict[str, str],
        conversation_history: str,
        target_language: str
    ) -> str:
        """
        构建 QA prompt

        Args:
            question: 用户问题
            context: 上下文字典
            conversation_history: 对话历史
            target_language: 目标语言

        Returns:
            str: 完整的 prompt
        """
        # 获取 prompt 模板
        prompt_template = self.prompts["qa_answering"]

        # 准备上下文内容
        report_content = context.get("report", "No report available.")

        # 简化的分析摘要（后续可以从 memory 中提取）
        analysis_summary = "Analysis results are integrated in the report."

        # 研究摘要（仅在 enhanced/full 模式下）
        research_summary = ""
        if "research" in context:
            research_summary = f"\n## Research Data\n{context['research']}\n"

        # 填充 prompt
        prompt = prompt_template.format(
            current_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            report_content=report_content[:30000],  # 限制长度
            analysis_summary=analysis_summary,
            research_summary=research_summary,
            conversation_history=conversation_history,
            question=question,
            target_language=target_language
        )

        return prompt

    def _extract_citations(self, text: str) -> List[str]:
        """
        从文本中提取引用 ID

        Args:
            text: 回答文本

        Returns:
            List[str]: 引用 ID 列表
        """
        # 匹配 [^citation-id] 格式
        pattern = r'\[\^([\w-]+)\]'
        citations = re.findall(pattern, text)
        return list(set(citations))  # 去重

    def _split_into_sentences(self, text: str) -> List[str]:
        """
        将文本分割为句子（用于模拟流式输出）

        Args:
            text: 完整文本

        Returns:
            List[str]: 句子列表
        """
        # 简单的按句子分割（中英文）
        sentences = []
        current = ""

        for char in text:
            current += char
            if char in ["。", "!", "?", "！", "？", ".", "\n"]:
                if current.strip():
                    sentences.append(current)
                current = ""

        if current.strip():
            sentences.append(current)

        return sentences
