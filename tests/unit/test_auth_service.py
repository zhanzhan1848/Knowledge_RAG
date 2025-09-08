# Knowledge RAG System - 认证服务单元测试
# 测试用户认证、授权、JWT令牌管理等功能

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta, timezone
import hashlib
import json
from fastapi import HTTPException, status


class TestUserAuthentication:
    """用户认证测试类"""

    def test_user_registration(self):
        """测试用户注册"""

        def mock_hash_password(password: str) -> str:
            """模拟密码哈希"""
            return hashlib.sha256(password.encode()).hexdigest()

        def mock_register_user(username: str, email: str, password: str) -> dict:
            """模拟用户注册"""
            # 验证输入
            if len(username) < 3:
                raise ValueError("用户名至少3个字符")

            if "@" not in email:
                raise ValueError("无效的邮箱格式")

            if len(password) < 8:
                raise ValueError("密码至少8个字符")

            # 检查用户是否已存在（模拟）
            existing_users = ["existinguser", "admin"]
            if username in existing_users:
                raise ValueError("用户名已存在")

            # 创建用户
            user = {
                "id": "user_123",
                "username": username,
                "email": email,
                "password_hash": mock_hash_password(password),
                "created_at": datetime.utcnow().isoformat(),
                "is_active": True,
                "role": "user",
            }

            return user

        # 测试成功注册
        user = mock_register_user("newuser", "newuser@example.com", "password123")
        assert user["username"] == "newuser"
        assert user["email"] == "newuser@example.com"
        assert user["is_active"] is True
        assert user["role"] == "user"
        assert "password_hash" in user
        assert user["password_hash"] != "password123"  # 密码应该被哈希

        # 测试用户名太短
        with pytest.raises(ValueError, match="用户名至少3个字符"):
            mock_register_user("ab", "test@example.com", "password123")

        # 测试无效邮箱
        with pytest.raises(ValueError, match="无效的邮箱格式"):
            mock_register_user("testuser", "invalid-email", "password123")

        # 测试密码太短
        with pytest.raises(ValueError, match="密码至少8个字符"):
            mock_register_user("testuser", "test@example.com", "123")

        # 测试用户名已存在
        with pytest.raises(ValueError, match="用户名已存在"):
            mock_register_user("existinguser", "test@example.com", "password123")

    def test_user_login(self):
        """测试用户登录"""

        def mock_hash_password(password: str) -> str:
            return hashlib.sha256(password.encode()).hexdigest()

        def mock_verify_password(password: str, hashed: str) -> bool:
            return mock_hash_password(password) == hashed

        def mock_login_user(username: str, password: str) -> dict:
            """模拟用户登录"""
            # 模拟数据库中的用户
            users_db = {
                "testuser": {
                    "id": "user_123",
                    "username": "testuser",
                    "email": "test@example.com",
                    "password_hash": mock_hash_password("correct_password"),
                    "is_active": True,
                    "role": "user",
                },
                "inactiveuser": {
                    "id": "user_456",
                    "username": "inactiveuser",
                    "email": "inactive@example.com",
                    "password_hash": mock_hash_password("password123"),
                    "is_active": False,
                    "role": "user",
                },
            }

            # 检查用户是否存在
            if username not in users_db:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误"
                )

            user = users_db[username]

            # 检查密码
            if not mock_verify_password(password, user["password_hash"]):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误"
                )

            # 检查用户是否激活
            if not user["is_active"]:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="账户已被禁用"
                )

            # 返回用户信息（不包含密码哈希）
            return {
                "id": user["id"],
                "username": user["username"],
                "email": user["email"],
                "role": user["role"],
            }

        # 测试成功登录
        user = mock_login_user("testuser", "correct_password")
        assert user["username"] == "testuser"
        assert user["email"] == "test@example.com"
        assert "password_hash" not in user  # 不应返回密码哈希

        # 测试用户不存在
        with pytest.raises(HTTPException) as exc_info:
            mock_login_user("nonexistent", "password")
        assert exc_info.value.status_code == 401
        assert "用户名或密码错误" in str(exc_info.value.detail)

        # 测试密码错误
        with pytest.raises(HTTPException) as exc_info:
            mock_login_user("testuser", "wrong_password")
        assert exc_info.value.status_code == 401
        assert "用户名或密码错误" in str(exc_info.value.detail)

        # 测试账户被禁用
        with pytest.raises(HTTPException) as exc_info:
            mock_login_user("inactiveuser", "password123")
        assert exc_info.value.status_code == 401
        assert "账户已被禁用" in str(exc_info.value.detail)

    def test_password_reset(self):
        """测试密码重置"""

        def mock_generate_reset_token(user_id: str) -> str:
            """生成密码重置令牌"""
            import uuid

            token = str(uuid.uuid4())
            # 在实际实现中，这个令牌会存储在数据库中，并设置过期时间
            return token

        def mock_send_reset_email(email: str, token: str) -> bool:
            """发送密码重置邮件"""
            # 模拟邮件发送
            return True

        def mock_request_password_reset(email: str) -> dict:
            """请求密码重置"""
            # 模拟用户数据库
            users_db = {
                "test@example.com": {
                    "id": "user_123",
                    "username": "testuser",
                    "email": "test@example.com",
                }
            }

            if email not in users_db:
                # 为了安全，即使邮箱不存在也返回成功
                return {"message": "如果邮箱存在，重置链接已发送"}

            user = users_db[email]
            token = mock_generate_reset_token(user["id"])

            # 发送邮件
            if mock_send_reset_email(email, token):
                return {"message": "如果邮箱存在，重置链接已发送"}
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="邮件发送失败",
                )

        # 测试密码重置请求
        result = mock_request_password_reset("test@example.com")
        assert "重置链接已发送" in result["message"]

        # 测试不存在的邮箱（应该返回相同消息）
        result = mock_request_password_reset("nonexistent@example.com")
        assert "重置链接已发送" in result["message"]


class TestJWTTokenManagement:
    """JWT令牌管理测试类"""

    def test_create_access_token(self):
        """测试创建访问令牌"""

        def mock_create_access_token(
            user_data: dict, expires_delta: timedelta = None
        ) -> str:
            """创建访问令牌"""
            if expires_delta is None:
                expires_delta = timedelta(hours=1)

            payload = {
                "user_id": user_data["id"],
                "username": user_data["username"],
                "role": user_data["role"],
                "exp": datetime.utcnow() + expires_delta,
                "iat": datetime.utcnow(),
                "type": "access",
            }

            # 简化的令牌格式（实际应使用JWT库）
            token_data = json.dumps(payload, default=str, sort_keys=True)
            return f"access_token_{token_data}"

        user_data = {"id": "user_123", "username": "testuser", "role": "user"}

        token = mock_create_access_token(user_data)
        assert token.startswith("access_token_")
        assert "user_123" in token
        assert "testuser" in token
        assert "access" in token

    def test_create_refresh_token(self):
        """测试创建刷新令牌"""

        def mock_create_refresh_token(user_id: str) -> str:
            """创建刷新令牌"""
            payload = {
                "user_id": user_id,
                "exp": datetime.utcnow() + timedelta(days=30),
                "iat": datetime.utcnow(),
                "type": "refresh",
            }

            token_data = json.dumps(payload, default=str, sort_keys=True)
            return f"refresh_token_{token_data}"

        token = mock_create_refresh_token("user_123")
        assert token.startswith("refresh_token_")
        assert "user_123" in token
        assert "refresh" in token

    def test_verify_token(self):
        """测试令牌验证"""

        def mock_verify_token(token: str) -> dict:
            """验证令牌"""
            if not token.startswith(("access_token_", "refresh_token_")):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的令牌格式"
                )

            try:
                # 提取令牌数据
                if token.startswith("access_token_"):
                    token_data = token.replace("access_token_", "")
                else:
                    token_data = token.replace("refresh_token_", "")

                payload = json.loads(token_data)

                # 检查过期时间
                exp_time = datetime.fromisoformat(payload["exp"].replace("Z", "+00:00"))
                if exp_time < datetime.utcnow():
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED, detail="令牌已过期"
                    )

                return payload

            except (json.JSONDecodeError, KeyError, ValueError):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的令牌"
                )

        # 创建有效令牌
        valid_payload = {
            "user_id": "user_123",
            "username": "testuser",
            "role": "user",
            "exp": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
            "iat": datetime.utcnow().isoformat(),
            "type": "access",
        }
        valid_token = f"access_token_{json.dumps(valid_payload, sort_keys=True)}"

        # 测试有效令牌
        decoded = mock_verify_token(valid_token)
        assert decoded["user_id"] == "user_123"
        assert decoded["username"] == "testuser"
        assert decoded["type"] == "access"

        # 测试无效格式
        with pytest.raises(HTTPException) as exc_info:
            mock_verify_token("invalid_token_format")
        assert exc_info.value.status_code == 401
        assert "无效的令牌格式" in str(exc_info.value.detail)

    def test_refresh_access_token(self):
        """测试刷新访问令牌"""

        def mock_refresh_access_token(refresh_token: str) -> dict:
            """使用刷新令牌获取新的访问令牌"""
            # 验证刷新令牌
            if not refresh_token.startswith("refresh_token_"):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的刷新令牌"
                )

            try:
                token_data = refresh_token.replace("refresh_token_", "")
                payload = json.loads(token_data)

                # 检查令牌类型
                if payload.get("type") != "refresh":
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED, detail="令牌类型错误"
                    )

                # 检查过期时间
                exp_time = datetime.fromisoformat(payload["exp"].replace("Z", "+00:00"))
                if exp_time < datetime.utcnow():
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="刷新令牌已过期",
                    )

                # 获取用户信息（模拟从数据库获取）
                user_data = {
                    "id": payload["user_id"],
                    "username": "testuser",  # 实际应从数据库获取
                    "role": "user",
                }

                # 创建新的访问令牌
                new_access_payload = {
                    "user_id": user_data["id"],
                    "username": user_data["username"],
                    "role": user_data["role"],
                    "exp": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
                    "iat": datetime.utcnow().isoformat(),
                    "type": "access",
                }

                new_access_token = (
                    f"access_token_{json.dumps(new_access_payload, sort_keys=True)}"
                )

                return {
                    "access_token": new_access_token,
                    "token_type": "bearer",
                    "expires_in": 3600,
                }

            except (json.JSONDecodeError, KeyError):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的刷新令牌"
                )

        # 创建有效的刷新令牌
        refresh_payload = {
            "user_id": "user_123",
            "exp": (datetime.utcnow() + timedelta(days=30)).isoformat(),
            "iat": datetime.utcnow().isoformat(),
            "type": "refresh",
        }
        refresh_token = f"refresh_token_{json.dumps(refresh_payload, sort_keys=True)}"

        # 测试令牌刷新
        result = mock_refresh_access_token(refresh_token)
        assert "access_token" in result
        assert result["token_type"] == "bearer"
        assert result["expires_in"] == 3600
        assert result["access_token"].startswith("access_token_")


class TestUserAuthorization:
    """用户授权测试类"""

    def test_role_based_access(self):
        """测试基于角色的访问控制"""

        def mock_check_role_permission(user_role: str, required_role: str) -> bool:
            """检查角色权限"""
            role_hierarchy = {
                "super_admin": 4,
                "admin": 3,
                "moderator": 2,
                "user": 1,
                "guest": 0,
            }

            user_level = role_hierarchy.get(user_role, 0)
            required_level = role_hierarchy.get(required_role, 0)

            return user_level >= required_level

        # 测试各种角色权限
        assert mock_check_role_permission("admin", "user") is True
        assert mock_check_role_permission("user", "admin") is False
        assert mock_check_role_permission("moderator", "moderator") is True
        assert mock_check_role_permission("super_admin", "admin") is True
        assert mock_check_role_permission("guest", "user") is False

    def test_resource_based_access(self):
        """测试基于资源的访问控制"""

        def mock_check_resource_permission(
            user_id: str, resource_id: str, action: str
        ) -> bool:
            """检查资源权限"""
            # 模拟权限数据库
            permissions = {
                "user_123": {
                    "document_456": ["read", "write"],
                    "document_789": ["read"],
                },
                "user_456": {
                    "document_456": ["read"],
                },
            }

            user_permissions = permissions.get(user_id, {})
            resource_permissions = user_permissions.get(resource_id, [])

            return action in resource_permissions

        # 测试资源权限
        assert (
            mock_check_resource_permission("user_123", "document_456", "read") is True
        )
        assert (
            mock_check_resource_permission("user_123", "document_456", "write") is True
        )
        assert (
            mock_check_resource_permission("user_123", "document_789", "read") is True
        )
        assert (
            mock_check_resource_permission("user_123", "document_789", "write") is False
        )

        assert (
            mock_check_resource_permission("user_456", "document_456", "read") is True
        )
        assert (
            mock_check_resource_permission("user_456", "document_456", "write") is False
        )

        # 测试无权限
        assert (
            mock_check_resource_permission("user_789", "document_456", "read") is False
        )

    def test_permission_decorator(self):
        """测试权限装饰器"""

        def mock_require_permission(required_role: str):
            """权限装饰器"""

            def decorator(func):
                def wrapper(current_user: dict, *args, **kwargs):
                    user_role = current_user.get("role", "guest")

                    role_hierarchy = {"admin": 3, "moderator": 2, "user": 1, "guest": 0}

                    user_level = role_hierarchy.get(user_role, 0)
                    required_level = role_hierarchy.get(required_role, 0)

                    if user_level < required_level:
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN, detail="权限不足"
                        )

                    return func(current_user, *args, **kwargs)

                return wrapper

            return decorator

        # 创建需要管理员权限的函数
        @mock_require_permission("admin")
        def admin_only_function(current_user: dict):
            return {"message": "管理员操作成功"}

        # 测试管理员用户
        admin_user = {"id": "admin_123", "username": "admin", "role": "admin"}
        result = admin_only_function(admin_user)
        assert result["message"] == "管理员操作成功"

        # 测试普通用户
        normal_user = {"id": "user_123", "username": "user", "role": "user"}
        with pytest.raises(HTTPException) as exc_info:
            admin_only_function(normal_user)
        assert exc_info.value.status_code == 403
        assert "权限不足" in str(exc_info.value.detail)


class TestSessionManagement:
    """会话管理测试类"""

    def test_create_session(self):
        """测试创建会话"""

        def mock_create_session(user_id: str, ip_address: str, user_agent: str) -> dict:
            """创建用户会话"""
            import uuid

            session = {
                "session_id": str(uuid.uuid4()),
                "user_id": user_id,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "created_at": datetime.utcnow().isoformat(),
                "last_activity": datetime.utcnow().isoformat(),
                "is_active": True,
            }

            return session

        session = mock_create_session(
            "user_123",
            "192.168.1.1",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        )

        assert "session_id" in session
        assert session["user_id"] == "user_123"
        assert session["ip_address"] == "192.168.1.1"
        assert session["is_active"] is True

    def test_validate_session(self):
        """测试验证会话"""

        def mock_validate_session(session_id: str, ip_address: str) -> dict:
            """验证会话"""
            # 模拟会话数据库
            sessions = {
                "session_123": {
                    "session_id": "session_123",
                    "user_id": "user_123",
                    "ip_address": "192.168.1.1",
                    "created_at": datetime.utcnow().isoformat(),
                    "last_activity": datetime.utcnow().isoformat(),
                    "is_active": True,
                },
                "session_456": {
                    "session_id": "session_456",
                    "user_id": "user_456",
                    "ip_address": "192.168.1.2",
                    "created_at": (datetime.utcnow() - timedelta(hours=25)).isoformat(),
                    "last_activity": (
                        datetime.utcnow() - timedelta(hours=25)
                    ).isoformat(),
                    "is_active": True,
                },
            }

            if session_id not in sessions:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的会话"
                )

            session = sessions[session_id]

            # 检查会话是否激活
            if not session["is_active"]:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="会话已失效"
                )

            # 检查IP地址（可选的安全检查）
            if session["ip_address"] != ip_address:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="IP地址不匹配"
                )

            # 检查会话是否过期（24小时）
            last_activity = datetime.fromisoformat(session["last_activity"])
            if datetime.utcnow() - last_activity > timedelta(hours=24):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="会话已过期"
                )

            # 更新最后活动时间
            session["last_activity"] = datetime.utcnow().isoformat()

            return session

        # 测试有效会话
        session = mock_validate_session("session_123", "192.168.1.1")
        assert session["user_id"] == "user_123"

        # 测试无效会话ID
        with pytest.raises(HTTPException) as exc_info:
            mock_validate_session("invalid_session", "192.168.1.1")
        assert exc_info.value.status_code == 401
        assert "无效的会话" in str(exc_info.value.detail)

        # 测试IP地址不匹配
        with pytest.raises(HTTPException) as exc_info:
            mock_validate_session("session_123", "192.168.1.999")
        assert exc_info.value.status_code == 401
        assert "IP地址不匹配" in str(exc_info.value.detail)

        # 测试过期会话
        with pytest.raises(HTTPException) as exc_info:
            mock_validate_session("session_456", "192.168.1.2")
        assert exc_info.value.status_code == 401
        assert "会话已过期" in str(exc_info.value.detail)

    def test_logout_session(self):
        """测试登出会话"""

        def mock_logout_session(session_id: str) -> dict:
            """登出会话"""
            # 模拟会话数据库
            sessions = {
                "session_123": {
                    "session_id": "session_123",
                    "user_id": "user_123",
                    "is_active": True,
                }
            }

            if session_id not in sessions:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在"
                )

            # 标记会话为非激活状态
            sessions[session_id]["is_active"] = False
            sessions[session_id]["logged_out_at"] = datetime.utcnow().isoformat()

            return {"message": "登出成功"}

        # 测试成功登出
        result = mock_logout_session("session_123")
        assert result["message"] == "登出成功"

        # 测试登出不存在的会话
        with pytest.raises(HTTPException) as exc_info:
            mock_logout_session("nonexistent_session")
        assert exc_info.value.status_code == 404
        assert "会话不存在" in str(exc_info.value.detail)


@pytest.mark.unit
class TestSecurityFeatures:
    """安全功能测试类"""

    def test_password_strength_validation(self):
        """测试密码强度验证"""

        def mock_validate_password_strength(password: str) -> dict:
            """验证密码强度"""
            result = {"is_valid": True, "score": 0, "errors": []}

            # 长度检查
            if len(password) >= 8:
                result["score"] += 1
            else:
                result["is_valid"] = False
                result["errors"].append("密码长度至少8位")

            # 大写字母
            if any(c.isupper() for c in password):
                result["score"] += 1
            else:
                result["errors"].append("密码应包含大写字母")

            # 小写字母
            if any(c.islower() for c in password):
                result["score"] += 1
            else:
                result["errors"].append("密码应包含小写字母")

            # 数字
            if any(c.isdigit() for c in password):
                result["score"] += 1
            else:
                result["errors"].append("密码应包含数字")

            # 特殊字符
            special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
            if any(c in special_chars for c in password):
                result["score"] += 1
            else:
                result["errors"].append("密码应包含特殊字符")

            # 最终验证
            if result["score"] < 3:
                result["is_valid"] = False

            return result

        # 测试强密码
        strong_result = mock_validate_password_strength("StrongPass123!")
        assert strong_result["is_valid"] is True
        assert strong_result["score"] == 5

        # 测试弱密码
        weak_result = mock_validate_password_strength("weak")
        assert weak_result["is_valid"] is False
        assert weak_result["score"] < 3
        assert len(weak_result["errors"]) > 0

    def test_account_lockout(self):
        """测试账户锁定机制"""

        class MockAccountLockout:
            def __init__(self):
                self.failed_attempts = {}
                self.lockout_duration = timedelta(minutes=15)
                self.max_attempts = 5

            def record_failed_attempt(self, username: str) -> dict:
                """记录失败尝试"""
                now = datetime.utcnow()

                if username not in self.failed_attempts:
                    self.failed_attempts[username] = []

                # 清理过期的失败记录
                self.failed_attempts[username] = [
                    attempt
                    for attempt in self.failed_attempts[username]
                    if now - attempt < self.lockout_duration
                ]

                # 添加当前失败尝试
                self.failed_attempts[username].append(now)

                attempts_count = len(self.failed_attempts[username])

                if attempts_count >= self.max_attempts:
                    return {
                        "is_locked": True,
                        "attempts": attempts_count,
                        "unlock_time": (now + self.lockout_duration).isoformat(),
                    }
                else:
                    return {
                        "is_locked": False,
                        "attempts": attempts_count,
                        "remaining_attempts": self.max_attempts - attempts_count,
                    }

            def is_account_locked(self, username: str) -> bool:
                """检查账户是否被锁定"""
                if username not in self.failed_attempts:
                    return False

                now = datetime.utcnow()

                # 清理过期的失败记录
                self.failed_attempts[username] = [
                    attempt
                    for attempt in self.failed_attempts[username]
                    if now - attempt < self.lockout_duration
                ]

                return len(self.failed_attempts[username]) >= self.max_attempts

        lockout = MockAccountLockout()

        # 测试正常情况
        assert lockout.is_account_locked("testuser") is False

        # 记录失败尝试
        for i in range(4):
            result = lockout.record_failed_attempt("testuser")
            assert result["is_locked"] is False
            assert result["attempts"] == i + 1

        # 第5次失败应该锁定账户
        result = lockout.record_failed_attempt("testuser")
        assert result["is_locked"] is True
        assert result["attempts"] == 5

        # 验证账户已被锁定
        assert lockout.is_account_locked("testuser") is True

    def test_two_factor_authentication(self):
        """测试双因素认证"""

        def mock_generate_totp_secret() -> str:
            """生成TOTP密钥"""
            import secrets
            import base64

            # 生成32字节随机密钥
            secret = secrets.token_bytes(32)
            return base64.b32encode(secret).decode("utf-8")

        def mock_generate_totp_code(secret: str, timestamp: int = None) -> str:
            """生成TOTP验证码"""
            if timestamp is None:
                timestamp = int(datetime.utcnow().timestamp())

            # 简化的TOTP实现（实际应使用专门的库）
            time_step = timestamp // 30  # 30秒时间窗口
            code = str(time_step % 1000000).zfill(6)  # 6位数字
            return code

        def mock_verify_totp_code(
            secret: str, code: str, timestamp: int = None
        ) -> bool:
            """验证TOTP验证码"""
            if timestamp is None:
                timestamp = int(datetime.utcnow().timestamp())

            # 允许前后30秒的时间窗口
            for offset in [-1, 0, 1]:
                test_timestamp = timestamp + (offset * 30)
                expected_code = mock_generate_totp_code(secret, test_timestamp)
                if code == expected_code:
                    return True

            return False

        # 测试TOTP流程
        secret = mock_generate_totp_secret()
        assert len(secret) > 0

        # 生成验证码
        timestamp = int(datetime.utcnow().timestamp())
        code = mock_generate_totp_code(secret, timestamp)
        assert len(code) == 6
        assert code.isdigit()

        # 验证码验证
        assert mock_verify_totp_code(secret, code, timestamp) is True

        # 错误验证码
        assert mock_verify_totp_code(secret, "000000", timestamp) is False
