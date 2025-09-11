#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MinIO存储客户端模块

该模块提供MinIO对象存储的基础操作功能，包括文件上传、下载、删除等。
"""

import io
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, BinaryIO
from urllib.parse import urljoin

from minio import Minio
from minio.error import S3Error
from minio.commonconfig import CopySource
from minio.deleteobjects import DeleteObject

from config import get_config

logger = logging.getLogger(__name__)
config = get_config()


class MinIOStorage:
    """MinIO存储客户端类"""
    
    def __init__(self):
        """初始化MinIO客户端"""
        self.client = Minio(
            endpoint=config.minio_endpoint,
            access_key=config.minio_access_key,
            secret_key=config.minio_secret_key,
            secure=config.minio_secure
        )
        self.bucket_name = config.minio_bucket_name
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self) -> None:
        """确保存储桶存在"""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info(f"Created bucket: {self.bucket_name}")
            else:
                logger.info(f"Bucket {self.bucket_name} already exists")
        except S3Error as e:
            logger.error(f"Error creating bucket: {e}")
            raise
    
    def upload_file(
        self, 
        file_data: BinaryIO, 
        object_name: str, 
        content_type: str = "application/octet-stream",
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """上传文件到MinIO
        
        Args:
            file_data: 文件数据流
            object_name: 对象名称（文件路径）
            content_type: 文件MIME类型
            metadata: 文件元数据
            
        Returns:
            Dict: 上传结果信息
        """
        try:
            # 获取文件大小
            file_data.seek(0, 2)  # 移动到文件末尾
            file_size = file_data.tell()
            file_data.seek(0)  # 重置到文件开头
            
            # 上传文件
            result = self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                data=file_data,
                length=file_size,
                content_type=content_type,
                metadata=metadata or {}
            )
            
            logger.info(f"Successfully uploaded {object_name} to {self.bucket_name}")
            
            return {
                "bucket_name": self.bucket_name,
                "object_name": object_name,
                "etag": result.etag,
                "size": file_size,
                "content_type": content_type,
                "upload_time": datetime.utcnow().isoformat()
            }
            
        except S3Error as e:
            logger.error(f"Error uploading file {object_name}: {e}")
            raise
    
    def download_file(self, object_name: str) -> bytes:
        """从MinIO下载文件
        
        Args:
            object_name: 对象名称
            
        Returns:
            bytes: 文件内容
        """
        try:
            response = self.client.get_object(self.bucket_name, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            
            logger.info(f"Successfully downloaded {object_name} from {self.bucket_name}")
            return data
            
        except S3Error as e:
            logger.error(f"Error downloading file {object_name}: {e}")
            raise
    
    def get_file_stream(self, object_name: str):
        """获取文件流
        
        Args:
            object_name: 对象名称
            
        Returns:
            文件流对象
        """
        try:
            return self.client.get_object(self.bucket_name, object_name)
        except S3Error as e:
            logger.error(f"Error getting file stream {object_name}: {e}")
            raise
    
    def delete_file(self, object_name: str) -> bool:
        """删除文件
        
        Args:
            object_name: 对象名称
            
        Returns:
            bool: 删除是否成功
        """
        try:
            self.client.remove_object(self.bucket_name, object_name)
            logger.info(f"Successfully deleted {object_name} from {self.bucket_name}")
            return True
            
        except S3Error as e:
            logger.error(f"Error deleting file {object_name}: {e}")
            return False
    
    def delete_files(self, object_names: List[str]) -> Dict[str, bool]:
        """批量删除文件
        
        Args:
            object_names: 对象名称列表
            
        Returns:
            Dict: 删除结果，键为文件名，值为是否成功
        """
        results = {}
        
        try:
            delete_objects = [DeleteObject(name) for name in object_names]
            errors = self.client.remove_objects(self.bucket_name, delete_objects)
            
            # 处理删除结果
            error_objects = {error.object_name for error in errors}
            
            for object_name in object_names:
                if object_name in error_objects:
                    results[object_name] = False
                    logger.error(f"Failed to delete {object_name}")
                else:
                    results[object_name] = True
                    logger.info(f"Successfully deleted {object_name}")
            
            return results
            
        except S3Error as e:
            logger.error(f"Error in batch delete: {e}")
            # 如果批量删除失败，标记所有文件删除失败
            return {name: False for name in object_names}
    
    def file_exists(self, object_name: str) -> bool:
        """检查文件是否存在
        
        Args:
            object_name: 对象名称
            
        Returns:
            bool: 文件是否存在
        """
        try:
            self.client.stat_object(self.bucket_name, object_name)
            return True
        except S3Error:
            return False
    
    def get_file_info(self, object_name: str) -> Optional[Dict[str, Any]]:
        """获取文件信息
        
        Args:
            object_name: 对象名称
            
        Returns:
            Dict: 文件信息，如果文件不存在返回None
        """
        try:
            stat = self.client.stat_object(self.bucket_name, object_name)
            
            return {
                "object_name": object_name,
                "size": stat.size,
                "etag": stat.etag,
                "last_modified": stat.last_modified.isoformat(),
                "content_type": stat.content_type,
                "metadata": stat.metadata
            }
            
        except S3Error as e:
            logger.warning(f"File {object_name} not found: {e}")
            return None
    
    def list_files(self, prefix: str = "", recursive: bool = True) -> List[Dict[str, Any]]:
        """列出文件
        
        Args:
            prefix: 文件名前缀
            recursive: 是否递归列出子目录
            
        Returns:
            List: 文件信息列表
        """
        try:
            objects = self.client.list_objects(
                self.bucket_name, 
                prefix=prefix, 
                recursive=recursive
            )
            
            files = []
            for obj in objects:
                files.append({
                    "object_name": obj.object_name,
                    "size": obj.size,
                    "etag": obj.etag,
                    "last_modified": obj.last_modified.isoformat(),
                    "is_dir": obj.is_dir
                })
            
            return files
            
        except S3Error as e:
            logger.error(f"Error listing files: {e}")
            return []
    
    def generate_presigned_url(
        self, 
        object_name: str, 
        expires: timedelta = timedelta(hours=1),
        method: str = "GET"
    ) -> str:
        """生成预签名URL
        
        Args:
            object_name: 对象名称
            expires: 过期时间
            method: HTTP方法
            
        Returns:
            str: 预签名URL
        """
        try:
            url = self.client.presigned_get_object(
                self.bucket_name, 
                object_name, 
                expires=expires
            )
            return url
            
        except S3Error as e:
            logger.error(f"Error generating presigned URL for {object_name}: {e}")
            raise
    
    def copy_file(self, source_object: str, dest_object: str) -> bool:
        """复制文件
        
        Args:
            source_object: 源对象名称
            dest_object: 目标对象名称
            
        Returns:
            bool: 复制是否成功
        """
        try:
            copy_source = CopySource(self.bucket_name, source_object)
            self.client.copy_object(
                self.bucket_name,
                dest_object,
                copy_source
            )
            
            logger.info(f"Successfully copied {source_object} to {dest_object}")
            return True
            
        except S3Error as e:
            logger.error(f"Error copying file from {source_object} to {dest_object}: {e}")
            return False
    
    def get_bucket_usage(self) -> Dict[str, Any]:
        """获取存储桶使用情况
        
        Returns:
            Dict: 存储桶使用统计
        """
        try:
            objects = self.client.list_objects(self.bucket_name, recursive=True)
            
            total_size = 0
            file_count = 0
            
            for obj in objects:
                if not obj.is_dir:
                    total_size += obj.size
                    file_count += 1
            
            return {
                "bucket_name": self.bucket_name,
                "total_size": total_size,
                "file_count": file_count,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "total_size_gb": round(total_size / (1024 * 1024 * 1024), 2)
            }
            
        except S3Error as e:
            logger.error(f"Error getting bucket usage: {e}")
            return {
                "bucket_name": self.bucket_name,
                "total_size": 0,
                "file_count": 0,
                "error": str(e)
            }


# 全局存储客户端实例
storage_client = MinIOStorage()


def get_storage_client() -> MinIOStorage:
    """获取存储客户端实例
    
    Returns:
        MinIOStorage: 存储客户端实例
    """
    return storage_client