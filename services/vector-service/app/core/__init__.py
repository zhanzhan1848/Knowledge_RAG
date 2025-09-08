#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
向量服务核心模块

该模块包含向量服务的核心配置和依赖管理功能。

Author: Knowledge RAG Team
Date: 2024
"""

from .config import Settings
from .dependencies import get_embedding_service, get_vector_manager

__all__ = [
    "Settings",
    "get_embedding_service",
    "get_vector_manager",
]
