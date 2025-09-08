#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Knowledge RAG System - 测试数据初始化脚本

该脚本用于初始化测试环境的数据，包括：
1. 数据库连接测试
2. Redis连接测试
3. Elasticsearch索引创建
4. Neo4j图数据库初始化
5. 测试数据插入和验证

作者: Knowledge RAG Team
创建时间: 2024-01-20
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import asyncpg
import redis.asyncio as redis
from elasticsearch import AsyncElasticsearch
from neo4j import AsyncGraphDatabase

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/tmp/test_data_init.log')
    ]
)
logger = logging.getLogger(__name__)


class TestDataInitializer:
    """
    测试数据初始化器
    
    负责初始化所有测试环境所需的数据和配置
    """
    
    def __init__(self):
        """初始化配置"""
        self.database_url = os.getenv('DATABASE_URL', 'postgresql+asyncpg://testuser:testpass123@postgres-test:5432/knowledge_rag_test')
        self.redis_url = os.getenv('REDIS_URL', 'redis://redis-test:6379/0')
        self.elasticsearch_url = os.getenv('ELASTICSEARCH_URL', 'http://elasticsearch-test:9200')
        self.neo4j_uri = os.getenv('NEO4J_URI', 'bolt://neo4j-test:7687')
        self.neo4j_user = os.getenv('NEO4J_USER', 'neo4j')
        self.neo4j_password = os.getenv('NEO4J_PASSWORD', 'testpass123')
        
        # 连接对象
        self.pg_pool: Optional[asyncpg.Pool] = None
        self.redis_client: Optional[redis.Redis] = None
        self.es_client: Optional[AsyncElasticsearch] = None
        self.neo4j_driver = None
    
    async def initialize_all(self) -> bool:
        """
        初始化所有测试数据
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            logger.info("🚀 开始初始化测试数据...")
            
            # 1. 建立数据库连接
            await self._setup_connections()
            
            # 2. 验证数据库连接
            await self._verify_connections()
            
            # 3. 初始化Elasticsearch索引
            await self._setup_elasticsearch_indices()
            
            # 4. 初始化Neo4j约束和索引
            await self._setup_neo4j_constraints()
            
            # 5. 插入额外的测试数据
            await self._insert_additional_test_data()
            
            # 6. 验证数据完整性
            await self._verify_test_data()
            
            logger.info("✅ 测试数据初始化完成！")
            return True
            
        except Exception as e:
            logger.error(f"❌ 测试数据初始化失败: {e}")
            return False
        finally:
            await self._cleanup_connections()
    
    async def _setup_connections(self):
        """建立数据库连接"""
        logger.info("📡 建立数据库连接...")
        
        # PostgreSQL连接
        try:
            # 从URL中提取连接参数
            import urllib.parse
            parsed = urllib.parse.urlparse(self.database_url.replace('postgresql+asyncpg://', 'postgresql://'))
            
            self.pg_pool = await asyncpg.create_pool(
                host=parsed.hostname,
                port=parsed.port or 5432,
                user=parsed.username,
                password=parsed.password,
                database=parsed.path.lstrip('/'),
                min_size=1,
                max_size=5
            )
            logger.info("✅ PostgreSQL连接建立成功")
        except Exception as e:
            logger.error(f"❌ PostgreSQL连接失败: {e}")
            raise
        
        # Redis连接
        try:
            self.redis_client = redis.from_url(self.redis_url)
            logger.info("✅ Redis连接建立成功")
        except Exception as e:
            logger.error(f"❌ Redis连接失败: {e}")
            raise
        
        # Elasticsearch连接
        try:
            self.es_client = AsyncElasticsearch([self.elasticsearch_url])
            logger.info("✅ Elasticsearch连接建立成功")
        except Exception as e:
            logger.error(f"❌ Elasticsearch连接失败: {e}")
            raise
        
        # Neo4j连接
        try:
            self.neo4j_driver = AsyncGraphDatabase.driver(
                self.neo4j_uri,
                auth=(self.neo4j_user, self.neo4j_password)
            )
            logger.info("✅ Neo4j连接建立成功")
        except Exception as e:
            logger.error(f"❌ Neo4j连接失败: {e}")
            raise
    
    async def _verify_connections(self):
        """验证数据库连接"""
        logger.info("🔍 验证数据库连接...")
        
        # 验证PostgreSQL
        async with self.pg_pool.acquire() as conn:
            result = await conn.fetchval('SELECT version()')
            logger.info(f"PostgreSQL版本: {result.split(',')[0]}")
        
        # 验证Redis
        await self.redis_client.ping()
        info = await self.redis_client.info()
        logger.info(f"Redis版本: {info['redis_version']}")
        
        # 验证Elasticsearch
        info = await self.es_client.info()
        logger.info(f"Elasticsearch版本: {info['version']['number']}")
        
        # 验证Neo4j
        async with self.neo4j_driver.session() as session:
            result = await session.run("CALL dbms.components() YIELD name, versions RETURN name, versions[0] as version")
            async for record in result:
                if record['name'] == 'Neo4j Kernel':
                    logger.info(f"Neo4j版本: {record['version']}")
                    break
    
    async def _setup_elasticsearch_indices(self):
        """设置Elasticsearch索引"""
        logger.info("📊 设置Elasticsearch索引...")
        
        # 文档索引映射
        document_mapping = {
            "mappings": {
                "properties": {
                    "id": {"type": "keyword"},
                    "title": {
                        "type": "text",
                        "analyzer": "ik_max_word",
                        "search_analyzer": "ik_smart"
                    },
                    "content": {
                        "type": "text",
                        "analyzer": "ik_max_word",
                        "search_analyzer": "ik_smart"
                    },
                    "description": {
                        "type": "text",
                        "analyzer": "ik_max_word",
                        "search_analyzer": "ik_smart"
                    },
                    "document_type": {"type": "keyword"},
                    "status": {"type": "keyword"},
                    "user_id": {"type": "keyword"},
                    "tags": {"type": "keyword"},
                    "language": {"type": "keyword"},
                    "created_at": {"type": "date"},
                    "updated_at": {"type": "date"},
                    "file_size": {"type": "long"},
                    "word_count": {"type": "integer"},
                    "character_count": {"type": "integer"}
                }
            },
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
                "analysis": {
                    "analyzer": {
                        "ik_max_word": {
                            "type": "standard"
                        },
                        "ik_smart": {
                            "type": "standard"
                        }
                    }
                }
            }
        }
        
        # 文档块索引映射
        chunk_mapping = {
            "mappings": {
                "properties": {
                    "id": {"type": "keyword"},
                    "document_id": {"type": "keyword"},
                    "chunk_index": {"type": "integer"},
                    "content": {
                        "type": "text",
                        "analyzer": "ik_max_word",
                        "search_analyzer": "ik_smart"
                    },
                    "embedding": {
                        "type": "dense_vector",
                        "dims": 1536
                    },
                    "token_count": {"type": "integer"},
                    "character_count": {"type": "integer"},
                    "page_number": {"type": "integer"},
                    "section_title": {"type": "text"},
                    "created_at": {"type": "date"}
                }
            },
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0
            }
        }
        
        # 创建索引
        indices = [
            ("documents", document_mapping),
            ("document_chunks", chunk_mapping)
        ]
        
        for index_name, mapping in indices:
            try:
                # 删除已存在的索引
                if await self.es_client.indices.exists(index=index_name):
                    await self.es_client.indices.delete(index=index_name)
                    logger.info(f"删除已存在的索引: {index_name}")
                
                # 创建新索引
                await self.es_client.indices.create(index=index_name, body=mapping)
                logger.info(f"✅ 创建索引成功: {index_name}")
                
            except Exception as e:
                logger.error(f"❌ 创建索引失败 {index_name}: {e}")
                raise
    
    async def _setup_neo4j_constraints(self):
        """设置Neo4j约束和索引"""
        logger.info("🔗 设置Neo4j约束和索引...")
        
        constraints_and_indices = [
            # 实体约束
            "CREATE CONSTRAINT entity_name_type IF NOT EXISTS FOR (e:Entity) REQUIRE (e.name, e.type) IS UNIQUE",
            "CREATE INDEX entity_name_index IF NOT EXISTS FOR (e:Entity) ON (e.name)",
            "CREATE INDEX entity_type_index IF NOT EXISTS FOR (e:Entity) ON (e.type)",
            
            # 文档约束
            "CREATE CONSTRAINT document_id IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE",
            "CREATE INDEX document_title_index IF NOT EXISTS FOR (d:Document) ON (d.title)",
            "CREATE INDEX document_type_index IF NOT EXISTS FOR (d:Document) ON (d.document_type)",
            
            # 用户约束
            "CREATE CONSTRAINT user_id IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE",
            "CREATE INDEX user_email_index IF NOT EXISTS FOR (u:User) ON (u.email)",
            
            # 关系索引
            "CREATE INDEX relationship_type_index IF NOT EXISTS FOR ()-[r:RELATES_TO]-() ON (r.type)",
            "CREATE INDEX relationship_confidence_index IF NOT EXISTS FOR ()-[r:RELATES_TO]-() ON (r.confidence)"
        ]
        
        async with self.neo4j_driver.session() as session:
            for constraint in constraints_and_indices:
                try:
                    await session.run(constraint)
                    logger.info(f"✅ 执行成功: {constraint[:50]}...")
                except Exception as e:
                    # 约束已存在的错误可以忽略
                    if "already exists" in str(e) or "equivalent" in str(e):
                        logger.info(f"⚠️ 约束已存在: {constraint[:50]}...")
                    else:
                        logger.error(f"❌ 执行失败: {constraint[:50]}... - {e}")
                        raise
    
    async def _insert_additional_test_data(self):
        """插入额外的测试数据"""
        logger.info("📝 插入额外的测试数据...")
        
        # 插入Redis测试数据
        await self._insert_redis_test_data()
        
        # 插入Elasticsearch测试数据
        await self._insert_elasticsearch_test_data()
        
        # 插入Neo4j测试数据
        await self._insert_neo4j_test_data()
    
    async def _insert_redis_test_data(self):
        """插入Redis测试数据"""
        logger.info("📦 插入Redis测试数据...")
        
        # 用户会话数据
        session_data = {
            "user_id": "550e8400-e29b-41d4-a716-446655440002",
            "username": "testuser1",
            "role": "user",
            "created_at": datetime.now().isoformat()
        }
        
        await self.redis_client.setex(
            "session:test_session_token_123",
            3600,  # 1小时过期
            json.dumps(session_data)
        )
        
        # 缓存测试数据
        cache_data = {
            "document_id": "660e8400-e29b-41d4-a716-446655440001",
            "title": "测试文档1",
            "content_preview": "这是测试文档的内容预览...",
            "cached_at": datetime.now().isoformat()
        }
        
        await self.redis_client.setex(
            "document:660e8400-e29b-41d4-a716-446655440001",
            1800,  # 30分钟过期
            json.dumps(cache_data)
        )
        
        # 限流测试数据
        await self.redis_client.setex(
            "rate_limit:user:550e8400-e29b-41d4-a716-446655440002",
            60,  # 1分钟过期
            "5"  # 已使用5次
        )
        
        logger.info("✅ Redis测试数据插入完成")
    
    async def _insert_elasticsearch_test_data(self):
        """插入Elasticsearch测试数据"""
        logger.info("🔍 插入Elasticsearch测试数据...")
        
        # 文档数据
        documents = [
            {
                "id": "660e8400-e29b-41d4-a716-446655440001",
                "title": "测试文档1",
                "content": "这是测试文档的内容，用于验证系统功能。包含人工智能、机器学习等相关概念。",
                "description": "这是一个测试文档",
                "document_type": "txt",
                "status": "completed",
                "user_id": "550e8400-e29b-41d4-a716-446655440002",
                "tags": ["测试", "AI", "机器学习"],
                "language": "zh",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "file_size": 1024,
                "word_count": 50,
                "character_count": 150
            },
            {
                "id": "660e8400-e29b-41d4-a716-446655440002",
                "title": "测试文档2",
                "content": "# 测试文档\n\n这是一个Markdown格式的测试文档，包含深度学习和神经网络的内容。",
                "description": "这是另一个测试文档",
                "document_type": "md",
                "status": "completed",
                "user_id": "550e8400-e29b-41d4-a716-446655440002",
                "tags": ["测试", "深度学习", "神经网络"],
                "language": "zh",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "file_size": 2048,
                "word_count": 80,
                "character_count": 200
            }
        ]
        
        # 批量插入文档
        for doc in documents:
            await self.es_client.index(
                index="documents",
                id=doc["id"],
                body=doc
            )
        
        # 文档块数据
        chunks = [
            {
                "id": "chunk_001",
                "document_id": "660e8400-e29b-41d4-a716-446655440001",
                "chunk_index": 0,
                "content": "这是测试文档的第一个块，包含人工智能相关内容。",
                "token_count": 25,
                "character_count": 75,
                "page_number": 1,
                "section_title": "引言",
                "created_at": datetime.now().isoformat()
            },
            {
                "id": "chunk_002",
                "document_id": "660e8400-e29b-41d4-a716-446655440001",
                "chunk_index": 1,
                "content": "机器学习是人工智能的一个重要分支，用于验证系统功能。",
                "token_count": 30,
                "character_count": 85,
                "page_number": 1,
                "section_title": "机器学习",
                "created_at": datetime.now().isoformat()
            }
        ]
        
        # 批量插入文档块
        for chunk in chunks:
            await self.es_client.index(
                index="document_chunks",
                id=chunk["id"],
                body=chunk
            )
        
        # 刷新索引
        await self.es_client.indices.refresh(index="documents")
        await self.es_client.indices.refresh(index="document_chunks")
        
        logger.info("✅ Elasticsearch测试数据插入完成")
    
    async def _insert_neo4j_test_data(self):
        """插入Neo4j测试数据"""
        logger.info("🕸️ 插入Neo4j测试数据...")
        
        async with self.neo4j_driver.session() as session:
            # 清除已存在的测试数据
            await session.run("MATCH (n) WHERE n.test_data = true DETACH DELETE n")
            
            # 创建用户节点
            await session.run("""
                CREATE (u1:User {
                    id: '550e8400-e29b-41d4-a716-446655440002',
                    username: 'testuser1',
                    email: 'user1@test.com',
                    full_name: '测试用户1',
                    test_data: true
                })
                CREATE (u2:User {
                    id: '550e8400-e29b-41d4-a716-446655440003',
                    username: 'testuser2',
                    email: 'user2@test.com',
                    full_name: '测试用户2',
                    test_data: true
                })
            """)
            
            # 创建文档节点
            await session.run("""
                CREATE (d1:Document {
                    id: '660e8400-e29b-41d4-a716-446655440001',
                    title: '测试文档1',
                    document_type: 'txt',
                    status: 'completed',
                    test_data: true
                })
                CREATE (d2:Document {
                    id: '660e8400-e29b-41d4-a716-446655440002',
                    title: '测试文档2',
                    document_type: 'md',
                    status: 'completed',
                    test_data: true
                })
            """)
            
            # 创建实体节点
            await session.run("""
                CREATE (e1:Entity {
                    id: '990e8400-e29b-41d4-a716-446655440001',
                    name: '人工智能',
                    type: 'CONCEPT',
                    description: '人工智能相关概念',
                    confidence: 0.95,
                    test_data: true
                })
                CREATE (e2:Entity {
                    id: '990e8400-e29b-41d4-a716-446655440002',
                    name: '机器学习',
                    type: 'CONCEPT',
                    description: '机器学习技术',
                    confidence: 0.90,
                    test_data: true
                })
                CREATE (e3:Entity {
                    id: '990e8400-e29b-41d4-a716-446655440003',
                    name: '深度学习',
                    type: 'CONCEPT',
                    description: '深度学习方法',
                    confidence: 0.88,
                    test_data: true
                })
            """)
            
            # 创建关系
            await session.run("""
                MATCH (u1:User {id: '550e8400-e29b-41d4-a716-446655440002'})
                MATCH (d1:Document {id: '660e8400-e29b-41d4-a716-446655440001'})
                MATCH (d2:Document {id: '660e8400-e29b-41d4-a716-446655440002'})
                CREATE (u1)-[:OWNS]->(d1)
                CREATE (u1)-[:OWNS]->(d2)
            """)
            
            await session.run("""
                MATCH (e1:Entity {name: '人工智能'})
                MATCH (e2:Entity {name: '机器学习'})
                MATCH (e3:Entity {name: '深度学习'})
                CREATE (e1)-[:INCLUDES {confidence: 0.92, test_data: true}]->(e2)
                CREATE (e2)-[:INCLUDES {confidence: 0.89, test_data: true}]->(e3)
            """)
            
            await session.run("""
                MATCH (d1:Document {id: '660e8400-e29b-41d4-a716-446655440001'})
                MATCH (e1:Entity {name: '人工智能'})
                MATCH (e2:Entity {name: '机器学习'})
                CREATE (d1)-[:MENTIONS {confidence: 0.85, test_data: true}]->(e1)
                CREATE (d1)-[:MENTIONS {confidence: 0.80, test_data: true}]->(e2)
            """)
        
        logger.info("✅ Neo4j测试数据插入完成")
    
    async def _verify_test_data(self):
        """验证测试数据完整性"""
        logger.info("🔍 验证测试数据完整性...")
        
        # 验证PostgreSQL数据
        async with self.pg_pool.acquire() as conn:
            user_count = await conn.fetchval("SELECT COUNT(*) FROM users")
            doc_count = await conn.fetchval("SELECT COUNT(*) FROM documents")
            msg_count = await conn.fetchval("SELECT COUNT(*) FROM messages")
            
            logger.info(f"PostgreSQL数据统计: 用户={user_count}, 文档={doc_count}, 消息={msg_count}")
            
            if user_count < 4 or doc_count < 3 or msg_count < 3:
                raise ValueError("PostgreSQL测试数据不完整")
        
        # 验证Redis数据
        session_exists = await self.redis_client.exists("session:test_session_token_123")
        cache_exists = await self.redis_client.exists("document:660e8400-e29b-41d4-a716-446655440001")
        
        logger.info(f"Redis数据统计: 会话存在={session_exists}, 缓存存在={cache_exists}")
        
        if not session_exists or not cache_exists:
            raise ValueError("Redis测试数据不完整")
        
        # 验证Elasticsearch数据
        doc_count = await self.es_client.count(index="documents")
        chunk_count = await self.es_client.count(index="document_chunks")
        
        logger.info(f"Elasticsearch数据统计: 文档={doc_count['count']}, 块={chunk_count['count']}")
        
        if doc_count['count'] < 2 or chunk_count['count'] < 2:
            raise ValueError("Elasticsearch测试数据不完整")
        
        # 验证Neo4j数据
        async with self.neo4j_driver.session() as session:
            result = await session.run("MATCH (n) WHERE n.test_data = true RETURN labels(n) as labels, count(n) as count")
            neo4j_stats = {}
            async for record in result:
                labels = record['labels']
                count = record['count']
                for label in labels:
                    if label != 'test_data':
                        neo4j_stats[label] = neo4j_stats.get(label, 0) + count
            
            logger.info(f"Neo4j数据统计: {neo4j_stats}")
            
            if neo4j_stats.get('User', 0) < 2 or neo4j_stats.get('Entity', 0) < 3:
                raise ValueError("Neo4j测试数据不完整")
        
        logger.info("✅ 测试数据验证通过")
    
    async def _cleanup_connections(self):
        """清理数据库连接"""
        logger.info("🧹 清理数据库连接...")
        
        try:
            if self.pg_pool:
                await self.pg_pool.close()
            
            if self.redis_client:
                await self.redis_client.close()
            
            if self.es_client:
                await self.es_client.close()
            
            if self.neo4j_driver:
                await self.neo4j_driver.close()
            
            logger.info("✅ 数据库连接清理完成")
        except Exception as e:
            logger.error(f"❌ 清理连接时出错: {e}")


async def main():
    """
    主函数
    """
    initializer = TestDataInitializer()
    
    try:
        success = await initializer.initialize_all()
        if success:
            logger.info("🎉 测试环境初始化成功！")
            sys.exit(0)
        else:
            logger.error("💥 测试环境初始化失败！")
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("⏹️ 用户中断初始化过程")
        sys.exit(1)
    except Exception as e:
        logger.error(f"💥 初始化过程中发生未预期的错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())