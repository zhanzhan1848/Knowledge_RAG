# Knowledge_RAG Architecture Document

## Introduction

This document outlines the overall project architecture for Knowledge_RAG, including backend systems, shared services, and non-UI specific concerns. Its primary goal is to serve as the guiding architectural blueprint for AI-driven development, ensuring consistency and adherence to chosen patterns and technologies.

**Relationship to Frontend Architecture:**
If the project includes a significant user interface, a separate Frontend Architecture Document will detail the frontend-specific design and MUST be used in conjunction with this document. Core technology stack choices documented herein (see "Tech Stack") are definitive for the entire project, including any frontend components.

### Starter Template or Existing Project

**选择决策：FastAPI 微服务模板**

基于项目需求分析，我们选择使用 FastAPI 微服务模板作为基础架构，原因如下：

1. **技术栈匹配**：PRD 中明确指定使用 Python 3.11 + FastAPI 作为主要技术栈
2. **微服务架构支持**：FastAPI 天然支持异步处理和高性能 API 开发
3. **AI/ML 生态兼容**：Python 生态系统对 AI/ML 库支持完善
4. **自动文档生成**：FastAPI 自动生成 OpenAPI/Swagger 文档，符合 PRD 要求
5. **容器化友好**：易于 Docker 化和 Kubernetes 部署

**模板特性：**
- 标准化的项目结构和代码组织
- 内置的依赖注入和配置管理
- 异步数据库连接池
- 统一的错误处理和日志记录
- 自动化测试框架集成
- Docker 和 Kubernetes 配置模板

### Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2024-01-XX | 1.0 | Initial architecture document creation | AI Architect |

## High Level Architecture

### Technical Summary

Knowledge_RAG 采用基于 FastAPI 的微服务架构，专注于构建高性能的智能知识问答系统。系统核心采用 GraphRAG 技术，结合向量检索和知识图谱，实现多模态文档的智能解析和精准问答。架构设计遵循云原生原则，支持水平扩展和容器化部署，通过 API 网关统一管理服务间通信，确保系统的高可用性和可维护性。整体架构支持 PRD 中定义的 8 个核心 Epic，从基础设施建设到高级 AI 功能的完整实现。

### High Level Overview

**架构风格：** 微服务架构（Microservices Architecture）
- **服务拆分原则：** 按业务领域和技术职责划分，每个服务独立部署和扩展
- **通信模式：** 同步 REST API + 异步消息队列
- **数据一致性：** 最终一致性模型，支持分布式事务

**仓库结构：** Monorepo
- **统一代码管理：** 所有微服务在单一仓库中管理
- **共享组件：** 公共库、工具和配置统一维护
- **构建和部署：** 统一的 CI/CD 流水线

**核心用户交互流程：**
1. **文档上传** → 文档处理服务 → 向量化 → 知识图谱构建
2. **智能问答** → API 网关 → 查询引擎 → GraphRAG 检索 → LLM 生成答案
3. **知识管理** → API接口 → 后端服务 → 数据存储层

**关键架构决策：**
- **Python 生态系统：** 利用丰富的 AI/ML 库支持
- **异步处理：** FastAPI + Celery 处理耗时任务
- **多数据库策略：** PostgreSQL + Neo4j + Weaviate + Redis
- **容器化部署：** Docker + Kubernetes 云原生架构

### High Level Project Diagram

```mermaid
graph TB
    %% 客户端层
    User[第三方客户端] --> RestAPI[RESTful API 接口]
    User --> MCPAPI[MCP 协议接口]
    User --> WebhookAPI[Webhook 接口]
    
    %% API 网关层
    RestAPI --> Gateway[API 网关<br/>Kong + Nginx]
    MCPAPI --> Gateway
    WebhookAPI --> Gateway
    
    %% 核心服务层
    Gateway --> AuthService[用户管理服务<br/>Node.js + Express]
    Gateway --> DocService[文档处理服务<br/>Python + FastAPI]
    Gateway --> VectorService[向量检索服务<br/>Python + Weaviate]
    Gateway --> GraphService[知识图谱服务<br/>Python + Neo4j]
    Gateway --> QueryService[查询引擎服务<br/>Python + LangChain]
    Gateway --> NotifyService[通知服务<br/>Python + Redis]
    
    %% 数据存储层
    AuthService --> PostgreSQL[(PostgreSQL<br/>用户数据)]
    DocService --> MinIO[(MinIO/S3<br/>文档存储)]
    VectorService --> Weaviate[(Weaviate<br/>向量数据库)]
    GraphService --> Neo4j[(Neo4j<br/>知识图谱)]
    QueryService --> Redis[(Redis<br/>缓存层)]
    
    %% 外部服务
    QueryService --> LLMService[大语言模型<br/>OpenAI/Claude]
    DocService --> OCRService[OCR 服务<br/>PaddleOCR]
    
    %% 消息队列
    DocService --> MessageQueue[消息队列<br/>Celery + Redis]
    VectorService --> MessageQueue
    GraphService --> MessageQueue
    
    %% 监控和运维
    Gateway --> Monitoring[监控系统<br/>Prometheus + Grafana]
    DocService --> Monitoring
    VectorService --> Monitoring
    GraphService --> Monitoring
    QueryService --> Monitoring
```

## 项目类型确认

**重要决策：纯后端API系统**

根据用户明确要求，本项目将构建为：
- ✅ **纯后端API接口系统**
- ❌ 不包含前端界面
- ❌ 不包含Web UI组件
- ✅ 专注于RESTful API设计
- ✅ 支持第三方系统集成

### Architectural and Design Patterns

基于 FastAPI 微服务模板和项目需求，我推荐以下架构和设计模式：

**1. 微服务架构模式 (Microservices Pattern)**
- **描述：** 将应用拆分为独立的、可部署的服务
- **理由：** 符合 PRD 要求，支持独立扩展和技术栈选择，便于团队协作

**2. API 网关模式 (API Gateway Pattern)**
- **描述：** 使用 Kong 作为统一入口，处理路由、认证、限流
- **理由：** 简化客户端复杂性，提供统一的安全和监控点

**3. 仓储模式 (Repository Pattern)**
- **描述：** 抽象数据访问逻辑，支持多种数据源
- **理由：** 便于测试和数据源切换，符合 FastAPI 最佳实践

**4. 事件驱动架构 (Event-Driven Architecture)**
- **描述：** 使用 Celery + Redis 处理异步任务和服务间通信
- **理由：** 支持文档处理等耗时操作，提高系统响应性

**5. CQRS 模式 (Command Query Responsibility Segregation)**
- **描述：** 读写操作分离，优化查询性能
- **理由：** 适合知识检索场景，支持复杂的 GraphRAG 查询

**6. 依赖注入模式 (Dependency Injection)**
- **描述：** FastAPI 内置 DI 容器，管理服务依赖
- **理由：** 提高代码可测试性和可维护性

**7. 断路器模式 (Circuit Breaker Pattern)**
- **描述：** 保护系统免受外部服务故障影响
- **理由：** 提高系统稳定性，特别是对 LLM API 调用

✅ **架构模式已确认**

## 技术栈选择

基于Knowledge_RAG项目需求、性能要求和架构模式，推荐以下技术栈：

### 核心开发语言和框架

**后端API框架**
- **Python 3.11+** - 主要开发语言
- **FastAPI 0.104+** - 高性能异步Web框架
- **Pydantic 2.5+** - 数据验证和序列化
- **Uvicorn 0.24+** - ASGI服务器

**异步处理**
- **Celery 5.3+** - 分布式任务队列
- **Redis 7.2+** - 消息代理和缓存

### 数据存储层

**向量数据库**
- **Weaviate 1.22+** - 向量存储和检索
- **OpenAI Embeddings** - 文本向量化

**图数据库**
- **Neo4j 5.13+** - 知识图谱存储
- **py2neo 2021.2+** - Python Neo4j驱动

**关系数据库**
- **PostgreSQL 16+** - 主数据库
- **SQLAlchemy 2.0+** - ORM框架
- **Alembic 1.12+** - 数据库迁移

**对象存储**
- **MinIO** - 文档文件存储
- **boto3** - AWS S3兼容客户端

### API网关和服务发现

**API网关**
- **Kong 3.4+** - API网关
- **Nginx 1.25+** - 反向代理和负载均衡

### AI/ML集成

**大语言模型**
- **LangChain 0.1+** - LLM应用框架
- **OpenAI GPT-4** - 主要LLM服务
- **Anthropic Claude** - 备用LLM服务

**文档处理**
- **PyPDF2/pdfplumber** - PDF处理
- **python-docx** - Word文档处理
- **openpyxl** - Excel处理
- **Tesseract OCR** - 图像文字识别

### 容器化和编排

**容器技术**
- **Docker 24+** - 容器化
- **Docker Compose 2.21+** - 本地开发环境
- **Kubernetes 1.28+** - 生产环境编排
- **Helm 3.13+** - Kubernetes包管理

### 监控和日志

**应用监控**
- **Prometheus 2.47+** - 指标收集
- **Grafana 10.2+** - 监控仪表板
- **Jaeger 1.50+** - 分布式链路追踪

**日志管理**
- **ELK Stack** (Elasticsearch + Logstash + Kibana)
- **Fluentd** - 日志收集

### 开发工具链

**代码质量**
- **Black** - 代码格式化
- **isort** - 导入排序
- **flake8** - 代码检查
- **mypy** - 类型检查
- **pytest** - 单元测试
- **coverage** - 测试覆盖率

**API文档**
- **OpenAPI 3.0** - API规范
- **FastAPI Docs** - 自动生成文档
- **Redoc** - 备用API文档生成器

### 安全组件

**认证授权**
- **JWT** - 令牌认证
- **OAuth 2.0** - 第三方认证
- **bcrypt** - 密码哈希

**安全扫描**
- **bandit** - Python安全扫描
- **safety** - 依赖安全检查

### 版本固定说明

所有依赖版本将在`requirements.txt`中固定，确保：
- 生产环境稳定性
- 可重现的构建
- 安全漏洞控制
- 团队开发一致性

✅ **技术栈已确认**

## 组件设计

基于微服务架构和确认的技术栈，Knowledge_RAG系统将拆分为以下核心组件：

### 1. API网关服务 (api-gateway)

**职责**
- 统一API入口点和路由管理
- 请求认证和授权
- 限流和熔断保护
- API版本管理
- 请求/响应日志记录

**技术栈**
- Kong 3.4+ (API网关)
- Nginx 1.25+ (负载均衡)
- Redis (会话存储)

**接口**
- 外部API: `/api/v1/*` (RESTful)
- 内部路由: 转发到各微服务

**依赖**
- 所有后端微服务
- Redis (会话和缓存)
- 认证服务

### 2. 用户管理服务 (user-service)

**职责**
- 用户注册、登录、注销
- 用户信息管理
- 权限和角色管理
- JWT令牌生成和验证
- 用户行为审计

**技术栈**
- FastAPI 0.104+
- PostgreSQL (用户数据)
- Redis (会话缓存)
- bcrypt (密码哈希)
- JWT (令牌认证)

**接口**
```
POST /auth/register     # 用户注册
POST /auth/login        # 用户登录
POST /auth/logout       # 用户注销
GET  /auth/profile      # 获取用户信息
PUT  /auth/profile      # 更新用户信息
POST /auth/refresh      # 刷新令牌
```

**依赖**
- PostgreSQL
- Redis

### 3. 文档处理服务 (document-service)

**职责**
- 文档上传和存储管理
- 多格式文档解析 (PDF/Word/Excel)
- 文本提取和预处理
- OCR图像文字识别
- 文档元数据管理

**技术栈**
- FastAPI 0.104+
- Celery 5.3+ (异步任务)
- MinIO (文件存储)
- PyPDF2/pdfplumber (PDF处理)
- python-docx (Word处理)
- Tesseract OCR
- PostgreSQL (元数据)

**接口**
```
POST /documents/upload           # 上传文档
GET  /documents/{doc_id}         # 获取文档信息
DELETE /documents/{doc_id}       # 删除文档
GET  /documents/{doc_id}/content # 获取文档内容
POST /documents/{doc_id}/process # 触发文档处理
GET  /documents/                 # 文档列表
```

**依赖**
- MinIO (对象存储)
- PostgreSQL (元数据)
- Redis (任务队列)
- 向量化服务

### 4. 向量化服务 (embedding-service)

**职责**
- 文本向量化处理
- 向量数据存储和索引
- 语义相似度计算
- 向量检索和排序
- 嵌入模型管理

**技术栈**
- FastAPI 0.104+
- Weaviate 1.22+ (向量数据库)
- OpenAI Embeddings API
- sentence-transformers (备用模型)
- numpy (向量计算)

**接口**
```
POST /embeddings/create          # 创建文本向量
POST /embeddings/search          # 向量相似度搜索
GET  /embeddings/{doc_id}        # 获取文档向量
DELETE /embeddings/{doc_id}      # 删除文档向量
POST /embeddings/batch           # 批量向量化
```

**依赖**
- Weaviate
- OpenAI API
- 文档处理服务

### 5. 知识图谱服务 (knowledge-graph-service)

**职责**
- 实体识别和关系抽取
- 知识图谱构建和维护
- 图数据查询和遍历
- 实体链接和消歧
- 图谱可视化数据

**技术栈**
- FastAPI 0.104+
- Neo4j 5.13+ (图数据库)
- py2neo 2021.2+ (Neo4j驱动)
- spaCy (NLP处理)
- LangChain (实体抽取)

**接口**
```
POST /graph/entities             # 创建实体
POST /graph/relationships        # 创建关系
GET  /graph/entities/{entity_id} # 获取实体信息
POST /graph/query                # Cypher查询
GET  /graph/neighbors/{entity_id}# 获取邻居节点
POST /graph/extract              # 从文本抽取实体关系
```

**依赖**
- Neo4j
- 文档处理服务
- LLM服务

### 6. 查询引擎服务 (query-service)

**职责**
- 自然语言查询理解
- 多模态检索策略
- RAG流程编排
- 答案生成和后处理
- 查询历史管理

**技术栈**
- FastAPI 0.104+
- LangChain 0.1+
- OpenAI GPT-4
- Anthropic Claude (备用)
- PostgreSQL (查询历史)

**接口**
```
POST /query/ask                  # 提交问题
GET  /query/{query_id}           # 获取查询结果
GET  /query/history              # 查询历史
POST /query/feedback             # 结果反馈
POST /query/stream               # 流式查询
```

**依赖**
- 向量化服务
- 知识图谱服务
- LLM API
- PostgreSQL

### 7. 通知服务 (notification-service)

**职责**
- 异步消息处理
- 任务状态通知
- 系统事件广播
- 邮件和推送通知
- 消息队列管理

**技术栈**
- FastAPI 0.104+
- Celery 5.3+
- Redis (消息队列)
- SMTP (邮件发送)

**接口**
```
POST /notifications/send         # 发送通知
GET  /notifications/             # 获取通知列表
PUT  /notifications/{id}/read    # 标记已读
POST /notifications/subscribe    # 订阅通知
```

**依赖**
- Redis
- SMTP服务器

### 组件交互图

```mermaid
graph TB
    Client[客户端] --> Gateway[API网关]
    Gateway --> Auth[用户管理服务]
    Gateway --> Doc[文档处理服务]
    Gateway --> Query[查询引擎服务]
    
    Doc --> Storage[MinIO存储]
    Doc --> Embed[向量化服务]
    Doc --> Graph[知识图谱服务]
    
    Embed --> Weaviate[Weaviate向量库]
    Graph --> Neo4j[Neo4j图数据库]
    
    Query --> Embed
    Query --> Graph
    Query --> LLM[LLM API]
    
    Auth --> PG[(PostgreSQL)]
    Doc --> PG
    Query --> PG
    
    Notify[通知服务] --> Redis[(Redis)]
    Doc --> Notify
    Query --> Notify
    
    Gateway --> Redis
    Auth --> Redis
```

✅ **组件设计已确认**

---

# 数据模型设计

## 核心数据模型概述

基于微服务架构和业务需求，我们定义以下核心数据模型：

### 1. 用户管理服务数据模型

#### User（用户）
```python
class User(BaseModel):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    username: str = Field(max_length=50, unique=True, index=True)
    email: str = Field(max_length=100, unique=True, index=True)
    password_hash: str = Field(max_length=255)
    full_name: Optional[str] = Field(max_length=100)
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)
    role: UserRole = Field(default=UserRole.USER)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
```

#### UserRole（用户角色）
```python
class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"
```

#### UserSession（用户会话）
```python
class UserSession(BaseModel):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id")
    token: str = Field(max_length=500, unique=True)
    expires_at: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True)
```

### 2. 文档处理服务数据模型

#### Document（文档）
```python
class Document(BaseModel):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id")
    filename: str = Field(max_length=255)
    original_filename: str = Field(max_length=255)
    file_path: str = Field(max_length=500)
    file_size: int
    mime_type: str = Field(max_length=100)
    file_hash: str = Field(max_length=64, unique=True)  # SHA-256
    status: DocumentStatus = Field(default=DocumentStatus.UPLOADED)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
```

#### DocumentStatus（文档状态）
```python
class DocumentStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    DELETED = "deleted"
```

#### DocumentMetadata（文档元数据）
```python
class DocumentMetadata(BaseModel):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    document_id: UUID = Field(foreign_key="document.id")
    title: Optional[str] = Field(max_length=500)
    author: Optional[str] = Field(max_length=200)
    subject: Optional[str] = Field(max_length=500)
    keywords: Optional[List[str]] = Field(default_factory=list)
    language: Optional[str] = Field(max_length=10)
    page_count: Optional[int]
    word_count: Optional[int]
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

#### DocumentChunk（文档分块）
```python
class DocumentChunk(BaseModel):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    document_id: UUID = Field(foreign_key="document.id")
    chunk_index: int
    content: str = Field(max_length=4000)  # 文本内容
    content_type: ChunkType = Field(default=ChunkType.TEXT)
    page_number: Optional[int]
    position: Optional[Dict[str, Any]]  # 位置信息
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

#### ChunkType（分块类型）
```python
class ChunkType(str, Enum):
    TEXT = "text"
    TABLE = "table"
    IMAGE = "image"
    HEADER = "header"
    FOOTER = "footer"
```

### 3. 向量化服务数据模型

#### EmbeddingVector（向量）
```python
class EmbeddingVector(BaseModel):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    chunk_id: UUID = Field(foreign_key="document_chunk.id")
    vector: List[float] = Field(max_length=1536)  # OpenAI embedding维度
    model_name: str = Field(max_length=100)  # 使用的模型名称
    vector_dimension: int = Field(default=1536)
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

#### SemanticSearch（语义搜索记录）
```python
class SemanticSearch(BaseModel):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id")
    query: str = Field(max_length=1000)
    query_vector: List[float]
    results: List[Dict[str, Any]]  # 搜索结果
    similarity_threshold: float = Field(default=0.7)
    max_results: int = Field(default=10)
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

### 4. 知识图谱服务数据模型

#### Entity（实体）
```python
class Entity(BaseModel):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(max_length=200, index=True)
    entity_type: EntityType
    description: Optional[str] = Field(max_length=1000)
    properties: Dict[str, Any] = Field(default_factory=dict)
    confidence_score: float = Field(ge=0.0, le=1.0)
    source_document_id: UUID = Field(foreign_key="document.id")
    source_chunk_id: UUID = Field(foreign_key="document_chunk.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

#### EntityType（实体类型）
```python
class EntityType(str, Enum):
    PERSON = "person"
    ORGANIZATION = "organization"
    LOCATION = "location"
    EVENT = "event"
    CONCEPT = "concept"
    PRODUCT = "product"
    DATE = "date"
    MONEY = "money"
    OTHER = "other"
```

#### Relationship（关系）
```python
class Relationship(BaseModel):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    source_entity_id: UUID = Field(foreign_key="entity.id")
    target_entity_id: UUID = Field(foreign_key="entity.id")
    relationship_type: str = Field(max_length=100)
    description: Optional[str] = Field(max_length=500)
    confidence_score: float = Field(ge=0.0, le=1.0)
    properties: Dict[str, Any] = Field(default_factory=dict)
    source_document_id: UUID = Field(foreign_key="document.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

### 5. 查询引擎服务数据模型

#### QuerySession（查询会话）
```python
class QuerySession(BaseModel):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id")
    session_name: Optional[str] = Field(max_length=200)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True)
```

#### Query（查询）
```python
class Query(BaseModel):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    session_id: UUID = Field(foreign_key="query_session.id")
    user_id: UUID = Field(foreign_key="user.id")
    question: str = Field(max_length=2000)
    query_type: QueryType = Field(default=QueryType.GENERAL)
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

#### QueryType（查询类型）
```python
class QueryType(str, Enum):
    GENERAL = "general"          # 一般问答
    SEMANTIC = "semantic"        # 语义搜索
    GRAPH = "graph"              # 图谱查询
    SUMMARY = "summary"          # 文档摘要
    COMPARISON = "comparison"    # 对比分析
```

#### Answer（答案）
```python
class Answer(BaseModel):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    query_id: UUID = Field(foreign_key="query.id")
    content: str = Field(max_length=5000)
    confidence_score: float = Field(ge=0.0, le=1.0)
    sources: List[Dict[str, Any]] = Field(default_factory=list)  # 引用来源
    model_used: str = Field(max_length=100)
    tokens_used: Optional[int]
    processing_time: Optional[float]  # 处理时间（秒）
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

### 6. 通知服务数据模型

#### Notification（通知）
```python
class Notification(BaseModel):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id")
    title: str = Field(max_length=200)
    message: str = Field(max_length=1000)
    notification_type: NotificationType
    priority: NotificationPriority = Field(default=NotificationPriority.NORMAL)
    is_read: bool = Field(default=False)
    data: Optional[Dict[str, Any]] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    read_at: Optional[datetime] = None
```

#### NotificationType（通知类型）
```python
class NotificationType(str, Enum):
    DOCUMENT_PROCESSED = "document_processed"
    QUERY_COMPLETED = "query_completed"
    SYSTEM_ALERT = "system_alert"
    USER_ACTION = "user_action"
    ERROR = "error"
```

#### NotificationPriority（通知优先级）
```python
class NotificationPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"
```

## 数据模型关系图

```mermaid
erDiagram
    User ||--o{ Document : uploads
    User ||--o{ QuerySession : creates
    User ||--o{ Notification : receives
    User ||--o{ UserSession : has
    
    Document ||--o{ DocumentMetadata : has
    Document ||--o{ DocumentChunk : contains
    Document ||--o{ Entity : extracts
    
    DocumentChunk ||--|| EmbeddingVector : generates
    DocumentChunk ||--o{ Entity : contains
    
    Entity ||--o{ Relationship : source
    Entity ||--o{ Relationship : target
    
    QuerySession ||--o{ Query : contains
    Query ||--|| Answer : generates
    
    User {
        UUID id PK
        string username
        string email
        string password_hash
        string full_name
        boolean is_active
        UserRole role
        datetime created_at
    }
    
    Document {
        UUID id PK
        UUID user_id FK
        string filename
        string file_path
        int file_size
        DocumentStatus status
        datetime created_at
    }
    
    Entity {
        UUID id PK
        string name
        EntityType entity_type
        string description
        float confidence_score
        UUID source_document_id FK
        datetime created_at
    }
    
    Query {
        UUID id PK
        UUID session_id FK
        UUID user_id FK
        string question
        QueryType query_type
        datetime created_at
    }
```

## 数据模型设计原则

### 1. 一致性原则
- 所有主键使用UUID格式
- 统一的时间戳字段命名（created_at, updated_at）
- 一致的状态枚举定义
- 统一的外键命名规范

### 2. 可扩展性原则
- 使用JSON字段存储动态属性（properties, data）
- 预留扩展字段
- 支持多版本数据结构

### 3. 性能优化原则
- 关键查询字段添加索引
- 合理的字段长度限制
- 分离热数据和冷数据

### 4. 数据完整性原则
- 外键约束确保引用完整性
- 非空约束确保必要数据
- 唯一约束防止重复数据

### 5. 安全性原则
- 密码字段使用哈希存储
- 敏感数据字段标识
- 审计日志字段

## 数据模型确认

✅ **数据模型设计已完成**

---

# API规范设计

## API设计原则

### 1. RESTful设计原则
- 使用标准HTTP方法（GET, POST, PUT, DELETE, PATCH）
- 资源导向的URL设计
- 统一的响应格式
- 合理的HTTP状态码使用

### 2. 版本控制
- API版本通过URL路径控制：`/api/v1/`
- 向后兼容性保证
- 废弃API的优雅过渡

### 3. 安全性
- JWT Token认证
- API密钥管理
- 请求频率限制
- 输入数据验证

### 4. 性能优化
- 分页查询支持
- 字段选择器
- 缓存策略
- 异步处理支持

## 统一响应格式

### 成功响应格式
```json
{
  "success": true,
  "data": {},
  "message": "操作成功",
  "timestamp": "2024-01-15T10:30:00Z",
  "request_id": "req_123456789"
}
```

### 错误响应格式
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "请求参数验证失败",
    "details": [
      {
        "field": "email",
        "message": "邮箱格式不正确"
      }
    ]
  },
  "timestamp": "2024-01-15T10:30:00Z",
  "request_id": "req_123456789"
}
```

### 分页响应格式
```json
{
  "success": true,
  "data": {
    "items": [],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total_items": 100,
      "total_pages": 5,
      "has_next": true,
      "has_prev": false
    }
  },
  "message": "查询成功",
  "timestamp": "2024-01-15T10:30:00Z",
  "request_id": "req_123456789"
}
```

## 微服务API规范

### 1. 用户管理服务 API

**基础路径**: `/api/v1/users`

#### 用户认证
```yaml
# 用户注册
POST /api/v1/auth/register
Content-Type: application/json

Request Body:
{
  "username": "string",
  "email": "string",
  "password": "string",
  "full_name": "string"
}

Response: 201 Created
{
  "success": true,
  "data": {
    "user_id": "uuid",
    "username": "string",
    "email": "string",
    "role": "user"
  }
}

# 用户登录
POST /api/v1/auth/login
Content-Type: application/json

Request Body:
{
  "username": "string",
  "password": "string"
}

Response: 200 OK
{
  "success": true,
  "data": {
    "access_token": "string",
    "token_type": "bearer",
    "expires_in": 3600,
    "user": {
      "id": "uuid",
      "username": "string",
      "email": "string",
      "role": "user"
    }
  }
}

# 刷新Token
POST /api/v1/auth/refresh
Authorization: Bearer <token>

Response: 200 OK
{
  "success": true,
  "data": {
    "access_token": "string",
    "expires_in": 3600
  }
}

# 用户登出
POST /api/v1/auth/logout
Authorization: Bearer <token>

Response: 200 OK
{
  "success": true,
  "message": "登出成功"
}
```

#### 用户管理
```yaml
# 获取当前用户信息
GET /api/v1/users/me
Authorization: Bearer <token>

Response: 200 OK
{
  "success": true,
  "data": {
    "id": "uuid",
    "username": "string",
    "email": "string",
    "full_name": "string",
    "role": "user",
    "is_active": true,
    "created_at": "2024-01-15T10:30:00Z",
    "last_login": "2024-01-15T10:30:00Z"
  }
}

# 更新用户信息
PUT /api/v1/users/me
Authorization: Bearer <token>
Content-Type: application/json

Request Body:
{
  "full_name": "string",
  "email": "string"
}

Response: 200 OK
{
  "success": true,
  "data": {
    "id": "uuid",
    "username": "string",
    "email": "string",
    "full_name": "string",
    "updated_at": "2024-01-15T10:30:00Z"
  }
}

# 修改密码
PUT /api/v1/users/me/password
Authorization: Bearer <token>
Content-Type: application/json

Request Body:
{
  "current_password": "string",
  "new_password": "string"
}

Response: 200 OK
{
  "success": true,
  "message": "密码修改成功"
}
```

### 2. 文档处理服务 API

**基础路径**: `/api/v1/documents`

#### 文档管理
```yaml
# 上传文档
POST /api/v1/documents/upload
Authorization: Bearer <token>
Content-Type: multipart/form-data

Request Body:
- file: binary
- metadata: json (optional)

Response: 201 Created
{
  "success": true,
  "data": {
    "document_id": "uuid",
    "filename": "string",
    "file_size": 1024,
    "mime_type": "application/pdf",
    "status": "uploaded",
    "created_at": "2024-01-15T10:30:00Z"
  }
}

# 获取文档列表
GET /api/v1/documents
Authorization: Bearer <token>
Query Parameters:
- page: int (default: 1)
- page_size: int (default: 20)
- status: string (optional)
- search: string (optional)

Response: 200 OK
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "uuid",
        "filename": "string",
        "file_size": 1024,
        "status": "processed",
        "created_at": "2024-01-15T10:30:00Z",
        "processed_at": "2024-01-15T10:35:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total_items": 50,
      "total_pages": 3
    }
  }
}

# 获取文档详情
GET /api/v1/documents/{document_id}
Authorization: Bearer <token>

Response: 200 OK
{
  "success": true,
  "data": {
    "id": "uuid",
    "filename": "string",
    "original_filename": "string",
    "file_size": 1024,
    "mime_type": "application/pdf",
    "status": "processed",
    "metadata": {
      "title": "string",
      "author": "string",
      "page_count": 10,
      "word_count": 5000
    },
    "created_at": "2024-01-15T10:30:00Z",
    "processed_at": "2024-01-15T10:35:00Z"
  }
}

# 删除文档
DELETE /api/v1/documents/{document_id}
Authorization: Bearer <token>

Response: 200 OK
{
  "success": true,
  "message": "文档删除成功"
}

# 获取文档处理状态
GET /api/v1/documents/{document_id}/status
Authorization: Bearer <token>

Response: 200 OK
{
  "success": true,
  "data": {
    "document_id": "uuid",
    "status": "processing",
    "progress": 75,
    "message": "正在提取文本内容",
    "updated_at": "2024-01-15T10:33:00Z"
  }
}
```

#### 文档分块管理
```yaml
# 获取文档分块
GET /api/v1/documents/{document_id}/chunks
Authorization: Bearer <token>
Query Parameters:
- page: int (default: 1)
- page_size: int (default: 20)
- content_type: string (optional)

Response: 200 OK
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "uuid",
        "chunk_index": 1,
        "content": "string",
        "content_type": "text",
        "page_number": 1,
        "created_at": "2024-01-15T10:35:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total_items": 100
    }
  }
}
```

### 3. 向量化服务 API

**基础路径**: `/api/v1/embeddings`

#### 向量化操作
```yaml
# 文本向量化
POST /api/v1/embeddings/encode
Authorization: Bearer <token>
Content-Type: application/json

Request Body:
{
  "text": "string",
  "model": "text-embedding-ada-002"
}

Response: 200 OK
{
  "success": true,
  "data": {
    "vector": [0.1, 0.2, ...],
    "dimension": 1536,
    "model": "text-embedding-ada-002"
  }
}

# 语义搜索
POST /api/v1/embeddings/search
Authorization: Bearer <token>
Content-Type: application/json

Request Body:
{
  "query": "string",
  "similarity_threshold": 0.7,
  "max_results": 10,
  "document_ids": ["uuid1", "uuid2"] // optional
}

Response: 200 OK
{
  "success": true,
  "data": {
    "query": "string",
    "results": [
      {
        "chunk_id": "uuid",
        "document_id": "uuid",
        "content": "string",
        "similarity_score": 0.85,
        "metadata": {
          "page_number": 1,
          "chunk_index": 1
        }
      }
    ],
    "total_results": 5,
    "search_time": 0.123
  }
}
```

### 4. 知识图谱服务 API

**基础路径**: `/api/v1/knowledge-graph`

#### 实体管理
```yaml
# 获取实体列表
GET /api/v1/knowledge-graph/entities
Authorization: Bearer <token>
Query Parameters:
- page: int (default: 1)
- page_size: int (default: 20)
- entity_type: string (optional)
- search: string (optional)
- document_id: uuid (optional)

Response: 200 OK
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "uuid",
        "name": "string",
        "entity_type": "person",
        "description": "string",
        "confidence_score": 0.95,
        "properties": {},
        "created_at": "2024-01-15T10:30:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total_items": 200
    }
  }
}

# 获取实体详情
GET /api/v1/knowledge-graph/entities/{entity_id}
Authorization: Bearer <token>

Response: 200 OK
{
  "success": true,
  "data": {
    "id": "uuid",
    "name": "string",
    "entity_type": "person",
    "description": "string",
    "confidence_score": 0.95,
    "properties": {},
    "relationships": [
      {
        "id": "uuid",
        "target_entity": {
          "id": "uuid",
          "name": "string",
          "entity_type": "organization"
        },
        "relationship_type": "works_for",
        "confidence_score": 0.88
      }
    ],
    "source_documents": [
      {
        "document_id": "uuid",
        "filename": "string"
      }
    ],
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

#### 关系查询
```yaml
# 获取关系列表
GET /api/v1/knowledge-graph/relationships
Authorization: Bearer <token>
Query Parameters:
- page: int (default: 1)
- page_size: int (default: 20)
- relationship_type: string (optional)
- entity_id: uuid (optional)

Response: 200 OK
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "uuid",
        "source_entity": {
          "id": "uuid",
          "name": "string",
          "entity_type": "person"
        },
        "target_entity": {
          "id": "uuid",
          "name": "string",
          "entity_type": "organization"
        },
        "relationship_type": "works_for",
        "confidence_score": 0.88,
        "created_at": "2024-01-15T10:30:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total_items": 500
    }
  }
}

# 图谱查询
POST /api/v1/knowledge-graph/query
Authorization: Bearer <token>
Content-Type: application/json

Request Body:
{
  "query": "MATCH (p:Person)-[r:WORKS_FOR]->(o:Organization) RETURN p, r, o LIMIT 10",
  "parameters": {}
}

Response: 200 OK
{
  "success": true,
  "data": {
    "nodes": [
      {
        "id": "uuid",
        "labels": ["Person"],
        "properties": {
          "name": "string",
          "entity_type": "person"
        }
      }
    ],
    "relationships": [
      {
        "id": "uuid",
        "type": "WORKS_FOR",
        "source_id": "uuid",
        "target_id": "uuid",
        "properties": {}
      }
    ],
    "query_time": 0.045
  }
}
```

### 5. 查询引擎服务 API

**基础路径**: `/api/v1/query`

#### 智能问答
```yaml
# 创建查询会话
POST /api/v1/query/sessions
Authorization: Bearer <token>
Content-Type: application/json

Request Body:
{
  "session_name": "string"
}

Response: 201 Created
{
  "success": true,
  "data": {
    "session_id": "uuid",
    "session_name": "string",
    "created_at": "2024-01-15T10:30:00Z"
  }
}

# 获取查询会话列表
GET /api/v1/query/sessions
Authorization: Bearer <token>
Query Parameters:
- page: int (default: 1)
- page_size: int (default: 20)
- is_active: boolean (optional)

Response: 200 OK
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "uuid",
        "session_name": "string",
        "is_active": true,
        "query_count": 5,
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-01-15T11:00:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total_items": 10
    }
  }
}

# 提交查询
POST /api/v1/query/sessions/{session_id}/ask
Authorization: Bearer <token>
Content-Type: application/json

Request Body:
{
  "question": "string",
  "query_type": "general",
  "context": {
    "document_ids": ["uuid1", "uuid2"],
    "max_sources": 5,
    "temperature": 0.7
  }
}

Response: 200 OK
{
  "success": true,
  "data": {
    "query_id": "uuid",
    "question": "string",
    "answer": {
      "content": "string",
      "confidence_score": 0.92,
      "sources": [
        {
          "document_id": "uuid",
          "document_name": "string",
          "chunk_id": "uuid",
          "content": "string",
          "page_number": 1,
          "similarity_score": 0.85
        }
      ],
      "model_used": "gpt-4",
      "tokens_used": 150,
      "processing_time": 2.34
    },
    "created_at": "2024-01-15T10:30:00Z"
  }
}

# 获取会话历史
GET /api/v1/query/sessions/{session_id}/history
Authorization: Bearer <token>
Query Parameters:
- page: int (default: 1)
- page_size: int (default: 20)

Response: 200 OK
{
  "success": true,
  "data": {
    "items": [
      {
        "query_id": "uuid",
        "question": "string",
        "answer": {
          "content": "string",
          "confidence_score": 0.92
        },
        "query_type": "general",
        "created_at": "2024-01-15T10:30:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total_items": 15
    }
  }
}
```

### 6. 通知服务 API

**基础路径**: `/api/v1/notifications`

#### 通知管理
```yaml
# 获取通知列表
GET /api/v1/notifications
Authorization: Bearer <token>
Query Parameters:
- page: int (default: 1)
- page_size: int (default: 20)
- is_read: boolean (optional)
- notification_type: string (optional)
- priority: string (optional)

Response: 200 OK
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "uuid",
        "title": "string",
        "message": "string",
        "notification_type": "document_processed",
        "priority": "normal",
        "is_read": false,
        "data": {
          "document_id": "uuid",
          "document_name": "string"
        },
        "created_at": "2024-01-15T10:30:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total_items": 25
    },
    "unread_count": 5
  }
}

# 标记通知为已读
PUT /api/v1/notifications/{notification_id}/read
Authorization: Bearer <token>

Response: 200 OK
{
  "success": true,
  "message": "通知已标记为已读"
}

# 批量标记通知为已读
PUT /api/v1/notifications/mark-read
Authorization: Bearer <token>
Content-Type: application/json

Request Body:
{
  "notification_ids": ["uuid1", "uuid2"]
}

Response: 200 OK
{
  "success": true,
  "message": "批量标记成功",
  "data": {
    "marked_count": 2
  }
}

# 获取未读通知数量
GET /api/v1/notifications/unread-count
Authorization: Bearer <token>

Response: 200 OK
{
  "success": true,
  "data": {
    "unread_count": 5,
    "by_priority": {
      "urgent": 1,
      "high": 2,
      "normal": 2,
      "low": 0
    }
  }
}
```

## API网关路由配置

### 路由规则
```yaml
# Kong Gateway 路由配置示例
routes:
  # 用户服务路由
  - name: user-service
    paths: ["/api/v1/auth", "/api/v1/users"]
    service: user-service
    plugins:
      - name: jwt
      - name: rate-limiting
        config:
          minute: 100
          hour: 1000
  
  # 文档服务路由
  - name: document-service
    paths: ["/api/v1/documents"]
    service: document-service
    plugins:
      - name: jwt
      - name: file-log
      - name: request-size-limiting
        config:
          allowed_payload_size: 100
  
  # 向量化服务路由
  - name: embedding-service
    paths: ["/api/v1/embeddings"]
    service: embedding-service
    plugins:
      - name: jwt
      - name: rate-limiting
        config:
          minute: 50
  
  # 知识图谱服务路由
  - name: knowledge-graph-service
    paths: ["/api/v1/knowledge-graph"]
    service: knowledge-graph-service
    plugins:
      - name: jwt
      - name: response-transformer
  
  # 查询引擎服务路由
  - name: query-service
    paths: ["/api/v1/query"]
    service: query-service
    plugins:
      - name: jwt
      - name: rate-limiting
        config:
          minute: 30
  
  # 通知服务路由
  - name: notification-service
    paths: ["/api/v1/notifications"]
    service: notification-service
    plugins:
      - name: jwt
```

## API文档生成

### OpenAPI 3.0规范
- 使用FastAPI自动生成OpenAPI文档
- API文档服务：`/docs`
- ReDoc文档：`/redoc`
- OpenAPI规范：`/openapi.json`

### 文档内容
- 完整的API端点描述
- 请求/响应模型定义
- 认证方式说明
- 错误码参考
- 使用示例

## API安全规范

### 认证授权
- JWT Token认证
- Token过期时间：1小时
- Refresh Token机制
- 角色权限控制

### 数据验证
- 请求参数验证
- 数据类型检查
- 长度限制
- 格式验证

### 安全头部
```yaml
Security Headers:
- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY
- X-XSS-Protection: 1; mode=block
- Strict-Transport-Security: max-age=31536000
- Content-Security-Policy: default-src 'self'
```

## API规范确认

✅ **API规范设计已完成**

---

# 数据库架构设计

## 数据库架构概览

### 多数据库架构策略

Knowledge_RAG系统采用多数据库架构，针对不同的数据类型和访问模式选择最适合的数据库技术：

```mermaid
graph TB
    subgraph "应用层"
        A[API Gateway]
        B[User Service]
        C[Document Service]
        D[Embedding Service]
        E[Knowledge Graph Service]
        F[Query Service]
        G[Notification Service]
    end
    
    subgraph "数据存储层"
        H[(PostgreSQL<br/>关系型数据)]
        I[(Weaviate<br/>向量数据库)]
        J[(Neo4j<br/>图数据库)]
        K[(MinIO<br/>对象存储)]
        L[(Redis<br/>缓存/队列)]
    end
    
    B --> H
    C --> H
    C --> K
    D --> I
    D --> H
    E --> J
    E --> H
    F --> H
    F --> I
    F --> J
    G --> H
    
    B --> L
    C --> L
    D --> L
    E --> L
    F --> L
    G --> L
```

### 数据库选择原则

1. **PostgreSQL**: 结构化数据、事务性操作、复杂查询
2. **Weaviate**: 向量存储、语义搜索、相似度计算
3. **Neo4j**: 图数据、关系查询、知识图谱
4. **MinIO**: 文件存储、大对象、静态资源
5. **Redis**: 缓存、会话、消息队列

## PostgreSQL 数据库设计

### 数据库分片策略

```sql
-- 主数据库：用户、文档元数据、查询记录
CREATE DATABASE knowledge_rag_main;

-- 通知数据库：通知、消息队列
CREATE DATABASE knowledge_rag_notifications;

-- 日志数据库：系统日志、审计记录
CREATE DATABASE knowledge_rag_logs;
```

### 主数据库表结构

#### 用户管理表
```sql
-- 用户表
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    role user_role_enum DEFAULT 'user',
    is_active BOOLEAN DEFAULT true,
    email_verified BOOLEAN DEFAULT false,
    last_login TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 用户角色枚举
CREATE TYPE user_role_enum AS ENUM ('admin', 'user', 'guest');

-- 用户会话表
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    refresh_token VARCHAR(255) UNIQUE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_active BOOLEAN DEFAULT true,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_user_sessions_token ON user_sessions(session_token);
CREATE INDEX idx_user_sessions_expires ON user_sessions(expires_at);
```

#### 文档管理表
```sql
-- 文档状态枚举
CREATE TYPE document_status_enum AS ENUM (
    'uploaded', 'processing', 'processed', 'failed', 'deleted'
);

-- 文档表
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size BIGINT NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    file_hash VARCHAR(64) UNIQUE NOT NULL,
    status document_status_enum DEFAULT 'uploaded',
    metadata JSONB DEFAULT '{}',
    processing_progress INTEGER DEFAULT 0,
    processing_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP WITH TIME ZONE
);

-- 文档分块表
CREATE TABLE document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    content_type VARCHAR(50) DEFAULT 'text',
    page_number INTEGER,
    start_char INTEGER,
    end_char INTEGER,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(document_id, chunk_index)
);

-- 索引
CREATE INDEX idx_documents_user_id ON documents(user_id);
CREATE INDEX idx_documents_status ON documents(status);
CREATE INDEX idx_documents_created_at ON documents(created_at);
CREATE INDEX idx_documents_file_hash ON documents(file_hash);
CREATE INDEX idx_document_chunks_document_id ON document_chunks(document_id);
CREATE INDEX idx_document_chunks_content_gin ON document_chunks USING gin(to_tsvector('english', content));
```

#### 查询管理表
```sql
-- 查询类型枚举
CREATE TYPE query_type_enum AS ENUM (
    'general', 'semantic', 'graph', 'hybrid'
);

-- 查询会话表
CREATE TABLE query_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_name VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 查询表
CREATE TABLE queries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES query_sessions(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    question TEXT NOT NULL,
    query_type query_type_enum DEFAULT 'general',
    context JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 答案表
CREATE TABLE answers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_id UUID NOT NULL REFERENCES queries(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    confidence_score DECIMAL(3,2),
    sources JSONB DEFAULT '[]',
    model_used VARCHAR(100),
    tokens_used INTEGER,
    processing_time DECIMAL(8,3),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_query_sessions_user_id ON query_sessions(user_id);
CREATE INDEX idx_query_sessions_active ON query_sessions(is_active);
CREATE INDEX idx_queries_session_id ON queries(session_id);
CREATE INDEX idx_queries_user_id ON queries(user_id);
CREATE INDEX idx_queries_created_at ON queries(created_at);
CREATE INDEX idx_answers_query_id ON answers(query_id);
```

### 通知数据库表结构

```sql
-- 通知类型枚举
CREATE TYPE notification_type_enum AS ENUM (
    'document_uploaded', 'document_processed', 'document_failed',
    'query_completed', 'system_alert', 'user_action'
);

-- 通知优先级枚举
CREATE TYPE notification_priority_enum AS ENUM (
    'low', 'normal', 'high', 'urgent'
);

-- 通知表
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    notification_type notification_type_enum NOT NULL,
    priority notification_priority_enum DEFAULT 'normal',
    is_read BOOLEAN DEFAULT false,
    data JSONB DEFAULT '{}',
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    read_at TIMESTAMP WITH TIME ZONE
);

-- 索引
CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_is_read ON notifications(is_read);
CREATE INDEX idx_notifications_type ON notifications(notification_type);
CREATE INDEX idx_notifications_priority ON notifications(priority);
CREATE INDEX idx_notifications_created_at ON notifications(created_at);
```

## Weaviate 向量数据库设计

### Schema 定义

```json
{
  "classes": [
    {
      "class": "DocumentChunk",
      "description": "文档分块的向量表示",
      "vectorizer": "text2vec-openai",
      "moduleConfig": {
        "text2vec-openai": {
          "model": "text-embedding-ada-002",
          "modelVersion": "002",
          "type": "text"
        }
      },
      "properties": [
        {
          "name": "content",
          "dataType": ["text"],
          "description": "分块内容",
          "moduleConfig": {
            "text2vec-openai": {
              "skip": false,
              "vectorizePropertyName": false
            }
          }
        },
        {
          "name": "documentId",
          "dataType": ["string"],
          "description": "文档ID"
        },
        {
          "name": "chunkId",
          "dataType": ["string"],
          "description": "分块ID"
        },
        {
          "name": "chunkIndex",
          "dataType": ["int"],
          "description": "分块索引"
        },
        {
          "name": "pageNumber",
          "dataType": ["int"],
          "description": "页码"
        },
        {
          "name": "contentType",
          "dataType": ["string"],
          "description": "内容类型"
        },
        {
          "name": "metadata",
          "dataType": ["object"],
          "description": "元数据"
        },
        {
          "name": "createdAt",
          "dataType": ["date"],
          "description": "创建时间"
        }
      ]
    },
    {
      "class": "QueryVector",
      "description": "查询向量缓存",
      "vectorizer": "text2vec-openai",
      "moduleConfig": {
        "text2vec-openai": {
          "model": "text-embedding-ada-002",
          "modelVersion": "002",
          "type": "text"
        }
      },
      "properties": [
        {
          "name": "query",
          "dataType": ["text"],
          "description": "查询文本"
        },
        {
          "name": "queryHash",
          "dataType": ["string"],
          "description": "查询哈希"
        },
        {
          "name": "userId",
          "dataType": ["string"],
          "description": "用户ID"
        },
        {
          "name": "createdAt",
          "dataType": ["date"],
          "description": "创建时间"
        }
      ]
    }
  ]
}
```

### 索引配置

```json
{
  "vectorIndexConfig": {
    "skip": false,
    "cleanupIntervalSeconds": 300,
    "maxConnections": 64,
    "efConstruction": 128,
    "ef": -1,
    "dynamicEfMin": 100,
    "dynamicEfMax": 500,
    "dynamicEfFactor": 8,
    "vectorCacheMaxObjects": 1000000000000,
    "flatSearchCutoff": 40000,
    "distance": "cosine"
  }
}
```

## Neo4j 图数据库设计

### 节点标签定义

```cypher
-- 实体类型约束
CREATE CONSTRAINT entity_id_unique FOR (e:Entity) REQUIRE e.id IS UNIQUE;
CREATE CONSTRAINT person_id_unique FOR (p:Person) REQUIRE p.id IS UNIQUE;
CREATE CONSTRAINT organization_id_unique FOR (o:Organization) REQUIRE o.id IS UNIQUE;
CREATE CONSTRAINT location_id_unique FOR (l:Location) REQUIRE l.id IS UNIQUE;
CREATE CONSTRAINT concept_id_unique FOR (c:Concept) REQUIRE c.id IS UNIQUE;
CREATE CONSTRAINT document_id_unique FOR (d:Document) REQUIRE d.id IS UNIQUE;

-- 索引创建
CREATE INDEX entity_name_index FOR (e:Entity) ON (e.name);
CREATE INDEX entity_type_index FOR (e:Entity) ON (e.entity_type);
CREATE INDEX person_name_index FOR (p:Person) ON (p.name);
CREATE INDEX organization_name_index FOR (o:Organization) ON (o.name);
CREATE INDEX document_filename_index FOR (d:Document) ON (d.filename);
```

### 关系类型定义

```cypher
-- 基础关系类型
CREATE ()
-[:WORKS_FOR {confidence: 0.95, source_document: "doc_id"}]->
();

CREATE ()
-[:LOCATED_IN {confidence: 0.88, source_document: "doc_id"}]->
();

CREATE ()
-[:RELATED_TO {confidence: 0.75, relationship_type: "mentions"}]->
();

CREATE ()
-[:PART_OF {confidence: 0.92, source_document: "doc_id"}]->
();

CREATE ()
-[:CONTAINS {confidence: 0.85, chunk_id: "chunk_id"}]->
();
```

### 图数据模型

```cypher
-- 实体节点结构
CREATE (:Entity {
  id: "uuid",
  name: "实体名称",
  entity_type: "person|organization|location|concept",
  description: "实体描述",
  confidence_score: 0.95,
  properties: {},
  source_documents: ["doc_id1", "doc_id2"],
  created_at: datetime(),
  updated_at: datetime()
});

-- 文档节点结构
CREATE (:Document {
  id: "uuid",
  filename: "文档名称",
  file_path: "文件路径",
  processed_at: datetime(),
  chunk_count: 100,
  entity_count: 50,
  relationship_count: 75
});

-- 分块节点结构
CREATE (:Chunk {
  id: "uuid",
  document_id: "doc_uuid",
  chunk_index: 1,
  content: "分块内容",
  page_number: 1,
  entity_mentions: ["entity_id1", "entity_id2"]
});
```

## MinIO 对象存储设计

### 存储桶结构

```yaml
# 存储桶配置
buckets:
  # 原始文档存储
  documents:
    name: "knowledge-rag-documents"
    versioning: enabled
    encryption: AES256
    lifecycle:
      - rule_id: "delete_old_versions"
        status: enabled
        expiration_days: 90
        noncurrent_version_expiration_days: 30
    
  # 处理后的文件存储
  processed:
    name: "knowledge-rag-processed"
    versioning: enabled
    encryption: AES256
    lifecycle:
      - rule_id: "archive_old_files"
        status: enabled
        transition_days: 30
        storage_class: "GLACIER"
  
  # 临时文件存储
  temp:
    name: "knowledge-rag-temp"
    versioning: disabled
    lifecycle:
      - rule_id: "delete_temp_files"
        status: enabled
        expiration_days: 7
  
  # 系统备份存储
  backups:
    name: "knowledge-rag-backups"
    versioning: enabled
    encryption: AES256
    lifecycle:
      - rule_id: "retain_backups"
        status: enabled
        expiration_days: 365
```

### 文件路径规范

```
# 文档存储路径结构
documents/
├── {user_id}/
│   ├── {year}/
│   │   ├── {month}/
│   │   │   ├── {document_id}/
│   │   │   │   ├── original.{ext}          # 原始文件
│   │   │   │   ├── metadata.json          # 元数据
│   │   │   │   └── thumbnails/            # 缩略图
│   │   │   │       ├── page_1.jpg
│   │   │   │       └── page_2.jpg

# 处理后文件路径结构
processed/
├── {document_id}/
│   ├── text/
│   │   ├── full_text.txt                  # 完整文本
│   │   └── chunks/                        # 分块文本
│   │       ├── chunk_001.txt
│   │       └── chunk_002.txt
│   ├── images/                            # 提取的图片
│   │   ├── image_001.jpg
│   │   └── image_002.jpg
│   └── analysis/                          # 分析结果
│       ├── entities.json                  # 实体提取结果
│       ├── relationships.json             # 关系提取结果
│       └── summary.json                   # 摘要信息
```

## Redis 缓存设计

### 缓存策略

```yaml
# Redis 数据库分配
databases:
  0: "用户会话缓存"          # 用户登录状态、JWT Token
  1: "查询结果缓存"          # 查询结果、向量搜索结果
  2: "文档处理队列"          # Celery任务队列
  3: "实时通知"             # WebSocket连接、实时消息
  4: "API限流"              # 接口访问频率限制
  5: "系统配置缓存"          # 系统配置、模型参数
```

### 缓存键命名规范

```redis
# 用户会话 (DB 0)
user:session:{user_id}                    # 用户会话信息
user:token:{token_hash}                   # Token验证信息
user:profile:{user_id}                    # 用户资料缓存

# 查询缓存 (DB 1)
query:result:{query_hash}                 # 查询结果缓存
query:vector:{query_hash}                 # 查询向量缓存
search:semantic:{query_hash}              # 语义搜索结果

# 任务队列 (DB 2)
celery:task:{task_id}                     # 任务状态
queue:document:processing                 # 文档处理队列
queue:embedding:generation                # 向量生成队列

# 实时通知 (DB 3)
notification:user:{user_id}               # 用户通知列表
websocket:connection:{connection_id}      # WebSocket连接

# API限流 (DB 4)
ratelimit:user:{user_id}:{endpoint}       # 用户接口限流
ratelimit:ip:{ip_address}:{endpoint}      # IP接口限流

# 系统配置 (DB 5)
config:system                             # 系统配置
config:model:{model_name}                 # 模型配置
config:embedding:settings                 # 向量化配置
```

### 缓存过期策略

```yaml
# TTL 配置
ttl_settings:
  user_session: 3600                      # 1小时
  query_result: 1800                      # 30分钟
  vector_cache: 7200                      # 2小时
  notification: 86400                     # 24小时
  rate_limit: 60                          # 1分钟
  system_config: 300                      # 5分钟
  
# 内存管理
memory_policy: "allkeys-lru"              # LRU淘汰策略
max_memory: "2gb"                         # 最大内存限制
max_memory_samples: 5                     # 采样数量
```

## 数据库连接池配置

### PostgreSQL 连接池

```yaml
# 连接池配置
postgresql:
  main_db:
    host: "postgres-main"
    port: 5432
    database: "knowledge_rag_main"
    pool_size: 20
    max_overflow: 30
    pool_timeout: 30
    pool_recycle: 3600
    pool_pre_ping: true
    
  notification_db:
    host: "postgres-notifications"
    port: 5432
    database: "knowledge_rag_notifications"
    pool_size: 10
    max_overflow: 15
    pool_timeout: 30
    pool_recycle: 3600
    pool_pre_ping: true
```

### Weaviate 连接配置

```yaml
weaviate:
  host: "weaviate-cluster"
  port: 8080
  grpc_port: 50051
  scheme: "http"
  timeout: 30
  connection_pool_size: 10
  retry_attempts: 3
  retry_delay: 1
```

### Neo4j 连接配置

```yaml
neo4j:
  uri: "bolt://neo4j-cluster:7687"
  auth:
    username: "neo4j"
    password: "${NEO4J_PASSWORD}"
  max_connection_lifetime: 3600
  max_connection_pool_size: 50
  connection_acquisition_timeout: 60
  connection_timeout: 30
  max_retry_time: 30
```

## 数据备份与恢复策略

### 备份策略

```yaml
backup_strategy:
  postgresql:
    full_backup:
      frequency: "daily"
      time: "02:00"
      retention: 30  # 保留30天
    incremental_backup:
      frequency: "hourly"
      retention: 7   # 保留7天
    
  neo4j:
    backup:
      frequency: "daily"
      time: "03:00"
      retention: 30
    
  weaviate:
    backup:
      frequency: "daily"
      time: "04:00"
      retention: 30
    
  minio:
    versioning: enabled
    cross_region_replication: enabled
    backup_frequency: "daily"
    retention: 90
```

### 恢复流程

```yaml
recovery_procedures:
  rto: 4  # 恢复时间目标：4小时
  rpo: 1  # 恢复点目标：1小时
  
  steps:
    1. "评估数据损失范围"
    2. "选择合适的备份点"
    3. "按依赖顺序恢复数据库"
    4. "验证数据完整性"
    5. "重建索引和缓存"
    6. "执行应用层验证"
```

## 数据库监控与性能优化

### 监控指标

```yaml
monitoring_metrics:
  postgresql:
    - "连接数使用率"
    - "查询响应时间"
    - "慢查询统计"
    - "锁等待时间"
    - "缓存命中率"
    - "磁盘I/O使用率"
    
  weaviate:
    - "向量搜索延迟"
    - "索引构建时间"
    - "内存使用率"
    - "查询吞吐量"
    
  neo4j:
    - "图查询性能"
    - "节点/关系数量"
    - "页面缓存命中率"
    - "事务吞吐量"
    
  redis:
    - "内存使用率"
    - "缓存命中率"
    - "连接数"
    - "操作延迟"
```

### 性能优化策略

```yaml
performance_optimization:
  postgresql:
    - "定期VACUUM和ANALYZE"
    - "合理设置work_mem和shared_buffers"
    - "优化查询计划"
    - "分区表设计"
    - "读写分离"
    
  weaviate:
    - "向量维度优化"
    - "批量导入优化"
    - "索引参数调优"
    - "内存分配优化"
    
  neo4j:
    - "查询优化和索引策略"
    - "内存配置调优"
    - "批量导入优化"
    - "图模型设计优化"
    
  redis:
    - "内存优化和数据结构选择"
    - "持久化策略优化"
    - "集群分片策略"
    - "管道操作优化"
```

## 数据库架构确认

✅ **数据库架构设计已完成**

---

# 部署策略设计

## 云原生部署架构

### 整体部署架构

Knowledge_RAG系统采用云原生架构，基于Kubernetes进行容器化部署，支持多环境、高可用、自动扩缩容：

```mermaid
graph TB
    subgraph "外部访问层"
        A[Load Balancer]
        B[CDN]
    end
    
    subgraph "Kubernetes集群"
        subgraph "Ingress层"
            C[Nginx Ingress Controller]
            D[Kong API Gateway]
        end
        
        subgraph "应用服务层"
            E[User Service Pod]
            F[Document Service Pod]
            G[Embedding Service Pod]
            H[Knowledge Graph Service Pod]
            I[Query Service Pod]
            J[Notification Service Pod]
        end
        
        subgraph "数据存储层"
            K[PostgreSQL Cluster]
            L[Weaviate Cluster]
            M[Neo4j Cluster]
            N[MinIO Cluster]
            O[Redis Cluster]
        end
        
        subgraph "监控与日志"
            P[Prometheus]
            Q[Grafana]
            R[Jaeger]
            S[ELK Stack]
        end
    end
    
    A --> C
    B --> C
    C --> D
    D --> E
    D --> F
    D --> G
    D --> H
    D --> I
    D --> J
    
    E --> K
    F --> K
    F --> N
    G --> L
    H --> M
    I --> K
    I --> L
    I --> M
    J --> K
    
    E --> O
    F --> O
    G --> O
    H --> O
    I --> O
    J --> O
```

### 环境分层策略

```yaml
# 环境配置
environments:
  development:
    cluster_size: "small"
    replicas: 1
    resources:
      cpu: "0.5"
      memory: "1Gi"
    storage: "local"
    monitoring: "basic"
    
  staging:
    cluster_size: "medium"
    replicas: 2
    resources:
      cpu: "1"
      memory: "2Gi"
    storage: "persistent"
    monitoring: "full"
    
  production:
    cluster_size: "large"
    replicas: 3
    resources:
      cpu: "2"
      memory: "4Gi"
    storage: "distributed"
    monitoring: "enterprise"
    backup: "enabled"
    security: "enhanced"
```

## Kubernetes 部署配置

### 命名空间设计

```yaml
# 命名空间配置
apiVersion: v1
kind: Namespace
metadata:
  name: knowledge-rag-prod
  labels:
    environment: production
    project: knowledge-rag
---
apiVersion: v1
kind: Namespace
metadata:
  name: knowledge-rag-staging
  labels:
    environment: staging
    project: knowledge-rag
---
apiVersion: v1
kind: Namespace
metadata:
  name: knowledge-rag-dev
  labels:
    environment: development
    project: knowledge-rag
---
apiVersion: v1
kind: Namespace
metadata:
  name: knowledge-rag-monitoring
  labels:
    component: monitoring
    project: knowledge-rag
```

### 服务部署配置

#### User Service 部署
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: user-service
  namespace: knowledge-rag-prod
  labels:
    app: user-service
    version: v1.0.0
spec:
  replicas: 3
  selector:
    matchLabels:
      app: user-service
  template:
    metadata:
      labels:
        app: user-service
        version: v1.0.0
    spec:
      containers:
      - name: user-service
        image: knowledge-rag/user-service:v1.0.0
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: redis-secret
              key: redis-url
        - name: JWT_SECRET
          valueFrom:
            secretKeyRef:
              name: jwt-secret
              key: secret-key
        resources:
          requests:
            cpu: 500m
            memory: 1Gi
          limits:
            cpu: 1000m
            memory: 2Gi
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: user-service
  namespace: knowledge-rag-prod
spec:
  selector:
    app: user-service
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: ClusterIP
```

#### Document Service 部署
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: document-service
  namespace: knowledge-rag-prod
  labels:
    app: document-service
    version: v1.0.0
spec:
  replicas: 3
  selector:
    matchLabels:
      app: document-service
  template:
    metadata:
      labels:
        app: document-service
        version: v1.0.0
    spec:
      containers:
      - name: document-service
        image: knowledge-rag/document-service:v1.0.0
        ports:
        - containerPort: 8001
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: database-url
        - name: MINIO_URL
          valueFrom:
            secretKeyRef:
              name: minio-secret
              key: endpoint
        - name: MINIO_ACCESS_KEY
          valueFrom:
            secretKeyRef:
              name: minio-secret
              key: access-key
        - name: MINIO_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: minio-secret
              key: secret-key
        - name: CELERY_BROKER_URL
          valueFrom:
            secretKeyRef:
              name: redis-secret
              key: redis-url
        resources:
          requests:
            cpu: 1000m
            memory: 2Gi
          limits:
            cpu: 2000m
            memory: 4Gi
        volumeMounts:
        - name: temp-storage
          mountPath: /tmp/uploads
      volumes:
      - name: temp-storage
        emptyDir:
          sizeLimit: 10Gi
---
apiVersion: v1
kind: Service
metadata:
  name: document-service
  namespace: knowledge-rag-prod
spec:
  selector:
    app: document-service
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8001
  type: ClusterIP
```

### 数据库部署配置

#### PostgreSQL 集群部署
```yaml
apiVersion: postgresql.cnpg.io/v1
kind: Cluster
metadata:
  name: postgres-cluster
  namespace: knowledge-rag-prod
spec:
  instances: 3
  primaryUpdateStrategy: unsupervised
  
  postgresql:
    parameters:
      max_connections: "200"
      shared_buffers: "256MB"
      effective_cache_size: "1GB"
      maintenance_work_mem: "64MB"
      checkpoint_completion_target: "0.9"
      wal_buffers: "16MB"
      default_statistics_target: "100"
      random_page_cost: "1.1"
      effective_io_concurrency: "200"
      work_mem: "4MB"
      min_wal_size: "1GB"
      max_wal_size: "4GB"
  
  bootstrap:
    initdb:
      database: knowledge_rag_main
      owner: app_user
      secret:
        name: postgres-credentials
  
  storage:
    size: 100Gi
    storageClass: fast-ssd
  
  monitoring:
    enabled: true
    
  backup:
    retentionPolicy: "30d"
    barmanObjectStore:
      destinationPath: "s3://knowledge-rag-backups/postgres"
      s3Credentials:
        accessKeyId:
          name: backup-credentials
          key: ACCESS_KEY_ID
        secretAccessKey:
          name: backup-credentials
          key: SECRET_ACCESS_KEY
      wal:
        retention: "5d"
      data:
        retention: "30d"
```

#### Weaviate 集群部署
```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: weaviate
  namespace: knowledge-rag-prod
spec:
  serviceName: weaviate
  replicas: 3
  selector:
    matchLabels:
      app: weaviate
  template:
    metadata:
      labels:
        app: weaviate
    spec:
      containers:
      - name: weaviate
        image: semitechnologies/weaviate:1.22.4
        ports:
        - containerPort: 8080
        - containerPort: 50051
        env:
        - name: QUERY_DEFAULTS_LIMIT
          value: "25"
        - name: AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED
          value: "false"
        - name: AUTHENTICATION_APIKEY_ENABLED
          value: "true"
        - name: AUTHENTICATION_APIKEY_ALLOWED_KEYS
          valueFrom:
            secretKeyRef:
              name: weaviate-secret
              key: api-keys
        - name: AUTHORIZATION_ADMINLIST_ENABLED
          value: "true"
        - name: AUTHORIZATION_ADMINLIST_USERS
          value: "admin"
        - name: PERSISTENCE_DATA_PATH
          value: "/var/lib/weaviate"
        - name: DEFAULT_VECTORIZER_MODULE
          value: "text2vec-openai"
        - name: ENABLE_MODULES
          value: "text2vec-openai,generative-openai"
        - name: OPENAI_APIKEY
          valueFrom:
            secretKeyRef:
              name: openai-secret
              key: api-key
        - name: CLUSTER_HOSTNAME
          value: "weaviate"
        - name: CLUSTER_GOSSIP_BIND_PORT
          value: "7100"
        - name: CLUSTER_DATA_BIND_PORT
          value: "7101"
        resources:
          requests:
            cpu: 1000m
            memory: 4Gi
          limits:
            cpu: 2000m
            memory: 8Gi
        volumeMounts:
        - name: weaviate-data
          mountPath: /var/lib/weaviate
  volumeClaimTemplates:
  - metadata:
      name: weaviate-data
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: fast-ssd
      resources:
        requests:
          storage: 200Gi
---
apiVersion: v1
kind: Service
metadata:
  name: weaviate
  namespace: knowledge-rag-prod
spec:
  clusterIP: None
  selector:
    app: weaviate
  ports:
  - name: http
    port: 8080
    targetPort: 8080
  - name: grpc
    port: 50051
    targetPort: 50051
  - name: gossip
    port: 7100
    targetPort: 7100
  - name: data
    port: 7101
    targetPort: 7101
```

#### Neo4j 集群部署
```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: neo4j
  namespace: knowledge-rag-prod
spec:
  serviceName: neo4j
  replicas: 3
  selector:
    matchLabels:
      app: neo4j
  template:
    metadata:
      labels:
        app: neo4j
    spec:
      containers:
      - name: neo4j
        image: neo4j:5.13-enterprise
        ports:
        - containerPort: 7474
        - containerPort: 7687
        - containerPort: 6362
        - containerPort: 7000
        env:
        - name: NEO4J_AUTH
          valueFrom:
            secretKeyRef:
              name: neo4j-secret
              key: auth
        - name: NEO4J_ACCEPT_LICENSE_AGREEMENT
          value: "yes"
        - name: NEO4J_dbms_mode
          value: "CORE"
        - name: NEO4J_causal__clustering_minimum__core__cluster__size__at__formation
          value: "3"
        - name: NEO4J_causal__clustering_minimum__core__cluster__size__at__runtime
          value: "3"
        - name: NEO4J_causal__clustering_initial__discovery__members
          value: "neo4j-0.neo4j:5000,neo4j-1.neo4j:5000,neo4j-2.neo4j:5000"
        - name: NEO4J_dbms_connector_bolt_listen__address
          value: "0.0.0.0:7687"
        - name: NEO4J_dbms_connector_http_listen__address
          value: "0.0.0.0:7474"
        - name: NEO4J_dbms_memory_heap_initial__size
          value: "2G"
        - name: NEO4J_dbms_memory_heap_max__size
          value: "4G"
        - name: NEO4J_dbms_memory_pagecache_size
          value: "2G"
        resources:
          requests:
            cpu: 1000m
            memory: 6Gi
          limits:
            cpu: 2000m
            memory: 8Gi
        volumeMounts:
        - name: neo4j-data
          mountPath: /data
        - name: neo4j-logs
          mountPath: /logs
  volumeClaimTemplates:
  - metadata:
      name: neo4j-data
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: fast-ssd
      resources:
        requests:
          storage: 100Gi
  - metadata:
      name: neo4j-logs
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: standard
      resources:
        requests:
          storage: 20Gi
```

#### MinIO 集群部署
```yaml
apiVersion: v1
kind: Service
metadata:
  name: minio
  namespace: knowledge-rag-prod
spec:
  clusterIP: None
  ports:
  - port: 9000
    name: minio
  - port: 9001
    name: minio-console
  selector:
    app: minio
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: minio
  namespace: knowledge-rag-prod
spec:
  serviceName: minio
  replicas: 4
  selector:
    matchLabels:
      app: minio
  template:
    metadata:
      labels:
        app: minio
    spec:
      containers:
      - name: minio
        image: minio/minio:RELEASE.2023-11-20T22-40-07Z
        command:
        - /bin/bash
        - -c
        args:
        - minio server http://minio-{0...3}.minio.knowledge-rag-prod.svc.cluster.local/data --console-address ":9001"
        ports:
        - containerPort: 9000
        - containerPort: 9001
        env:
        - name: MINIO_ROOT_USER
          valueFrom:
            secretKeyRef:
              name: minio-secret
              key: root-user
        - name: MINIO_ROOT_PASSWORD
          valueFrom:
            secretKeyRef:
              name: minio-secret
              key: root-password
        - name: MINIO_STORAGE_CLASS_STANDARD
          value: "EC:2"
        resources:
          requests:
            cpu: 500m
            memory: 2Gi
          limits:
            cpu: 1000m
            memory: 4Gi
        volumeMounts:
        - name: minio-data
          mountPath: /data
        livenessProbe:
          httpGet:
            path: /minio/health/live
            port: 9000
          initialDelaySeconds: 120
          periodSeconds: 20
        readinessProbe:
          httpGet:
            path: /minio/health/ready
            port: 9000
          initialDelaySeconds: 120
          periodSeconds: 20
  volumeClaimTemplates:
  - metadata:
      name: minio-data
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: fast-ssd
      resources:
        requests:
          storage: 500Gi
```

#### Redis 集群部署
```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: redis
  namespace: knowledge-rag-prod
spec:
  serviceName: redis
  replicas: 6
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7.2-alpine
        command:
        - redis-server
        args:
        - /etc/redis/redis.conf
        - --cluster-enabled
        - "yes"
        - --cluster-config-file
        - /data/nodes.conf
        - --cluster-node-timeout
        - "5000"
        - --appendonly
        - "yes"
        - --protected-mode
        - "no"
        ports:
        - containerPort: 6379
        - containerPort: 16379
        env:
        - name: REDIS_PASSWORD
          valueFrom:
            secretKeyRef:
              name: redis-secret
              key: password
        resources:
          requests:
            cpu: 250m
            memory: 1Gi
          limits:
            cpu: 500m
            memory: 2Gi
        volumeMounts:
        - name: redis-data
          mountPath: /data
        - name: redis-config
          mountPath: /etc/redis
      volumes:
      - name: redis-config
        configMap:
          name: redis-config
  volumeClaimTemplates:
  - metadata:
      name: redis-data
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: fast-ssd
      resources:
        requests:
          storage: 50Gi
```

## Helm Charts 配置

### Chart 结构

```
knowledge-rag-helm/
├── Chart.yaml
├── values.yaml
├── values-dev.yaml
├── values-staging.yaml
├── values-prod.yaml
├── templates/
│   ├── _helpers.tpl
│   ├── configmap.yaml
│   ├── secret.yaml
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   ├── hpa.yaml
│   ├── pdb.yaml
│   └── serviceaccount.yaml
├── charts/
│   ├── postgresql/
│   ├── weaviate/
│   ├── neo4j/
│   ├── minio/
│   ├── redis/
│   └── monitoring/
└── crds/
```

### 主 Chart 配置

```yaml
# Chart.yaml
apiVersion: v2
name: knowledge-rag
description: Knowledge RAG System Helm Chart
type: application
version: 1.0.0
appVersion: "1.0.0"

dependencies:
- name: postgresql
  version: "12.12.10"
  repository: "https://charts.bitnami.com/bitnami"
  condition: postgresql.enabled
- name: redis
  version: "18.1.5"
  repository: "https://charts.bitnami.com/bitnami"
  condition: redis.enabled
- name: minio
  version: "12.8.22"
  repository: "https://charts.bitnami.com/bitnami"
  condition: minio.enabled
- name: prometheus
  version: "25.1.0"
  repository: "https://prometheus-community.github.io/helm-charts"
  condition: monitoring.prometheus.enabled
- name: grafana
  version: "7.0.3"
  repository: "https://grafana.github.io/helm-charts"
  condition: monitoring.grafana.enabled
```

### Values 配置

```yaml
# values.yaml
global:
  imageRegistry: "registry.knowledge-rag.com"
  imagePullSecrets:
    - name: registry-secret
  storageClass: "fast-ssd"
  
replicaCount: 3

image:
  repository: knowledge-rag
  pullPolicy: IfNotPresent
  tag: "1.0.0"

serviceAccount:
  create: true
  annotations: {}
  name: ""

resources:
  limits:
    cpu: 2000m
    memory: 4Gi
  requests:
    cpu: 1000m
    memory: 2Gi

autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
  targetMemoryUtilizationPercentage: 80

service:
  type: ClusterIP
  port: 80

ingress:
  enabled: true
  className: "nginx"
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
  hosts:
    - host: api.knowledge-rag.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: knowledge-rag-tls
      hosts:
        - api.knowledge-rag.com

# 数据库配置
postgresql:
  enabled: true
  auth:
    postgresPassword: "secure-password"
    database: "knowledge_rag_main"
  primary:
    persistence:
      enabled: true
      size: 100Gi
      storageClass: "fast-ssd"
  metrics:
    enabled: true

redis:
  enabled: true
  auth:
    enabled: true
    password: "redis-password"
  cluster:
    enabled: true
    nodes: 6
  persistence:
    enabled: true
    size: 50Gi
    storageClass: "fast-ssd"

minio:
  enabled: true
  auth:
    rootUser: "admin"
    rootPassword: "minio-password"
  defaultBuckets: "knowledge-rag-documents,knowledge-rag-processed,knowledge-rag-temp,knowledge-rag-backups"
  persistence:
    enabled: true
    size: 500Gi
    storageClass: "fast-ssd"

# 监控配置
monitoring:
  prometheus:
    enabled: true
  grafana:
    enabled: true
    adminPassword: "grafana-password"
  jaeger:
    enabled: true
```

### 生产环境配置

```yaml
# values-prod.yaml
replicaCount: 5

resources:
  limits:
    cpu: 4000m
    memory: 8Gi
  requests:
    cpu: 2000m
    memory: 4Gi

autoscaling:
  enabled: true
  minReplicas: 5
  maxReplicas: 20
  targetCPUUtilizationPercentage: 60
  targetMemoryUtilizationPercentage: 70

postgresql:
  primary:
    persistence:
      size: 500Gi
  readReplicas:
    replicaCount: 2
    persistence:
      size: 500Gi

redis:
  cluster:
    nodes: 6
  persistence:
    size: 100Gi

minio:
  mode: distributed
  statefulset:
    replicaCount: 4
  persistence:
    size: 1Ti

monitoring:
  prometheus:
    server:
      retention: "30d"
      persistentVolume:
        size: 100Gi
  grafana:
    persistence:
      enabled: true
      size: 10Gi
```

## CI/CD 流水线

### GitLab CI 配置

```yaml
# .gitlab-ci.yml
stages:
  - test
  - build
  - security
  - deploy-dev
  - deploy-staging
  - deploy-prod

variables:
  DOCKER_REGISTRY: registry.knowledge-rag.com
  DOCKER_DRIVER: overlay2
  KUBECONFIG: /tmp/kubeconfig

# 测试阶段
unit-test:
  stage: test
  image: python:3.11-slim
  services:
    - postgres:15
    - redis:7-alpine
  variables:
    POSTGRES_DB: test_db
    POSTGRES_USER: test_user
    POSTGRES_PASSWORD: test_password
  before_script:
    - pip install -r requirements-dev.txt
  script:
    - pytest tests/unit/ --cov=src --cov-report=xml
    - flake8 src/
    - black --check src/
    - mypy src/
  artifacts:
    reports:
      coverage: coverage.xml
    paths:
      - coverage.xml
  only:
    - merge_requests
    - main
    - develop

integration-test:
  stage: test
  image: python:3.11-slim
  services:
    - postgres:15
    - redis:7-alpine
    - weaviate/weaviate:1.22.4
  script:
    - pytest tests/integration/ -v
  only:
    - merge_requests
    - main

# 构建阶段
build-images:
  stage: build
  image: docker:24-dind
  services:
    - docker:24-dind
  variables:
    DOCKER_TLS_CERTDIR: "/certs"
  before_script:
    - echo $CI_REGISTRY_PASSWORD | docker login -u $CI_REGISTRY_USER --password-stdin $DOCKER_REGISTRY
  script:
    - |
      for service in user-service document-service embedding-service knowledge-graph-service query-service notification-service api-gateway; do
        docker build -t $DOCKER_REGISTRY/knowledge-rag/$service:$CI_COMMIT_SHA -f services/$service/Dockerfile .
        docker push $DOCKER_REGISTRY/knowledge-rag/$service:$CI_COMMIT_SHA
        docker tag $DOCKER_REGISTRY/knowledge-rag/$service:$CI_COMMIT_SHA $DOCKER_REGISTRY/knowledge-rag/$service:latest
        docker push $DOCKER_REGISTRY/knowledge-rag/$service:latest
      done
  only:
    - main
    - develop
    - tags

# 安全扫描
security-scan:
  stage: security
  image: aquasec/trivy:latest
  script:
    - |
      for service in user-service document-service embedding-service knowledge-graph-service query-service notification-service api-gateway; do
        trivy image --exit-code 1 --severity HIGH,CRITICAL $DOCKER_REGISTRY/knowledge-rag/$service:$CI_COMMIT_SHA
      done
  allow_failure: true
  only:
    - main
    - develop

# 开发环境部署
deploy-dev:
  stage: deploy-dev
  image: bitnami/kubectl:latest
  environment:
    name: development
    url: https://dev-api.knowledge-rag.com
  before_script:
    - echo $KUBE_CONFIG_DEV | base64 -d > $KUBECONFIG
    - kubectl config use-context dev-cluster
  script:
    - helm upgrade --install knowledge-rag-dev ./helm/knowledge-rag \
        --namespace knowledge-rag-dev \
        --create-namespace \
        --values ./helm/knowledge-rag/values-dev.yaml \
        --set global.image.tag=$CI_COMMIT_SHA \
        --wait --timeout=600s
  only:
    - develop

# 预发布环境部署
deploy-staging:
  stage: deploy-staging
  image: bitnami/kubectl:latest
  environment:
    name: staging
    url: https://staging-api.knowledge-rag.com
  before_script:
    - echo $KUBE_CONFIG_STAGING | base64 -d > $KUBECONFIG
    - kubectl config use-context staging-cluster
  script:
    - helm upgrade --install knowledge-rag-staging ./helm/knowledge-rag \
        --namespace knowledge-rag-staging \
        --create-namespace \
        --values ./helm/knowledge-rag/values-staging.yaml \
        --set global.image.tag=$CI_COMMIT_SHA \
        --wait --timeout=600s
    - kubectl rollout status deployment/user-service -n knowledge-rag-staging
    - kubectl rollout status deployment/document-service -n knowledge-rag-staging
  when: manual
  only:
    - main

# 生产环境部署
deploy-prod:
  stage: deploy-prod
  image: bitnami/kubectl:latest
  environment:
    name: production
    url: https://api.knowledge-rag.com
  before_script:
    - echo $KUBE_CONFIG_PROD | base64 -d > $KUBECONFIG
    - kubectl config use-context prod-cluster
  script:
    - helm upgrade --install knowledge-rag-prod ./helm/knowledge-rag \
        --namespace knowledge-rag-prod \
        --create-namespace \
        --values ./helm/knowledge-rag/values-prod.yaml \
        --set global.image.tag=$CI_COMMIT_SHA \
        --wait --timeout=900s
    - kubectl rollout status deployment/user-service -n knowledge-rag-prod
    - kubectl rollout status deployment/document-service -n knowledge-rag-prod
    - kubectl rollout status deployment/embedding-service -n knowledge-rag-prod
    - kubectl rollout status deployment/knowledge-graph-service -n knowledge-rag-prod
    - kubectl rollout status deployment/query-service -n knowledge-rag-prod
    - kubectl rollout status deployment/notification-service -n knowledge-rag-prod
  when: manual
  only:
    - tags
```

### GitHub Actions 配置

```yaml
# .github/workflows/ci-cd.yml
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
    tags: [ 'v*' ]
  pull_request:
    branches: [ main ]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: knowledge-rag

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
      
      redis:
        image: redis:7-alpine
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379

    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
        
    - name: Cache pip dependencies
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements*.txt') }}
        restore-keys: |
          ${{ runner.os }}-pip-
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements-dev.txt
    
    - name: Run linting
      run: |
        flake8 src/
        black --check src/
        mypy src/
    
    - name: Run unit tests
      run: |
        pytest tests/unit/ --cov=src --cov-report=xml --cov-report=html
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_db
        REDIS_URL: redis://localhost:6379/0
    
    - name: Upload coverage reports
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: unittests
        name: codecov-umbrella

  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.event_name == 'push'
    
    permissions:
      contents: read
      packages: write
    
    strategy:
      matrix:
        service: 
          - user-service
          - document-service
          - embedding-service
          - knowledge-graph-service
          - query-service
          - notification-service
          - api-gateway
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Log in to Container Registry
      uses: docker/login-action@v3
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}
    
    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v5
      with:
        images: ${{ env.REGISTRY }}/${{ github.repository }}/${{ matrix.service }}
        tags: |
          type=ref,event=branch
          type=ref,event=pr
          type=semver,pattern={{version}}
          type=semver,pattern={{major}}.{{minor}}
          type=sha,prefix={{branch}}-
    
    - name: Build and push Docker image
      uses: docker/build-push-action@v5
      with:
        context: .
        file: ./services/${{ matrix.service }}/Dockerfile
        push: true
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}

  deploy-dev:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/develop'
    environment: development
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Configure kubectl
      run: |
        echo "${{ secrets.KUBE_CONFIG_DEV }}" | base64 -d > $GITHUB_WORKSPACE/kubeconfig
        echo "KUBECONFIG=$GITHUB_WORKSPACE/kubeconfig" >> $GITHUB_ENV
    
    - name: Deploy to development
      run: |
        helm upgrade --install knowledge-rag-dev ./helm/knowledge-rag \
          --namespace knowledge-rag-dev \
          --create-namespace \
          --values ./helm/knowledge-rag/values-dev.yaml \
          --set global.image.tag=${{ github.sha }} \
          --wait --timeout=600s

  deploy-prod:
    needs: build
    runs-on: ubuntu-latest
    if: startsWith(github.ref, 'refs/tags/v')
    environment: production
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Configure kubectl
      run: |
        echo "${{ secrets.KUBE_CONFIG_PROD }}" | base64 -d > $GITHUB_WORKSPACE/kubeconfig
        echo "KUBECONFIG=$GITHUB_WORKSPACE/kubeconfig" >> $GITHUB_ENV
    
    - name: Deploy to production
      run: |
        helm upgrade --install knowledge-rag-prod ./helm/knowledge-rag \
          --namespace knowledge-rag-prod \
          --create-namespace \
          --values ./helm/knowledge-rag/values-prod.yaml \
          --set global.image.tag=${{ github.sha }} \
          --wait --timeout=900s
```

## 监控和日志

### Prometheus 监控配置

```yaml
# monitoring/prometheus-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: knowledge-rag-monitoring
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
      evaluation_interval: 15s
    
    rule_files:
      - "/etc/prometheus/rules/*.yml"
    
    alerting:
      alertmanagers:
        - static_configs:
            - targets:
              - alertmanager:9093
    
    scrape_configs:
      # Kubernetes API Server
      - job_name: 'kubernetes-apiservers'
        kubernetes_sd_configs:
        - role: endpoints
        scheme: https
        tls_config:
          ca_file: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
        bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
        relabel_configs:
        - source_labels: [__meta_kubernetes_namespace, __meta_kubernetes_service_name, __meta_kubernetes_endpoint_port_name]
          action: keep
          regex: default;kubernetes;https
      
      # Knowledge RAG Services
      - job_name: 'knowledge-rag-services'
        kubernetes_sd_configs:
        - role: endpoints
          namespaces:
            names:
            - knowledge-rag-prod
            - knowledge-rag-staging
            - knowledge-rag-dev
        relabel_configs:
        - source_labels: [__meta_kubernetes_service_annotation_prometheus_io_scrape]
          action: keep
          regex: true
        - source_labels: [__meta_kubernetes_service_annotation_prometheus_io_path]
          action: replace
          target_label: __metrics_path__
          regex: (.+)
        - source_labels: [__address__, __meta_kubernetes_service_annotation_prometheus_io_port]
          action: replace
          regex: ([^:]+)(?::\d+)?;(\d+)
          replacement: $1:$2
          target_label: __address__
        - action: labelmap
          regex: __meta_kubernetes_service_label_(.+)
        - source_labels: [__meta_kubernetes_namespace]
          action: replace
          target_label: kubernetes_namespace
        - source_labels: [__meta_kubernetes_service_name]
          action: replace
          target_label: kubernetes_name
      
      # PostgreSQL Exporter
      - job_name: 'postgresql'
        static_configs:
        - targets: ['postgres-exporter:9187']
        scrape_interval: 30s
      
      # Redis Exporter
      - job_name: 'redis'
        static_configs:
        - targets: ['redis-exporter:9121']
        scrape_interval: 30s
      
      # Weaviate Metrics
      - job_name: 'weaviate'
        static_configs:
        - targets: ['weaviate:2112']
        scrape_interval: 30s
      
      # Neo4j Metrics
      - job_name: 'neo4j'
        static_configs:
        - targets: ['neo4j:2004']
        scrape_interval: 30s
      
      # MinIO Metrics
      - job_name: 'minio'
        static_configs:
        - targets: ['minio:9000']
        scrape_interval: 30s
        metrics_path: /minio/v2/metrics/cluster
```

### 告警规则配置

```yaml
# monitoring/alert-rules.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-rules
  namespace: knowledge-rag-monitoring
data:
  knowledge-rag.yml: |
    groups:
    - name: knowledge-rag.rules
      rules:
      # 服务可用性告警
      - alert: ServiceDown
        expr: up{job=~"knowledge-rag-services"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Service {{ $labels.kubernetes_name }} is down"
          description: "Service {{ $labels.kubernetes_name }} in namespace {{ $labels.kubernetes_namespace }} has been down for more than 1 minute."
      
      # 高错误率告警
      - alert: HighErrorRate
        expr: |
          (
            rate(http_requests_total{status=~"5.."}[5m]) /
            rate(http_requests_total[5m])
          ) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value | humanizePercentage }} for service {{ $labels.kubernetes_name }}"
      
      # 高延迟告警
      - alert: HighLatency
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High latency detected"
          description: "95th percentile latency is {{ $value }}s for service {{ $labels.kubernetes_name }}"
      
      # CPU 使用率告警
      - alert: HighCPUUsage
        expr: |
          (
            rate(container_cpu_usage_seconds_total{container!="POD",container!=""}[5m]) * 100
          ) > 80
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage detected"
          description: "CPU usage is {{ $value }}% for container {{ $labels.container }} in pod {{ $labels.pod }}"
      
      # 内存使用率告警
      - alert: HighMemoryUsage
        expr: |
          (
            container_memory_working_set_bytes{container!="POD",container!=""} /
            container_spec_memory_limit_bytes{container!="POD",container!=""} * 100
          ) > 85
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage detected"
          description: "Memory usage is {{ $value }}% for container {{ $labels.container }} in pod {{ $labels.pod }}"
      
      # 数据库连接告警
      - alert: DatabaseConnectionHigh
        expr: pg_stat_activity_count > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High database connections"
          description: "PostgreSQL has {{ $value }} active connections"
      
      # 向量数据库告警
      - alert: WeaviateDown
        expr: up{job="weaviate"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Weaviate is down"
          description: "Weaviate vector database has been down for more than 1 minute"
      
      # 知识图谱数据库告警
      - alert: Neo4jDown
        expr: up{job="neo4j"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Neo4j is down"
          description: "Neo4j graph database has been down for more than 1 minute"
```

### ELK Stack 日志配置

```yaml
# logging/elasticsearch.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: elasticsearch
  namespace: knowledge-rag-logging
spec:
  serviceName: elasticsearch
  replicas: 3
  selector:
    matchLabels:
      app: elasticsearch
  template:
    metadata:
      labels:
        app: elasticsearch
    spec:
      containers:
      - name: elasticsearch
        image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
        ports:
        - containerPort: 9200
        - containerPort: 9300
        env:
        - name: cluster.name
          value: "knowledge-rag-logs"
        - name: node.name
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
        - name: discovery.seed_hosts
          value: "elasticsearch-0.elasticsearch,elasticsearch-1.elasticsearch,elasticsearch-2.elasticsearch"
        - name: cluster.initial_master_nodes
          value: "elasticsearch-0,elasticsearch-1,elasticsearch-2"
        - name: ES_JAVA_OPTS
          value: "-Xms2g -Xmx2g"
        - name: xpack.security.enabled
          value: "false"
        - name: xpack.monitoring.collection.enabled
          value: "true"
        resources:
          requests:
            cpu: 1000m
            memory: 4Gi
          limits:
            cpu: 2000m
            memory: 6Gi
        volumeMounts:
        - name: elasticsearch-data
          mountPath: /usr/share/elasticsearch/data
  volumeClaimTemplates:
  - metadata:
      name: elasticsearch-data
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: fast-ssd
      resources:
        requests:
          storage: 200Gi
```

### Grafana 仪表板配置

```json
{
  "dashboard": {
    "id": null,
    "title": "Knowledge RAG System Overview",
    "tags": ["knowledge-rag"],
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "Service Status",
        "type": "stat",
        "targets": [
          {
            "expr": "up{job=\"knowledge-rag-services\"}",
            "legendFormat": "{{ kubernetes_name }}"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "color": {
              "mode": "thresholds"
            },
            "thresholds": {
              "steps": [
                {"color": "red", "value": 0},
                {"color": "green", "value": 1}
              ]
            }
          }
        }
      },
      {
        "id": 2,
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{ kubernetes_name }}"
          }
        ]
      },
      {
        "id": 3,
        "title": "Response Time (95th percentile)",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "{{ kubernetes_name }}"
          }
        ]
      },
      {
        "id": 4,
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total{status=~\"5..\"}[5m]) / rate(http_requests_total[5m])",
            "legendFormat": "{{ kubernetes_name }}"
          }
        ]
      },
      {
        "id": 5,
        "title": "Database Connections",
        "type": "graph",
        "targets": [
          {
            "expr": "pg_stat_activity_count",
            "legendFormat": "PostgreSQL Connections"
          }
        ]
      },
      {
        "id": 6,
        "title": "Vector Database Status",
        "type": "stat",
        "targets": [
          {
            "expr": "weaviate_objects_total",
            "legendFormat": "Total Objects"
          }
        ]
      }
    ],
    "time": {
      "from": "now-1h",
      "to": "now"
    },
    "refresh": "30s"
  }
}
```

## 灾备和恢复策略

### 备份策略

#### PostgreSQL 备份

```yaml
# backup/postgres-backup-cronjob.yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: postgres-backup
  namespace: knowledge-rag-prod
spec:
  schedule: "0 2 * * *"  # 每天凌晨2点
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: postgres-backup
            image: postgres:15
            command:
            - /bin/bash
            - -c
            - |
              TIMESTAMP=$(date +%Y%m%d_%H%M%S)
              BACKUP_FILE="knowledge_rag_backup_${TIMESTAMP}.sql"
              
              # 创建备份
              pg_dump -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB > /backup/$BACKUP_FILE
              
              # 压缩备份文件
              gzip /backup/$BACKUP_FILE
              
              # 上传到 MinIO
              mc alias set minio $MINIO_ENDPOINT $MINIO_ACCESS_KEY $MINIO_SECRET_KEY
              mc cp /backup/${BACKUP_FILE}.gz minio/knowledge-rag-backups/postgres/
              
              # 清理本地文件
              rm /backup/${BACKUP_FILE}.gz
              
              # 清理7天前的备份
              mc rm --recursive --force --older-than 7d minio/knowledge-rag-backups/postgres/
            env:
            - name: POSTGRES_HOST
              value: "postgresql"
            - name: POSTGRES_USER
              valueFrom:
                secretKeyRef:
                  name: postgres-secret
                  key: username
            - name: POSTGRES_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: postgres-secret
                  key: password
            - name: POSTGRES_DB
              value: "knowledge_rag_main"
            - name: MINIO_ENDPOINT
              value: "http://minio:9000"
            - name: MINIO_ACCESS_KEY
              valueFrom:
                secretKeyRef:
                  name: minio-secret
                  key: root-user
            - name: MINIO_SECRET_KEY
              valueFrom:
                secretKeyRef:
                  name: minio-secret
                  key: root-password
            volumeMounts:
            - name: backup-storage
              mountPath: /backup
          volumes:
          - name: backup-storage
            emptyDir: {}
          restartPolicy: OnFailure
```

#### Weaviate 备份

```yaml
# backup/weaviate-backup-cronjob.yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: weaviate-backup
  namespace: knowledge-rag-prod
spec:
  schedule: "0 3 * * *"  # 每天凌晨3点
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: weaviate-backup
            image: curlimages/curl:latest
            command:
            - /bin/sh
            - -c
            - |
              TIMESTAMP=$(date +%Y%m%d_%H%M%S)
              BACKUP_ID="backup_${TIMESTAMP}"
              
              # 创建备份
              curl -X POST "http://weaviate:8080/v1/backups/filesystem" \
                -H "Content-Type: application/json" \
                -d "{
                  \"id\": \"$BACKUP_ID\",
                  \"include\": [\"DocumentChunk\", \"QueryVector\"]
                }"
              
              # 等待备份完成
              while true; do
                STATUS=$(curl -s "http://weaviate:8080/v1/backups/filesystem/$BACKUP_ID" | jq -r '.status')
                if [ "$STATUS" = "SUCCESS" ]; then
                  echo "Backup completed successfully"
                  break
                elif [ "$STATUS" = "FAILED" ]; then
                  echo "Backup failed"
                  exit 1
                fi
                sleep 30
              done
          restartPolicy: OnFailure
```

#### Neo4j 备份

```bash
#!/bin/bash
# backup/neo4j-backup.sh

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/neo4j_${TIMESTAMP}"

# 创建备份目录
mkdir -p $BACKUP_DIR

# 执行备份
neo4j-admin database backup --to-path=$BACKUP_DIR neo4j

# 压缩备份
tar -czf "${BACKUP_DIR}.tar.gz" -C /backup "neo4j_${TIMESTAMP}"

# 上传到 MinIO
mc cp "${BACKUP_DIR}.tar.gz" minio/knowledge-rag-backups/neo4j/

# 清理本地文件
rm -rf $BACKUP_DIR "${BACKUP_DIR}.tar.gz"

# 清理7天前的备份
mc rm --recursive --force --older-than 7d minio/knowledge-rag-backups/neo4j/
```

### 恢复策略

#### 数据库恢复脚本

```bash
#!/bin/bash
# recovery/restore-databases.sh

set -e

BACKUP_DATE=${1:-$(date +%Y%m%d)}
NAMESPACE=${2:-knowledge-rag-prod}

echo "Starting database restoration for date: $BACKUP_DATE"

# 1. PostgreSQL 恢复
echo "Restoring PostgreSQL..."
POSTGRES_BACKUP=$(mc find minio/knowledge-rag-backups/postgres/ --name "*${BACKUP_DATE}*.sql.gz" | head -1)
if [ -n "$POSTGRES_BACKUP" ]; then
    # 下载备份文件
    mc cp "$POSTGRES_BACKUP" /tmp/postgres_backup.sql.gz
    gunzip /tmp/postgres_backup.sql.gz
    
    # 停止应用服务
    kubectl scale deployment --replicas=0 -n $NAMESPACE -l app.kubernetes.io/component=application
    
    # 恢复数据库
    kubectl exec -n $NAMESPACE postgresql-0 -- psql -U postgres -c "DROP DATABASE IF EXISTS knowledge_rag_main;"
    kubectl exec -n $NAMESPACE postgresql-0 -- psql -U postgres -c "CREATE DATABASE knowledge_rag_main;"
    kubectl exec -i -n $NAMESPACE postgresql-0 -- psql -U postgres -d knowledge_rag_main < /tmp/postgres_backup.sql
    
    rm /tmp/postgres_backup.sql
    echo "PostgreSQL restoration completed"
else
    echo "No PostgreSQL backup found for date: $BACKUP_DATE"
    exit 1
fi

# 2. Weaviate 恢复
echo "Restoring Weaviate..."
WEAVIATE_BACKUP_ID="backup_${BACKUP_DATE}_*"
curl -X POST "http://weaviate:8080/v1/backups/filesystem/$WEAVIATE_BACKUP_ID/restore" \
  -H "Content-Type: application/json" \
  -d '{
    "include": ["DocumentChunk", "QueryVector"]
  }'

# 等待恢复完成
while true; do
    STATUS=$(curl -s "http://weaviate:8080/v1/backups/filesystem/$WEAVIATE_BACKUP_ID/restore" | jq -r '.status')
    if [ "$STATUS" = "SUCCESS" ]; then
        echo "Weaviate restoration completed"
        break
    elif [ "$STATUS" = "FAILED" ]; then
        echo "Weaviate restoration failed"
        exit 1
    fi
    sleep 30
done

# 3. Neo4j 恢复
echo "Restoring Neo4j..."
NEO4J_BACKUP=$(mc find minio/knowledge-rag-backups/neo4j/ --name "*${BACKUP_DATE}*.tar.gz" | head -1)
if [ -n "$NEO4J_BACKUP" ]; then
    # 下载并解压备份
    mc cp "$NEO4J_BACKUP" /tmp/neo4j_backup.tar.gz
    tar -xzf /tmp/neo4j_backup.tar.gz -C /tmp/
    
    # 停止 Neo4j
    kubectl scale statefulset neo4j --replicas=0 -n $NAMESPACE
    
    # 恢复数据
    kubectl exec -n $NAMESPACE neo4j-0 -- neo4j-admin database restore --from-path=/tmp/neo4j_* neo4j
    
    # 重启 Neo4j
    kubectl scale statefulset neo4j --replicas=3 -n $NAMESPACE
    
    rm -rf /tmp/neo4j_* /tmp/neo4j_backup.tar.gz
    echo "Neo4j restoration completed"
else
    echo "No Neo4j backup found for date: $BACKUP_DATE"
fi

# 4. 重启应用服务
echo "Restarting application services..."
kubectl scale deployment --replicas=3 -n $NAMESPACE -l app.kubernetes.io/component=application

# 等待服务就绪
kubectl wait --for=condition=available --timeout=600s deployment -n $NAMESPACE -l app.kubernetes.io/component=application

echo "Database restoration completed successfully"
```

### 灾难恢复计划

#### RTO/RPO 目标

| 组件 | RTO (恢复时间目标) | RPO (恢复点目标) | 备份频率 |
|------|-------------------|------------------|----------|
| PostgreSQL | 30分钟 | 1小时 | 每小时增量，每日全量 |
| Weaviate | 1小时 | 4小时 | 每4小时 |
| Neo4j | 1小时 | 4小时 | 每4小时 |
| MinIO | 15分钟 | 15分钟 | 实时复制 |
| Redis | 5分钟 | 1小时 | 每小时 |
| 应用服务 | 10分钟 | 0 | 无状态，镜像重建 |

#### 故障场景和应对策略

1. **单个服务故障**
   - 自动重启和健康检查
   - 负载均衡器自动切换
   - 预期恢复时间：< 2分钟

2. **数据库故障**
   - 主从切换（PostgreSQL）
   - 集群自愈（Redis、Neo4j）
   - 备份恢复（最坏情况）
   - 预期恢复时间：5-30分钟

3. **整个可用区故障**
   - 跨可用区部署自动切换
   - 数据复制保证数据一致性
   - 预期恢复时间：< 10分钟

4. **完全灾难恢复**
   - 异地备份恢复
   - 重新部署整个系统
   - 预期恢复时间：2-4小时

✅ **部署策略设计已完成**

部署策略涵盖了完整的云原生Kubernetes部署架构，包括：
- 多环境Kubernetes集群配置
- 微服务和数据库的详细部署规范
- Helm Charts包管理和配置
- CI/CD自动化流水线
- 全面的监控告警体系
- 企业级备份和灾难恢复策略

系统具备高可用、可扩展、可观测的生产级部署能力。

---

# 安全标准和规范

## 安全架构概览

Knowledge_RAG系统采用多层防御安全架构，确保数据安全、访问控制和系统完整性。

```mermaid
graph TB
    subgraph "外部访问层"
        A["客户端应用"]
        B["Web浏览器"]
        C["移动应用"]
    end
    
    subgraph "网络安全层"
        D["WAF (Web应用防火墙)"]
        E["DDoS防护"]
        F["SSL/TLS终端"]
    end
    
    subgraph "API网关层"
        G["Kong Gateway"]
        H["JWT验证"]
        I["API限流"]
        J["请求验证"]
    end
    
    subgraph "应用安全层"
        K["身份认证服务"]
        L["授权服务"]
        M["审计日志"]
        N["数据验证"]
    end
    
    subgraph "数据安全层"
        O["数据加密"]
        P["密钥管理"]
        Q["数据脱敏"]
        R["备份加密"]
    end
    
    subgraph "基础设施安全层"
        S["Kubernetes RBAC"]
        T["网络策略"]
        U["Pod安全策略"]
        V["镜像扫描"]
    end
    
    A --> D
    B --> D
    C --> D
    D --> G
    E --> G
    F --> G
    G --> K
    H --> L
    I --> M
    J --> N
    K --> O
    L --> P
    M --> Q
    N --> R
    O --> S
    P --> T
    Q --> U
    R --> V
```

## 身份认证和授权

### JWT认证机制

```python
# security/jwt_auth.py
"""
JWT认证服务实现
提供用户身份验证和令牌管理功能
"""

import jwt
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

class JWTAuthService:
    """
    JWT认证服务类
    负责用户认证、令牌生成和验证
    """
    
    def __init__(self, private_key: str, public_key: str, algorithm: str = "RS256"):
        """
        初始化JWT认证服务
        
        Args:
            private_key: RSA私钥，用于签名
            public_key: RSA公钥，用于验证
            algorithm: 签名算法，默认RS256
        """
        self.private_key = serialization.load_pem_private_key(
            private_key.encode(), password=None
        )
        self.public_key = serialization.load_pem_public_key(
            public_key.encode()
        )
        self.algorithm = algorithm
        self.access_token_expire = timedelta(hours=1)
        self.refresh_token_expire = timedelta(days=7)
    
    def hash_password(self, password: str) -> str:
        """
        密码哈希处理
        
        Args:
            password: 明文密码
            
        Returns:
            str: 哈希后的密码
        """
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """
        验证密码
        
        Args:
            password: 明文密码
            hashed: 哈希密码
            
        Returns:
            bool: 验证结果
        """
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def generate_tokens(self, user_id: str, user_role: str, permissions: list) -> Dict[str, str]:
        """
        生成访问令牌和刷新令牌
        
        Args:
            user_id: 用户ID
            user_role: 用户角色
            permissions: 用户权限列表
            
        Returns:
            Dict[str, str]: 包含access_token和refresh_token的字典
        """
        now = datetime.utcnow()
        
        # 访问令牌载荷
        access_payload = {
            "user_id": user_id,
            "role": user_role,
            "permissions": permissions,
            "type": "access",
            "iat": now,
            "exp": now + self.access_token_expire,
            "jti": self._generate_jti()
        }
        
        # 刷新令牌载荷
        refresh_payload = {
            "user_id": user_id,
            "type": "refresh",
            "iat": now,
            "exp": now + self.refresh_token_expire,
            "jti": self._generate_jti()
        }
        
        access_token = jwt.encode(
            access_payload, self.private_key, algorithm=self.algorithm
        )
        refresh_token = jwt.encode(
            refresh_payload, self.private_key, algorithm=self.algorithm
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
            "expires_in": int(self.access_token_expire.total_seconds())
        }
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        验证JWT令牌
        
        Args:
            token: JWT令牌
            
        Returns:
            Optional[Dict[str, Any]]: 解码后的载荷，验证失败返回None
        """
        try:
            payload = jwt.decode(
                token, self.public_key, algorithms=[self.algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token has expired")
        except jwt.InvalidTokenError:
            raise AuthenticationError("Invalid token")
    
    def _generate_jti(self) -> str:
        """
        生成JWT ID
        
        Returns:
            str: 唯一的JWT ID
        """
        import uuid
        return str(uuid.uuid4())

class AuthenticationError(Exception):
    """认证异常类"""
    pass
```

### RBAC权限控制

```python
# security/rbac.py
"""
RBAC (基于角色的访问控制) 实现
定义角色、权限和访问控制逻辑
"""

from enum import Enum
from typing import List, Dict, Set
from dataclasses import dataclass

class Permission(Enum):
    """
    系统权限枚举
    定义所有可用的系统权限
    """
    # 用户管理权限
    USER_CREATE = "user:create"
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    
    # 文档管理权限
    DOCUMENT_UPLOAD = "document:upload"
    DOCUMENT_READ = "document:read"
    DOCUMENT_UPDATE = "document:update"
    DOCUMENT_DELETE = "document:delete"
    DOCUMENT_SHARE = "document:share"
    
    # 知识库权限
    KNOWLEDGE_QUERY = "knowledge:query"
    KNOWLEDGE_MANAGE = "knowledge:manage"
    KNOWLEDGE_EXPORT = "knowledge:export"
    
    # 系统管理权限
    SYSTEM_CONFIG = "system:config"
    SYSTEM_MONITOR = "system:monitor"
    SYSTEM_AUDIT = "system:audit"
    
    # API权限
    API_ACCESS = "api:access"
    API_ADMIN = "api:admin"

class Role(Enum):
    """
    系统角色枚举
    定义系统中的用户角色
    """
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"
    GUEST = "guest"

@dataclass
class RoleDefinition:
    """
    角色定义数据类
    包含角色名称、描述和权限列表
    """
    name: str
    description: str
    permissions: Set[Permission]
    inherits_from: List[str] = None

class RBACService:
    """
    RBAC服务类
    提供角色和权限管理功能
    """
    
    def __init__(self):
        """
        初始化RBAC服务
        定义系统角色和权限映射
        """
        self.role_definitions = self._initialize_roles()
        self.user_roles: Dict[str, Set[str]] = {}
    
    def _initialize_roles(self) -> Dict[str, RoleDefinition]:
        """
        初始化系统角色定义
        
        Returns:
            Dict[str, RoleDefinition]: 角色定义映射
        """
        return {
            Role.SUPER_ADMIN.value: RoleDefinition(
                name="超级管理员",
                description="拥有系统所有权限",
                permissions=set(Permission)
            ),
            Role.ADMIN.value: RoleDefinition(
                name="管理员",
                description="系统管理权限",
                permissions={
                    Permission.USER_CREATE, Permission.USER_READ, 
                    Permission.USER_UPDATE, Permission.USER_DELETE,
                    Permission.DOCUMENT_UPLOAD, Permission.DOCUMENT_READ,
                    Permission.DOCUMENT_UPDATE, Permission.DOCUMENT_DELETE,
                    Permission.DOCUMENT_SHARE, Permission.KNOWLEDGE_QUERY,
                    Permission.KNOWLEDGE_MANAGE, Permission.SYSTEM_CONFIG,
                    Permission.SYSTEM_MONITOR, Permission.API_ACCESS
                }
            ),
            Role.MANAGER.value: RoleDefinition(
                name="管理者",
                description="业务管理权限",
                permissions={
                    Permission.USER_READ, Permission.DOCUMENT_UPLOAD,
                    Permission.DOCUMENT_READ, Permission.DOCUMENT_UPDATE,
                    Permission.DOCUMENT_SHARE, Permission.KNOWLEDGE_QUERY,
                    Permission.KNOWLEDGE_MANAGE, Permission.API_ACCESS
                }
            ),
            Role.USER.value: RoleDefinition(
                name="普通用户",
                description="基础使用权限",
                permissions={
                    Permission.DOCUMENT_UPLOAD, Permission.DOCUMENT_READ,
                    Permission.DOCUMENT_UPDATE, Permission.KNOWLEDGE_QUERY,
                    Permission.API_ACCESS
                }
            ),
            Role.GUEST.value: RoleDefinition(
                name="访客",
                description="只读权限",
                permissions={
                    Permission.DOCUMENT_READ, Permission.KNOWLEDGE_QUERY
                }
            )
        }
    
    def assign_role(self, user_id: str, role: str) -> bool:
        """
        为用户分配角色
        
        Args:
            user_id: 用户ID
            role: 角色名称
            
        Returns:
            bool: 分配结果
        """
        if role not in self.role_definitions:
            return False
        
        if user_id not in self.user_roles:
            self.user_roles[user_id] = set()
        
        self.user_roles[user_id].add(role)
        return True
    
    def remove_role(self, user_id: str, role: str) -> bool:
        """
        移除用户角色
        
        Args:
            user_id: 用户ID
            role: 角色名称
            
        Returns:
            bool: 移除结果
        """
        if user_id in self.user_roles and role in self.user_roles[user_id]:
            self.user_roles[user_id].remove(role)
            return True
        return False
    
    def get_user_permissions(self, user_id: str) -> Set[Permission]:
        """
        获取用户所有权限
        
        Args:
            user_id: 用户ID
            
        Returns:
            Set[Permission]: 用户权限集合
        """
        permissions = set()
        user_roles = self.user_roles.get(user_id, set())
        
        for role in user_roles:
            if role in self.role_definitions:
                permissions.update(self.role_definitions[role].permissions)
        
        return permissions
    
    def check_permission(self, user_id: str, permission: Permission) -> bool:
        """
        检查用户是否拥有特定权限
        
        Args:
            user_id: 用户ID
            permission: 权限
            
        Returns:
            bool: 权限检查结果
        """
        user_permissions = self.get_user_permissions(user_id)
        return permission in user_permissions
```

### API安全中间件

```python
# security/middleware.py
"""
API安全中间件
提供请求验证、限流、审计等安全功能
"""

import time
import json
import hashlib
from typing import Dict, Optional
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import redis

class SecurityMiddleware(BaseHTTPMiddleware):
    """
    安全中间件类
    处理请求安全验证和限流
    """
    
    def __init__(self, app, redis_client: redis.Redis, jwt_service, rbac_service):
        """
        初始化安全中间件
        
        Args:
            app: FastAPI应用实例
            redis_client: Redis客户端
            jwt_service: JWT认证服务
            rbac_service: RBAC权限服务
        """
        super().__init__(app)
        self.redis_client = redis_client
        self.jwt_service = jwt_service
        self.rbac_service = rbac_service
        self.rate_limit_window = 3600  # 1小时
        self.rate_limit_max_requests = 1000  # 每小时最大请求数
    
    async def dispatch(self, request: Request, call_next):
        """
        处理HTTP请求
        
        Args:
            request: HTTP请求对象
            call_next: 下一个中间件或路由处理器
            
        Returns:
            Response: HTTP响应
        """
        start_time = time.time()
        
        try:
            # 1. IP白名单检查
            if not self._check_ip_whitelist(request):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="IP address not allowed"
                )
            
            # 2. 请求限流
            if not self._check_rate_limit(request):
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded"
                )
            
            # 3. 请求验证
            self._validate_request(request)
            
            # 4. 身份认证
            user_info = await self._authenticate_request(request)
            if user_info:
                request.state.user = user_info
            
            # 5. 权限检查
            if not self._check_authorization(request):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
            
            # 处理请求
            response = await call_next(request)
            
            # 6. 审计日志
            await self._log_request(request, response, time.time() - start_time)
            
            return response
            
        except HTTPException:
            raise
        except Exception as e:
            # 记录错误日志
            await self._log_error(request, str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def _check_ip_whitelist(self, request: Request) -> bool:
        """
        检查IP白名单
        
        Args:
            request: HTTP请求对象
            
        Returns:
            bool: 检查结果
        """
        client_ip = self._get_client_ip(request)
        
        # 从Redis获取IP白名单
        whitelist = self.redis_client.smembers("ip_whitelist")
        if not whitelist:
            return True  # 如果没有配置白名单，则允许所有IP
        
        return client_ip.encode() in whitelist
    
    def _check_rate_limit(self, request: Request) -> bool:
        """
        检查请求限流
        
        Args:
            request: HTTP请求对象
            
        Returns:
            bool: 检查结果
        """
        client_ip = self._get_client_ip(request)
        key = f"rate_limit:{client_ip}"
        
        current_requests = self.redis_client.get(key)
        if current_requests is None:
            # 首次请求，设置计数器
            self.redis_client.setex(key, self.rate_limit_window, 1)
            return True
        
        current_requests = int(current_requests)
        if current_requests >= self.rate_limit_max_requests:
            return False
        
        # 增加请求计数
        self.redis_client.incr(key)
        return True
    
    def _validate_request(self, request: Request):
        """
        验证请求格式和内容
        
        Args:
            request: HTTP请求对象
        """
        # 检查请求头
        if "user-agent" not in request.headers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing User-Agent header"
            )
        
        # 检查Content-Type
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")
            if not content_type.startswith("application/json"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid Content-Type"
                )
    
    async def _authenticate_request(self, request: Request) -> Optional[Dict]:
        """
        认证请求
        
        Args:
            request: HTTP请求对象
            
        Returns:
            Optional[Dict]: 用户信息，未认证返回None
        """
        # 跳过不需要认证的路径
        if request.url.path in ["/health", "/docs", "/openapi.json"]:
            return None
        
        authorization = request.headers.get("authorization")
        if not authorization:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing authorization header"
            )
        
        try:
            scheme, token = authorization.split(" ", 1)
            if scheme.lower() != "bearer":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication scheme"
                )
            
            payload = self.jwt_service.verify_token(token)
            return payload
            
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header format"
            )
    
    def _check_authorization(self, request: Request) -> bool:
        """
        检查用户权限
        
        Args:
            request: HTTP请求对象
            
        Returns:
            bool: 权限检查结果
        """
        # 跳过不需要授权的路径
        if request.url.path in ["/health", "/docs", "/openapi.json"]:
            return True
        
        if not hasattr(request.state, "user"):
            return False
        
        user_info = request.state.user
        user_id = user_info.get("user_id")
        
        # 根据路径和方法确定所需权限
        required_permission = self._get_required_permission(request)
        if not required_permission:
            return True
        
        return self.rbac_service.check_permission(user_id, required_permission)
    
    def _get_required_permission(self, request: Request) -> Optional[Permission]:
        """
        根据请求路径和方法获取所需权限
        
        Args:
            request: HTTP请求对象
            
        Returns:
            Optional[Permission]: 所需权限
        """
        path = request.url.path
        method = request.method
        
        # 权限映射规则
        permission_map = {
            ("/api/v1/users", "POST"): Permission.USER_CREATE,
            ("/api/v1/users", "GET"): Permission.USER_READ,
            ("/api/v1/users", "PUT"): Permission.USER_UPDATE,
            ("/api/v1/users", "DELETE"): Permission.USER_DELETE,
            ("/api/v1/documents", "POST"): Permission.DOCUMENT_UPLOAD,
            ("/api/v1/documents", "GET"): Permission.DOCUMENT_READ,
            ("/api/v1/documents", "PUT"): Permission.DOCUMENT_UPDATE,
            ("/api/v1/documents", "DELETE"): Permission.DOCUMENT_DELETE,
            ("/api/v1/knowledge/query", "POST"): Permission.KNOWLEDGE_QUERY,
        }
        
        return permission_map.get((path, method))
    
    def _get_client_ip(self, request: Request) -> str:
        """
        获取客户端IP地址
        
        Args:
            request: HTTP请求对象
            
        Returns:
            str: 客户端IP地址
        """
        # 检查代理头
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        return request.client.host
    
    async def _log_request(self, request: Request, response: Response, duration: float):
        """
        记录请求审计日志
        
        Args:
            request: HTTP请求对象
            response: HTTP响应对象
            duration: 请求处理时间
        """
        log_data = {
            "timestamp": time.time(),
            "method": request.method,
            "path": request.url.path,
            "query_params": str(request.query_params),
            "client_ip": self._get_client_ip(request),
            "user_agent": request.headers.get("user-agent", ""),
            "status_code": response.status_code,
            "duration": duration,
            "user_id": getattr(request.state, "user", {}).get("user_id"),
        }
        
        # 发送到审计日志队列
        self.redis_client.lpush("audit_logs", json.dumps(log_data))
    
    async def _log_error(self, request: Request, error: str):
        """
        记录错误日志
        
        Args:
            request: HTTP请求对象
            error: 错误信息
        """
        error_data = {
            "timestamp": time.time(),
            "method": request.method,
            "path": request.url.path,
            "client_ip": self._get_client_ip(request),
            "error": error,
            "user_id": getattr(request.state, "user", {}).get("user_id"),
        }
        
        # 发送到错误日志队列
        self.redis_client.lpush("error_logs", json.dumps(error_data))
```

## 数据加密和密钥管理

### 数据加密策略

```python
# security/encryption.py
"""
数据加密服务
提供数据加密、解密和密钥管理功能
"""

import os
import base64
from typing import Union, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

class EncryptionService:
    """
    加密服务类
    提供对称和非对称加密功能
    """
    
    def __init__(self, master_key: Optional[str] = None):
        """
        初始化加密服务
        
        Args:
            master_key: 主密钥，用于派生其他密钥
        """
        self.master_key = master_key or os.environ.get('MASTER_KEY')
        if not self.master_key:
            raise ValueError("Master key is required")
        
        self.fernet = self._create_fernet_key()
    
    def _create_fernet_key(self) -> Fernet:
        """
        创建Fernet密钥
        
        Returns:
            Fernet: Fernet加密实例
        """
        # 使用PBKDF2从主密钥派生Fernet密钥
        salt = b'knowledge_rag_salt'  # 在生产环境中应使用随机盐
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.master_key.encode()))
        return Fernet(key)
    
    def encrypt_data(self, data: Union[str, bytes]) -> str:
        """
        加密数据
        
        Args:
            data: 要加密的数据
            
        Returns:
            str: 加密后的数据（Base64编码）
        """
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        encrypted_data = self.fernet.encrypt(data)
        return base64.urlsafe_b64encode(encrypted_data).decode('utf-8')
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """
        解密数据
        
        Args:
            encrypted_data: 加密的数据（Base64编码）
            
        Returns:
            str: 解密后的数据
        """
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode('utf-8'))
        decrypted_data = self.fernet.decrypt(encrypted_bytes)
        return decrypted_data.decode('utf-8')
    
    def encrypt_file(self, file_path: str, output_path: str) -> bool:
        """
        加密文件
        
        Args:
            file_path: 源文件路径
            output_path: 加密文件输出路径
            
        Returns:
            bool: 加密结果
        """
        try:
            with open(file_path, 'rb') as file:
                file_data = file.read()
            
            encrypted_data = self.fernet.encrypt(file_data)
            
            with open(output_path, 'wb') as encrypted_file:
                encrypted_file.write(encrypted_data)
            
            return True
        except Exception as e:
            print(f"File encryption failed: {e}")
            return False
    
    def decrypt_file(self, encrypted_file_path: str, output_path: str) -> bool:
        """
        解密文件
        
        Args:
            encrypted_file_path: 加密文件路径
            output_path: 解密文件输出路径
            
        Returns:
            bool: 解密结果
        """
        try:
            with open(encrypted_file_path, 'rb') as encrypted_file:
                encrypted_data = encrypted_file.read()
            
            decrypted_data = self.fernet.decrypt(encrypted_data)
            
            with open(output_path, 'wb') as file:
                file.write(decrypted_data)
            
            return True
        except Exception as e:
            print(f"File decryption failed: {e}")
            return False

class RSAEncryption:
    """
    RSA非对称加密类
    用于密钥交换和数字签名
    """
    
    def __init__(self, key_size: int = 2048):
        """
        初始化RSA加密
        
        Args:
            key_size: RSA密钥长度
        """
        self.key_size = key_size
        self.private_key = None
        self.public_key = None
    
    def generate_key_pair(self) -> tuple:
        """
        生成RSA密钥对
        
        Returns:
            tuple: (私钥PEM, 公钥PEM)
        """
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=self.key_size
        )
        self.public_key = self.private_key.public_key()
        
        private_pem = self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        public_pem = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        return private_pem.decode('utf-8'), public_pem.decode('utf-8')
    
    def load_private_key(self, private_key_pem: str):
        """
        加载私钥
        
        Args:
            private_key_pem: 私钥PEM格式字符串
        """
        self.private_key = serialization.load_pem_private_key(
            private_key_pem.encode('utf-8'),
            password=None
        )
    
    def load_public_key(self, public_key_pem: str):
        """
        加载公钥
        
        Args:
            public_key_pem: 公钥PEM格式字符串
        """
        self.public_key = serialization.load_pem_public_key(
            public_key_pem.encode('utf-8')
        )
    
    def encrypt(self, data: str) -> str:
        """
        使用公钥加密数据
        
        Args:
            data: 要加密的数据
            
        Returns:
            str: 加密后的数据（Base64编码）
        """
        if not self.public_key:
            raise ValueError("Public key not loaded")
        
        encrypted_data = self.public_key.encrypt(
            data.encode('utf-8'),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        return base64.b64encode(encrypted_data).decode('utf-8')
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        使用私钥解密数据
        
        Args:
            encrypted_data: 加密的数据（Base64编码）
            
        Returns:
            str: 解密后的数据
        """
        if not self.private_key:
            raise ValueError("Private key not loaded")
        
        encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
        decrypted_data = self.private_key.decrypt(
            encrypted_bytes,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        return decrypted_data.decode('utf-8')
```

### 密钥管理配置

```yaml
# k8s/security/vault-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: vault-config
  namespace: knowledge-rag
data:
  vault.hcl: |
    ui = true
    
    listener "tcp" {
      address = "0.0.0.0:8200"
      tls_disable = 1
    }
    
    storage "postgresql" {
      connection_url = "postgres://vault:vault_password@postgres:5432/vault?sslmode=disable"
    }
    
    default_lease_ttl = "168h"
    max_lease_ttl = "720h"
    
    api_addr = "http://vault:8200"
    cluster_addr = "http://vault:8201"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vault
  namespace: knowledge-rag
spec:
  replicas: 1
  selector:
    matchLabels:
      app: vault
  template:
    metadata:
      labels:
        app: vault
    spec:
      containers:
      - name: vault
        image: vault:1.15.2
        ports:
        - containerPort: 8200
          name: vault-port
        - containerPort: 8201
          name: cluster-port
        env:
        - name: VAULT_CONFIG_DIR
          value: "/vault/config"
        - name: VAULT_DEV_ROOT_TOKEN_ID
          value: "root-token"
        volumeMounts:
        - name: vault-config
          mountPath: /vault/config
        command:
        - vault
        - server
        - -config=/vault/config/vault.hcl
        securityContext:
          capabilities:
            add:
            - IPC_LOCK
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
      volumes:
      - name: vault-config
        configMap:
          name: vault-config
---
apiVersion: v1
kind: Service
metadata:
  name: vault
  namespace: knowledge-rag
spec:
  selector:
    app: vault
  ports:
  - name: vault-port
    port: 8200
    targetPort: 8200
  - name: cluster-port
    port: 8201
    targetPort: 8201
```

## 网络安全配置

### Kubernetes网络策略

```yaml
# k8s/security/network-policies.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: knowledge-rag
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-api-gateway
  namespace: knowledge-rag
spec:
  podSelector:
    matchLabels:
      app: api-gateway
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - podSelector:
        matchLabels:
          tier: backend
    ports:
    - protocol: TCP
      port: 8000
  - to: []  # 允许DNS查询
    ports:
    - protocol: UDP
      port: 53
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-backend-services
  namespace: knowledge-rag
spec:
  podSelector:
    matchLabels:
      tier: backend
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: api-gateway
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - podSelector:
        matchLabels:
          tier: database
    ports:
    - protocol: TCP
      port: 5432  # PostgreSQL
    - protocol: TCP
      port: 8080  # Weaviate
    - protocol: TCP
      port: 7474  # Neo4j HTTP
    - protocol: TCP
      port: 7687  # Neo4j Bolt
    - protocol: TCP
      port: 9000  # MinIO
    - protocol: TCP
      port: 6379  # Redis
  - to: []  # 允许DNS查询
    ports:
    - protocol: UDP
      port: 53
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-database-access
  namespace: knowledge-rag
spec:
  podSelector:
    matchLabels:
      tier: database
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          tier: backend
    ports:
    - protocol: TCP
      port: 5432  # PostgreSQL
    - protocol: TCP
      port: 8080  # Weaviate
    - protocol: TCP
      port: 7474  # Neo4j HTTP
    - protocol: TCP
      port: 7687  # Neo4j Bolt
    - protocol: TCP
      port: 9000  # MinIO
    - protocol: TCP
      port: 6379  # Redis
```

### SSL/TLS配置

```yaml
# k8s/security/tls-config.yaml
apiVersion: v1
kind: Secret
metadata:
  name: tls-secret
  namespace: knowledge-rag
type: kubernetes.io/tls
data:
  tls.crt: LS0tLS1CRUdJTi... # Base64编码的证书
  tls.key: LS0tLS1CRUdJTi... # Base64编码的私钥
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: knowledge-rag-ingress
  namespace: knowledge-rag
  annotations:
    kubernetes.io/ingress.class: "nginx"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
    nginx.ingress.kubernetes.io/ssl-protocols: "TLSv1.2 TLSv1.3"
    nginx.ingress.kubernetes.io/ssl-ciphers: "ECDHE-RSA-AES128-GCM-SHA256,ECDHE-RSA-AES256-GCM-SHA384"
    nginx.ingress.kubernetes.io/proxy-body-size: "50m"
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/rate-limit-window: "1m"
spec:
  tls:
  - hosts:
    - api.knowledge-rag.com
    secretName: tls-secret
  rules:
  - host: api.knowledge-rag.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api-gateway
            port:
              number: 8000
```

## 容器安全配置

### Pod安全策略

```yaml
# k8s/security/pod-security-policy.yaml
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: knowledge-rag-psp
spec:
  privileged: false
  allowPrivilegeEscalation: false
  requiredDropCapabilities:
    - ALL
  volumes:
    - 'configMap'
    - 'emptyDir'
    - 'projected'
    - 'secret'
    - 'downwardAPI'
    - 'persistentVolumeClaim'
  runAsUser:
    rule: 'MustRunAsNonRoot'
  seLinux:
    rule: 'RunAsAny'
  fsGroup:
    rule: 'RunAsAny'
  readOnlyRootFilesystem: true
  seccompProfile:
    type: RuntimeDefault
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: knowledge-rag-psp-user
rules:
- apiGroups: ['policy']
  resources: ['podsecuritypolicies']
  verbs: ['use']
  resourceNames:
  - knowledge-rag-psp
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: knowledge-rag-psp-binding
roleRef:
  kind: ClusterRole
  name: knowledge-rag-psp-user
  apiGroup: rbac.authorization.k8s.io
subjects:
- kind: ServiceAccount
  name: default
  namespace: knowledge-rag
```

### 容器镜像安全扫描

```yaml
# .github/workflows/security-scan.yml
name: Security Scan

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  security-scan:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v3
    
    - name: Build Docker image
      run: |
        docker build -t knowledge-rag:${{ github.sha }} .
    
    - name: Run Trivy vulnerability scanner
      uses: aquasecurity/trivy-action@master
      with:
        image-ref: 'knowledge-rag:${{ github.sha }}'
        format: 'sarif'
        output: 'trivy-results.sarif'
    
    - name: Upload Trivy scan results to GitHub Security tab
      uses: github/codeql-action/upload-sarif@v2
      with:
        sarif_file: 'trivy-results.sarif'
    
    - name: Run Snyk to check for vulnerabilities
      uses: snyk/actions/docker@master
      env:
        SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
      with:
        image: knowledge-rag:${{ github.sha }}
        args: --severity-threshold=high
    
    - name: Run OWASP Dependency Check
      uses: dependency-check/Dependency-Check_Action@main
      with:
        project: 'Knowledge_RAG'
        path: '.'
        format: 'ALL'
        args: >
          --enableRetired
          --enableExperimental
          --failOnCVSS 7
    
    - name: Upload OWASP results
       uses: actions/upload-artifact@v4
       with:
         name: dependency-check-report
         path: reports/
```

## 合规性和审计

### 数据保护合规性

```python
# security/compliance.py
"""
合规性检查服务
提供GDPR、CCPA等数据保护法规的合规性检查
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from enum import Enum
import json

class DataCategory(Enum):
    """数据分类枚举"""
    PERSONAL = "personal"  # 个人数据
    SENSITIVE = "sensitive"  # 敏感数据
    PUBLIC = "public"  # 公开数据
    INTERNAL = "internal"  # 内部数据

class ProcessingPurpose(Enum):
    """数据处理目的枚举"""
    SERVICE_PROVISION = "service_provision"  # 服务提供
    ANALYTICS = "analytics"  # 分析
    MARKETING = "marketing"  # 营销
    SECURITY = "security"  # 安全

class ComplianceService:
    """
    合规性服务类
    处理数据保护法规的合规性检查
    """
    
    def __init__(self, redis_client):
        """
        初始化合规性服务
        
        Args:
            redis_client: Redis客户端
        """
        self.redis_client = redis_client
        self.retention_policies = {
            DataCategory.PERSONAL: timedelta(days=365 * 2),  # 2年
            DataCategory.SENSITIVE: timedelta(days=365 * 1),  # 1年
            DataCategory.PUBLIC: timedelta(days=365 * 5),  # 5年
            DataCategory.INTERNAL: timedelta(days=365 * 3)  # 3年
        }
    
    def register_data_processing(self, 
                               user_id: str,
                               data_category: DataCategory,
                               purpose: ProcessingPurpose,
                               data_description: str,
                               legal_basis: str) -> str:
        """
        注册数据处理活动
        
        Args:
            user_id: 用户ID
            data_category: 数据分类
            purpose: 处理目的
            data_description: 数据描述
            legal_basis: 法律依据
            
        Returns:
            str: 处理记录ID
        """
        processing_id = f"proc_{user_id}_{datetime.now().timestamp()}"
        
        processing_record = {
            "id": processing_id,
            "user_id": user_id,
            "data_category": data_category.value,
            "purpose": purpose.value,
            "data_description": data_description,
            "legal_basis": legal_basis,
            "created_at": datetime.now().isoformat(),
            "retention_until": (datetime.now() + self.retention_policies[data_category]).isoformat()
        }
        
        # 存储处理记录
        self.redis_client.hset(
            f"processing_records:{user_id}",
            processing_id,
            json.dumps(processing_record)
        )
        
        # 设置过期时间
        self.redis_client.expire(
            f"processing_records:{user_id}",
            int(self.retention_policies[data_category].total_seconds())
        )
        
        return processing_id
    
    def check_consent(self, user_id: str, purpose: ProcessingPurpose) -> bool:
        """
        检查用户同意状态
        
        Args:
            user_id: 用户ID
            purpose: 处理目的
            
        Returns:
            bool: 是否已同意
        """
        consent_key = f"consent:{user_id}:{purpose.value}"
        consent_data = self.redis_client.get(consent_key)
        
        if not consent_data:
            return False
        
        consent_info = json.loads(consent_data)
        consent_time = datetime.fromisoformat(consent_info['timestamp'])
        
        # 检查同意是否在有效期内（13个月）
        if datetime.now() - consent_time > timedelta(days=395):
            self.redis_client.delete(consent_key)
            return False
        
        return consent_info['granted']
    
    def record_consent(self, user_id: str, purpose: ProcessingPurpose, granted: bool) -> bool:
        """
        记录用户同意状态
        
        Args:
            user_id: 用户ID
            purpose: 处理目的
            granted: 是否同意
            
        Returns:
            bool: 记录结果
        """
        consent_key = f"consent:{user_id}:{purpose.value}"
        consent_data = {
            "user_id": user_id,
            "purpose": purpose.value,
            "granted": granted,
            "timestamp": datetime.now().isoformat(),
            "ip_address": "127.0.0.1",  # 应从请求中获取
            "user_agent": "Unknown"  # 应从请求中获取
        }
        
        self.redis_client.setex(
            consent_key,
            timedelta(days=395),  # 13个月
            json.dumps(consent_data)
        )
        
        return True
    
    def handle_data_subject_request(self, user_id: str, request_type: str) -> Dict:
        """
        处理数据主体权利请求
        
        Args:
            user_id: 用户ID
            request_type: 请求类型（access, rectification, erasure, portability）
            
        Returns:
            Dict: 处理结果
        """
        if request_type == "access":
            return self._handle_access_request(user_id)
        elif request_type == "rectification":
            return self._handle_rectification_request(user_id)
        elif request_type == "erasure":
            return self._handle_erasure_request(user_id)
        elif request_type == "portability":
            return self._handle_portability_request(user_id)
        else:
            return {"error": "Invalid request type"}
    
    def _handle_access_request(self, user_id: str) -> Dict:
        """
        处理数据访问请求
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict: 用户数据
        """
        # 收集用户所有数据
        user_data = {
            "user_id": user_id,
            "processing_records": [],
            "consent_records": [],
            "personal_data": {}
        }
        
        # 获取处理记录
        processing_records = self.redis_client.hgetall(f"processing_records:{user_id}")
        for record_id, record_data in processing_records.items():
            user_data["processing_records"].append(json.loads(record_data))
        
        # 获取同意记录
        consent_keys = self.redis_client.keys(f"consent:{user_id}:*")
        for key in consent_keys:
            consent_data = self.redis_client.get(key)
            if consent_data:
                user_data["consent_records"].append(json.loads(consent_data))
        
        return user_data
    
    def _handle_erasure_request(self, user_id: str) -> Dict:
        """
        处理数据删除请求
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict: 删除结果
        """
        try:
            # 删除处理记录
            self.redis_client.delete(f"processing_records:{user_id}")
            
            # 删除同意记录
            consent_keys = self.redis_client.keys(f"consent:{user_id}:*")
            if consent_keys:
                self.redis_client.delete(*consent_keys)
            
            # 记录删除操作
            deletion_record = {
                "user_id": user_id,
                "deleted_at": datetime.now().isoformat(),
                "deletion_reason": "user_request"
            }
            
            self.redis_client.setex(
                f"deletion_log:{user_id}",
                timedelta(days=365 * 3),  # 保留3年用于审计
                json.dumps(deletion_record)
            )
            
            return {"status": "success", "message": "Data deleted successfully"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
```

### 安全监控和告警

```python
# security/monitoring.py
"""
安全监控服务
提供实时安全事件监控和告警功能
"""

import json
import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass

class SecurityEventType(Enum):
    """安全事件类型枚举"""
    LOGIN_FAILURE = "login_failure"
    SUSPICIOUS_ACCESS = "suspicious_access"
    DATA_BREACH = "data_breach"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    MALWARE_DETECTED = "malware_detected"
    DDOS_ATTACK = "ddos_attack"
    SQL_INJECTION = "sql_injection"
    XSS_ATTEMPT = "xss_attempt"

class SeverityLevel(Enum):
    """严重程度枚举"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class SecurityEvent:
    """安全事件数据类"""
    event_id: str
    event_type: SecurityEventType
    severity: SeverityLevel
    timestamp: datetime
    source_ip: str
    user_id: Optional[str]
    description: str
    metadata: Dict

class SecurityMonitoringService:
    """
    安全监控服务类
    提供实时安全事件监控和告警
    """
    
    def __init__(self, redis_client, notification_service):
        """
        初始化安全监控服务
        
        Args:
            redis_client: Redis客户端
            notification_service: 通知服务
        """
        self.redis_client = redis_client
        self.notification_service = notification_service
        
        # 配置告警阈值
        self.alert_thresholds = {
            SecurityEventType.LOGIN_FAILURE: {
                "count": 5,
                "window": timedelta(minutes=15),
                "severity": SeverityLevel.MEDIUM
            },
            SecurityEventType.SUSPICIOUS_ACCESS: {
                "count": 3,
                "window": timedelta(minutes=10),
                "severity": SeverityLevel.HIGH
            },
            SecurityEventType.SQL_INJECTION: {
                "count": 1,
                "window": timedelta(minutes=1),
                "severity": SeverityLevel.CRITICAL
            }
        }
    
    async def log_security_event(self, event: SecurityEvent) -> bool:
        """
        记录安全事件
        
        Args:
            event: 安全事件
            
        Returns:
            bool: 记录结果
        """
        try:
            # 序列化事件数据
            event_data = {
                "event_id": event.event_id,
                "event_type": event.event_type.value,
                "severity": event.severity.value,
                "timestamp": event.timestamp.isoformat(),
                "source_ip": event.source_ip,
                "user_id": event.user_id,
                "description": event.description,
                "metadata": event.metadata
            }
            
            # 存储到Redis
            event_key = f"security_events:{event.timestamp.strftime('%Y-%m-%d')}:{event.event_id}"
            self.redis_client.setex(
                event_key,
                timedelta(days=90),  # 保留90天
                json.dumps(event_data)
            )
            
            # 更新事件计数器
            await self._update_event_counter(event)
            
            # 检查是否需要触发告警
            await self._check_alert_conditions(event)
            
            return True
        except Exception as e:
            print(f"Failed to log security event: {e}")
            return False
    
    async def _update_event_counter(self, event: SecurityEvent):
        """
        更新事件计数器
        
        Args:
            event: 安全事件
        """
        counter_key = f"event_counter:{event.event_type.value}:{event.source_ip}"
        
        # 使用滑动窗口计数
        current_time = int(event.timestamp.timestamp())
        
        # 添加当前事件
        self.redis_client.zadd(counter_key, {event.event_id: current_time})
        
        # 清理过期事件
        threshold_config = self.alert_thresholds.get(event.event_type)
        if threshold_config:
            window_start = current_time - int(threshold_config["window"].total_seconds())
            self.redis_client.zremrangebyscore(counter_key, 0, window_start)
        
        # 设置过期时间
        self.redis_client.expire(counter_key, 3600)  # 1小时
    
    async def _check_alert_conditions(self, event: SecurityEvent):
        """
        检查告警条件
        
        Args:
            event: 安全事件
        """
        threshold_config = self.alert_thresholds.get(event.event_type)
        if not threshold_config:
            return
        
        counter_key = f"event_counter:{event.event_type.value}:{event.source_ip}"
        
        # 获取窗口内的事件数量
        current_time = int(event.timestamp.timestamp())
        window_start = current_time - int(threshold_config["window"].total_seconds())
        
        event_count = self.redis_client.zcount(counter_key, window_start, current_time)
        
        # 检查是否超过阈值
        if event_count >= threshold_config["count"]:
            await self._trigger_alert(event, event_count, threshold_config)
    
    async def _trigger_alert(self, event: SecurityEvent, event_count: int, threshold_config: Dict):
        """
        触发安全告警
        
        Args:
            event: 触发告警的事件
            event_count: 事件数量
            threshold_config: 阈值配置
        """
        alert_data = {
            "alert_id": f"alert_{event.event_type.value}_{int(datetime.now().timestamp())}",
            "event_type": event.event_type.value,
            "severity": threshold_config["severity"].value,
            "source_ip": event.source_ip,
            "event_count": event_count,
            "time_window": str(threshold_config["window"]),
            "timestamp": datetime.now().isoformat(),
            "description": f"Security alert: {event_count} {event.event_type.value} events from {event.source_ip}"
        }
        
        # 发送告警通知
        await self.notification_service.send_security_alert(alert_data)
        
        # 记录告警
        alert_key = f"security_alerts:{alert_data['alert_id']}"
        self.redis_client.setex(
            alert_key,
            timedelta(days=30),  # 保留30天
            json.dumps(alert_data)
        )
    
    async def get_security_dashboard_data(self) -> Dict:
        """
        获取安全仪表板数据
        
        Returns:
            Dict: 仪表板数据
        """
        dashboard_data = {
            "total_events_today": 0,
            "critical_alerts": 0,
            "top_threat_sources": [],
            "event_distribution": {},
            "recent_alerts": []
        }
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        # 获取今日事件总数
        event_keys = self.redis_client.keys(f"security_events:{today}:*")
        dashboard_data["total_events_today"] = len(event_keys)
        
        # 获取关键告警数量
        alert_keys = self.redis_client.keys("security_alerts:*")
        critical_count = 0
        recent_alerts = []
        
        for key in alert_keys:
            alert_data = self.redis_client.get(key)
            if alert_data:
                alert = json.loads(alert_data)
                if alert["severity"] == SeverityLevel.CRITICAL.value:
                    critical_count += 1
                recent_alerts.append(alert)
        
        dashboard_data["critical_alerts"] = critical_count
        dashboard_data["recent_alerts"] = sorted(
            recent_alerts,
            key=lambda x: x["timestamp"],
            reverse=True
        )[:10]
        
        return dashboard_data
```

### 安全配置总结

```yaml
# k8s/security/security-summary.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: security-summary
  namespace: knowledge-rag
data:
  security-checklist.md: |
    # Knowledge_RAG 安全配置检查清单
    
    ## 认证和授权 ✅
    - [x] JWT认证实现
    - [x] RBAC权限控制
    - [x] 密码安全策略
    - [x] 会话管理
    
    ## 数据保护 ✅
    - [x] 数据加密（静态和传输）
    - [x] 密钥管理（Vault）
    - [x] 数据分类和标记
    - [x] 备份加密
    
    ## 网络安全 ✅
    - [x] 网络策略配置
    - [x] SSL/TLS配置
    - [x] 防火墙规则
    - [x] DDoS防护
    
    ## 容器安全 ✅
    - [x] Pod安全策略
    - [x] 镜像安全扫描
    - [x] 运行时安全
    - [x] 资源限制
    
    ## 监控和审计 ✅
    - [x] 安全事件监控
    - [x] 审计日志
    - [x] 告警机制
    - [x] 合规性检查
    
    ## 事件响应 ✅
    - [x] 事件分类和处理
    - [x] 自动化响应
    - [x] 通知机制
    - [x] 恢复程序
```

✅ **安全标准和规范设计已完成**

本安全架构实现了多层防护体系，包括：

1. **身份认证和授权**：JWT + RBAC权限控制
2. **数据加密**：静态和传输加密，密钥管理
3. **网络安全**：网络策略、SSL/TLS、防火墙
4. **容器安全**：Pod安全策略、镜像扫描
5. **合规性**：GDPR/CCPA数据保护合规
6. **监控告警**：实时安全事件监控和响应

安全架构遵循零信任原则，确保系统在各个层面都有适当的安全控制措施。