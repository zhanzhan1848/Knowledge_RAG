#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
认证服务主应用

提供用户认证、授权、注册、登录等功能的FastAPI应用。

作者: 系统
创建时间: 2025-01-09
"""

import os
import secrets
import uuid
from datetime import datetime, timedelta
from typing import List, Optional
from functools import wraps

from fastapi import FastAPI, HTTPException, Depends, status, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import or_
import jwt
from passlib.context import CryptContext

from database import get_db, init_database
from models import (
    User, Role, Permission, UserStatus,
    UserCreate, UserLogin, UserResponse, UserUpdate,
    Token, TokenData, PasswordReset, PasswordResetConfirm,
    EmailVerification, RoleResponse, PermissionResponse
)

# 应用配置
app = FastAPI(
    title="认证服务",
    description="Knowledge RAG 系统认证和授权服务",
    version="1.0.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# JWT配置
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
JWT_REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# 密码加密配置
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer认证
security = HTTPBearer()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建访问令牌
    
    Args:
        data: 令牌数据
        expires_delta: 过期时间增量
        
    Returns:
        str: JWT令牌
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """
    创建刷新令牌
    
    Args:
        data: 令牌数据
        
    Returns:
        str: JWT刷新令牌
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> TokenData:
    """
    验证JWT令牌
    
    Args:
        token: JWT令牌
        
    Returns:
        TokenData: 令牌数据
        
    Raises:
        HTTPException: 令牌无效时抛出异常
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id: int = payload.get("sub")
        username: str = payload.get("username")
        permissions: List[str] = payload.get("permissions", [])
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的令牌",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        token_data = TokenData(
            user_id=user_id,
            username=username,
            permissions=permissions
        )
        return token_data
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)) -> User:
    """
    获取当前用户
    
    Args:
        credentials: HTTP认证凭据
        db: 数据库会话
        
    Returns:
        User: 当前用户对象
        
    Raises:
        HTTPException: 认证失败时抛出异常
    """
    token_data = verify_token(credentials.credentials)
    user = db.query(User).filter(User.id == token_data.user_id).first()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="账户未激活或已被锁定",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


def get_user_permissions(user: User) -> List[str]:
    """
    获取用户权限列表
    
    Args:
        user: 用户对象
        
    Returns:
        List[str]: 权限列表
    """
    permissions = set()
    
    for user_role in user.roles:
        role = user_role.role
        if role.is_active:
            for role_permission in role.permissions:
                permission = role_permission.permission
                if permission.is_active:
                    permissions.add(permission.name)
    
    return list(permissions)


def require_permission(permission_name: str):
    """
    权限验证装饰器
    
    Args:
        permission_name: 所需权限名称
        
    Returns:
        function: 装饰器函数
    """
    def decorator(func):
        @wraps(func)
        def wrapper(current_user: User = Depends(get_current_user), *args, **kwargs):
            user_permissions = get_user_permissions(current_user)
            if permission_name not in user_permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="权限不足"
                )
            return func(current_user=current_user, *args, **kwargs)
        return wrapper
    return decorator





@app.on_event("startup")
async def startup_event():
    """
    应用启动事件
    """
    try:
        init_database()
        print("认证服务启动成功")
    except Exception as e:
        print(f"认证服务启动失败: {e}")
        raise


@app.get("/health")
async def health_check():
    """
    健康检查端点
    
    Returns:
        dict: 健康状态
    """
    return {"status": "healthy", "service": "auth-service"}


@app.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    用户注册
    
    Args:
        user_data: 用户注册数据
        background_tasks: 后台任务
        db: 数据库会话
        
    Returns:
        UserResponse: 注册成功的用户信息
        
    Raises:
        HTTPException: 注册失败时抛出异常
    """
    # 检查用户名是否已存在
    existing_user = db.query(User).filter(
        or_(User.username == user_data.username, User.email == user_data.email)
    ).first()
    
    if existing_user:
        if existing_user.username == user_data.username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被注册"
            )
    
    # 创建新用户
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        status=UserStatus.PENDING_VERIFICATION,
        email_verification_token=str(uuid.uuid4())
    )
    new_user.set_password(user_data.password)
    
    # 添加默认用户角色
    default_role = db.query(Role).filter(Role.name == "user").first()
    if default_role:
        new_user.roles.append(default_role)
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # 发送邮箱验证邮件（后台任务）
    background_tasks.add_task(
        send_verification_email_task,
        new_user.email,
        new_user.username,
        new_user.email_verification_token
    )
    
    # 构建响应
    response = UserResponse(
        id=new_user.id,
        username=new_user.username,
        email=new_user.email,
        full_name=new_user.full_name,
        status=new_user.status,
        is_superuser=new_user.is_superuser,
        email_verified=new_user.email_verified,
        last_login=new_user.last_login,
        created_at=new_user.created_at,
        roles=[role.name for role in new_user.roles]
    )
    
    return response


@app.post("/auth/login", response_model=Token)
async def login_user(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """
    用户登录
    
    Args:
        user_credentials: 用户登录凭据
        db: 数据库会话
        
    Returns:
        Token: JWT令牌
        
    Raises:
        HTTPException: 登录失败时抛出异常
    """
    # 查找用户
    user = db.query(User).filter(
        or_(
            User.username == user_credentials.username,
            User.email == user_credentials.username
        )
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    
    # 检查账户是否被锁定
    if user.is_locked():
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=f"账户已被锁定，请在 {user.locked_until.strftime('%Y-%m-%d %H:%M:%S')} 后重试或联系管理员"
        )
    
    # 验证密码
    if not user.verify_password(user_credentials.password):
        # 记录失败登录
        user.record_failed_login()
        db.commit()
        
        # 检查是否需要锁定账户
        if user.is_locked():
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail=f"登录失败次数过多，账户已被锁定至 {user.locked_until.strftime('%Y-%m-%d %H:%M:%S')}"
            )
        
        remaining_attempts = 5 - user.failed_login_attempts
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"用户名或密码错误，还有 {remaining_attempts} 次尝试机会"
        )
    
    # 检查账户状态
    if user.status != UserStatus.ACTIVE:
        if user.status == UserStatus.PENDING_VERIFICATION:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="请先验证邮箱"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="账户未激活"
            )
    
    # 登录成功，重置失败计数
    user.reset_failed_login()
    user.last_login = datetime.utcnow()
    db.commit()
    
    # 获取用户权限
    permissions = get_user_permissions(user)
    
    # 创建令牌
    access_token_expires = timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user.id,
            "username": user.username,
            "permissions": permissions
        },
        expires_delta=access_token_expires
    )
    
    refresh_token = create_refresh_token(
        data={"sub": user.id, "username": user.username}
    )
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@app.post("/auth/refresh", response_model=Token)
async def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    """
    刷新访问令牌
    
    Args:
        refresh_token: 刷新令牌
        db: 数据库会话
        
    Returns:
        Token: 新的JWT令牌
        
    Raises:
        HTTPException: 刷新失败时抛出异常
    """
    try:
        payload = jwt.decode(refresh_token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id: int = payload.get("sub")
        token_type: str = payload.get("type")
        
        if token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的刷新令牌"
            )
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user or user.status != UserStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在或未激活"
            )
        
        # 获取用户权限
        permissions = get_user_permissions(user)
        
        # 创建新的访问令牌
        access_token_expires = timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={
                "sub": user.id,
                "username": user.username,
                "permissions": permissions
            },
            expires_delta=access_token_expires
        )
        
        # 创建新的刷新令牌
        new_refresh_token = create_refresh_token(
            data={"sub": user.id, "username": user.username}
        )
        
        return Token(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的刷新令牌"
        )


@app.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    获取当前用户信息
    
    Args:
        current_user: 当前用户
        
    Returns:
        UserResponse: 用户信息
    """
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        status=current_user.status,
        is_superuser=current_user.is_superuser,
        email_verified=current_user.email_verified,
        last_login=current_user.last_login,
        created_at=current_user.created_at,
        roles=[role.name for role in current_user.roles]
    )


@app.put("/auth/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新当前用户信息
    
    Args:
        user_update: 用户更新数据
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        UserResponse: 更新后的用户信息
    """
    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name
    
    if user_update.email is not None:
        # 检查邮箱是否已被其他用户使用
        existing_user = db.query(User).filter(
            User.email == user_update.email,
            User.id != current_user.id
        ).first()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被其他用户使用"
            )
        
        current_user.email = user_update.email
        current_user.email_verified = False  # 需要重新验证邮箱
    
    current_user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(current_user)
    
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        status=current_user.status,
        is_superuser=current_user.is_superuser,
        email_verified=current_user.email_verified,
        last_login=current_user.last_login,
        created_at=current_user.created_at,
        roles=[role.name for role in current_user.roles]
    )


@app.post("/auth/logout")
async def logout_user(current_user: User = Depends(get_current_user)):
    """
    用户登出
    
    Args:
        current_user: 当前用户
        
    Returns:
        dict: 登出成功消息
    
    Note:
        在无状态JWT系统中，登出主要是客户端删除令牌
        服务端可以维护黑名单来实现真正的令牌失效
    """
    # TODO: 可以将令牌加入黑名单（需要Redis支持）
    return {"message": "登出成功"}


@app.post("/auth/verify-email")
async def verify_email(
    verification_data: EmailVerification,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    验证邮箱
    
    Args:
        verification_data: 邮箱验证数据
        background_tasks: 后台任务
        db: 数据库会话
        
    Returns:
        dict: 验证结果
        
    Raises:
        HTTPException: 验证失败时抛出异常
    """
    user = db.query(User).filter(
        User.email_verification_token == verification_data.token
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的验证令牌"
        )
    
    # 验证邮箱
    user.is_email_verified = True
    user.email_verification_token = None
    user.updated_at = datetime.utcnow()
    
    db.commit()
    
    # 发送欢迎邮件
    background_tasks.add_task(
        send_welcome_email_task,
        user.email,
        user.username
    )
    
    return {"message": "邮箱验证成功"}


@app.post("/auth/resend-verification")
async def resend_verification_email(
    email: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    重新发送验证邮件
    
    Args:
        email: 邮箱地址
        background_tasks: 后台任务
        db: 数据库会话
        
    Returns:
        dict: 发送结果
        
    Raises:
        HTTPException: 发送失败时抛出异常
    """
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    if user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已验证"
        )
    
    # 生成新的验证令牌
    user.email_verification_token = str(uuid.uuid4())
    user.updated_at = datetime.utcnow()
    db.commit()
    
    # 发送验证邮件
    background_tasks.add_task(
        send_verification_email_task,
        user.email,
        user.username,
        user.email_verification_token
    )
    
    return {"message": "验证邮件已发送"}


@app.post("/auth/password-reset")
async def request_password_reset(
    reset_data: PasswordReset,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    请求密码重置
    
    Args:
        reset_data: 密码重置请求数据
        background_tasks: 后台任务
        db: 数据库会话
        
    Returns:
        dict: 请求结果
    """
    user = db.query(User).filter(User.email == reset_data.email).first()
    
    if not user:
        # 为了安全，即使用户不存在也返回成功消息
        return {"message": "如果邮箱存在，重置链接已发送"}
    
    # 生成密码重置令牌
    reset_token = str(uuid.uuid4())
    user.password_reset_token = reset_token
    user.password_reset_expires = datetime.utcnow() + timedelta(hours=1)  # 1小时有效期
    user.updated_at = datetime.utcnow()
    
    db.commit()
    
    # 发送密码重置邮件
    background_tasks.add_task(
        send_password_reset_email_task,
        user.email,
        user.username,
        reset_token
    )
    
    return {"message": "如果邮箱存在，重置链接已发送"}


@app.post("/auth/password-reset/confirm")
async def confirm_password_reset(
    reset_data: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """
    确认密码重置
    
    Args:
        reset_data: 密码重置确认数据
        db: 数据库会话
        
    Returns:
        dict: 重置结果
        
    Raises:
        HTTPException: 重置失败时抛出异常
    """
    user = db.query(User).filter(
        User.password_reset_token == reset_data.token
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的重置令牌"
        )
    
    # 检查令牌是否过期
    if user.password_reset_expires < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="重置令牌已过期"
        )
    
    # 更新密码
    user.set_password(reset_data.new_password)
    user.password_reset_token = None
    user.password_reset_expires = None
    user.updated_at = datetime.utcnow()
    
    # 重置失败登录次数
    user.reset_failed_login()
    
    db.commit()
    
    return {"message": "密码重置成功"}


@app.get("/auth/permissions", response_model=List[str])
async def get_user_permissions_endpoint(current_user: User = Depends(get_current_user)):
    """
    获取当前用户权限列表
    
    Args:
        current_user: 当前用户
        
    Returns:
        List[str]: 权限列表
    """
    return get_user_permissions(current_user)


@app.get("/auth/roles", response_model=List[RoleResponse])
async def get_all_roles(
    current_user: User = Depends(require_permission("user.admin")),
    db: Session = Depends(get_db)
):
    """
    获取所有角色（需要管理员权限）
    
    Args:
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        List[RoleResponse]: 角色列表
    """
    roles = db.query(Role).all()
    return [RoleResponse(
        id=role.id,
        name=role.name,
        description=role.description,
        is_active=role.is_active
    ) for role in roles]


@app.post("/auth/admin/unlock-user")
async def unlock_user(
    user_id: int,
    current_user: User = Depends(require_permission("user.admin")),
    db: Session = Depends(get_db)
):
    """
    解锁用户账户（需要管理员权限）
    
    Args:
        user_id: 用户ID
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        dict: 操作结果
        
    Raises:
        HTTPException: 用户不存在时抛出异常
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 解锁用户
    user.reset_failed_login()
    user.updated_at = datetime.utcnow()
    
    db.commit()
    
    return {
        "message": f"用户 {user.username} 已解锁",
        "user_id": user.id,
        "username": user.username
    }


@app.get("/auth/admin/locked-users")
async def get_locked_users(
    current_user: User = Depends(require_permission("user.admin")),
    db: Session = Depends(get_db)
):
    """
    获取被锁定的用户列表（需要管理员权限）
    
    Args:
        current_user: 当前用户
        db: 数据库会话
        
    Returns:
        List[dict]: 被锁定的用户列表
    """
    locked_users = db.query(User).filter(
        User.locked_until > datetime.utcnow()
    ).all()
    
    return [
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "failed_login_attempts": user.failed_login_attempts,
            "locked_until": user.locked_until.isoformat() if user.locked_until else None,
            "last_failed_login": user.last_failed_login.isoformat() if user.last_failed_login else None
        }
        for user in locked_users
    ]


async def send_verification_email_task(email: str, username: str, token: str):
    """
    发送验证邮件（后台任务）
    
    Args:
        email: 用户邮箱
        username: 用户名
        token: 验证令牌
    """
    from email_service import send_verification_email
    try:
        success = await send_verification_email(email, username, token)
        if success:
            print(f"验证邮件发送成功: {email}")
        else:
            print(f"验证邮件发送失败: {email}")
    except Exception as e:
        print(f"发送验证邮件时出错: {e}")


async def send_password_reset_email_task(email: str, username: str, token: str):
    """
    发送密码重置邮件（后台任务）
    
    Args:
        email: 用户邮箱
        username: 用户名
        token: 重置令牌
    """
    from email_service import send_password_reset_email
    try:
        success = await send_password_reset_email(email, username, token)
        if success:
            print(f"密码重置邮件发送成功: {email}")
        else:
            print(f"密码重置邮件发送失败: {email}")
    except Exception as e:
        print(f"发送密码重置邮件时出错: {e}")


async def send_welcome_email_task(email: str, username: str):
    """
    发送欢迎邮件（后台任务）
    
    Args:
        email: 用户邮箱
        username: 用户名
    """
    from email_service import send_welcome_email
    try:
        success = await send_welcome_email(email, username)
        if success:
            print(f"欢迎邮件发送成功: {email}")
        else:
            print(f"欢迎邮件发送失败: {email}")
    except Exception as e:
        print(f"发送欢迎邮件时出错: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True
    )