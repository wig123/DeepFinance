"""测试简化的报告生成流水线

端到端测试：PDF → 分析 → 研究 → 报告

PDF 路径来源（按优先级）：
1. 命令行位置参数：``python scripts/run_pipeline.py --mode full path/to.pdf``
2. 环境变量 ``PIPELINE_TEST_PDF``
3. 默认 ``inputs/sample.pdf``
"""

import logging
import os
import sys
from pathlib import Path

DEFAULT_PDF = os.environ.get("PIPELINE_TEST_PDF", "inputs/sample.pdf")

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("/tmp/pipeline_test.log", encoding="utf-8"),
    ],
)

logger = logging.getLogger(__name__)


def test_full_pipeline(pdf_path: str = DEFAULT_PDF):
    """测试完整流水线"""
    from src.pipeline import ReportPipeline

    if not Path(pdf_path).exists():
        logger.error(f"测试文件不存在: {pdf_path}")
        return False

    logger.info("=" * 80)
    logger.info("DeepFinance - 简化流水线测试")
    logger.info("=" * 80)
    logger.info(f"测试文件: {pdf_path}")

    try:
        # 创建流水线（启用所有功能）
        pipeline = ReportPipeline(
            output_base="outputs/test_pipeline",
            enable_image_analysis=True,  # 启用图片分析
            enable_research=True,  # 启用外部研究
            analyzer_model="gemini-2.5-flash-lite-preview-09-2025",  # 使用Gemini（CloseAI）
            generator_model="gemini-2.5-flash-lite-preview-09-2025",  # 使用Gemini（CloseAI）
            search_engine="tavily",  # 使用Tavily搜索
        )

        # 运行流水线
        output_dir = pipeline.run(pdf_path)

        logger.info("\n" + "=" * 80)
        logger.info("测试成功！")
        logger.info("=" * 80)
        logger.info(f"输出目录: {output_dir}")
        logger.info("\n生成的文件:")
        logger.info(f"  - {output_dir / 'source' / 'content.md'} (解析的文档)")
        logger.info(f"  - {output_dir / 'source' / 'metadata.json'} (元数据)")
        logger.info(f"  - {output_dir / '01_analysis.json'} (文档分析)")
        logger.info(f"  - {output_dir / '02_research.json'} (补充研究)")
        logger.info(f"  - {output_dir / 'report.md'} (最终报告)")
        logger.info(f"  - {output_dir / 'report_metadata.json'} (报告元数据)")

        return True

    except Exception as e:
        logger.error(f"测试失败: {e}", exc_info=True)
        return False


def test_without_research(pdf_path: str = DEFAULT_PDF):
    """测试无外部研究的流水线（更快）"""
    from src.pipeline import ReportPipeline

    logger.info("=" * 80)
    logger.info("测试：无外部研究模式")
    logger.info("=" * 80)

    try:
        pipeline = ReportPipeline(
            output_base="outputs/test_pipeline_no_research",
            enable_image_analysis=True,
            enable_research=False,  # 禁用外部研究
            analyzer_model="claude-sonnet-4-5-20250929",
            generator_model="claude-sonnet-4-5-20250929",
        )

        output_dir = pipeline.run(pdf_path)

        logger.info(f"\n测试成功！输出: {output_dir}")
        return True

    except Exception as e:
        logger.error(f"测试失败: {e}", exc_info=True)
        return False


def test_minimal_pipeline(pdf_path: str = DEFAULT_PDF):
    """测试最小配置（无图片分析，无外部研究）"""
    from src.pipeline import ReportPipeline

    logger.info("=" * 80)
    logger.info("测试：最小配置模式")
    logger.info("=" * 80)

    try:
        pipeline = ReportPipeline(
            output_base="outputs/test_pipeline_minimal",
            enable_image_analysis=False,  # 禁用图片分析
            enable_research=False,  # 禁用外部研究
            analyzer_model="gemini-2.5-flash-lite-preview-09-2025",  # CloseAI Gemini 分析
            generator_model="gemini-2.5-flash-lite-preview-09-2025",  # CloseAI Gemini 生成
        )

        output_dir = pipeline.run(pdf_path)

        logger.info(f"\n测试成功！输出: {output_dir}")
        return True

    except Exception as e:
        logger.error(f"测试失败: {e}", exc_info=True)
        return False


def main():
    """主测试函数"""
    import argparse

    parser = argparse.ArgumentParser(description="测试报告生成流水线")
    parser.add_argument(
        "--mode",
        choices=["full", "no-research", "minimal"],
        default="full",
        help="测试模式",
    )
    parser.add_argument(
        "pdf",
        nargs="?",
        default=DEFAULT_PDF,
        help=f"待解析的 PDF 路径（默认 {DEFAULT_PDF}，亦可通过环境变量 PIPELINE_TEST_PDF 配置）",
    )

    args = parser.parse_args()

    if args.mode == "full":
        success = test_full_pipeline(args.pdf)
    elif args.mode == "no-research":
        success = test_without_research(args.pdf)
    else:
        success = test_minimal_pipeline(args.pdf)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
