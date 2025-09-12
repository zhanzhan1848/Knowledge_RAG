# -*- coding: utf-8 -*-
"""
Neo4j图数据库配置和连接管理模块

提供Neo4j图数据库的连接管理、会话管理、
性能优化和监控功能。

Author: Knowledge RAG System
Date: 2025-01-16
"""

import os
import asyncio
import logging
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager
from neo4j import GraphDatabase, AsyncGraphDatabase
from neo4j.exceptions import ServiceUnavailable, AuthError
import time

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Neo4jConfig:
    """
    Neo4j图数据库配置类
    
    管理Neo4j连接参数、认证信息和性能优化设置。
    """
    
    def __init__(self):
        """初始化Neo4j配置"""
        self.uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
        self.username = os.getenv('NEO4J_USERNAME', 'neo4j')
        self.password = os.getenv('NEO4J_PASSWORD', 'neo4j123')
        self.database = os.getenv('NEO4J_DATABASE', 'neo4j')
        
        # 连接池配置
        self.max_connection_lifetime = int(os.getenv('NEO4J_MAX_CONNECTION_LIFETIME', 3600))
        self.max_connection_pool_size = int(os.getenv('NEO4J_MAX_CONNECTION_POOL_SIZE', 100))
        self.connection_acquisition_timeout = int(os.getenv('NEO4J_CONNECTION_ACQUISITION_TIMEOUT', 60))
        
        # 性能配置
        self.fetch_size = int(os.getenv('NEO4J_FETCH_SIZE', 1000))
        self.max_retry_time = int(os.getenv('NEO4J_MAX_RETRY_TIME', 30))
        
        # 安全配置
        self.encrypted = os.getenv('NEO4J_ENCRYPTED', 'false').lower() == 'true'
        self.trust = os.getenv('NEO4J_TRUST', 'TRUST_ALL_CERTIFICATES')

class Neo4jManager:
    """
    Neo4j图数据库管理器
    
    提供图数据库连接管理、会话管理和健康检查功能。
    """
    
    def __init__(self, config: Neo4jConfig):
        """初始化Neo4j管理器"""
        self.config = config
        self.driver = None
        self.async_driver = None
        self._is_connected = False
        
    async def initialize(self):
        """
        初始化Neo4j连接
        """
        try:
            # 创建异步驱动
            self.async_driver = AsyncGraphDatabase.driver(
                self.config.uri,
                auth=(self.config.username, self.config.password),
                max_connection_lifetime=self.config.max_connection_lifetime,
                max_connection_pool_size=self.config.max_connection_pool_size,
                connection_acquisition_timeout=self.config.connection_acquisition_timeout,
                encrypted=self.config.encrypted
            )
            
            # 创建同步驱动（用于某些操作）
            self.driver = GraphDatabase.driver(
                self.config.uri,
                auth=(self.config.username, self.config.password),
                max_connection_lifetime=self.config.max_connection_lifetime,
                max_connection_pool_size=self.config.max_connection_pool_size,
                connection_acquisition_timeout=self.config.connection_acquisition_timeout,
                encrypted=self.config.encrypted
            )
            
            # 验证连接
            await self._verify_connectivity()
            self._is_connected = True
            
            logger.info("Neo4j管理器初始化完成")
            
        except Exception as e:
            logger.error(f"Neo4j初始化失败: {e}")
            raise
    
    async def _verify_connectivity(self):
        """
        验证数据库连接
        """
        try:
            async with self.async_driver.session(database=self.config.database) as session:
                result = await session.run("RETURN 1 as test")
                record = await result.single()
                if record["test"] != 1:
                    raise Exception("连接验证失败")
        except Exception as e:
            logger.error(f"Neo4j连接验证失败: {e}")
            raise
    
    @asynccontextmanager
    async def get_session(self, database: Optional[str] = None):
        """
        获取Neo4j会话上下文管理器
        
        Args:
            database: 数据库名称
            
        Yields:
            AsyncSession: Neo4j会话
        """
        if not self._is_connected:
            raise Exception("Neo4j未连接")
            
        db_name = database or self.config.database
        
        async with self.async_driver.session(database=db_name) as session:
            try:
                yield session
            except Exception as e:
                logger.error(f"Neo4j会话错误: {e}")
                raise
    
    async def execute_query(self, query: str, parameters: Dict = None, database: Optional[str] = None) -> List[Dict]:
        """
        执行Cypher查询
        
        Args:
            query: Cypher查询语句
            parameters: 查询参数
            database: 数据库名称
            
        Returns:
            List[Dict]: 查询结果
        """
        async with self.get_session(database) as session:
            result = await session.run(query, parameters or {})
            return [record.data() for record in await result.data()]
    
    async def execute_write_query(self, query: str, parameters: Dict = None, database: Optional[str] = None) -> Dict:
        """
        执行写入查询
        
        Args:
            query: Cypher查询语句
            parameters: 查询参数
            database: 数据库名称
            
        Returns:
            Dict: 执行结果统计
        """
        async with self.get_session(database) as session:
            result = await session.run(query, parameters or {})
            summary = await result.consume()
            return {
                'nodes_created': summary.counters.nodes_created,
                'nodes_deleted': summary.counters.nodes_deleted,
                'relationships_created': summary.counters.relationships_created,
                'relationships_deleted': summary.counters.relationships_deleted,
                'properties_set': summary.counters.properties_set
            }
    
    async def health_check(self) -> bool:
        """
        Neo4j健康检查
        
        Returns:
            bool: 健康状态
        """
        try:
            async with self.get_session() as session:
                result = await session.run("RETURN 1 as health")
                record = await result.single()
                return record["health"] == 1
        except Exception as e:
            logger.error(f"Neo4j健康检查失败: {e}")
            return False
    
    async def get_database_info(self) -> Dict[str, Any]:
        """
        获取数据库信息
        
        Returns:
            Dict[str, Any]: 数据库信息
        """
        try:
            async with self.get_session() as session:
                # 获取节点和关系统计
                node_count_result = await session.run("MATCH (n) RETURN count(n) as node_count")
                node_count = (await node_count_result.single())["node_count"]
                
                rel_count_result = await session.run("MATCH ()-[r]->() RETURN count(r) as rel_count")
                rel_count = (await rel_count_result.single())["rel_count"]
                
                # 获取标签信息
                labels_result = await session.run("CALL db.labels()")
                labels = [record["label"] for record in await labels_result.data()]
                
                # 获取关系类型信息
                rel_types_result = await session.run("CALL db.relationshipTypes()")
                rel_types = [record["relationshipType"] for record in await rel_types_result.data()]
                
                return {
                    'node_count': node_count,
                    'relationship_count': rel_count,
                    'labels': labels,
                    'relationship_types': rel_types,
                    'database': self.config.database
                }
        except Exception as e:
            logger.error(f"获取Neo4j数据库信息失败: {e}")
            return {}
    
    async def create_indexes(self):
        """
        创建常用索引
        """
        indexes = [
            "CREATE INDEX entity_id_index IF NOT EXISTS FOR (n:Entity) ON (n.id)",
            "CREATE INDEX entity_name_index IF NOT EXISTS FOR (n:Entity) ON (n.name)",
            "CREATE INDEX document_id_index IF NOT EXISTS FOR (n:Document) ON (n.id)",
            "CREATE INDEX user_id_index IF NOT EXISTS FOR (n:User) ON (n.id)",
        ]
        
        for index_query in indexes:
            try:
                await self.execute_write_query(index_query)
                logger.info(f"索引创建成功: {index_query}")
            except Exception as e:
                logger.warning(f"索引创建失败: {index_query}, 错误: {e}")
    
    async def clear_database(self, database: Optional[str] = None):
        """
        清空数据库（谨慎使用）
        
        Args:
            database: 数据库名称
        """
        logger.warning("正在清空Neo4j数据库...")
        await self.execute_write_query("MATCH (n) DETACH DELETE n", database=database)
        logger.info("Neo4j数据库已清空")
    
    async def close(self):
        """
        关闭数据库连接
        """
        if self.async_driver:
            await self.async_driver.close()
        if self.driver:
            self.driver.close()
        
        self._is_connected = False
        logger.info("Neo4j连接已关闭")

# 全局Neo4j管理器实例
neo4j_config = Neo4jConfig()
neo4j_manager = Neo4jManager(neo4j_config)

# 便捷函数
async def get_neo4j_session(database: Optional[str] = None):
    """
    获取Neo4j数据库会话
    
    Args:
        database: 数据库名称
        
    Returns:
        AsyncSession: Neo4j会话上下文管理器
    """
    return neo4j_manager.get_session(database)

async def neo4j_health_check() -> bool:
    """
    Neo4j健康检查
    
    Returns:
        bool: 健康状态
    """
    return await neo4j_manager.health_check()

async def execute_cypher(query: str, parameters: Dict = None, database: Optional[str] = None) -> List[Dict]:
    """
    执行Cypher查询
    
    Args:
        query: Cypher查询语句
        parameters: 查询参数
        database: 数据库名称
        
    Returns:
        List[Dict]: 查询结果
    """
    return await neo4j_manager.execute_query(query, parameters, database)