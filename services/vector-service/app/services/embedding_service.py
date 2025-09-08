#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
嵌入服务模块

该模块提供统一的文本嵌入服务，支持多种嵌入模型：
- OpenAI Embeddings
- HuggingFace Transformers
- Sentence Transformers
- 本地模型

Author: Knowledge RAG Team
Date: 2024
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Union
from abc import ABC, abstractmethod
from datetime import datetime
import numpy as np
from dataclasses import dataclass
import hashlib
import json

from app.core.config import settings, EmbeddingProvider
from shared.utils.cache import CacheManager
from shared.utils.metrics import MetricsCollector

logger = logging.getLogger(__name__)


@dataclass
class EmbeddingResult:
    """嵌入结果数据类"""
    vector: List[float]
    model: str
    dimensions: int
    tokens_used: Optional[int] = None
    processing_time: Optional[float] = None


class EmbeddingProvider(ABC):
    """嵌入提供者抽象基类"""
    
    @abstractmethod
    async def embed_text(self, text: str) -> List[float]:
        """嵌入单个文本"""
        pass
    
    @abstractmethod
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """批量嵌入文本"""
        pass
    
    @abstractmethod
    async def get_dimensions(self) -> int:
        """获取向量维度"""
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


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI 嵌入提供者"""
    
    def __init__(self):
        """初始化 OpenAI 嵌入提供者"""
        self.client = None
        self.model = settings.OPENAI_EMBEDDING_MODEL
        self.api_key = settings.OPENAI_API_KEY
        self.base_url = settings.OPENAI_BASE_URL
        self.dimensions = None
        self.requests_count = 0
        self.tokens_used = 0
    
    async def initialize(self) -> None:
        """初始化 OpenAI 客户端"""
        try:
            import openai
            
            self.client = openai.AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
            
            # 获取模型维度
            self.dimensions = await self._get_model_dimensions()
            
            logger.info(f"OpenAI 嵌入提供者初始化成功，模型: {self.model}，维度: {self.dimensions}")
            
        except Exception as e:
            logger.error(f"OpenAI 嵌入提供者初始化失败: {e}")
            raise
    
    async def embed_text(self, text: str) -> List[float]:
        """嵌入单个文本"""
        try:
            start_time = datetime.now()
            
            response = await self.client.embeddings.create(
                model=self.model,
                input=text
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # 更新统计信息
            self.requests_count += 1
            self.tokens_used += response.usage.total_tokens
            
            vector = response.data[0].embedding
            
            logger.debug(f"OpenAI 嵌入完成，处理时间: {processing_time:.3f}s，tokens: {response.usage.total_tokens}")
            
            return vector
            
        except Exception as e:
            logger.error(f"OpenAI 文本嵌入失败: {e}")
            raise
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """批量嵌入文本"""
        try:
            start_time = datetime.now()
            
            response = await self.client.embeddings.create(
                model=self.model,
                input=texts
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # 更新统计信息
            self.requests_count += 1
            self.tokens_used += response.usage.total_tokens
            
            vectors = [item.embedding for item in response.data]
            
            logger.debug(f"OpenAI 批量嵌入完成，处理时间: {processing_time:.3f}s，texts: {len(texts)}，tokens: {response.usage.total_tokens}")
            
            return vectors
            
        except Exception as e:
            logger.error(f"OpenAI 批量文本嵌入失败: {e}")
            raise
    
    async def get_dimensions(self) -> int:
        """获取向量维度"""
        return self.dimensions or 1536  # text-embedding-ada-002 默认维度
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            if not self.client:
                return False
            
            # 尝试嵌入一个简单文本
            await self.embed_text("health check")
            return True
            
        except Exception:
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "provider": "openai",
            "model": self.model,
            "dimensions": await self.get_dimensions(),
            "requests_count": self.requests_count,
            "tokens_used": self.tokens_used,
            "status": "healthy" if await self.health_check() else "unhealthy"
        }
    
    async def cleanup(self) -> None:
        """清理资源"""
        try:
            if self.client:
                await self.client.close()
            logger.info("OpenAI 嵌入提供者资源清理完成")
        except Exception as e:
            logger.error(f"OpenAI 嵌入提供者资源清理失败: {e}")
    
    async def _get_model_dimensions(self) -> int:
        """获取模型维度"""
        # 模型维度映射
        model_dimensions = {
            "text-embedding-ada-002": 1536,
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072
        }
        
        return model_dimensions.get(self.model, 1536)


class HuggingFaceEmbeddingProvider(EmbeddingProvider):
    """HuggingFace 嵌入提供者"""
    
    def __init__(self):
        """初始化 HuggingFace 嵌入提供者"""
        self.model = None
        self.tokenizer = None
        self.model_name = settings.HUGGINGFACE_MODEL_NAME
        self.device = settings.EMBEDDING_DEVICE
        self.dimensions = None
        self.requests_count = 0
    
    async def initialize(self) -> None:
        """初始化 HuggingFace 模型"""
        try:
            from transformers import AutoTokenizer, AutoModel
            import torch
            
            # 加载模型和分词器
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModel.from_pretrained(self.model_name)
            
            # 移动到指定设备
            if self.device and torch.cuda.is_available():
                self.model = self.model.to(self.device)
            
            # 获取模型维度
            self.dimensions = self.model.config.hidden_size
            
            logger.info(f"HuggingFace 嵌入提供者初始化成功，模型: {self.model_name}，维度: {self.dimensions}")
            
        except Exception as e:
            logger.error(f"HuggingFace 嵌入提供者初始化失败: {e}")
            raise
    
    async def embed_text(self, text: str) -> List[float]:
        """嵌入单个文本"""
        try:
            import torch
            
            start_time = datetime.now()
            
            # 分词
            inputs = self.tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512)
            
            # 移动到设备
            if self.device and torch.cuda.is_available():
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # 获取嵌入
            with torch.no_grad():
                outputs = self.model(**inputs)
                # 使用 [CLS] token 的嵌入或平均池化
                embeddings = outputs.last_hidden_state.mean(dim=1).squeeze()
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # 更新统计信息
            self.requests_count += 1
            
            vector = embeddings.cpu().numpy().tolist()
            
            logger.debug(f"HuggingFace 嵌入完成，处理时间: {processing_time:.3f}s")
            
            return vector
            
        except Exception as e:
            logger.error(f"HuggingFace 文本嵌入失败: {e}")
            raise
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """批量嵌入文本"""
        try:
            import torch
            
            start_time = datetime.now()
            
            # 批量分词
            inputs = self.tokenizer(texts, return_tensors="pt", truncation=True, padding=True, max_length=512)
            
            # 移动到设备
            if self.device and torch.cuda.is_available():
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # 获取嵌入
            with torch.no_grad():
                outputs = self.model(**inputs)
                # 平均池化
                embeddings = outputs.last_hidden_state.mean(dim=1)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # 更新统计信息
            self.requests_count += 1
            
            vectors = embeddings.cpu().numpy().tolist()
            
            logger.debug(f"HuggingFace 批量嵌入完成，处理时间: {processing_time:.3f}s，texts: {len(texts)}")
            
            return vectors
            
        except Exception as e:
            logger.error(f"HuggingFace 批量文本嵌入失败: {e}")
            raise
    
    async def get_dimensions(self) -> int:
        """获取向量维度"""
        return self.dimensions or 768  # BERT 默认维度
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            if not self.model or not self.tokenizer:
                return False
            
            # 尝试嵌入一个简单文本
            await self.embed_text("health check")
            return True
            
        except Exception:
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "provider": "huggingface",
            "model": self.model_name,
            "dimensions": await self.get_dimensions(),
            "device": self.device,
            "requests_count": self.requests_count,
            "status": "healthy" if await self.health_check() else "unhealthy"
        }
    
    async def cleanup(self) -> None:
        """清理资源"""
        try:
            # 清理 GPU 内存
            if self.model and hasattr(self.model, 'cpu'):
                self.model.cpu()
            
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            logger.info("HuggingFace 嵌入提供者资源清理完成")
        except Exception as e:
            logger.error(f"HuggingFace 嵌入提供者资源清理失败: {e}")


class SentenceTransformersEmbeddingProvider(EmbeddingProvider):
    """Sentence Transformers 嵌入提供者"""
    
    def __init__(self):
        """初始化 Sentence Transformers 嵌入提供者"""
        self.model = None
        self.model_name = settings.SENTENCE_TRANSFORMERS_MODEL
        self.device = settings.EMBEDDING_DEVICE
        self.dimensions = None
        self.requests_count = 0
    
    async def initialize(self) -> None:
        """初始化 Sentence Transformers 模型"""
        try:
            from sentence_transformers import SentenceTransformer
            
            # 加载模型
            self.model = SentenceTransformer(self.model_name, device=self.device)
            
            # 获取模型维度
            self.dimensions = self.model.get_sentence_embedding_dimension()
            
            logger.info(f"Sentence Transformers 嵌入提供者初始化成功，模型: {self.model_name}，维度: {self.dimensions}")
            
        except Exception as e:
            logger.error(f"Sentence Transformers 嵌入提供者初始化失败: {e}")
            raise
    
    async def embed_text(self, text: str) -> List[float]:
        """嵌入单个文本"""
        try:
            start_time = datetime.now()
            
            # 获取嵌入
            embedding = self.model.encode(text, convert_to_numpy=True)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # 更新统计信息
            self.requests_count += 1
            
            vector = embedding.tolist()
            
            logger.debug(f"Sentence Transformers 嵌入完成，处理时间: {processing_time:.3f}s")
            
            return vector
            
        except Exception as e:
            logger.error(f"Sentence Transformers 文本嵌入失败: {e}")
            raise
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """批量嵌入文本"""
        try:
            start_time = datetime.now()
            
            # 批量获取嵌入
            embeddings = self.model.encode(texts, convert_to_numpy=True, batch_size=settings.EMBEDDING_BATCH_SIZE)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # 更新统计信息
            self.requests_count += 1
            
            vectors = embeddings.tolist()
            
            logger.debug(f"Sentence Transformers 批量嵌入完成，处理时间: {processing_time:.3f}s，texts: {len(texts)}")
            
            return vectors
            
        except Exception as e:
            logger.error(f"Sentence Transformers 批量文本嵌入失败: {e}")
            raise
    
    async def get_dimensions(self) -> int:
        """获取向量维度"""
        return self.dimensions or 384  # all-MiniLM-L6-v2 默认维度
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            if not self.model:
                return False
            
            # 尝试嵌入一个简单文本
            await self.embed_text("health check")
            return True
            
        except Exception:
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "provider": "sentence_transformers",
            "model": self.model_name,
            "dimensions": await self.get_dimensions(),
            "device": self.device,
            "requests_count": self.requests_count,
            "status": "healthy" if await self.health_check() else "unhealthy"
        }
    
    async def cleanup(self) -> None:
        """清理资源"""
        try:
            # 清理 GPU 内存
            if self.device and "cuda" in self.device:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            
            logger.info("Sentence Transformers 嵌入提供者资源清理完成")
        except Exception as e:
            logger.error(f"Sentence Transformers 嵌入提供者资源清理失败: {e}")


class EmbeddingService:
    """嵌入服务"""
    
    def __init__(self):
        """初始化嵌入服务"""
        self.provider: Optional[EmbeddingProvider] = None
        self.cache_manager = CacheManager()
        self.metrics_collector = MetricsCollector()
    
    async def initialize(self) -> None:
        """初始化嵌入服务"""
        try:
            # 根据配置创建嵌入提供者
            if settings.EMBEDDING_PROVIDER == "openai":
                self.provider = OpenAIEmbeddingProvider()
            elif settings.EMBEDDING_PROVIDER == "huggingface":
                self.provider = HuggingFaceEmbeddingProvider()
            elif settings.EMBEDDING_PROVIDER == "sentence_transformers":
                self.provider = SentenceTransformersEmbeddingProvider()
            else:
                raise ValueError(f"不支持的嵌入提供者: {settings.EMBEDDING_PROVIDER}")
            
            # 初始化提供者
            await self.provider.initialize()
            
            logger.info(f"嵌入服务初始化成功，使用提供者: {settings.EMBEDDING_PROVIDER}")
            
        except Exception as e:
            logger.error(f"嵌入服务初始化失败: {e}")
            raise
    
    async def embed_text(self, text: str, use_cache: bool = True) -> List[float]:
        """嵌入单个文本"""
        try:
            # 检查缓存
            if use_cache:
                cache_key = self._get_cache_key(text)
                cached_vector = await self.cache_manager.get(cache_key)
                if cached_vector:
                    self.metrics_collector.increment("embedding_cache_hits")
                    return cached_vector
            
            # 生成嵌入
            start_time = datetime.now()
            vector = await self.provider.embed_text(text)
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # 缓存结果
            if use_cache:
                await self.cache_manager.set(cache_key, vector, ttl=settings.EMBEDDING_CACHE_TTL)
            
            # 记录指标
            self.metrics_collector.increment("embeddings_generated")
            self.metrics_collector.record("embedding_processing_time", processing_time)
            
            return vector
            
        except Exception as e:
            logger.error(f"文本嵌入失败: {e}")
            self.metrics_collector.increment("embedding_errors")
            raise
    
    async def embed_texts(self, texts: List[str], use_cache: bool = True) -> List[List[float]]:
        """批量嵌入文本"""
        try:
            if not texts:
                return []
            
            vectors = []
            uncached_texts = []
            uncached_indices = []
            
            # 检查缓存
            if use_cache:
                for i, text in enumerate(texts):
                    cache_key = self._get_cache_key(text)
                    cached_vector = await self.cache_manager.get(cache_key)
                    if cached_vector:
                        vectors.append(cached_vector)
                        self.metrics_collector.increment("embedding_cache_hits")
                    else:
                        vectors.append(None)
                        uncached_texts.append(text)
                        uncached_indices.append(i)
            else:
                uncached_texts = texts
                uncached_indices = list(range(len(texts)))
                vectors = [None] * len(texts)
            
            # 生成未缓存的嵌入
            if uncached_texts:
                start_time = datetime.now()
                uncached_vectors = await self.provider.embed_texts(uncached_texts)
                processing_time = (datetime.now() - start_time).total_seconds()
                
                # 更新结果和缓存
                for i, (idx, vector) in enumerate(zip(uncached_indices, uncached_vectors)):
                    vectors[idx] = vector
                    
                    # 缓存结果
                    if use_cache:
                        cache_key = self._get_cache_key(uncached_texts[i])
                        await self.cache_manager.set(cache_key, vector, ttl=settings.EMBEDDING_CACHE_TTL)
                
                # 记录指标
                self.metrics_collector.increment("embeddings_generated", len(uncached_texts))
                self.metrics_collector.record("batch_embedding_processing_time", processing_time)
            
            return vectors
            
        except Exception as e:
            logger.error(f"批量文本嵌入失败: {e}")
            self.metrics_collector.increment("embedding_errors")
            raise
    
    async def get_dimensions(self) -> int:
        """获取向量维度"""
        if not self.provider:
            raise RuntimeError("嵌入服务未初始化")
        
        return await self.provider.get_dimensions()
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            if not self.provider:
                return False
            
            return await self.provider.health_check()
            
        except Exception:
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        try:
            provider_stats = await self.provider.get_stats() if self.provider else {}
            metrics_stats = self.metrics_collector.get_metrics()
            
            return {
                "provider": provider_stats,
                "metrics": metrics_stats,
                "cache_stats": await self.cache_manager.get_stats(),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取嵌入服务统计信息失败: {e}")
            return {"error": str(e)}
    
    async def cleanup(self) -> None:
        """清理资源"""
        try:
            if self.provider:
                await self.provider.cleanup()
            
            logger.info("嵌入服务资源清理完成")
            
        except Exception as e:
            logger.error(f"嵌入服务资源清理失败: {e}")
    
    def _get_cache_key(self, text: str) -> str:
        """生成缓存键"""
        # 使用文本内容和提供者信息生成唯一键
        content = f"{settings.EMBEDDING_PROVIDER}:{text}"
        return f"embedding:{hashlib.md5(content.encode()).hexdigest()}"


# 导出的公共接口
__all__ = [
    'EmbeddingService',
    'EmbeddingResult',
    'EmbeddingProvider',
    'OpenAIEmbeddingProvider',
    'HuggingFaceEmbeddingProvider',
    'SentenceTransformersEmbeddingProvider'
]