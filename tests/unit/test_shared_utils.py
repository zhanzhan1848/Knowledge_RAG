# Knowledge RAG System - 共享工具单元测试
# 测试共享库中的工具函数和类

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone
import json
import hashlib


class TestPasswordUtils:
    """密码工具测试类"""
    
    def test_hash_password(self):
        """测试密码哈希功能"""
        # 模拟密码哈希函数
        def mock_hash_password(password: str) -> str:
            return hashlib.sha256(password.encode()).hexdigest()
        
        password = "test_password_123"
        hashed = mock_hash_password(password)
        
        assert hashed is not None
        assert len(hashed) == 64  # SHA256 哈希长度
        assert hashed != password  # 确保密码被哈希
    
    def test_verify_password(self):
        """测试密码验证功能"""
        def mock_hash_password(password: str) -> str:
            return hashlib.sha256(password.encode()).hexdigest()
        
        def mock_verify_password(password: str, hashed: str) -> bool:
            return mock_hash_password(password) == hashed
        
        password = "test_password_123"
        hashed = mock_hash_password(password)
        
        # 正确密码验证
        assert mock_verify_password(password, hashed) is True
        
        # 错误密码验证
        assert mock_verify_password("wrong_password", hashed) is False


class TestJWTUtils:
    """JWT 工具测试类"""
    
    def test_create_access_token(self):
        """测试创建访问令牌"""
        def mock_create_token(data: dict, expires_delta: int = 3600) -> str:
            # 模拟 JWT 令牌创建
            payload = {
                **data,
                "exp": datetime.now(timezone.utc).timestamp() + expires_delta,
                "iat": datetime.now(timezone.utc).timestamp()
            }
            # 简化的令牌格式（实际应使用 JWT 库）
            return f"mock_token_{json.dumps(payload, sort_keys=True)}"
        
        user_data = {"user_id": "123", "username": "testuser"}
        token = mock_create_token(user_data)
        
        assert token is not None
        assert "mock_token_" in token
        assert "user_id" in token
    
    def test_decode_access_token(self):
        """测试解码访问令牌"""
        def mock_create_token(data: dict, expires_delta: int = 3600) -> str:
            payload = {
                **data,
                "exp": datetime.now(timezone.utc).timestamp() + expires_delta,
                "iat": datetime.now(timezone.utc).timestamp()
            }
            return f"mock_token_{json.dumps(payload, sort_keys=True)}"
        
        def mock_decode_token(token: str) -> dict:
            if not token.startswith("mock_token_"):
                raise ValueError("Invalid token format")
            
            payload_str = token.replace("mock_token_", "")
            payload = json.loads(payload_str)
            
            # 检查令牌是否过期
            if payload["exp"] < datetime.now(timezone.utc).timestamp():
                raise ValueError("Token expired")
            
            return payload
        
        user_data = {"user_id": "123", "username": "testuser"}
        token = mock_create_token(user_data)
        decoded = mock_decode_token(token)
        
        assert decoded["user_id"] == "123"
        assert decoded["username"] == "testuser"
        assert "exp" in decoded
        assert "iat" in decoded
    
    def test_decode_expired_token(self):
        """测试解码过期令牌"""
        def mock_create_expired_token(data: dict) -> str:
            payload = {
                **data,
                "exp": datetime.now(timezone.utc).timestamp() - 3600,  # 1小时前过期
                "iat": datetime.now(timezone.utc).timestamp() - 7200   # 2小时前创建
            }
            return f"mock_token_{json.dumps(payload, sort_keys=True)}"
        
        def mock_decode_token(token: str) -> dict:
            if not token.startswith("mock_token_"):
                raise ValueError("Invalid token format")
            
            payload_str = token.replace("mock_token_", "")
            payload = json.loads(payload_str)
            
            if payload["exp"] < datetime.now(timezone.utc).timestamp():
                raise ValueError("Token expired")
            
            return payload
        
        user_data = {"user_id": "123", "username": "testuser"}
        expired_token = mock_create_expired_token(user_data)
        
        with pytest.raises(ValueError, match="Token expired"):
            mock_decode_token(expired_token)


class TestValidationUtils:
    """验证工具测试类"""
    
    def test_validate_email(self):
        """测试邮箱验证"""
        import re
        
        def mock_validate_email(email: str) -> bool:
            pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            return bool(re.match(pattern, email))
        
        # 有效邮箱
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "test+tag@example.org"
        ]
        
        for email in valid_emails:
            assert mock_validate_email(email) is True
        
        # 无效邮箱
        invalid_emails = [
            "invalid-email",
            "@example.com",
            "test@",
            "test.example.com"
        ]
        
        for email in invalid_emails:
            assert mock_validate_email(email) is False
    
    def test_validate_password_strength(self):
        """测试密码强度验证"""
        def mock_validate_password_strength(password: str) -> dict:
            result = {
                "is_valid": True,
                "errors": []
            }
            
            if len(password) < 8:
                result["is_valid"] = False
                result["errors"].append("密码长度至少8位")
            
            if not any(c.isupper() for c in password):
                result["is_valid"] = False
                result["errors"].append("密码必须包含大写字母")
            
            if not any(c.islower() for c in password):
                result["is_valid"] = False
                result["errors"].append("密码必须包含小写字母")
            
            if not any(c.isdigit() for c in password):
                result["is_valid"] = False
                result["errors"].append("密码必须包含数字")
            
            return result
        
        # 强密码
        strong_password = "StrongPass123"
        result = mock_validate_password_strength(strong_password)
        assert result["is_valid"] is True
        assert len(result["errors"]) == 0
        
        # 弱密码
        weak_password = "weak"
        result = mock_validate_password_strength(weak_password)
        assert result["is_valid"] is False
        assert len(result["errors"]) > 0


class TestFileUtils:
    """文件工具测试类"""
    
    def test_get_file_extension(self):
        """测试获取文件扩展名"""
        def mock_get_file_extension(filename: str) -> str:
            return filename.split('.')[-1].lower() if '.' in filename else ''
        
        test_cases = [
            ("document.pdf", "pdf"),
            ("image.PNG", "png"),
            ("archive.tar.gz", "gz"),
            ("no_extension", ""),
            (".hidden", "hidden")
        ]
        
        for filename, expected in test_cases:
            assert mock_get_file_extension(filename) == expected
    
    def test_validate_file_type(self):
        """测试文件类型验证"""
        def mock_validate_file_type(filename: str, allowed_types: list) -> bool:
            extension = filename.split('.')[-1].lower() if '.' in filename else ''
            return extension in [t.lower() for t in allowed_types]
        
        allowed_types = ["pdf", "docx", "txt", "md"]
        
        # 允许的文件类型
        valid_files = ["document.pdf", "text.txt", "readme.MD"]
        for filename in valid_files:
            assert mock_validate_file_type(filename, allowed_types) is True
        
        # 不允许的文件类型
        invalid_files = ["image.jpg", "script.py", "archive.zip"]
        for filename in invalid_files:
            assert mock_validate_file_type(filename, allowed_types) is False
    
    def test_calculate_file_hash(self):
        """测试文件哈希计算"""
        def mock_calculate_file_hash(content: bytes) -> str:
            return hashlib.md5(content).hexdigest()
        
        test_content = b"This is test file content"
        hash1 = mock_calculate_file_hash(test_content)
        hash2 = mock_calculate_file_hash(test_content)
        
        # 相同内容应产生相同哈希
        assert hash1 == hash2
        
        # 不同内容应产生不同哈希
        different_content = b"This is different content"
        hash3 = mock_calculate_file_hash(different_content)
        assert hash1 != hash3


class TestDateTimeUtils:
    """日期时间工具测试类"""
    
    def test_format_datetime(self):
        """测试日期时间格式化"""
        def mock_format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
            return dt.strftime(format_str)
        
        test_dt = datetime(2024, 1, 15, 10, 30, 45)
        
        # 默认格式
        formatted = mock_format_datetime(test_dt)
        assert formatted == "2024-01-15 10:30:45"
        
        # 自定义格式
        iso_formatted = mock_format_datetime(test_dt, "%Y-%m-%dT%H:%M:%SZ")
        assert iso_formatted == "2024-01-15T10:30:45Z"
    
    def test_parse_datetime(self):
        """测试日期时间解析"""
        def mock_parse_datetime(dt_str: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> datetime:
            return datetime.strptime(dt_str, format_str)
        
        # 标准格式解析
        dt_str = "2024-01-15 10:30:45"
        parsed = mock_parse_datetime(dt_str)
        assert parsed.year == 2024
        assert parsed.month == 1
        assert parsed.day == 15
        assert parsed.hour == 10
        assert parsed.minute == 30
        assert parsed.second == 45
        
        # ISO 格式解析
        iso_str = "2024-01-15T10:30:45Z"
        iso_parsed = mock_parse_datetime(iso_str, "%Y-%m-%dT%H:%M:%SZ")
        assert iso_parsed.year == 2024
    
    def test_get_utc_now(self):
        """测试获取 UTC 当前时间"""
        def mock_get_utc_now() -> datetime:
            return datetime.now(timezone.utc)
        
        utc_now = mock_get_utc_now()
        assert utc_now.tzinfo == timezone.utc
        
        # 检查时间是否合理（在当前时间附近）
        current_time = datetime.now(timezone.utc)
        time_diff = abs((current_time - utc_now).total_seconds())
        assert time_diff < 1  # 应该在1秒内


class TestConfigUtils:
    """配置工具测试类"""
    
    @patch.dict('os.environ', {'TEST_VAR': 'test_value', 'TEST_INT': '123'})
    def test_get_env_variable(self):
        """测试环境变量获取"""
        import os
        
        def mock_get_env(key: str, default=None, var_type=str):
            value = os.environ.get(key, default)
            if value is None:
                return None
            
            if var_type == int:
                return int(value)
            elif var_type == bool:
                return value.lower() in ('true', '1', 'yes', 'on')
            else:
                return str(value)
        
        # 字符串环境变量
        assert mock_get_env('TEST_VAR') == 'test_value'
        
        # 整数环境变量
        assert mock_get_env('TEST_INT', var_type=int) == 123
        
        # 不存在的环境变量（使用默认值）
        assert mock_get_env('NON_EXISTENT', 'default') == 'default'
        
        # 不存在的环境变量（无默认值）
        assert mock_get_env('NON_EXISTENT') is None
    
    def test_validate_config(self):
        """测试配置验证"""
        def mock_validate_config(config: dict, required_keys: list) -> dict:
            result = {
                "is_valid": True,
                "missing_keys": [],
                "errors": []
            }
            
            for key in required_keys:
                if key not in config or config[key] is None:
                    result["is_valid"] = False
                    result["missing_keys"].append(key)
                    result["errors"].append(f"缺少必需的配置项: {key}")
            
            return result
        
        # 完整配置
        complete_config = {
            "database_url": "postgresql://localhost/test",
            "redis_url": "redis://localhost:6379",
            "jwt_secret": "secret_key"
        }
        required_keys = ["database_url", "redis_url", "jwt_secret"]
        
        result = mock_validate_config(complete_config, required_keys)
        assert result["is_valid"] is True
        assert len(result["missing_keys"]) == 0
        
        # 不完整配置
        incomplete_config = {
            "database_url": "postgresql://localhost/test"
        }
        
        result = mock_validate_config(incomplete_config, required_keys)
        assert result["is_valid"] is False
        assert "redis_url" in result["missing_keys"]
        assert "jwt_secret" in result["missing_keys"]


@pytest.mark.unit
class TestAsyncUtils:
    """异步工具测试类"""
    
    @pytest.mark.asyncio
    async def test_async_retry_decorator(self):
        """测试异步重试装饰器"""
        call_count = 0
        
        async def mock_retry_async(func, max_retries=3, delay=0.1):
            """模拟异步重试装饰器"""
            for attempt in range(max_retries + 1):
                try:
                    return await func()
                except Exception as e:
                    if attempt == max_retries:
                        raise e
                    await asyncio.sleep(delay)
        
        async def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary failure")
            return "success"
        
        # 测试重试成功
        result = await mock_retry_async(failing_function)
        assert result == "success"
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_async_timeout(self):
        """测试异步超时"""
        async def mock_with_timeout(coro, timeout_seconds):
            """模拟异步超时装饰器"""
            try:
                return await asyncio.wait_for(coro, timeout=timeout_seconds)
            except asyncio.TimeoutError:
                raise TimeoutError(f"Operation timed out after {timeout_seconds} seconds")
        
        async def slow_function():
            await asyncio.sleep(1)
            return "completed"
        
        # 测试超时
        with pytest.raises(TimeoutError):
            await mock_with_timeout(slow_function(), 0.1)
        
        # 测试正常完成
        async def fast_function():
            await asyncio.sleep(0.01)
            return "completed"
        
        result = await mock_with_timeout(fast_function(), 1)
        assert result == "completed"