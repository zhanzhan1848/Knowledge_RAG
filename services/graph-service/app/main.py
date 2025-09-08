#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GraphRAG服务主应用模块

该模块是GraphRAG服务的入口点，基于FastAPI构建，提供：
- 知识图谱构建和管理
- 图谱查询和推理
- 实体关系提取
- 社区检测和摘要
- GraphRAG查询处理

Author: Knowledge RAG Team
Date: 2024
"""

import asyncio
import logging
import sys
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi

from app.core.config import settings
from app.core.dependencies import service_manager
from app.api.routes import router
from shared.middleware.logging import LoggingMiddleware
from shared.middleware.metrics import MetricsMiddleware
from shared.middleware.security import SecurityMiddleware
from shared.utils.logger import setup_logging
from shared.utils.metrics import MetricsCollector

# 设置日志
setup_logging()
logger = logging.getLogger(__name__)

# 指标收集器
metrics_collector = MetricsCollector()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("GraphRAG服务启动中...")
    
    try:
        # 初始化服务
        await service_manager.startup()
        
        # 记录启动指标
        metrics_collector.increment("service_startups")
        
        logger.info(f"GraphRAG服务启动成功，监听端口: {settings.PORT}")
        
        yield
        
    except Exception as e:
        logger.error(f"GraphRAG服务启动失败: {e}")
        metrics_collector.increment("service_startup_failures")
        raise
    
    finally:
        # 关闭时执行
        logger.info("GraphRAG服务关闭中...")
        
        try:
            await service_manager.shutdown()
            metrics_collector.increment("service_shutdowns")
            logger.info("GraphRAG服务关闭完成")
        except Exception as e:
            logger.error(f"GraphRAG服务关闭异常: {e}")


# 创建FastAPI应用
app = FastAPI(
    title="Knowledge RAG - GraphRAG Service",
    description="基于GraphRAG的知识图谱服务，提供图谱构建、查询和推理功能",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan
)


# 添加中间件
if settings.ENABLE_CORS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# 启用Gzip压缩
app.add_middleware(GZipMiddleware, minimum_size=1000)

# 添加自定义中间件
app.add_middleware(SecurityMiddleware)
app.add_middleware(MetricsMiddleware, metrics_collector=metrics_collector)
app.add_middleware(LoggingMiddleware)


# 全局异常处理器
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP异常处理器"""
    metrics_collector.increment(f"http_errors_{exc.status_code}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "type": "HTTPException"
            },
            "timestamp": metrics_collector.get_current_timestamp()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理器"""
    logger.error(f"未处理的异常: {exc}", exc_info=True)
    metrics_collector.increment("unhandled_exceptions")
    
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": 500,
                "message": "内部服务器错误" if not settings.DEBUG else str(exc),
                "type": "InternalServerError"
            },
            "timestamp": metrics_collector.get_current_timestamp()
        }
    )


# 注册路由
app.include_router(router)


# 根路径
@app.get("/")
async def root():
    """根路径处理器"""
    return {
        "service": "graph-service",
        "version": "1.0.0",
        "description": "Knowledge RAG GraphRAG服务",
        "status": "running",
        "docs_url": "/docs" if settings.DEBUG else None,
        "health_url": "/api/v1/health",
        "metrics_url": "/api/v1/metrics"
    }


# 健康检查端点
@app.get("/health")
async def health_check():
    """简单健康检查"""
    try:
        # 检查服务状态
        status = await service_manager.get_status()
        
        is_healthy = (
            status.get("manager_initialized", False) and
            all(
                service.get("healthy", False) 
                for service in status.get("services", {}).values()
            )
        )
        
        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "timestamp": metrics_collector.get_current_timestamp(),
            "service": "graph-service",
            "version": "1.0.0"
        }
        
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": metrics_collector.get_current_timestamp(),
            "service": "graph-service",
            "version": "1.0.0"
        }


# 指标端点
@app.get("/metrics")
async def get_metrics():
    """获取服务指标"""
    try:
        return {
            "metrics": metrics_collector.get_metrics(),
            "timestamp": metrics_collector.get_current_timestamp(),
            "service": "graph-service"
        }
    except Exception as e:
        logger.error(f"获取指标失败: {e}")
        raise HTTPException(status_code=500, detail="获取指标失败")


# 自定义OpenAPI文档
if settings.DEBUG:
    def custom_openapi():
        """自定义OpenAPI规范"""
        if app.openapi_schema:
            return app.openapi_schema
        
        openapi_schema = get_openapi(
            title="Knowledge RAG - GraphRAG Service API",
            version="1.0.0",
            description="基于GraphRAG的知识图谱服务API文档",
            routes=app.routes,
        )
        
        # 添加自定义信息
        openapi_schema["info"]["x-logo"] = {
            "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
        }
        
        app.openapi_schema = openapi_schema
        return app.openapi_schema
    
    app.openapi = custom_openapi


# 启动函数
def start_server():
    """启动服务器"""
    import uvicorn
    
    # 配置uvicorn
    config = uvicorn.Config(
        app=app,
        host=settings.HOST,
        port=settings.PORT,
        log_level=settings.LOG_LEVEL.lower(),
        reload=settings.DEBUG,
        workers=1 if settings.DEBUG else settings.WORKERS,
        access_log=settings.ACCESS_LOG,
        use_colors=True,
        server_header=False,
        date_header=False
    )
    
    server = uvicorn.Server(config)
    
    try:
        logger.info(f"启动GraphRAG服务: http://{settings.HOST}:{settings.PORT}")
        server.run()
    except KeyboardInterrupt:
        logger.info("收到中断信号，正在关闭服务...")
    except Exception as e:
        logger.error(f"服务启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    start_server()


# 导出应用实例
__all__ = ['app', 'start_server']