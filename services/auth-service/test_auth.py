#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
认证服务单元测试

测试认证服务的各项功能，包括用户注册、登录、权限验证、密码重置等。

作者: 系统
创建时间: 2025-01-09
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, MagicMock

from main import app, get_db
from models import Base, User, Role, Permission, UserStatus
from database import get_db

# 测试数据库配置
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """覆盖数据库依赖"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(scope="module")
def setup_database():
    """设置测试数据库"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    """创建数据库会话"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def sample_user(db_session):
    """创建测试用户"""
    user = User(
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        status=UserStatus.ACTIVE
    )
    user.set_password("testpassword123")
    user.email_verified = True
    
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_user(db_session):
    """创建管理员用户"""
    # 创建管理员角色和权限
    admin_permission = Permission(
        name="user.admin",
        description="用户管理权限",
        resource="user",
        action="admin"
    )
    db_session.add(admin_permission)
    
    admin_role = Role(
        name="admin",
        description="管理员角色"
    )
    admin_role.permissions.append(admin_permission)
    db_session.add(admin_role)
    
    # 创建管理员用户
    admin = User(
        username="admin",
        email="admin@example.com",
        full_name="Admin User",
        status=UserStatus.ACTIVE,
        is_superuser=True
    )
    admin.set_password("adminpassword123")
    admin.email_verified = True
    admin.roles.append(admin_role)
    
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin


class TestUserRegistration:
    """用户注册测试"""
    
    def test_register_success(self, setup_database):
        """测试成功注册"""
        user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "newpassword123",
            "full_name": "New User"
        }
        
        response = client.post("/auth/register", json=user_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert data["status"] == UserStatus.PENDING_VERIFICATION
        assert "id" in data
    
    def test_register_duplicate_username(self, setup_database, sample_user):
        """测试重复用户名注册"""
        user_data = {
            "username": "testuser",  # 已存在的用户名
            "email": "another@example.com",
            "password": "password123",
            "full_name": "Another User"
        }
        
        response = client.post("/auth/register", json=user_data)
        assert response.status_code == 400
        assert "用户名已存在" in response.json()["detail"]
    
    def test_register_duplicate_email(self, setup_database, sample_user):
        """测试重复邮箱注册"""
        user_data = {
            "username": "anotheruser",
            "email": "test@example.com",  # 已存在的邮箱
            "password": "password123",
            "full_name": "Another User"
        }
        
        response = client.post("/auth/register", json=user_data)
        assert response.status_code == 400
        assert "邮箱已存在" in response.json()["detail"]
    
    def test_register_invalid_password(self, setup_database):
        """测试无效密码注册"""
        user_data = {
            "username": "testuser2",
            "email": "test2@example.com",
            "password": "123",  # 密码太短
            "full_name": "Test User 2"
        }
        
        response = client.post("/auth/register", json=user_data)
        assert response.status_code == 422


class TestUserLogin:
    """用户登录测试"""
    
    def test_login_success(self, setup_database, sample_user):
        """测试成功登录"""
        login_data = {
            "username_or_email": "testuser",
            "password": "testpassword123"
        }
        
        response = client.post("/auth/login", json=login_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_with_email(self, setup_database, sample_user):
        """测试使用邮箱登录"""
        login_data = {
            "username_or_email": "test@example.com",
            "password": "testpassword123"
        }
        
        response = client.post("/auth/login", json=login_data)
        assert response.status_code == 200
    
    def test_login_wrong_password(self, setup_database, sample_user):
        """测试错误密码登录"""
        login_data = {
            "username_or_email": "testuser",
            "password": "wrongpassword"
        }
        
        response = client.post("/auth/login", json=login_data)
        assert response.status_code == 401
        assert "用户名或密码错误" in response.json()["detail"]
    
    def test_login_nonexistent_user(self, setup_database):
        """测试不存在用户登录"""
        login_data = {
            "username_or_email": "nonexistent",
            "password": "password123"
        }
        
        response = client.post("/auth/login", json=login_data)
        assert response.status_code == 401
        assert "用户名或密码错误" in response.json()["detail"]
    
    def test_login_account_lockout(self, setup_database, sample_user, db_session):
        """测试账户锁定机制"""
        login_data = {
            "username_or_email": "testuser",
            "password": "wrongpassword"
        }
        
        # 连续5次错误登录
        for i in range(5):
            response = client.post("/auth/login", json=login_data)
            if i < 4:
                assert response.status_code == 401
                assert f"还有 {4-i} 次尝试机会" in response.json()["detail"]
            else:
                assert response.status_code == 423
                assert "账户已被锁定" in response.json()["detail"]
        
        # 再次尝试登录应该被锁定
        response = client.post("/auth/login", json=login_data)
        assert response.status_code == 423


class TestEmailVerification:
    """邮箱验证测试"""
    
    @patch('main.send_verification_email_task')
    def test_send_verification_email(self, mock_send_email, setup_database):
        """测试发送验证邮件"""
        user_data = {
            "username": "verifyuser",
            "email": "verify@example.com",
            "password": "password123",
            "full_name": "Verify User"
        }
        
        response = client.post("/auth/register", json=user_data)
        assert response.status_code == 201
        
        # 验证是否调用了发送邮件函数
        mock_send_email.assert_called_once()
    
    def test_verify_email_success(self, setup_database, db_session):
        """测试成功验证邮箱"""
        # 创建待验证用户
        user = User(
            username="verifyuser",
            email="verify@example.com",
            full_name="Verify User",
            status=UserStatus.PENDING_VERIFICATION,
            email_verification_token="test_token"
        )
        user.set_password("password123")
        
        db_session.add(user)
        db_session.commit()
        
        # 验证邮箱
        response = client.post("/auth/verify-email", json={"token": "test_token"})
        assert response.status_code == 200
        assert "邮箱验证成功" in response.json()["message"]
        
        # 检查用户状态
        db_session.refresh(user)
        assert user.email_verified == True
        assert user.status == UserStatus.ACTIVE
    
    def test_verify_email_invalid_token(self, setup_database):
        """测试无效验证令牌"""
        response = client.post("/auth/verify-email", json={"token": "invalid_token"})
        assert response.status_code == 400
        assert "无效的验证令牌" in response.json()["detail"]


class TestPasswordReset:
    """密码重置测试"""
    
    @patch('main.send_password_reset_email_task')
    def test_request_password_reset(self, mock_send_email, setup_database, sample_user):
        """测试请求密码重置"""
        reset_data = {"email": "test@example.com"}
        
        response = client.post("/auth/password-reset", json=reset_data)
        assert response.status_code == 200
        assert "密码重置邮件已发送" in response.json()["message"]
        
        # 验证是否调用了发送邮件函数
        mock_send_email.assert_called_once()
    
    def test_password_reset_confirm(self, setup_database, sample_user, db_session):
        """测试确认密码重置"""
        # 设置重置令牌
        sample_user.password_reset_token = "reset_token"
        sample_user.password_reset_expires = datetime.utcnow() + timedelta(hours=1)
        db_session.commit()
        
        reset_data = {
            "token": "reset_token",
            "new_password": "newpassword123"
        }
        
        response = client.post("/auth/password-reset/confirm", json=reset_data)
        assert response.status_code == 200
        assert "密码重置成功" in response.json()["message"]
        
        # 验证密码已更改
        db_session.refresh(sample_user)
        assert sample_user.verify_password("newpassword123")
        assert sample_user.password_reset_token is None


class TestPermissions:
    """权限测试"""
    
    def test_get_user_permissions(self, setup_database, admin_user):
        """测试获取用户权限"""
        # 先登录获取token
        login_data = {
            "username_or_email": "admin",
            "password": "adminpassword123"
        }
        
        login_response = client.post("/auth/login", json=login_data)
        token = login_response.json()["access_token"]
        
        # 获取权限
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/auth/permissions", headers=headers)
        
        assert response.status_code == 200
        permissions = response.json()
        assert "user.admin" in permissions
    
    def test_admin_unlock_user(self, setup_database, admin_user, sample_user, db_session):
        """测试管理员解锁用户"""
        # 锁定用户
        sample_user.failed_login_attempts = 5
        sample_user.locked_until = datetime.utcnow() + timedelta(minutes=30)
        sample_user.status = UserStatus.LOCKED
        db_session.commit()
        
        # 管理员登录
        login_data = {
            "username_or_email": "admin",
            "password": "adminpassword123"
        }
        
        login_response = client.post("/auth/login", json=login_data)
        token = login_response.json()["access_token"]
        
        # 解锁用户
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post(f"/auth/admin/unlock-user?user_id={sample_user.id}", headers=headers)
        
        assert response.status_code == 200
        assert "已解锁" in response.json()["message"]
        
        # 验证用户已解锁
        db_session.refresh(sample_user)
        assert sample_user.failed_login_attempts == 0
        assert sample_user.locked_until is None
    
    def test_get_locked_users(self, setup_database, admin_user, sample_user, db_session):
        """测试获取被锁定用户列表"""
        # 锁定用户
        sample_user.failed_login_attempts = 5
        sample_user.locked_until = datetime.utcnow() + timedelta(minutes=30)
        db_session.commit()
        
        # 管理员登录
        login_data = {
            "username_or_email": "admin",
            "password": "adminpassword123"
        }
        
        login_response = client.post("/auth/login", json=login_data)
        token = login_response.json()["access_token"]
        
        # 获取锁定用户列表
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/auth/admin/locked-users", headers=headers)
        
        assert response.status_code == 200
        locked_users = response.json()
        assert len(locked_users) > 0
        assert any(user["id"] == sample_user.id for user in locked_users)


class TestTokens:
    """令牌测试"""
    
    def test_refresh_token(self, setup_database, sample_user):
        """测试刷新令牌"""
        # 先登录获取token
        login_data = {
            "username_or_email": "testuser",
            "password": "testpassword123"
        }
        
        login_response = client.post("/auth/login", json=login_data)
        refresh_token = login_response.json()["refresh_token"]
        
        # 刷新令牌
        refresh_data = {"refresh_token": refresh_token}
        response = client.post("/auth/refresh", json=refresh_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
    
    def test_get_current_user(self, setup_database, sample_user):
        """测试获取当前用户信息"""
        # 先登录获取token
        login_data = {
            "username_or_email": "testuser",
            "password": "testpassword123"
        }
        
        login_response = client.post("/auth/login", json=login_data)
        token = login_response.json()["access_token"]
        
        # 获取用户信息
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/auth/me", headers=headers)
        
        assert response.status_code == 200
        user_data = response.json()
        assert user_data["username"] == "testuser"
        assert user_data["email"] == "test@example.com"


if __name__ == "__main__":
    pytest.main(["-v", __file__])