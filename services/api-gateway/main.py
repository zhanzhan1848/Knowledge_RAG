#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
api-gateway 主模块

该模块实现了API网关的主要功能，包括请求路由、认证、限流等。
"""

from fastapi import FastAPI, HTTPException, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import httpx
import logging
import os
import time
import json
import random
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

# 导入配置
from config import get_config, ServiceConfig
import asyncio

# 获取配置
config = get_config()

# 配置日志
# 确保日志目录存在
import os
log_dir = os.path.dirname(config.log_file)
if not os.path.exists(log_dir):
    os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=getattr(logging, config.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(config.log_file),
    ],
)
logger = logging.getLogger(__name__)

# 从配置获取服务信息
SERVICES = config.services

# 创建FastAPI应用
app = FastAPI(
    title="Knowledge RAG API Gateway",
    description="API Gateway for Knowledge RAG system - 统一入口和路由管理",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=config.cors_methods,
    allow_headers=config.cors_headers,
    expose_headers=["X-Request-ID", "X-Process-Time"],
)


# 请求日志中间件
class RequestLoggerMiddleware(BaseHTTPMiddleware):
    """请求日志中间件，记录请求和响应信息"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        request_id = request.headers.get("X-Request-ID", "")
        
        # 记录请求信息
        logger.info(f"Request {request_id}: {request.method} {request.url.path}")
        
        # 处理请求
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # 添加处理时间头
            response.headers["X-Process-Time"] = str(process_time)
            
            # 记录响应信息
            logger.info(
                f"Response {request_id}: {response.status_code} "
                f"completed in {process_time:.4f}s"
            )
            return response
        except Exception as e:
            logger.error(f"Request {request_id} failed: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal Server Error"},
            )

# 速率限制中间件
class RateLimitMiddleware(BaseHTTPMiddleware):
    """速率限制中间件，防止DDoS攻击"""
    
    def __init__(self, app):
        super().__init__(app)
        # 在实际应用中，应该使用Redis等分布式存储来跟踪请求
        self.requests = {}
        # 从配置获取限制
        self.enabled = config.rate_limit_enabled
        self.rate_limit = config.rate_limit_requests
        self.time_window = config.rate_limit_window  # 秒
    
    async def dispatch(self, request: Request, call_next):
        # 如果未启用速率限制，直接处理请求
        if not self.enabled:
            return await call_next(request)
            
        # 获取客户端IP
        client_ip = request.client.host
        current_time = time.time()
        
        # 清理过期记录
        if client_ip in self.requests:
            self.requests[client_ip] = [t for t in self.requests[client_ip] 
                                      if current_time - t < self.time_window]
        else:
            self.requests[client_ip] = []
        
        # 检查是否超过限制
        if len(self.requests[client_ip]) >= self.rate_limit:
            logger.warning(f"Rate limit exceeded for {client_ip}")
            return JSONResponse(
                status_code=429,
                content={"detail": "Too Many Requests"},
            )
        
        # 记录请求时间
        self.requests[client_ip].append(current_time)
        
        # 处理请求
        return await call_next(request)

# 认证中间件
class AuthMiddleware(BaseHTTPMiddleware):
    """认证中间件，验证请求中的JWT令牌"""
    
    async def dispatch(self, request: Request, call_next):
        # 获取路径
        path = request.url.path
        
        # 不需要认证的路径
        public_paths = [
            "/health", 
            "/api/docs", 
            "/api/redoc", 
            "/api/openapi.json",
            "/services",
            "/services/health",
            "/auth/login",
            "/auth/register"
        ]
        
        # 检查是否是公开路径
        for public_path in public_paths:
            if path.startswith(public_path):
                return await call_next(request)
        
        # 获取认证头
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"detail": "Authentication required"}
            )
        
        # 提取令牌
        token = auth_header.replace("Bearer ", "")
        
        # 在实际应用中，这里应该调用auth服务验证令牌
        # 为了测试，我们简单地接受任何非空令牌
        if token:
            # 添加用户信息到请求状态
            request.state.user = {"user_id": "test_user", "role": "user"}
            return await call_next(request)
        else:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid token"}
            )

# 添加中间件
app.add_middleware(RequestLoggerMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(AuthMiddleware)

# 创建HTTP客户端
http_client = httpx.AsyncClient()

# 路由函数
async def get_service_for_path(path: str) -> Optional[ServiceConfig]:
    """根据路径获取对应的服务配置
    
    如果有多个匹配的服务，根据权重进行负载均衡选择
    
    Args:
        path: 请求路径
        
    Returns:
        ServiceConfig: 匹配的服务配置，如果没有匹配则返回None
    """
    matching_services = []
    
    # 查找所有匹配的服务
    for service in SERVICES.values():
        if not service.is_active:
            continue
            
        for route in service.routes:
            if path.startswith(route):
                matching_services.append(service)
                break
    
    if not matching_services:
        return None
        
    # 如果只有一个匹配的服务，直接返回
    if len(matching_services) == 1:
        return matching_services[0]
        
    # 根据权重进行负载均衡
    total_weight = sum(service.weight for service in matching_services)
    r = random.uniform(0, total_weight)
    upto = 0
    
    for service in matching_services:
        upto += service.weight
        if upto >= r:
            return service
            
    # 默认返回第一个
    return matching_services[0]

@app.get("/")
async def root():
    """根路径响应"""
    return {
        "message": "Welcome to Knowledge RAG API Gateway",
        "version": "0.1.0",
        "services": [s.name for s in SERVICES.values() if s.is_active],
    }

@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy", "service": "api-gateway"}

@app.get("/services")
async def list_services():
    """列出所有可用服务"""
    return {
        "services": [
            {
                "name": service.name,
                "routes": service.routes,
                "status": "active" if service.is_active else "inactive",
            }
            for service in SERVICES.values()
        ]
    }

@app.get("/services/health")
async def services_health():
    """检查所有服务的健康状态"""
    results = {}
    
    for service_id, service in SERVICES.items():
        if not service.is_active:
            results[service_id] = {"status": "inactive"}
            continue
            
        try:
            health_url = f"{service.base_url}{service.health_check_path}"
            response = await http_client.get(
                health_url, 
                timeout=5.0
            )
            if response.status_code == 200:
                results[service_id] = {"status": "healthy"}
            else:
                results[service_id] = {
                    "status": "unhealthy",
                    "code": response.status_code,
                }
        except Exception as e:
            results[service_id] = {
                "status": "unreachable",
                "error": str(e),
            }
    
    return {"services": results}


# 通用代理路由
@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def proxy_route(request: Request, path: str):
    """通用API网关路由，转发请求到对应的微服务"""
    # 获取完整路径
    full_path = f"/{path}"
    
    # 查找对应的服务
    service = await get_service_for_path(full_path)
    if not service:
        return JSONResponse(
            status_code=404,
            content={"detail": f"No service found for path: {full_path}"},
        )
    
    if not service.is_active:
        return JSONResponse(
            status_code=503,
            content={"detail": f"Service {service.name} is currently unavailable"},
        )
    
    # 构建目标URL
    target_url = f"{service.base_url}{full_path}"
    
    # 获取请求内容
    body = await request.body()
    headers = dict(request.headers)
    
    # 添加跟踪信息
    headers["X-Forwarded-For"] = request.client.host
    headers["X-Gateway-Service"] = "api-gateway"
    
    try:
        # 转发请求，支持重试
        retry_count = 0
        max_retries = config.max_retries if config.retry_enabled else 0
        
        while True:
            try:
                response = await http_client.request(
                    method=request.method,
                    url=target_url,
                    content=body,
                    headers=headers,
                    params=request.query_params,
                    cookies=request.cookies,
                    follow_redirects=True,
                    timeout=service.timeout,
                )
                break
            except httpx.RequestError as e:
                retry_count += 1
                if retry_count > max_retries:
                    raise
                    
                # 指数退避重试
                wait_time = config.retry_backoff * (2 ** (retry_count - 1))
                logger.warning(f"Retrying request to {service.name} after {wait_time}s (attempt {retry_count}/{max_retries})")
                await asyncio.sleep(wait_time)
        
        # 构建响应
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers),
        )
    except httpx.RequestError as e:
        logger.error(f"Error forwarding request to {service.name}: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={"detail": f"Service {service.name} unavailable: {str(e)}"},
        )
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal Server Error"},
        )

# 应用启动和关闭事件
@app.on_event("startup")
async def startup_event():
    """应用启动时执行"""
    logger.info("API Gateway starting up")
    # 确保日志目录存在
    os.makedirs("logs", exist_ok=True)

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时执行"""
    logger.info("API Gateway shutting down")
    await http_client.aclose()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)