#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
llm-service 主模块

该模块实现了大语言模型服务的主要功能，包括模型加载、推理和管理等。
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
import os

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="LLM Service API",
    description="API for large language model inference and management",
    version="0.1.0",
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该限制来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """根路径响应"""
    return {"message": "Welcome to LLM Service API"}


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy", "service": "llm-service"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)