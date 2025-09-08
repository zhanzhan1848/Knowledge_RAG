#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
向量服务主应用模块

该模块提供向量数据库的统一接口，支持多种向量数据库：
- ChromaDB
- FAISS
- Weaviate

Author: Knowledge RAG Team
Date: 2024
"""

import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

import uvicorn
from app.api.v1 import embeddings, search, vectors
from app.core.config import settings
from app.core.exceptions import VectorServiceException
from app.core.logging import setup_logging
from app.services.vector_manager import VectorManager
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from shared.middleware.auth import AuthMiddleware
from shared.middleware.metrics import MetricsMiddleware
from shared.middleware.rate_limit import RateLimitMiddleware
from shared.utils.health import HealthChecker

# 设置日志
setup_logging()
logger = logging.getLogger(__name__)

# 全局向量管理器
vector_manager: Optional[VectorManager] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global vector_manager

    # 启动时初始化
    logger.info("正在启动向量服务...")
    try:
        vector_manager = VectorManager()
        await vector_manager.initialize()
        logger.info("向量服务启动成功")
        yield
    except Exception as e:
        logger.error(f"向量服务启动失败: {e}")
        raise
    finally:
        # 关闭时清理
        if vector_manager:
            await vector_manager.cleanup()
        logger.info("向量服务已关闭")


# 创建 FastAPI 应用
app = FastAPI(
    title="Knowledge RAG - 向量服务",
    description="提供向量存储、检索和相似性搜索功能",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# 添加中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(AuthMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(MetricsMiddleware)


# 依赖注入
def get_vector_manager() -> VectorManager:
    """获取向量管理器实例"""
    if vector_manager is None:
        raise HTTPException(status_code=503, detail="向量服务未初始化")
    return vector_manager


# 异常处理
@app.exception_handler(VectorServiceException)
async def vector_service_exception_handler(request, exc: VectorServiceException):
    """向量服务异常处理"""
    logger.error(f"向量服务异常: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "type": "VectorServiceError"},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """通用异常处理"""
    logger.error(f"未处理的异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "内部服务器错误", "type": "InternalServerError"},
    )


# 健康检查
@app.get("/health")
async def health_check():
    """健康检查端点"""
    health_checker = HealthChecker()

    # 检查向量管理器状态
    vector_status = (
        "healthy"
        if vector_manager and await vector_manager.health_check()
        else "unhealthy"
    )

    health_status = {
        "status": "healthy" if vector_status == "healthy" else "unhealthy",
        "timestamp": health_checker.get_timestamp(),
        "version": "1.0.0",
        "components": {
            "vector_manager": vector_status,
            "database": await health_checker.check_database(),
            "redis": await health_checker.check_redis(),
        },
    }

    status_code = 200 if health_status["status"] == "healthy" else 503
    return JSONResponse(content=health_status, status_code=status_code)


@app.get("/metrics")
async def metrics():
    """指标端点"""
    if not vector_manager:
        raise HTTPException(status_code=503, detail="向量服务未初始化")

    metrics_data = await vector_manager.get_metrics()
    return JSONResponse(content=metrics_data)


# 注册路由
app.include_router(vectors.router, prefix="/api/v1/vectors", tags=["向量管理"])
app.include_router(embeddings.router, prefix="/api/v1/embeddings", tags=["嵌入向量"])
app.include_router(search.router, prefix="/api/v1/search", tags=["向量搜索"])


# 根路径
@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "Knowledge RAG - 向量服务",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs" if settings.DEBUG else "disabled",
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app", host="0.0.0.0", port=8003, reload=settings.DEBUG, log_level="info"
    )
