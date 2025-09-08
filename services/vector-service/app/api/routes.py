#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
向量服务API路由模块

该模块定义了向量服务的所有API端点，包括：
- 文档管理（添加、删除、更新、查询）
- 向量搜索
- 嵌入生成
- 健康检查和监控

Author: Knowledge RAG Team
Date: 2024
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Query, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator

from app.services.vector_manager import VectorManager, SearchResult
from app.services.embedding_service import EmbeddingService
from app.core.dependencies import get_vector_manager, get_embedding_service
from shared.utils.auth import verify_api_key
from shared.utils.rate_limiter import RateLimiter
from shared.utils.metrics import MetricsCollector

logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/api/v1", tags=["vector-service"])
metrics_collector = MetricsCollector()
rate_limiter = RateLimiter()


# Pydantic 模型定义
class DocumentInput(BaseModel):
    """文档输入模型"""
    id: str = Field(..., description="文档唯一标识")
    content: str = Field(..., min_length=1, description="文档内容")
    metadata: Optional[Dict[str, Any]] = Field(default={}, description="文档元数据")
    
    @validator('content')
    def validate_content(cls, v):
        if len(v.strip()) == 0:
            raise ValueError('文档内容不能为空')
        return v


class DocumentsInput(BaseModel):
    """批量文档输入模型"""
    documents: List[DocumentInput] = Field(..., min_items=1, max_items=100, description="文档列表")


class SearchRequest(BaseModel):
    """搜索请求模型"""
    query: str = Field(..., min_length=1, description="搜索查询")
    top_k: int = Field(default=10, ge=1, le=100, description="返回结果数量")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="过滤条件")
    
    @validator('query')
    def validate_query(cls, v):
        if len(v.strip()) == 0:
            raise ValueError('搜索查询不能为空')
        return v


class VectorSearchRequest(BaseModel):
    """向量搜索请求模型"""
    vector: List[float] = Field(..., min_items=1, description="查询向量")
    top_k: int = Field(default=10, ge=1, le=100, description="返回结果数量")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="过滤条件")


class EmbeddingRequest(BaseModel):
    """嵌入请求模型"""
    text: str = Field(..., min_length=1, description="待嵌入文本")
    
    @validator('text')
    def validate_text(cls, v):
        if len(v.strip()) == 0:
            raise ValueError('待嵌入文本不能为空')
        return v


class BatchEmbeddingRequest(BaseModel):
    """批量嵌入请求模型"""
    texts: List[str] = Field(..., min_items=1, max_items=100, description="待嵌入文本列表")
    
    @validator('texts')
    def validate_texts(cls, v):
        for text in v:
            if len(text.strip()) == 0:
                raise ValueError('待嵌入文本不能为空')
        return v


class DocumentResponse(BaseModel):
    """文档响应模型"""
    id: str
    content: str
    metadata: Dict[str, Any]
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class SearchResponse(BaseModel):
    """搜索响应模型"""
    results: List[Dict[str, Any]]
    total: int
    query: str
    processing_time: float
    timestamp: str


class EmbeddingResponse(BaseModel):
    """嵌入响应模型"""
    vector: List[float]
    dimensions: int
    model: str
    processing_time: float
    timestamp: str


class HealthResponse(BaseModel):
    """健康检查响应模型"""
    status: str
    timestamp: str
    services: Dict[str, Any]


class MetricsResponse(BaseModel):
    """指标响应模型"""
    metrics: Dict[str, Any]
    timestamp: str


# API 端点定义
@router.post("/documents", response_model=Dict[str, Any])
async def add_documents(
    request: DocumentsInput,
    vector_manager: VectorManager = Depends(get_vector_manager),
    api_key: str = Depends(verify_api_key)
):
    """添加文档"""
    try:
        start_time = datetime.now()
        
        # 速率限制检查
        await rate_limiter.check_rate_limit(api_key, "add_documents")
        
        # 转换为字典格式
        documents = [doc.dict() for doc in request.documents]
        
        # 添加文档
        document_ids = await vector_manager.add_documents(documents)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # 记录指标
        metrics_collector.increment("api_add_documents_requests")
        metrics_collector.record("api_add_documents_processing_time", processing_time)
        
        return {
            "message": "文档添加成功",
            "document_ids": document_ids,
            "count": len(document_ids),
            "processing_time": processing_time,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"添加文档失败: {e}")
        metrics_collector.increment("api_add_documents_errors")
        raise HTTPException(status_code=500, detail=f"添加文档失败: {str(e)}")


@router.post("/search", response_model=SearchResponse)
async def search_documents(
    request: SearchRequest,
    vector_manager: VectorManager = Depends(get_vector_manager),
    api_key: str = Depends(verify_api_key)
):
    """搜索文档"""
    try:
        start_time = datetime.now()
        
        # 速率限制检查
        await rate_limiter.check_rate_limit(api_key, "search")
        
        # 执行搜索
        results = await vector_manager.search_documents(
            query=request.query,
            top_k=request.top_k,
            filters=request.filters
        )
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # 转换结果格式
        search_results = [
            {
                "id": result.id,
                "content": result.content,
                "score": result.score,
                "metadata": result.metadata or {}
            }
            for result in results
        ]
        
        # 记录指标
        metrics_collector.increment("api_search_requests")
        metrics_collector.record("api_search_processing_time", processing_time)
        metrics_collector.record("api_search_results_count", len(search_results))
        
        return SearchResponse(
            results=search_results,
            total=len(search_results),
            query=request.query,
            processing_time=processing_time,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"搜索文档失败: {e}")
        metrics_collector.increment("api_search_errors")
        raise HTTPException(status_code=500, detail=f"搜索文档失败: {str(e)}")


@router.post("/search/vector", response_model=SearchResponse)
async def vector_search(
    request: VectorSearchRequest,
    vector_manager: VectorManager = Depends(get_vector_manager),
    api_key: str = Depends(verify_api_key)
):
    """向量搜索"""
    try:
        start_time = datetime.now()
        
        # 速率限制检查
        await rate_limiter.check_rate_limit(api_key, "vector_search")
        
        # 执行向量搜索
        results = await vector_manager.vector_store.search(
            query_vector=request.vector,
            top_k=request.top_k,
            filters=request.filters
        )
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # 转换结果格式
        search_results = [
            {
                "id": result.id,
                "content": result.content,
                "score": result.score,
                "metadata": result.metadata or {}
            }
            for result in results
        ]
        
        # 记录指标
        metrics_collector.increment("api_vector_search_requests")
        metrics_collector.record("api_vector_search_processing_time", processing_time)
        
        return SearchResponse(
            results=search_results,
            total=len(search_results),
            query="vector_search",
            processing_time=processing_time,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"向量搜索失败: {e}")
        metrics_collector.increment("api_vector_search_errors")
        raise HTTPException(status_code=500, detail=f"向量搜索失败: {str(e)}")


@router.delete("/documents")
async def delete_documents(
    document_ids: List[str] = Body(..., embed=True),
    vector_manager: VectorManager = Depends(get_vector_manager),
    api_key: str = Depends(verify_api_key)
):
    """删除文档"""
    try:
        start_time = datetime.now()
        
        # 速率限制检查
        await rate_limiter.check_rate_limit(api_key, "delete_documents")
        
        # 删除文档
        success = await vector_manager.delete_documents(document_ids)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # 记录指标
        metrics_collector.increment("api_delete_documents_requests")
        metrics_collector.record("api_delete_documents_processing_time", processing_time)
        
        if success:
            return {
                "message": "文档删除成功",
                "document_ids": document_ids,
                "count": len(document_ids),
                "processing_time": processing_time,
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail="文档删除失败")
        
    except Exception as e:
        logger.error(f"删除文档失败: {e}")
        metrics_collector.increment("api_delete_documents_errors")
        raise HTTPException(status_code=500, detail=f"删除文档失败: {str(e)}")


@router.post("/embeddings", response_model=EmbeddingResponse)
async def generate_embedding(
    request: EmbeddingRequest,
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    api_key: str = Depends(verify_api_key)
):
    """生成文本嵌入"""
    try:
        start_time = datetime.now()
        
        # 速率限制检查
        await rate_limiter.check_rate_limit(api_key, "embeddings")
        
        # 生成嵌入
        vector = await embedding_service.embed_text(request.text)
        dimensions = await embedding_service.get_dimensions()
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # 记录指标
        metrics_collector.increment("api_embeddings_requests")
        metrics_collector.record("api_embeddings_processing_time", processing_time)
        
        return EmbeddingResponse(
            vector=vector,
            dimensions=dimensions,
            model=embedding_service.provider.model_name if hasattr(embedding_service.provider, 'model_name') else "unknown",
            processing_time=processing_time,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"生成嵌入失败: {e}")
        metrics_collector.increment("api_embeddings_errors")
        raise HTTPException(status_code=500, detail=f"生成嵌入失败: {str(e)}")


@router.post("/embeddings/batch", response_model=Dict[str, Any])
async def generate_batch_embeddings(
    request: BatchEmbeddingRequest,
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    api_key: str = Depends(verify_api_key)
):
    """批量生成文本嵌入"""
    try:
        start_time = datetime.now()
        
        # 速率限制检查
        await rate_limiter.check_rate_limit(api_key, "batch_embeddings")
        
        # 批量生成嵌入
        vectors = await embedding_service.embed_texts(request.texts)
        dimensions = await embedding_service.get_dimensions()
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # 记录指标
        metrics_collector.increment("api_batch_embeddings_requests")
        metrics_collector.record("api_batch_embeddings_processing_time", processing_time)
        metrics_collector.record("api_batch_embeddings_count", len(vectors))
        
        return {
            "vectors": vectors,
            "dimensions": dimensions,
            "count": len(vectors),
            "model": embedding_service.provider.model_name if hasattr(embedding_service.provider, 'model_name') else "unknown",
            "processing_time": processing_time,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"批量生成嵌入失败: {e}")
        metrics_collector.increment("api_batch_embeddings_errors")
        raise HTTPException(status_code=500, detail=f"批量生成嵌入失败: {str(e)}")


@router.get("/health", response_model=HealthResponse)
async def health_check(
    vector_manager: VectorManager = Depends(get_vector_manager),
    embedding_service: EmbeddingService = Depends(get_embedding_service)
):
    """健康检查"""
    try:
        # 检查各服务状态
        vector_manager_healthy = await vector_manager.health_check()
        embedding_service_healthy = await embedding_service.health_check()
        
        overall_status = "healthy" if vector_manager_healthy and embedding_service_healthy else "unhealthy"
        
        return HealthResponse(
            status=overall_status,
            timestamp=datetime.now().isoformat(),
            services={
                "vector_manager": "healthy" if vector_manager_healthy else "unhealthy",
                "embedding_service": "healthy" if embedding_service_healthy else "unhealthy"
            }
        )
        
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return HealthResponse(
            status="error",
            timestamp=datetime.now().isoformat(),
            services={"error": str(e)}
        )


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics(
    vector_manager: VectorManager = Depends(get_vector_manager),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    api_key: str = Depends(verify_api_key)
):
    """获取服务指标"""
    try:
        # 获取各服务指标
        vector_metrics = await vector_manager.get_metrics()
        embedding_metrics = await embedding_service.get_stats()
        api_metrics = metrics_collector.get_metrics()
        
        return MetricsResponse(
            metrics={
                "vector_manager": vector_metrics,
                "embedding_service": embedding_metrics,
                "api": api_metrics
            },
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"获取指标失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取指标失败: {str(e)}")


@router.get("/info")
async def get_service_info(
    vector_manager: VectorManager = Depends(get_vector_manager),
    embedding_service: EmbeddingService = Depends(get_embedding_service)
):
    """获取服务信息"""
    try:
        # 获取服务配置信息
        embedding_dimensions = await embedding_service.get_dimensions()
        
        return {
            "service": "vector-service",
            "version": "1.0.0",
            "description": "Knowledge RAG 向量服务",
            "capabilities": {
                "vector_backends": ["weaviate", "chromadb", "faiss"],
                "embedding_providers": ["openai", "huggingface", "sentence_transformers"],
                "embedding_dimensions": embedding_dimensions,
                "max_batch_size": 100,
                "supported_operations": [
                    "add_documents",
                    "search_documents",
                    "vector_search",
                    "delete_documents",
                    "generate_embeddings",
                    "batch_embeddings"
                ]
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"获取服务信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取服务信息失败: {str(e)}")


# 导出路由器
__all__ = ['router']