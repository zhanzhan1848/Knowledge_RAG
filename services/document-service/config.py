#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
文档服务配置模块

该模块包含文档服务的所有配置项，包括MinIO存储配置、数据库配置等。
"""

import os
from typing import Optional
from pydantic import BaseSettings, Field


class DocumentServiceConfig(BaseSettings):
    """文档服务配置类"""
    
    # 服务基础配置
    service_name: str = "document-service"
    host: str = Field(default="0.0.0.0", env="DOC_SERVICE_HOST")
    port: int = Field(default=8002, env="DOC_SERVICE_PORT")
    debug: bool = Field(default=False, env="DEBUG")
    
    # MinIO 配置
    minio_endpoint: str = Field(default="localhost:9000", env="MINIO_ENDPOINT")
    minio_access_key: str = Field(default="minioadmin", env="MINIO_ACCESS_KEY")
    minio_secret_key: str = Field(default="minioadmin", env="MINIO_SECRET_KEY")
    minio_secure: bool = Field(default=False, env="MINIO_SECURE")
    minio_bucket_name: str = Field(default="documents", env="MINIO_BUCKET_NAME")
    
    # 数据库配置
    database_url: str = Field(
        default="postgresql://postgres:password@localhost:5432/knowledge_rag",
        env="DATABASE_URL"
    )
    
    # 文件上传配置
    max_file_size: int = Field(default=100 * 1024 * 1024, env="MAX_FILE_SIZE")  # 100MB
    allowed_file_types: list = Field(
        default=[".pdf", ".doc", ".docx", ".txt", ".md", ".html", ".rtf"],
        env="ALLOWED_FILE_TYPES"
    )
    
    # 存储配额配置
    default_user_quota: int = Field(default=1024 * 1024 * 1024, env="DEFAULT_USER_QUOTA")  # 1GB
    max_user_quota: int = Field(default=10 * 1024 * 1024 * 1024, env="MAX_USER_QUOTA")  # 10GB
    
    # 认证服务配置
    auth_service_url: str = Field(default="http://localhost:8001", env="AUTH_SERVICE_URL")
    
    # 日志配置
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: str = Field(default="logs/document-service.log", env="LOG_FILE")
    
    # Redis配置（用于缓存）
    redis_url: str = Field(default="redis://localhost:6379/2", env="REDIS_URL")
    
    # 备份配置
    backup_enabled: bool = Field(default=False, env="BACKUP_ENABLED")
    backup_s3_bucket: Optional[str] = Field(default=None, env="BACKUP_S3_BUCKET")
    backup_s3_access_key: Optional[str] = Field(default=None, env="BACKUP_S3_ACCESS_KEY")
    backup_s3_secret_key: Optional[str] = Field(default=None, env="BACKUP_S3_SECRET_KEY")
    backup_s3_region: str = Field(default="us-east-1", env="BACKUP_S3_REGION")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# 全局配置实例
config = DocumentServiceConfig()


def get_config() -> DocumentServiceConfig:
    """获取配置实例
    
    Returns:
        DocumentServiceConfig: 配置实例
    """
    return config