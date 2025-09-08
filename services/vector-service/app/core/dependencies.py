#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
依赖注入模块

该模块定义了向量服务的依赖注入函数，用于：
- 管理服务实例的生命周期
- 提供单例模式的服务实例
- 处理服务初始化和清理

Author: Knowledge RAG Team
Date: 2024
"""

import logging
from typing import Optional
from functools import lru_cache

from fastapi import Depends, HTTPException

from app.services.vector_manager import VectorManager
from app.services.embedding_service import EmbeddingService
from app.core.config import settings

logger = logging.getLogger(__name__)

# 全局服务实例
_vector_manager: Optional[VectorManager] = None
_embedding_service: Optional[EmbeddingService] = None


async def initialize_services():
    """初始化所有服务"""
    global _vector_manager, _embedding_service

    try:
        logger.info("开始初始化向量服务依赖...")

        # 初始化嵌入服务
        if _embedding_service is None:
            _embedding_service = EmbeddingService()
            await _embedding_service.initialize()
            logger.info("嵌入服务初始化完成")

        # 初始化向量管理器
        if _vector_manager is None:
            _vector_manager = VectorManager()
            await _vector_manager.initialize()
            logger.info("向量管理器初始化完成")

        logger.info("所有向量服务依赖初始化完成")

    except Exception as e:
        logger.error(f"服务初始化失败: {e}")
        raise


async def cleanup_services():
    """清理所有服务"""
    global _vector_manager, _embedding_service

    try:
        logger.info("开始清理向量服务依赖...")

        # 清理向量管理器
        if _vector_manager:
            await _vector_manager.cleanup()
            _vector_manager = None
            logger.info("向量管理器清理完成")

        # 清理嵌入服务
        if _embedding_service:
            await _embedding_service.cleanup()
            _embedding_service = None
            logger.info("嵌入服务清理完成")

        logger.info("所有向量服务依赖清理完成")

    except Exception as e:
        logger.error(f"服务清理失败: {e}")


async def get_vector_manager() -> VectorManager:
    """获取向量管理器实例"""
    global _vector_manager

    if _vector_manager is None:
        logger.error("向量管理器未初始化")
        raise HTTPException(status_code=503, detail="向量管理器服务不可用，请稍后重试")

    # 检查服务健康状态
    if not await _vector_manager.health_check():
        logger.error("向量管理器健康检查失败")
        raise HTTPException(status_code=503, detail="向量管理器服务不健康，请稍后重试")

    return _vector_manager


async def get_embedding_service() -> EmbeddingService:
    """获取嵌入服务实例"""
    global _embedding_service

    if _embedding_service is None:
        logger.error("嵌入服务未初始化")
        raise HTTPException(status_code=503, detail="嵌入服务不可用，请稍后重试")

    # 检查服务健康状态
    if not await _embedding_service.health_check():
        logger.error("嵌入服务健康检查失败")
        raise HTTPException(status_code=503, detail="嵌入服务不健康，请稍后重试")

    return _embedding_service


@lru_cache()
def get_settings():
    """获取配置设置（缓存）"""
    return settings


async def get_service_status() -> dict:
    """获取所有服务状态"""
    global _vector_manager, _embedding_service

    status = {
        "vector_manager": {
            "initialized": _vector_manager is not None,
            "healthy": False,
        },
        "embedding_service": {
            "initialized": _embedding_service is not None,
            "healthy": False,
        },
    }

    # 检查向量管理器健康状态
    if _vector_manager:
        try:
            status["vector_manager"]["healthy"] = await _vector_manager.health_check()
        except Exception as e:
            logger.error(f"向量管理器健康检查异常: {e}")

    # 检查嵌入服务健康状态
    if _embedding_service:
        try:
            status["embedding_service"][
                "healthy"
            ] = await _embedding_service.health_check()
        except Exception as e:
            logger.error(f"嵌入服务健康检查异常: {e}")

    return status


class ServiceManager:
    """服务管理器类"""

    def __init__(self):
        """初始化服务管理器"""
        self.initialized = False

    async def startup(self):
        """启动服务"""
        if not self.initialized:
            await initialize_services()
            self.initialized = True
            logger.info("服务管理器启动完成")

    async def shutdown(self):
        """关闭服务"""
        if self.initialized:
            await cleanup_services()
            self.initialized = False
            logger.info("服务管理器关闭完成")

    async def restart(self):
        """重启服务"""
        logger.info("开始重启服务...")
        await self.shutdown()
        await self.startup()
        logger.info("服务重启完成")

    async def get_status(self) -> dict:
        """获取服务状态"""
        service_status = await get_service_status()
        return {"manager_initialized": self.initialized, "services": service_status}


# 全局服务管理器实例
service_manager = ServiceManager()


# 导出的公共接口
__all__ = [
    "get_vector_manager",
    "get_embedding_service",
    "get_settings",
    "get_service_status",
    "initialize_services",
    "cleanup_services",
    "service_manager",
    "ServiceManager",
]
