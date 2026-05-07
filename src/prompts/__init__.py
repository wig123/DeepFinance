"""提示词管理模块

所有提示词解耦到独立文件，便于维护和版本控制。
"""

from pathlib import Path

PROMPTS_DIR = Path(__file__).parent


def load_prompt(prompt_name: str) -> str:
    """加载提示词模板

    Args:
        prompt_name: 提示词名称（不含扩展名）

    Returns:
        str: 提示词模板内容

    Raises:
        FileNotFoundError: 提示词文件不存在
    """
    prompt_file = PROMPTS_DIR / f"{prompt_name}.txt"

    if not prompt_file.exists():
        raise FileNotFoundError(f"提示词文件不存在: {prompt_file}")

    return prompt_file.read_text(encoding="utf-8")


def format_prompt(prompt_name: str, **kwargs) -> str:
    """加载并格式化提示词

    Args:
        prompt_name: 提示词名称
        **kwargs: 格式化参数

    Returns:
        str: 格式化后的提示词
    """
    template = load_prompt(prompt_name)
    return template.format(**kwargs)


# 便捷访问
def get_document_analysis_prompt(**kwargs) -> str:
    """获取文档分析提示词"""
    return format_prompt("analysis/document_analysis", **kwargs)


def get_report_generation_prompt(**kwargs) -> str:
    """获取报告生成提示词"""
    return format_prompt("generation/report_generation", **kwargs)


def get_chunk_analysis_prompt(**kwargs) -> str:
    """获取分块分析提示词"""
    return format_prompt("analysis/chunk_analysis", **kwargs)


def get_merge_analysis_prompt(**kwargs) -> str:
    """获取合并分析提示词"""
    return format_prompt("analysis/merge_analysis", **kwargs)
