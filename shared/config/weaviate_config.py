#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Weaviate 向量数据库配置模块

该模块提供 Weaviate 向量数据库的配置管理功能，包括：
- 连接配置
- 类（Class）定义
- 向量化器配置
- 批处理配置

Author: Knowledge RAG Team
Date: 2024
"""

import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum


class WeaviateVectorizer(Enum):
    """Weaviate 向量化器枚举"""
    TEXT2VEC_OPENAI = "text2vec-openai"
    TEXT2VEC_COHERE = "text2vec-cohere"
    TEXT2VEC_HUGGINGFACE = "text2vec-huggingface"
    TEXT2VEC_TRANSFORMERS = "text2vec-transformers"
    NONE = "none"


@dataclass
class WeaviateConfig:
    """Weaviate 配置类"""
    url: str
    api_key: Optional[str] = None
    timeout: int = 30
    startup_period: int = 5
    
    # 类配置
    class_name: str = "Document"
    vectorizer: WeaviateVectorizer = WeaviateVectorizer.TEXT2VEC_OPENAI
    
    # 批处理配置
    batch_size: int = 100
    batch_dynamic: bool = True
    batch_timeout_retries: int = 3
    
    # 向量配置
    vector_index_type: str = "hnsw"
    distance_metric: str = "cosine"
    
    @classmethod
    def from_env(cls) -> 'WeaviateConfig':
        """从环境变量创建配置"""
        return cls(
            url=os.getenv('WEAVIATE_URL', 'http://localhost:8080'),
            api_key=os.getenv('WEAVIATE_API_KEY'),
            timeout=int(os.getenv('WEAVIATE_TIMEOUT', '30')),
            startup_period=int(os.getenv('WEAVIATE_STARTUP_PERIOD', '5')),
            class_name=os.getenv('WEAVIATE_CLASS_NAME', 'Document'),
            vectorizer=WeaviateVectorizer(os.getenv('WEAVIATE_VECTORIZER', 'text2vec-openai')),
            batch_size=int(os.getenv('WEAVIATE_BATCH_SIZE', '100')),
            batch_dynamic=os.getenv('WEAVIATE_BATCH_DYNAMIC', 'true').lower() == 'true',
            batch_timeout_retries=int(os.getenv('WEAVIATE_BATCH_TIMEOUT_RETRIES', '3')),
            vector_index_type=os.getenv('WEAVIATE_VECTOR_INDEX_TYPE', 'hnsw'),
            distance_metric=os.getenv('WEAVIATE_DISTANCE_METRIC', 'cosine')
        )


class WeaviateSchemaManager:
    """Weaviate 模式管理器"""
    
    @staticmethod
    def get_document_class_definition(config: WeaviateConfig) -> Dict[str, Any]:
        """获取文档类定义"""
        return {
            "class": config.class_name,
            "description": "Knowledge RAG 系统文档类",
            "vectorizer": config.vectorizer.value,
            "moduleConfig": WeaviateSchemaManager._get_module_config(config.vectorizer),
            "vectorIndexConfig": {
                "distance": config.distance_metric,
                "ef": 64,
                "efConstruction": 128,
                "maxConnections": 64
            },
            "properties": [
                {
                    "name": "title",
                    "dataType": ["text"],
                    "description": "文档标题",
                    "tokenization": "word"
                },
                {
                    "name": "content",
                    "dataType": ["text"],
                    "description": "文档内容",
                    "tokenization": "word"
                },
                {
                    "name": "source",
                    "dataType": ["text"],
                    "description": "文档来源",
                    "tokenization": "keyword"
                },
                {
                    "name": "document_type",
                    "dataType": ["text"],
                    "description": "文档类型",
                    "tokenization": "keyword"
                },
                {
                    "name": "chunk_index",
                    "dataType": ["int"],
                    "description": "文档块索引"
                },
                {
                    "name": "metadata",
                    "dataType": ["object"],
                    "description": "文档元数据"
                },
                {
                    "name": "created_at",
                    "dataType": ["date"],
                    "description": "创建时间"
                },
                {
                    "name": "updated_at",
                    "dataType": ["date"],
                    "description": "更新时间"
                }
            ]
        }
    
    @staticmethod
    def _get_module_config(vectorizer: WeaviateVectorizer) -> Dict[str, Any]:
        """获取模块配置"""
        if vectorizer == WeaviateVectorizer.TEXT2VEC_OPENAI:
            return {
                "text2vec-openai": {
                    "model": "ada",
                    "modelVersion": "002",
                    "type": "text"
                }
            }
        elif vectorizer == WeaviateVectorizer.TEXT2VEC_COHERE:
            return {
                "text2vec-cohere": {
                    "model": "embed-multilingual-v2.0"
                }
            }
        elif vectorizer == WeaviateVectorizer.TEXT2VEC_HUGGINGFACE:
            return {
                "text2vec-huggingface": {
                    "model": "sentence-transformers/all-MiniLM-L6-v2"
                }
            }
        elif vectorizer == WeaviateVectorizer.TEXT2VEC_TRANSFORMERS:
            return {
                "text2vec-transformers": {
                    "poolingStrategy": "masked_mean",
                    "vectorizeClassName": False
                }
            }
        else:
            return {}


class WeaviateConnectionManager:
    """Weaviate 连接管理器"""
    
    def __init__(self, config: WeaviateConfig):
        """初始化连接管理器"""
        self.config = config
        self._client = None
    
    def get_client(self):
        """获取 Weaviate 客户端"""
        if self._client is None:
            try:
                import weaviate
                
                # 配置认证
                auth_config = None
                if self.config.api_key:
                    auth_config = weaviate.AuthApiKey(api_key=self.config.api_key)
                
                # 创建客户端
                self._client = weaviate.Client(
                    url=self.config.url,
                    auth_client_secret=auth_config,
                    timeout_config=(self.config.timeout, self.config.timeout),
                    startup_period=self.config.startup_period
                )
                
                # 检查连接
                if not self._client.is_ready():
                    raise ConnectionError("Weaviate 服务未就绪")
                    
            except ImportError:
                raise ImportError("请安装 weaviate-client: pip install weaviate-client")
            except Exception as e:
                raise ConnectionError(f"连接 Weaviate 失败: {e}")
        
        return self._client
    
    def close(self):
        """关闭连接"""
        if self._client:
            self._client = None
    
    def health_check(self) -> bool:
        """健康检查"""
        try:
            client = self.get_client()
            return client.is_ready()
        except Exception:
            return False


# 全局配置实例
weaviate_config = WeaviateConfig.from_env()
weaviate_connection = WeaviateConnectionManager(weaviate_config)
weaviate_schema = WeaviateSchemaManager()


# 导出的公共接口
__all__ = [
    'WeaviateConfig',
    'WeaviateVectorizer', 
    'WeaviateSchemaManager',
    'WeaviateConnectionManager',
    'weaviate_config',
    'weaviate_connection',
    'weaviate_schema'
]