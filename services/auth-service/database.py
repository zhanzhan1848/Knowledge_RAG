#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
认证服务数据库配置

提供数据库连接、会话管理和初始化功能。

作者: 系统
创建时间: 2025-01-09
"""

import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from models import Base, User, Role, Permission, user_roles, role_permissions

# 数据库配置
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres:password@localhost:5432/knowledge_rag_auth"
)

# 创建数据库引擎
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=os.getenv("DEBUG", "false").lower() == "true"
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    获取数据库会话
    
    Yields:
        Session: 数据库会话对象
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """
    创建数据库表
    """
    Base.metadata.create_all(bind=engine)


def init_default_data(db: Session):
    """
    初始化默认数据
    
    Args:
        db: 数据库会话
    """
    # 创建默认权限
    default_permissions = [
        # 文档权限
        {"name": "document.read", "description": "读取文档", "resource": "document", "action": "read"},
        {"name": "document.write", "description": "创建和编辑文档", "resource": "document", "action": "write"},
        {"name": "document.delete", "description": "删除文档", "resource": "document", "action": "delete"},
        {"name": "document.admin", "description": "文档管理", "resource": "document", "action": "admin"},
        
        # 用户权限
        {"name": "user.read", "description": "查看用户信息", "resource": "user", "action": "read"},
        {"name": "user.write", "description": "编辑用户信息", "resource": "user", "action": "write"},
        {"name": "user.delete", "description": "删除用户", "resource": "user", "action": "delete"},
        {"name": "user.admin", "description": "用户管理", "resource": "user", "action": "admin"},
        
        # 系统权限
        {"name": "system.read", "description": "查看系统信息", "resource": "system", "action": "read"},
        {"name": "system.admin", "description": "系统管理", "resource": "system", "action": "admin"},
        
        # QA权限
        {"name": "qa.read", "description": "查看问答", "resource": "qa", "action": "read"},
        {"name": "qa.write", "description": "创建问答", "resource": "qa", "action": "write"},
        {"name": "qa.admin", "description": "问答管理", "resource": "qa", "action": "admin"},
    ]
    
    for perm_data in default_permissions:
        existing_perm = db.query(Permission).filter(
            Permission.name == perm_data["name"]
        ).first()
        if not existing_perm:
            permission = Permission(**perm_data)
            db.add(permission)
    
    # 创建默认角色
    default_roles = [
        {
            "name": "user",
            "description": "普通用户",
            "permissions": ["document.read", "document.write", "qa.read", "qa.write", "user.read"]
        },
        {
            "name": "admin",
            "description": "管理员",
            "permissions": [
                "document.read", "document.write", "document.delete", "document.admin",
                "user.read", "user.write", "user.delete", "user.admin",
                "qa.read", "qa.write", "qa.admin",
                "system.read", "system.admin"
            ]
        },
        {
            "name": "viewer",
            "description": "只读用户",
            "permissions": ["document.read", "qa.read", "user.read"]
        }
    ]
    
    for role_data in default_roles:
        existing_role = db.query(Role).filter(
            Role.name == role_data["name"]
        ).first()
        if not existing_role:
            role = Role(
                name=role_data["name"],
                description=role_data["description"]
            )
            
            # 添加权限
            for perm_name in role_data["permissions"]:
                permission = db.query(Permission).filter(
                    Permission.name == perm_name
                ).first()
                if permission:
                    role.permissions.append(permission)
            
            db.add(role)
    
    # 创建默认管理员用户
    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com")
    admin_password = os.getenv("ADMIN_PASSWORD", "Admin123456")
    
    existing_admin = db.query(User).filter(
        User.username == admin_username
    ).first()
    
    if not existing_admin:
        admin_user = User(
            username=admin_username,
            email=admin_email,
            full_name="系统管理员",
            status="active",
            is_superuser=True,
            email_verified=True
        )
        admin_user.set_password(admin_password)
        
        # 添加管理员角色
        admin_role = db.query(Role).filter(Role.name == "admin").first()
        if admin_role:
            admin_user.roles.append(admin_role)
        
        db.add(admin_user)
    
    db.commit()


def init_database():
    """
    初始化数据库
    """
    # 创建表
    create_tables()
    
    # 初始化默认数据
    db = SessionLocal()
    try:
        init_default_data(db)
        print("数据库初始化完成")
    except Exception as e:
        print(f"数据库初始化失败: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init_database()