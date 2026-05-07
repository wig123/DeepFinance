"""FastAPI 主应用入口"""

from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import citations, files, projects, reports, qa
from src.api.websocket.progress import router as ws_router

# 加载环境变量
env_path = Path(__file__).parents[2] / ".env"
load_dotenv(env_path)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    print("DeepFinance API 启动中...")
    yield
    # 关闭时
    print("DeepFinance API 已关闭")


app = FastAPI(
    title="DeepFinance API",
    description="基于长上下文LLM的金融文档分析与深度研究报告生成系统",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(projects.router, prefix="/api/projects", tags=["项目管理"])
app.include_router(reports.router, prefix="/api/projects", tags=["报告查看"])
app.include_router(citations.router, prefix="/api/projects", tags=["引用查询"])
app.include_router(files.router, prefix="/api/projects", tags=["文件服务"])
app.include_router(qa.router, prefix="/api/projects", tags=["报告问答"])
app.include_router(ws_router, tags=["WebSocket"])


@app.get("/")
async def root():
    """根路由"""
    return {
        "name": "DeepFinance API",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "healthy"}
