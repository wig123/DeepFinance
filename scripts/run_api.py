#!/usr/bin/env python
"""DeepFinance API 启动脚本"""

import argparse
import logging

import uvicorn


def setup_logging(level: str = "INFO"):
    """配置日志"""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def main():
    parser = argparse.ArgumentParser(description="DeepFinance API 服务器")
    parser.add_argument("--host", default="0.0.0.0", help="主机地址 (默认: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8001, help="端口 (默认: 8001)")
    parser.add_argument("--reload", action="store_true", help="开发模式，自动重载")
    parser.add_argument("--log-level", default="info", help="日志级别 (默认: info)")

    args = parser.parse_args()

    setup_logging(args.log_level)

    print(f"""
╔═══════════════════════════════════════════════════════════════╗
║                    DeepFinance API Server                     ║
╠═══════════════════════════════════════════════════════════════╣
║  API 文档:    http://{args.host}:{args.port}/docs                       ║
║  健康检查:    http://{args.host}:{args.port}/health                     ║
║  WebSocket:   ws://{args.host}:{args.port}/ws/projects/{{project_id}}    ║
╚═══════════════════════════════════════════════════════════════╝
    """)

    uvicorn.run(
        "src.api.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level,
    )


if __name__ == "__main__":
    main()
