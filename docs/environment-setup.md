# 环境变量配置指南

本文档详细说明了 Knowledge RAG 系统的环境变量配置。

## 快速开始

1. 复制环境变量模板文件：
   ```bash
   cp .env.example .env
   ```

2. 编辑 `.env` 文件，填入实际的配置值

3. 启动服务：
   ```bash
   docker-compose up -d
   ```

## 配置文件说明

### `.env.template`
完整的环境变量模板，包含所有可配置的选项和详细说明。适合生产环境使用。

### `.env.example`
简化的环境变量示例，只包含最基本的配置项。适合快速开发和测试。

## 必填配置项

以下配置项是系统运行的必要条件，必须正确配置：

### API 密钥
- `OPENAI_API_KEY`: OpenAI API 密钥，用于 LLM 服务
- `HUGGINGFACE_API_KEY`: HuggingFace API 密钥，用于模型下载
- `JWT_SECRET_KEY`: JWT 令牌签名密钥，用于用户认证

### 数据库连接
- `DATABASE_URL`: PostgreSQL 主数据库连接字符串
- `REDIS_URL`: Redis 缓存数据库连接字符串
- `NEO4J_URI`: Neo4j 图数据库连接字符串
- `NEO4J_USER` / `NEO4J_PASSWORD`: Neo4j 认证信息

## 可选配置项

### 向量数据库
- `WEAVIATE_URL`: Weaviate 向量数据库地址
- `WEAVIATE_API_KEY`: Weaviate API 密钥（如果启用认证）
- `CHROMA_HOST` / `CHROMA_PORT`: ChromaDB 配置
- `FAISS_INDEX_PATH`: FAISS 索引存储路径

### LLM 模型配置
- `OPENAI_MODEL`: 使用的 OpenAI 模型（默认：gpt-3.5-turbo）
- `OPENAI_MAX_TOKENS`: 最大令牌数（默认：4096）
- `OPENAI_TEMPERATURE`: 生成温度（默认：0.7）
- `LOCAL_MODEL_PATH`: 本地模型存储路径

### GraphRAG 配置
- `GRAPHRAG_STORAGE_TYPE`: 存储类型（file/blob）
- `GRAPHRAG_STORAGE_BASE_DIR`: 存储基础目录
- `GRAPHRAG_LLM_MODEL`: GraphRAG 使用的 LLM 模型
- `GRAPHRAG_EMBEDDING_MODEL`: 嵌入模型
- `GRAPHRAG_CHUNK_SIZE`: 文档分块大小
- `GRAPHRAG_CHUNK_OVERLAP`: 分块重叠大小

### 文件存储
- `UPLOAD_DIR`: 文件上传目录
- `MAX_FILE_SIZE`: 最大文件大小
- `ALLOWED_FILE_TYPES`: 允许的文件类型

### 监控和日志
- `PROMETHEUS_ENABLED`: 是否启用 Prometheus 监控
- `JAEGER_ENABLED`: 是否启用 Jaeger 链路追踪
- `LOG_LEVEL`: 日志级别（DEBUG/INFO/WARNING/ERROR）
- `LOG_FORMAT`: 日志格式（json/text）

## 环境特定配置

### 开发环境
```env
ENVIRONMENT=development
DEBUG=true
RELOAD=true
WORKERS=1
LOG_LEVEL=DEBUG
```

### 生产环境
```env
ENVIRONMENT=production
DEBUG=false
RELOAD=false
WORKERS=4
LOG_LEVEL=WARNING
```

## 安全注意事项

1. **永远不要将包含真实密钥的 `.env` 文件提交到版本控制系统**
2. 在生产环境中使用强密码和复杂的密钥
3. 定期轮换 API 密钥和数据库密码
4. 使用环境变量管理工具（如 HashiCorp Vault）管理敏感信息
5. 限制 CORS 源到可信域名

## 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查数据库服务是否运行
   - 验证连接字符串格式
   - 确认用户名和密码正确

2. **API 密钥无效**
   - 检查密钥是否正确复制
   - 验证密钥是否有足够的权限
   - 确认密钥未过期

3. **端口冲突**
   - 检查端口是否被其他服务占用
   - 修改微服务端口配置
   - 更新 docker-compose.yml 中的端口映射

### 调试技巧

1. 启用调试模式：`DEBUG=true`
2. 提高日志级别：`LOG_LEVEL=DEBUG`
3. 检查服务健康状态：访问 `/health` 端点
4. 查看容器日志：`docker-compose logs [service_name]`

## 配置验证

系统启动时会自动验证关键配置项。如果发现配置错误，会在日志中输出详细的错误信息。

建议在部署前使用以下命令验证配置：

```bash
# 检查配置文件语法
docker-compose config

# 验证服务连接
docker-compose up --dry-run
```