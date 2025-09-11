#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据验证模式

该模块定义了API请求和响应的数据验证模式，使用Pydantic进行数据验证和序列化。
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

from pydantic import BaseModel, Field, validator, root_validator
from pydantic.types import PositiveInt, NonNegativeInt

from .models import DocumentStatus, AccessLevel, PermissionType


class DocumentStatusEnum(str, Enum):
    """文档状态枚举"""
    UPLOADING = "uploading"
    PROCESSING = "processing"
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"
    ERROR = "error"


class AccessLevelEnum(str, Enum):
    """访问级别枚举"""
    PRIVATE = "private"
    SHARED = "shared"
    PUBLIC = "public"


class PermissionTypeEnum(str, Enum):
    """权限类型枚举"""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    SHARE = "share"


# 基础模式
class BaseSchema(BaseModel):
    """基础模式"""
    
    class Config:
        orm_mode = True
        use_enum_values = True
        allow_population_by_field_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


# 文档相关模式
class DocumentBase(BaseSchema):
    """文档基础模式"""
    filename: str = Field(..., min_length=1, max_length=255, description="文件名")
    display_name: Optional[str] = Field(None, max_length=255, description="显示名称")
    description: Optional[str] = Field(None, description="文档描述")
    access_level: AccessLevelEnum = Field(AccessLevelEnum.PRIVATE, description="访问级别")
    
    @validator('filename')
    def validate_filename(cls, v):
        """验证文件名"""
        if not v or v.strip() == "":
            raise ValueError("文件名不能为空")
        
        # 检查非法字符
        illegal_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for char in illegal_chars:
            if char in v:
                raise ValueError(f"文件名不能包含字符: {char}")
        
        return v.strip()


class DocumentCreate(DocumentBase):
    """创建文档请求模式"""
    content_type: str = Field(..., description="MIME类型")
    file_size: PositiveInt = Field(..., description="文件大小（字节）")
    
    @validator('content_type')
    def validate_content_type(cls, v):
        """验证MIME类型"""
        if not v or '/' not in v:
            raise ValueError("无效的MIME类型")
        return v.lower()


class DocumentUpdate(BaseSchema):
    """更新文档请求模式"""
    display_name: Optional[str] = Field(None, max_length=255, description="显示名称")
    description: Optional[str] = Field(None, description="文档描述")
    access_level: Optional[AccessLevelEnum] = Field(None, description="访问级别")
    status: Optional[DocumentStatusEnum] = Field(None, description="文档状态")


class DocumentResponse(DocumentBase):
    """文档响应模式"""
    id: int = Field(..., description="文档ID")
    object_name: str = Field(..., description="存储对象名称")
    bucket_name: str = Field(..., description="存储桶名称")
    file_size: int = Field(..., description="文件大小（字节）")
    content_type: str = Field(..., description="MIME类型")
    file_extension: Optional[str] = Field(None, description="文件扩展名")
    etag: Optional[str] = Field(None, description="文件ETag")
    owner_id: int = Field(..., description="所有者用户ID")
    status: DocumentStatusEnum = Field(..., description="文档状态")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    deleted_at: Optional[datetime] = Field(None, description="删除时间")
    download_count: NonNegativeInt = Field(0, description="下载次数")
    view_count: NonNegativeInt = Field(0, description="查看次数")
    last_accessed_at: Optional[datetime] = Field(None, description="最后访问时间")
    version: PositiveInt = Field(1, description="版本号")
    parent_id: Optional[int] = Field(None, description="父文档ID")
    processing_status: Optional[str] = Field(None, description="处理状态")
    processing_error: Optional[str] = Field(None, description="处理错误信息")


class DocumentListResponse(BaseSchema):
    """文档列表响应模式"""
    documents: List[DocumentResponse] = Field(..., description="文档列表")
    total: NonNegativeInt = Field(..., description="总数")
    page: PositiveInt = Field(..., description="页码")
    size: PositiveInt = Field(..., description="每页大小")
    pages: NonNegativeInt = Field(..., description="总页数")


# 权限相关模式
class DocumentPermissionBase(BaseSchema):
    """文档权限基础模式"""
    user_id: int = Field(..., description="用户ID")
    permission_type: PermissionTypeEnum = Field(..., description="权限类型")
    expires_at: Optional[datetime] = Field(None, description="过期时间")


class DocumentPermissionCreate(DocumentPermissionBase):
    """创建文档权限请求模式"""
    pass


class DocumentPermissionResponse(DocumentPermissionBase):
    """文档权限响应模式"""
    id: int = Field(..., description="权限ID")
    document_id: int = Field(..., description="文档ID")
    granted_by: int = Field(..., description="授权者用户ID")
    granted_at: datetime = Field(..., description="授权时间")
    is_active: bool = Field(..., description="是否活跃")


# 配额相关模式
class UserQuotaBase(BaseSchema):
    """用户配额基础模式"""
    total_quota: PositiveInt = Field(..., description="总配额（字节）")
    max_file_size: Optional[PositiveInt] = Field(None, description="单文件最大大小（字节）")


class UserQuotaCreate(UserQuotaBase):
    """创建用户配额请求模式"""
    user_id: int = Field(..., description="用户ID")


class UserQuotaUpdate(BaseSchema):
    """更新用户配额请求模式"""
    total_quota: Optional[PositiveInt] = Field(None, description="总配额（字节）")
    max_file_size: Optional[PositiveInt] = Field(None, description="单文件最大大小（字节）")


class UserQuotaResponse(UserQuotaBase):
    """用户配额响应模式"""
    id: int = Field(..., description="配额ID")
    user_id: int = Field(..., description="用户ID")
    used_quota: NonNegativeInt = Field(..., description="已使用配额（字节）")
    file_count: NonNegativeInt = Field(..., description="文件数量")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    available_quota: int = Field(..., description="可用配额（字节）")
    usage_percentage: float = Field(..., description="使用率百分比")


# 分享相关模式
class DocumentShareBase(BaseSchema):
    """文档分享基础模式"""
    expires_at: Optional[datetime] = Field(None, description="过期时间")
    max_downloads: Optional[PositiveInt] = Field(None, description="最大下载次数")
    password: Optional[str] = Field(None, min_length=4, max_length=50, description="访问密码")


class DocumentShareCreate(DocumentShareBase):
    """创建文档分享请求模式"""
    document_id: int = Field(..., description="文档ID")


class DocumentShareResponse(DocumentShareBase):
    """文档分享响应模式"""
    id: int = Field(..., description="分享ID")
    document_id: int = Field(..., description="文档ID")
    share_token: str = Field(..., description="分享令牌")
    created_by: int = Field(..., description="创建者用户ID")
    download_count: NonNegativeInt = Field(..., description="已下载次数")
    is_active: bool = Field(..., description="是否活跃")
    created_at: datetime = Field(..., description="创建时间")
    is_expired: bool = Field(..., description="是否已过期")
    is_download_limit_reached: bool = Field(..., description="是否已达下载上限")
    can_access: bool = Field(..., description="是否可以访问")


# 访问日志相关模式
class DocumentAccessLogCreate(BaseSchema):
    """创建访问日志请求模式"""
    document_id: int = Field(..., description="文档ID")
    user_id: Optional[int] = Field(None, description="用户ID")
    action: str = Field(..., min_length=1, max_length=50, description="操作类型")
    ip_address: Optional[str] = Field(None, max_length=45, description="IP地址")
    user_agent: Optional[str] = Field(None, description="用户代理")


class DocumentAccessLogResponse(DocumentAccessLogCreate):
    """访问日志响应模式"""
    id: int = Field(..., description="日志ID")
    accessed_at: datetime = Field(..., description="访问时间")


# 标签相关模式
class DocumentTagBase(BaseSchema):
    """文档标签基础模式"""
    tag_name: str = Field(..., min_length=1, max_length=50, description="标签名称")
    
    @validator('tag_name')
    def validate_tag_name(cls, v):
        """验证标签名称"""
        if not v or v.strip() == "":
            raise ValueError("标签名称不能为空")
        
        # 只允许字母、数字、中文、下划线和连字符
        import re
        if not re.match(r'^[\w\u4e00-\u9fff-]+$', v.strip()):
            raise ValueError("标签名称只能包含字母、数字、中文、下划线和连字符")
        
        return v.strip()


class DocumentTagCreate(DocumentTagBase):
    """创建文档标签请求模式"""
    document_id: int = Field(..., description="文档ID")


class DocumentTagResponse(DocumentTagBase):
    """文档标签响应模式"""
    id: int = Field(..., description="标签ID")
    document_id: int = Field(..., description="文档ID")
    created_by: int = Field(..., description="创建者用户ID")
    created_at: datetime = Field(..., description="创建时间")


# 上传相关模式
class UploadInitRequest(BaseSchema):
    """初始化上传请求模式"""
    filename: str = Field(..., min_length=1, max_length=255, description="文件名")
    file_size: PositiveInt = Field(..., description="文件大小（字节）")
    content_type: str = Field(..., description="MIME类型")
    chunk_size: Optional[PositiveInt] = Field(8 * 1024 * 1024, description="分片大小（字节）")
    display_name: Optional[str] = Field(None, max_length=255, description="显示名称")
    description: Optional[str] = Field(None, description="文档描述")
    access_level: AccessLevelEnum = Field(AccessLevelEnum.PRIVATE, description="访问级别")
    
    @validator('chunk_size')
    def validate_chunk_size(cls, v):
        """验证分片大小"""
        min_size = 5 * 1024 * 1024  # 5MB
        max_size = 100 * 1024 * 1024  # 100MB
        
        if v < min_size:
            raise ValueError(f"分片大小不能小于 {min_size} 字节")
        if v > max_size:
            raise ValueError(f"分片大小不能大于 {max_size} 字节")
        
        return v


class UploadInitResponse(BaseSchema):
    """初始化上传响应模式"""
    upload_id: str = Field(..., description="上传ID")
    document_id: int = Field(..., description="文档ID")
    chunk_count: int = Field(..., description="分片总数")
    chunk_size: int = Field(..., description="分片大小（字节）")
    upload_urls: List[str] = Field(..., description="上传URL列表")
    expires_at: datetime = Field(..., description="上传链接过期时间")


class UploadCompleteRequest(BaseSchema):
    """完成上传请求模式"""
    upload_id: str = Field(..., description="上传ID")
    parts: List[Dict[str, Any]] = Field(..., description="分片信息列表")
    
    @validator('parts')
    def validate_parts(cls, v):
        """验证分片信息"""
        if not v:
            raise ValueError("分片信息不能为空")
        
        for i, part in enumerate(v):
            if 'PartNumber' not in part or 'ETag' not in part:
                raise ValueError(f"分片 {i+1} 缺少必要字段")
            
            if not isinstance(part['PartNumber'], int) or part['PartNumber'] < 1:
                raise ValueError(f"分片 {i+1} 的 PartNumber 无效")
            
            if not isinstance(part['ETag'], str) or not part['ETag']:
                raise ValueError(f"分片 {i+1} 的 ETag 无效")
        
        return v


class UploadCompleteResponse(BaseSchema):
    """完成上传响应模式"""
    document: DocumentResponse = Field(..., description="文档信息")
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")


# 搜索和过滤模式
class DocumentSearchRequest(BaseSchema):
    """文档搜索请求模式"""
    query: Optional[str] = Field(None, min_length=1, description="搜索关键词")
    owner_id: Optional[int] = Field(None, description="所有者用户ID")
    status: Optional[DocumentStatusEnum] = Field(None, description="文档状态")
    access_level: Optional[AccessLevelEnum] = Field(None, description="访问级别")
    content_type: Optional[str] = Field(None, description="MIME类型")
    file_extension: Optional[str] = Field(None, description="文件扩展名")
    tags: Optional[List[str]] = Field(None, description="标签列表")
    created_after: Optional[datetime] = Field(None, description="创建时间起始")
    created_before: Optional[datetime] = Field(None, description="创建时间结束")
    min_size: Optional[NonNegativeInt] = Field(None, description="最小文件大小")
    max_size: Optional[PositiveInt] = Field(None, description="最大文件大小")
    page: PositiveInt = Field(1, description="页码")
    size: PositiveInt = Field(20, description="每页大小")
    sort_by: Optional[str] = Field("created_at", description="排序字段")
    sort_order: Optional[str] = Field("desc", description="排序方向")
    
    @validator('size')
    def validate_size(cls, v):
        """验证每页大小"""
        if v > 100:
            raise ValueError("每页大小不能超过100")
        return v
    
    @validator('sort_by')
    def validate_sort_by(cls, v):
        """验证排序字段"""
        allowed_fields = [
            'created_at', 'updated_at', 'filename', 'file_size',
            'download_count', 'view_count', 'last_accessed_at'
        ]
        if v not in allowed_fields:
            raise ValueError(f"排序字段必须是: {', '.join(allowed_fields)}")
        return v
    
    @validator('sort_order')
    def validate_sort_order(cls, v):
        """验证排序方向"""
        if v.lower() not in ['asc', 'desc']:
            raise ValueError("排序方向必须是 'asc' 或 'desc'")
        return v.lower()


# 统计相关模式
class DocumentStatsResponse(BaseSchema):
    """文档统计响应模式"""
    total_documents: NonNegativeInt = Field(..., description="文档总数")
    total_size: NonNegativeInt = Field(..., description="总大小（字节）")
    by_status: Dict[str, int] = Field(..., description="按状态统计")
    by_content_type: Dict[str, int] = Field(..., description="按类型统计")
    by_access_level: Dict[str, int] = Field(..., description="按访问级别统计")
    recent_uploads: List[DocumentResponse] = Field(..., description="最近上传")
    popular_documents: List[DocumentResponse] = Field(..., description="热门文档")


class DocumentBatchDeleteRequest(BaseSchema):
    """批量删除文档请求模式"""
    document_ids: List[int] = Field(..., description="文档ID列表")
    permanent: bool = Field(False, description="是否永久删除")


class DocumentBatchDeleteResponse(BaseSchema):
    """批量删除文档响应模式"""
    success_count: int = Field(..., description="成功删除数量")
    failed_count: int = Field(..., description="删除失败数量")
    failed_documents: List[Dict[str, Any]] = Field(..., description="删除失败的文档信息")
    message: str = Field(..., description="操作结果消息")


# 通用响应模式
class MessageResponse(BaseSchema):
    """消息响应模式"""
    message: str = Field(..., description="响应消息")
    success: bool = Field(True, description="是否成功")
    data: Optional[Dict[str, Any]] = Field(None, description="附加数据")


class ErrorResponse(BaseSchema):
    """错误响应模式"""
    error: str = Field(..., description="错误信息")
    detail: Optional[str] = Field(None, description="详细信息")
    code: Optional[str] = Field(None, description="错误代码")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="时间戳")