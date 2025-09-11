#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
认证中间件模块

提供JWT认证中间件和权限验证中间件，用于保护API端点。

作者: Knowledge RAG Team
创建时间: 2024
"""

import jwt
from fastapi import HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional, List, Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from database import get_db
from models import User
from config import get_config

config = get_config()
security = HTTPBearer()


class AuthMiddleware(BaseHTTPMiddleware):
    """
    JWT认证中间件
    
    自动验证请求中的JWT令牌，并将用户信息添加到请求状态中。
    """
    
    def __init__(self, app, exclude_paths: Optional[List[str]] = None):
        """
        初始化认证中间件
        
        Args:
            app: FastAPI应用实例
            exclude_paths: 不需要认证的路径列表
        """
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/auth/register",
            "/auth/login",
            "/auth/refresh",
            "/auth/password-reset",
            "/auth/password-reset/confirm",
            "/auth/verify-email"
        ]
    
    async def dispatch(self, request: Request, call_next: Callable):
        """
        处理请求
        
        Args:
            request: HTTP请求
            call_next: 下一个中间件或路由处理器
            
        Returns:
            Response: HTTP响应
        """
        # 检查是否为排除路径
        if request.url.path in self.exclude_paths:
            return await call_next(request)
        
        # 获取Authorization头
        authorization = request.headers.get("Authorization")
        if not authorization:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "缺少认证令牌"}
            )
        
        # 验证Bearer格式
        if not authorization.startswith("Bearer "):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "无效的认证格式"}
            )
        
        token = authorization.split(" ")[1]
        
        try:
            # 验证JWT令牌
            payload = jwt.decode(
                token, 
                config.jwt_secret_key, 
                algorithms=[config.jwt_algorithm]
            )
            user_id = payload.get("sub")
            
            if not user_id:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "无效的令牌"}
                )
            
            # 获取用户信息
            db = next(get_db())
            user = db.query(User).filter(User.id == user_id).first()
            
            if not user:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "用户不存在"}
                )
            
            if user.status != "active":
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "用户账户已被禁用"}
                )
            
            # 将用户信息添加到请求状态
            request.state.user = user
            request.state.user_id = user_id
            
        except jwt.ExpiredSignatureError:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "令牌已过期"}
            )
        except jwt.InvalidTokenError:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "无效的令牌"}
            )
        except Exception as e:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "认证服务错误"}
            )
        
        return await call_next(request)


class PermissionMiddleware(BaseHTTPMiddleware):
    """
    权限验证中间件
    
    基于用户角色和权限验证API访问权限。
    """
    
    def __init__(self, app, permission_map: Optional[dict] = None):
        """
        初始化权限中间件
        
        Args:
            app: FastAPI应用实例
            permission_map: 路径权限映射字典
        """
        super().__init__(app)
        self.permission_map = permission_map or {
            "/auth/roles": "user.admin",
            "/auth/users": "user.admin",
            "/auth/permissions": "user.read"
        }
    
    async def dispatch(self, request: Request, call_next: Callable):
        """
        处理请求权限验证
        
        Args:
            request: HTTP请求
            call_next: 下一个中间件或路由处理器
            
        Returns:
            Response: HTTP响应
        """
        # 检查是否需要权限验证
        required_permission = self.permission_map.get(request.url.path)
        
        if not required_permission:
            return await call_next(request)
        
        # 检查用户是否已认证
        if not hasattr(request.state, "user"):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "需要认证"}
            )
        
        user = request.state.user
        
        # 超级用户拥有所有权限
        if user.is_superuser:
            return await call_next(request)
        
        # 获取用户权限
        user_permissions = self._get_user_permissions(user)
        
        if required_permission not in user_permissions:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": f"需要权限: {required_permission}"}
            )
        
        return await call_next(request)
    
    def _get_user_permissions(self, user: User) -> List[str]:
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


def get_current_user_from_request(request: Request) -> Optional[User]:
    """
    从请求中获取当前用户
    
    Args:
        request: HTTP请求对象
        
    Returns:
        Optional[User]: 用户对象，如果未认证则返回None
    """
    return getattr(request.state, "user", None)


def require_auth(request: Request) -> User:
    """
    要求用户认证
    
    Args:
        request: HTTP请求对象
        
    Returns:
        User: 当前用户对象
        
    Raises:
        HTTPException: 如果用户未认证
    """
    user = get_current_user_from_request(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="需要认证"
        )
    return user


def require_permission(permission: str):
    """
    权限验证装饰器
    
    Args:
        permission: 所需权限
        
    Returns:
        function: 装饰器函数
    """
    def decorator(func):
        def wrapper(request: Request, *args, **kwargs):
            user = require_auth(request)
            
            # 超级用户拥有所有权限
            if user.is_superuser:
                return func(request, *args, **kwargs)
            
            # 获取用户权限
            user_permissions = []
            for user_role in user.roles:
                role = user_role.role
                if role.is_active:
                    for role_permission in role.permissions:
                        perm = role_permission.permission
                        if perm.is_active:
                            user_permissions.append(perm.name)
            
            if permission not in user_permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"需要权限: {permission}"
                )
            
            return func(request, *args, **kwargs)
        return wrapper
    return decorator