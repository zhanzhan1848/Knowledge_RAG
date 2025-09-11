#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
API网关配置模块

该模块包含API网关的配置信息，包括服务路由、超时设置、安全策略等。
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class ServiceConfig(BaseModel):
    """微服务配置模型"""
    name: str
    base_url: str
    routes: List[str]
    health_check_path: str = "/health"
    timeout: float = 30.0
    is_active: bool = True
    weight: int = 1  # 负载均衡权重


class ApiGatewayConfig(BaseModel):
    """API网关配置"""
    # 服务配置
    services: Dict[str, ServiceConfig] = Field(default_factory=dict)
    
    # 安全配置
    cors_origins: List[str] = ["*"]
    cors_methods: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]
    cors_headers: List[str] = ["*"]
    
    # 速率限制配置
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 100  # 请求数量
    rate_limit_window: int = 60  # 时间窗口（秒）
    
    # 日志配置
    log_level: str = "INFO"
    log_file: str = "logs/api_gateway.log"
    
    # 超时配置
    default_timeout: float = 30.0  # 默认超时时间（秒）
    
    # 重试配置
    retry_enabled: bool = True
    max_retries: int = 3
    retry_backoff: float = 0.5  # 重试间隔（秒）


# 默认配置
default_config = ApiGatewayConfig(
    services={
        "auth": ServiceConfig(
            name="auth-service",
            base_url="http://auth-service:8001",
            routes=["/auth", "/users"],
        ),
        "document": ServiceConfig(
            name="document-service",
            base_url="http://document-service:8002",
            routes=[
                "/documents",
                "/files", 
                "/documents/upload",
                "/documents/download",
                "/documents/preview",
                "/documents/batch-delete",
                "/documents/batch-restore",
                "/documents/trash",
                "/documents/restore",
                "/documents/permissions",
                "/documents/share",
                "/documents/stats",
                "/quota",
                "/backup"
            ],
        ),
        "vector": ServiceConfig(
            name="vector-service",
            base_url="http://vector-service:8003",
            routes=["/vectors", "/embeddings"],
        ),
        "graph": ServiceConfig(
            name="graph-service",
            base_url="http://graph-service:8004",
            routes=["/graph", "/entities", "/relationships"],
        ),
        "qa": ServiceConfig(
            name="qa-service",
            base_url="http://qa-service:8005",
            routes=["/qa", "/questions", "/answers"],
        ),
        "llm": ServiceConfig(
            name="llm-service",
            base_url="http://llm-service:8006",
            routes=["/llm", "/completions", "/chat"],
        ),
    },
    cors_origins=["*"],  # 在生产环境中应该限制来源
    rate_limit_enabled=True,
    rate_limit_requests=100,
    rate_limit_window=60,
)


def get_config() -> ApiGatewayConfig:
    """获取API网关配置
    
    根据环境变量和配置文件获取API网关配置
    
    Returns:
        ApiGatewayConfig: API网关配置对象
    """
    # TODO: 从环境变量或配置文件加载配置
    return default_config