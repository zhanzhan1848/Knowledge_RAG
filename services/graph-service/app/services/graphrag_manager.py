#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GraphRAG管理器模块

该模块提供GraphRAG的核心功能，包括：
- 知识图谱构建和索引
- GraphRAG查询处理
- 实体和关系提取
- 社区检测和摘要
- 图谱数据管理

Author: Knowledge RAG Team
Date: 2024
"""

import asyncio
import json
import logging
import os
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime

try:
    from graphrag.config import GraphRagConfig
    from graphrag.index import create_pipeline_config
    from graphrag.index.run import run_pipeline_with_config
    from graphrag.query.context_builder.entity_extraction import EntityVectorStoreKey
    from graphrag.query.indexer_adapters import (
        read_indexer_entities,
        read_indexer_relationships,
        read_indexer_reports,
        read_indexer_text_units,
    )
    from graphrag.query.llm.oai.chat_openai import ChatOpenAI
    from graphrag.query.llm.oai.embedding import OpenAIEmbedding
    from graphrag.query.structured_search.global_search.community_context import (
        GlobalCommunityContext,
    )
    from graphrag.query.structured_search.global_search.search import GlobalSearch
    from graphrag.query.structured_search.local_search.mixed_context import (
        LocalSearchMixedContext,
    )
    from graphrag.query.structured_search.local_search.search import LocalSearch

    GRAPHRAG_AVAILABLE = True
except ImportError:
    GRAPHRAG_AVAILABLE = False
    logging.warning("GraphRAG库未安装，某些功能将不可用")

from app.core.config import settings
from shared.utils.logger import get_logger
from shared.utils.metrics import MetricsCollector

logger = get_logger(__name__)
metrics = MetricsCollector()


class GraphRAGManager:
    """GraphRAG管理器"""

    def __init__(self):
        """初始化GraphRAG管理器"""
        self.work_dir = Path(settings.GRAPHRAG_WORK_DIR)
        self.index_path = Path(settings.GRAPHRAG_INDEX_PATH)
        self.config_file = settings.GRAPHRAG_CONFIG_FILE

        # 确保目录存在
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.index_path.mkdir(parents=True, exist_ok=True)

        # GraphRAG组件
        self.config: Optional[GraphRagConfig] = None
        self.global_search: Optional[GlobalSearch] = None
        self.local_search: Optional[LocalSearch] = None

        # 状态
        self.initialized = False
        self.indexing_in_progress = False

        logger.info(f"GraphRAG管理器初始化完成，工作目录: {self.work_dir}")

    async def initialize(self) -> bool:
        """初始化GraphRAG"""
        try:
            if not GRAPHRAG_AVAILABLE:
                logger.error("GraphRAG库未安装")
                return False

            # 加载或创建配置
            await self._load_or_create_config()

            # 初始化搜索引擎
            await self._initialize_search_engines()

            self.initialized = True
            metrics.increment("graphrag_initializations")
            logger.info("GraphRAG初始化成功")
            return True

        except Exception as e:
            logger.error(f"GraphRAG初始化失败: {e}")
            metrics.increment("graphrag_initialization_failures")
            return False

    async def _load_or_create_config(self):
        """加载或创建GraphRAG配置"""
        try:
            if self.config_file and Path(self.config_file).exists():
                # 从文件加载配置
                self.config = GraphRagConfig.from_file(self.config_file)
                logger.info(f"从文件加载GraphRAG配置: {self.config_file}")
            else:
                # 创建默认配置
                self.config = self._create_default_config()
                logger.info("创建默认GraphRAG配置")

        except Exception as e:
            logger.error(f"加载GraphRAG配置失败: {e}")
            raise

    def _create_default_config(self) -> GraphRagConfig:
        """创建默认GraphRAG配置"""
        config_dict = {
            "llm": {
                "api_key": settings.OPENAI_API_KEY,
                "type": "openai_chat",
                "model": settings.OPENAI_MODEL,
                "max_tokens": settings.OPENAI_MAX_TOKENS,
                "temperature": settings.OPENAI_TEMPERATURE,
                "api_base": settings.OPENAI_API_BASE,
            },
            "embeddings": {
                "api_key": settings.OPENAI_API_KEY,
                "type": "openai_embedding",
                "model": settings.OPENAI_EMBEDDING_MODEL,
                "api_base": settings.OPENAI_API_BASE,
            },
            "storage": {"type": "file", "base_dir": str(self.work_dir)},
            "cache": {"type": "file", "base_dir": str(self.work_dir / "cache")},
            "reporting": {"type": "file", "base_dir": str(self.work_dir / "reports")},
            "entity_extraction": {
                "prompt": settings.ENTITY_EXTRACTION_PROMPT,
                "entity_types": ["person", "organization", "location", "event"],
                "max_gleanings": 1,
            },
            "summarize_descriptions": {
                "prompt": "Summarize the following entity descriptions:",
                "max_length": 500,
            },
            "community_reports": {
                "prompt": "Generate a community report based on the following information:",
                "max_length": 1500,
                "max_input_length": 8000,
            },
            "claim_extraction": {
                "enabled": True,
                "prompt": "Extract claims from the following text:",
                "max_gleanings": 1,
            },
            "community_detection": {
                "algorithm": settings.COMMUNITY_DETECTION_ALGORITHM,
                "max_cluster_size": 10,
                "resolution": settings.COMMUNITY_DETECTION_RESOLUTION,
            },
            "chunks": {"size": 1200, "overlap": 100, "group_by_columns": ["id"]},
            "input": {
                "type": "file",
                "file_type": "text",
                "base_dir": str(self.work_dir / "input"),
                "file_encoding": "utf-8",
                "file_pattern": ".*\\.txt$",
            },
        }

        return GraphRagConfig.from_dict(config_dict)

    async def _initialize_search_engines(self):
        """初始化搜索引擎"""
        try:
            if not self.index_path.exists() or not any(self.index_path.iterdir()):
                logger.warning("索引不存在，需要先构建索引")
                return

            # 读取索引数据
            entities = read_indexer_entities(
                self.index_path, EntityVectorStoreKey.ID, EntityVectorStoreKey.TITLE
            )
            relationships = read_indexer_relationships(self.index_path)
            reports = read_indexer_reports(self.index_path)
            text_units = read_indexer_text_units(self.index_path)

            # 初始化LLM和嵌入模型
            llm = ChatOpenAI(
                api_key=settings.OPENAI_API_KEY,
                model=settings.OPENAI_MODEL,
                api_base=settings.OPENAI_API_BASE,
                max_tokens=settings.OPENAI_MAX_TOKENS,
                temperature=settings.OPENAI_TEMPERATURE,
            )

            embedding_model = OpenAIEmbedding(
                api_key=settings.OPENAI_API_KEY,
                model=settings.OPENAI_EMBEDDING_MODEL,
                api_base=settings.OPENAI_API_BASE,
            )

            # 初始化全局搜索
            context_builder = GlobalCommunityContext(
                community_reports=reports,
                entities=entities,
                token_encoder=llm.get_token_encoder(),
            )

            self.global_search = GlobalSearch(
                llm=llm,
                context_builder=context_builder,
                token_encoder=llm.get_token_encoder(),
                max_tokens=settings.OPENAI_MAX_TOKENS,
                llm_params={
                    "max_tokens": settings.OPENAI_MAX_TOKENS,
                    "temperature": settings.OPENAI_TEMPERATURE,
                },
            )

            # 初始化本地搜索
            local_context_builder = LocalSearchMixedContext(
                community_reports=reports,
                text_units=text_units,
                entities=entities,
                relationships=relationships,
                covariates=None,
                entity_text_embeddings=embedding_model,
                embedding_vectorstore_key=EntityVectorStoreKey.ID,
                text_embedder=embedding_model,
                token_encoder=llm.get_token_encoder(),
            )

            self.local_search = LocalSearch(
                llm=llm,
                context_builder=local_context_builder,
                token_encoder=llm.get_token_encoder(),
                llm_params={
                    "max_tokens": settings.OPENAI_MAX_TOKENS,
                    "temperature": settings.OPENAI_TEMPERATURE,
                },
                context_builder_params={
                    "text_unit_prop": 0.5,
                    "community_prop": 0.1,
                    "conversation_history_max_turns": 5,
                    "conversation_history_user_turns_only": True,
                    "top_k_mapped_entities": 10,
                    "top_k_relationships": 10,
                    "include_entity_rank": True,
                    "include_relationship_weight": True,
                    "include_community_rank": False,
                    "return_candidate_context": False,
                    "embedding_vectorstore_key": EntityVectorStoreKey.ID,
                    "max_tokens": 12000,
                },
            )

            logger.info("搜索引擎初始化成功")

        except Exception as e:
            logger.error(f"搜索引擎初始化失败: {e}")
            raise

    async def build_index(
        self, input_files: List[str], force_rebuild: bool = False
    ) -> Dict[str, Any]:
        """构建GraphRAG索引"""
        try:
            if self.indexing_in_progress:
                return {
                    "success": False,
                    "message": "索引构建正在进行中",
                    "status": "in_progress",
                }

            if not GRAPHRAG_AVAILABLE:
                return {
                    "success": False,
                    "message": "GraphRAG库未安装",
                    "status": "error",
                }

            self.indexing_in_progress = True
            start_time = datetime.now()

            try:
                # 准备输入文件
                input_dir = self.work_dir / "input"
                input_dir.mkdir(exist_ok=True)

                # 清理旧的输入文件
                if force_rebuild:
                    shutil.rmtree(input_dir, ignore_errors=True)
                    input_dir.mkdir(exist_ok=True)

                    # 清理索引目录
                    shutil.rmtree(self.index_path, ignore_errors=True)
                    self.index_path.mkdir(parents=True, exist_ok=True)

                # 复制输入文件
                for i, file_path in enumerate(input_files):
                    if os.path.exists(file_path):
                        dest_path = input_dir / f"input_{i}.txt"
                        shutil.copy2(file_path, dest_path)
                        logger.info(f"复制输入文件: {file_path} -> {dest_path}")

                # 创建管道配置
                pipeline_config = create_pipeline_config(self.config)

                # 运行索引管道
                logger.info("开始构建GraphRAG索引...")
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: run_pipeline_with_config(
                        pipeline_config,
                        callbacks=None,
                        progress_reporter=None,
                        emit=["parquet", "csv"],
                    ),
                )

                # 重新初始化搜索引擎
                await self._initialize_search_engines()

                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()

                metrics.increment("graphrag_index_builds")
                metrics.histogram("graphrag_index_build_duration", duration)

                logger.info(f"GraphRAG索引构建完成，耗时: {duration:.2f}秒")

                return {
                    "success": True,
                    "message": "索引构建成功",
                    "status": "completed",
                    "duration": duration,
                    "files_processed": len(input_files),
                    "timestamp": end_time.isoformat(),
                }

            except Exception as e:
                logger.error(f"索引构建失败: {e}")
                metrics.increment("graphrag_index_build_failures")

                return {
                    "success": False,
                    "message": f"索引构建失败: {str(e)}",
                    "status": "error",
                    "timestamp": datetime.now().isoformat(),
                }

        finally:
            self.indexing_in_progress = False

    async def global_search_query(self, query: str, **kwargs) -> Dict[str, Any]:
        """执行全局搜索查询"""
        try:
            if not self.initialized or not self.global_search:
                return {
                    "success": False,
                    "message": "GraphRAG未初始化或索引不存在",
                    "response": "",
                }

            start_time = datetime.now()

            # 执行全局搜索
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.global_search.search(
                    query=query,
                    community_level=kwargs.get(
                        "community_level", settings.GRAPHRAG_COMMUNITY_LEVEL
                    ),
                    response_type=kwargs.get(
                        "response_type", settings.GRAPHRAG_RESPONSE_TYPE
                    ),
                    **kwargs,
                ),
            )

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            metrics.increment("graphrag_global_searches")
            metrics.histogram("graphrag_global_search_duration", duration)

            logger.info(f"全局搜索完成，耗时: {duration:.2f}秒")

            return {
                "success": True,
                "response": result.response,
                "context_data": result.context_data,
                "completion_time": duration,
                "llm_calls": result.llm_calls,
                "prompt_tokens": result.prompt_tokens,
                "timestamp": end_time.isoformat(),
            }

        except Exception as e:
            logger.error(f"全局搜索失败: {e}")
            metrics.increment("graphrag_global_search_failures")

            return {
                "success": False,
                "message": f"全局搜索失败: {str(e)}",
                "response": "",
                "timestamp": datetime.now().isoformat(),
            }

    async def local_search_query(self, query: str, **kwargs) -> Dict[str, Any]:
        """执行本地搜索查询"""
        try:
            if not self.initialized or not self.local_search:
                return {
                    "success": False,
                    "message": "GraphRAG未初始化或索引不存在",
                    "response": "",
                }

            start_time = datetime.now()

            # 执行本地搜索
            result = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.local_search.search(query=query, **kwargs)
            )

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            metrics.increment("graphrag_local_searches")
            metrics.histogram("graphrag_local_search_duration", duration)

            logger.info(f"本地搜索完成，耗时: {duration:.2f}秒")

            return {
                "success": True,
                "response": result.response,
                "context_data": result.context_data,
                "completion_time": duration,
                "llm_calls": result.llm_calls,
                "prompt_tokens": result.prompt_tokens,
                "timestamp": end_time.isoformat(),
            }

        except Exception as e:
            logger.error(f"本地搜索失败: {e}")
            metrics.increment("graphrag_local_search_failures")

            return {
                "success": False,
                "message": f"本地搜索失败: {str(e)}",
                "response": "",
                "timestamp": datetime.now().isoformat(),
            }

    async def get_index_status(self) -> Dict[str, Any]:
        """获取索引状态"""
        try:
            status = {
                "initialized": self.initialized,
                "indexing_in_progress": self.indexing_in_progress,
                "index_exists": False,
                "index_path": str(self.index_path),
                "work_dir": str(self.work_dir),
                "files": {},
                "statistics": {},
            }

            if self.index_path.exists():
                status["index_exists"] = True

                # 检查索引文件
                index_files = {
                    "entities": (
                        self.index_path / "create_final_entities.parquet"
                    ).exists(),
                    "relationships": (
                        self.index_path / "create_final_relationships.parquet"
                    ).exists(),
                    "communities": (
                        self.index_path / "create_final_communities.parquet"
                    ).exists(),
                    "community_reports": (
                        self.index_path / "create_final_community_reports.parquet"
                    ).exists(),
                    "text_units": (
                        self.index_path / "create_final_text_units.parquet"
                    ).exists(),
                }
                status["files"] = index_files

                # 统计信息
                if all(index_files.values()):
                    try:
                        import pandas as pd

                        entities_df = pd.read_parquet(
                            self.index_path / "create_final_entities.parquet"
                        )
                        relationships_df = pd.read_parquet(
                            self.index_path / "create_final_relationships.parquet"
                        )
                        communities_df = pd.read_parquet(
                            self.index_path / "create_final_communities.parquet"
                        )

                        status["statistics"] = {
                            "entities_count": len(entities_df),
                            "relationships_count": len(relationships_df),
                            "communities_count": len(communities_df),
                        }

                    except Exception as e:
                        logger.warning(f"读取索引统计信息失败: {e}")

            return status

        except Exception as e:
            logger.error(f"获取索引状态失败: {e}")
            return {
                "initialized": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def get_entities(self, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """获取实体列表"""
        try:
            if not self.index_path.exists():
                return {"success": False, "message": "索引不存在", "entities": []}

            entities_file = self.index_path / "create_final_entities.parquet"
            if not entities_file.exists():
                return {"success": False, "message": "实体文件不存在", "entities": []}

            import pandas as pd

            entities_df = pd.read_parquet(entities_file)
            total_count = len(entities_df)

            # 分页
            entities_page = entities_df.iloc[offset : offset + limit]

            entities = []
            for _, row in entities_page.iterrows():
                entities.append(
                    {
                        "id": row.get("id", ""),
                        "title": row.get("title", ""),
                        "type": row.get("type", ""),
                        "description": row.get("description", ""),
                        "degree": row.get("degree", 0),
                        "community_ids": row.get("community_ids", []),
                    }
                )

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
        self, limit: int = 100, offset: int = 0
    ) -> Dict[str, Any]:
        """获取关系列表"""
        try:
            if not self.index_path.exists():
                return {"success": False, "message": "索引不存在", "relationships": []}

            relationships_file = self.index_path / "create_final_relationships.parquet"
            if not relationships_file.exists():
                return {
                    "success": False,
                    "message": "关系文件不存在",
                    "relationships": [],
                }

            import pandas as pd

            relationships_df = pd.read_parquet(relationships_file)
            total_count = len(relationships_df)

            # 分页
            relationships_page = relationships_df.iloc[offset : offset + limit]

            relationships = []
            for _, row in relationships_page.iterrows():
                relationships.append(
                    {
                        "id": row.get("id", ""),
                        "source": row.get("source", ""),
                        "target": row.get("target", ""),
                        "description": row.get("description", ""),
                        "weight": row.get("weight", 0.0),
                        "text_unit_ids": row.get("text_unit_ids", []),
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
        self, limit: int = 100, offset: int = 0
    ) -> Dict[str, Any]:
        """获取社区列表"""
        try:
            if not self.index_path.exists():
                return {"success": False, "message": "索引不存在", "communities": []}

            communities_file = self.index_path / "create_final_communities.parquet"
            if not communities_file.exists():
                return {
                    "success": False,
                    "message": "社区文件不存在",
                    "communities": [],
                }

            import pandas as pd

            communities_df = pd.read_parquet(communities_file)
            total_count = len(communities_df)

            # 分页
            communities_page = communities_df.iloc[offset : offset + limit]

            communities = []
            for _, row in communities_page.iterrows():
                communities.append(
                    {
                        "id": row.get("id", ""),
                        "title": row.get("title", ""),
                        "level": row.get("level", 0),
                        "size": row.get("size", 0),
                        "entity_ids": row.get("entity_ids", []),
                        "relationship_ids": row.get("relationship_ids", []),
                    }
                )

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

    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            status = {
                "healthy": True,
                "initialized": self.initialized,
                "graphrag_available": GRAPHRAG_AVAILABLE,
                "index_exists": self.index_path.exists()
                and any(self.index_path.iterdir()),
                "work_dir_writable": os.access(self.work_dir, os.W_OK),
                "services": {
                    "global_search": self.global_search is not None,
                    "local_search": self.local_search is not None,
                },
                "timestamp": datetime.now().isoformat(),
            }

            # 检查整体健康状态
            status["healthy"] = (
                status["graphrag_available"]
                and status["work_dir_writable"]
                and status["initialized"]
            )

            return status

        except Exception as e:
            logger.error(f"健康检查失败: {e}")
            return {
                "healthy": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def cleanup(self):
        """清理资源"""
        try:
            self.global_search = None
            self.local_search = None
            self.config = None
            self.initialized = False

            logger.info("GraphRAG管理器资源清理完成")

        except Exception as e:
            logger.error(f"GraphRAG管理器资源清理失败: {e}")


# 导出
__all__ = ["GraphRAGManager"]
