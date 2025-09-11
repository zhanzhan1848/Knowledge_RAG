#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
文档服务业务逻辑

该模块实现文档相关的业务逻辑，包括文档的创建、查询、更新、删除等操作。
"""

import os
import uuid
import hashlib
import mimetypes
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, func
from fastapi import HTTPException, UploadFile
from minio.error import S3Error

from .models import (
    Document, DocumentPermission, UserQuota, DocumentAccessLog,
    DocumentTag, DocumentShare, DocumentStatus, AccessLevel, PermissionType
)
from .schemas import (
    DocumentCreate, DocumentUpdate, DocumentSearchRequest,
    UploadInitRequest, UploadCompleteRequest, DocumentPermissionCreate,
    UserQuotaCreate, UserQuotaUpdate, DocumentShareCreate,
    DocumentAccessLogCreate, DocumentTagCreate
)
from .storage import get_storage
from .config import get_settings


class DocumentService:
    """文档服务类"""
    
    def __init__(self, db: Session):
        """初始化文档服务
        
        Args:
            db: 数据库会话
        """
        self.db = db
        self.storage = get_storage()
        self.settings = get_settings()
    
    def create_document(self, document_data: DocumentCreate, owner_id: int) -> Document:
        """创建文档记录
        
        Args:
            document_data: 文档创建数据
            owner_id: 所有者用户ID
            
        Returns:
            Document: 创建的文档对象
            
        Raises:
            HTTPException: 当配额不足或其他错误时
        """
        # 检查用户配额
        quota = self.get_user_quota(owner_id)
        if quota and not quota.can_upload(document_data.file_size):
            raise HTTPException(
                status_code=413,
                detail=f"存储配额不足。可用空间: {quota.available_quota} 字节，需要: {document_data.file_size} 字节"
            )
        
        # 生成唯一的对象名称
        file_extension = Path(document_data.filename).suffix.lower()
        object_name = f"{uuid.uuid4().hex}{file_extension}"
        
        # 创建文档记录
        document = Document(
            filename=document_data.filename,
            display_name=document_data.display_name or document_data.filename,
            description=document_data.description,
            object_name=object_name,
            bucket_name=self.settings.MINIO_BUCKET_NAME,
            file_size=document_data.file_size,
            content_type=document_data.content_type,
            file_extension=file_extension,
            owner_id=owner_id,
            access_level=document_data.access_level,
            status=DocumentStatus.UPLOADING
        )
        
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        
        return document
    
    def init_multipart_upload(self, request: UploadInitRequest, owner_id: int) -> Dict[str, Any]:
        """初始化分片上传
        
        Args:
            request: 上传初始化请求
            owner_id: 所有者用户ID
            
        Returns:
            Dict: 包含上传ID和预签名URL的字典
        """
        # 创建文档记录
        document_data = DocumentCreate(
            filename=request.filename,
            display_name=request.display_name,
            description=request.description,
            content_type=request.content_type,
            file_size=request.file_size,
            access_level=request.access_level
        )
        
        document = self.create_document(document_data, owner_id)
        
        try:
            # 计算分片数量
            chunk_count = (request.file_size + request.chunk_size - 1) // request.chunk_size
            
            # 初始化MinIO分片上传
            upload_id = self.storage.init_multipart_upload(
                document.bucket_name,
                document.object_name
            )
            
            # 生成预签名上传URL
            upload_urls = []
            for part_number in range(1, chunk_count + 1):
                url = self.storage.get_presigned_upload_url(
                    document.bucket_name,
                    document.object_name,
                    upload_id,
                    part_number
                )
                upload_urls.append(url)
            
            return {
                "upload_id": upload_id,
                "document_id": document.id,
                "chunk_count": chunk_count,
                "chunk_size": request.chunk_size,
                "upload_urls": upload_urls,
                "expires_at": datetime.utcnow() + timedelta(hours=1)
            }
            
        except Exception as e:
            # 如果初始化失败，删除文档记录
            self.db.delete(document)
            self.db.commit()
            raise HTTPException(status_code=500, detail=f"初始化上传失败: {str(e)}")
    
    def complete_multipart_upload(self, request: UploadCompleteRequest) -> Document:
        """完成分片上传
        
        Args:
            request: 完成上传请求
            
        Returns:
            Document: 更新后的文档对象
        """
        # 查找文档记录
        document = self.db.query(Document).filter(
            Document.id == request.document_id,
            Document.status == DocumentStatus.UPLOADING
        ).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在或状态无效")
        
        try:
            # 完成MinIO分片上传
            etag = self.storage.complete_multipart_upload(
                document.bucket_name,
                document.object_name,
                request.upload_id,
                request.parts
            )
            
            # 更新文档状态
            document.status = DocumentStatus.PROCESSING
            document.etag = etag
            document.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            # 更新用户配额
            self._update_user_quota(document.owner_id, document.file_size)
            
            # 异步处理文档（如果需要）
            self._process_document_async(document)
            
            return document
            
        except Exception as e:
            # 上传失败，标记为错误状态
            document.status = DocumentStatus.ERROR
            document.processing_error = str(e)
            self.db.commit()
            raise HTTPException(status_code=500, detail=f"完成上传失败: {str(e)}")
    
    def get_document(self, document_id: int, user_id: Optional[int] = None) -> Optional[Document]:
        """获取文档信息
        
        Args:
            document_id: 文档ID
            user_id: 用户ID（用于权限检查）
            
        Returns:
            Document: 文档对象，如果不存在或无权限则返回None
        """
        query = self.db.query(Document).filter(Document.id == document_id)
        
        # 如果指定了用户ID，检查权限
        if user_id is not None:
            query = query.filter(
                or_(
                    Document.owner_id == user_id,
                    Document.access_level == AccessLevel.PUBLIC,
                    and_(
                        Document.access_level == AccessLevel.SHARED,
                        Document.permissions.any(
                            and_(
                                DocumentPermission.user_id == user_id,
                                DocumentPermission.is_active == True,
                                or_(
                                    DocumentPermission.expires_at.is_(None),
                                    DocumentPermission.expires_at > datetime.utcnow()
                                )
                            )
                        )
                    )
                )
            )
        
        return query.first()
    
    def search_documents(self, request: DocumentSearchRequest, user_id: Optional[int] = None) -> Tuple[List[Document], int]:
        """搜索文档
        
        Args:
            request: 搜索请求
            user_id: 用户ID（用于权限过滤）
            
        Returns:
            Tuple[List[Document], int]: 文档列表和总数
        """
        query = self.db.query(Document)
        
        # 权限过滤
        if user_id is not None:
            query = query.filter(
                or_(
                    Document.owner_id == user_id,
                    Document.access_level == AccessLevel.PUBLIC,
                    and_(
                        Document.access_level == AccessLevel.SHARED,
                        Document.permissions.any(
                            and_(
                                DocumentPermission.user_id == user_id,
                                DocumentPermission.is_active == True,
                                or_(
                                    DocumentPermission.expires_at.is_(None),
                                    DocumentPermission.expires_at > datetime.utcnow()
                                )
                            )
                        )
                    )
                )
            )
        
        # 搜索条件
        if request.query:
            search_term = f"%{request.query}%"
            query = query.filter(
                or_(
                    Document.filename.ilike(search_term),
                    Document.display_name.ilike(search_term),
                    Document.description.ilike(search_term)
                )
            )
        
        if request.owner_id:
            query = query.filter(Document.owner_id == request.owner_id)
        
        if request.status:
            query = query.filter(Document.status == request.status)
        
        if request.access_level:
            query = query.filter(Document.access_level == request.access_level)
        
        if request.content_type:
            query = query.filter(Document.content_type.ilike(f"%{request.content_type}%"))
        
        if request.file_extension:
            query = query.filter(Document.file_extension == request.file_extension)
        
        if request.created_after:
            query = query.filter(Document.created_at >= request.created_after)
        
        if request.created_before:
            query = query.filter(Document.created_at <= request.created_before)
        
        if request.min_size:
            query = query.filter(Document.file_size >= request.min_size)
        
        if request.max_size:
            query = query.filter(Document.file_size <= request.max_size)
        
        # 标签过滤
        if request.tags:
            for tag in request.tags:
                query = query.filter(
                    Document.id.in_(
                        self.db.query(DocumentTag.document_id).filter(
                            DocumentTag.tag_name == tag
                        )
                    )
                )
        
        # 获取总数
        total = query.count()
        
        # 排序
        sort_column = getattr(Document, request.sort_by, Document.created_at)
        if request.sort_order == 'desc':
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))
        
        # 分页
        offset = (request.page - 1) * request.size
        documents = query.offset(offset).limit(request.size).all()
        
        return documents, total
    
    def update_document(self, document_id: int, update_data: DocumentUpdate, user_id: int) -> Document:
        """更新文档信息
        
        Args:
            document_id: 文档ID
            update_data: 更新数据
            user_id: 用户ID
            
        Returns:
            Document: 更新后的文档对象
        """
        document = self.get_document(document_id, user_id)
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        # 检查权限（只有所有者可以更新）
        if document.owner_id != user_id:
            raise HTTPException(status_code=403, detail="无权限更新此文档")
        
        # 更新字段
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(document, field, value)
        
        document.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(document)
        
        return document
    
    def delete_document(self, document_id: int, user_id: int, permanent: bool = False) -> bool:
        """删除文档
        
        Args:
            document_id: 文档ID
            user_id: 用户ID
            permanent: 是否永久删除
            
        Returns:
            bool: 是否删除成功
        """
        document = self.get_document(document_id, user_id)
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        # 检查权限（只有所有者可以删除）
        if document.owner_id != user_id:
            raise HTTPException(status_code=403, detail="无权限删除此文档")
        
        try:
            if permanent:
                # 永久删除：从存储和数据库中删除
                self.storage.delete_object(document.bucket_name, document.object_name)
                
                # 更新用户配额
                self._update_user_quota(document.owner_id, -document.file_size)
                
                # 删除数据库记录
                self.db.delete(document)
            else:
                # 软删除：标记为已删除
                document.status = DocumentStatus.DELETED
                document.deleted_at = datetime.utcnow()
            
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"删除文档失败: {str(e)}")
    
    def get_download_url(self, document_id: int, user_id: Optional[int] = None, expires: int = 3600) -> str:
        """获取文档下载URL
        
        Args:
            document_id: 文档ID
            user_id: 用户ID
            expires: URL过期时间（秒）
            
        Returns:
            str: 预签名下载URL
        """
        document = self.get_document(document_id, user_id)
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        if document.status != DocumentStatus.ACTIVE:
            raise HTTPException(status_code=400, detail="文档状态不允许下载")
        
        try:
            # 生成预签名下载URL
            url = self.storage.get_presigned_download_url(
                document.bucket_name,
                document.object_name,
                expires
            )
            
            # 记录访问日志
            self._log_document_access(document.id, user_id, "download")
            
            # 更新下载计数
            document.download_count += 1
            document.last_accessed_at = datetime.utcnow()
            self.db.commit()
            
            return url
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"生成下载URL失败: {str(e)}")
    
    def get_user_quota(self, user_id: int) -> Optional[UserQuota]:
        """获取用户配额信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            UserQuota: 用户配额对象
        """
        return self.db.query(UserQuota).filter(UserQuota.user_id == user_id).first()
    
    def create_user_quota(self, quota_data: UserQuotaCreate) -> UserQuota:
        """创建用户配额
        
        Args:
            quota_data: 配额创建数据
            
        Returns:
            UserQuota: 创建的配额对象
        """
        # 检查是否已存在
        existing = self.get_user_quota(quota_data.user_id)
        if existing:
            raise HTTPException(status_code=400, detail="用户配额已存在")
        
        quota = UserQuota(**quota_data.dict())
        self.db.add(quota)
        self.db.commit()
        self.db.refresh(quota)
        
        return quota
    
    def update_user_quota(self, user_id: int, update_data: UserQuotaUpdate) -> UserQuota:
        """更新用户配额
        
        Args:
            user_id: 用户ID
            update_data: 更新数据
            
        Returns:
            UserQuota: 更新后的配额对象
        """
        quota = self.get_user_quota(user_id)
        if not quota:
            raise HTTPException(status_code=404, detail="用户配额不存在")
        
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(quota, field, value)
        
        quota.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(quota)
        
        return quota
    
    def batch_delete_documents(self, document_ids: List[int], user_id: int, permanent: bool = False) -> Dict[str, Any]:
        """批量删除文档
        
        Args:
            document_ids: 文档ID列表
            user_id: 用户ID
            permanent: 是否永久删除
            
        Returns:
            Dict[str, Any]: 删除结果统计
        """
        success_count = 0
        failed_count = 0
        failed_documents = []
        
        for doc_id in document_ids:
            try:
                document = self.db.query(Document).filter(
                    Document.id == doc_id,
                    Document.owner_id == user_id
                ).first()
                
                if not document:
                    failed_count += 1
                    failed_documents.append({
                        "id": doc_id,
                        "reason": "文档不存在或无权限"
                    })
                    continue
                
                if permanent:
                    # 永久删除：从存储和数据库中删除
                    try:
                        self.storage.delete_object(document.bucket_name, document.object_name)
                    except Exception as e:
                        # 记录警告但继续删除数据库记录
                        pass
                    
                    # 更新用户配额
                    self._update_user_quota(document.owner_id, -document.file_size)
                    
                    # 删除数据库记录
                    self.db.delete(document)
                else:
                    # 软删除：标记为已删除状态
                    document.status = DocumentStatus.DELETED
                    document.deleted_at = datetime.utcnow()
                
                success_count += 1
                
            except Exception as e:
                failed_count += 1
                failed_documents.append({
                    "id": doc_id,
                    "reason": str(e)
                })
        
        self.db.commit()
        
        return {
            "success_count": success_count,
            "failed_count": failed_count,
            "failed_documents": failed_documents
        }
    
    def batch_restore_documents(self, document_ids: List[int], user_id: int) -> Dict[str, Any]:
        """批量恢复文档
        
        Args:
            document_ids: 文档ID列表
            user_id: 用户ID
            
        Returns:
            Dict[str, Any]: 恢复结果统计
        """
        success_count = 0
        failed_count = 0
        failed_documents = []
        
        for doc_id in document_ids:
            try:
                document = self.db.query(Document).filter(
                    Document.id == doc_id,
                    Document.owner_id == user_id,
                    Document.status == DocumentStatus.DELETED
                ).first()
                
                if not document:
                    failed_count += 1
                    failed_documents.append({
                        "id": doc_id,
                        "reason": "文档不存在或无权限"
                    })
                    continue
                
                document.status = DocumentStatus.ACTIVE
                document.updated_at = datetime.utcnow()
                success_count += 1
                
            except Exception as e:
                failed_count += 1
                failed_documents.append({
                    "id": doc_id,
                    "reason": str(e)
                })
        
        self.db.commit()
        
        return {
            "success_count": success_count,
            "failed_count": failed_count,
            "failed_documents": failed_documents
        }
    
    def get_trash_documents(self, user_id: int, page: int = 1, size: int = 20) -> Tuple[List[Document], int]:
        """获取回收站文档
        
        Args:
            user_id: 用户ID
            page: 页码
            size: 每页大小
            
        Returns:
            Tuple[List[Document], int]: 文档列表和总数
        """
        query = self.db.query(Document).filter(
            Document.owner_id == user_id,
            Document.status == DocumentStatus.DELETED
        )
        
        total = query.count()
        
        documents = query.order_by(desc(Document.updated_at)).offset(
            (page - 1) * size
        ).limit(size).all()
        
        return documents, total
    
    def restore_document(self, document_id: int, user_id: int) -> bool:
        """恢复单个文档
        
        Args:
            document_id: 文档ID
            user_id: 用户ID
            
        Returns:
            bool: 是否恢复成功
        """
        try:
            document = self.db.query(Document).filter(
                Document.id == document_id,
                Document.owner_id == user_id,
                Document.status == DocumentStatus.DELETED
            ).first()
            
            if not document:
                return False
            
            document.status = DocumentStatus.ACTIVE
            document.updated_at = datetime.utcnow()
            
            self.db.commit()
            return True
            
        except Exception as e:
             self.db.rollback()
             return False
    
    def create_document_permission(self, document_id: int, owner_id: int, permission_data: DocumentPermissionCreate) -> DocumentPermission:
        """创建文档权限
        
        Args:
            document_id: 文档ID
            owner_id: 文档所有者ID
            permission_data: 权限数据
            
        Returns:
            DocumentPermission: 创建的权限记录
        """
        # 检查文档是否存在且用户是所有者
        document = self.db.query(Document).filter(
            Document.id == document_id,
            Document.owner_id == owner_id
        ).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在或无权限")
        
        # 检查权限是否已存在
        existing_permission = self.db.query(DocumentPermission).filter(
            DocumentPermission.document_id == document_id,
            DocumentPermission.user_id == permission_data.user_id
        ).first()
        
        if existing_permission:
            raise HTTPException(status_code=400, detail="用户权限已存在")
        
        # 创建权限记录
        permission = DocumentPermission(
            document_id=document_id,
            user_id=permission_data.user_id,
            permission_type=permission_data.permission_type,
            granted_by=owner_id,
            expires_at=permission_data.expires_at
        )
        
        self.db.add(permission)
        self.db.commit()
        self.db.refresh(permission)
        
        return permission
    
    def get_document_permissions(self, document_id: int, owner_id: int) -> List[DocumentPermission]:
        """获取文档权限列表
        
        Args:
            document_id: 文档ID
            owner_id: 文档所有者ID
            
        Returns:
            List[DocumentPermission]: 权限列表
        """
        # 检查文档是否存在且用户是所有者
        document = self.db.query(Document).filter(
            Document.id == document_id,
            Document.owner_id == owner_id
        ).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在或无权限")
        
        return self.db.query(DocumentPermission).filter(
            DocumentPermission.document_id == document_id
        ).all()
    
    def update_document_permission(self, document_id: int, permission_id: int, owner_id: int, permission_data: DocumentPermissionUpdate) -> DocumentPermission:
        """更新文档权限
        
        Args:
            document_id: 文档ID
            permission_id: 权限ID
            owner_id: 文档所有者ID
            permission_data: 权限更新数据
            
        Returns:
            DocumentPermission: 更新后的权限记录
        """
        # 检查文档是否存在且用户是所有者
        document = self.db.query(Document).filter(
            Document.id == document_id,
            Document.owner_id == owner_id
        ).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在或无权限")
        
        # 获取权限记录
        permission = self.db.query(DocumentPermission).filter(
            DocumentPermission.id == permission_id,
            DocumentPermission.document_id == document_id
        ).first()
        
        if not permission:
            raise HTTPException(status_code=404, detail="权限记录不存在")
        
        # 更新权限信息
        for field, value in permission_data.dict(exclude_unset=True).items():
            setattr(permission, field, value)
        
        permission.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(permission)
        
        return permission
    
    def delete_document_permission(self, document_id: int, permission_id: int, owner_id: int) -> bool:
        """删除文档权限
        
        Args:
            document_id: 文档ID
            permission_id: 权限ID
            owner_id: 文档所有者ID
            
        Returns:
            bool: 是否删除成功
        """
        try:
            # 检查文档是否存在且用户是所有者
            document = self.db.query(Document).filter(
                Document.id == document_id,
                Document.owner_id == owner_id
            ).first()
            
            if not document:
                return False
            
            # 获取并删除权限记录
            permission = self.db.query(DocumentPermission).filter(
                DocumentPermission.id == permission_id,
                DocumentPermission.document_id == document_id
            ).first()
            
            if not permission:
                return False
            
            self.db.delete(permission)
            self.db.commit()
            
            return True
            
        except Exception as e:
            self.db.rollback()
            return False
    
    def create_document_share(self, document_id: int, owner_id: int, share_data: DocumentShareCreate) -> DocumentShare:
        """创建文档分享链接
        
        Args:
            document_id: 文档ID
            owner_id: 文档所有者ID
            share_data: 分享数据
            
        Returns:
            DocumentShare: 创建的分享记录
        """
        # 检查文档是否存在且用户是所有者
        document = self.db.query(Document).filter(
            Document.id == document_id,
            Document.owner_id == owner_id
        ).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在或无权限")
        
        # 生成分享链接
        import uuid
        share_token = str(uuid.uuid4())
        
        # 创建分享记录
        share = DocumentShare(
            document_id=document_id,
            share_token=share_token,
            password=share_data.password,
            expires_at=share_data.expires_at,
            max_downloads=share_data.max_downloads,
            created_by=owner_id
        )
        
        self.db.add(share)
        self.db.commit()
        self.db.refresh(share)
        
        return share
    
    def get_document_shares(self, document_id: int, owner_id: int) -> List[DocumentShare]:
        """获取文档分享链接列表
        
        Args:
            document_id: 文档ID
            owner_id: 文档所有者ID
            
        Returns:
            List[DocumentShare]: 分享链接列表
        """
        # 检查文档是否存在且用户是所有者
        document = self.db.query(Document).filter(
            Document.id == document_id,
            Document.owner_id == owner_id
        ).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在或无权限")
        
        return self.db.query(DocumentShare).filter(
            DocumentShare.document_id == document_id
        ).all()
    
    def delete_document_share(self, share_id: int, owner_id: int) -> bool:
        """删除文档分享链接
        
        Args:
            share_id: 分享ID
            owner_id: 文档所有者ID
            
        Returns:
            bool: 是否删除成功
        """
        try:
            # 获取分享记录
            share = self.db.query(DocumentShare).filter(
                DocumentShare.id == share_id,
                DocumentShare.created_by == owner_id
            ).first()
            
            if not share:
                return False
            
            self.db.delete(share)
            self.db.commit()
            
            return True
            
        except Exception as e:
            self.db.rollback()
            return False
    
    def _update_user_quota(self, user_id: int, size_delta: int) -> None:
        """更新用户配额使用量
        
        Args:
            user_id: 用户ID
            size_delta: 大小变化（正数表示增加，负数表示减少）
        """
        quota = self.get_user_quota(user_id)
        if quota:
            quota.used_quota += size_delta
            if size_delta > 0:
                quota.file_count += 1
            elif size_delta < 0:
                quota.file_count = max(0, quota.file_count - 1)
            
            quota.updated_at = datetime.utcnow()
            self.db.commit()
    
    def get_quota_usage(self, user_id: int) -> dict:
        """获取用户配额使用情况
        
        Args:
            user_id: 用户ID
            
        Returns:
            dict: 配额使用情况
        """
        quota = self.get_user_quota(user_id)
        if not quota:
            return {
                "total_quota": 0,
                "used_quota": 0,
                "available_quota": 0,
                "usage_percentage": 0,
                "file_count": 0
            }
        
        available_quota = quota.total_quota - quota.used_quota
        usage_percentage = (quota.used_quota / quota.total_quota * 100) if quota.total_quota > 0 else 0
        
        return {
            "total_quota": quota.total_quota,
            "used_quota": quota.used_quota,
            "available_quota": available_quota,
            "usage_percentage": round(usage_percentage, 2),
            "file_count": quota.file_count
        }
    
    def check_quota_limit(self, user_id: int, size: int) -> bool:
        """检查是否超出配额限制
        
        Args:
            user_id: 用户ID
            size: 文件大小
            
        Returns:
            bool: 是否可以上传
        """
        quota = self.get_user_quota(user_id)
        if not quota:
            # 如果没有配额记录，默认不允许上传
            return False
        
        return quota.can_upload(size)
    
    def get_user_quota_summary(self, user_id: int) -> dict:
        """获取用户配额摘要信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            dict: 配额摘要信息
        """
        quota = self.get_user_quota(user_id)
        if not quota:
            return None
        
        # 获取文档统计
        document_count = self.db.query(Document).filter(
            Document.owner_id == user_id,
            Document.status != DocumentStatus.DELETED
        ).count()
        
        # 获取最近上传的文档
        recent_documents = self.db.query(Document).filter(
            Document.owner_id == user_id,
            Document.status != DocumentStatus.DELETED
        ).order_by(desc(Document.created_at)).limit(5).all()
        
        return {
            "quota": quota,
            "document_count": document_count,
            "recent_documents": recent_documents,
            "usage_info": self.get_quota_usage(user_id)
        }
    
    def _process_document_async(self, document: Document) -> None:
        """异步处理文档
        
        Args:
            document: 文档对象
        """
        # 这里可以添加异步处理逻辑，如：
        # - 文档内容提取
        # - 缩略图生成
        # - 病毒扫描
        # - 格式转换等
        
        # 暂时直接标记为活跃状态
        document.status = DocumentStatus.ACTIVE
        document.processing_status = "completed"
        self.db.commit()
    
    def _log_document_access(self, document_id: int, user_id: Optional[int], action: str, 
                           ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> None:
        """记录文档访问日志
        
        Args:
            document_id: 文档ID
            user_id: 用户ID
            action: 操作类型
            ip_address: IP地址
            user_agent: 用户代理
        """
        log = DocumentAccessLog(
            document_id=document_id,
            user_id=user_id,
            action=action,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.db.add(log)
        self.db.commit()


def get_document_service(db: Session) -> DocumentService:
    """获取文档服务实例
    
    Args:
        db: 数据库会话
        
    Returns:
        DocumentService: 文档服务实例
    """
    return DocumentService(db)