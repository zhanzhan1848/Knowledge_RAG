# API网关服务

## 概述

API网关服务是Knowledge RAG系统的统一入口，负责请求路由、认证授权、限流控制等功能。

## 功能特性

### 核心功能
- **请求路由**: 将请求转发到对应的微服务
- **负载均衡**: 支持多实例服务的负载均衡
- **认证授权**: JWT令牌验证和权限控制
- **限流控制**: 基于IP和用户的请求限流
- **健康检查**: 服务健康状态监控
- **请求日志**: 详细的请求日志记录
- **CORS支持**: 跨域请求处理

### 支持的服务
- **认证服务** (`/auth`, `/users`)
- **文档服务** (`/documents`, `/files`, `/quota`, `/backup`)
- **向量服务** (`/vectors`, `/embeddings`)
- **知识图谱服务** (`/graph`, `/entities`, `/relationships`)
- **问答服务** (`/qa`, `/questions`, `/answers`)
- **LLM服务** (`/llm`, `/completions`, `/chat`)

## 快速开始

### 环境要求
- Python 3.11+
- Docker (可选)
- 依赖的微服务

### 本地开发

1. **安装依赖**
```bash
cd services/api-gateway
pip install -r requirements.txt
```

2. **配置环境变量**
```bash
export LOG_LEVEL=INFO
export CORS_ORIGINS="*"
export RATE_LIMIT_ENABLED=true
```

3. **启动服务**
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Docker部署

1. **构建镜像**
```bash
docker build -t knowledge-rag/api-gateway .
```

2. **运行容器**
```bash
docker run -p 8000:8000 knowledge-rag/api-gateway
```

3. **使用Docker Compose**
```bash
docker-compose up -d
```

## 配置说明

### 服务配置

配置文件位于 `config.py`，主要配置项：

```python
class ApiGatewayConfig(BaseModel):
    # 服务配置
    services: Dict[str, ServiceConfig]
    
    # 安全配置
    cors_origins: List[str] = ["*"]
    cors_methods: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]
    
    # 速率限制配置
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 100
    rate_limit_window: int = 60
    
    # 超时配置
    default_timeout: float = 30.0
    
    # 重试配置
    retry_enabled: bool = True
    max_retries: int = 3
```

### 环境变量

| 变量名 | 描述 | 默认值 |
|--------|------|--------|
| `LOG_LEVEL` | 日志级别 | `INFO` |
| `CORS_ORIGINS` | 允许的跨域来源 | `*` |
| `RATE_LIMIT_ENABLED` | 是否启用限流 | `true` |
| `RATE_LIMIT_REQUESTS` | 限流请求数 | `100` |
| `RATE_LIMIT_WINDOW` | 限流时间窗口(秒) | `60` |

## API文档

### 健康检查
```http
GET /health
```

响应:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-15T10:00:00Z",
  "services": {
    "auth-service": "healthy",
    "document-service": "healthy"
  }
}
```

### 服务状态
```http
GET /status
```

### 路由信息
```http
GET /routes
```

## 监控和日志

### 日志配置
- 日志文件: `logs/api_gateway.log`
- 日志格式: JSON结构化日志
- 日志级别: DEBUG, INFO, WARNING, ERROR

### 监控指标
- 请求总数
- 响应时间
- 错误率
- 服务健康状态

## 安全配置

### JWT认证
- 支持Bearer Token认证
- 自动验证JWT令牌
- 提取用户信息

### 限流策略
- 基于IP地址限流
- 基于用户ID限流
- 滑动窗口算法

### CORS配置
- 支持预检请求
- 可配置允许的来源
- 支持凭证传递

## 故障排除

### 常见问题

1. **服务无法启动**
   - 检查端口是否被占用
   - 验证配置文件语法
   - 查看日志文件

2. **路由失败**
   - 检查目标服务是否运行
   - 验证路由配置
   - 检查网络连接

3. **认证失败**
   - 验证JWT令牌格式
   - 检查令牌是否过期
   - 确认密钥配置

### 调试模式

启用调试模式:
```bash
export LOG_LEVEL=DEBUG
uvicorn main:app --host 0.0.0.0 --port 8000 --reload --log-level debug
```

## 性能优化

### 连接池配置
- HTTP连接复用
- 连接超时设置
- 最大连接数限制

### 缓存策略
- 路由缓存
- 健康检查缓存
- 响应缓存

### 负载均衡
- 轮询算法
- 加权轮询
- 健康检查集成

## 开发指南

### 添加新服务

1. 在 `config.py` 中添加服务配置:
```python
"new-service": ServiceConfig(
    name="new-service",
    base_url="http://new-service:8007",
    routes=["/new-api"],
),
```

2. 重启网关服务

### 自定义中间件

创建新的中间件类:
```python
class CustomMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 自定义逻辑
        response = await call_next(request)
        return response

app.add_middleware(CustomMiddleware)
```

## 测试

### 单元测试
```bash
pytest tests/unit/ -v
```

### 集成测试
```bash
pytest tests/integration/ -v
```

### 性能测试
```bash
# 使用wrk进行压力测试
wrk -t12 -c400 -d30s http://localhost:8000/health
```

## 部署

### 生产环境配置

1. **安全配置**
   - 限制CORS来源
   - 启用HTTPS
   - 配置防火墙

2. **性能配置**
   - 调整worker数量
   - 优化连接池
   - 启用缓存

3. **监控配置**
   - 集成Prometheus
   - 配置告警规则
   - 设置日志收集

### Kubernetes部署

参考 `k8s/` 目录下的配置文件。

## 许可证

MIT License