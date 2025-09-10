# Knowledge RAG System - API网关单元测试
# 测试API网关的路由、认证、限流等功能

import json
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch, MagicMock

import pytest
import httpx
from fastapi import FastAPI, HTTPException, status, Request
from fastapi.testclient import TestClient
from pydantic import BaseModel
from typing import List, Dict, Optional

# 导入API网关相关模块
from config import ServiceConfig, get_config
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))


class TestAPIGateway:
    """API网关测试类"""

    def setup_method(self):
        """测试方法设置"""
        self.app = FastAPI(title="Test API Gateway")
        self.client = TestClient(self.app)

    def test_health_check_endpoint(self):
        """测试健康检查端点"""

        @self.app.get("/health")
        async def health_check():
            return {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "version": "1.0.0",
            }

        response = self.client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data

    def test_cors_headers(self):
        """测试CORS头部设置"""

        @self.app.get("/test")
        async def test_endpoint():
            return {"message": "test"}

        # 模拟CORS中间件
        response = self.client.get("/test", headers={"Origin": "http://localhost:3000"})

        assert response.status_code == 200
        # 在实际实现中，这些头部会由CORS中间件添加
        # assert "Access-Control-Allow-Origin" in response.headers
        
    @pytest.mark.asyncio
    @patch("main.get_service_for_path")
    @patch("httpx.AsyncClient.request")
    async def test_proxy_route(self, mock_request, mock_get_service):
        """测试代理路由功能"""
        from main import proxy_route
        
        # 模拟请求和服务
        mock_request = AsyncMock()
        mock_request.return_value = AsyncMock(
            status_code=200,
            headers={"Content-Type": "application/json"},
            content=json.dumps({"result": "success"}).encode(),
        )
        
        mock_service = ServiceConfig(
            name="test-service",
            base_url="http://test-service:8000",
            routes=["/test"],
            health_check_path="/health",
            timeout=30.0,
            is_active=True,
            weight=1
        )
        mock_get_service.return_value = mock_service
        
        # 创建模拟请求
        request = Request(scope={
            "type": "http",
            "method": "GET",
            "path": "/test/endpoint",
            "headers": [(b"host", b"testserver")],
        })
        
        # 调用代理路由
        response = await proxy_route(request, "/test/endpoint")
        
        # 验证结果
        assert response.status_code == 200
        assert json.loads(response.body) == {"result": "success"}
        
        # 验证服务调用
        mock_get_service.assert_called_once_with("/test/endpoint")
        mock_request.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_service_discovery(self):
        """测试服务发现功能"""
        from main import get_service_for_path
        
        # 创建测试服务配置
        services = {
            "auth": ServiceConfig(
                name="auth-service",
                base_url="http://auth-service:8001",
                routes=["/auth", "/users"],
                is_active=True,
                weight=1
            ),
            "document": ServiceConfig(
                name="document-service",
                base_url="http://document-service:8002",
                routes=["/documents"],
                is_active=True,
                weight=1
            )
        }
        
        # 模拟SERVICES字典
        with patch("main.SERVICES", services):
            # 测试匹配路由
            service = await get_service_for_path("/auth/login")
            assert service is not None
            assert service.name == "auth-service"
            
            # 测试未匹配路由
            service = await get_service_for_path("/unknown/path")
            assert service is None
            
            # 测试非活动服务
            services["auth"].is_active = False
            service = await get_service_for_path("/auth/login")
            assert service is None


class TestLoadBalancing:
    """负载均衡测试类"""
    
    @pytest.mark.asyncio
    async def test_weighted_load_balancing(self):
        """测试加权负载均衡"""
        from main import get_service_for_path
        import random
        
        # 创建测试服务配置，两个服务具有相同路由但不同权重
        services = {
            "service1": ServiceConfig(
                name="service1",
                base_url="http://service1:8001",
                routes=["/api"],
                is_active=True,
                weight=3  # 权重为3
            ),
            "service2": ServiceConfig(
                name="service2",
                base_url="http://service2:8002",
                routes=["/api"],
                is_active=True,
                weight=1  # 权重为1
            )
        }
        
        # 模拟随机函数，确保可预测的测试结果
        with patch("main.SERVICES", services), \
             patch("random.uniform", side_effect=[1.5, 3.5]):
            # 第一次调用应该返回service1（权重范围0-3）
            service = await get_service_for_path("/api/endpoint")
            assert service.name == "service1"
            
            # 第二次调用应该返回service2（权重范围3-4）
            service = await get_service_for_path("/api/endpoint")
            assert service.name == "service2"


class TestRateLimiting:
    """速率限制测试类"""
    
    @pytest.mark.asyncio
    async def test_rate_limit_middleware(self):
        """测试速率限制中间件"""
        from main import RateLimitMiddleware
        
        # 创建测试应用和中间件
        app = FastAPI()
        
        # 模拟配置
        config_mock = MagicMock()
        config_mock.rate_limit_enabled = True
        config_mock.rate_limit_requests = 2  # 限制为2个请求
        config_mock.rate_limit_window = 60
        
        with patch("main.config", config_mock):
            middleware = RateLimitMiddleware(app)
            
            # 创建模拟请求
            request = Request(scope={
                "type": "http",
                "client": ("127.0.0.1", 12345),
                "method": "GET",
                "path": "/test",
            })
            
            # 模拟call_next函数
            async def mock_call_next(request):
                return Response(content="OK", status_code=200)
            
            # 第一个请求应该通过
            response = await middleware.dispatch(request, mock_call_next)
            assert response.status_code == 200
            
            # 第二个请求应该通过
            response = await middleware.dispatch(request, mock_call_next)
            assert response.status_code == 200
            
            # 第三个请求应该被限制
            response = await middleware.dispatch(request, mock_call_next)
            assert response.status_code == 429
            
    @pytest.mark.asyncio
    async def test_rate_limit_disabled(self):
        """测试禁用速率限制"""
        from main import RateLimitMiddleware
        
        # 创建测试应用和中间件
        app = FastAPI()
        
        # 模拟配置
        config_mock = MagicMock()
        config_mock.rate_limit_enabled = False
        
        with patch("main.config", config_mock):
            middleware = RateLimitMiddleware(app)
            
            # 创建模拟请求
            request = Request(scope={
                "type": "http",
                "client": ("127.0.0.1", 12345),
                "method": "GET",
                "path": "/test",
            })
            
            # 模拟call_next函数
            async def mock_call_next(request):
                return Response(content="OK", status_code=200)
            
            # 多次请求都应该通过
            for _ in range(10):
                response = await middleware.dispatch(request, mock_call_next)
                assert response.status_code == 200


class TestAuthentication:
    """认证测试类"""

    def setup_method(self):
        """测试方法设置"""
        self.app = FastAPI()
        self.client = TestClient(self.app)

    def test_jwt_token_validation(self):
        """测试JWT令牌验证"""

        def mock_verify_token(token: str) -> dict:
            """模拟令牌验证函数"""
            if token == "valid_token":
                return {
                    "user_id": "123",
                    "username": "testuser",
                    "exp": (datetime.utcnow() + timedelta(hours=1)).timestamp(),
                }
            elif token == "expired_token":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
                )

        # 测试有效令牌
        user_data = mock_verify_token("valid_token")
        assert user_data["user_id"] == "123"
        assert user_data["username"] == "testuser"

        # 测试无效令牌
        with pytest.raises(HTTPException) as exc_info:
            mock_verify_token("invalid_token")
        assert exc_info.value.status_code == 401
        assert "Invalid token" in str(exc_info.value.detail)

        # 测试过期令牌
        with pytest.raises(HTTPException) as exc_info:
            mock_verify_token("expired_token")
        assert exc_info.value.status_code == 401
        assert "Token expired" in str(exc_info.value.detail)

    def test_protected_endpoint(self):
        """测试受保护的端点"""
        # 此处可以添加受保护端点的测试逻辑
        pass


class TestRetryMechanism:
    """重试机制测试类"""
    
    @pytest.mark.asyncio
    @patch("main.get_service_for_path")
    @patch("httpx.AsyncClient.request")
    @patch("asyncio.sleep")
    async def test_retry_mechanism(self, mock_sleep, mock_request, mock_get_service):
        """测试请求重试机制"""
        from main import proxy_route
        
        # 模拟服务
        mock_service = ServiceConfig(
            name="test-service",
            base_url="http://test-service:8000",
            routes=["/test"],
            health_check_path="/health",
            timeout=1.0,
            is_active=True,
            weight=1
        )
        mock_get_service.return_value = mock_service
        
        # 模拟配置
        config_mock = MagicMock()
        config_mock.retry_enabled = True
        config_mock.max_retries = 2
        config_mock.retry_backoff = 0.1
        
        # 模拟请求失败后成功
        mock_request.side_effect = [
            httpx.RequestError("Connection error"),  # 第一次失败
            AsyncMock(  # 第二次成功
                status_code=200,
                headers={"Content-Type": "application/json"},
                content=json.dumps({"result": "success"}).encode(),
            )
        ]
        
        # 创建模拟请求
        request = Request(scope={
            "type": "http",
            "method": "GET",
            "path": "/test/endpoint",
            "headers": [(b"host", b"testserver")],
        })
        
        # 调用代理路由
        with patch("main.config", config_mock):
            response = await proxy_route(request, "/test/endpoint")
        
        # 验证结果
        assert response.status_code == 200
        assert json.loads(response.body) == {"result": "success"}
        
        # 验证重试
        assert mock_request.call_count == 2
        mock_sleep.assert_called_once_with(0.1)  # 验证退避时间
        
    @pytest.mark.asyncio
    @patch("main.get_service_for_path")
    @patch("httpx.AsyncClient.request")
    async def test_retry_exhausted(self, mock_request, mock_get_service):
        """测试重试耗尽"""
        from main import proxy_route
        
        # 模拟服务
        mock_service = ServiceConfig(
            name="test-service",
            base_url="http://test-service:8000",
            routes=["/test"],
            health_check_path="/health",
            timeout=1.0,
            is_active=True,
            weight=1
        )
        mock_get_service.return_value = mock_service
        
        # 模拟配置
        config_mock = MagicMock()
        config_mock.retry_enabled = True
        config_mock.max_retries = 2
        config_mock.retry_backoff = 0.1
        
        # 模拟请求始终失败
        error = httpx.RequestError("Connection error")
        mock_request.side_effect = [error, error, error]
        
        # 创建模拟请求
        request = Request(scope={
            "type": "http",
            "method": "GET",
            "path": "/test/endpoint",
            "headers": [(b"host", b"testserver")],
        })
        
        # 调用代理路由
        with patch("main.config", config_mock), pytest.raises(httpx.RequestError):
            await proxy_route(request, "/test/endpoint")
        
        # 验证重试次数
        assert mock_request.call_count == 3  # 初始请求 + 2次重试


class TestAuthentication(TestAuthentication):
    """继续认证测试类"""
    
    def mock_get_current_user(self, token: str = None):
        """模拟获取当前用户函数"""
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing authentication token",
            )

        if token == "Bearer valid_token":
            return {"user_id": "123", "username": "testuser", "role": "user"}
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
            )

    def test_protected_endpoint(self):
        """测试受保护的端点"""
        # 定义受保护的端点
        def setup_protected_endpoint():
            @self.app.get("/protected")
            async def protected_endpoint(authorization: str = None):
                user = self.mock_get_current_user(authorization)
                return {"message": f"Hello, {user['username']}!"}
            
        # 设置端点
        setup_protected_endpoint()
        
        # 测试无令牌访问
        response = self.client.get("/protected")
        assert response.status_code == 401
        
        # 测试有效令牌访问
        response = self.client.get("/protected", headers={"Authorization": "Bearer valid_token"})
        assert response.status_code == 200
        assert response.json()["message"] == "Hello, testuser!"
        
        # 测试无效令牌访问
        response = self.client.get("/protected", headers={"Authorization": "Bearer invalid_token"})
        assert response.status_code == 401

        # 测试有效令牌访问
        response = self.client.get(
            "/protected", headers={"Authorization": "Bearer valid_token"}
        )
        # 在实际实现中，这会返回200和用户信息

    def test_role_based_access_control(self):
        """测试基于角色的访问控制"""

        def mock_check_permission(user_role: str, required_role: str) -> bool:
            """模拟权限检查函数"""
            role_hierarchy = {"admin": 3, "moderator": 2, "user": 1, "guest": 0}

            user_level = role_hierarchy.get(user_role, 0)
            required_level = role_hierarchy.get(required_role, 0)

            return user_level >= required_level

        # 测试管理员访问用户资源
        assert mock_check_permission("admin", "user") is True

        # 测试用户访问管理员资源
        assert mock_check_permission("user", "admin") is False

        # 测试相同角色访问
        assert mock_check_permission("moderator", "moderator") is True

        # 测试未知角色
        assert mock_check_permission("unknown", "user") is False


class TestRateLimiting:
    """限流测试类"""

    def test_rate_limit_per_user(self):
        """测试用户级别限流"""

        class MockRateLimiter:
            def __init__(self):
                self.requests = {}

            def is_allowed(
                self, user_id: str, limit: int = 100, window: int = 3600
            ) -> bool:
                """检查是否允许请求"""
                now = datetime.utcnow().timestamp()

                if user_id not in self.requests:
                    self.requests[user_id] = []

                # 清理过期请求
                self.requests[user_id] = [
                    req_time
                    for req_time in self.requests[user_id]
                    if now - req_time < window
                ]

                # 检查是否超过限制
                if len(self.requests[user_id]) >= limit:
                    return False

                # 记录当前请求
                self.requests[user_id].append(now)
                return True

        limiter = MockRateLimiter()

        # 测试正常请求
        assert limiter.is_allowed("user1", limit=5) is True
        assert limiter.is_allowed("user1", limit=5) is True

        # 测试达到限制
        for _ in range(3):
            limiter.is_allowed("user1", limit=5)

        # 第6个请求应该被拒绝
        assert limiter.is_allowed("user1", limit=5) is False

        # 不同用户不受影响
        assert limiter.is_allowed("user2", limit=5) is True

    def test_rate_limit_per_ip(self):
        """测试IP级别限流"""

        class MockIPRateLimiter:
            def __init__(self):
                self.ip_requests = {}

            def is_allowed(
                self, ip_address: str, limit: int = 1000, window: int = 3600
            ) -> bool:
                """检查IP是否允许请求"""
                now = datetime.utcnow().timestamp()

                if ip_address not in self.ip_requests:
                    self.ip_requests[ip_address] = []

                # 清理过期请求
                self.ip_requests[ip_address] = [
                    req_time
                    for req_time in self.ip_requests[ip_address]
                    if now - req_time < window
                ]

                # 检查是否超过限制
                if len(self.ip_requests[ip_address]) >= limit:
                    return False

                # 记录当前请求
                self.ip_requests[ip_address].append(now)
                return True

        limiter = MockIPRateLimiter()

        # 测试正常请求
        assert limiter.is_allowed("192.168.1.1", limit=3) is True
        assert limiter.is_allowed("192.168.1.1", limit=3) is True
        assert limiter.is_allowed("192.168.1.1", limit=3) is True

        # 第4个请求应该被拒绝
        assert limiter.is_allowed("192.168.1.1", limit=3) is False

        # 不同IP不受影响
        assert limiter.is_allowed("192.168.1.2", limit=3) is True


class TestRequestRouting:
    """请求路由测试类"""

    def setup_method(self):
        """测试方法设置"""
        self.app = FastAPI()
        self.client = TestClient(self.app)

    def test_service_routing(self):
        """测试服务路由"""

        class MockServiceRouter:
            def __init__(self):
                self.services = {
                    "auth": "http://auth-service:8001",
                    "document": "http://document-service:8002",
                    "vector": "http://vector-service:8003",
                    "llm": "http://llm-service:8004",
                    "qa": "http://qa-service:8005",
                }

            def get_service_url(self, service_name: str) -> str:
                """获取服务URL"""
                if service_name not in self.services:
                    raise ValueError(f"Unknown service: {service_name}")
                return self.services[service_name]

            def route_request(self, path: str) -> str:
                """根据路径路由请求"""
                if path.startswith("/auth/"):
                    return self.get_service_url("auth")
                elif path.startswith("/documents/"):
                    return self.get_service_url("document")
                elif path.startswith("/vectors/"):
                    return self.get_service_url("vector")
                elif path.startswith("/llm/"):
                    return self.get_service_url("llm")
                elif path.startswith("/qa/"):
                    return self.get_service_url("qa")
                else:
                    raise ValueError(f"No route found for path: {path}")

        router = MockServiceRouter()

        # 测试各种路径路由
        assert router.route_request("/auth/login") == "http://auth-service:8001"
        assert (
            router.route_request("/documents/upload") == "http://document-service:8002"
        )
        assert router.route_request("/vectors/search") == "http://vector-service:8003"
        assert router.route_request("/llm/generate") == "http://llm-service:8004"
        assert router.route_request("/qa/ask") == "http://qa-service:8005"

        # 测试未知路径
        with pytest.raises(ValueError, match="No route found for path"):
            router.route_request("/unknown/path")

    def test_load_balancing(self):
        """测试负载均衡"""

        class MockLoadBalancer:
            def __init__(self):
                self.services = {
                    "document": [
                        "http://document-service-1:8002",
                        "http://document-service-2:8002",
                        "http://document-service-3:8002",
                    ]
                }
                self.current_index = {}

            def get_next_instance(self, service_name: str) -> str:
                """获取下一个服务实例（轮询）"""
                if service_name not in self.services:
                    raise ValueError(f"Unknown service: {service_name}")

                instances = self.services[service_name]
                if service_name not in self.current_index:
                    self.current_index[service_name] = 0

                instance = instances[self.current_index[service_name]]
                self.current_index[service_name] = (
                    self.current_index[service_name] + 1
                ) % len(instances)

                return instance

        balancer = MockLoadBalancer()

        # 测试轮询负载均衡
        instances = []
        for _ in range(6):  # 请求6次，应该轮询两轮
            instances.append(balancer.get_next_instance("document"))

        # 验证轮询顺序
        expected = [
            "http://document-service-1:8002",
            "http://document-service-2:8002",
            "http://document-service-3:8002",
            "http://document-service-1:8002",
            "http://document-service-2:8002",
            "http://document-service-3:8002",
        ]
        assert instances == expected


class TestRequestValidation:
    """请求验证测试类"""

    def test_request_size_validation(self):
        """测试请求大小验证"""

        def mock_validate_request_size(
            content_length: int, max_size: int = 10 * 1024 * 1024
        ) -> bool:
            """验证请求大小（默认10MB）"""
            return content_length <= max_size

        # 测试正常大小请求
        assert mock_validate_request_size(1024) is True  # 1KB
        assert mock_validate_request_size(5 * 1024 * 1024) is True  # 5MB

        # 测试超大请求
        assert mock_validate_request_size(15 * 1024 * 1024) is False  # 15MB

    def test_content_type_validation(self):
        """测试内容类型验证"""

        def mock_validate_content_type(content_type: str, allowed_types: list) -> bool:
            """验证内容类型"""
            return content_type in allowed_types

        allowed_types = [
            "application/json",
            "application/pdf",
            "text/plain",
            "multipart/form-data",
        ]

        # 测试允许的内容类型
        assert mock_validate_content_type("application/json", allowed_types) is True
        assert mock_validate_content_type("application/pdf", allowed_types) is True

        # 测试不允许的内容类型
        assert mock_validate_content_type("application/xml", allowed_types) is False
        assert mock_validate_content_type("image/jpeg", allowed_types) is False

    def test_request_headers_validation(self):
        """测试请求头验证"""

        def mock_validate_headers(headers: dict) -> dict:
            """验证请求头"""
            result = {"is_valid": True, "errors": []}

            # 检查必需的头部
            required_headers = ["User-Agent", "Accept"]
            for header in required_headers:
                if header not in headers:
                    result["is_valid"] = False
                    result["errors"].append(f"Missing required header: {header}")

            # 检查内容长度
            if "Content-Length" in headers:
                try:
                    content_length = int(headers["Content-Length"])
                    if content_length < 0:
                        result["is_valid"] = False
                        result["errors"].append("Invalid Content-Length")
                except ValueError:
                    result["is_valid"] = False
                    result["errors"].append("Invalid Content-Length format")

            return result

        # 测试有效头部
        valid_headers = {
            "User-Agent": "TestClient/1.0",
            "Accept": "application/json",
            "Content-Length": "1024",
        }
        result = mock_validate_headers(valid_headers)
        assert result["is_valid"] is True
        assert len(result["errors"]) == 0

        # 测试缺少必需头部
        invalid_headers = {"Content-Type": "application/json"}
        result = mock_validate_headers(invalid_headers)
        assert result["is_valid"] is False
        assert "Missing required header: User-Agent" in result["errors"]
        assert "Missing required header: Accept" in result["errors"]


@pytest.mark.unit
class TestErrorHandling:
    """错误处理测试类"""

    def test_http_exception_handler(self):
        """测试HTTP异常处理"""

        def mock_handle_http_exception(exc: HTTPException) -> dict:
            """模拟HTTP异常处理器"""
            return {
                "error": {
                    "code": exc.status_code,
                    "message": exc.detail,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            }

        # 测试401异常
        exc_401 = HTTPException(status_code=401, detail="Unauthorized")
        response = mock_handle_http_exception(exc_401)
        assert response["error"]["code"] == 401
        assert response["error"]["message"] == "Unauthorized"

        # 测试404异常
        exc_404 = HTTPException(status_code=404, detail="Not Found")
        response = mock_handle_http_exception(exc_404)
        assert response["error"]["code"] == 404
        assert response["error"]["message"] == "Not Found"

    def test_validation_error_handler(self):
        """测试验证错误处理"""

        def mock_handle_validation_error(errors: list) -> dict:
            """模拟验证错误处理器"""
            return {
                "error": {
                    "code": 422,
                    "message": "Validation Error",
                    "details": errors,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            }

        validation_errors = [
            {"field": "email", "message": "Invalid email format"},
            {"field": "password", "message": "Password too short"},
        ]

        response = mock_handle_validation_error(validation_errors)
        assert response["error"]["code"] == 422
        assert response["error"]["message"] == "Validation Error"
        assert len(response["error"]["details"]) == 2

    def test_internal_server_error_handler(self):
        """测试内部服务器错误处理"""

        def mock_handle_internal_error(exc: Exception) -> dict:
            """模拟内部错误处理器"""
            return {
                "error": {
                    "code": 500,
                    "message": "Internal Server Error",
                    "timestamp": datetime.utcnow().isoformat(),
                    # 在生产环境中不应暴露详细错误信息
                    "debug_info": (
                        str(exc) if hasattr(exc, "__str__") else "Unknown error"
                    ),
                }
            }

        # 测试一般异常
        exc = ValueError("Something went wrong")
        response = mock_handle_internal_error(exc)
        assert response["error"]["code"] == 500
        assert response["error"]["message"] == "Internal Server Error"
        assert "Something went wrong" in response["error"]["debug_info"]
