#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
向量服务配置模块

该模块定义向量服务的所有配置项，包括：
- 基础服务配置
- 向量数据库配置
- 嵌入模型配置
- 缓存配置

Author: Knowledge RAG Team
Date: 2024
"""

import os
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseSettings, Field, validator


class VectorBackend(str, Enum):
    """向量数据库后端枚举"""

    CHROMADB = "chromadb"
    FAISS = "faiss"
    WEAVIATE = "weaviate"
    QDRANT = "qdrant"


class EmbeddingProvider(str, Enum):
    """嵌入模型提供商枚举"""

    OPENAI = "openai"
    HUGGINGFACE = "huggingface"
    SENTENCE_TRANSFORMERS = "sentence_transformers"
    LOCAL = "local"


class Settings(BaseSettings):
    """向量服务配置类"""

    # ===========================================
    # 基础服务配置
    # ===========================================
    SERVICE_NAME: str = "vector-service"
    SERVICE_VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False, env="DEBUG")
    HOST: str = Field(default="0.0.0.0", env="VECTOR_SERVICE_HOST")
    PORT: int = Field(default=8003, env="VECTOR_SERVICE_PORT")

    # CORS 配置
    ALLOWED_HOSTS: List[str] = Field(default=["*"], env="ALLOWED_HOSTS")

    # ===========================================
    # 数据库配置
    # ===========================================
    DATABASE_URL: str = Field(
        default="postgresql://vector_user:vector_pass@localhost:5432/vector_db",
        env="DATABASE_URL",
    )

    # Redis 配置
    REDIS_URL: str = Field(default="redis://localhost:6379/2", env="REDIS_URL")

    # ===========================================
    # 向量数据库配置
    # ===========================================
    VECTOR_BACKEND: VectorBackend = Field(
        default=VectorBackend.CHROMADB, env="VECTOR_BACKEND"
    )

    # ChromaDB 配置
    CHROMA_HOST: str = Field(default="localhost", env="CHROMA_HOST")
    CHROMA_PORT: int = Field(default=8000, env="CHROMA_PORT")
    CHROMA_PERSIST_DIRECTORY: str = Field(
        default="./data/chroma", env="CHROMA_PERSIST_DIRECTORY"
    )

    # FAISS 配置
    FAISS_INDEX_PATH: str = Field(default="./data/faiss", env="FAISS_INDEX_PATH")
    FAISS_DIMENSION: int = Field(default=768, env="FAISS_DIMENSION")

    # Weaviate 配置
    WEAVIATE_URL: str = Field(default="http://localhost:8080", env="WEAVIATE_URL")
    WEAVIATE_API_KEY: Optional[str] = Field(default=None, env="WEAVIATE_API_KEY")
    WEAVIATE_CLASS_NAME: str = Field(default="Document", env="WEAVIATE_CLASS_NAME")
    WEAVIATE_VECTORIZER: str = Field(
        default="text2vec-openai", env="WEAVIATE_VECTORIZER"
    )
    WEAVIATE_BATCH_SIZE: int = Field(default=100, env="WEAVIATE_BATCH_SIZE")

    # ===========================================
    # 嵌入模型配置
    # ===========================================
    EMBEDDING_PROVIDER: EmbeddingProvider = Field(
        default=EmbeddingProvider.SENTENCE_TRANSFORMERS, env="EMBEDDING_PROVIDER"
    )
    EMBEDDING_MODEL: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2", env="EMBEDDING_MODEL"
    )
    EMBEDDING_DIMENSION: int = Field(default=384, env="EMBEDDING_DIMENSION")
    EMBEDDING_BATCH_SIZE: int = Field(default=32, env="EMBEDDING_BATCH_SIZE")

    # OpenAI 嵌入配置
    OPENAI_API_KEY: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    OPENAI_EMBEDDING_MODEL: str = Field(
        default="text-embedding-ada-002", env="OPENAI_EMBEDDING_MODEL"
    )

    # HuggingFace 配置
    HUGGINGFACE_API_KEY: Optional[str] = Field(default=None, env="HUGGINGFACE_API_KEY")
    HUGGINGFACE_MODEL_PATH: str = Field(
        default="./models/huggingface", env="HUGGINGFACE_MODEL_PATH"
    )

    # ===========================================
    # 缓存配置
    # ===========================================
    CACHE_TTL: int = Field(default=3600, env="CACHE_TTL")  # 1小时
    CACHE_MAX_SIZE: int = Field(default=1000, env="CACHE_MAX_SIZE")

    # ===========================================
    # 搜索配置
    # ===========================================
    DEFAULT_TOP_K: int = Field(default=10, env="DEFAULT_TOP_K")
    MAX_TOP_K: int = Field(default=100, env="MAX_TOP_K")
    SIMILARITY_THRESHOLD: float = Field(default=0.7, env="SIMILARITY_THRESHOLD")

    # ===========================================
    # 性能配置
    # ===========================================
    MAX_CONCURRENT_REQUESTS: int = Field(default=10, env="MAX_CONCURRENT_REQUESTS")
    REQUEST_TIMEOUT: int = Field(default=30, env="REQUEST_TIMEOUT")
    BATCH_PROCESSING_SIZE: int = Field(default=100, env="BATCH_PROCESSING_SIZE")

    # ===========================================
    # 监控配置
    # ===========================================
    ENABLE_METRICS: bool = Field(default=True, env="ENABLE_METRICS")
    METRICS_PORT: int = Field(default=9003, env="METRICS_PORT")

    # ===========================================
    # 日志配置
    # ===========================================
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s", env="LOG_FORMAT"
    )

    # ===========================================
    # 安全配置
    # ===========================================
    JWT_SECRET_KEY: str = Field(default="your-secret-key-here", env="JWT_SECRET_KEY")
    JWT_ALGORITHM: str = Field(default="HS256", env="JWT_ALGORITHM")

    # API 密钥配置
    API_KEY_HEADER: str = Field(default="X-API-Key", env="API_KEY_HEADER")
    VALID_API_KEYS: List[str] = Field(default=["dev-api-key"], env="VALID_API_KEYS")

    # ===========================================
    # 文件存储配置
    # ===========================================
    UPLOAD_DIR: str = Field(default="./data/uploads", env="UPLOAD_DIR")
    MAX_FILE_SIZE: int = Field(default=100 * 1024 * 1024, env="MAX_FILE_SIZE")  # 100MB
    ALLOWED_FILE_TYPES: List[str] = Field(
        default=[".txt", ".pdf", ".docx", ".md"], env="ALLOWED_FILE_TYPES"
    )

    @validator("ALLOWED_HOSTS", pre=True)
    def parse_allowed_hosts(cls, v):
        """解析允许的主机列表"""
        if isinstance(v, str):
            return [host.strip() for host in v.split(",")]
        return v

    @validator("VALID_API_KEYS", pre=True)
    def parse_api_keys(cls, v):
        """解析 API 密钥列表"""
        if isinstance(v, str):
            return [key.strip() for key in v.split(",")]
        return v

    @validator("ALLOWED_FILE_TYPES", pre=True)
    def parse_file_types(cls, v):
        """解析允许的文件类型列表"""
        if isinstance(v, str):
            return [ext.strip() for ext in v.split(",")]
        return v

    def get_vector_config(self) -> Dict[str, Any]:
        """获取向量数据库配置"""
        if self.VECTOR_BACKEND == VectorBackend.CHROMADB:
            return {
                "host": self.CHROMA_HOST,
                "port": self.CHROMA_PORT,
                "persist_directory": self.CHROMA_PERSIST_DIRECTORY,
            }
        elif self.VECTOR_BACKEND == VectorBackend.FAISS:
            return {
                "index_path": self.FAISS_INDEX_PATH,
                "dimension": self.FAISS_DIMENSION,
            }
        elif self.VECTOR_BACKEND == VectorBackend.WEAVIATE:
            return {
                "url": self.WEAVIATE_URL,
                "api_key": self.WEAVIATE_API_KEY,
                "class_name": self.WEAVIATE_CLASS_NAME,
                "vectorizer": self.WEAVIATE_VECTORIZER,
                "batch_size": self.WEAVIATE_BATCH_SIZE,
            }
        else:
            return {}

    def get_embedding_config(self) -> Dict[str, Any]:
        """获取嵌入模型配置"""
        base_config = {
            "provider": self.EMBEDDING_PROVIDER,
            "model": self.EMBEDDING_MODEL,
            "dimension": self.EMBEDDING_DIMENSION,
            "batch_size": self.EMBEDDING_BATCH_SIZE,
        }

        if self.EMBEDDING_PROVIDER == EmbeddingProvider.OPENAI:
            base_config.update(
                {"api_key": self.OPENAI_API_KEY, "model": self.OPENAI_EMBEDDING_MODEL}
            )
        elif self.EMBEDDING_PROVIDER == EmbeddingProvider.HUGGINGFACE:
            base_config.update(
                {
                    "api_key": self.HUGGINGFACE_API_KEY,
                    "model_path": self.HUGGINGFACE_MODEL_PATH,
                }
            )

        return base_config

    class Config:
        """Pydantic 配置"""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# 创建全局配置实例
settings = Settings()


# 导出的公共接口
__all__ = ["Settings", "VectorBackend", "EmbeddingProvider", "settings"]
