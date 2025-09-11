#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
文档服务数据模型

该模块定义了文档服务相关的数据库模型，包括文档元数据、用户配额、访问权限等。
"""

from datetime import datetime
from typing import Optional, List
from enum import Enum

from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, Text, BigInteger,
    ForeignKey, Index, UniqueConstraint, CheckConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Session
from sqlalchemy.sql import func

Base = declarative_base()


class DocumentStatus(str, Enum):
    """文档状态枚举"""
    UPLOADING = "uploading"  # 上传中
    PROCESSING = "processing"  # 处理中
    ACTIVE = "active"  # 活跃
    ARCHIVED = "archived"  # 已归档
    DELETED = "deleted"  # 已删除
    ERROR = "error"  # 错误状态


class AccessLevel(str, Enum):
    """访问级别枚举"""
    PRIVATE = "private"  # 私有
    SHARED = "shared"  # 共享
    PUBLIC = "public"  # 公开


class PermissionType(str, Enum):
    """权限类型枚举"""
    READ = "read"  # 读取
    WRITE = "write"  # 写入
    DELETE = "delete"  # 删除
    SHARE = "share"  # 分享


class Document(Base):
    """文档模型"""
    __tablename__ = "documents"
    
    # 基础字段
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False, comment="原始文件名")
    display_name = Column(String(255), nullable=True, comment="显示名称")
    description = Column(Text, nullable=True, comment="文档描述")
    
    # 存储相关
    object_name = Column(String(500), nullable=False, unique=True, comment="MinIO对象名称")
    bucket_name = Column(String(100), nullable=False, comment="存储桶名称")
    file_size = Column(BigInteger, nullable=False, comment="文件大小（字节）")
    content_type = Column(String(100), nullable=False, comment="MIME类型")
    file_extension = Column(String(10), nullable=True, comment="文件扩展名")
    etag = Column(String(100), nullable=True, comment="文件ETag")
    
    # 用户和权限
    owner_id = Column(Integer, nullable=False, comment="所有者用户ID")
    access_level = Column(String(20), nullable=False, default=AccessLevel.PRIVATE, comment="访问级别")
    
    # 状态和时间
    status = Column(String(20), nullable=False, default=DocumentStatus.UPLOADING, comment="文档状态")
    created_at = Column(DateTime, nullable=False, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now(), comment="更新时间")
    deleted_at = Column(DateTime, nullable=True, comment="删除时间")
    
    # 访问统计
    download_count = Column(Integer, nullable=False, default=0, comment="下载次数")
    view_count = Column(Integer, nullable=False, default=0, comment="查看次数")
    last_accessed_at = Column(DateTime, nullable=True, comment="最后访问时间")
    
    # 处理相关
    processing_status = Column(String(50), nullable=True, comment="处理状态")
    processing_error = Column(Text, nullable=True, comment="处理错误信息")
    
    # 版本控制
    version = Column(Integer, nullable=False, default=1, comment="版本号")
    parent_id = Column(Integer, ForeignKey("documents.id"), nullable=True, comment="父文档ID")
    
    # 关系
    children = relationship("Document", backref="parent", remote_side=[id])
    permissions = relationship("DocumentPermission", back_populates="document", cascade="all, delete-orphan")
    access_logs = relationship("DocumentAccessLog", back_populates="document", cascade="all, delete-orphan")
    
    # 索引
    __table_args__ = (
        Index("idx_documents_owner_status", "owner_id", "status"),
        Index("idx_documents_created_at", "created_at"),
        Index("idx_documents_object_name", "object_name"),
        CheckConstraint("file_size >= 0", name="check_file_size_positive"),
        CheckConstraint("version >= 1", name="check_version_positive"),
    )
    
    def __repr__(self):
        return f"<Document(id={self.id}, filename='{self.filename}', owner_id={self.owner_id})>"
    
    def to_dict(self) -> dict:
        """转换为字典格式
        
        Returns:
            dict: 文档信息字典
        """
        return {
            "id": self.id,
            "filename": self.filename,
            "display_name": self.display_name,
            "description": self.description,
            "file_size": self.file_size,
            "content_type": self.content_type,
            "file_extension": self.file_extension,
            "owner_id": self.owner_id,
            "access_level": self.access_level,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "download_count": self.download_count,
            "view_count": self.view_count,
            "last_accessed_at": self.last_accessed_at.isoformat() if self.last_accessed_at else None,
            "version": self.version,
            "parent_id": self.parent_id
        }


class DocumentPermission(Base):
    """文档权限模型"""
    __tablename__ = "document_permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, comment="文档ID")
    user_id = Column(Integer, nullable=False, comment="用户ID")
    permission_type = Column(String(20), nullable=False, comment="权限类型")
    granted_by = Column(Integer, nullable=False, comment="授权者用户ID")
    granted_at = Column(DateTime, nullable=False, default=func.now(), comment="授权时间")
    expires_at = Column(DateTime, nullable=True, comment="过期时间")
    is_active = Column(Boolean, nullable=False, default=True, comment="是否活跃")
    
    # 关系
    document = relationship("Document", back_populates="permissions")
    
    # 索引和约束
    __table_args__ = (
        UniqueConstraint("document_id", "user_id", "permission_type", name="uq_doc_user_permission"),
        Index("idx_permissions_user_id", "user_id"),
        Index("idx_permissions_document_id", "document_id"),
    )
    
    def __repr__(self):
        return f"<DocumentPermission(document_id={self.document_id}, user_id={self.user_id}, type='{self.permission_type}')>"


class UserQuota(Base):
    """用户存储配额模型"""
    __tablename__ = "user_quotas"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, unique=True, comment="用户ID")
    total_quota = Column(BigInteger, nullable=False, comment="总配额（字节）")
    used_quota = Column(BigInteger, nullable=False, default=0, comment="已使用配额（字节）")
    file_count = Column(Integer, nullable=False, default=0, comment="文件数量")
    max_file_size = Column(BigInteger, nullable=True, comment="单文件最大大小（字节）")
    
    created_at = Column(DateTime, nullable=False, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 索引和约束
    __table_args__ = (
        Index("idx_quotas_user_id", "user_id"),
        CheckConstraint("total_quota >= 0", name="check_total_quota_positive"),
        CheckConstraint("used_quota >= 0", name="check_used_quota_positive"),
        CheckConstraint("used_quota <= total_quota", name="check_quota_limit"),
        CheckConstraint("file_count >= 0", name="check_file_count_positive"),
    )
    
    def __repr__(self):
        return f"<UserQuota(user_id={self.user_id}, used={self.used_quota}/{self.total_quota})>"
    
    @property
    def available_quota(self) -> int:
        """可用配额
        
        Returns:
            int: 可用配额（字节）
        """
        return self.total_quota - self.used_quota
    
    @property
    def usage_percentage(self) -> float:
        """使用率百分比
        
        Returns:
            float: 使用率（0-100）
        """
        if self.total_quota == 0:
            return 0.0
        return (self.used_quota / self.total_quota) * 100
    
    def can_upload(self, file_size: int) -> bool:
        """检查是否可以上传指定大小的文件
        
        Args:
            file_size: 文件大小（字节）
            
        Returns:
            bool: 是否可以上传
        """
        # 检查总配额
        if self.used_quota + file_size > self.total_quota:
            return False
        
        # 检查单文件大小限制
        if self.max_file_size and file_size > self.max_file_size:
            return False
        
        return True


class DocumentAccessLog(Base):
    """文档访问日志模型"""
    __tablename__ = "document_access_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, comment="文档ID")
    user_id = Column(Integer, nullable=True, comment="用户ID（匿名访问时为空）")
    action = Column(String(50), nullable=False, comment="操作类型（view/download/share等）")
    ip_address = Column(String(45), nullable=True, comment="IP地址")
    user_agent = Column(Text, nullable=True, comment="用户代理")
    accessed_at = Column(DateTime, nullable=False, default=func.now(), comment="访问时间")
    
    # 关系
    document = relationship("Document", back_populates="access_logs")
    
    # 索引
    __table_args__ = (
        Index("idx_access_logs_document_id", "document_id"),
        Index("idx_access_logs_user_id", "user_id"),
        Index("idx_access_logs_accessed_at", "accessed_at"),
    )
    
    def __repr__(self):
        return f"<DocumentAccessLog(document_id={self.document_id}, user_id={self.user_id}, action='{self.action}')>"


class DocumentTag(Base):
    """文档标签模型"""
    __tablename__ = "document_tags"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, comment="文档ID")
    tag_name = Column(String(50), nullable=False, comment="标签名称")
    created_by = Column(Integer, nullable=False, comment="创建者用户ID")
    created_at = Column(DateTime, nullable=False, default=func.now(), comment="创建时间")
    
    # 索引和约束
    __table_args__ = (
        UniqueConstraint("document_id", "tag_name", name="uq_document_tag"),
        Index("idx_tags_document_id", "document_id"),
        Index("idx_tags_name", "tag_name"),
    )
    
    def __repr__(self):
        return f"<DocumentTag(document_id={self.document_id}, tag='{self.tag_name}')>"


class DocumentShare(Base):
    """文档分享模型"""
    __tablename__ = "document_shares"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, comment="文档ID")
    share_token = Column(String(100), nullable=False, unique=True, comment="分享令牌")
    created_by = Column(Integer, nullable=False, comment="创建者用户ID")
    expires_at = Column(DateTime, nullable=True, comment="过期时间")
    max_downloads = Column(Integer, nullable=True, comment="最大下载次数")
    download_count = Column(Integer, nullable=False, default=0, comment="已下载次数")
    is_active = Column(Boolean, nullable=False, default=True, comment="是否活跃")
    password = Column(String(100), nullable=True, comment="访问密码（哈希）")
    
    created_at = Column(DateTime, nullable=False, default=func.now(), comment="创建时间")
    
    # 索引
    __table_args__ = (
        Index("idx_shares_token", "share_token"),
        Index("idx_shares_document_id", "document_id"),
        Index("idx_shares_created_by", "created_by"),
    )
    
    def __repr__(self):
        return f"<DocumentShare(document_id={self.document_id}, token='{self.share_token[:8]}...')>"
    
    @property
    def is_expired(self) -> bool:
        """检查分享是否已过期
        
        Returns:
            bool: 是否已过期
        """
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_download_limit_reached(self) -> bool:
        """检查下载次数是否已达上限
        
        Returns:
            bool: 是否已达上限
        """
        if not self.max_downloads:
            return False
        return self.download_count >= self.max_downloads
    
    def can_access(self) -> bool:
        """检查是否可以访问
        
        Returns:
            bool: 是否可以访问
        """
        return (
            self.is_active and 
            not self.is_expired and 
            not self.is_download_limit_reached
        )


class BackupRecord(Base):
    """备份记录模型"""
    __tablename__ = "backup_records"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, comment="文档ID")
    backup_type = Column(String(20), nullable=False, comment="备份类型：full, incremental, manual")
    status = Column(String(20), nullable=False, comment="备份状态：pending, running, completed, failed, cancelled")
    backup_path = Column(String(500), nullable=True, comment="备份文件路径")
    metadata_path = Column(String(500), nullable=True, comment="元数据备份路径")
    file_size = Column(BigInteger, nullable=True, comment="备份文件大小")
    created_at = Column(DateTime, nullable=False, default=func.now(), comment="创建时间")
    started_at = Column(DateTime, nullable=True, comment="开始时间")
    completed_at = Column(DateTime, nullable=True, comment="完成时间")
    error_message = Column(Text, nullable=True, comment="错误信息")
    
    # 索引
    __table_args__ = (
        Index("idx_backup_records_document_id", "document_id"),
        Index("idx_backup_records_status", "status"),
        Index("idx_backup_records_created_at", "created_at"),
    )
    
    def __repr__(self):
        return f"<BackupRecord(document_id={self.document_id}, type='{self.backup_type}', status='{self.status}')>"