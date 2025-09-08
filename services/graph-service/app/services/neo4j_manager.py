#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Neo4j图数据库管理器模块

该模块提供Neo4j图数据库的管理功能，包括：
- 数据库连接管理
- 图谱数据的CRUD操作
- 实体和关系管理
- 图谱查询和分析
- 社区检测和图算法

Author: Knowledge RAG Team
Date: 2024
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

try:
    from neo4j import Driver, GraphDatabase, Session
    from neo4j.exceptions import AuthError, ConfigurationError, ServiceUnavailable

    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    logging.warning("Neo4j驱动未安装，图数据库功能将不可用")

from app.core.config import settings
from shared.utils.logger import get_logger
from shared.utils.metrics import MetricsCollector

logger = get_logger(__name__)
metrics = MetricsCollector()


class Neo4jManager:
    """Neo4j图数据库管理器"""

    def __init__(self):
        """初始化Neo4j管理器"""
        self.driver: Optional[Driver] = None
        self.connected = False

        # 连接配置
        self.uri = settings.NEO4J_URI
        self.username = settings.NEO4J_USERNAME
        self.password = settings.NEO4J_PASSWORD
        self.database = settings.NEO4J_DATABASE

        logger.info(f"Neo4j管理器初始化完成，URI: {self.uri}")

    async def connect(self) -> bool:
        """连接到Neo4j数据库"""
        try:
            if not NEO4J_AVAILABLE:
                logger.error("Neo4j驱动未安装")
                return False

            # 创建驱动
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.username, self.password),
                max_connection_lifetime=3600,
                max_connection_pool_size=50,
                connection_acquisition_timeout=60,
            )

            # 验证连接
            await asyncio.get_event_loop().run_in_executor(
                None, self.driver.verify_connectivity
            )

            self.connected = True
            metrics.increment("neo4j_connections")
            logger.info("Neo4j连接成功")

            # 创建索引和约束
            await self._create_indexes_and_constraints()

            return True

        except (ServiceUnavailable, AuthError, ConfigurationError) as e:
            logger.error(f"Neo4j连接失败: {e}")
            metrics.increment("neo4j_connection_failures")
            return False
        except Exception as e:
            logger.error(f"Neo4j连接异常: {e}")
            metrics.increment("neo4j_connection_errors")
            return False

    async def _create_indexes_and_constraints(self):
        """创建索引和约束"""
        try:
            queries = [
                # 实体约束和索引
                "CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE",
                "CREATE INDEX entity_title IF NOT EXISTS FOR (e:Entity) ON (e.title)",
                "CREATE INDEX entity_type IF NOT EXISTS FOR (e:Entity) ON (e.type)",
                # 关系索引
                "CREATE INDEX relationship_type IF NOT EXISTS FOR ()-[r:RELATED_TO]-() ON (r.type)",
                "CREATE INDEX relationship_weight IF NOT EXISTS FOR ()-[r:RELATED_TO]-() ON (r.weight)",
                # 社区约束和索引
                "CREATE CONSTRAINT community_id IF NOT EXISTS FOR (c:Community) REQUIRE c.id IS UNIQUE",
                "CREATE INDEX community_level IF NOT EXISTS FOR (c:Community) ON (c.level)",
                "CREATE INDEX community_size IF NOT EXISTS FOR (c:Community) ON (c.size)",
                # 文档约束和索引
                "CREATE CONSTRAINT document_id IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE",
                "CREATE INDEX document_title IF NOT EXISTS FOR (d:Document) ON (d.title)",
                "CREATE INDEX document_created_at IF NOT EXISTS FOR (d:Document) ON (d.created_at)",
            ]

            for query in queries:
                try:
                    await self._execute_query(query)
                except Exception as e:
                    # 忽略已存在的约束/索引错误
                    if "already exists" not in str(e).lower():
                        logger.warning(f"创建索引/约束失败: {query}, 错误: {e}")

            logger.info("Neo4j索引和约束创建完成")

        except Exception as e:
            logger.error(f"创建索引和约束失败: {e}")

    async def _execute_query(self, query: str, parameters: Dict = None) -> List[Dict]:
        """执行Cypher查询"""
        if not self.connected or not self.driver:
            raise Exception("Neo4j未连接")

        def _run_query(tx):
            result = tx.run(query, parameters or {})
            return [record.data() for record in result]

        try:
            async with self.driver.session(database=self.database) as session:
                result = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: session.execute_read(_run_query)
                )
                return result
        except Exception as e:
            logger.error(f"查询执行失败: {query}, 错误: {e}")
            raise

    async def _execute_write_query(
        self, query: str, parameters: Dict = None
    ) -> List[Dict]:
        """执行写入查询"""
        if not self.connected or not self.driver:
            raise Exception("Neo4j未连接")

        def _run_query(tx):
            result = tx.run(query, parameters or {})
            return [record.data() for record in result]

        try:
            async with self.driver.session(database=self.database) as session:
                result = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: session.execute_write(_run_query)
                )
                return result
        except Exception as e:
            logger.error(f"写入查询执行失败: {query}, 错误: {e}")
            raise

    async def create_entity(self, entity_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建实体"""
        try:
            query = """
            MERGE (e:Entity {id: $id})
            SET e.title = $title,
                e.type = $type,
                e.description = $description,
                e.degree = $degree,
                e.community_ids = $community_ids,
                e.created_at = datetime(),
                e.updated_at = datetime()
            RETURN e
            """

            parameters = {
                "id": entity_data.get("id"),
                "title": entity_data.get("title", ""),
                "type": entity_data.get("type", ""),
                "description": entity_data.get("description", ""),
                "degree": entity_data.get("degree", 0),
                "community_ids": entity_data.get("community_ids", []),
            }

            result = await self._execute_write_query(query, parameters)

            if result:
                metrics.increment("neo4j_entities_created")
                logger.info(f"实体创建成功: {entity_data.get('id')}")
                return {
                    "success": True,
                    "entity": result[0]["e"],
                    "message": "实体创建成功",
                }
            else:
                return {"success": False, "message": "实体创建失败"}

        except Exception as e:
            logger.error(f"创建实体失败: {e}")
            metrics.increment("neo4j_entity_creation_failures")
            return {"success": False, "message": f"创建实体失败: {str(e)}"}

    async def create_relationship(
        self, relationship_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """创建关系"""
        try:
            query = """
            MATCH (source:Entity {id: $source_id})
            MATCH (target:Entity {id: $target_id})
            MERGE (source)-[r:RELATED_TO {id: $id}]->(target)
            SET r.type = $type,
                r.description = $description,
                r.weight = $weight,
                r.text_unit_ids = $text_unit_ids,
                r.created_at = datetime(),
                r.updated_at = datetime()
            RETURN r, source, target
            """

            parameters = {
                "id": relationship_data.get("id"),
                "source_id": relationship_data.get("source"),
                "target_id": relationship_data.get("target"),
                "type": relationship_data.get("type", "RELATED_TO"),
                "description": relationship_data.get("description", ""),
                "weight": relationship_data.get("weight", 1.0),
                "text_unit_ids": relationship_data.get("text_unit_ids", []),
            }

            result = await self._execute_write_query(query, parameters)

            if result:
                metrics.increment("neo4j_relationships_created")
                logger.info(f"关系创建成功: {relationship_data.get('id')}")
                return {
                    "success": True,
                    "relationship": result[0]["r"],
                    "source": result[0]["source"],
                    "target": result[0]["target"],
                    "message": "关系创建成功",
                }
            else:
                return {"success": False, "message": "关系创建失败"}

        except Exception as e:
            logger.error(f"创建关系失败: {e}")
            metrics.increment("neo4j_relationship_creation_failures")
            return {"success": False, "message": f"创建关系失败: {str(e)}"}

    async def create_community(self, community_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建社区"""
        try:
            # 创建社区节点
            query = """
            MERGE (c:Community {id: $id})
            SET c.title = $title,
                c.level = $level,
                c.size = $size,
                c.entity_ids = $entity_ids,
                c.relationship_ids = $relationship_ids,
                c.created_at = datetime(),
                c.updated_at = datetime()
            RETURN c
            """

            parameters = {
                "id": community_data.get("id"),
                "title": community_data.get("title", ""),
                "level": community_data.get("level", 0),
                "size": community_data.get("size", 0),
                "entity_ids": community_data.get("entity_ids", []),
                "relationship_ids": community_data.get("relationship_ids", []),
            }

            result = await self._execute_write_query(query, parameters)

            if result:
                # 创建社区与实体的关系
                entity_ids = community_data.get("entity_ids", [])
                if entity_ids:
                    await self._link_community_entities(
                        community_data.get("id"), entity_ids
                    )

                metrics.increment("neo4j_communities_created")
                logger.info(f"社区创建成功: {community_data.get('id')}")
                return {
                    "success": True,
                    "community": result[0]["c"],
                    "message": "社区创建成功",
                }
            else:
                return {"success": False, "message": "社区创建失败"}

        except Exception as e:
            logger.error(f"创建社区失败: {e}")
            metrics.increment("neo4j_community_creation_failures")
            return {"success": False, "message": f"创建社区失败: {str(e)}"}

    async def _link_community_entities(self, community_id: str, entity_ids: List[str]):
        """链接社区和实体"""
        try:
            query = """
            MATCH (c:Community {id: $community_id})
            MATCH (e:Entity)
            WHERE e.id IN $entity_ids
            MERGE (c)-[:CONTAINS]->(e)
            """

            parameters = {"community_id": community_id, "entity_ids": entity_ids}

            await self._execute_write_query(query, parameters)

        except Exception as e:
            logger.error(f"链接社区和实体失败: {e}")

    async def get_entities(
        self, limit: int = 100, offset: int = 0, entity_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取实体列表"""
        try:
            # 构建查询
            where_clause = "WHERE e.type = $entity_type" if entity_type else ""

            query = f"""
            MATCH (e:Entity)
            {where_clause}
            RETURN e
            ORDER BY e.created_at DESC
            SKIP $offset
            LIMIT $limit
            """

            count_query = f"""
            MATCH (e:Entity)
            {where_clause}
            RETURN count(e) as total
            """

            parameters = {"limit": limit, "offset": offset}

            if entity_type:
                parameters["entity_type"] = entity_type

            # 获取总数
            count_result = await self._execute_query(count_query, parameters)
            total_count = count_result[0]["total"] if count_result else 0

            # 获取实体
            result = await self._execute_query(query, parameters)

            entities = [record["e"] for record in result]

            return {
                "success": True,
                "entities": entities,
                "total_count": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total_count,
            }

        except Exception as e:
            logger.error(f"获取实体列表失败: {e}")
            return {
                "success": False,
                "message": f"获取实体列表失败: {str(e)}",
                "entities": [],
            }

    async def get_relationships(
        self,
        limit: int = 100,
        offset: int = 0,
        source_id: Optional[str] = None,
        target_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """获取关系列表"""
        try:
            # 构建查询条件
            where_conditions = []
            if source_id:
                where_conditions.append("source.id = $source_id")
            if target_id:
                where_conditions.append("target.id = $target_id")

            where_clause = (
                "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
            )

            query = f"""
            MATCH (source:Entity)-[r:RELATED_TO]->(target:Entity)
            {where_clause}
            RETURN r, source, target
            ORDER BY r.created_at DESC
            SKIP $offset
            LIMIT $limit
            """

            count_query = f"""
            MATCH (source:Entity)-[r:RELATED_TO]->(target:Entity)
            {where_clause}
            RETURN count(r) as total
            """

            parameters = {"limit": limit, "offset": offset}

            if source_id:
                parameters["source_id"] = source_id
            if target_id:
                parameters["target_id"] = target_id

            # 获取总数
            count_result = await self._execute_query(count_query, parameters)
            total_count = count_result[0]["total"] if count_result else 0

            # 获取关系
            result = await self._execute_query(query, parameters)

            relationships = []
            for record in result:
                relationships.append(
                    {
                        "relationship": record["r"],
                        "source": record["source"],
                        "target": record["target"],
                    }
                )

            return {
                "success": True,
                "relationships": relationships,
                "total_count": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total_count,
            }

        except Exception as e:
            logger.error(f"获取关系列表失败: {e}")
            return {
                "success": False,
                "message": f"获取关系列表失败: {str(e)}",
                "relationships": [],
            }

    async def get_communities(
        self, limit: int = 100, offset: int = 0, level: Optional[int] = None
    ) -> Dict[str, Any]:
        """获取社区列表"""
        try:
            # 构建查询条件
            where_clause = "WHERE c.level = $level" if level is not None else ""

            query = f"""
            MATCH (c:Community)
            {where_clause}
            RETURN c
            ORDER BY c.size DESC, c.created_at DESC
            SKIP $offset
            LIMIT $limit
            """

            count_query = f"""
            MATCH (c:Community)
            {where_clause}
            RETURN count(c) as total
            """

            parameters = {"limit": limit, "offset": offset}

            if level is not None:
                parameters["level"] = level

            # 获取总数
            count_result = await self._execute_query(count_query, parameters)
            total_count = count_result[0]["total"] if count_result else 0

            # 获取社区
            result = await self._execute_query(query, parameters)

            communities = [record["c"] for record in result]

            return {
                "success": True,
                "communities": communities,
                "total_count": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total_count,
            }

        except Exception as e:
            logger.error(f"获取社区列表失败: {e}")
            return {
                "success": False,
                "message": f"获取社区列表失败: {str(e)}",
                "communities": [],
            }

    async def search_entities(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """搜索实体"""
        try:
            cypher_query = """
            MATCH (e:Entity)
            WHERE e.title CONTAINS $query OR e.description CONTAINS $query
            RETURN e, 
                   CASE 
                       WHEN e.title CONTAINS $query THEN 2
                       ELSE 1
                   END as relevance
            ORDER BY relevance DESC, e.degree DESC
            LIMIT $limit
            """

            parameters = {"query": query, "limit": limit}

            result = await self._execute_query(cypher_query, parameters)

            entities = []
            for record in result:
                entity = record["e"]
                entity["relevance"] = record["relevance"]
                entities.append(entity)

            return {
                "success": True,
                "entities": entities,
                "query": query,
                "count": len(entities),
            }

        except Exception as e:
            logger.error(f"搜索实体失败: {e}")
            return {
                "success": False,
                "message": f"搜索实体失败: {str(e)}",
                "entities": [],
            }

    async def get_entity_neighbors(
        self, entity_id: str, depth: int = 1, limit: int = 50
    ) -> Dict[str, Any]:
        """获取实体的邻居节点"""
        try:
            query = f"""
            MATCH (e:Entity {{id: $entity_id}})
            MATCH (e)-[r:RELATED_TO*1..{depth}]-(neighbor:Entity)
            RETURN DISTINCT neighbor, 
                   min(length([rel in r | rel])) as distance,
                   collect(DISTINCT [rel in r | {{type: rel.type, weight: rel.weight}}]) as paths
            ORDER BY distance ASC, neighbor.degree DESC
            LIMIT $limit
            """

            parameters = {"entity_id": entity_id, "limit": limit}

            result = await self._execute_query(query, parameters)

            neighbors = []
            for record in result:
                neighbor = record["neighbor"]
                neighbor["distance"] = record["distance"]
                neighbor["paths"] = record["paths"]
                neighbors.append(neighbor)

            return {
                "success": True,
                "entity_id": entity_id,
                "neighbors": neighbors,
                "count": len(neighbors),
            }

        except Exception as e:
            logger.error(f"获取实体邻居失败: {e}")
            return {
                "success": False,
                "message": f"获取实体邻居失败: {str(e)}",
                "neighbors": [],
            }

    async def get_shortest_path(
        self, source_id: str, target_id: str, max_depth: int = 5
    ) -> Dict[str, Any]:
        """获取两个实体之间的最短路径"""
        try:
            query = f"""
            MATCH (source:Entity {{id: $source_id}}), (target:Entity {{id: $target_id}})
            MATCH path = shortestPath((source)-[r:RELATED_TO*1..{max_depth}]-(target))
            RETURN path,
                   length(path) as path_length,
                   [rel in relationships(path) | {{type: rel.type, weight: rel.weight, description: rel.description}}] as relationships,
                   [node in nodes(path) | {{id: node.id, title: node.title, type: node.type}}] as entities
            """

            parameters = {"source_id": source_id, "target_id": target_id}

            result = await self._execute_query(query, parameters)

            if result:
                path_data = result[0]
                return {
                    "success": True,
                    "source_id": source_id,
                    "target_id": target_id,
                    "path_length": path_data["path_length"],
                    "entities": path_data["entities"],
                    "relationships": path_data["relationships"],
                }
            else:
                return {
                    "success": False,
                    "message": "未找到路径",
                    "source_id": source_id,
                    "target_id": target_id,
                }

        except Exception as e:
            logger.error(f"获取最短路径失败: {e}")
            return {
                "success": False,
                "message": f"获取最短路径失败: {str(e)}",
                "source_id": source_id,
                "target_id": target_id,
            }

    async def get_graph_statistics(self) -> Dict[str, Any]:
        """获取图谱统计信息"""
        try:
            queries = {
                "entities_count": "MATCH (e:Entity) RETURN count(e) as count",
                "relationships_count": "MATCH ()-[r:RELATED_TO]->() RETURN count(r) as count",
                "communities_count": "MATCH (c:Community) RETURN count(c) as count",
                "entity_types": "MATCH (e:Entity) RETURN e.type as type, count(e) as count ORDER BY count DESC",
                "avg_degree": "MATCH (e:Entity) RETURN avg(e.degree) as avg_degree",
                "max_degree": "MATCH (e:Entity) RETURN max(e.degree) as max_degree",
                "community_levels": "MATCH (c:Community) RETURN c.level as level, count(c) as count ORDER BY level",
            }

            statistics = {}

            for key, query in queries.items():
                try:
                    result = await self._execute_query(query)
                    if key in [
                        "entities_count",
                        "relationships_count",
                        "communities_count",
                        "avg_degree",
                        "max_degree",
                    ]:
                        statistics[key] = (
                            result[0][list(result[0].keys())[0]] if result else 0
                        )
                    else:
                        statistics[key] = result
                except Exception as e:
                    logger.warning(f"获取统计信息失败 {key}: {e}")
                    statistics[key] = (
                        0
                        if key.endswith("_count") or key.startswith(("avg_", "max_"))
                        else []
                    )

            return {
                "success": True,
                "statistics": statistics,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"获取图谱统计信息失败: {e}")
            return {
                "success": False,
                "message": f"获取图谱统计信息失败: {str(e)}",
                "statistics": {},
            }

    async def clear_graph(self) -> Dict[str, Any]:
        """清空图谱数据"""
        try:
            queries = [
                "MATCH (n) DETACH DELETE n",  # 删除所有节点和关系
            ]

            for query in queries:
                await self._execute_write_query(query)

            metrics.increment("neo4j_graph_clears")
            logger.info("图谱数据清空完成")

            return {"success": True, "message": "图谱数据清空成功"}

        except Exception as e:
            logger.error(f"清空图谱数据失败: {e}")
            metrics.increment("neo4j_graph_clear_failures")
            return {"success": False, "message": f"清空图谱数据失败: {str(e)}"}

    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            if not self.connected or not self.driver:
                return {
                    "healthy": False,
                    "message": "Neo4j未连接",
                    "timestamp": datetime.now().isoformat(),
                }

            # 执行简单查询测试连接
            result = await self._execute_query("RETURN 1 as test")

            if result and result[0]["test"] == 1:
                return {
                    "healthy": True,
                    "connected": self.connected,
                    "database": self.database,
                    "timestamp": datetime.now().isoformat(),
                }
            else:
                return {
                    "healthy": False,
                    "message": "Neo4j查询测试失败",
                    "timestamp": datetime.now().isoformat(),
                }

        except Exception as e:
            logger.error(f"Neo4j健康检查失败: {e}")
            return {
                "healthy": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def close(self):
        """关闭连接"""
        try:
            if self.driver:
                await asyncio.get_event_loop().run_in_executor(None, self.driver.close)
                self.driver = None
                self.connected = False
                logger.info("Neo4j连接已关闭")

        except Exception as e:
            logger.error(f"关闭Neo4j连接失败: {e}")


# 导出
__all__ = ["Neo4jManager"]
