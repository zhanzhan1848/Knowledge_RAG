# 部署模式说明

本项目支持多种部署模式，以适应不同的环境需求。

## 1. 完整部署模式 (生产环境)

### 使用场景
- 生产环境
- 本地完整功能测试
- 性能测试

### 启动命令
```bash
docker compose -f docker-compose.yml up -d --build
```

### 包含服务
- **基础设施**: PostgreSQL, Redis, Elasticsearch, Neo4j, RabbitMQ, Weaviate, text2vec-model2vec
- **微服务**: api-gateway, auth-service, document-service, vector-service, llm-service, qa-service, knowledge-graph-service, graph-service, notification-service
- **监控**: Prometheus, Grafana

### 资源需求
- **内存**: 至少 8GB RAM
- **CPU**: 至少 4 核心
- **存储**: 至少 20GB 可用空间

## 2. CI/CD 轻量化模式

### 使用场景
- GitHub Actions CI/CD
- 集成测试
- 资源受限环境

### 启动命令
```bash
docker compose -f docker-compose.ci.yml up -d --build
```

### 包含服务
- **基础设施**: PostgreSQL, Redis (仅核心服务)
- **微服务**: api-gateway, auth-service, vector-service, llm-service, qa-service
- **排除服务**: Elasticsearch, Neo4j, Weaviate, document-service, knowledge-graph-service, graph-service, notification-service

### 资源需求
- **内存**: 2-4GB RAM
- **CPU**: 2 核心
- **存储**: 5GB 可用空间

### 特殊配置
- `vector-service`: 使用内存向量存储替代 Weaviate
- `llm-service`: 使用模拟模式替代真实 LLM 调用
- `ENVIRONMENT=testing`: 启用测试模式配置

## 3. 最小化模式 (故障恢复)

### 使用场景
- CI/CD 环境资源不足时的后备方案
- 快速功能验证
- 调试核心服务

### 启动命令
```bash
docker compose -f docker-compose.ci.yml up -d --build postgres redis api-gateway auth-service
```

### 包含服务
- **基础设施**: PostgreSQL, Redis
- **微服务**: api-gateway, auth-service

## 4. 部署策略建议

### GitHub Actions CI/CD

#### 渐进式测试策略
我们提供了三种CI/CD测试模式：

1. **基础设施测试** (`test-infrastructure`)
   ```bash
   # 仅测试PostgreSQL + Redis
   docker compose -f docker-compose.core.yml up -d postgres redis
   ```

2. **核心RAG服务测试** (`test-core-rag`)
   ```bash
   # 测试完整的RAG核心组件
   docker compose -f docker-compose.core.yml up -d postgres redis neo4j text2vec-model2vec weaviate
   docker compose -f docker-compose.core.yml up -d --build api-gateway auth-service vector-service knowledge-graph-service
   ```

3. **完整工作流测试** (`test-full-rag-workflow`)
   ```bash
   # 测试完整的RAG系统
   docker compose -f docker-compose.core.yml up -d --build
   ```

#### 手动触发测试
```bash
# 在GitHub Actions中手动选择测试级别
# basic: 仅基础设施
# core: 核心RAG服务
# full: 完整工作流
```

#### 传统CI/CD模式（备用方案）

当前 CI/CD 工作流采用渐进式部署策略：

1. **首选**: 使用 `docker-compose.ci.yml` 启动轻量化服务
2. **后备**: 如果轻量化模式失败，自动降级到最小化模式
3. **清理**: 确保所有配置文件都被正确清理

### 本地开发

```bash
# 完整功能开发
docker compose -f docker-compose.yml up -d --build

# 快速测试
docker compose -f docker-compose.ci.yml up -d --build

# 调试特定服务
docker compose -f docker-compose.yml up -d postgres redis
docker compose -f docker-compose.yml up -d --build api-gateway
```

## 5. 常见问题解决

### Elasticsearch 启动失败
- **原因**: 内存不足或虚拟内存设置问题
- **解决**: 使用 CI 模式，排除 Elasticsearch
- **命令**: `docker compose -f docker-compose.ci.yml up -d --build`

### Weaviate 连接超时
- **原因**: 向量数据库启动时间较长
- **解决**: 使用内存向量存储
- **配置**: `VECTOR_STORE_TYPE=memory`

### 服务依赖问题
- **原因**: 服务启动顺序或健康检查失败
- **解决**: 使用最小化模式逐步启动
- **策略**: 先启动基础设施，再启动应用服务

### 资源不足
- **症状**: 容器频繁重启或 OOM 错误
- **解决**: 使用轻量化或最小化模式
- **监控**: 检查 `docker stats` 输出

## 6. 环境变量配置

### 生产环境
```bash
ENVIRONMENT=production
OPENAI_API_KEY=your_real_key
HUGGINGFACE_API_KEY=your_real_key
```

### CI/CD 环境
```bash
ENVIRONMENT=testing
OPENAI_API_KEY=test_key
HUGGINGFACE_API_KEY=test_key
LLM_MODE=mock
VECTOR_STORE_TYPE=memory
```

## 7. 监控和日志

### 服务状态检查
```bash
# 检查所有服务状态
docker compose ps

# 检查特定服务日志
docker compose logs api-gateway

# 实时监控资源使用
docker stats
```

### 健康检查端点
- API Gateway: `http://localhost:8000/health`
- Auth Service: `http://localhost:8001/health`
- 其他服务: `http://localhost:800X/health`

## 8. 故障排除流程

1. **检查服务状态**: `docker compose ps`
2. **查看服务日志**: `docker compose logs [service_name]`
3. **检查资源使用**: `docker stats`
4. **尝试重启服务**: `docker compose restart [service_name]`
5. **降级到轻量化模式**: 使用 `docker-compose.ci.yml`
6. **最后手段**: 使用最小化模式

通过这种分层的部署策略，可以确保在不同环境和资源约束下都能成功部署和测试系统。