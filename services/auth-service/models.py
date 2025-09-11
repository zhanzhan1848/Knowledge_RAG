#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
认证服务数据模型

定义用户、角色和权限相关的数据模型，包括数据库表结构和Pydantic模型。

作者: 系统
创建时间: 2025-01-09
"""

from datetime import datetime, timedelta
from typing import Optional, List
from enum import Enum

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from pydantic import BaseModel, EmailStr, validator
import bcrypt

Base = declarative_base()

# 用户角色关联表
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True)
)

# 角色权限关联表
role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.id'), primary_key=True)
)


class UserStatus(str, Enum):
    """用户状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    LOCKED = "locked"
    PENDING_VERIFICATION = "pending_verification"


class User(Base):
    """用户数据模型"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100))
    status = Column(String(20), default=UserStatus.PENDING_VERIFICATION)
    is_superuser = Column(Boolean, default=False)
    
    # 认证相关字段
    email_verified = Column(Boolean, default=False)
    email_verification_token = Column(String(255))
    password_reset_token = Column(String(255))
    password_reset_expires = Column(DateTime)
    
    # 安全相关字段
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime)
    last_failed_login = Column(DateTime)
    last_login = Column(DateTime)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    roles = relationship("Role", secondary=user_roles, back_populates="users")
    
    def set_password(self, password: str) -> None:
        """设置密码哈希"""
        salt = bcrypt.gensalt()
        self.hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def verify_password(self, password: str) -> bool:
        """验证密码"""
        return bcrypt.checkpw(password.encode('utf-8'), self.hashed_password.encode('utf-8'))
    
    def is_locked(self) -> bool:
        """检查账户是否被锁定"""
        if self.locked_until and self.locked_until > datetime.utcnow():
            return True
        return self.status == UserStatus.LOCKED
    
    def record_failed_login(self) -> None:
        """记录失败登录"""
        self.failed_login_attempts += 1
        self.last_failed_login = datetime.utcnow()
        # 如果失败次数达到5次，锁定账户30分钟
        if self.failed_login_attempts >= 5:
            self.locked_until = datetime.utcnow() + timedelta(minutes=30)
            self.status = UserStatus.LOCKED
    
    def reset_failed_login(self) -> None:
        """重置失败登录次数"""
        self.failed_login_attempts = 0
        self.locked_until = None
        if self.status == UserStatus.LOCKED:
            self.status = UserStatus.ACTIVE


class Role(Base):
    """角色数据模型"""
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    users = relationship("User", secondary=user_roles, back_populates="roles")
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")


class Permission(Base):
    """权限数据模型"""
    __tablename__ = "permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    resource = Column(String(50))  # 资源类型，如 'document', 'user', 'system'
    action = Column(String(50))    # 操作类型，如 'read', 'write', 'delete', 'admin'
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")


# Pydantic 模型用于API请求和响应

class UserBase(BaseModel):
    """用户基础模型"""
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    
    @validator('username')
    def username_alphanumeric(cls, v):
        assert v.isalnum(), '用户名只能包含字母和数字'
        assert len(v) >= 3, '用户名至少3个字符'
        return v


class UserCreate(UserBase):
    """用户创建模型"""
    password: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('密码至少8个字符')
        if not any(c.isupper() for c in v):
            raise ValueError('密码必须包含至少一个大写字母')
        if not any(c.islower() for c in v):
            raise ValueError('密码必须包含至少一个小写字母')
        if not any(c.isdigit() for c in v):
            raise ValueError('密码必须包含至少一个数字')
        return v


class UserUpdate(BaseModel):
    """
    用户更新请求模型
    """
    username: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None


class PasswordReset(BaseModel):
    """
    密码重置请求模型
    """
    email: str


class PasswordResetConfirm(BaseModel):
    """
    密码重置确认模型
    """
    token: str
    new_password: str = Field(..., min_length=8)


class RoleResponse(BaseModel):
    """
    角色响应模型
    """
    id: int
    name: str
    description: Optional[str] = None
    is_active: bool


class UserResponse(UserBase):
    """用户响应模型"""
    id: int
    status: UserStatus
    is_superuser: bool
    email_verified: bool
    last_login: Optional[datetime]
    created_at: datetime
    roles: List[str] = []
    
    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    """用户登录模型"""
    username: str
    password: str


class Token(BaseModel):
    """JWT令牌模型"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    """令牌数据模型"""
    user_id: Optional[int] = None
    username: Optional[str] = None
    permissions: List[str] = []


class PasswordReset(BaseModel):
    """密码重置模型"""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """密码重置确认模型"""
    token: str
    new_password: str
    
    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('密码至少8个字符')
        if not any(c.isupper() for c in v):
            raise ValueError('密码必须包含至少一个大写字母')
        if not any(c.islower() for c in v):
            raise ValueError('密码必须包含至少一个小写字母')
        if not any(c.isdigit() for c in v):
            raise ValueError('密码必须包含至少一个数字')
        return v


class EmailVerification(BaseModel):
    """邮箱验证模型"""
    token: str


class RoleCreate(BaseModel):
    """角色创建模型"""
    name: str
    description: Optional[str] = None


class RoleResponse(BaseModel):
    """角色响应模型"""
    id: int
    name: str
    description: Optional[str]
    is_active: bool
    
    class Config:
        from_attributes = True


class PermissionResponse(BaseModel):
    """权限响应模型"""
    id: int
    name: str
    description: Optional[str]
    resource: Optional[str]
    action: Optional[str]
    
    class Config:
        from_attributes = True