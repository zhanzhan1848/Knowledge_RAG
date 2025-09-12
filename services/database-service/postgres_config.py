# -*- coding: utf-8 -*-
"""
PostgreSQL数据库配置和连接管理模块

提供PostgreSQL数据库的连接池管理、性能优化配置、
健康检查和监控功能。

Author: Knowledge RAG System
Date: 2025-01-16
"""

import os
import asyncio
import logging
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
    AsyncEngine
)
from sqlalchemy.pool import QueuePool
from sqlalchemy import text, event
from sqlalchemy.engine import Engine
import psycopg2
from psycopg2 import pool

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PostgreSQLConfig:
    """
    PostgreSQL数据库配置类
    
    管理数据库连接参数、连接池配置和性能优化设置。
    """
    
    def __init__(self):
        """初始化PostgreSQL配置"""
        self.host = os.getenv('POSTGRES_HOST', 'localhost')
        self.port = int(os.getenv('POSTGRES_PORT', 5432))
        self.username = os.getenv('POSTGRES_USER', 'postgres')
        self.password = os.getenv('POSTGRES_PASSWORD', 'postgres123')
        self.database = os.getenv('POSTGRES_DB', 'knowledge_rag')
        
        # 连接池配置
        self.pool_size = int(os.getenv('POSTGRES_POOL_SIZE', 20))
        self.max_overflow = int(os.getenv('POSTGRES_MAX_OVERFLOW', 30))
        self.pool_timeout = int(os.getenv('POSTGRES_POOL_TIMEOUT', 30))
        self.pool_recycle = int(os.getenv('POSTGRES_POOL_RECYCLE', 3600))
        
        # 性能优化配置
        self.echo = os.getenv('POSTGRES_ECHO', 'false').lower() == 'true'
        self.echo_pool = os.getenv('POSTGRES_ECHO_POOL', 'false').lower() == 'true'
        
    def get_database_url(self, database_name: Optional[str] = None) -> str:
        """
        获取数据库连接URL
        
        Args:
            database_name: 数据库名称，如果不提供则使用默认数据库
            
        Returns:
            str: 数据库连接URL
        """
        db_name = database_name or self.database
        return f"postgresql+asyncpg://{self.username}:{self.password}@{self.host}:{self.port}/{db_name}"
    
    def get_sync_database_url(self, database_name: Optional[str] = None) -> str:
        """
        获取同步数据库连接URL
        
        Args:
            database_name: 数据库名称
            
        Returns:
            str: 同步数据库连接URL
        """
        db_name = database_name or self.database
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{db_name}"

class PostgreSQLManager:
    """
    PostgreSQL数据库管理器
    
    提供数据库连接池管理、会话管理和健康检查功能。
    """
    
    def __init__(self, config: PostgreSQLConfig):
        """初始化PostgreSQL管理器"""
        self.config = config
        self.engines: Dict[str, AsyncEngine] = {}
        self.session_makers: Dict[str, async_sessionmaker] = {}
        self._connection_pool = None
        
    async def initialize(self, databases: list = None):
        """
        初始化数据库连接
        
        Args:
            databases: 要初始化的数据库列表
        """
        if databases is None:
            databases = ['knowledge_rag', 'auth_db', 'document_db', 'vector_db', 'knowledge_graph_db']
            
        for db_name in databases:
            await self._create_engine(db_name)
            
        logger.info(f"PostgreSQL管理器初始化完成，已连接数据库: {list(self.engines.keys())}")
    
    async def _create_engine(self, database_name: str):
        """
        创建数据库引擎
        
        Args:
            database_name: 数据库名称
        """
        database_url = self.config.get_database_url(database_name)
        
        # 创建异步引擎
        engine = create_async_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=self.config.pool_size,
            max_overflow=self.config.max_overflow,
            pool_timeout=self.config.pool_timeout,
            pool_recycle=self.config.pool_recycle,
            echo=self.config.echo,
            echo_pool=self.config.echo_pool,
            future=True
        )
        
        # 添加连接事件监听器
        @event.listens_for(engine.sync_engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            """设置连接参数"""
            if hasattr(dbapi_connection, 'set_session'):
                dbapi_connection.set_session(autocommit=False)
        
        self.engines[database_name] = engine
        
        # 创建会话工厂
        session_maker = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        self.session_makers[database_name] = session_maker
        
        logger.info(f"数据库引擎创建成功: {database_name}")
    
    @asynccontextmanager
    async def get_session(self, database_name: str = 'knowledge_rag'):
        """
        获取数据库会话上下文管理器
        
        Args:
            database_name: 数据库名称
            
        Yields:
            AsyncSession: 数据库会话
        """
        if database_name not in self.session_makers:
            raise ValueError(f"数据库 {database_name} 未初始化")
            
        async with self.session_makers[database_name]() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error(f"数据库会话错误: {e}")
                raise
    
    async def health_check(self, database_name: str = 'knowledge_rag') -> bool:
        """
        数据库健康检查
        
        Args:
            database_name: 数据库名称
            
        Returns:
            bool: 健康状态
        """
        try:
            async with self.get_session(database_name) as session:
                result = await session.execute(text("SELECT 1"))
                return result.scalar() == 1
        except Exception as e:
            logger.error(f"数据库健康检查失败 {database_name}: {e}")
            return False
    
    async def get_connection_info(self, database_name: str = 'knowledge_rag') -> Dict[str, Any]:
        """
        获取连接池信息
        
        Args:
            database_name: 数据库名称
            
        Returns:
            Dict[str, Any]: 连接池信息
        """
        if database_name not in self.engines:
            return {}
            
        engine = self.engines[database_name]
        pool = engine.pool
        
        return {
            'database': database_name,
            'pool_size': pool.size(),
            'checked_in': pool.checkedin(),
            'checked_out': pool.checkedout(),
            'overflow': pool.overflow(),
            'invalid': pool.invalid()
        }
    
    async def close_all(self):
        """
        关闭所有数据库连接
        """
        for database_name, engine in self.engines.items():
            await engine.dispose()
            logger.info(f"数据库连接已关闭: {database_name}")
        
        self.engines.clear()
        self.session_makers.clear()

# 全局PostgreSQL管理器实例
postgres_config = PostgreSQLConfig()
postgres_manager = PostgreSQLManager(postgres_config)

# 便捷函数
async def get_postgres_session(database_name: str = 'knowledge_rag'):
    """
    获取PostgreSQL数据库会话
    
    Args:
        database_name: 数据库名称
        
    Returns:
        AsyncSession: 数据库会话上下文管理器
    """
    return postgres_manager.get_session(database_name)

async def postgres_health_check(database_name: str = 'knowledge_rag') -> bool:
    """
    PostgreSQL健康检查
    
    Args:
        database_name: 数据库名称
        
    Returns:
        bool: 健康状态
    """
    return await postgres_manager.health_check(database_name)