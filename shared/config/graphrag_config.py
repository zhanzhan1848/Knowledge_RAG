#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GraphRAG 知识图谱配置模块

该模块提供 GraphRAG 知识图谱的配置管理功能，包括：
- 存储配置
- LLM 配置
- 嵌入模型配置
- 文档处理配置
- 图谱构建配置

Author: Knowledge RAG Team
Date: 2024
"""

import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


class GraphRAGStorageType(Enum):
    """GraphRAG 存储类型枚举"""

    FILE = "file"
    BLOB = "blob"
    MEMORY = "memory"


class GraphRAGLLMType(Enum):
    """GraphRAG LLM 类型枚举"""

    OPENAI = "openai"
    AZURE_OPENAI = "azure_openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"


class GraphRAGEmbeddingType(Enum):
    """GraphRAG 嵌入模型类型枚举"""

    OPENAI = "openai"
    AZURE_OPENAI = "azure_openai"
    SENTENCE_TRANSFORMERS = "sentence_transformers"
    HUGGINGFACE = "huggingface"


@dataclass
class GraphRAGStorageConfig:
    """GraphRAG 存储配置"""

    type: GraphRAGStorageType = GraphRAGStorageType.FILE
    base_dir: str = "./data/graphrag"
    connection_string: Optional[str] = None
    container_name: Optional[str] = None

    def __post_init__(self):
        """初始化后处理"""
        if self.type == GraphRAGStorageType.FILE:
            Path(self.base_dir).mkdir(parents=True, exist_ok=True)


@dataclass
class GraphRAGLLMConfig:
    """GraphRAG LLM 配置"""

    type: GraphRAGLLMType = GraphRAGLLMType.OPENAI
    model: str = "gpt-3.5-turbo"
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    api_version: Optional[str] = None
    deployment_name: Optional[str] = None
    max_tokens: int = 8000
    temperature: float = 0.0
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    request_timeout: int = 180
    max_retries: int = 3
    concurrent_requests: int = 5


@dataclass
class GraphRAGEmbeddingConfig:
    """GraphRAG 嵌入模型配置"""

    type: GraphRAGEmbeddingType = GraphRAGEmbeddingType.OPENAI
    model: str = "text-embedding-ada-002"
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    api_version: Optional[str] = None
    deployment_name: Optional[str] = None
    batch_size: int = 16
    max_retries: int = 3
    request_timeout: int = 60
    concurrent_requests: int = 5
    vector_store_type: str = "lancedb"


@dataclass
class GraphRAGChunkingConfig:
    """GraphRAG 文档分块配置"""

    size: int = 1200
    overlap: int = 100
    group_by_columns: List[str] = field(default_factory=lambda: ["id"])
    strategy: str = "tokens"
    encoding_model: str = "cl100k_base"


@dataclass
class GraphRAGEntityExtractionConfig:
    """GraphRAG 实体提取配置"""

    prompt: Optional[str] = None
    entity_types: List[str] = field(
        default_factory=lambda: [
            "PERSON",
            "ORGANIZATION",
            "LOCATION",
            "EVENT",
            "CONCEPT",
        ]
    )
    max_gleanings: int = 1
    strategy: str = "graph_intelligence"


@dataclass
class GraphRAGCommunityConfig:
    """GraphRAG 社区检测配置"""

    hierarchical_communities: bool = True
    max_cluster_size: int = 10
    use_lcc: bool = True
    seed: int = 0xDEADBEEF
    levels: List[int] = field(default_factory=lambda: [0, 1, 2])


@dataclass
class GraphRAGSummarizationConfig:
    """GraphRAG 摘要配置"""

    prompt: Optional[str] = None
    max_length: int = 500
    strategy: str = "graph_intelligence"


@dataclass
class GraphRAGConfig:
    """GraphRAG 主配置类"""

    # 基础配置
    root_dir: str = "./data/graphrag"
    reporting_dir: str = "./data/graphrag/output"

    # 存储配置
    storage: GraphRAGStorageConfig = field(default_factory=GraphRAGStorageConfig)

    # LLM 配置
    llm: GraphRAGLLMConfig = field(default_factory=GraphRAGLLMConfig)

    # 嵌入配置
    embeddings: GraphRAGEmbeddingConfig = field(default_factory=GraphRAGEmbeddingConfig)

    # 文档处理配置
    chunking: GraphRAGChunkingConfig = field(default_factory=GraphRAGChunkingConfig)

    # 实体提取配置
    entity_extraction: GraphRAGEntityExtractionConfig = field(
        default_factory=GraphRAGEntityExtractionConfig
    )

    # 社区检测配置
    community_reports: GraphRAGCommunityConfig = field(
        default_factory=GraphRAGCommunityConfig
    )

    # 摘要配置
    summarize_descriptions: GraphRAGSummarizationConfig = field(
        default_factory=GraphRAGSummarizationConfig
    )

    # 缓存配置
    cache_type: str = "file"
    cache_base_dir: str = "./data/graphrag/cache"

    # 输入配置
    input_type: str = "file"
    input_file_type: str = "text"
    input_base_dir: str = "./data/graphrag/input"
    input_file_encoding: str = "utf-8"

    # 输出配置
    skip_workflows: List[str] = field(default_factory=list)

    @classmethod
    def from_env(cls) -> "GraphRAGConfig":
        """从环境变量创建配置"""
        config = cls()

        # 基础配置
        config.root_dir = os.getenv("GRAPHRAG_ROOT_DIR", config.root_dir)
        config.reporting_dir = os.getenv("GRAPHRAG_REPORTING_DIR", config.reporting_dir)

        # 存储配置
        config.storage.type = GraphRAGStorageType(
            os.getenv("GRAPHRAG_STORAGE_TYPE", "file")
        )
        config.storage.base_dir = os.getenv(
            "GRAPHRAG_STORAGE_BASE_DIR", config.storage.base_dir
        )

        # LLM 配置
        config.llm.type = GraphRAGLLMType(os.getenv("GRAPHRAG_LLM_TYPE", "openai"))
        config.llm.model = os.getenv("GRAPHRAG_LLM_MODEL", config.llm.model)
        config.llm.api_key = os.getenv("OPENAI_API_KEY") or os.getenv(
            "GRAPHRAG_LLM_API_KEY"
        )
        config.llm.api_base = os.getenv("GRAPHRAG_LLM_API_BASE")
        config.llm.max_tokens = int(
            os.getenv("GRAPHRAG_MAX_TOKENS", str(config.llm.max_tokens))
        )
        config.llm.temperature = float(
            os.getenv("GRAPHRAG_TEMPERATURE", str(config.llm.temperature))
        )

        # 嵌入配置
        config.embeddings.type = GraphRAGEmbeddingType(
            os.getenv("GRAPHRAG_EMBEDDING_TYPE", "openai")
        )
        config.embeddings.model = os.getenv(
            "GRAPHRAG_EMBEDDING_MODEL", config.embeddings.model
        )
        config.embeddings.api_key = os.getenv("OPENAI_API_KEY") or os.getenv(
            "GRAPHRAG_EMBEDDING_API_KEY"
        )
        config.embeddings.batch_size = int(
            os.getenv(
                "GRAPHRAG_EMBEDDING_BATCH_SIZE", str(config.embeddings.batch_size)
            )
        )

        # 分块配置
        config.chunking.size = int(
            os.getenv("GRAPHRAG_CHUNK_SIZE", str(config.chunking.size))
        )
        config.chunking.overlap = int(
            os.getenv("GRAPHRAG_CHUNK_OVERLAP", str(config.chunking.overlap))
        )

        # 社区配置
        community_level = os.getenv("GRAPHRAG_COMMUNITY_LEVEL")
        if community_level:
            config.community_reports.levels = [int(community_level)]

        # 缓存配置
        config.cache_base_dir = os.getenv(
            "GRAPHRAG_CACHE_BASE_DIR", config.cache_base_dir
        )

        # 输入配置
        config.input_base_dir = os.getenv(
            "GRAPHRAG_INPUT_BASE_DIR", config.input_base_dir
        )

        return config

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "root_dir": self.root_dir,
            "reporting": {"type": "file", "base_dir": self.reporting_dir},
            "storage": {
                "type": self.storage.type.value,
                "base_dir": self.storage.base_dir,
            },
            "cache": {"type": self.cache_type, "base_dir": self.cache_base_dir},
            "input": {
                "type": self.input_type,
                "file_type": self.input_file_type,
                "base_dir": self.input_base_dir,
                "file_encoding": self.input_file_encoding,
            },
            "llm": {
                "api_key": self.llm.api_key,
                "type": self.llm.type.value,
                "model": self.llm.model,
                "model_supports_json": True,
                "max_tokens": self.llm.max_tokens,
                "temperature": self.llm.temperature,
                "top_p": self.llm.top_p,
                "request_timeout": self.llm.request_timeout,
                "api_base": self.llm.api_base,
                "api_version": self.llm.api_version,
                "concurrent_requests": self.llm.concurrent_requests,
            },
            "embeddings": {
                "api_key": self.embeddings.api_key,
                "type": self.embeddings.type.value,
                "model": self.embeddings.model,
                "batch_size": self.embeddings.batch_size,
                "api_base": self.embeddings.api_base,
                "api_version": self.embeddings.api_version,
                "concurrent_requests": self.embeddings.concurrent_requests,
            },
            "chunks": {
                "size": self.chunking.size,
                "overlap": self.chunking.overlap,
                "group_by_columns": self.chunking.group_by_columns,
                "strategy": self.chunking.strategy,
                "encoding_model": self.chunking.encoding_model,
            },
            "entity_extraction": {
                "prompt": self.entity_extraction.prompt,
                "entity_types": self.entity_extraction.entity_types,
                "max_gleanings": self.entity_extraction.max_gleanings,
                "strategy": self.entity_extraction.strategy,
            },
            "community_reports": {
                "prompt": self.community_reports,
                "max_length": 2000,
                "strategy": "graph_intelligence",
            },
            "summarize_descriptions": {
                "prompt": self.summarize_descriptions.prompt,
                "max_length": self.summarize_descriptions.max_length,
                "strategy": self.summarize_descriptions.strategy,
            },
            "skip_workflows": self.skip_workflows,
        }

    def create_directories(self):
        """创建必要的目录"""
        directories = [
            self.root_dir,
            self.reporting_dir,
            self.storage.base_dir,
            self.cache_base_dir,
            self.input_base_dir,
        ]

        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)


class GraphRAGConfigManager:
    """GraphRAG 配置管理器"""

    def __init__(self, config: GraphRAGConfig):
        """初始化配置管理器"""
        self.config = config

    def validate_config(self) -> List[str]:
        """验证配置"""
        errors = []

        # 验证 LLM 配置
        if not self.config.llm.api_key:
            errors.append("LLM API key 未配置")

        # 验证嵌入配置
        if not self.config.embeddings.api_key:
            errors.append("Embedding API key 未配置")

        # 验证目录权限
        try:
            self.config.create_directories()
        except PermissionError:
            errors.append("无法创建必要的目录，请检查权限")

        return errors

    def save_config(self, file_path: str):
        """保存配置到文件"""
        import yaml

        config_dict = self.config.to_dict()

        with open(file_path, "w", encoding="utf-8") as f:
            yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True)

    def load_config(self, file_path: str) -> GraphRAGConfig:
        """从文件加载配置"""
        import yaml

        with open(file_path, "r", encoding="utf-8") as f:
            config_dict = yaml.safe_load(f)

        # 这里可以添加从字典创建配置的逻辑
        # 暂时返回当前配置
        return self.config


# 全局配置实例
graphrag_config = GraphRAGConfig.from_env()
graphrag_manager = GraphRAGConfigManager(graphrag_config)


# 导出的公共接口
__all__ = [
    "GraphRAGConfig",
    "GraphRAGStorageType",
    "GraphRAGLLMType",
    "GraphRAGEmbeddingType",
    "GraphRAGStorageConfig",
    "GraphRAGLLMConfig",
    "GraphRAGEmbeddingConfig",
    "GraphRAGChunkingConfig",
    "GraphRAGEntityExtractionConfig",
    "GraphRAGCommunityConfig",
    "GraphRAGSummarizationConfig",
    "GraphRAGConfigManager",
    "graphrag_config",
    "graphrag_manager",
]
