#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文档备份和恢复服务模块

提供文档的自动备份、手动备份、恢复等功能，支持多种备份策略和存储后端。

Author: Assistant
Date: 2024
"""

import os
import json
import shutil
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.orm import Session
from minio import Minio
from minio.error import S3Error

from .models import Document, DocumentStatus, BackupRecord
from .database import get_db
from .config import settings


class BackupStatus(str, Enum):
    """备份状态枚举"""
    PENDING = "pending"      # 待备份
    RUNNING = "running"      # 备份中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"        # 失败
    CANCELLED = "cancelled"  # 已取消


class BackupType(str, Enum):
    """备份类型枚举"""
    FULL = "full"            # 全量备份
    INCREMENTAL = "incremental"  # 增量备份
    MANUAL = "manual"        # 手动备份


@dataclass
class BackupConfig:
    """备份配置"""
    enabled: bool = True
    backup_interval: int = 24  # 备份间隔（小时）
    retention_days: int = 30   # 保留天数
    max_backups: int = 100     # 最大备份数量
    backup_path: str = "/tmp/document_backups"
    compress: bool = True      # 是否压缩
    encrypt: bool = False      # 是否加密
    backup_metadata: bool = True  # 是否备份元数据


class DocumentBackupService:
    """文档备份服务类"""
    
    def __init__(self, db: Session, minio_client: Minio, config: BackupConfig = None):
        """
        初始化备份服务
        
        Args:
            db: 数据库会话
            minio_client: MinIO客户端
            config: 备份配置
        """
        self.db = db
        self.minio_client = minio_client
        self.config = config or BackupConfig()
        self.logger = logging.getLogger(__name__)
        
        # 确保备份目录存在
        Path(self.config.backup_path).mkdir(parents=True, exist_ok=True)
    
    async def create_backup(self, document_id: int, backup_type: BackupType = BackupType.MANUAL) -> Optional[BackupRecord]:
        """
        创建文档备份
        
        Args:
            document_id: 文档ID
            backup_type: 备份类型
            
        Returns:
            BackupRecord: 备份记录
        """
        try:
            # 获取文档信息
            document = self.db.query(Document).filter(Document.id == document_id).first()
            if not document:
                self.logger.error(f"文档不存在: {document_id}")
                return None
            
            # 创建备份记录
            backup_record = BackupRecord(
                document_id=document_id,
                backup_type=backup_type,
                status=BackupStatus.PENDING,
                created_at=datetime.utcnow()
            )
            self.db.add(backup_record)
            self.db.commit()
            
            # 执行备份
            backup_record.status = BackupStatus.RUNNING
            backup_record.started_at = datetime.utcnow()
            self.db.commit()
            
            # 备份文件内容
            backup_path = await self._backup_document_content(document, backup_record.id)
            if not backup_path:
                backup_record.status = BackupStatus.FAILED
                backup_record.error_message = "备份文件内容失败"
                self.db.commit()
                return backup_record
            
            # 备份元数据
            if self.config.backup_metadata:
                metadata_path = await self._backup_document_metadata(document, backup_record.id)
                backup_record.metadata_path = metadata_path
            
            # 更新备份记录
            backup_record.backup_path = backup_path
            backup_record.status = BackupStatus.COMPLETED
            backup_record.completed_at = datetime.utcnow()
            backup_record.file_size = os.path.getsize(backup_path) if os.path.exists(backup_path) else 0
            
            self.db.commit()
            
            self.logger.info(f"文档备份完成: {document_id} -> {backup_path}")
            return backup_record
            
        except Exception as e:
            self.logger.error(f"创建备份失败: {str(e)}")
            if 'backup_record' in locals():
                backup_record.status = BackupStatus.FAILED
                backup_record.error_message = str(e)
                self.db.commit()
            return None
    
    async def _backup_document_content(self, document: Document, backup_id: int) -> Optional[str]:
        """
        备份文档内容
        
        Args:
            document: 文档对象
            backup_id: 备份ID
            
        Returns:
            str: 备份文件路径
        """
        try:
            # 生成备份文件路径
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"doc_{document.id}_backup_{backup_id}_{timestamp}.{document.file_extension}"
            backup_path = os.path.join(self.config.backup_path, backup_filename)
            
            # 从MinIO下载文件
            self.minio_client.fget_object(
                bucket_name=settings.MINIO_BUCKET_NAME,
                object_name=document.storage_path,
                file_path=backup_path
            )
            
            # 如果启用压缩
            if self.config.compress:
                compressed_path = f"{backup_path}.gz"
                await self._compress_file(backup_path, compressed_path)
                os.remove(backup_path)
                backup_path = compressed_path
            
            return backup_path
            
        except Exception as e:
            self.logger.error(f"备份文档内容失败: {str(e)}")
            return None
    
    async def _backup_document_metadata(self, document: Document, backup_id: int) -> Optional[str]:
        """
        备份文档元数据
        
        Args:
            document: 文档对象
            backup_id: 备份ID
            
        Returns:
            str: 元数据备份文件路径
        """
        try:
            # 生成元数据备份文件路径
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            metadata_filename = f"doc_{document.id}_metadata_{backup_id}_{timestamp}.json"
            metadata_path = os.path.join(self.config.backup_path, metadata_filename)
            
            # 构建元数据
            metadata = {
                "id": document.id,
                "filename": document.filename,
                "original_filename": document.original_filename,
                "file_size": document.file_size,
                "file_type": document.file_type,
                "file_extension": document.file_extension,
                "mime_type": document.mime_type,
                "storage_path": document.storage_path,
                "owner_id": document.owner_id,
                "status": document.status,
                "created_at": document.created_at.isoformat() if document.created_at else None,
                "updated_at": document.updated_at.isoformat() if document.updated_at else None,
                "description": document.description,
                "tags": document.tags,
                "backup_timestamp": datetime.utcnow().isoformat()
            }
            
            # 保存元数据
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            return metadata_path
            
        except Exception as e:
            self.logger.error(f"备份文档元数据失败: {str(e)}")
            return None
    
    async def _compress_file(self, source_path: str, target_path: str) -> bool:
        """
        压缩文件
        
        Args:
            source_path: 源文件路径
            target_path: 目标文件路径
            
        Returns:
            bool: 是否成功
        """
        try:
            import gzip
            
            with open(source_path, 'rb') as f_in:
                with gzip.open(target_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            return True
            
        except Exception as e:
            self.logger.error(f"压缩文件失败: {str(e)}")
            return False
    
    async def restore_document(self, backup_id: int, target_document_id: Optional[int] = None) -> bool:
        """
        恢复文档
        
        Args:
            backup_id: 备份ID
            target_document_id: 目标文档ID（如果为空则恢复到原文档）
            
        Returns:
            bool: 是否成功
        """
        try:
            # 获取备份记录
            backup_record = self.db.query(BackupRecord).filter(BackupRecord.id == backup_id).first()
            if not backup_record or backup_record.status != BackupStatus.COMPLETED:
                self.logger.error(f"备份记录不存在或状态异常: {backup_id}")
                return False
            
            # 确定目标文档
            target_id = target_document_id or backup_record.document_id
            target_document = self.db.query(Document).filter(Document.id == target_id).first()
            if not target_document:
                self.logger.error(f"目标文档不存在: {target_id}")
                return False
            
            # 恢复文件内容
            if not await self._restore_document_content(backup_record, target_document):
                return False
            
            # 恢复元数据（如果有）
            if backup_record.metadata_path and os.path.exists(backup_record.metadata_path):
                await self._restore_document_metadata(backup_record, target_document)
            
            # 更新文档状态
            target_document.status = DocumentStatus.ACTIVE
            target_document.updated_at = datetime.utcnow()
            self.db.commit()
            
            self.logger.info(f"文档恢复完成: {backup_id} -> {target_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"恢复文档失败: {str(e)}")
            return False
    
    async def _restore_document_content(self, backup_record: BackupRecord, target_document: Document) -> bool:
        """
        恢复文档内容
        
        Args:
            backup_record: 备份记录
            target_document: 目标文档
            
        Returns:
            bool: 是否成功
        """
        try:
            backup_path = backup_record.backup_path
            if not backup_path or not os.path.exists(backup_path):
                self.logger.error(f"备份文件不存在: {backup_path}")
                return False
            
            # 如果是压缩文件，先解压
            restore_path = backup_path
            if backup_path.endswith('.gz'):
                restore_path = backup_path[:-3]  # 去掉.gz后缀
                await self._decompress_file(backup_path, restore_path)
            
            # 上传到MinIO
            self.minio_client.fput_object(
                bucket_name=settings.MINIO_BUCKET_NAME,
                object_name=target_document.storage_path,
                file_path=restore_path
            )
            
            # 清理临时文件
            if restore_path != backup_path and os.path.exists(restore_path):
                os.remove(restore_path)
            
            return True
            
        except Exception as e:
            self.logger.error(f"恢复文档内容失败: {str(e)}")
            return False
    
    async def _decompress_file(self, source_path: str, target_path: str) -> bool:
        """
        解压文件
        
        Args:
            source_path: 源文件路径
            target_path: 目标文件路径
            
        Returns:
            bool: 是否成功
        """
        try:
            import gzip
            
            with gzip.open(source_path, 'rb') as f_in:
                with open(target_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            return True
            
        except Exception as e:
            self.logger.error(f"解压文件失败: {str(e)}")
            return False
    
    async def _restore_document_metadata(self, backup_record: BackupRecord, target_document: Document) -> bool:
        """
        恢复文档元数据
        
        Args:
            backup_record: 备份记录
            target_document: 目标文档
            
        Returns:
            bool: 是否成功
        """
        try:
            with open(backup_record.metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            # 恢复部分元数据（保留ID和所有者信息）
            target_document.description = metadata.get('description')
            target_document.tags = metadata.get('tags')
            
            return True
            
        except Exception as e:
            self.logger.error(f"恢复文档元数据失败: {str(e)}")
            return False
    
    async def cleanup_old_backups(self) -> int:
        """
        清理过期备份
        
        Returns:
            int: 清理的备份数量
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=self.config.retention_days)
            
            # 查询过期备份
            old_backups = self.db.query(BackupRecord).filter(
                BackupRecord.created_at < cutoff_date
            ).all()
            
            cleaned_count = 0
            for backup in old_backups:
                # 删除备份文件
                if backup.backup_path and os.path.exists(backup.backup_path):
                    os.remove(backup.backup_path)
                
                # 删除元数据文件
                if backup.metadata_path and os.path.exists(backup.metadata_path):
                    os.remove(backup.metadata_path)
                
                # 删除数据库记录
                self.db.delete(backup)
                cleaned_count += 1
            
            self.db.commit()
            
            self.logger.info(f"清理过期备份完成，共清理 {cleaned_count} 个备份")
            return cleaned_count
            
        except Exception as e:
            self.logger.error(f"清理过期备份失败: {str(e)}")
            return 0
    
    def get_backup_list(self, document_id: Optional[int] = None, limit: int = 100) -> List[BackupRecord]:
        """
        获取备份列表
        
        Args:
            document_id: 文档ID（可选）
            limit: 限制数量
            
        Returns:
            List[BackupRecord]: 备份记录列表
        """
        query = self.db.query(BackupRecord)
        
        if document_id:
            query = query.filter(BackupRecord.document_id == document_id)
        
        return query.order_by(BackupRecord.created_at.desc()).limit(limit).all()
    
    def get_backup_stats(self) -> Dict[str, Any]:
        """
        获取备份统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        try:
            total_backups = self.db.query(BackupRecord).count()
            completed_backups = self.db.query(BackupRecord).filter(
                BackupRecord.status == BackupStatus.COMPLETED
            ).count()
            failed_backups = self.db.query(BackupRecord).filter(
                BackupRecord.status == BackupStatus.FAILED
            ).count()
            
            # 计算总备份大小
            total_size = self.db.query(BackupRecord).filter(
                BackupRecord.status == BackupStatus.COMPLETED,
                BackupRecord.file_size.isnot(None)
            ).with_entities(BackupRecord.file_size).all()
            
            total_backup_size = sum(size[0] for size in total_size if size[0])
            
            return {
                "total_backups": total_backups,
                "completed_backups": completed_backups,
                "failed_backups": failed_backups,
                "success_rate": (completed_backups / total_backups * 100) if total_backups > 0 else 0,
                "total_backup_size": total_backup_size,
                "config": {
                    "retention_days": self.config.retention_days,
                    "backup_interval": self.config.backup_interval,
                    "max_backups": self.config.max_backups
                }
            }
            
        except Exception as e:
            self.logger.error(f"获取备份统计失败: {str(e)}")
            return {}


# 全局备份服务实例
_backup_service = None


def get_backup_service(db: Session = None, minio_client: Minio = None) -> DocumentBackupService:
    """
    获取备份服务实例
    
    Args:
        db: 数据库会话
        minio_client: MinIO客户端
        
    Returns:
        DocumentBackupService: 备份服务实例
    """
    global _backup_service
    
    if _backup_service is None and db and minio_client:
        config = BackupConfig(
            enabled=getattr(settings, 'BACKUP_ENABLED', True),
            backup_interval=getattr(settings, 'BACKUP_INTERVAL', 24),
            retention_days=getattr(settings, 'BACKUP_RETENTION_DAYS', 30),
            max_backups=getattr(settings, 'BACKUP_MAX_COUNT', 100),
            backup_path=getattr(settings, 'BACKUP_PATH', '/tmp/document_backups'),
            compress=getattr(settings, 'BACKUP_COMPRESS', True),
            encrypt=getattr(settings, 'BACKUP_ENCRYPT', False),
            backup_metadata=getattr(settings, 'BACKUP_METADATA', True)
        )
        _backup_service = DocumentBackupService(db, minio_client, config)
    
    return _backup_service