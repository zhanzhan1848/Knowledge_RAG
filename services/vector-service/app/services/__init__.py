#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
向量服务业务逻辑模块

该模块包含向量服务的核心业务逻辑，包括嵌入生成和向量管理。

Author: Knowledge RAG Team
Date: 2024
"""

from .embedding_service import EmbeddingService
from .vector_manager import VectorManager, SearchResult

__all__ = ["EmbeddingService", "VectorManager", "SearchResult"]