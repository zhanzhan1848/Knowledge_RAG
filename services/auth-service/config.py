#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
认证服务配置

提供认证服务的配置管理功能。

作者: 系统
创建时间: 2025-01-09
"""

import os
from typing import Optional
from pydantic import BaseSettings, validator


class AuthConfig(BaseSettings):
    """
    认证服务配置类
    """
    # 数据库配置
    database_url: str = "postgresql://postgres:password@localhost:5432/knowledge_rag_auth"
    
    # JWT配置
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7
    
    # 管理员配置
    admin_username: str = "admin"
    admin_email: str = "admin@example.com"
    admin_password: str = "Admin123456"
    
    # 邮件配置
    smtp_server: Optional[str] = None
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_use_tls: bool = True
    
    # SendGrid配置（可选）
    sendgrid_api_key: Optional[str] = None
    
    # Redis配置（用于会话和限流）
    redis_url: str = "redis://localhost:6379/0"
    
    # 安全配置
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 30
    
    # 应用配置
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8001
    
    @validator('jwt_secret_key')
    def validate_jwt_secret(cls, v):
        if v == "your-secret-key-change-in-production":
            import warnings
            warnings.warn("请在生产环境中更改JWT密钥")
        return v
    
    class Config:
        env_file = ".env"
        env_prefix = "AUTH_"


# 全局配置实例
config = AuthConfig()


def get_config() -> AuthConfig:
    """
    获取配置实例
    
    Returns:
        AuthConfig: 配置对象
    """
    return config