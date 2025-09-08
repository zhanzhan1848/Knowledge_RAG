#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GraphRAG服务配置模块

该模块定义了GraphRAG服务的所有配置项，包括：
- 基础服务配置
- GraphRAG配置
- 知识图谱配置
- LLM配置
- 嵌入模型配置
- 存储配置
- 缓存配置
- 监控配置
- 安全配置

Author: Knowledge RAG Team
Date: 2024
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseSettings, Field, validator


class GraphRAGServiceSettings(BaseSettings):
    """GraphRAG服务配置类"""

    # ==================== 基础服务配置 ====================
    SERVICE_NAME: str = Field(default="graph-service", description="服务名称")
    HOST: str = Field(default="0.0.0.0", description="服务主机")
    PORT: int = Field(default=8003, description="服务端口")
    DEBUG: bool = Field(default=False, description="调试模式")
    WORKERS: int = Field(default=4, description="工作进程数")

    # 日志配置
    LOG_LEVEL: str = Field(default="INFO", description="日志级别")
    ACCESS_LOG: bool = Field(default=True, description="访问日志")
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="日志格式",
    )

    # CORS配置
    ENABLE_CORS: bool = Field(default=True, description="启用CORS")
    CORS_ORIGINS: List[str] = Field(default=["*"], description="CORS允许的源")

    # ==================== GraphRAG配置 ====================
    # GraphRAG工作目录
    GRAPHRAG_WORK_DIR: str = Field(
        default="./data/graphrag", description="GraphRAG工作目录"
    )

    # GraphRAG配置文件
    GRAPHRAG_CONFIG_FILE: Optional[str] = Field(
        default=None, description="GraphRAG配置文件路径"
    )

    # GraphRAG索引配置
    GRAPHRAG_INDEX_TYPE: str = Field(default="file", description="GraphRAG索引类型")

    GRAPHRAG_INDEX_PATH: str = Field(
        default="./data/graphrag/output", description="GraphRAG索引路径"
    )

    # GraphRAG查询配置
    GRAPHRAG_QUERY_TYPE: str = Field(
        default="global", description="GraphRAG查询类型 (global/local)"
    )

    GRAPHRAG_COMMUNITY_LEVEL: int = Field(default=2, description="社区层级")

    GRAPHRAG_RESPONSE_TYPE: str = Field(
        default="multiple paragraphs", description="响应类型"
    )

    # ==================== 知识图谱配置 ====================
    # Neo4j配置
    NEO4J_URI: str = Field(default="bolt://localhost:7687", description="Neo4j连接URI")
    NEO4J_USERNAME: str = Field(default="neo4j", description="Neo4j用户名")
    NEO4J_PASSWORD: str = Field(default="password", description="Neo4j密码")
    NEO4J_DATABASE: str = Field(default="neo4j", description="Neo4j数据库名")

    # 图谱构建配置
    GRAPH_MAX_ENTITIES: int = Field(default=10000, description="最大实体数量")
    GRAPH_MAX_RELATIONSHIPS: int = Field(default=50000, description="最大关系数量")

    # 实体提取配置
    ENTITY_EXTRACTION_MODEL: str = Field(default="gpt-4", description="实体提取模型")
    ENTITY_EXTRACTION_PROMPT: str = Field(
        default="Extract entities and relationships from the following text:",
        description="实体提取提示词",
    )

    # 关系提取配置
    RELATIONSHIP_EXTRACTION_MODEL: str = Field(
        default="gpt-4", description="关系提取模型"
    )
    RELATIONSHIP_EXTRACTION_PROMPT: str = Field(
        default="Extract relationships between entities from the following text:",
        description="关系提取提示词",
    )

    # 社区检测配置
    COMMUNITY_DETECTION_ALGORITHM: str = Field(
        default="leiden", description="社区检测算法"
    )
    COMMUNITY_DETECTION_RESOLUTION: float = Field(
        default=1.0, description="社区检测分辨率"
    )

    # ==================== LLM配置 ====================
    # OpenAI配置
    OPENAI_API_KEY: Optional[str] = Field(default=None, description="OpenAI API密钥")
    OPENAI_API_BASE: str = Field(
        default="https://api.openai.com/v1", description="OpenAI API基础URL"
    )
    OPENAI_MODEL: str = Field(default="gpt-4", description="OpenAI模型")
    OPENAI_MAX_TOKENS: int = Field(default=4000, description="最大令牌数")
    OPENAI_TEMPERATURE: float = Field(default=0.1, description="温度参数")

    # Anthropic配置
    ANTHROPIC_API_KEY: Optional[str] = Field(
        default=None, description="Anthropic API密钥"
    )
    ANTHROPIC_MODEL: str = Field(
        default="claude-3-sonnet-20240229", description="Anthropic模型"
    )

    # 本地模型配置
    LOCAL_LLM_ENDPOINT: Optional[str] = Field(default=None, description="本地LLM端点")
    LOCAL_LLM_MODEL: str = Field(default="llama2", description="本地LLM模型")

    # ==================== 嵌入模型配置 ====================
    # 嵌入模型类型
    EMBEDDING_MODEL_TYPE: str = Field(
        default="openai",
        description="嵌入模型类型 (openai/huggingface/sentence_transformers)",
    )

    # OpenAI嵌入配置
    OPENAI_EMBEDDING_MODEL: str = Field(
        default="text-embedding-ada-002", description="OpenAI嵌入模型"
    )
    OPENAI_EMBEDDING_DIMENSIONS: int = Field(default=1536, description="OpenAI嵌入维度")

    # HuggingFace嵌入配置
    HUGGINGFACE_EMBEDDING_MODEL: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="HuggingFace嵌入模型",
    )

    # Sentence Transformers配置
    SENTENCE_TRANSFORMERS_MODEL: str = Field(
        default="all-MiniLM-L6-v2", description="Sentence Transformers模型"
    )

    # ==================== 存储配置 ====================
    # 文件存储配置
    STORAGE_TYPE: str = Field(default="local", description="存储类型 (local/s3/azure)")
    STORAGE_PATH: str = Field(default="./data/storage", description="本地存储路径")

    # S3配置
    AWS_ACCESS_KEY_ID: Optional[str] = Field(default=None, description="AWS访问密钥ID")
    AWS_SECRET_ACCESS_KEY: Optional[str] = Field(
        default=None, description="AWS秘密访问密钥"
    )
    AWS_REGION: str = Field(default="us-east-1", description="AWS区域")
    S3_BUCKET: Optional[str] = Field(default=None, description="S3存储桶")

    # Azure配置
    AZURE_STORAGE_CONNECTION_STRING: Optional[str] = Field(
        default=None, description="Azure存储连接字符串"
    )
    AZURE_CONTAINER_NAME: Optional[str] = Field(
        default=None, description="Azure容器名称"
    )

    # ==================== 缓存配置 ====================
    # Redis配置
    REDIS_URL: str = Field(
        default="redis://localhost:6379/2", description="Redis连接URL"
    )
    REDIS_PASSWORD: Optional[str] = Field(default=None, description="Redis密码")
    REDIS_DB: int = Field(default=2, description="Redis数据库")

    # 缓存配置
    CACHE_TTL: int = Field(default=3600, description="缓存TTL（秒）")
    CACHE_MAX_SIZE: int = Field(default=1000, description="缓存最大大小")
    ENABLE_CACHE: bool = Field(default=True, description="启用缓存")

    # ==================== 搜索配置 ====================
    # 搜索参数
    DEFAULT_SEARCH_LIMIT: int = Field(default=10, description="默认搜索限制")
    MAX_SEARCH_LIMIT: int = Field(default=100, description="最大搜索限制")
    SEARCH_SIMILARITY_THRESHOLD: float = Field(
        default=0.7, description="搜索相似度阈值"
    )

    # ==================== 性能配置 ====================
    # 并发配置
    MAX_CONCURRENT_REQUESTS: int = Field(default=100, description="最大并发请求数")
    REQUEST_TIMEOUT: int = Field(default=300, description="请求超时时间（秒）")

    # 批处理配置
    BATCH_SIZE: int = Field(default=100, description="批处理大小")
    MAX_BATCH_SIZE: int = Field(default=1000, description="最大批处理大小")

    # ==================== 监控配置 ====================
    # Prometheus配置
    ENABLE_METRICS: bool = Field(default=True, description="启用指标收集")
    METRICS_PORT: int = Field(default=9003, description="指标端口")

    # 健康检查配置
    HEALTH_CHECK_INTERVAL: int = Field(default=30, description="健康检查间隔（秒）")

    # ==================== 安全配置 ====================
    # JWT配置
    JWT_SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production", description="JWT密钥"
    )
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT算法")
    JWT_EXPIRE_MINUTES: int = Field(default=1440, description="JWT过期时间（分钟）")

    # API密钥配置
    API_KEY_HEADER: str = Field(default="X-API-Key", description="API密钥头")
    REQUIRE_API_KEY: bool = Field(default=False, description="需要API密钥")

    # 速率限制配置
    RATE_LIMIT_ENABLED: bool = Field(default=True, description="启用速率限制")
    RATE_LIMIT_REQUESTS: int = Field(default=100, description="速率限制请求数")
    RATE_LIMIT_WINDOW: int = Field(default=60, description="速率限制窗口（秒）")

    # ==================== 验证器 ====================
    @validator("GRAPHRAG_WORK_DIR", "GRAPHRAG_INDEX_PATH", "STORAGE_PATH")
    def validate_paths(cls, v):
        """验证路径配置"""
        if v:
            path = Path(v)
            path.mkdir(parents=True, exist_ok=True)
        return v

    @validator("PORT", "METRICS_PORT")
    def validate_ports(cls, v):
        """验证端口配置"""
        if not (1 <= v <= 65535):
            raise ValueError(f"端口必须在1-65535范围内: {v}")
        return v

    @validator("LOG_LEVEL")
    def validate_log_level(cls, v):
        """验证日志级别"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"日志级别必须是: {valid_levels}")
        return v.upper()

    @validator("EMBEDDING_MODEL_TYPE")
    def validate_embedding_model_type(cls, v):
        """验证嵌入模型类型"""
        valid_types = ["openai", "huggingface", "sentence_transformers"]
        if v not in valid_types:
            raise ValueError(f"嵌入模型类型必须是: {valid_types}")
        return v

    @validator("STORAGE_TYPE")
    def validate_storage_type(cls, v):
        """验证存储类型"""
        valid_types = ["local", "s3", "azure"]
        if v not in valid_types:
            raise ValueError(f"存储类型必须是: {valid_types}")
        return v

    @validator("GRAPHRAG_QUERY_TYPE")
    def validate_query_type(cls, v):
        """验证查询类型"""
        valid_types = ["global", "local"]
        if v not in valid_types:
            raise ValueError(f"查询类型必须是: {valid_types}")
        return v

    @validator("COMMUNITY_DETECTION_ALGORITHM")
    def validate_community_algorithm(cls, v):
        """验证社区检测算法"""
        valid_algorithms = ["leiden", "louvain", "label_propagation"]
        if v not in valid_algorithms:
            raise ValueError(f"社区检测算法必须是: {valid_algorithms}")
        return v

    # ==================== 配置方法 ====================
    def get_graphrag_config(self) -> Dict[str, Any]:
        """获取GraphRAG配置"""
        return {
            "work_dir": self.GRAPHRAG_WORK_DIR,
            "config_file": self.GRAPHRAG_CONFIG_FILE,
            "index_type": self.GRAPHRAG_INDEX_TYPE,
            "index_path": self.GRAPHRAG_INDEX_PATH,
            "query_type": self.GRAPHRAG_QUERY_TYPE,
            "community_level": self.GRAPHRAG_COMMUNITY_LEVEL,
            "response_type": self.GRAPHRAG_RESPONSE_TYPE,
        }

    def get_llm_config(self) -> Dict[str, Any]:
        """获取LLM配置"""
        return {
            "openai": {
                "api_key": self.OPENAI_API_KEY,
                "api_base": self.OPENAI_API_BASE,
                "model": self.OPENAI_MODEL,
                "max_tokens": self.OPENAI_MAX_TOKENS,
                "temperature": self.OPENAI_TEMPERATURE,
            },
            "anthropic": {
                "api_key": self.ANTHROPIC_API_KEY,
                "model": self.ANTHROPIC_MODEL,
            },
            "local": {
                "endpoint": self.LOCAL_LLM_ENDPOINT,
                "model": self.LOCAL_LLM_MODEL,
            },
        }

    def get_embedding_config(self) -> Dict[str, Any]:
        """获取嵌入配置"""
        return {
            "type": self.EMBEDDING_MODEL_TYPE,
            "openai": {
                "model": self.OPENAI_EMBEDDING_MODEL,
                "dimensions": self.OPENAI_EMBEDDING_DIMENSIONS,
            },
            "huggingface": {"model": self.HUGGINGFACE_EMBEDDING_MODEL},
            "sentence_transformers": {"model": self.SENTENCE_TRANSFORMERS_MODEL},
        }

    def get_neo4j_config(self) -> Dict[str, Any]:
        """获取Neo4j配置"""
        return {
            "uri": self.NEO4J_URI,
            "username": self.NEO4J_USERNAME,
            "password": self.NEO4J_PASSWORD,
            "database": self.NEO4J_DATABASE,
        }

    def get_storage_config(self) -> Dict[str, Any]:
        """获取存储配置"""
        return {
            "type": self.STORAGE_TYPE,
            "local": {"path": self.STORAGE_PATH},
            "s3": {
                "access_key_id": self.AWS_ACCESS_KEY_ID,
                "secret_access_key": self.AWS_SECRET_ACCESS_KEY,
                "region": self.AWS_REGION,
                "bucket": self.S3_BUCKET,
            },
            "azure": {
                "connection_string": self.AZURE_STORAGE_CONNECTION_STRING,
                "container_name": self.AZURE_CONTAINER_NAME,
            },
        }

    class Config:
        """Pydantic配置"""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        validate_assignment = True


# 创建全局配置实例
settings = GraphRAGServiceSettings()


# 导出配置
__all__ = ["GraphRAGServiceSettings", "settings"]
