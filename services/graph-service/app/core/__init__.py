#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GraphRAG服务核心模块

该模块包含GraphRAG服务的核心配置和依赖管理功能。

Author: Knowledge RAG Team
Date: 2024
"""

from .config import Settings
from .dependencies import (
    get_config_settings,
    get_graphrag_manager,
    get_neo4j_manager,
)

__all__ = [
    "Settings",
    "get_config_settings",
    "get_graphrag_manager",
    "get_neo4j_manager",
]