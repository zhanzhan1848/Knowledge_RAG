#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
向量管理器模块

该模块提供统一的向量数据库管理接口，支持多种向量数据库：
- ChromaDB
- FAISS
- Weaviate

Author: Knowledge RAG Team
Date: 2024
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Union, Tuple
from abc import ABC, abstractmethod
from datetime import datetime
import numpy as np
from dataclasses import dataclass

from app.core.config import settings, VectorBackend
from app.services.embedding_service import EmbeddingService
from shared.config.weaviate_config import (
    weaviate_config, weaviate_connection, weaviate_schema
)
from shared.utils.cache import CacheManager
from shared.utils.metrics import MetricsCollector

logger = logging.getLogger(__name__)


@dataclass
class VectorDocument:
    """向量文档数据类"""
    id: str
    content: str
    vector: Optional[List[float]] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class SearchResult:
    """搜索结果数据类"""
    id: str
    content: str
    score: float
    metadata: Optional[Dict[str, Any]] = None


class VectorStore(ABC):
    """向量存储抽象基类"""
    
    @abstractmethod
    async def initialize(self) -> None:
        """初始化向量存储"""
        pass
    
    @abstractmethod
    async def add_documents(self, documents: List[VectorDocument]) -> List[str]:
        """添加文档"""
        pass
    
    @abstractmethod
    async def search(self, query_vector: List[float], top_k: int = 10, 
                    filters: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """向量搜索"""
        pass
    
    @abstractmethod
    async def delete_documents(self, document_ids: List[str]) -> bool:
        """删除文档"""
        pass
    
    @abstractmethod
    async def update_document(self, document: VectorDocument) -> bool:
        """更新文档"""
        pass
    
    @abstractmethod
    async def get_document(self, document_id: str) -> Optional[VectorDocument]:
        """获取文档"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """健康检查"""
        pass
    
    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """清理资源"""
        pass


class WeaviateStore(VectorStore):
    """Weaviate 向量存储实现"""
    
    def __init__(self):
        """初始化 Weaviate 存储"""
        self.client = None
        self.class_name = weaviate_config.class_name
        self.batch_size = weaviate_config.batch_size
    
    async def initialize(self) -> None:
        """初始化 Weaviate 连接"""
        try:
            self.client = weaviate_connection.get_client()
            
            # 检查类是否存在，不存在则创建
            if not self.client.schema.exists(self.class_name):
                class_definition = weaviate_schema.get_document_class_definition(weaviate_config)
                self.client.schema.create_class(class_definition)
                logger.info(f"创建 Weaviate 类: {self.class_name}")
            
            logger.info("Weaviate 初始化成功")
            
        except Exception as e:
            logger.error(f"Weaviate 初始化失败: {e}")
            raise
    
    async def add_documents(self, documents: List[VectorDocument]) -> List[str]:
        """添加文档到 Weaviate"""
        try:
            added_ids = []
            
            # 批量处理
            with self.client.batch as batch:
                batch.batch_size = self.batch_size
                
                for doc in documents:
                    # 准备数据对象
                    data_object = {
                        "title": doc.metadata.get("title", "") if doc.metadata else "",
                        "content": doc.content,
                        "source": doc.metadata.get("source", "") if doc.metadata else "",
                        "document_type": doc.metadata.get("document_type", "text") if doc.metadata else "text",
                        "chunk_index": doc.metadata.get("chunk_index", 0) if doc.metadata else 0,
                        "metadata": doc.metadata or {},
                        "created_at": doc.created_at.isoformat() if doc.created_at else datetime.now().isoformat(),
                        "updated_at": doc.updated_at.isoformat() if doc.updated_at else datetime.now().isoformat()
                    }
                    
                    # 添加到批处理
                    batch.add_data_object(
                        data_object=data_object,
                        class_name=self.class_name,
                        uuid=doc.id,
                        vector=doc.vector
                    )
                    added_ids.append(doc.id)
            
            logger.info(f"成功添加 {len(added_ids)} 个文档到 Weaviate")
            return added_ids
            
        except Exception as e:
            logger.error(f"添加文档到 Weaviate 失败: {e}")
            raise
    
    async def search(self, query_vector: List[float], top_k: int = 10, 
                    filters: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """在 Weaviate 中搜索"""
        try:
            # 构建查询
            query_builder = (
                self.client.query
                .get(self.class_name, ["title", "content", "source", "metadata"])
                .with_near_vector({"vector": query_vector})
                .with_limit(top_k)
                .with_additional(["certainty", "id"])
            )
            
            # 添加过滤条件
            if filters:
                where_filter = self._build_where_filter(filters)
                if where_filter:
                    query_builder = query_builder.with_where(where_filter)
            
            # 执行查询
            result = query_builder.do()
            
            # 处理结果
            search_results = []
            if "data" in result and "Get" in result["data"] and self.class_name in result["data"]["Get"]:
                for item in result["data"]["Get"][self.class_name]:
                    search_results.append(SearchResult(
                        id=item["_additional"]["id"],
                        content=item["content"],
                        score=item["_additional"]["certainty"],
                        metadata=item.get("metadata", {})
                    ))
            
            logger.info(f"Weaviate 搜索返回 {len(search_results)} 个结果")
            return search_results
            
        except Exception as e:
            logger.error(f"Weaviate 搜索失败: {e}")
            raise
    
    async def delete_documents(self, document_ids: List[str]) -> bool:
        """从 Weaviate 删除文档"""
        try:
            for doc_id in document_ids:
                self.client.data_object.delete(
                    uuid=doc_id,
                    class_name=self.class_name
                )
            
            logger.info(f"成功从 Weaviate 删除 {len(document_ids)} 个文档")
            return True
            
        except Exception as e:
            logger.error(f"从 Weaviate 删除文档失败: {e}")
            return False
    
    async def update_document(self, document: VectorDocument) -> bool:
        """更新 Weaviate 中的文档"""
        try:
            # 准备更新数据
            data_object = {
                "title": document.metadata.get("title", "") if document.metadata else "",
                "content": document.content,
                "source": document.metadata.get("source", "") if document.metadata else "",
                "document_type": document.metadata.get("document_type", "text") if document.metadata else "text",
                "chunk_index": document.metadata.get("chunk_index", 0) if document.metadata else 0,
                "metadata": document.metadata or {},
                "updated_at": datetime.now().isoformat()
            }
            
            # 更新文档
            self.client.data_object.update(
                data_object=data_object,
                class_name=self.class_name,
                uuid=document.id,
                vector=document.vector
            )
            
            logger.info(f"成功更新 Weaviate 文档: {document.id}")
            return True
            
        except Exception as e:
            logger.error(f"更新 Weaviate 文档失败: {e}")
            return False
    
    async def get_document(self, document_id: str) -> Optional[VectorDocument]:
        """从 Weaviate 获取文档"""
        try:
            result = (
                self.client.query
                .get(self.class_name, ["title", "content", "source", "metadata", "created_at", "updated_at"])
                .with_where({
                    "path": ["id"],
                    "operator": "Equal",
                    "valueText": document_id
                })
                .with_additional(["id", "vector"])
                .do()
            )
            
            if "data" in result and "Get" in result["data"] and self.class_name in result["data"]["Get"]:
                items = result["data"]["Get"][self.class_name]
                if items:
                    item = items[0]
                    return VectorDocument(
                        id=item["_additional"]["id"],
                        content=item["content"],
                        vector=item["_additional"].get("vector"),
                        metadata=item.get("metadata", {}),
                        created_at=datetime.fromisoformat(item.get("created_at", "")) if item.get("created_at") else None,
                        updated_at=datetime.fromisoformat(item.get("updated_at", "")) if item.get("updated_at") else None
                    )
            
            return None
            
        except Exception as e:
            logger.error(f"从 Weaviate 获取文档失败: {e}")
            return None
    
    async def health_check(self) -> bool:
        """Weaviate 健康检查"""
        try:
            return weaviate_connection.health_check()
        except Exception:
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """获取 Weaviate 统计信息"""
        try:
            # 获取类统计信息
            result = self.client.query.aggregate(self.class_name).with_meta_count().do()
            
            count = 0
            if "data" in result and "Aggregate" in result["data"] and self.class_name in result["data"]["Aggregate"]:
                aggregate_data = result["data"]["Aggregate"][self.class_name]
                if aggregate_data:
                    count = aggregate_data[0].get("meta", {}).get("count", 0)
            
            return {
                "backend": "weaviate",
                "class_name": self.class_name,
                "document_count": count,
                "status": "healthy" if await self.health_check() else "unhealthy"
            }
            
        except Exception as e:
            logger.error(f"获取 Weaviate 统计信息失败: {e}")
            return {
                "backend": "weaviate",
                "status": "error",
                "error": str(e)
            }
    
    async def cleanup(self) -> None:
        """清理 Weaviate 资源"""
        try:
            weaviate_connection.close()
            logger.info("Weaviate 资源清理完成")
        except Exception as e:
            logger.error(f"Weaviate 资源清理失败: {e}")
    
    def _build_where_filter(self, filters: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """构建 Weaviate where 过滤条件"""
        if not filters:
            return None
        
        # 简单的过滤条件构建，可以根据需要扩展
        conditions = []
        
        for key, value in filters.items():
            if isinstance(value, str):
                conditions.append({
                    "path": [key],
                    "operator": "Equal",
                    "valueText": value
                })
            elif isinstance(value, (int, float)):
                conditions.append({
                    "path": [key],
                    "operator": "Equal",
                    "valueNumber": value
                })
        
        if len(conditions) == 1:
            return conditions[0]
        elif len(conditions) > 1:
            return {
                "operator": "And",
                "operands": conditions
            }
        
        return None


class VectorManager:
    """向量管理器"""
    
    def __init__(self):
        """初始化向量管理器"""
        self.vector_store: Optional[VectorStore] = None
        self.embedding_service = EmbeddingService()
        self.cache_manager = CacheManager()
        self.metrics_collector = MetricsCollector()
    
    async def initialize(self) -> None:
        """初始化向量管理器"""
        try:
            # 根据配置创建向量存储
            if settings.VECTOR_BACKEND == VectorBackend.WEAVIATE:
                self.vector_store = WeaviateStore()
            elif settings.VECTOR_BACKEND == VectorBackend.CHROMADB:
                # TODO: 实现 ChromaDB 存储
                raise NotImplementedError("ChromaDB 存储尚未实现")
            elif settings.VECTOR_BACKEND == VectorBackend.FAISS:
                # TODO: 实现 FAISS 存储
                raise NotImplementedError("FAISS 存储尚未实现")
            else:
                raise ValueError(f"不支持的向量后端: {settings.VECTOR_BACKEND}")
            
            # 初始化向量存储
            await self.vector_store.initialize()
            
            # 初始化嵌入服务
            await self.embedding_service.initialize()
            
            logger.info(f"向量管理器初始化成功，使用后端: {settings.VECTOR_BACKEND}")
            
        except Exception as e:
            logger.error(f"向量管理器初始化失败: {e}")
            raise
    
    async def add_documents(self, documents: List[Dict[str, Any]]) -> List[str]:
        """添加文档"""
        try:
            # 转换为 VectorDocument 对象
            vector_docs = []
            for doc in documents:
                # 生成嵌入向量
                vector = await self.embedding_service.embed_text(doc["content"])
                
                vector_doc = VectorDocument(
                    id=doc["id"],
                    content=doc["content"],
                    vector=vector,
                    metadata=doc.get("metadata", {}),
                    created_at=datetime.now()
                )
                vector_docs.append(vector_doc)
            
            # 添加到向量存储
            result = await self.vector_store.add_documents(vector_docs)
            
            # 记录指标
            self.metrics_collector.increment("documents_added", len(result))
            
            return result
            
        except Exception as e:
            logger.error(f"添加文档失败: {e}")
            self.metrics_collector.increment("add_documents_errors")
            raise
    
    async def search_documents(self, query: str, top_k: int = 10, 
                              filters: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """搜索文档"""
        try:
            # 生成查询向量
            query_vector = await self.embedding_service.embed_text(query)
            
            # 检查缓存
            cache_key = f"search:{hash(query)}:{top_k}:{hash(str(filters))}"
            cached_result = await self.cache_manager.get(cache_key)
            if cached_result:
                self.metrics_collector.increment("search_cache_hits")
                return cached_result
            
            # 执行搜索
            results = await self.vector_store.search(query_vector, top_k, filters)
            
            # 缓存结果
            await self.cache_manager.set(cache_key, results, ttl=settings.CACHE_TTL)
            
            # 记录指标
            self.metrics_collector.increment("searches_performed")
            self.metrics_collector.record("search_results_count", len(results))
            
            return results
            
        except Exception as e:
            logger.error(f"搜索文档失败: {e}")
            self.metrics_collector.increment("search_errors")
            raise
    
    async def delete_documents(self, document_ids: List[str]) -> bool:
        """删除文档"""
        try:
            result = await self.vector_store.delete_documents(document_ids)
            
            if result:
                self.metrics_collector.increment("documents_deleted", len(document_ids))
            else:
                self.metrics_collector.increment("delete_documents_errors")
            
            return result
            
        except Exception as e:
            logger.error(f"删除文档失败: {e}")
            self.metrics_collector.increment("delete_documents_errors")
            raise
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            if not self.vector_store:
                return False
            
            vector_store_healthy = await self.vector_store.health_check()
            embedding_service_healthy = await self.embedding_service.health_check()
            
            return vector_store_healthy and embedding_service_healthy
            
        except Exception:
            return False
    
    async def get_metrics(self) -> Dict[str, Any]:
        """获取指标"""
        try:
            vector_stats = await self.vector_store.get_stats() if self.vector_store else {}
            embedding_stats = await self.embedding_service.get_stats()
            metrics_stats = self.metrics_collector.get_metrics()
            
            return {
                "vector_store": vector_stats,
                "embedding_service": embedding_stats,
                "metrics": metrics_stats,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取指标失败: {e}")
            return {"error": str(e)}
    
    async def cleanup(self) -> None:
        """清理资源"""
        try:
            if self.vector_store:
                await self.vector_store.cleanup()
            
            await self.embedding_service.cleanup()
            
            logger.info("向量管理器资源清理完成")
            
        except Exception as e:
            logger.error(f"向量管理器资源清理失败: {e}")


# 导出的公共接口
__all__ = [
    'VectorManager',
    'VectorDocument',
    'SearchResult',
    'VectorStore',
    'WeaviateStore'
]