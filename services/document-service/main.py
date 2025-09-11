#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
文档存储服务

提供文档上传、下载、管理等功能的微服务。
"""

import logging
from contextlib import asynccontextmanager
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from .config import get_settings
from .database import init_database, get_db, close_database, check_database_connection
from .storage import init_storage, get_storage
from .services import get_document_service
from .preview import get_preview_service
from .backup import get_backup_service
from .schemas import (
    DocumentCreate, DocumentUpdate, DocumentResponse, DocumentListResponse,
    DocumentSearchRequest, UploadInitRequest, UploadInitResponse,
    UploadCompleteRequest, UploadCompleteResponse, UserQuotaCreate,
    UserQuotaUpdate, UserQuotaResponse, DocumentPermissionCreate,
    DocumentPermissionResponse, DocumentShareCreate, DocumentShareResponse,
    DocumentAccessLogResponse, DocumentTagCreate, DocumentTagResponse,
    DocumentStatsResponse, MessageResponse, ErrorResponse, DocumentBatchDeleteRequest,
    DocumentBatchDeleteResponse
)
from .models import Document, DocumentStatus, AccessLevel

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    logger.info("正在启动文档存储服务...")
    
    try:
        # 初始化数据库
        init_database()
        logger.info("数据库初始化完成")
        
        # 初始化存储
        init_storage()
        logger.info("存储服务初始化完成")
        
        logger.info("文档存储服务启动成功")
        
    except Exception as e:
        logger.error(f"服务启动失败: {e}")
        raise
    
    yield
    
    # 关闭时清理
    logger.info("正在关闭文档存储服务...")
    close_database()
    logger.info("文档存储服务已关闭")


# 创建FastAPI应用
app = FastAPI(
    title="文档存储服务",
    description="提供文档上传、下载、管理等功能",
    version="1.0.0",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该限制具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 异常处理器
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP异常处理器"""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            code=str(exc.status_code)
        ).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理器"""
    logger.error(f"未处理的异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="内部服务器错误",
            detail=str(exc),
            code="500"
        ).dict()
    )


# 辅助函数
def get_current_user_id(request: Request) -> Optional[int]:
    """从请求中获取当前用户ID
    
    Args:
        request: FastAPI请求对象
        
    Returns:
        Optional[int]: 用户ID，如果未认证则返回None
    """
    # 这里应该从JWT令牌或其他认证方式中获取用户ID
    # 暂时从请求头中获取
    user_id = request.headers.get("X-User-ID")
    return int(user_id) if user_id else None


# 基础端点
@app.get("/")
async def root():
    """根路径响应"""
    return {
        "service": "文档存储服务",
        "status": "运行中",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """健康检查端点"""
    db_status = check_database_connection()
    storage_status = True  # 可以添加存储健康检查
    
    return {
        "status": "healthy" if db_status and storage_status else "unhealthy",
        "service": "document-service",
        "database": "connected" if db_status else "disconnected",
        "storage": "connected" if storage_status else "disconnected"
    }


# 文档管理端点
@app.post("/documents/upload/init", response_model=UploadInitResponse)
async def init_upload(
    request: UploadInitRequest,
    req: Request,
    db: Session = Depends(get_db)
):
    """初始化文档上传
    
    Args:
        request: 上传初始化请求
        req: FastAPI请求对象
        db: 数据库会话
        
    Returns:
        UploadInitResponse: 上传初始化响应
    """
    user_id = get_current_user_id(req)
    if not user_id:
        raise HTTPException(status_code=401, detail="未认证")
    
    service = get_document_service(db)
    result = service.init_multipart_upload(request, user_id)
    
    return UploadInitResponse(**result)


@app.post("/documents/upload/complete", response_model=UploadCompleteResponse)
async def complete_upload(
    request: UploadCompleteRequest,
    req: Request,
    db: Session = Depends(get_db)
):
    """完成文档上传
    
    Args:
        request: 完成上传请求
        req: FastAPI请求对象
        db: 数据库会话
        
    Returns:
        UploadCompleteResponse: 完成上传响应
    """
    user_id = get_current_user_id(req)
    if not user_id:
        raise HTTPException(status_code=401, detail="未认证")
    
    service = get_document_service(db)
    document = service.complete_multipart_upload(request)
    
    return UploadCompleteResponse(
        document=DocumentResponse.from_orm(document),
        success=True,
        message="文档上传完成"
    )


@app.get("/documents", response_model=DocumentListResponse)
async def search_documents(
    req: Request,
    query: Optional[str] = Query(None, description="搜索关键词"),
    owner_id: Optional[int] = Query(None, description="所有者用户ID"),
    status: Optional[str] = Query(None, description="文档状态"),
    access_level: Optional[str] = Query(None, description="访问级别"),
    content_type: Optional[str] = Query(None, description="MIME类型"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页大小"),
    sort_by: str = Query("created_at", description="排序字段"),
    sort_order: str = Query("desc", description="排序方向"),
    db: Session = Depends(get_db)
):
    """搜索文档
    
    Args:
        req: FastAPI请求对象
        query: 搜索关键词
        owner_id: 所有者用户ID
        status: 文档状态
        access_level: 访问级别
        content_type: MIME类型
        page: 页码
        size: 每页大小
        sort_by: 排序字段
        sort_order: 排序方向
        db: 数据库会话
        
    Returns:
        DocumentListResponse: 文档列表响应
    """
    user_id = get_current_user_id(req)
    
    search_request = DocumentSearchRequest(
        query=query,
        owner_id=owner_id,
        status=status,
        access_level=access_level,
        content_type=content_type,
        page=page,
        size=size,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    service = get_document_service(db)
    documents, total = service.search_documents(search_request, user_id)
    
    pages = (total + size - 1) // size
    
    return DocumentListResponse(
        documents=[DocumentResponse.from_orm(doc) for doc in documents],
        total=total,
        page=page,
        size=size,
        pages=pages
    )


@app.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    req: Request,
    db: Session = Depends(get_db)
):
    """获取文档信息
    
    Args:
        document_id: 文档ID
        req: FastAPI请求对象
        db: 数据库会话
        
    Returns:
        DocumentResponse: 文档响应
    """
    user_id = get_current_user_id(req)
    
    service = get_document_service(db)
    document = service.get_document(document_id, user_id)
    
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    return DocumentResponse.from_orm(document)


@app.put("/documents/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: int,
    update_data: DocumentUpdate,
    req: Request,
    db: Session = Depends(get_db)
):
    """更新文档信息
    
    Args:
        document_id: 文档ID
        update_data: 更新数据
        req: FastAPI请求对象
        db: 数据库会话
        
    Returns:
        DocumentResponse: 更新后的文档响应
    """
    user_id = get_current_user_id(req)
    if not user_id:
        raise HTTPException(status_code=401, detail="未认证")
    
    service = get_document_service(db)
    document = service.update_document(document_id, update_data, user_id)
    
    return DocumentResponse.from_orm(document)


@app.delete("/documents/{document_id}", response_model=MessageResponse)
async def delete_document(
    document_id: int,
    req: Request,
    permanent: bool = Query(False, description="是否永久删除"),
    db: Session = Depends(get_db)
):
    """删除文档
    
    Args:
        document_id: 文档ID
        req: FastAPI请求对象
        permanent: 是否永久删除
        db: 数据库会话
        
    Returns:
        MessageResponse: 删除结果响应
    """
    user_id = get_current_user_id(req)
    if not user_id:
        raise HTTPException(status_code=401, detail="未认证")
    
    service = get_document_service(db)
    success = service.delete_document(document_id, user_id, permanent)
    
    return MessageResponse(
        message="文档删除成功" if success else "文档删除失败",
        success=success
    )


@app.post("/documents/batch/delete", response_model=DocumentBatchDeleteResponse)
async def batch_delete_documents(
    request: DocumentBatchDeleteRequest,
    req: Request,
    db: Session = Depends(get_db)
):
    """批量删除文档
    
    Args:
        request: 批量删除请求
        req: FastAPI请求对象
        db: 数据库会话
        
    Returns:
        DocumentBatchDeleteResponse: 批量删除响应
    """
    user_id = get_current_user_id(req)
    if not user_id:
        raise HTTPException(status_code=401, detail="未认证")
    
    service = get_document_service(db)
    result = service.batch_delete_documents(request.document_ids, user_id, request.permanent)
    
    return DocumentBatchDeleteResponse(
        success_count=result['success_count'],
        failed_count=result['failed_count'],
        failed_documents=result['failed_documents'],
        message=f"成功删除 {result['success_count']} 个文档，失败 {result['failed_count']} 个"
    )


@app.post("/documents/batch/restore", response_model=MessageResponse)
async def batch_restore_documents(
    document_ids: List[int],
    req: Request,
    db: Session = Depends(get_db)
):
    """批量恢复文档
    
    Args:
        document_ids: 文档ID列表
        req: FastAPI请求对象
        db: 数据库会话
        
    Returns:
        MessageResponse: 恢复结果响应
    """
    user_id = get_current_user_id(req)
    if not user_id:
        raise HTTPException(status_code=401, detail="未认证")
    
    service = get_document_service(db)
    result = service.batch_restore_documents(document_ids, user_id)
    
    return MessageResponse(
        message=f"成功恢复 {result['success_count']} 个文档，失败 {result['failed_count']} 个",
        success=result['success_count'] > 0
    )


@app.get("/documents/trash", response_model=DocumentListResponse)
async def get_trash_documents(
    req: Request,
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页大小"),
    db: Session = Depends(get_db)
):
    """获取回收站文档
    
    Args:
        req: FastAPI请求对象
        page: 页码
        size: 每页大小
        db: 数据库会话
        
    Returns:
        DocumentListResponse: 回收站文档列表响应
    """
    user_id = get_current_user_id(req)
    if not user_id:
        raise HTTPException(status_code=401, detail="未认证")
    
    service = get_document_service(db)
    documents, total = service.get_trash_documents(user_id, page, size)
    
    pages = (total + size - 1) // size
    
    return DocumentListResponse(
        documents=[DocumentResponse.from_orm(doc) for doc in documents],
        total=total,
        page=page,
        size=size,
        pages=pages
    )


@app.post("/documents/{document_id}/restore", response_model=MessageResponse)
async def restore_document(
    document_id: int,
    req: Request,
    db: Session = Depends(get_db)
):
    """恢复文档
    
    Args:
        document_id: 文档ID
        req: FastAPI请求对象
        db: 数据库会话
        
    Returns:
        MessageResponse: 恢复结果响应
    """
    user_id = get_current_user_id(req)
    if not user_id:
        raise HTTPException(status_code=401, detail="未认证")
    
    service = get_document_service(db)
    success = service.restore_document(document_id, user_id)
    
    return MessageResponse(
        message="文档恢复成功" if success else "文档恢复失败",
        success=success
    )


@app.get("/documents/{document_id}/download")
async def download_document(
    document_id: int,
    req: Request,
    expires: int = Query(3600, ge=60, le=86400, description="URL过期时间（秒）"),
    db: Session = Depends(get_db)
):
    """下载文档
    
    Args:
        document_id: 文档ID
        req: FastAPI请求对象
        expires: URL过期时间（秒）
        db: 数据库会话
        
    Returns:
        RedirectResponse: 重定向到下载URL
    """
    user_id = get_current_user_id(req)
    
    service = get_document_service(db)
    download_url = service.get_download_url(document_id, user_id, expires)
    
    return RedirectResponse(url=download_url)


@app.get("/documents/{document_id}/preview")
async def preview_document(
    document_id: int,
    req: Request,
    page: int = Query(1, ge=1, description="页码"),
    width: int = Query(800, ge=100, le=2000, description="预览宽度"),
    height: int = Query(600, ge=100, le=2000, description="预览高度"),
    db: Session = Depends(get_db)
):
    """预览文档
    
    Args:
        document_id: 文档ID
        req: FastAPI请求对象
        page: 页码
        width: 预览宽度
        height: 预览高度
        db: 数据库会话
        
    Returns:
        StreamingResponse: 预览图片流
    """
    user_id = get_current_user_id(req)
    
    service = get_document_service(db)
    document = service.get_document(document_id, user_id)
    
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    # 生成预览
    preview_service = get_preview_service()
    
    if not preview_service.is_previewable(document.content_type):
        raise HTTPException(
            status_code=400,
            detail=f"不支持预览的文件类型: {document.content_type}"
        )
    
    return await preview_service.generate_preview(
        document.file_path,
        document.content_type,
        page=page,
        size=(width, height)
    )


@app.get("/documents/{document_id}/info")
async def get_document_info(
    document_id: int,
    req: Request,
    db: Session = Depends(get_db)
):
    """获取文档详细信息
    
    Args:
        document_id: 文档ID
        req: FastAPI请求对象
        db: 数据库会话
        
    Returns:
        dict: 文档详细信息
    """
    user_id = get_current_user_id(req)
    
    service = get_document_service(db)
    document = service.get_document(document_id, user_id)
    
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    # 获取预览服务
    preview_service = get_preview_service()
    
    # 构建响应
    response_data = {
        "id": document.id,
        "filename": document.filename,
        "content_type": document.content_type,
        "file_size": document.file_size,
        "status": document.status.value,
        "access_level": document.access_level.value,
        "description": document.description,
        "tags": document.tags,
        "metadata": document.metadata,
        "created_at": document.created_at,
        "updated_at": document.updated_at,
        "download_count": document.download_count,
        "is_previewable": preview_service.is_previewable(document.content_type),
        "owner_id": document.owner_id
    }
    
    # 如果是所有者，返回更多信息
    if document.owner_id == user_id:
        response_data.update({
            "file_path": document.file_path,
            "checksum": document.checksum
        })
    
    return response_data


# 权限管理端点
@app.post("/documents/{document_id}/permissions", response_model=DocumentPermissionResponse)
async def create_document_permission(
    document_id: int,
    permission_data: DocumentPermissionCreate,
    req: Request,
    db: Session = Depends(get_db)
):
    """创建文档权限
    
    Args:
        document_id: 文档ID
        permission_data: 权限数据
        req: FastAPI请求对象
        db: 数据库会话
        
    Returns:
        DocumentPermissionResponse: 权限响应
    """
    user_id = get_current_user_id(req)
    if not user_id:
        raise HTTPException(status_code=401, detail="未认证")
    
    service = get_document_service(db)
    permission = service.create_document_permission(document_id, user_id, permission_data)
    
    return DocumentPermissionResponse.from_orm(permission)


@app.get("/documents/{document_id}/permissions", response_model=List[DocumentPermissionResponse])
async def get_document_permissions(
    document_id: int,
    req: Request,
    db: Session = Depends(get_db)
):
    """获取文档权限列表
    
    Args:
        document_id: 文档ID
        req: FastAPI请求对象
        db: 数据库会话
        
    Returns:
        List[DocumentPermissionResponse]: 权限列表
    """
    user_id = get_current_user_id(req)
    if not user_id:
        raise HTTPException(status_code=401, detail="未认证")
    
    service = get_document_service(db)
    permissions = service.get_document_permissions(document_id, user_id)
    
    return [DocumentPermissionResponse.from_orm(perm) for perm in permissions]


@app.put("/documents/{document_id}/permissions/{permission_id}", response_model=DocumentPermissionResponse)
async def update_document_permission(
    document_id: int,
    permission_id: int,
    permission_data: DocumentPermissionUpdate,
    req: Request,
    db: Session = Depends(get_db)
):
    """更新文档权限
    
    Args:
        document_id: 文档ID
        permission_id: 权限ID
        permission_data: 权限更新数据
        req: FastAPI请求对象
        db: 数据库会话
        
    Returns:
        DocumentPermissionResponse: 更新后的权限响应
    """
    user_id = get_current_user_id(req)
    if not user_id:
        raise HTTPException(status_code=401, detail="未认证")
    
    service = get_document_service(db)
    permission = service.update_document_permission(document_id, permission_id, user_id, permission_data)
    
    return DocumentPermissionResponse.from_orm(permission)


@app.delete("/documents/{document_id}/permissions/{permission_id}", response_model=MessageResponse)
async def delete_document_permission(
    document_id: int,
    permission_id: int,
    req: Request,
    db: Session = Depends(get_db)
):
    """删除文档权限
    
    Args:
        document_id: 文档ID
        permission_id: 权限ID
        req: FastAPI请求对象
        db: 数据库会话
        
    Returns:
        MessageResponse: 删除结果响应
    """
    user_id = get_current_user_id(req)
    if not user_id:
        raise HTTPException(status_code=401, detail="未认证")
    
    service = get_document_service(db)
    success = service.delete_document_permission(document_id, permission_id, user_id)
    
    return MessageResponse(
        message="权限删除成功" if success else "权限删除失败",
        success=success
    )


@app.post("/documents/{document_id}/share", response_model=DocumentShareResponse)
async def create_document_share(
    document_id: int,
    share_data: DocumentShareCreate,
    req: Request,
    db: Session = Depends(get_db)
):
    """创建文档分享链接
    
    Args:
        document_id: 文档ID
        share_data: 分享数据
        req: FastAPI请求对象
        db: 数据库会话
        
    Returns:
        DocumentShareResponse: 分享链接响应
    """
    user_id = get_current_user_id(req)
    if not user_id:
        raise HTTPException(status_code=401, detail="未认证")
    
    service = get_document_service(db)
    share = service.create_document_share(document_id, user_id, share_data)
    
    return DocumentShareResponse.from_orm(share)


@app.get("/documents/{document_id}/shares", response_model=List[DocumentShareResponse])
async def get_document_shares(
    document_id: int,
    req: Request,
    db: Session = Depends(get_db)
):
    """获取文档分享链接列表
    
    Args:
        document_id: 文档ID
        req: FastAPI请求对象
        db: 数据库会话
        
    Returns:
        List[DocumentShareResponse]: 分享链接列表
    """
    user_id = get_current_user_id(req)
    if not user_id:
        raise HTTPException(status_code=401, detail="未认证")
    
    service = get_document_service(db)
    shares = service.get_document_shares(document_id, user_id)
    
    return [DocumentShareResponse.from_orm(share) for share in shares]


@app.delete("/shares/{share_id}", response_model=MessageResponse)
async def delete_document_share(
    share_id: int,
    req: Request,
    db: Session = Depends(get_db)
):
    """删除文档分享链接
    
    Args:
        share_id: 分享ID
        req: FastAPI请求对象
        db: 数据库会话
        
    Returns:
        MessageResponse: 删除结果响应
    """
    user_id = get_current_user_id(req)
    if not user_id:
        raise HTTPException(status_code=401, detail="未认证")
    
    service = get_document_service(db)
    success = service.delete_document_share(share_id, user_id)
    
    return MessageResponse(
        message="分享链接删除成功" if success else "分享链接删除失败",
        success=success
    )


# 配额管理端点
@app.get("/quotas/{user_id}", response_model=UserQuotaResponse)
async def get_user_quota(
    user_id: int,
    req: Request,
    db: Session = Depends(get_db)
):
    """获取用户配额信息
    
    Args:
        user_id: 用户ID
        req: FastAPI请求对象
        db: 数据库会话
        
    Returns:
        UserQuotaResponse: 用户配额响应
    """
    current_user_id = get_current_user_id(req)
    if not current_user_id:
        raise HTTPException(status_code=401, detail="未认证")
    
    # 只能查看自己的配额信息（除非是管理员）
    if current_user_id != user_id:
        raise HTTPException(status_code=403, detail="无权限查看此配额信息")
    
    service = get_document_service(db)
    quota = service.get_user_quota(user_id)
    
    if not quota:
        raise HTTPException(status_code=404, detail="用户配额不存在")
    
    return UserQuotaResponse.from_orm(quota)


@app.post("/quotas", response_model=UserQuotaResponse)
async def create_user_quota(
    quota_data: UserQuotaCreate,
    req: Request,
    db: Session = Depends(get_db)
):
    """创建用户配额
    
    Args:
        quota_data: 配额创建数据
        req: FastAPI请求对象
        db: 数据库会话
        
    Returns:
        UserQuotaResponse: 创建的配额响应
    """
    user_id = get_current_user_id(req)
    if not user_id:
        raise HTTPException(status_code=401, detail="未认证")
    
    # 这里应该检查管理员权限
    
    service = get_document_service(db)
    quota = service.create_user_quota(quota_data)
    
    return UserQuotaResponse.from_orm(quota)


@app.put("/quotas/{user_id}", response_model=UserQuotaResponse)
async def update_user_quota(
    user_id: int,
    update_data: UserQuotaUpdate,
    req: Request,
    db: Session = Depends(get_db)
):
    """更新用户配额
    
    Args:
        user_id: 用户ID
        update_data: 更新数据
        req: FastAPI请求对象
        db: 数据库会话
        
    Returns:
        UserQuotaResponse: 更新后的配额响应
    """
    current_user_id = get_current_user_id(req)
    if not current_user_id:
        raise HTTPException(status_code=401, detail="未认证")
    
    # 这里应该检查管理员权限
    
    service = get_document_service(db)
    quota = service.update_user_quota(user_id, update_data)
    
    return UserQuotaResponse.from_orm(quota)


# 统计端点
@app.get("/stats", response_model=DocumentStatsResponse)
async def get_document_stats(
    req: Request,
    db: Session = Depends(get_db)
):
    """获取文档统计信息
    
    Args:
        req: FastAPI请求对象
        db: 数据库会话
        
    Returns:
        DocumentStatsResponse: 文档统计响应
    """
    user_id = get_current_user_id(req)
    if not user_id:
        raise HTTPException(status_code=401, detail="未认证")
    
    # 获取用户的文档统计
    total_docs = db.query(Document).filter(Document.owner_id == user_id).count()
    total_size = db.query(func.sum(Document.file_size)).filter(Document.owner_id == user_id).scalar() or 0
    
    # 按状态统计
    status_stats = {}
    for status in DocumentStatus:
        count = db.query(Document).filter(
            Document.owner_id == user_id,
            Document.status == status
        ).count()
        status_stats[status.value] = count
    
    # 按内容类型统计
    content_type_stats = {}
    content_types = db.query(Document.content_type, func.count(Document.id)).filter(
        Document.owner_id == user_id
    ).group_by(Document.content_type).all()
    
    for content_type, count in content_types:
        content_type_stats[content_type] = count
    
    # 按访问级别统计
    access_level_stats = {}
    for level in AccessLevel:
        count = db.query(Document).filter(
            Document.owner_id == user_id,
            Document.access_level == level
        ).count()
        access_level_stats[level.value] = count
    
    # 最近上传的文档
    recent_uploads = db.query(Document).filter(
        Document.owner_id == user_id
    ).order_by(desc(Document.created_at)).limit(5).all()
    
    # 热门文档（按下载次数）
    popular_docs = db.query(Document).filter(
        Document.owner_id == user_id
    ).order_by(desc(Document.download_count)).limit(5).all()
    
    return DocumentStatsResponse(
        total_documents=total_docs,
        total_size=total_size,
        by_status=status_stats,
        by_content_type=content_type_stats,
        by_access_level=access_level_stats,
        recent_uploads=[DocumentResponse.from_orm(doc) for doc in recent_uploads],
        popular_documents=[DocumentResponse.from_orm(doc) for doc in popular_docs]
    )


# 存储配额管理端点
@app.get("/quota", response_model=UserQuotaResponse)
async def get_user_quota(
    req: Request,
    db: Session = Depends(get_db)
):
    """获取用户存储配额信息
    
    Args:
        req: FastAPI请求对象
        db: 数据库会话
        
    Returns:
        UserQuotaResponse: 用户配额响应
    """
    user_id = get_current_user_id(req)
    if not user_id:
        raise HTTPException(status_code=401, detail="未认证")
    
    service = get_document_service(db)
    quota = service.get_user_quota(user_id)
    
    if not quota:
        raise HTTPException(status_code=404, detail="配额信息不存在")
    
    return UserQuotaResponse.from_orm(quota)


@app.post("/quota", response_model=UserQuotaResponse)
async def create_user_quota(
    quota_data: UserQuotaCreate,
    req: Request,
    db: Session = Depends(get_db)
):
    """创建用户存储配额
    
    Args:
        quota_data: 配额创建数据
        req: FastAPI请求对象
        db: 数据库会话
        
    Returns:
        UserQuotaResponse: 创建的配额响应
    """
    user_id = get_current_user_id(req)
    if not user_id:
        raise HTTPException(status_code=401, detail="未认证")
    
    # 检查是否为管理员（这里应该从用户信息中获取角色）
    # 暂时允许所有认证用户创建配额
    
    service = get_document_service(db)
    quota = service.create_user_quota(quota_data)
    
    return UserQuotaResponse.from_orm(quota)


@app.put("/quota/{user_id}", response_model=UserQuotaResponse)
async def update_user_quota(
    user_id: int,
    quota_data: UserQuotaUpdate,
    req: Request,
    db: Session = Depends(get_db)
):
    """更新用户存储配额
    
    Args:
        user_id: 用户ID
        quota_data: 配额更新数据
        req: FastAPI请求对象
        db: 数据库会话
        
    Returns:
        UserQuotaResponse: 更新后的配额响应
    """
    current_user_id = get_current_user_id(req)
    if not current_user_id:
        raise HTTPException(status_code=401, detail="未认证")
    
    # 检查权限：管理员或用户本人
    # 暂时只允许用户本人更新
    if current_user_id != user_id:
        raise HTTPException(status_code=403, detail="权限不足")
    
    service = get_document_service(db)
    quota = service.update_user_quota(user_id, quota_data)
    
    if not quota:
        raise HTTPException(status_code=404, detail="配额信息不存在")
    
    return UserQuotaResponse.from_orm(quota)


@app.get("/quota/usage/{user_id}")
async def get_quota_usage(
    user_id: int,
    req: Request,
    db: Session = Depends(get_db)
):
    """获取用户配额使用情况
    
    Args:
        user_id: 用户ID
        req: FastAPI请求对象
        db: 数据库会话
        
    Returns:
        dict: 配额使用情况
    """
    current_user_id = get_current_user_id(req)
    if not current_user_id:
        raise HTTPException(status_code=401, detail="未认证")
    
    # 检查权限：管理员或用户本人
    # 暂时只允许用户本人查看
    if current_user_id != user_id:
        raise HTTPException(status_code=403, detail="权限不足")
    
    service = get_document_service(db)
    usage = service.get_quota_usage(user_id)
    
    return usage


@app.post("/quota/check")
async def check_quota_limit(
    size: int = Query(..., description="文件大小（字节）"),
    req: Request = None,
    db: Session = Depends(get_db)
):
    """检查是否超出配额限制
    
    Args:
        size: 文件大小（字节）
        req: FastAPI请求对象
        db: 数据库会话
        
    Returns:
        dict: 检查结果
    """
    user_id = get_current_user_id(req)
    if not user_id:
        raise HTTPException(status_code=401, detail="未认证")
    
    service = get_document_service(db)
    can_upload = service.check_quota_limit(user_id, size)
    
    return {
         "can_upload": can_upload,
         "message": "可以上传" if can_upload else "超出配额限制"
     }


# 备份和恢复端点
@app.post("/backup/{document_id}")
async def create_backup(
    document_id: int,
    backup_type: str = Query("manual", description="备份类型"),
    req: Request = None,
    db: Session = Depends(get_db)
):
    """创建文档备份
    
    Args:
        document_id: 文档ID
        backup_type: 备份类型
        req: FastAPI请求对象
        db: 数据库会话
        
    Returns:
        dict: 备份结果
    """
    user_id = get_current_user_id(req)
    if not user_id:
        raise HTTPException(status_code=401, detail="未认证")
    
    # 检查文档权限
    service = get_document_service(db)
    document = service.get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    if document.owner_id != user_id:
        raise HTTPException(status_code=403, detail="权限不足")
    
    # 创建备份
    backup_service = get_backup_service(db, get_minio_client())
    backup_record = await backup_service.create_backup(document_id, backup_type)
    
    if not backup_record:
        raise HTTPException(status_code=500, detail="备份创建失败")
    
    return {
        "backup_id": backup_record.id,
        "status": backup_record.status,
        "message": "备份创建成功"
    }


@app.post("/restore/{backup_id}")
async def restore_document(
    backup_id: int,
    target_document_id: Optional[int] = Query(None, description="目标文档ID"),
    req: Request = None,
    db: Session = Depends(get_db)
):
    """恢复文档
    
    Args:
        backup_id: 备份ID
        target_document_id: 目标文档ID
        req: FastAPI请求对象
        db: 数据库会话
        
    Returns:
        dict: 恢复结果
    """
    user_id = get_current_user_id(req)
    if not user_id:
        raise HTTPException(status_code=401, detail="未认证")
    
    # 获取备份记录
    backup_service = get_backup_service(db, get_minio_client())
    backup_records = backup_service.get_backup_list()
    backup_record = next((b for b in backup_records if b.id == backup_id), None)
    
    if not backup_record:
        raise HTTPException(status_code=404, detail="备份记录不存在")
    
    # 检查权限
    service = get_document_service(db)
    document = service.get_document(backup_record.document_id)
    if not document or document.owner_id != user_id:
        raise HTTPException(status_code=403, detail="权限不足")
    
    # 执行恢复
    success = await backup_service.restore_document(backup_id, target_document_id)
    
    if not success:
        raise HTTPException(status_code=500, detail="文档恢复失败")
    
    return {
        "message": "文档恢复成功",
        "backup_id": backup_id,
        "target_document_id": target_document_id or backup_record.document_id
    }


@app.get("/backups")
async def get_backup_list(
    document_id: Optional[int] = Query(None, description="文档ID"),
    limit: int = Query(100, description="限制数量"),
    req: Request = None,
    db: Session = Depends(get_db)
):
    """获取备份列表
    
    Args:
        document_id: 文档ID
        limit: 限制数量
        req: FastAPI请求对象
        db: 数据库会话
        
    Returns:
        dict: 备份列表
    """
    user_id = get_current_user_id(req)
    if not user_id:
        raise HTTPException(status_code=401, detail="未认证")
    
    backup_service = get_backup_service(db, get_minio_client())
    backups = backup_service.get_backup_list(document_id, limit)
    
    # 过滤用户权限
    service = get_document_service(db)
    filtered_backups = []
    for backup in backups:
        document = service.get_document(backup.document_id)
        if document and document.owner_id == user_id:
            filtered_backups.append({
                "id": backup.id,
                "document_id": backup.document_id,
                "backup_type": backup.backup_type,
                "status": backup.status,
                "file_size": backup.file_size,
                "created_at": backup.created_at,
                "completed_at": backup.completed_at,
                "error_message": backup.error_message
            })
    
    return {
        "backups": filtered_backups,
        "total": len(filtered_backups)
    }


@app.get("/backup/stats")
async def get_backup_stats(
    req: Request = None,
    db: Session = Depends(get_db)
):
    """获取备份统计信息
    
    Args:
        req: FastAPI请求对象
        db: 数据库会话
        
    Returns:
        dict: 备份统计信息
    """
    user_id = get_current_user_id(req)
    if not user_id:
        raise HTTPException(status_code=401, detail="未认证")
    
    backup_service = get_backup_service(db, get_minio_client())
    stats = backup_service.get_backup_stats()
    
    return stats


@app.post("/backup/cleanup")
async def cleanup_old_backups(
    req: Request = None,
    db: Session = Depends(get_db)
):
    """清理过期备份
    
    Args:
        req: FastAPI请求对象
        db: 数据库会话
        
    Returns:
        dict: 清理结果
    """
    user_id = get_current_user_id(req)
    if not user_id:
        raise HTTPException(status_code=401, detail="未认证")
    
    # 这里可以添加管理员权限检查
    
    backup_service = get_backup_service(db, get_minio_client())
    cleaned_count = await backup_service.cleanup_old_backups()
    
    return {
        "message": f"清理完成，共清理 {cleaned_count} 个过期备份",
        "cleaned_count": cleaned_count
    }


if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info" if not settings.DEBUG else "debug"
    )