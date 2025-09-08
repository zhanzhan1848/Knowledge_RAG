#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GraphRAG服务依赖注入模块

该模块定义了GraphRAG服务的依赖注入功能，包括：
- 服务实例的创建和管理
- 生命周期管理
- 配置设置获取
- 服务状态管理

Author: Knowledge RAG Team
Date: 2024
"""

import asyncio
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager
from datetime import datetime

from app.core.config import Settings, get_settings
from app.services.graphrag_manager import GraphRAGManager
from app.services.neo4j_manager import Neo4jManager
from shared.utils.logger import get_logger
from shared.utils.metrics import MetricsCollector

logger = get_logger(__name__)
metrics = MetricsCollector()


class ServiceManager:
    """服务管理器，负责管理所有服务实例的生命周期"""
    
    def __init__(self):
        """初始化服务管理器"""
        self._graphrag_manager: Optional[GraphRAGManager] = None
        self._neo4j_manager: Optional[Neo4jManager] = None
        self._settings: Optional[Settings] = None
        self._initialized = False
        self._lock = asyncio.Lock()
        
        logger.info("服务管理器初始化完成")
    
    async def initialize(self):
        """初始化所有服务"""
        async with self._lock:
            if self._initialized:
                return
            
            try:
                logger.info("开始初始化GraphRAG服务...")
                
                # 获取配置
                self._settings = get_settings()
                
                # 初始化Neo4j管理器
                logger.info("初始化Neo4j管理器...")
                self._neo4j_manager = Neo4jManager()
                neo4j_connected = await self._neo4j_manager.connect()
                
                if not neo4j_connected:
                    logger.warning("Neo4j连接失败，图数据库功能将不可用")
                else:
                    logger.info("Neo4j管理器初始化成功")
                
                # 初始化GraphRAG管理器
                logger.info("初始化GraphRAG管理器...")
                self._graphrag_manager = GraphRAGManager()
                graphrag_initialized = await self._graphrag_manager.initialize()
                
                if not graphrag_initialized:
                    logger.warning("GraphRAG管理器初始化失败")
                else:
                    logger.info("GraphRAG管理器初始化成功")
                
                self._initialized = True
                metrics.increment("service_initializations")
                logger.info("GraphRAG服务初始化完成")
                
            except Exception as e:
                logger.error(f"服务初始化失败: {e}")
                metrics.increment("service_initialization_failures")
                raise
    
    async def cleanup(self):
        """清理所有服务资源"""
        async with self._lock:
            if not self._initialized:
                return
            
            try:
                logger.info("开始清理GraphRAG服务资源...")
                
                # 清理GraphRAG管理器
                if self._graphrag_manager:
                    try:
                        await self._graphrag_manager.cleanup()
                        logger.info("GraphRAG管理器资源清理完成")
                    except Exception as e:
                        logger.error(f"清理GraphRAG管理器失败: {e}")
                    finally:
                        self._graphrag_manager = None
                
                # 清理Neo4j管理器
                if self._neo4j_manager:
                    try:
                        await self._neo4j_manager.close()
                        logger.info("Neo4j管理器资源清理完成")
                    except Exception as e:
                        logger.error(f"清理Neo4j管理器失败: {e}")
                    finally:
                        self._neo4j_manager = None
                
                self._initialized = False
                metrics.increment("service_cleanups")
                logger.info("GraphRAG服务资源清理完成")
                
            except Exception as e:
                logger.error(f"服务资源清理失败: {e}")
                metrics.increment("service_cleanup_failures")
    
    def get_graphrag_manager(self) -> Optional[GraphRAGManager]:
        """获取GraphRAG管理器实例"""
        if not self._initialized:
            logger.warning("服务未初始化，无法获取GraphRAG管理器")
            return None
        return self._graphrag_manager
    
    def get_neo4j_manager(self) -> Optional[Neo4jManager]:
        """获取Neo4j管理器实例"""
        if not self._initialized:
            logger.warning("服务未初始化，无法获取Neo4j管理器")
            return None
        return self._neo4j_manager
    
    def get_settings(self) -> Optional[Settings]:
        """获取配置设置"""
        return self._settings or get_settings()
    
    def is_initialized(self) -> bool:
        """检查服务是否已初始化"""
        return self._initialized
    
    async def health_check(self) -> Dict[str, Any]:
        """服务健康检查"""
        try:
            if not self._initialized:
                return {
                    "healthy": False,
                    "message": "服务未初始化",
                    "timestamp": datetime.now().isoformat()
                }
            
            health_status = {
                "healthy": True,
                "services": {},
                "timestamp": datetime.now().isoformat()
            }
            
            # 检查GraphRAG管理器
            if self._graphrag_manager:
                graphrag_health = await self._graphrag_manager.health_check()
                health_status["services"]["graphrag"] = graphrag_health
                if not graphrag_health.get("healthy", False):
                    health_status["healthy"] = False
            else:
                health_status["services"]["graphrag"] = {
                    "healthy": False,
                    "message": "GraphRAG管理器未初始化"
                }
                health_status["healthy"] = False
            
            # 检查Neo4j管理器
            if self._neo4j_manager:
                neo4j_health = await self._neo4j_manager.health_check()
                health_status["services"]["neo4j"] = neo4j_health
                if not neo4j_health.get("healthy", False):
                    health_status["healthy"] = False
            else:
                health_status["services"]["neo4j"] = {
                    "healthy": False,
                    "message": "Neo4j管理器未初始化"
                }
                health_status["healthy"] = False
            
            return health_status
            
        except Exception as e:
            logger.error(f"健康检查失败: {e}")
            return {
                "healthy": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


# 全局服务管理器实例
_service_manager: Optional[ServiceManager] = None


def get_service_manager() -> ServiceManager:
    """获取服务管理器实例"""
    global _service_manager
    if _service_manager is None:
        _service_manager = ServiceManager()
    return _service_manager


@asynccontextmanager
async def lifespan_context():
    """应用生命周期上下文管理器"""
    service_manager = get_service_manager()
    
    try:
        # 启动时初始化服务
        await service_manager.initialize()
        logger.info("应用启动完成")
        yield service_manager
    finally:
        # 关闭时清理资源
        await service_manager.cleanup()
        logger.info("应用关闭完成")


# ==================== 依赖注入函数 ====================

async def get_graphrag_manager() -> GraphRAGManager:
    """获取GraphRAG管理器依赖"""
    service_manager = get_service_manager()
    
    if not service_manager.is_initialized():
        await service_manager.initialize()
    
    graphrag_manager = service_manager.get_graphrag_manager()
    
    if graphrag_manager is None:
        logger.error("GraphRAG管理器未初始化")
        raise RuntimeError("GraphRAG管理器未初始化")
    
    return graphrag_manager


async def get_neo4j_manager() -> Neo4jManager:
    """获取Neo4j管理器依赖"""
    service_manager = get_service_manager()
    
    if not service_manager.is_initialized():
        await service_manager.initialize()
    
    neo4j_manager = service_manager.get_neo4j_manager()
    
    if neo4j_manager is None:
        logger.error("Neo4j管理器未初始化")
        raise RuntimeError("Neo4j管理器未初始化")
    
    return neo4j_manager


def get_config_settings() -> Settings:
    """获取配置设置依赖"""
    service_manager = get_service_manager()
    settings = service_manager.get_settings()
    
    if settings is None:
        logger.error("配置设置未初始化")
        raise RuntimeError("配置设置未初始化")
    
    return settings


async def get_service_status() -> Dict[str, Any]:
    """获取服务状态依赖"""
    service_manager = get_service_manager()
    
    return {
        "initialized": service_manager.is_initialized(),
        "timestamp": datetime.now().isoformat(),
        "health": await service_manager.health_check()
    }


# ==================== 初始化和清理函数 ====================

async def initialize_services():
    """初始化所有服务"""
    service_manager = get_service_manager()
    await service_manager.initialize()


async def cleanup_services():
    """清理所有服务资源"""
    service_manager = get_service_manager()
    await service_manager.cleanup()


# ==================== 健康检查函数 ====================

async def check_service_health() -> Dict[str, Any]:
    """检查服务健康状态"""
    service_manager = get_service_manager()
    return await service_manager.health_check()


# ==================== 服务重启函数 ====================

async def restart_services():
    """重启所有服务"""
    try:
        logger.info("开始重启GraphRAG服务...")
        
        # 清理现有服务
        await cleanup_services()
        
        # 重新初始化服务
        await initialize_services()
        
        logger.info("GraphRAG服务重启完成")
        metrics.increment("service_restarts")
        
    except Exception as e:
        logger.error(f"服务重启失败: {e}")
        metrics.increment("service_restart_failures")
        raise


# 导出
__all__ = [
    'ServiceManager',
    'get_service_manager',
    'lifespan_context',
    'get_graphrag_manager',
    'get_neo4j_manager',
    'get_config_settings',
    'get_service_status',
    'initialize_services',
    'cleanup_services',
    'check_service_health',
    'restart_services'
]