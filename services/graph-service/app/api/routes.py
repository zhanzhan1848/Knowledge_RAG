#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GraphRAG服务API路由模块

该模块定义了GraphRAG服务的所有RESTful API端点，包括：
- 知识图谱构建和管理
- GraphRAG查询处理
- 实体和关系管理
- 社区检测和分析
- 图谱数据查询和统计

Author: Knowledge RAG Team
Date: 2024
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, Path
from fastapi.responses import JSONResponse
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field, validator
import asyncio

from app.core.dependencies import (
    get_graphrag_manager,
    get_neo4j_manager,
    get_config_settings
)
from app.services.graphrag_manager import GraphRAGManager
from app.services.neo4j_manager import Neo4jManager
from app.core.config import Settings
from shared.utils.logger import get_logger
from shared.utils.metrics import MetricsCollector

logger = get_logger(__name__)
metrics = MetricsCollector()

# 创建路由器
router = APIRouter(prefix="/api/v1", tags=["GraphRAG"])


# ==================== Pydantic模型定义 ====================

class DocumentInput(BaseModel):
    """文档输入模型"""
    content: str = Field(..., description="文档内容")
    title: Optional[str] = Field(None, description="文档标题")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="文档元数据")
    document_id: Optional[str] = Field(None, description="文档ID")
    
    @validator('content')
    def validate_content(cls, v):
        if not v or not v.strip():
            raise ValueError("文档内容不能为空")
        if len(v) > 1000000:  # 1MB限制
            raise ValueError("文档内容过长，最大支持1MB")
        return v.strip()


class BatchDocumentInput(BaseModel):
    """批量文档输入模型"""
    documents: List[DocumentInput] = Field(..., description="文档列表")
    
    @validator('documents')
    def validate_documents(cls, v):
        if not v:
            raise ValueError("文档列表不能为空")
        if len(v) > 100:  # 批量限制
            raise ValueError("单次最多处理100个文档")
        return v


class GraphRAGQuery(BaseModel):
    """GraphRAG查询模型"""
    query: str = Field(..., description="查询内容")
    query_type: str = Field(default="global", description="查询类型：global或local")
    community_level: Optional[int] = Field(default=2, description="社区层级")
    response_type: str = Field(default="multiple_paragraphs", description="响应类型")
    max_tokens: Optional[int] = Field(default=1500, description="最大token数")
    
    @validator('query')
    def validate_query(cls, v):
        if not v or not v.strip():
            raise ValueError("查询内容不能为空")
        return v.strip()
    
    @validator('query_type')
    def validate_query_type(cls, v):
        if v not in ["global", "local"]:
            raise ValueError("查询类型必须是global或local")
        return v


class EntityInput(BaseModel):
    """实体输入模型"""
    id: str = Field(..., description="实体ID")
    title: str = Field(..., description="实体标题")
    type: Optional[str] = Field(default="", description="实体类型")
    description: Optional[str] = Field(default="", description="实体描述")
    degree: Optional[int] = Field(default=0, description="实体度数")
    community_ids: Optional[List[str]] = Field(default_factory=list, description="所属社区ID列表")


class RelationshipInput(BaseModel):
    """关系输入模型"""
    id: str = Field(..., description="关系ID")
    source: str = Field(..., description="源实体ID")
    target: str = Field(..., description="目标实体ID")
    type: Optional[str] = Field(default="RELATED_TO", description="关系类型")
    description: Optional[str] = Field(default="", description="关系描述")
    weight: Optional[float] = Field(default=1.0, description="关系权重")
    text_unit_ids: Optional[List[str]] = Field(default_factory=list, description="文本单元ID列表")


class CommunityInput(BaseModel):
    """社区输入模型"""
    id: str = Field(..., description="社区ID")
    title: Optional[str] = Field(default="", description="社区标题")
    level: Optional[int] = Field(default=0, description="社区层级")
    size: Optional[int] = Field(default=0, description="社区大小")
    entity_ids: Optional[List[str]] = Field(default_factory=list, description="实体ID列表")
    relationship_ids: Optional[List[str]] = Field(default_factory=list, description="关系ID列表")


class SearchQuery(BaseModel):
    """搜索查询模型"""
    query: str = Field(..., description="搜索关键词")
    limit: Optional[int] = Field(default=10, description="返回结果数量限制")
    
    @validator('query')
    def validate_query(cls, v):
        if not v or not v.strip():
            raise ValueError("搜索关键词不能为空")
        return v.strip()


class PathQuery(BaseModel):
    """路径查询模型"""
    source_id: str = Field(..., description="源实体ID")
    target_id: str = Field(..., description="目标实体ID")
    max_depth: Optional[int] = Field(default=5, description="最大搜索深度")


# ==================== GraphRAG核心功能路由 ====================

@router.post("/documents/build-index", summary="构建知识图谱索引")
async def build_graph_index(
    document: DocumentInput,
    background_tasks: BackgroundTasks,
    graphrag_manager: GraphRAGManager = Depends(get_graphrag_manager)
):
    """构建单个文档的知识图谱索引"""
    try:
        metrics.increment("graphrag_index_build_requests")
        
        # 异步构建索引
        task_id = f"build_index_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        background_tasks.add_task(
            graphrag_manager.build_index,
            documents=[document.dict()],
            task_id=task_id
        )
        
        return JSONResponse(
            status_code=202,
            content={
                "success": True,
                "message": "索引构建任务已启动",
                "task_id": task_id,
                "status": "processing"
            }
        )
        
    except Exception as e:
        logger.error(f"构建索引失败: {e}")
        metrics.increment("graphrag_index_build_failures")
        raise HTTPException(status_code=500, detail=f"构建索引失败: {str(e)}")


@router.post("/documents/batch-build-index", summary="批量构建知识图谱索引")
async def batch_build_graph_index(
    batch_input: BatchDocumentInput,
    background_tasks: BackgroundTasks,
    graphrag_manager: GraphRAGManager = Depends(get_graphrag_manager)
):
    """批量构建文档的知识图谱索引"""
    try:
        metrics.increment("graphrag_batch_index_build_requests")
        
        # 异步批量构建索引
        task_id = f"batch_build_index_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        documents = [doc.dict() for doc in batch_input.documents]
        
        background_tasks.add_task(
            graphrag_manager.build_index,
            documents=documents,
            task_id=task_id
        )
        
        return JSONResponse(
            status_code=202,
            content={
                "success": True,
                "message": f"批量索引构建任务已启动，共{len(documents)}个文档",
                "task_id": task_id,
                "document_count": len(documents),
                "status": "processing"
            }
        )
        
    except Exception as e:
        logger.error(f"批量构建索引失败: {e}")
        metrics.increment("graphrag_batch_index_build_failures")
        raise HTTPException(status_code=500, detail=f"批量构建索引失败: {str(e)}")


@router.post("/query", summary="GraphRAG查询")
async def graphrag_query(
    query_input: GraphRAGQuery,
    graphrag_manager: GraphRAGManager = Depends(get_graphrag_manager)
):
    """执行GraphRAG查询"""
    try:
        metrics.increment("graphrag_query_requests")
        start_time = datetime.now()
        
        # 执行查询
        result = await graphrag_manager.query(
            query=query_input.query,
            query_type=query_input.query_type,
            community_level=query_input.community_level,
            response_type=query_input.response_type,
            max_tokens=query_input.max_tokens
        )
        
        # 计算查询时间
        query_time = (datetime.now() - start_time).total_seconds()
        metrics.record("graphrag_query_duration", query_time)
        
        if result.get("success"):
            metrics.increment("graphrag_query_successes")
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "result": result.get("result"),
                    "query": query_input.query,
                    "query_type": query_input.query_type,
                    "community_level": query_input.community_level,
                    "query_time": query_time,
                    "timestamp": datetime.now().isoformat()
                }
            )
        else:
            metrics.increment("graphrag_query_failures")
            raise HTTPException(
                status_code=400, 
                detail=result.get("message", "查询失败")
            )
            
    except Exception as e:
        logger.error(f"GraphRAG查询失败: {e}")
        metrics.increment("graphrag_query_errors")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/index/status", summary="获取索引状态")
async def get_index_status(
    graphrag_manager: GraphRAGManager = Depends(get_graphrag_manager)
):
    """获取知识图谱索引状态"""
    try:
        status = await graphrag_manager.get_index_status()
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "status": status,
                "timestamp": datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"获取索引状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取索引状态失败: {str(e)}")


# ==================== 图数据库管理路由 ====================

@router.post("/entities", summary="创建实体")
async def create_entity(
    entity: EntityInput,
    neo4j_manager: Neo4jManager = Depends(get_neo4j_manager)
):
    """创建新实体"""
    try:
        result = await neo4j_manager.create_entity(entity.dict())
        
        if result.get("success"):
            return JSONResponse(
                status_code=201,
                content=result
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=result.get("message", "创建实体失败")
            )
            
    except Exception as e:
        logger.error(f"创建实体失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建实体失败: {str(e)}")


@router.get("/entities", summary="获取实体列表")
async def get_entities(
    limit: int = Query(default=100, ge=1, le=1000, description="返回数量限制"),
    offset: int = Query(default=0, ge=0, description="偏移量"),
    entity_type: Optional[str] = Query(default=None, description="实体类型过滤"),
    neo4j_manager: Neo4jManager = Depends(get_neo4j_manager)
):
    """获取实体列表"""
    try:
        result = await neo4j_manager.get_entities(
            limit=limit,
            offset=offset,
            entity_type=entity_type
        )
        
        return JSONResponse(
            status_code=200,
            content=result
        )
        
    except Exception as e:
        logger.error(f"获取实体列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取实体列表失败: {str(e)}")


@router.post("/relationships", summary="创建关系")
async def create_relationship(
    relationship: RelationshipInput,
    neo4j_manager: Neo4jManager = Depends(get_neo4j_manager)
):
    """创建新关系"""
    try:
        result = await neo4j_manager.create_relationship(relationship.dict())
        
        if result.get("success"):
            return JSONResponse(
                status_code=201,
                content=result
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=result.get("message", "创建关系失败")
            )
            
    except Exception as e:
        logger.error(f"创建关系失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建关系失败: {str(e)}")


@router.get("/relationships", summary="获取关系列表")
async def get_relationships(
    limit: int = Query(default=100, ge=1, le=1000, description="返回数量限制"),
    offset: int = Query(default=0, ge=0, description="偏移量"),
    source_id: Optional[str] = Query(default=None, description="源实体ID过滤"),
    target_id: Optional[str] = Query(default=None, description="目标实体ID过滤"),
    neo4j_manager: Neo4jManager = Depends(get_neo4j_manager)
):
    """获取关系列表"""
    try:
        result = await neo4j_manager.get_relationships(
            limit=limit,
            offset=offset,
            source_id=source_id,
            target_id=target_id
        )
        
        return JSONResponse(
            status_code=200,
            content=result
        )
        
    except Exception as e:
        logger.error(f"获取关系列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取关系列表失败: {str(e)}")


@router.post("/communities", summary="创建社区")
async def create_community(
    community: CommunityInput,
    neo4j_manager: Neo4jManager = Depends(get_neo4j_manager)
):
    """创建新社区"""
    try:
        result = await neo4j_manager.create_community(community.dict())
        
        if result.get("success"):
            return JSONResponse(
                status_code=201,
                content=result
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=result.get("message", "创建社区失败")
            )
            
    except Exception as e:
        logger.error(f"创建社区失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建社区失败: {str(e)}")


@router.get("/communities", summary="获取社区列表")
async def get_communities(
    limit: int = Query(default=100, ge=1, le=1000, description="返回数量限制"),
    offset: int = Query(default=0, ge=0, description="偏移量"),
    level: Optional[int] = Query(default=None, description="社区层级过滤"),
    neo4j_manager: Neo4jManager = Depends(get_neo4j_manager)
):
    """获取社区列表"""
    try:
        result = await neo4j_manager.get_communities(
            limit=limit,
            offset=offset,
            level=level
        )
        
        return JSONResponse(
            status_code=200,
            content=result
        )
        
    except Exception as e:
        logger.error(f"获取社区列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取社区列表失败: {str(e)}")


# ==================== 图谱查询和分析路由 ====================

@router.post("/search/entities", summary="搜索实体")
async def search_entities(
    search_query: SearchQuery,
    neo4j_manager: Neo4jManager = Depends(get_neo4j_manager)
):
    """搜索实体"""
    try:
        result = await neo4j_manager.search_entities(
            query=search_query.query,
            limit=search_query.limit
        )
        
        return JSONResponse(
            status_code=200,
            content=result
        )
        
    except Exception as e:
        logger.error(f"搜索实体失败: {e}")
        raise HTTPException(status_code=500, detail=f"搜索实体失败: {str(e)}")


@router.get("/entities/{entity_id}/neighbors", summary="获取实体邻居")
async def get_entity_neighbors(
    entity_id: str = Path(..., description="实体ID"),
    depth: int = Query(default=1, ge=1, le=3, description="搜索深度"),
    limit: int = Query(default=50, ge=1, le=200, description="返回数量限制"),
    neo4j_manager: Neo4jManager = Depends(get_neo4j_manager)
):
    """获取实体的邻居节点"""
    try:
        result = await neo4j_manager.get_entity_neighbors(
            entity_id=entity_id,
            depth=depth,
            limit=limit
        )
        
        return JSONResponse(
            status_code=200,
            content=result
        )
        
    except Exception as e:
        logger.error(f"获取实体邻居失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取实体邻居失败: {str(e)}")


@router.post("/path/shortest", summary="获取最短路径")
async def get_shortest_path(
    path_query: PathQuery,
    neo4j_manager: Neo4jManager = Depends(get_neo4j_manager)
):
    """获取两个实体之间的最短路径"""
    try:
        result = await neo4j_manager.get_shortest_path(
            source_id=path_query.source_id,
            target_id=path_query.target_id,
            max_depth=path_query.max_depth
        )
        
        return JSONResponse(
            status_code=200,
            content=result
        )
        
    except Exception as e:
        logger.error(f"获取最短路径失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取最短路径失败: {str(e)}")


@router.get("/statistics", summary="获取图谱统计信息")
async def get_graph_statistics(
    neo4j_manager: Neo4jManager = Depends(get_neo4j_manager)
):
    """获取知识图谱统计信息"""
    try:
        result = await neo4j_manager.get_graph_statistics()
        
        return JSONResponse(
            status_code=200,
            content=result
        )
        
    except Exception as e:
        logger.error(f"获取图谱统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取图谱统计信息失败: {str(e)}")


# ==================== 管理功能路由 ====================

@router.delete("/graph/clear", summary="清空图谱数据")
async def clear_graph(
    neo4j_manager: Neo4jManager = Depends(get_neo4j_manager)
):
    """清空所有图谱数据"""
    try:
        result = await neo4j_manager.clear_graph()
        
        if result.get("success"):
            return JSONResponse(
                status_code=200,
                content=result
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=result.get("message", "清空图谱数据失败")
            )
            
    except Exception as e:
        logger.error(f"清空图谱数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"清空图谱数据失败: {str(e)}")


@router.get("/health", summary="健康检查")
async def health_check(
    graphrag_manager: GraphRAGManager = Depends(get_graphrag_manager),
    neo4j_manager: Neo4jManager = Depends(get_neo4j_manager)
):
    """服务健康检查"""
    try:
        # 检查GraphRAG管理器
        graphrag_health = await graphrag_manager.health_check()
        
        # 检查Neo4j管理器
        neo4j_health = await neo4j_manager.health_check()
        
        # 综合健康状态
        overall_healthy = (
            graphrag_health.get("healthy", False) and 
            neo4j_health.get("healthy", False)
        )
        
        status_code = 200 if overall_healthy else 503
        
        return JSONResponse(
            status_code=status_code,
            content={
                "healthy": overall_healthy,
                "services": {
                    "graphrag": graphrag_health,
                    "neo4j": neo4j_health
                },
                "timestamp": datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "healthy": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )


@router.get("/metrics", summary="获取服务指标")
async def get_metrics(
    settings: Settings = Depends(get_config_settings)
):
    """获取服务性能指标"""
    try:
        # 获取指标数据
        metrics_data = metrics.get_all_metrics()
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "metrics": metrics_data,
                "service": "graph-service",
                "version": settings.VERSION,
                "timestamp": datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"获取服务指标失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取服务指标失败: {str(e)}")


# 导出路由器
__all__ = ['router']