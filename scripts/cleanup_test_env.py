#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Knowledge RAG System - 测试环境清理脚本

该脚本用于清理测试环境，包括：
1. 清理测试数据库数据
2. 清理Redis缓存
3. 清理Elasticsearch索引
4. 清理Neo4j图数据
5. 重置测试环境到初始状态

作者: Knowledge RAG Team
创建时间: 2024-01-20
"""

import asyncio
import logging
import os
import sys
from typing import Optional

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
        logging.FileHandler('/tmp/test_cleanup.log')
    ]
)
logger = logging.getLogger(__name__)


class TestEnvironmentCleaner:
    """
    测试环境清理器
    
    负责清理所有测试环境的数据和配置
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
    
    async def cleanup_all(self, force: bool = False) -> bool:
        """
        清理所有测试数据
        
        Args:
            force: 是否强制清理（跳过确认）
        
        Returns:
            bool: 清理是否成功
        """
        try:
            if not force:
                confirmation = input("⚠️  确定要清理所有测试数据吗？这个操作不可逆！(y/N): ")
                if confirmation.lower() not in ['y', 'yes']:
                    logger.info("❌ 用户取消清理操作")
                    return False
            
            logger.info("🧹 开始清理测试环境...")
            
            # 1. 建立数据库连接
            await self._setup_connections()
            
            # 2. 清理PostgreSQL数据
            await self._cleanup_postgresql()
            
            # 3. 清理Redis数据
            await self._cleanup_redis()
            
            # 4. 清理Elasticsearch数据
            await self._cleanup_elasticsearch()
            
            # 5. 清理Neo4j数据
            await self._cleanup_neo4j()
            
            # 6. 验证清理结果
            await self._verify_cleanup()
            
            logger.info("✅ 测试环境清理完成！")
            return True
            
        except Exception as e:
            logger.error(f"❌ 测试环境清理失败: {e}")
            return False
        finally:
            await self._cleanup_connections()
    
    async def cleanup_specific(self, components: list) -> bool:
        """
        清理指定组件的测试数据
        
        Args:
            components: 要清理的组件列表 ['postgresql', 'redis', 'elasticsearch', 'neo4j']
        
        Returns:
            bool: 清理是否成功
        """
        try:
            logger.info(f"🧹 开始清理指定组件: {', '.join(components)}")
            
            # 建立连接
            await self._setup_connections()
            
            # 根据指定组件进行清理
            if 'postgresql' in components:
                await self._cleanup_postgresql()
            
            if 'redis' in components:
                await self._cleanup_redis()
            
            if 'elasticsearch' in components:
                await self._cleanup_elasticsearch()
            
            if 'neo4j' in components:
                await self._cleanup_neo4j()
            
            logger.info("✅ 指定组件清理完成！")
            return True
            
        except Exception as e:
            logger.error(f"❌ 指定组件清理失败: {e}")
            return False
        finally:
            await self._cleanup_connections()
    
    async def _setup_connections(self):
        """建立数据库连接"""
        logger.info("📡 建立数据库连接...")
        
        # PostgreSQL连接
        try:
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
            logger.warning(f"⚠️ PostgreSQL连接失败: {e}")
        
        # Redis连接
        try:
            self.redis_client = redis.from_url(self.redis_url)
            await self.redis_client.ping()
            logger.info("✅ Redis连接建立成功")
        except Exception as e:
            logger.warning(f"⚠️ Redis连接失败: {e}")
        
        # Elasticsearch连接
        try:
            self.es_client = AsyncElasticsearch([self.elasticsearch_url])
            await self.es_client.info()
            logger.info("✅ Elasticsearch连接建立成功")
        except Exception as e:
            logger.warning(f"⚠️ Elasticsearch连接失败: {e}")
        
        # Neo4j连接
        try:
            self.neo4j_driver = AsyncGraphDatabase.driver(
                self.neo4j_uri,
                auth=(self.neo4j_user, self.neo4j_password)
            )
            # 测试连接
            async with self.neo4j_driver.session() as session:
                await session.run("RETURN 1")
            logger.info("✅ Neo4j连接建立成功")
        except Exception as e:
            logger.warning(f"⚠️ Neo4j连接失败: {e}")
    
    async def _cleanup_postgresql(self):
        """清理PostgreSQL测试数据"""
        if not self.pg_pool:
            logger.warning("⚠️ PostgreSQL连接不可用，跳过清理")
            return
        
        logger.info("🗄️ 清理PostgreSQL测试数据...")
        
        async with self.pg_pool.acquire() as conn:
            # 获取清理前的数据统计
            stats_before = await self._get_postgresql_stats(conn)
            logger.info(f"清理前数据统计: {stats_before}")
            
            # 清理数据的SQL语句（按依赖关系顺序）
            cleanup_queries = [
                "DELETE FROM notifications WHERE user_id IN (SELECT id FROM users WHERE email LIKE '%@test.com')",
                "DELETE FROM entity_relationships WHERE source_entity_id IN (SELECT id FROM entities WHERE description LIKE '%测试%')",
                "DELETE FROM document_entities WHERE entity_id IN (SELECT id FROM entities WHERE description LIKE '%测试%')",
                "DELETE FROM entities WHERE description LIKE '%测试%'",
                "DELETE FROM messages WHERE conversation_id IN (SELECT id FROM conversations WHERE title LIKE '%测试%')",
                "DELETE FROM conversations WHERE title LIKE '%测试%'",
                "DELETE FROM document_chunks WHERE document_id IN (SELECT id FROM documents WHERE title LIKE '%测试%')",
                "DELETE FROM documents WHERE title LIKE '%测试%'",
                "DELETE FROM user_profiles WHERE user_id IN (SELECT id FROM users WHERE email LIKE '%@test.com')",
                "DELETE FROM users WHERE email LIKE '%@test.com'",
                
                # 重置序列
                "SELECT setval('users_id_seq', COALESCE((SELECT MAX(id) FROM users), 1), false)",
                "SELECT setval('documents_id_seq', COALESCE((SELECT MAX(id) FROM documents), 1), false)",
                "SELECT setval('conversations_id_seq', COALESCE((SELECT MAX(id) FROM conversations), 1), false)",
                "SELECT setval('messages_id_seq', COALESCE((SELECT MAX(id) FROM messages), 1), false)",
                "SELECT setval('entities_id_seq', COALESCE((SELECT MAX(id) FROM entities), 1), false)",
                "SELECT setval('notifications_id_seq', COALESCE((SELECT MAX(id) FROM notifications), 1), false)"
            ]
            
            # 执行清理
            for query in cleanup_queries:
                try:
                    result = await conn.execute(query)
                    if query.startswith('DELETE'):
                        # 提取删除的行数
                        rows_affected = int(result.split()[-1]) if result.split()[-1].isdigit() else 0
                        if rows_affected > 0:
                            logger.info(f"删除了 {rows_affected} 行: {query[:50]}...")
                except Exception as e:
                    logger.error(f"执行清理查询失败: {query[:50]}... - {e}")
            
            # 获取清理后的数据统计
            stats_after = await self._get_postgresql_stats(conn)
            logger.info(f"清理后数据统计: {stats_after}")
        
        logger.info("✅ PostgreSQL测试数据清理完成")
    
    async def _get_postgresql_stats(self, conn) -> dict:
        """获取PostgreSQL数据统计"""
        tables = ['users', 'documents', 'conversations', 'messages', 'entities', 'notifications']
        stats = {}
        
        for table in tables:
            try:
                count = await conn.fetchval(f"SELECT COUNT(*) FROM {table}")
                stats[table] = count
            except Exception as e:
                stats[table] = f"Error: {e}"
        
        return stats
    
    async def _cleanup_redis(self):
        """清理Redis测试数据"""
        if not self.redis_client:
            logger.warning("⚠️ Redis连接不可用，跳过清理")
            return
        
        logger.info("📦 清理Redis测试数据...")
        
        try:
            # 获取清理前的统计
            info_before = await self.redis_client.info('keyspace')
            logger.info(f"清理前Redis统计: {info_before}")
            
            # 清理测试相关的键
            test_patterns = [
                "session:test_*",
                "document:*test*",
                "rate_limit:user:*test*",
                "cache:*test*",
                "temp:*test*"
            ]
            
            total_deleted = 0
            for pattern in test_patterns:
                keys = await self.redis_client.keys(pattern)
                if keys:
                    deleted = await self.redis_client.delete(*keys)
                    total_deleted += deleted
                    logger.info(f"删除了 {deleted} 个键，模式: {pattern}")
            
            # 也可以选择清空整个测试数据库
            # await self.redis_client.flushdb()
            
            # 获取清理后的统计
            info_after = await self.redis_client.info('keyspace')
            logger.info(f"清理后Redis统计: {info_after}")
            logger.info(f"总共删除了 {total_deleted} 个键")
            
        except Exception as e:
            logger.error(f"Redis清理失败: {e}")
        
        logger.info("✅ Redis测试数据清理完成")
    
    async def _cleanup_elasticsearch(self):
        """清理Elasticsearch测试数据"""
        if not self.es_client:
            logger.warning("⚠️ Elasticsearch连接不可用，跳过清理")
            return
        
        logger.info("🔍 清理Elasticsearch测试数据...")
        
        try:
            # 获取所有索引
            indices_response = await self.es_client.cat.indices(format='json')
            test_indices = [idx['index'] for idx in indices_response if 'test' in idx['index'] or idx['index'] in ['documents', 'document_chunks']]
            
            logger.info(f"发现测试索引: {test_indices}")
            
            # 删除测试索引
            for index in test_indices:
                try:
                    # 获取索引统计
                    stats = await self.es_client.count(index=index)
                    doc_count = stats['count']
                    
                    if doc_count > 0:
                        # 删除索引中的测试数据
                        delete_query = {
                            "query": {
                                "bool": {
                                    "should": [
                                        {"wildcard": {"title": "*测试*"}},
                                        {"wildcard": {"content": "*测试*"}},
                                        {"term": {"user_id": "550e8400-e29b-41d4-a716-446655440002"}}
                                    ]
                                }
                            }
                        }
                        
                        result = await self.es_client.delete_by_query(index=index, body=delete_query)
                        deleted = result.get('deleted', 0)
                        logger.info(f"从索引 {index} 删除了 {deleted} 个文档")
                    
                    # 或者直接删除整个索引
                    # await self.es_client.indices.delete(index=index)
                    # logger.info(f"删除了索引: {index}")
                    
                except Exception as e:
                    logger.error(f"清理索引 {index} 失败: {e}")
            
            # 刷新索引
            for index in test_indices:
                try:
                    await self.es_client.indices.refresh(index=index)
                except:
                    pass
            
        except Exception as e:
            logger.error(f"Elasticsearch清理失败: {e}")
        
        logger.info("✅ Elasticsearch测试数据清理完成")
    
    async def _cleanup_neo4j(self):
        """清理Neo4j测试数据"""
        if not self.neo4j_driver:
            logger.warning("⚠️ Neo4j连接不可用，跳过清理")
            return
        
        logger.info("🕸️ 清理Neo4j测试数据...")
        
        try:
            async with self.neo4j_driver.session() as session:
                # 获取清理前的统计
                result = await session.run("MATCH (n) WHERE n.test_data = true RETURN labels(n) as labels, count(n) as count")
                stats_before = {}
                async for record in result:
                    labels = record['labels']
                    count = record['count']
                    for label in labels:
                        if label != 'test_data':
                            stats_before[label] = stats_before.get(label, 0) + count
                
                logger.info(f"清理前Neo4j统计: {stats_before}")
                
                # 删除所有测试数据节点和关系
                result = await session.run("MATCH (n) WHERE n.test_data = true DETACH DELETE n RETURN count(n) as deleted")
                async for record in result:
                    deleted_count = record['deleted']
                    logger.info(f"删除了 {deleted_count} 个测试节点")
                
                # 删除测试用户相关的数据
                test_user_queries = [
                    "MATCH (u:User) WHERE u.email ENDS WITH '@test.com' DETACH DELETE u",
                    "MATCH (d:Document) WHERE d.title CONTAINS '测试' DETACH DELETE d",
                    "MATCH (e:Entity) WHERE e.description CONTAINS '测试' DETACH DELETE e"
                ]
                
                for query in test_user_queries:
                    try:
                        result = await session.run(query)
                        # Neo4j不直接返回删除计数，但我们可以记录执行
                        logger.info(f"执行清理查询: {query[:50]}...")
                    except Exception as e:
                        logger.error(f"执行Neo4j清理查询失败: {query[:50]}... - {e}")
                
                # 获取清理后的统计
                result = await session.run("MATCH (n) RETURN labels(n) as labels, count(n) as count")
                stats_after = {}
                async for record in result:
                    labels = record['labels']
                    count = record['count']
                    for label in labels:
                        stats_after[label] = stats_after.get(label, 0) + count
                
                logger.info(f"清理后Neo4j统计: {stats_after}")
                
        except Exception as e:
            logger.error(f"Neo4j清理失败: {e}")
        
        logger.info("✅ Neo4j测试数据清理完成")
    
    async def _verify_cleanup(self):
        """验证清理结果"""
        logger.info("🔍 验证清理结果...")
        
        issues = []
        
        # 验证PostgreSQL
        if self.pg_pool:
            try:
                async with self.pg_pool.acquire() as conn:
                    test_users = await conn.fetchval("SELECT COUNT(*) FROM users WHERE email LIKE '%@test.com'")
                    test_docs = await conn.fetchval("SELECT COUNT(*) FROM documents WHERE title LIKE '%测试%'")
                    
                    if test_users > 0:
                        issues.append(f"PostgreSQL中仍有 {test_users} 个测试用户")
                    if test_docs > 0:
                        issues.append(f"PostgreSQL中仍有 {test_docs} 个测试文档")
            except Exception as e:
                issues.append(f"PostgreSQL验证失败: {e}")
        
        # 验证Redis
        if self.redis_client:
            try:
                test_keys = await self.redis_client.keys("*test*")
                if test_keys:
                    issues.append(f"Redis中仍有 {len(test_keys)} 个测试键")
            except Exception as e:
                issues.append(f"Redis验证失败: {e}")
        
        # 验证Elasticsearch
        if self.es_client:
            try:
                for index in ['documents', 'document_chunks']:
                    if await self.es_client.indices.exists(index=index):
                        search_result = await self.es_client.search(
                            index=index,
                            body={
                                "query": {
                                    "bool": {
                                        "should": [
                                            {"wildcard": {"title": "*测试*"}},
                                            {"wildcard": {"content": "*测试*"}}
                                        ]
                                    }
                                }
                            }
                        )
                        
                        if search_result['hits']['total']['value'] > 0:
                            issues.append(f"Elasticsearch索引 {index} 中仍有测试数据")
            except Exception as e:
                issues.append(f"Elasticsearch验证失败: {e}")
        
        # 验证Neo4j
        if self.neo4j_driver:
            try:
                async with self.neo4j_driver.session() as session:
                    result = await session.run("MATCH (n) WHERE n.test_data = true RETURN count(n) as count")
                    async for record in result:
                        if record['count'] > 0:
                            issues.append(f"Neo4j中仍有 {record['count']} 个测试数据节点")
            except Exception as e:
                issues.append(f"Neo4j验证失败: {e}")
        
        if issues:
            logger.warning("⚠️ 清理验证发现问题:")
            for issue in issues:
                logger.warning(f"  - {issue}")
        else:
            logger.info("✅ 清理验证通过，所有测试数据已清理")
    
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
    import argparse
    
    parser = argparse.ArgumentParser(description='Knowledge RAG 测试环境清理工具')
    parser.add_argument('--force', '-f', action='store_true', help='强制清理，跳过确认')
    parser.add_argument('--components', '-c', nargs='+', 
                       choices=['postgresql', 'redis', 'elasticsearch', 'neo4j'],
                       help='指定要清理的组件')
    
    args = parser.parse_args()
    
    cleaner = TestEnvironmentCleaner()
    
    try:
        if args.components:
            success = await cleaner.cleanup_specific(args.components)
        else:
            success = await cleaner.cleanup_all(force=args.force)
        
        if success:
            logger.info("🎉 测试环境清理成功！")
            sys.exit(0)
        else:
            logger.error("💥 测试环境清理失败！")
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("⏹️ 用户中断清理过程")
        sys.exit(1)
    except Exception as e:
        logger.error(f"💥 清理过程中发生未预期的错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())