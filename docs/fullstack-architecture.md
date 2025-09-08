# Knowledge RAG 全栈架构文档

## 文档信息

| 属性 | 值 |
|------|----|
| 文档ID | knowledge-rag-fullstack-arch |
| 版本 | 1.0.0 |
| 创建日期 | 2025-01-06 |
| 最后更新 | 2025-01-06 |
| 作者 | AI架构师 |
| 状态 | 草案 |

## 变更日志

| 日期 | 版本 | 描述 | 作者 |
|------|------|------|------|
| 2025-01-06 | 1.0.0 | 初始版本创建 | AI架构师 |

## 1. 引言

### 项目背景

Knowledge RAG是一个基于GraphRAG技术的智能知识管理系统，旨在通过先进的检索增强生成技术，为用户提供高效、准确的知识检索和问答服务。该系统专注于处理大规模文档集合，构建知识图谱，并提供智能化的信息检索能力。

### 架构方法

本文档采用API-First的后端架构设计方法，专注于构建高性能、可扩展的后端服务体系。我们的架构设计遵循以下核心原则：

- **微服务架构**：将系统拆分为独立的、可扩展的服务单元
- **异步处理**：采用事件驱动和消息队列机制处理复杂的文档处理流程
- **多数据库策略**：针对不同数据类型选择最适合的存储方案
- **容器化部署**：确保环境一致性和部署灵活性

### 项目类型

本项目为**纯后端API服务**，基于FastAPI微服务模板构建全新的知识管理平台。系统包含以下6个核心后端服务：

1. **API网关服务** - 统一入口和路由管理
2. **文档处理服务** - 多格式文档解析和预处理
3. **向量检索服务** - 基于Weaviate的语义检索
4. **知识图谱服务** - 基于Neo4j的图数据管理
5. **查询引擎服务** - GraphRAG混合检索和LLM集成
6. **用户管理服务** - 认证授权和用户数据管理

### 技术选型优势

选择FastAPI微服务架构的核心原因：

- **高性能异步处理**：原生支持async/await，适合I/O密集型的文档处理任务
- **自动API文档生成**：内置OpenAPI支持，便于API管理和测试
- **类型安全**：基于Python类型提示，提高代码质量和维护性
- **AI/ML生态兼容**：与Python机器学习库无缝集成
- **容器化友好**：轻量级部署，适合Kubernetes环境

### 关键约束条件

- **性能要求**：查询响应时间 < 2秒，支持并发用户数 > 1000
- **可扩展性**：支持10万+文档存储，水平扩展能力
- **可用性**：系统可用性 > 99.5%，故障恢复时间 < 5分钟
- **安全合规**：GDPR合规，数据加密存储和传输

### 核心决策权衡

1. **微服务 vs 单体架构**：选择微服务以支持独立扩展和技术栈多样性
2. **同步 vs 异步处理**：采用异步处理提高系统吞吐量
3. **SQL vs NoSQL**：多数据库策略，根据数据特性选择最优存储
4. **自建 vs 托管服务**：平衡成本和控制力，关键服务自建，辅助服务托管

### 核心假设

- 用户主要通过API接口访问系统功能
- 文档处理为批量异步操作，实时性要求不高
- 知识图谱构建为离线计算密集型任务
- 系统部署在云环境，支持弹性扩缩容

### 待验证决策

- LLM服务提供商选择（OpenAI vs 自部署模型）
- 向量数据库性能优化策略
- 知识图谱更新频率和一致性保证
- 多租户数据隔离方案

---

## 2. 高层架构设计

### 技术摘要

Knowledge RAG采用基于FastAPI的微服务架构，通过API网关统一管理6个核心后端服务。系统采用异步事件驱动模式处理文档上传、向量化、知识图谱构建等复杂流程。数据存储采用多数据库策略：PostgreSQL存储结构化数据，Weaviate管理向量数据，Neo4j构建知识图谱，Redis提供缓存和会话管理。整体架构通过Docker容器化部署在Kubernetes集群上，实现高可用和弹性扩缩容。该架构设计充分满足PRD中提出的高性能检索（<2秒响应）、大规模存储（10万+文档）和高可用性（99.5%）要求。

### 平台和基础设施选择

基于PRD要求和技术假设，我们评估了以下平台选项：

#### 选项对比

**1. AWS全栈方案**
- **优势**：成熟的微服务生态（EKS、API Gateway、Lambda）、丰富的AI/ML服务（SageMaker、Bedrock）、全球CDN和高可用性
- **劣势**：成本较高、厂商锁定风险、学习曲线陡峭
- **适用场景**：企业级部署，需要全球化服务

**2. Google Cloud方案**
- **优势**：AI/ML服务领先（Vertex AI、BigQuery ML）、Kubernetes原生支持（GKE）、成本效益好
- **劣势**：生态相对较小、部分地区服务有限
- **适用场景**：AI/ML重度应用，成本敏感项目

**3. 混合云方案（推荐）**
- **优势**：避免厂商锁定、成本可控、技术栈灵活、支持多云部署
- **劣势**：运维复杂度较高、需要更多DevOps投入
- **适用场景**：中长期项目，需要技术自主可控

#### 推荐方案

**平台：** 混合云架构（主要基于Kubernetes）  
**核心服务：** 
- **容器编排**：Kubernetes (EKS/GKE/AKS)
- **API网关**：Kong + Nginx Ingress
- **消息队列**：Redis + Celery
- **监控体系**：Prometheus + Grafana + Jaeger
- **CI/CD**：GitLab CI/CD + ArgoCD
- **存储**：云对象存储（S3/GCS/Azure Blob）

**部署主机和区域：** 多区域部署（主区域 + 灾备区域），支持就近访问

### 仓库结构

**结构：** Monorepo（单一仓库）  
**Monorepo工具：** Python Poetry + Docker Compose（开发环境）  
**包组织策略：** 按服务边界组织，共享组件独立管理

```
knowledge-rag/
├── services/                 # 微服务目录
│   ├── api-gateway/         # API网关服务
│   ├── document-processor/  # 文档处理服务
│   ├── vector-search/       # 向量检索服务
│   ├── knowledge-graph/     # 知识图谱服务
│   ├── query-engine/        # 查询引擎服务
│   └── user-management/     # 用户管理服务
├── shared/                  # 共享组件
│   ├── common/             # 通用工具和配置
│   ├── models/             # 数据模型定义
│   └── clients/            # 服务间通信客户端
├── infrastructure/          # 基础设施代码
│   ├── k8s/               # Kubernetes配置
│   ├── docker/            # Docker配置
│   └── terraform/         # 基础设施即代码
├── docs/                   # 文档目录
├── tests/                  # 集成测试
└── tools/                  # 开发工具
```

### 高层架构图

```mermaid
graph TB
    %% 客户端层
    Client["🖥️ 客户端应用<br/>(Web/Mobile/API)"] 
    
    %% API网关层
    subgraph "API网关层"
        Kong["🚪 Kong API Gateway<br/>路由/认证/限流"]
        Nginx["⚡ Nginx Ingress<br/>负载均衡/SSL"]
    end
    
    %% 核心服务层
    subgraph "核心服务层"
        UserMgmt["👤 用户管理服务<br/>认证/授权/用户数据"]
        DocProcessor["📄 文档处理服务<br/>解析/预处理/OCR"]
        VectorSearch["🔍 向量检索服务<br/>语义搜索/相似度"]
        KnowledgeGraph["🕸️ 知识图谱服务<br/>实体关系/图查询"]
        QueryEngine["🧠 查询引擎服务<br/>GraphRAG/LLM集成"]
        Notification["📢 通知服务<br/>消息推送/邮件"]
    end
    
    %% 数据存储层
    subgraph "数据存储层"
        PostgreSQL[("🗄️ PostgreSQL<br/>结构化数据")]
        MinIO[("📦 MinIO/S3<br/>文件存储")]
        Weaviate[("🔢 Weaviate<br/>向量数据库")]
        Neo4j[("🕸️ Neo4j<br/>图数据库")]
        Redis[("⚡ Redis<br/>缓存/会话")]
    end
    
    %% 外部服务
    subgraph "外部服务"
        LLM["🤖 大语言模型<br/>(OpenAI/Claude)"] 
        OCR["👁️ OCR服务<br/>(Tesseract/云OCR)"]
    end
    
    %% 消息队列
    subgraph "消息队列"
        Celery["📨 Celery + Redis<br/>异步任务处理"]
    end
    
    %% 连接关系
    Client --> Nginx
    Nginx --> Kong
    Kong --> UserMgmt
    Kong --> DocProcessor
    Kong --> VectorSearch
    Kong --> KnowledgeGraph
    Kong --> QueryEngine
    Kong --> Notification
    
    %% 服务间通信
    DocProcessor --> Celery
    VectorSearch --> Celery
    KnowledgeGraph --> Celery
    QueryEngine --> VectorSearch
    QueryEngine --> KnowledgeGraph
    QueryEngine --> LLM
    DocProcessor --> OCR
    
    %% 数据连接
    UserMgmt --> PostgreSQL
    DocProcessor --> MinIO
    DocProcessor --> PostgreSQL
    VectorSearch --> Weaviate
    KnowledgeGraph --> Neo4j
    QueryEngine --> Redis
    Notification --> Redis
    
    %% 样式定义
    classDef serviceBox fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef dataBox fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef externalBox fill:#fff3e0,stroke:#e65100,stroke-width:2px
    
    class UserMgmt,DocProcessor,VectorSearch,KnowledgeGraph,QueryEngine,Notification serviceBox
    class PostgreSQL,MinIO,Weaviate,Neo4j,Redis dataBox
    class LLM,OCR externalBox
```

### 架构模式

以下是指导整个系统开发的核心架构模式：

- **微服务架构**：按业务领域拆分服务，实现独立部署和扩展 - _理由：_ 支持团队独立开发，技术栈灵活选择，故障隔离

- **API网关模式**：统一API入口，集中处理认证、限流、监控 - _理由：_ 简化客户端集成，统一安全策略，便于API管理

- **事件驱动架构**：通过消息队列实现服务间异步通信 - _理由：_ 提高系统吞吐量，降低服务耦合度，支持复杂业务流程

- **CQRS模式**：读写分离，优化查询性能 - _理由：_ GraphRAG查询复杂度高，需要专门的读取优化

- **仓储模式**：抽象数据访问层，支持多数据库策略 - _理由：_ 便于单元测试，支持数据库迁移，代码可维护性

- **断路器模式**：防止级联故障，提高系统稳定性 - _理由：_ 外部LLM服务可能不稳定，需要故障隔离机制

- **缓存模式**：多层缓存策略，提升响应性能 - _理由：_ 向量检索和图查询计算密集，缓存可显著提升性能

---

## 3. 技术栈

本节定义Knowledge RAG项目的完整技术栈选型，这是整个项目开发的技术基准，所有开发工作必须严格遵循这些技术选择和版本要求。

### 技术栈选型表

| 类别 | 技术 | 版本 | 用途 | 选择理由 |
|------|------|------|------|----------|
| **开发语言** | Python | 3.11+ | 核心开发语言 | AI/ML生态丰富，异步支持优秀，开发效率高 |
| **Web框架** | FastAPI | 0.104+ | Web框架和API服务 | 高性能异步框架，自动API文档，类型安全 |
| **API风格** | REST API | OpenAPI 3.0 | HTTP API接口 | 标准化接口，易于集成和测试，工具链成熟 |
| **主数据库** | PostgreSQL | 15+ | 结构化数据存储 | ACID事务支持，JSON支持，成熟稳定 |
| **向量数据库** | Weaviate | 1.22+ | 向量存储和检索 | GraphQL查询，多模态支持，云原生架构 |
| **图数据库** | Neo4j | 5.0+ | 知识图谱存储 | Cypher查询语言，图算法丰富，可视化工具 |
| **缓存** | Redis | 7.0+ | 缓存和会话存储 | 高性能内存存储，数据结构丰富，集群支持 |
| **文件存储** | MinIO/S3 | Latest | 对象存储服务 | S3兼容API，可扩展，支持多云部署 |
| **消息队列** | Celery + Redis | 5.3+ | 异步任务处理 | Python原生支持，任务调度灵活，监控完善 |
| **认证授权** | JWT + OAuth2 | - | 身份认证和授权 | 无状态认证，标准协议，易于扩展 |
| **API网关** | Kong | 3.4+ | API管理和路由 | 插件生态丰富，性能优秀，企业级特性 |
| **负载均衡** | Nginx | 1.24+ | 反向代理和负载均衡 | 高性能，配置灵活，SSL终端 |
| **容器化** | Docker | 24.0+ | 应用容器化 | 环境一致性，部署简化，资源隔离 |
| **容器编排** | Kubernetes | 1.28+ | 容器集群管理 | 自动扩缩容，服务发现，滚动更新 |
| **单元测试** | pytest + httpx | 7.4+ | 单元和集成测试 | 异步测试支持，fixture机制，插件丰富 |
| **API测试** | pytest-asyncio | 0.21+ | 异步API测试 | FastAPI原生支持，测试覆盖完整 |
| **E2E测试** | Postman/Newman | Latest | 端到端API测试 | 自动化测试，CI/CD集成，团队协作 |
| **代码质量** | Black + isort + flake8 | Latest | 代码格式化和检查 | 代码风格统一，质量保证，CI集成 |
| **依赖管理** | Poetry | 1.6+ | Python包管理 | 依赖解析，虚拟环境，构建发布 |
| **构建工具** | Docker Compose | 2.21+ | 本地开发环境 | 多服务编排，环境隔离，快速启动 |
| **CI/CD** | GitLab CI/CD | - | 持续集成和部署 | 代码质量检查，自动化测试，部署流水线 |
| **基础设施即代码** | Terraform | 1.6+ | 云资源管理 | 多云支持，状态管理，版本控制 |
| **配置管理** | Helm | 3.13+ | Kubernetes应用管理 | 模板化部署，版本管理，回滚支持 |
| **监控** | Prometheus + Grafana | 2.47+ / 10.2+ | 系统监控和可视化 | 指标收集，告警规则，仪表板丰富 |
| **链路追踪** | Jaeger | 1.50+ | 分布式追踪 | 微服务调用链，性能分析，故障定位 |
| **日志管理** | ELK Stack | 8.10+ | 日志收集和分析 | 集中化日志，全文搜索，可视化分析 |
| **文档生成** | Swagger UI | 5.9+ | API文档展示 | 交互式文档，在线测试，自动生成 |
| **开发工具** | VS Code + Python扩展 | Latest | 集成开发环境 | 智能提示，调试支持，插件丰富 |

### 核心技术选型说明

#### 核心技术栈

**FastAPI + Python 3.11**
- **异步性能**：原生async/await支持，处理高并发请求
- **类型安全**：基于Pydantic的数据验证和序列化
- **自动文档**：OpenAPI/Swagger自动生成，减少文档维护成本
- **生态兼容**：与AI/ML库（transformers、langchain等）无缝集成

#### 数据存储策略

**多数据库架构设计**
- **PostgreSQL**：用户数据、文档元数据、系统配置等结构化数据
- **Weaviate**：文档向量、语义检索、相似度计算
- **Neo4j**：实体关系、知识图谱、图算法计算
- **Redis**：会话缓存、查询结果缓存、分布式锁

#### 微服务通信

**同步 + 异步混合模式**
- **同步通信**：REST API用于实时查询和用户交互
- **异步通信**：Celery任务队列处理文档解析、向量化、图构建
- **事件驱动**：Redis Pub/Sub实现服务间事件通知

#### 部署和运维

**云原生架构**
- **容器化**：Docker确保环境一致性
- **编排管理**：Kubernetes提供自动扩缩容和故障恢复
- **服务网格**：Kong API网关统一管理API路由和安全
- **可观测性**：Prometheus + Grafana + Jaeger全方位监控

### 版本兼容性矩阵

| 组件 | 最低版本 | 推荐版本 | 兼容性说明 |
|------|----------|----------|------------|
| Python | 3.11.0 | 3.11.6 | 必须支持async/await和类型提示 |
| FastAPI | 0.104.0 | 0.104.1 | 需要OpenAPI 3.0支持 |
| PostgreSQL | 15.0 | 15.4 | 需要JSON和全文搜索支持 |
| Weaviate | 1.22.0 | 1.22.4 | 需要GraphQL和多模态支持 |
| Neo4j | 5.0.0 | 5.13.0 | 需要APOC插件和图算法库 |
| Redis | 7.0.0 | 7.2.3 | 需要Stream和模块支持 |
| Kubernetes | 1.28.0 | 1.28.4 | 需要CRD和Operator支持 |

### 开发环境配置

**本地开发栈**
```yaml
# docker-compose.dev.yml
version: '3.8'
services:
  postgres:
    image: postgres:15.4
    environment:
      POSTGRES_DB: knowledge_rag
      POSTGRES_USER: dev
      POSTGRES_PASSWORD: dev123
    ports:
      - "5432:5432"
  
  redis:
    image: redis:7.2.3
    ports:
      - "6379:6379"
  
  weaviate:
    image: semitechnologies/weaviate:1.22.4
    ports:
      - "8080:8080"
    environment:
      QUERY_DEFAULTS_LIMIT: 25
      AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED: 'true'
  
  neo4j:
    image: neo4j:5.13.0
    ports:
      - "7474:7474"
      - "7687:7687"
    environment:
      NEO4J_AUTH: neo4j/dev123
      NEO4J_PLUGINS: '["apoc", "graph-data-science"]'
```

**Python依赖管理**
```toml
# pyproject.toml
[tool.poetry]
name = "knowledge-rag"
version = "0.1.0"
description = "GraphRAG-based Knowledge Management System"

[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.104.1"
uvicorn = {extras = ["standard"], version = "^0.24.0"}
sqlalchemy = "^2.0.23"
alembic = "^1.12.1"
psycopg2-binary = "^2.9.9"
redis = "^5.0.1"
celery = "^5.3.4"
weaviate-client = "^3.25.3"
neo4j = "^5.14.1"
pydantic = "^2.5.0"
python-jose = {extras = ["cryptography"], version = "^3.3.0"}
passlib = {extras = ["bcrypt"], version = "^1.7.4"}
langchain = "^0.0.350"
openai = "^1.3.7"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.3"
pytest-asyncio = "^0.21.1"
httpx = "^0.25.2"
black = "^23.11.0"
isort = "^5.12.0"
flake8 = "^6.1.0"
mypy = "^1.7.1"
```

## 4. 数据模型

### 4.1 核心业务实体概述

Knowledge RAG系统的数据模型围绕知识管理和智能检索的核心业务流程设计，主要包含以下核心实体：

- **文档实体**：系统中的核心知识载体，支持多模态内容
- **用户实体**：系统用户和权限管理的基础
- **知识图谱实体**：语义关系和概念的结构化表示
- **查询会话**：用户交互和上下文管理
- **向量索引**：语义检索的技术基础
- **工作空间**：团队协作和权限隔离的组织单位

### 4.2 文档管理模型

#### Document（文档）

**Purpose:** 系统中的核心知识载体，存储和管理用户上传的各类学术文档和多媒体内容。

**Key Attributes:**
- id: string - 文档唯一标识符（UUID格式）
- title: string - 文档标题
- originalFilename: string - 原始文件名
- fileType: DocumentType - 文档类型枚举
- fileSize: number - 文件大小（字节）
- uploadedAt: Date - 上传时间
- processedAt: Date | null - 处理完成时间
- status: ProcessingStatus - 处理状态
- metadata: DocumentMetadata - 文档元数据
- content: DocumentContent - 解析后的内容结构
- workspaceId: string - 所属工作空间ID
- uploadedBy: string - 上传用户ID
- tags: string[] - 文档标签
- version: number - 文档版本号

```typescript
interface Document {
  id: string;
  title: string;
  originalFilename: string;
  fileType: DocumentType;
  fileSize: number;
  uploadedAt: Date;
  processedAt: Date | null;
  status: ProcessingStatus;
  metadata: DocumentMetadata;
  content: DocumentContent;
  workspaceId: string;
  uploadedBy: string;
  tags: string[];
  version: number;
  createdAt: Date;
  updatedAt: Date;
}

enum DocumentType {
  PDF = 'pdf',
  DOCX = 'docx',
  PPTX = 'pptx',
  IMAGE = 'image',
  TEXT = 'text',
  MARKDOWN = 'markdown'
}

enum ProcessingStatus {
  PENDING = 'pending',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  FAILED = 'failed',
  ARCHIVED = 'archived'
}

interface DocumentMetadata {
  author?: string;
  subject?: string;
  keywords?: string[];
  creationDate?: Date;
  language?: string;
  pageCount?: number;
  wordCount?: number;
  extractedEntities?: string[];
}

interface DocumentContent {
  rawText: string;
  structuredContent: ContentBlock[];
  extractedImages?: ImageContent[];
  extractedTables?: TableContent[];
  extractedFormulas?: FormulaContent[];
}
```

**Relationships:**
- 属于一个工作空间（Workspace）
- 由一个用户上传（User）
- 包含多个内容块（ContentBlock）
- 关联多个向量嵌入（VectorEmbedding）
- 参与多个知识图谱关系（KnowledgeGraphRelation）

#### ContentBlock（内容块）

**Purpose:** 文档内容的结构化表示单元，支持不同类型的多模态内容块。

**Key Attributes:**
- id: string - 内容块唯一标识符
- documentId: string - 所属文档ID
- type: ContentBlockType - 内容块类型
- content: string - 文本内容
- position: BlockPosition - 在文档中的位置信息
- metadata: BlockMetadata - 内容块元数据
- vectorId: string | null - 关联的向量嵌入ID

```typescript
interface ContentBlock {
  id: string;
  documentId: string;
  type: ContentBlockType;
  content: string;
  position: BlockPosition;
  metadata: BlockMetadata;
  vectorId: string | null;
  createdAt: Date;
}

enum ContentBlockType {
  PARAGRAPH = 'paragraph',
  HEADING = 'heading',
  TABLE = 'table',
  IMAGE = 'image',
  FORMULA = 'formula',
  CODE = 'code',
  LIST = 'list'
}

interface BlockPosition {
  pageNumber?: number;
  startOffset: number;
  endOffset: number;
  boundingBox?: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
}

interface BlockMetadata {
  confidence?: number;
  language?: string;
  fontSize?: number;
  fontFamily?: string;
  extractionMethod?: string;
}
```

### 4.3 用户管理模型

#### User（用户）

**Purpose:** 系统用户的基础信息和身份认证管理。

**Key Attributes:**
- id: string - 用户唯一标识符
- email: string - 用户邮箱（登录凭证）
- username: string - 用户名
- displayName: string - 显示名称
- avatar: string | null - 头像URL
- role: UserRole - 用户角色
- preferences: UserPreferences - 用户偏好设置
- researchFields: string[] - 研究领域标签
- isActive: boolean - 账户状态
- lastLoginAt: Date | null - 最后登录时间

```typescript
interface User {
  id: string;
  email: string;
  username: string;
  displayName: string;
  avatar: string | null;
  role: UserRole;
  preferences: UserPreferences;
  researchFields: string[];
  isActive: boolean;
  lastLoginAt: Date | null;
  createdAt: Date;
  updatedAt: Date;
}

enum UserRole {
  ADMIN = 'admin',
  RESEARCHER = 'researcher',
  STUDENT = 'student',
  GUEST = 'guest'
}

interface UserPreferences {
  language: string;
  timezone: string;
  theme: 'light' | 'dark' | 'auto';
  notificationSettings: {
    email: boolean;
    inApp: boolean;
    documentProcessing: boolean;
    weeklyDigest: boolean;
  };
  searchSettings: {
    defaultSearchMode: 'vector' | 'graph' | 'hybrid';
    resultsPerPage: number;
    includeImages: boolean;
  };
}
```

**Relationships:**
- 拥有多个工作空间（Workspace）
- 上传多个文档（Document）
- 创建多个查询会话（QuerySession）
- 参与多个工作空间协作（WorkspaceMember）

#### Workspace（工作空间）

**Purpose:** 团队协作和权限隔离的组织单位，支持个人和团队知识库管理。

**Key Attributes:**
- id: string - 工作空间唯一标识符
- name: string - 工作空间名称
- description: string - 工作空间描述
- type: WorkspaceType - 工作空间类型
- ownerId: string - 所有者用户ID
- settings: WorkspaceSettings - 工作空间设置
- isPublic: boolean - 是否公开可见
- documentCount: number - 文档数量统计
- memberCount: number - 成员数量统计

```typescript
interface Workspace {
  id: string;
  name: string;
  description: string;
  type: WorkspaceType;
  ownerId: string;
  settings: WorkspaceSettings;
  isPublic: boolean;
  documentCount: number;
  memberCount: number;
  createdAt: Date;
  updatedAt: Date;
}

enum WorkspaceType {
  PERSONAL = 'personal',
  TEAM = 'team',
  ORGANIZATION = 'organization',
  PUBLIC = 'public'
}

interface WorkspaceSettings {
  allowGuestAccess: boolean;
  requireApprovalForJoin: boolean;
  maxDocuments: number;
  maxStorageSize: number;
  enableVersionControl: boolean;
  defaultPermissions: {
    read: boolean;
    write: boolean;
    delete: boolean;
    share: boolean;
  };
}
```

### 4.4 知识图谱模型

#### KnowledgeEntity（知识实体）

**Purpose:** 知识图谱中的实体节点，表示从文档中提取的概念、人物、机构等语义实体。

**Key Attributes:**
- id: string - 实体唯一标识符
- name: string - 实体名称
- type: EntityType - 实体类型
- description: string - 实体描述
- aliases: string[] - 实体别名
- properties: Record<string, any> - 实体属性
- confidence: number - 提取置信度
- sourceDocuments: string[] - 来源文档ID列表
- workspaceId: string - 所属工作空间

```typescript
interface KnowledgeEntity {
  id: string;
  name: string;
  type: EntityType;
  description: string;
  aliases: string[];
  properties: Record<string, any>;
  confidence: number;
  sourceDocuments: string[];
  workspaceId: string;
  createdAt: Date;
  updatedAt: Date;
}

enum EntityType {
  PERSON = 'person',
  ORGANIZATION = 'organization',
  CONCEPT = 'concept',
  TECHNOLOGY = 'technology',
  METHOD = 'method',
  DATASET = 'dataset',
  PUBLICATION = 'publication',
  LOCATION = 'location'
}
```

#### KnowledgeRelation（知识关系）

**Purpose:** 知识图谱中的关系边，表示实体之间的语义关联。

**Key Attributes:**
- id: string - 关系唯一标识符
- sourceEntityId: string - 源实体ID
- targetEntityId: string - 目标实体ID
- relationType: RelationType - 关系类型
- properties: Record<string, any> - 关系属性
- confidence: number - 关系置信度
- evidence: RelationEvidence[] - 关系证据
- workspaceId: string - 所属工作空间

```typescript
interface KnowledgeRelation {
  id: string;
  sourceEntityId: string;
  targetEntityId: string;
  relationType: RelationType;
  properties: Record<string, any>;
  confidence: number;
  evidence: RelationEvidence[];
  workspaceId: string;
  createdAt: Date;
  updatedAt: Date;
}

enum RelationType {
  AUTHORED_BY = 'authored_by',
  BELONGS_TO = 'belongs_to',
  USES = 'uses',
  IMPLEMENTS = 'implements',
  EXTENDS = 'extends',
  RELATED_TO = 'related_to',
  PART_OF = 'part_of',
  INFLUENCES = 'influences'
}

interface RelationEvidence {
  documentId: string;
  contentBlockId: string;
  extractedText: string;
  confidence: number;
}
```

### 4.5 查询和检索模型

#### QuerySession（查询会话）

**Purpose:** 用户查询会话的管理，支持多轮对话和上下文保持。

**Key Attributes:**
- id: string - 会话唯一标识符
- userId: string - 用户ID
- workspaceId: string - 工作空间ID
- title: string - 会话标题
- context: SessionContext - 会话上下文
- queries: Query[] - 查询历史
- isActive: boolean - 会话状态
- lastActivityAt: Date - 最后活动时间

```typescript
interface QuerySession {
  id: string;
  userId: string;
  workspaceId: string;
  title: string;
  context: SessionContext;
  queries: Query[];
  isActive: boolean;
  lastActivityAt: Date;
  createdAt: Date;
  updatedAt: Date;
}

interface SessionContext {
  researchTopic?: string;
  focusDocuments?: string[];
  preferredLanguage: string;
  searchMode: 'vector' | 'graph' | 'hybrid';
  conversationHistory: ConversationTurn[];
}

interface ConversationTurn {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  metadata?: Record<string, any>;
}
```

#### Query（查询）

**Purpose:** 单次查询请求的详细记录，包含查询参数、结果和性能指标。

**Key Attributes:**
- id: string - 查询唯一标识符
- sessionId: string - 所属会话ID
- queryText: string - 查询文本
- queryType: QueryType - 查询类型
- parameters: QueryParameters - 查询参数
- results: QueryResult[] - 查询结果
- performance: QueryPerformance - 性能指标
- feedback: QueryFeedback | null - 用户反馈

```typescript
interface Query {
  id: string;
  sessionId: string;
  queryText: string;
  queryType: QueryType;
  parameters: QueryParameters;
  results: QueryResult[];
  performance: QueryPerformance;
  feedback: QueryFeedback | null;
  createdAt: Date;
}

enum QueryType {
  SEMANTIC_SEARCH = 'semantic_search',
  GRAPH_TRAVERSAL = 'graph_traversal',
  HYBRID_RAG = 'hybrid_rag',
  ENTITY_LOOKUP = 'entity_lookup',
  DOCUMENT_QA = 'document_qa'
}

interface QueryParameters {
  maxResults: number;
  similarityThreshold: number;
  includeMetadata: boolean;
  filterCriteria?: {
    documentTypes?: DocumentType[];
    dateRange?: {
      start: Date;
      end: Date;
    };
    tags?: string[];
    authors?: string[];
  };
  graphTraversalDepth?: number;
  rerankingEnabled: boolean;
}

interface QueryResult {
  id: string;
  type: 'document' | 'content_block' | 'entity' | 'relation';
  sourceId: string;
  title: string;
  content: string;
  score: number;
  metadata: Record<string, any>;
  highlights?: TextHighlight[];
  citations?: Citation[];
}

interface QueryPerformance {
  totalDuration: number;
  vectorSearchDuration: number;
  graphTraversalDuration: number;
  rerankingDuration: number;
  resultsCount: number;
  cacheHit: boolean;
}
```

### 4.6 向量检索模型

#### VectorEmbedding（向量嵌入）

**Purpose:** 文档内容的向量化表示，支持语义相似性检索。

**Key Attributes:**
- id: string - 向量嵌入唯一标识符
- contentId: string - 关联内容ID（文档或内容块）
- contentType: 'document' | 'content_block' - 内容类型
- vector: number[] - 向量数据
- model: string - 嵌入模型名称
- dimensions: number - 向量维度
- metadata: EmbeddingMetadata - 嵌入元数据
- workspaceId: string - 所属工作空间

```typescript
interface VectorEmbedding {
  id: string;
  contentId: string;
  contentType: 'document' | 'content_block';
  vector: number[];
  model: string;
  dimensions: number;
  metadata: EmbeddingMetadata;
  workspaceId: string;
  createdAt: Date;
  updatedAt: Date;
}

interface EmbeddingMetadata {
  textLength: number;
  language: string;
  processingTime: number;
  chunkIndex?: number;
  chunkOverlap?: number;
}
```

### 4.7 数据模型关系图

```mermaid
erDiagram
    User ||--o{ Workspace : owns
    User ||--o{ Document : uploads
    User ||--o{ QuerySession : creates
    
    Workspace ||--o{ Document : contains
    Workspace ||--o{ KnowledgeEntity : contains
    Workspace ||--o{ KnowledgeRelation : contains
    Workspace ||--o{ WorkspaceMember : has
    
    Document ||--o{ ContentBlock : contains
    Document ||--o{ VectorEmbedding : generates
    
    ContentBlock ||--o| VectorEmbedding : has
    
    KnowledgeEntity ||--o{ KnowledgeRelation : participates
    KnowledgeEntity }o--o{ Document : extracted_from
    
    QuerySession ||--o{ Query : contains
    Query ||--o{ QueryResult : produces
    
    WorkspaceMember {
        string userId
        string workspaceId
        string role
        Date joinedAt
        boolean isActive
    }
```

### 4.8 数据模型设计原则

#### 4.8.1 可扩展性设计
- **模块化结构**：每个业务域独立建模，支持独立演进
- **元数据扩展**：使用灵活的metadata字段支持未来功能扩展
- **版本控制**：关键实体支持版本管理，确保数据一致性

#### 4.8.2 性能优化
- **索引策略**：基于查询模式设计复合索引
- **分区设计**：大表按工作空间或时间分区
- **缓存友好**：设计支持Redis缓存的数据结构

#### 4.8.3 数据一致性
- **外键约束**：确保引用完整性
- **事务边界**：明确定义业务事务范围
- **最终一致性**：异步处理场景采用事件驱动模式

#### 4.8.4 安全和隐私
- **数据隔离**：工作空间级别的数据隔离
- **敏感信息**：PII数据加密存储
- **审计追踪**：关键操作记录审计日志

## 5. API规范

基于Knowledge RAG项目的功能需求和REST API技术选型，我设计了完整的OpenAPI 3.0规范。API设计遵循RESTful原则，采用资源导向的URL设计，支持标准HTTP方法，并提供统一的错误处理和认证机制。

### 5.1 API设计原则

**资源导向设计**
- 使用名词表示资源，动词通过HTTP方法表达
- 采用层次化URL结构，体现资源间的关系
- 支持资源的CRUD操作和复杂查询

**版本控制策略**
- 采用URL路径版本控制（/api/v1/）
- 向后兼容性保证，渐进式API演进
- 明确的废弃策略和迁移指南

**统一响应格式**
- 标准化的成功和错误响应结构
- 丰富的HTTP状态码使用
- 详细的错误信息和调试支持

### 5.2 核心API端点设计

#### 5.2.1 文档管理API

```yaml
# 文档上传和管理
POST /api/v1/workspaces/{workspaceId}/documents
GET /api/v1/workspaces/{workspaceId}/documents
GET /api/v1/workspaces/{workspaceId}/documents/{documentId}
PUT /api/v1/workspaces/{workspaceId}/documents/{documentId}
DELETE /api/v1/workspaces/{workspaceId}/documents/{documentId}

# 文档处理状态
GET /api/v1/workspaces/{workspaceId}/documents/{documentId}/processing-status
POST /api/v1/workspaces/{workspaceId}/documents/{documentId}/reprocess
```

#### 5.2.2 智能检索API

```yaml
# 向量语义检索
POST /api/v1/workspaces/{workspaceId}/search/semantic
POST /api/v1/workspaces/{workspaceId}/search/hybrid

# 知识图谱查询
POST /api/v1/workspaces/{workspaceId}/knowledge-graph/query
GET /api/v1/workspaces/{workspaceId}/knowledge-graph/entities
GET /api/v1/workspaces/{workspaceId}/knowledge-graph/relations
```

#### 5.2.3 问答系统API

```yaml
# 会话管理
POST /api/v1/workspaces/{workspaceId}/sessions
GET /api/v1/workspaces/{workspaceId}/sessions
GET /api/v1/workspaces/{workspaceId}/sessions/{sessionId}

# 问答交互
POST /api/v1/workspaces/{workspaceId}/sessions/{sessionId}/queries
GET /api/v1/workspaces/{workspaceId}/sessions/{sessionId}/queries
```

### 5.3 认证和授权

**JWT Token认证**
- Bearer Token方式传递认证信息
- Token包含用户身份和权限信息
- 支持Token刷新和撤销机制

**基于角色的访问控制（RBAC）**
- 工作空间级别的权限管理
- 细粒度的资源访问控制
- 支持自定义角色和权限组合

### 5.4 请求/响应示例

#### 文档上传请求
```json
POST /api/v1/workspaces/ws-123/documents
Content-Type: multipart/form-data
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...

{
  "file": "<binary_data>",
  "metadata": {
    "title": "机器学习基础理论",
    "description": "深度学习算法研究论文",
    "tags": ["机器学习", "深度学习", "算法"]
  }
}
```

#### 语义检索请求
```json
POST /api/v1/workspaces/ws-123/search/semantic
Content-Type: application/json
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...

{
  "query": "什么是卷积神经网络的反向传播算法？",
  "limit": 10,
  "filters": {
    "documentTypes": ["pdf", "docx"],
    "tags": ["机器学习"]
  },
  "includeMetadata": true
}
```

#### 统一响应格式
```json
{
  "success": true,
  "data": {
    "results": [...],
    "pagination": {
      "page": 1,
      "limit": 10,
      "total": 156,
      "hasNext": true
    }
  },
  "metadata": {
    "requestId": "req-abc123",
    "timestamp": "2025-01-06T10:30:00Z",
    "processingTime": 245
  }
}
```

### 5.5 错误处理

**标准错误响应**
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "请求参数验证失败",
    "details": [
      {
        "field": "query",
        "message": "查询内容不能为空"
      }
    ]
  },
  "metadata": {
    "requestId": "req-def456",
    "timestamp": "2025-01-06T10:30:00Z"
  }
}
```

### 5.6 API设计决策说明

**工作空间隔离设计**
选择在URL路径中包含workspaceId的原因：
- 明确的数据隔离边界，避免跨空间数据泄露
- 简化权限验证逻辑，URL级别的访问控制
- 支持多租户架构，便于后续扩展

**异步处理模式**
文档处理采用异步模式的考虑：
- 大文件处理耗时较长，避免HTTP超时
- 支持批量处理和队列管理
- 提供处理状态查询，改善用户体验

**混合检索API设计**
结合向量检索和图谱查询的原因：
- 语义检索提供相关性排序
- 图谱推理增强答案准确性
- 统一接口简化客户端调用

## 6. 组件设计

基于微服务架构原则，Knowledge RAG系统被设计为6个核心服务组件，每个组件负责特定的业务领域，通过明确的接口进行交互。组件设计遵循单一职责原则、高内聚低耦合的设计理念。

### 6.1 组件架构概览

```mermaid
C4Container
    title Knowledge RAG 系统组件架构
    
    Person(user, "用户", "研究人员、学者")
    
    Container_Boundary(api_layer, "API层") {
        Container(gateway, "API网关", "Kong", "统一入口、路由、认证")
    }
    
    Container_Boundary(core_services, "核心服务层") {
        Container(auth_service, "用户管理服务", "FastAPI", "认证授权、用户管理")
        Container(doc_service, "文档处理服务", "FastAPI", "文档解析、预处理")
        Container(vector_service, "向量检索服务", "FastAPI", "语义检索、向量管理")
        Container(graph_service, "知识图谱服务", "FastAPI", "图谱构建、推理查询")
        Container(query_service, "查询引擎服务", "FastAPI", "GraphRAG、问答")
    }
    
    Container_Boundary(data_layer, "数据存储层") {
        ContainerDb(postgres, "PostgreSQL", "关系数据库", "用户、文档元数据")
        ContainerDb(weaviate, "Weaviate", "向量数据库", "文档向量、语义检索")
        ContainerDb(neo4j, "Neo4j", "图数据库", "知识图谱、实体关系")
        ContainerDb(redis, "Redis", "缓存数据库", "会话、缓存")
        ContainerDb(minio, "MinIO", "对象存储", "文档文件存储")
    }
    
    Container_Boundary(message_queue, "消息队列") {
        Container(celery, "Celery", "任务队列", "异步任务处理")
    }
    
    Rel(user, gateway, "HTTPS请求")
    Rel(gateway, auth_service, "认证请求")
    Rel(gateway, doc_service, "文档管理")
    Rel(gateway, vector_service, "语义检索")
    Rel(gateway, graph_service, "图谱查询")
    Rel(gateway, query_service, "问答查询")
    
    Rel(doc_service, celery, "异步处理任务")
    Rel(vector_service, celery, "向量化任务")
    Rel(graph_service, celery, "图谱构建任务")
    
    Rel(auth_service, postgres, "用户数据")
    Rel(doc_service, postgres, "文档元数据")
    Rel(doc_service, minio, "文档文件")
    Rel(vector_service, weaviate, "向量数据")
    Rel(graph_service, neo4j, "图谱数据")
    Rel(query_service, redis, "会话缓存")
```

### 6.2 核心组件详细设计

#### 6.2.1 API网关服务 (Kong)

**职责范围**
- 统一API入口和路由管理
- 请求认证和授权验证
- 流量控制和速率限制
- API监控和日志记录
- 跨域处理和安全防护

**关键接口**
```python
# Kong配置接口
class GatewayConfig:
    def configure_routes(self) -> Dict[str, Any]
    def setup_auth_plugins(self) -> List[Dict]
    def configure_rate_limiting(self) -> Dict[str, int]
    def setup_cors_policy(self) -> Dict[str, Any]
```

**依赖关系**
- **上游依赖**: 无
- **下游依赖**: 所有后端微服务
- **数据存储**: Kong内置数据库（PostgreSQL）

**技术细节**
- **部署方式**: Docker容器，支持水平扩展
- **配置管理**: 声明式配置，支持热更新
- **监控指标**: 请求量、响应时间、错误率

#### 6.2.2 用户管理服务 (User Management Service)

**职责范围**
- 用户注册、登录、注销
- JWT Token生成和验证
- 工作空间管理和权限控制
- 用户配置文件管理

**关键接口**
```python
class UserService:
    async def authenticate_user(self, credentials: UserCredentials) -> AuthResult
    async def create_workspace(self, user_id: str, workspace_data: WorkspaceCreate) -> Workspace
    async def manage_permissions(self, workspace_id: str, permissions: PermissionUpdate) -> bool
    async def get_user_profile(self, user_id: str) -> UserProfile
```

**依赖关系**
- **上游依赖**: API网关
- **下游依赖**: PostgreSQL数据库
- **外部服务**: 邮件服务（用户验证）

**技术细节**
- **认证机制**: JWT + Refresh Token
- **密码安全**: bcrypt哈希加密
- **会话管理**: Redis缓存用户会话

#### 6.2.3 文档处理服务 (Document Processing Service)

**职责范围**
- 多格式文档上传和存储
- 文档内容解析和提取
- 文本预处理和清洗
- 文档版本管理
- 异步处理任务调度

**关键接口**
```python
class DocumentService:
    async def upload_document(self, file: UploadFile, metadata: DocumentMetadata) -> Document
    async def parse_document(self, document_id: str) -> ParseResult
    async def extract_content_blocks(self, document_id: str) -> List[ContentBlock]
    async def get_processing_status(self, document_id: str) -> ProcessingStatus
```

**依赖关系**
- **上游依赖**: API网关
- **下游依赖**: PostgreSQL、MinIO、Celery队列
- **外部服务**: OCR服务、文档转换服务

**技术细节**
- **文件处理**: PyPDF2、python-docx、Pillow
- **异步任务**: Celery + Redis
- **存储策略**: 元数据存PostgreSQL，文件存MinIO

#### 6.2.4 向量检索服务 (Vector Retrieval Service)

**职责范围**
- 文档内容向量化处理
- 语义相似度检索
- 向量索引管理和优化
- 检索结果排序和过滤

**关键接口**
```python
class VectorService:
    async def vectorize_content(self, content: str, model: str) -> VectorEmbedding
    async def semantic_search(self, query: str, filters: SearchFilters) -> List[SearchResult]
    async def batch_vectorize(self, contents: List[str]) -> List[VectorEmbedding]
    async def update_vector_index(self, document_id: str) -> bool
```

**依赖关系**
- **上游依赖**: API网关、文档处理服务
- **下游依赖**: Weaviate向量数据库
- **外部服务**: OpenAI Embedding API、本地嵌入模型

**技术细节**
- **嵌入模型**: text-embedding-ada-002、sentence-transformers
- **向量维度**: 1536维（OpenAI）、768维（BERT）
- **检索算法**: HNSW近似最近邻搜索

#### 6.2.5 知识图谱服务 (Knowledge Graph Service)

**职责范围**
- 实体和关系抽取
- 知识图谱构建和维护
- 图谱推理和路径查询
- 实体链接和消歧

**关键接口**
```python
class GraphService:
    async def extract_entities(self, text: str) -> List[Entity]
    async def build_knowledge_graph(self, document_id: str) -> GraphBuildResult
    async def query_graph(self, cypher_query: str) -> List[Dict]
    async def find_entity_relations(self, entity_id: str, depth: int) -> RelationGraph
```

**依赖关系**
- **上游依赖**: API网关、文档处理服务
- **下游依赖**: Neo4j图数据库
- **外部服务**: NLP实体识别服务、知识库API

**技术细节**
- **NLP模型**: spaCy、BERT-NER、GPT-4实体抽取
- **图算法**: PageRank、社区发现、路径搜索
- **查询语言**: Cypher查询语言

#### 6.2.6 查询引擎服务 (Query Engine Service)

**职责范围**
- GraphRAG混合检索实现
- LLM集成和提示工程
- 多轮对话上下文管理
- 答案质量评估和优化

**关键接口**
```python
class QueryEngine:
    async def graphrag_query(self, query: str, context: QueryContext) -> QueryResult
    async def create_session(self, workspace_id: str) -> QuerySession
    async def multi_turn_chat(self, session_id: str, message: str) -> ChatResponse
    async def evaluate_answer_quality(self, query: str, answer: str) -> QualityScore
```

**依赖关系**
- **上游依赖**: API网关
- **下游依赖**: 向量检索服务、知识图谱服务、Redis缓存
- **外部服务**: OpenAI GPT-4、Claude API

**技术细节**
- **检索策略**: 向量检索 + 图谱推理 + 重排序
- **LLM集成**: OpenAI API、Anthropic Claude
- **上下文管理**: 滑动窗口、重要信息提取

### 6.3 组件间通信模式

#### 6.3.1 同步通信
- **协议**: HTTP/HTTPS REST API
- **格式**: JSON请求/响应
- **超时**: 30秒标准超时，长任务采用异步模式
- **重试**: 指数退避重试策略

#### 6.3.2 异步通信
- **消息队列**: Celery + Redis
- **任务类型**: 文档处理、向量化、图谱构建
- **可靠性**: 任务持久化、失败重试、死信队列

#### 6.3.3 事件驱动
- **事件总线**: Redis Pub/Sub
- **事件类型**: 文档上传、处理完成、用户操作
- **处理模式**: 异步事件处理、最终一致性

### 6.4 组件设计决策说明

**微服务拆分原则**
按业务领域拆分的原因：
- 每个服务专注单一业务职责，便于独立开发和部署
- 不同服务可选择最适合的技术栈和数据存储
- 支持团队独立工作，减少开发依赖

**异步处理设计**
采用Celery任务队列的考虑：
- 文档处理和向量化是CPU密集型任务，需要异步处理
- 支持任务优先级、重试和监控
- 可水平扩展worker节点，提高处理能力

**数据存储策略**
多数据库架构的选择：
- PostgreSQL：关系型数据，ACID事务保证
- Weaviate：向量数据，高效语义检索
- Neo4j：图数据，复杂关系查询
- Redis：缓存和会话，高性能读写
- MinIO：对象存储，大文件管理

## 7. 项目结构

基于微服务架构和Monorepo管理策略，Knowledge RAG项目采用统一代码仓库管理多个服务组件。项目结构设计遵循关注点分离、模块化开发和可维护性原则，支持独立开发、测试和部署。

### 7.1 Monorepo布局设计

```
knowledge-rag/
├── README.md                          # 项目总体说明
├── docker-compose.yml                 # 本地开发环境
├── docker-compose.prod.yml            # 生产环境配置
├── .env.example                       # 环境变量模板
├── .gitignore                         # Git忽略规则
├── Makefile                           # 构建和部署脚本
├── package.json                       # 根级依赖管理
├── requirements.txt                   # Python依赖汇总
├── pyproject.toml                     # Python项目配置
├── .pre-commit-config.yaml           # 代码质量检查
├── .github/                           # GitHub Actions CI/CD
│   └── workflows/
│       ├── ci.yml                     # 持续集成
│       ├── cd.yml                     # 持续部署
│       └── security-scan.yml          # 安全扫描
├── docs/                              # 项目文档
│   ├── api/                           # API文档
│   ├── architecture/                  # 架构设计文档
│   ├── deployment/                    # 部署指南
│   └── development/                   # 开发指南
├── scripts/                           # 构建和部署脚本
│   ├── build.sh                       # 构建脚本
│   ├── deploy.sh                      # 部署脚本
│   ├── test.sh                        # 测试脚本
│   └── setup-dev.sh                   # 开发环境设置
├── config/                            # 配置文件
│   ├── development/                   # 开发环境配置
│   ├── staging/                       # 测试环境配置
│   ├── production/                    # 生产环境配置
│   └── k8s/                           # Kubernetes配置
│       ├── namespace.yaml
│       ├── configmap.yaml
│       ├── secrets.yaml
│       └── services/
├── services/                          # 微服务目录
│   ├── api-gateway/                   # API网关服务
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py                # FastAPI应用入口
│   │   │   ├── config.py              # 配置管理
│   │   │   ├── middleware/            # 中间件
│   │   │   ├── routes/                # 路由定义
│   │   │   └── utils/                 # 工具函数
│   │   ├── tests/                     # 单元测试
│   │   └── k8s/                       # Kubernetes配置
│   ├── user-service/                  # 用户管理服务
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   ├── models/                # 数据模型
│   │   │   ├── schemas/               # Pydantic模式
│   │   │   ├── services/              # 业务逻辑
│   │   │   ├── repositories/          # 数据访问层
│   │   │   ├── auth/                  # 认证授权
│   │   │   └── utils/
│   │   ├── migrations/                # 数据库迁移
│   │   ├── tests/
│   │   └── k8s/
│   ├── document-service/              # 文档处理服务
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   ├── processors/            # 文档处理器
│   │   │   │   ├── pdf_processor.py
│   │   │   │   ├── docx_processor.py
│   │   │   │   ├── txt_processor.py
│   │   │   │   └── image_processor.py
│   │   │   ├── parsers/               # 内容解析器
│   │   │   ├── storage/               # 存储管理
│   │   │   ├── tasks/                 # Celery任务
│   │   │   └── models/
│   │   ├── tests/
│   │   └── k8s/
│   ├── vector-service/                # 向量检索服务
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   ├── embeddings/            # 嵌入模型管理
│   │   │   │   ├── openai_embedder.py
│   │   │   │   ├── local_embedder.py
│   │   │   │   └── embedding_cache.py
│   │   │   ├── search/                # 检索引擎
│   │   │   ├── indexing/              # 索引管理
│   │   │   ├── models/
│   │   │   └── tasks/
│   │   ├── tests/
│   │   └── k8s/
│   ├── graph-service/                 # 知识图谱服务
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   ├── extractors/            # 实体关系抽取
│   │   │   │   ├── ner_extractor.py
│   │   │   │   ├── relation_extractor.py
│   │   │   │   └── entity_linker.py
│   │   │   ├── graph/                 # 图谱操作
│   │   │   │   ├── builder.py
│   │   │   │   ├── query_engine.py
│   │   │   │   └── reasoner.py
│   │   │   ├── models/
│   │   │   └── tasks/
│   │   ├── tests/
│   │   └── k8s/
│   └── query-service/                 # 查询引擎服务
│       ├── Dockerfile
│       ├── requirements.txt
│       ├── app/
│       │   ├── __init__.py
│       │   ├── main.py
│       │   ├── engines/               # 查询引擎
│       │   │   ├── graphrag_engine.py
│       │   │   ├── retrieval_engine.py
│       │   │   └── ranking_engine.py
│       │   ├── llm/                   # LLM集成
│       │   │   ├── openai_client.py
│       │   │   ├── claude_client.py
│       │   │   └── prompt_templates.py
│       │   ├── context/               # 上下文管理
│       │   ├── models/
│       │   └── tasks/
│       ├── tests/
│       └── k8s/

├── shared/                            # 共享代码库
│   ├── __init__.py
│   ├── models/                        # 共享数据模型
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── document.py
│   │   ├── workspace.py
│   │   └── query.py
│   ├── schemas/                       # 共享Pydantic模式
│   ├── utils/                         # 共享工具函数
│   │   ├── __init__.py
│   │   ├── logging.py
│   │   ├── security.py
│   │   ├── validation.py
│   │   └── constants.py
│   ├── exceptions/                    # 自定义异常
│   └── middleware/                    # 共享中间件
├── infrastructure/                    # 基础设施代码
│   ├── terraform/                     # Terraform配置
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── modules/
│   ├── ansible/                       # Ansible配置
│   └── monitoring/                    # 监控配置
│       ├── prometheus/
│       ├── grafana/
│       └── alertmanager/
├── data/                              # 数据文件
│   ├── migrations/                    # 数据库迁移
│   ├── seeds/                         # 种子数据
│   └── fixtures/                      # 测试数据
└── tests/                             # 集成测试
    ├── integration/                   # 集成测试
    ├── e2e/                           # 端到端测试
    ├── performance/                   # 性能测试
    └── fixtures/                      # 测试夹具
```

### 7.2 服务组件结构详解

#### 7.2.1 标准服务结构模板

每个微服务遵循统一的目录结构：

```python
# 服务标准结构
service-name/
├── Dockerfile                         # 容器化配置
├── requirements.txt                   # Python依赖
├── .env.example                       # 环境变量模板
├── app/                               # 应用代码
│   ├── __init__.py
│   ├── main.py                        # FastAPI应用入口
│   ├── config.py                      # 配置管理
│   ├── models/                        # 数据模型
│   │   ├── __init__.py
│   │   └── *.py                       # 具体模型文件
│   ├── schemas/                       # Pydantic模式
│   │   ├── __init__.py
│   │   ├── request.py                 # 请求模式
│   │   └── response.py                # 响应模式
│   ├── services/                      # 业务逻辑层
│   │   ├── __init__.py
│   │   └── *.py                       # 业务服务
│   ├── repositories/                  # 数据访问层
│   │   ├── __init__.py
│   │   └── *.py                       # 数据仓库
│   ├── routes/                        # API路由
│   │   ├── __init__.py
│   │   └── *.py                       # 路由定义
│   ├── middleware/                    # 中间件
│   ├── utils/                         # 工具函数
│   └── tasks/                         # 异步任务
├── tests/                             # 单元测试
│   ├── __init__.py
│   ├── conftest.py                    # pytest配置
│   ├── test_*.py                      # 测试文件
│   └── fixtures/                      # 测试夹具
├── migrations/                        # 数据库迁移（如需要）
└── k8s/                               # Kubernetes配置
    ├── deployment.yaml
    ├── service.yaml
    ├── configmap.yaml
    └── ingress.yaml
```



### 7.3 共享代码管理

#### 7.3.1 共享模型定义

```python
# shared/models/base.py
"""
基础模型定义
提供所有业务模型的基类和通用字段
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from uuid import UUID, uuid4

class BaseEntity(BaseModel):
    """基础实体模型"""
    id: UUID = Field(default_factory=uuid4, description="唯一标识符")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    is_active: bool = Field(True, description="是否激活")
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }

class TimestampMixin(BaseModel):
    """时间戳混入类"""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
class WorkspaceScoped(BaseModel):
    """工作空间范围混入类"""
    workspace_id: UUID = Field(..., description="工作空间ID")
```

#### 7.3.2 共享工具函数

```python
# shared/utils/logging.py
"""
统一日志配置
为所有服务提供标准化的日志记录功能
"""
import logging
import sys
from typing import Optional
from pythonjsonlogger import jsonlogger

def setup_logging(
    service_name: str,
    log_level: str = "INFO",
    json_format: bool = True
) -> logging.Logger:
    """设置服务日志配置"""
    logger = logging.getLogger(service_name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # 清除现有处理器
    logger.handlers.clear()
    
    # 创建控制台处理器
    handler = logging.StreamHandler(sys.stdout)
    
    if json_format:
        # JSON格式日志
        formatter = jsonlogger.JsonFormatter(
            '%(asctime)s %(name)s %(levelname)s %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    else:
        # 标准格式日志
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger
```

### 7.4 配置管理策略

#### 7.4.1 环境配置分离

```python
# shared/config/base.py
"""
基础配置类
定义所有服务的通用配置项
"""
from typing import Optional, List
from pydantic import BaseSettings, Field

class BaseConfig(BaseSettings):
    """基础配置类"""
    # 应用基础配置
    app_name: str = Field(..., description="应用名称")
    app_version: str = Field("1.0.0", description="应用版本")
    debug: bool = Field(False, description="调试模式")
    
    # 数据库配置
    database_url: str = Field(..., description="数据库连接URL")
    database_pool_size: int = Field(10, description="数据库连接池大小")
    
    # Redis配置
    redis_url: str = Field(..., description="Redis连接URL")
    redis_max_connections: int = Field(20, description="Redis最大连接数")
    
    # 日志配置
    log_level: str = Field("INFO", description="日志级别")
    log_format: str = Field("json", description="日志格式")
    
    # 安全配置
    secret_key: str = Field(..., description="应用密钥")
    jwt_algorithm: str = Field("HS256", description="JWT算法")
    jwt_expire_minutes: int = Field(30, description="JWT过期时间（分钟）")
    
    # CORS配置
    cors_origins: List[str] = Field(["*"], description="CORS允许的源")
    
    class Config:
        env_file = ".env"
        case_sensitive = False

class DatabaseConfig(BaseSettings):
    """数据库专用配置"""
    postgres_host: str = Field(..., description="PostgreSQL主机")
    postgres_port: int = Field(5432, description="PostgreSQL端口")
    postgres_db: str = Field(..., description="数据库名")
    postgres_user: str = Field(..., description="数据库用户")
    postgres_password: str = Field(..., description="数据库密码")
    
    @property
    def database_url(self) -> str:
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
```

### 7.5 构建和部署配置

#### 7.5.1 Docker配置模板

```dockerfile
# services/*/Dockerfile模板
# 多阶段构建，优化镜像大小
FROM python:3.11-slim as builder

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .
COPY ../shared ./shared

# 安装Python依赖
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# 生产阶段
FROM python:3.11-slim

# 创建非root用户
RUN groupadd -r appuser && useradd -r -g appuser appuser

# 设置工作目录
WORKDIR /app

# 从构建阶段复制依赖
COPY --from=builder /root/.local /home/appuser/.local
COPY --from=builder /app/shared ./shared

# 复制应用代码
COPY app ./app
COPY *.py ./

# 设置环境变量
ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONPATH=/app

# 切换到非root用户
USER appuser

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 7.5.2 Kubernetes配置模板

```yaml
# services/*/k8s/deployment.yaml模板
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ service-name }}
  namespace: knowledge-rag
  labels:
    app: {{ service-name }}
    version: v1
spec:
  replicas: 3
  selector:
    matchLabels:
      app: {{ service-name }}
  template:
    metadata:
      labels:
        app: {{ service-name }}
        version: v1
    spec:
      containers:
      - name: {{ service-name }}
        image: knowledge-rag/{{ service-name }}:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: database-secret
              key: url
        - name: REDIS_URL
          valueFrom:
            configMapKeyRef:
              name: redis-config
              key: url
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
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
```

### 7.6 项目结构设计决策

**Monorepo选择理由**
采用Monorepo管理的优势：
- 统一的代码版本管理和依赖管理
- 简化跨服务的代码共享和重构
- 统一的CI/CD流水线和构建工具
- 便于代码审查和质量控制

**服务拆分策略**
按业务领域拆分服务的考虑：
- 每个服务专注单一业务职责
- 支持独立开发、测试和部署
- 便于团队分工和并行开发
- 降低服务间的耦合度

**共享代码管理**
建立shared目录的原因：
- 避免代码重复，提高开发效率
- 统一数据模型和接口定义
- 简化跨服务的类型检查
- 便于统一的错误处理和日志记录

**配置管理策略**
环境配置分离的设计：
- 支持多环境部署（开发、测试、生产）
- 敏感信息通过环境变量管理
- 配置热更新和版本控制
- 符合12-Factor应用原则

---

## 7. 部署架构

本节定义Knowledge RAG系统的完整部署架构，包括Kubernetes集群设计、服务编排策略、CI/CD流水线和运维监控体系。

### 7.1 Kubernetes集群架构

#### 集群拓扑设计

```mermaid
graph TB
    subgraph "Production Cluster"
        subgraph "Control Plane"
            Master1["Master Node 1"]
            Master2["Master Node 2"]
            Master3["Master Node 3"]
        end
        
        subgraph "Worker Nodes"
            Worker1["Worker Node 1<br/>App Services"]
            Worker2["Worker Node 2<br/>App Services"]
            Worker3["Worker Node 3<br/>Data Services"]
            Worker4["Worker Node 4<br/>Data Services"]
        end
        
        subgraph "Storage"
            PV1["Persistent Volume<br/>PostgreSQL"]
            PV2["Persistent Volume<br/>Neo4j"]
            PV3["Persistent Volume<br/>Weaviate"]
            PV4["Persistent Volume<br/>Redis"]
        end
    end
    
    subgraph "External Services"
        LB["Load Balancer"]
        DNS["DNS Service"]
        Registry["Container Registry"]
        Monitoring["Monitoring Stack"]
    end
    
    LB --> Master1
    LB --> Master2
    LB --> Master3
    
    Worker1 --> PV1
    Worker2 --> PV2
    Worker3 --> PV3
    Worker4 --> PV4
```

#### 节点规格配置

**Master节点（控制平面）**
- **规格**：4 vCPU, 8GB RAM, 100GB SSD
- **数量**：3个（高可用）
- **职责**：API Server、etcd、Controller Manager、Scheduler
- **网络**：内网通信，外部API访问

**Worker节点（应用服务）**
- **规格**：8 vCPU, 16GB RAM, 200GB SSD
- **数量**：2-6个（自动扩缩容）
- **职责**：运行应用服务Pod
- **标签**：`node-type=app-services`

**Worker节点（数据服务）**
- **规格**：16 vCPU, 32GB RAM, 1TB SSD
- **数量**：2-4个（根据数据量扩展）
- **职责**：运行数据库和存储服务
- **标签**：`node-type=data-services`

### 7.2 服务编排策略

#### Namespace设计

```yaml
# 命名空间划分
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
  name: knowledge-rag-monitoring
  labels:
    environment: shared
    project: knowledge-rag
```

#### 服务部署配置

**API网关部署**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-gateway
  namespace: knowledge-rag-prod
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api-gateway
  template:
    metadata:
      labels:
        app: api-gateway
    spec:
      containers:
      - name: kong
        image: kong:3.4-alpine
        ports:
        - containerPort: 8000
        - containerPort: 8001
        env:
        - name: KONG_DATABASE
          value: "postgres"
        - name: KONG_PG_HOST
          value: "postgresql-service"
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
      nodeSelector:
        node-type: app-services
```

**微服务部署模板**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ .Values.serviceName }}
  namespace: {{ .Values.namespace }}
spec:
  replicas: {{ .Values.replicas }}
  selector:
    matchLabels:
      app: {{ .Values.serviceName }}
  template:
    metadata:
      labels:
        app: {{ .Values.serviceName }}
        version: {{ .Values.version }}
    spec:
      containers:
      - name: {{ .Values.serviceName }}
        image: {{ .Values.image.repository }}:{{ .Values.image.tag }}
        ports:
        - containerPort: {{ .Values.service.port }}
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: database-secret
              key: url
        - name: REDIS_URL
          valueFrom:
            configMapKeyRef:
              name: redis-config
              key: url
        livenessProbe:
          httpGet:
            path: /health
            port: {{ .Values.service.port }}
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: {{ .Values.service.port }}
          initialDelaySeconds: 5
          periodSeconds: 5
        resources:
          requests:
            memory: {{ .Values.resources.requests.memory }}
            cpu: {{ .Values.resources.requests.cpu }}
          limits:
            memory: {{ .Values.resources.limits.memory }}
            cpu: {{ .Values.resources.limits.cpu }}
```

#### 数据服务部署

**PostgreSQL集群**
```yaml
apiVersion: postgresql.cnpg.io/v1
kind: Cluster
metadata:
  name: postgresql-cluster
  namespace: knowledge-rag-prod
spec:
  instances: 3
  primaryUpdateStrategy: unsupervised
  
  postgresql:
    parameters:
      max_connections: "200"
      shared_buffers: "256MB"
      effective_cache_size: "1GB"
      work_mem: "4MB"
  
  bootstrap:
    initdb:
      database: knowledge_rag
      owner: app_user
      secret:
        name: postgresql-credentials
  
  storage:
    size: 100Gi
    storageClass: fast-ssd
  
  nodeSelector:
    node-type: data-services
  
  monitoring:
    enabled: true
```

**Weaviate向量数据库**
```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: weaviate
  namespace: knowledge-rag-prod
spec:
  serviceName: weaviate
  replicas: 2
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
        env:
        - name: QUERY_DEFAULTS_LIMIT
          value: "25"
        - name: AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED
          value: "false"
        - name: PERSISTENCE_DATA_PATH
          value: "/var/lib/weaviate"
        - name: CLUSTER_HOSTNAME
          value: "weaviate"
        volumeMounts:
        - name: weaviate-data
          mountPath: /var/lib/weaviate
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
      nodeSelector:
        node-type: data-services
  volumeClaimTemplates:
  - metadata:
      name: weaviate-data
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: fast-ssd
      resources:
        requests:
          storage: 200Gi
```

### 7.3 CI/CD流水线

#### GitLab CI/CD配置

```yaml
# .gitlab-ci.yml
stages:
  - test
  - build
  - security
  - deploy-staging
  - integration-test
  - deploy-production

variables:
  DOCKER_REGISTRY: registry.gitlab.com/knowledge-rag
  KUBERNETES_NAMESPACE_STAGING: knowledge-rag-staging
  KUBERNETES_NAMESPACE_PROD: knowledge-rag-prod

# 代码质量检查
code-quality:
  stage: test
  image: python:3.11-slim
  script:
    - curl -LsSf https://astral.sh/uv/install.sh | sh
    - uv sync --prerelease=allow
    - black --check .
    - isort --check-only .
    - flake8 .
    - mypy .
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == "main"

# 单元测试
unit-tests:
  stage: test
  image: python:3.11-slim
  services:
    - postgres:15
    - redis:7
  variables:
    POSTGRES_DB: test_db
    POSTGRES_USER: test_user
    POSTGRES_PASSWORD: test_pass
    DATABASE_URL: postgresql://test_user:test_pass@postgres:5432/test_db
    REDIS_URL: redis://redis:6379/0
  script:
    - curl -LsSf https://astral.sh/uv/install.sh | sh
    - uv sync --prerelease=allow
    - poetry run pytest --cov=src --cov-report=xml
  coverage: '/TOTAL.+ ([0-9]{1,3}%)$/'
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml

# 构建Docker镜像
build-images:
  stage: build
  image: docker:24-dind
  services:
    - docker:24-dind
  variables:
    DOCKER_TLS_CERTDIR: "/certs"
  before_script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
  script:
    - |
      for service in api-gateway user-service document-service vector-service knowledge-service query-service; do
        docker build -t $DOCKER_REGISTRY/$service:$CI_COMMIT_SHA -f services/$service/Dockerfile .
        docker push $DOCKER_REGISTRY/$service:$CI_COMMIT_SHA
        docker tag $DOCKER_REGISTRY/$service:$CI_COMMIT_SHA $DOCKER_REGISTRY/$service:latest
        docker push $DOCKER_REGISTRY/$service:latest
      done
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
    - if: $CI_COMMIT_BRANCH == "develop"

# 安全扫描
security-scan:
  stage: security
  image: aquasec/trivy:latest
  script:
    - |
      for service in api-gateway user-service document-service vector-service knowledge-service query-service; do
        trivy image --exit-code 1 --severity HIGH,CRITICAL $DOCKER_REGISTRY/$service:$CI_COMMIT_SHA
      done
  allow_failure: true
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
    - if: $CI_COMMIT_BRANCH == "develop"

# 部署到Staging环境
deploy-staging:
  stage: deploy-staging
  image: bitnami/kubectl:latest
  environment:
    name: staging
    url: https://staging.knowledge-rag.com
  script:
    - kubectl config use-context $KUBE_CONTEXT_STAGING
    - helm upgrade --install knowledge-rag-staging ./helm/knowledge-rag \
        --namespace $KUBERNETES_NAMESPACE_STAGING \
        --set image.tag=$CI_COMMIT_SHA \
        --set environment=staging \
        --values ./helm/values-staging.yaml
    - kubectl rollout status deployment/api-gateway -n $KUBERNETES_NAMESPACE_STAGING
  rules:
    - if: $CI_COMMIT_BRANCH == "develop"

# 集成测试
integration-tests:
  stage: integration-test
  image: postman/newman:latest
  script:
    - newman run tests/postman/integration-tests.json \
        --environment tests/postman/staging-environment.json \
        --reporters cli,junit \
        --reporter-junit-export integration-test-results.xml
  artifacts:
    reports:
      junit: integration-test-results.xml
  rules:
    - if: $CI_COMMIT_BRANCH == "develop"

# 部署到生产环境
deploy-production:
  stage: deploy-production
  image: bitnami/kubectl:latest
  environment:
    name: production
    url: https://knowledge-rag.com
  script:
    - kubectl config use-context $KUBE_CONTEXT_PROD
    - helm upgrade --install knowledge-rag-prod ./helm/knowledge-rag \
        --namespace $KUBERNETES_NAMESPACE_PROD \
        --set image.tag=$CI_COMMIT_SHA \
        --set environment=production \
        --values ./helm/values-production.yaml
    - kubectl rollout status deployment/api-gateway -n $KUBERNETES_NAMESPACE_PROD
  when: manual
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
```

#### Helm Chart配置

**Chart.yaml**
```yaml
apiVersion: v2
name: knowledge-rag
description: GraphRAG-based Knowledge Management System
type: application
version: 0.1.0
appVersion: "1.0.0"

dependencies:
  - name: postgresql
    version: 12.12.10
    repository: https://charts.bitnami.com/bitnami
    condition: postgresql.enabled
  - name: redis
    version: 18.1.5
    repository: https://charts.bitnami.com/bitnami
    condition: redis.enabled
  - name: prometheus
    version: 25.1.0
    repository: https://prometheus-community.github.io/helm-charts
    condition: monitoring.prometheus.enabled
```

**values.yaml**
```yaml
# 全局配置
global:
  imageRegistry: registry.gitlab.com/knowledge-rag
  storageClass: fast-ssd
  
# 应用配置
image:
  tag: latest
  pullPolicy: Always

environment: production

# 服务配置
services:
  apiGateway:
    enabled: true
    replicas: 3
    resources:
      requests:
        memory: 512Mi
        cpu: 250m
      limits:
        memory: 1Gi
        cpu: 500m
  
  userService:
    enabled: true
    replicas: 2
    resources:
      requests:
        memory: 256Mi
        cpu: 100m
      limits:
        memory: 512Mi
        cpu: 200m
  
  documentService:
    enabled: true
    replicas: 3
    resources:
      requests:
        memory: 1Gi
        cpu: 500m
      limits:
        memory: 2Gi
        cpu: 1000m
  
  vectorService:
    enabled: true
    replicas: 2
    resources:
      requests:
        memory: 2Gi
        cpu: 1000m
      limits:
        memory: 4Gi
        cpu: 2000m
  
  knowledgeService:
    enabled: true
    replicas: 2
    resources:
      requests:
        memory: 1Gi
        cpu: 500m
      limits:
        memory: 2Gi
        cpu: 1000m
  
  queryService:
    enabled: true
    replicas: 3
    resources:
      requests:
        memory: 1Gi
        cpu: 500m
      limits:
        memory: 2Gi
        cpu: 1000m

# 数据库配置
postgresql:
  enabled: true
  auth:
    postgresPassword: "secure-postgres-password"
    database: knowledge_rag
  primary:
    persistence:
      enabled: true
      size: 100Gi
      storageClass: fast-ssd
    resources:
      requests:
        memory: 2Gi
        cpu: 1000m
      limits:
        memory: 4Gi
        cpu: 2000m

redis:
  enabled: true
  auth:
    enabled: true
    password: "secure-redis-password"
  master:
    persistence:
      enabled: true
      size: 20Gi
      storageClass: fast-ssd
    resources:
      requests:
        memory: 1Gi
        cpu: 500m
      limits:
        memory: 2Gi
        cpu: 1000m

# 外部数据库
weaviate:
  enabled: true
  replicas: 2
  persistence:
    size: 200Gi
    storageClass: fast-ssd
  resources:
    requests:
      memory: 2Gi
      cpu: 1000m
    limits:
      memory: 4Gi
      cpu: 2000m

neo4j:
  enabled: true
  core:
    numberOfServers: 3
  readReplica:
    numberOfServers: 2
  persistence:
    size: 100Gi
    storageClass: fast-ssd
  resources:
    requests:
      memory: 2Gi
      cpu: 1000m
    limits:
      memory: 4Gi
      cpu: 2000m

# 监控配置
monitoring:
  prometheus:
    enabled: true
  grafana:
    enabled: true
  jaeger:
    enabled: true

# 网络配置
ingress:
  enabled: true
  className: nginx
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/rate-limit: "100"
  hosts:
    - host: api.knowledge-rag.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: knowledge-rag-tls
      hosts:
        - api.knowledge-rag.com

# 自动扩缩容
autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
  targetMemoryUtilizationPercentage: 80
```

### 7.4 监控和可观测性

#### Prometheus监控配置

```yaml
# prometheus-config.yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "knowledge-rag-rules.yml"

scrape_configs:
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

  - job_name: 'knowledge-rag-services'
    kubernetes_sd_configs:
      - role: endpoints
        namespaces:
          names:
            - knowledge-rag-prod
            - knowledge-rag-staging
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

  - job_name: 'postgresql'
    static_configs:
      - targets: ['postgresql-service:5432']
    metrics_path: /metrics
    scrape_interval: 30s

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-service:6379']
    metrics_path: /metrics
    scrape_interval: 30s
```

#### 告警规则配置

```yaml
# knowledge-rag-rules.yml
groups:
  - name: knowledge-rag-alerts
    rules:
      # 服务可用性告警
      - alert: ServiceDown
        expr: up{job=~"knowledge-rag-.*"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Service {{ $labels.job }} is down"
          description: "Service {{ $labels.job }} has been down for more than 1 minute."
      
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
          description: "Error rate is {{ $value | humanizePercentage }} for {{ $labels.job }}"
      
      # 高延迟告警
      - alert: HighLatency
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High latency detected"
          description: "95th percentile latency is {{ $value }}s for {{ $labels.job }}"
      
      # 内存使用率告警
      - alert: HighMemoryUsage
        expr: |
          (
            container_memory_working_set_bytes{pod=~"knowledge-rag-.*"} /
            container_spec_memory_limit_bytes{pod=~"knowledge-rag-.*"}
          ) > 0.8
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage detected"
          description: "Memory usage is {{ $value | humanizePercentage }} for {{ $labels.pod }}"
      
      # CPU使用率告警
      - alert: HighCPUUsage
        expr: |
          (
            rate(container_cpu_usage_seconds_total{pod=~"knowledge-rag-.*"}[5m]) /
            container_spec_cpu_quota{pod=~"knowledge-rag-.*"} * container_spec_cpu_period{pod=~"knowledge-rag-.*"}
          ) > 0.8
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage detected"
          description: "CPU usage is {{ $value | humanizePercentage }} for {{ $labels.pod }}"
      
      # 数据库连接告警
      - alert: DatabaseConnectionHigh
        expr: pg_stat_activity_count > 150
        for: 2m
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
```

#### Grafana仪表板

**系统概览仪表板**
```json
{
  "dashboard": {
    "title": "Knowledge RAG System Overview",
    "panels": [
      {
        "title": "Service Status",
        "type": "stat",
        "targets": [
          {
            "expr": "up{job=~\"knowledge-rag-.*\"}",
            "legendFormat": "{{ job }}"
          }
        ]
      },
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{ job }} - {{ method }}"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          },
          {
            "expr": "histogram_quantile(0.50, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "50th percentile"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total{status=~\"5..\"}[5m]) / rate(http_requests_total[5m])",
            "legendFormat": "{{ job }}"
          }
        ]
      },
      {
        "title": "Resource Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(container_cpu_usage_seconds_total{pod=~\"knowledge-rag-.*\"}[5m])",
            "legendFormat": "CPU - {{ pod }}"
          },
          {
            "expr": "container_memory_working_set_bytes{pod=~\"knowledge-rag-.*\"} / 1024 / 1024 / 1024",
            "legendFormat": "Memory (GB) - {{ pod }}"
          }
        ]
      }
    ]
  }
}
```

### 7.5 安全和合规

#### 网络安全策略

```yaml
# network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: knowledge-rag-network-policy
  namespace: knowledge-rag-prod
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: knowledge-rag-prod
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: knowledge-rag-prod
  - to: []
    ports:
    - protocol: TCP
      port: 53
    - protocol: UDP
      port: 53
  - to: []
    ports:
    - protocol: TCP
      port: 443
```

#### Pod安全策略

```yaml
# pod-security-policy.yaml
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
```

### 7.6 灾难恢复

#### 备份策略

**数据库备份**
```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: postgresql-backup
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
              BACKUP_FILE="/backup/postgresql-$(date +%Y%m%d-%H%M%S).sql"
              pg_dump $DATABASE_URL > $BACKUP_FILE
              aws s3 cp $BACKUP_FILE s3://knowledge-rag-backups/postgresql/
              find /backup -name "postgresql-*.sql" -mtime +7 -delete
            env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: database-secret
                  key: url
            volumeMounts:
            - name: backup-storage
              mountPath: /backup
          volumes:
          - name: backup-storage
            persistentVolumeClaim:
              claimName: backup-pvc
          restartPolicy: OnFailure
```

**向量数据备份**
```yaml
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
            image: semitechnologies/weaviate:1.22.4
            command:
            - /bin/bash
            - -c
            - |
              BACKUP_FILE="/backup/weaviate-$(date +%Y%m%d-%H%M%S).tar.gz"
              tar -czf $BACKUP_FILE /var/lib/weaviate
              aws s3 cp $BACKUP_FILE s3://knowledge-rag-backups/weaviate/
              find /backup -name "weaviate-*.tar.gz" -mtime +7 -delete
            volumeMounts:
            - name: weaviate-data
              mountPath: /var/lib/weaviate
            - name: backup-storage
              mountPath: /backup
          volumes:
          - name: weaviate-data
            persistentVolumeClaim:
              claimName: weaviate-pvc
          - name: backup-storage
            persistentVolumeClaim:
              claimName: backup-pvc
          restartPolicy: OnFailure
```

#### 恢复流程

**数据恢复脚本**
```bash
#!/bin/bash
# restore-database.sh

set -e

BACKUP_DATE=${1:-$(date +%Y%m%d)}
NAMESPACE=${2:-knowledge-rag-prod}

echo "Starting database restore for date: $BACKUP_DATE"

# 下载备份文件
aws s3 cp s3://knowledge-rag-backups/postgresql/postgresql-${BACKUP_DATE}*.sql /tmp/restore.sql

# 停止应用服务
kubectl scale deployment --replicas=0 -l app.kubernetes.io/component=application -n $NAMESPACE

# 等待Pod终止
kubectl wait --for=delete pod -l app.kubernetes.io/component=application -n $NAMESPACE --timeout=300s

# 恢复数据库
kubectl exec -n $NAMESPACE postgresql-cluster-1 -- psql -U postgres -d knowledge_rag -f /tmp/restore.sql

# 重启应用服务
kubectl scale deployment --replicas=2 -l app.kubernetes.io/component=application -n $NAMESPACE

# 等待服务就绪
kubectl wait --for=condition=available deployment -l app.kubernetes.io/component=application -n $NAMESPACE --timeout=600s

echo "Database restore completed successfully"
```

### 7.7 部署架构总结

#### 架构优势

1. **高可用性**
   - 多节点Kubernetes集群确保服务连续性
   - 数据库主从复制和自动故障转移
   - 多可用区部署降低单点故障风险

2. **可扩展性**
   - 水平Pod自动扩缩容（HPA）
   - 垂直Pod自动扩缩容（VPA）
   - 集群节点自动扩缩容

3. **安全性**
   - 网络策略隔离服务通信
   - Pod安全策略限制容器权限
   - 密钥管理和证书自动轮换

4. **可观测性**
   - 全方位监控指标收集
   - 分布式链路追踪
   - 集中化日志管理和分析

5. **运维效率**
   - GitOps工作流自动化部署
   - 基础设施即代码管理
   - 自动化备份和恢复流程

#### 部署清单

**基础设施准备**
- [ ] Kubernetes集群搭建（3 Master + 4 Worker）
- [ ] 存储类配置（fast-ssd）
- [ ] 网络插件安装（Calico/Flannel）
- [ ] Ingress控制器部署（Nginx）
- [ ] 证书管理器安装（cert-manager）

**监控体系部署**
- [ ] Prometheus Operator安装
- [ ] Grafana仪表板配置
- [ ] Jaeger链路追踪部署
- [ ] ELK日志栈安装
- [ ] 告警规则配置

**应用部署**
- [ ] Helm Chart开发和测试
- [ ] CI/CD流水线配置
- [ ] 数据库集群部署
- [ ] 微服务应用部署
- [ ] API网关配置

**安全加固**
- [ ] 网络策略配置
- [ ] Pod安全策略实施
- [ ] RBAC权限配置
- [ ] 密钥管理配置
- [ ] 安全扫描集成

**备份恢复**
- [ ] 自动备份任务配置
- [ ] 备份存储配置
- [ ] 恢复流程测试
- [ ] 灾难恢复演练

---

---

## 8. 性能优化策略

本节详细阐述Knowledge RAG系统的性能优化策略，包括系统性能调优、扩展方案、缓存策略和资源优化等关键技术。

### 8.1 系统性能分析

#### 性能瓶颈识别

**计算密集型瓶颈**
- **向量化处理**：文档向量化和相似度计算
- **LLM推理**：大语言模型的推理延迟
- **图数据库查询**：复杂的图遍历和模式匹配
- **实体抽取**：NLP模型的实体识别和关系抽取

**I/O密集型瓶颈**
- **数据库查询**：PostgreSQL的复杂关联查询
- **向量检索**：Weaviate的大规模向量搜索
- **文件存储**：大文档的上传和下载
- **网络通信**：微服务间的API调用

**内存瓶颈**
- **向量缓存**：大量向量数据的内存占用
- **模型加载**：LLM和NLP模型的内存消耗
- **图数据缓存**：知识图谱的内存存储
- **会话状态**：用户会话和上下文的内存管理

#### 性能监控指标

```yaml
# 关键性能指标（KPI）
performance_metrics:
  response_time:
    api_gateway: "< 100ms (P95)"
    document_upload: "< 5s (P95)"
    vector_search: "< 500ms (P95)"
    qa_generation: "< 3s (P95)"
    graph_query: "< 1s (P95)"
  
  throughput:
    concurrent_users: "> 1000"
    documents_per_hour: "> 10000"
    queries_per_second: "> 100"
    vector_operations_per_second: "> 1000"
  
  resource_utilization:
    cpu_usage: "< 70% (average)"
    memory_usage: "< 80% (average)"
    disk_io: "< 80% (peak)"
    network_bandwidth: "< 60% (peak)"
  
  availability:
    system_uptime: "> 99.9%"
    service_availability: "> 99.95%"
    data_consistency: "100%"
```

### 8.2 缓存优化策略

#### 多层缓存架构

```mermaid
graph TB
    subgraph "缓存层次结构"
        L1["L1: 应用内存缓存<br/>Redis Cluster"]
        L2["L2: 分布式缓存<br/>Redis Sentinel"]
        L3["L3: 数据库缓存<br/>PostgreSQL Buffer"]
        L4["L4: 向量缓存<br/>Weaviate Memory"]
    end
    
    subgraph "缓存策略"
        LRU["LRU淘汰策略"]
        TTL["TTL过期策略"]
        WriteThrough["写透策略"]
        WriteBack["写回策略"]
    end
    
    L1 --> LRU
    L2 --> TTL
    L3 --> WriteThrough
    L4 --> WriteBack
```

#### Redis缓存配置

**Redis集群配置**
```yaml
# redis-cluster.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: redis-cluster
  namespace: knowledge-rag-prod
spec:
  serviceName: redis-cluster
  replicas: 6
  selector:
    matchLabels:
      app: redis-cluster
  template:
    metadata:
      labels:
        app: redis-cluster
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
        - containerPort: 16379
        command:
        - redis-server
        args:
        - /etc/redis/redis.conf
        - --cluster-enabled yes
        - --cluster-config-file nodes.conf
        - --cluster-node-timeout 5000
        - --appendonly yes
        - --maxmemory 2gb
        - --maxmemory-policy allkeys-lru
        - --save 900 1
        - --save 300 10
        - --save 60 10000
        volumeMounts:
        - name: redis-data
          mountPath: /data
        - name: redis-config
          mountPath: /etc/redis
        resources:
          requests:
            memory: "2Gi"
            cpu: "500m"
          limits:
            memory: "4Gi"
            cpu: "1000m"
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

**缓存策略实现**
```python
# cache_manager.py
"""
Knowledge RAG系统缓存管理器
提供多层缓存策略和性能优化功能
"""

import redis
import json
import hashlib
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

class CacheLevel(Enum):
    """缓存级别枚举"""
    L1_MEMORY = "l1_memory"
    L2_DISTRIBUTED = "l2_distributed"
    L3_DATABASE = "l3_database"
    L4_VECTOR = "l4_vector"

@dataclass
class CacheConfig:
    """缓存配置类"""
    ttl: int  # 生存时间（秒）
    max_size: int  # 最大缓存大小
    eviction_policy: str  # 淘汰策略
    compression: bool = False  # 是否压缩
    serialization: str = "json"  # 序列化方式

class CacheManager:
    """多层缓存管理器"""
    
    def __init__(self, redis_cluster_nodes: List[Dict[str, Any]]):
        """
        初始化缓存管理器
        
        Args:
            redis_cluster_nodes: Redis集群节点配置
        """
        self.redis_cluster = redis.RedisCluster(
            startup_nodes=redis_cluster_nodes,
            decode_responses=True,
            skip_full_coverage_check=True,
            health_check_interval=30
        )
        
        # 缓存配置
        self.cache_configs = {
            "document_vectors": CacheConfig(
                ttl=3600,  # 1小时
                max_size=10000,
                eviction_policy="lru",
                compression=True
            ),
            "search_results": CacheConfig(
                ttl=1800,  # 30分钟
                max_size=5000,
                eviction_policy="lru"
            ),
            "user_sessions": CacheConfig(
                ttl=7200,  # 2小时
                max_size=1000,
                eviction_policy="ttl"
            ),
            "knowledge_graph": CacheConfig(
                ttl=86400,  # 24小时
                max_size=50000,
                eviction_policy="lfu",
                compression=True
            )
        }
    
    def _generate_cache_key(self, namespace: str, key: str) -> str:
        """生成缓存键"""
        return f"{namespace}:{hashlib.md5(key.encode()).hexdigest()}"
    
    def get(self, namespace: str, key: str) -> Optional[Any]:
        """
        获取缓存数据
        
        Args:
            namespace: 命名空间
            key: 缓存键
            
        Returns:
            缓存的数据或None
        """
        cache_key = self._generate_cache_key(namespace, key)
        
        try:
            # 尝试从Redis获取
            cached_data = self.redis_cluster.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            print(f"Cache get error: {e}")
        
        return None
    
    def set(self, namespace: str, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        设置缓存数据
        
        Args:
            namespace: 命名空间
            key: 缓存键
            value: 缓存值
            ttl: 生存时间（秒）
            
        Returns:
            是否设置成功
        """
        cache_key = self._generate_cache_key(namespace, key)
        config = self.cache_configs.get(namespace)
        
        if not config:
            return False
        
        try:
            # 序列化数据
            serialized_data = json.dumps(value, ensure_ascii=False)
            
            # 设置TTL
            cache_ttl = ttl or config.ttl
            
            # 存储到Redis
            return self.redis_cluster.setex(
                cache_key, 
                cache_ttl, 
                serialized_data
            )
        except Exception as e:
            print(f"Cache set error: {e}")
            return False
    
    def delete(self, namespace: str, key: str) -> bool:
        """
        删除缓存数据
        
        Args:
            namespace: 命名空间
            key: 缓存键
            
        Returns:
            是否删除成功
        """
        cache_key = self._generate_cache_key(namespace, key)
        
        try:
            return bool(self.redis_cluster.delete(cache_key))
        except Exception as e:
            print(f"Cache delete error: {e}")
            return False
    
    def invalidate_pattern(self, pattern: str) -> int:
        """
        按模式批量删除缓存
        
        Args:
            pattern: 匹配模式
            
        Returns:
            删除的键数量
        """
        try:
            keys = self.redis_cluster.keys(pattern)
            if keys:
                return self.redis_cluster.delete(*keys)
            return 0
        except Exception as e:
            print(f"Cache invalidate error: {e}")
            return 0
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Returns:
            缓存统计数据
        """
        try:
            info = self.redis_cluster.info()
            return {
                "memory_usage": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "total_commands_processed": info.get("total_commands_processed"),
                "keyspace_hits": info.get("keyspace_hits"),
                "keyspace_misses": info.get("keyspace_misses"),
                "hit_rate": (
                    info.get("keyspace_hits", 0) / 
                    (info.get("keyspace_hits", 0) + info.get("keyspace_misses", 1))
                ) * 100
            }
        except Exception as e:
            print(f"Cache stats error: {e}")
            return {}
```

### 8.3 数据库优化

#### PostgreSQL性能调优

**数据库配置优化**
```sql
-- postgresql.conf 优化配置

-- 内存配置
shared_buffers = '4GB'                    -- 共享缓冲区
effective_cache_size = '12GB'             -- 有效缓存大小
work_mem = '256MB'                        -- 工作内存
maintenance_work_mem = '1GB'              -- 维护工作内存

-- 连接配置
max_connections = 200                     -- 最大连接数
max_prepared_transactions = 100           -- 最大预处理事务

-- 检查点配置
checkpoint_completion_target = 0.9        -- 检查点完成目标
wal_buffers = '64MB'                      -- WAL缓冲区
max_wal_size = '4GB'                      -- 最大WAL大小
min_wal_size = '1GB'                      -- 最小WAL大小

-- 查询优化
random_page_cost = 1.1                   -- 随机页面成本
effective_io_concurrency = 200            -- 有效IO并发

-- 日志配置
log_min_duration_statement = 1000         -- 记录慢查询（1秒）
log_checkpoints = on                      -- 记录检查点
log_connections = on                      -- 记录连接
log_disconnections = on                   -- 记录断开连接
log_lock_waits = on                       -- 记录锁等待
```

**索引优化策略**
```sql
-- 创建复合索引优化查询性能

-- 文档表索引
CREATE INDEX CONCURRENTLY idx_documents_workspace_status 
    ON documents(workspace_id, status) 
    WHERE status IN ('active', 'processing');

CREATE INDEX CONCURRENTLY idx_documents_created_at_desc 
    ON documents(created_at DESC);

CREATE INDEX CONCURRENTLY idx_documents_content_search 
    ON documents USING gin(to_tsvector('english', title || ' ' || content));

-- 向量表索引
CREATE INDEX CONCURRENTLY idx_vectors_document_chunk 
    ON document_vectors(document_id, chunk_index);

CREATE INDEX CONCURRENTLY idx_vectors_embedding_cosine 
    ON document_vectors USING ivfflat (embedding vector_cosine_ops) 
    WITH (lists = 1000);

-- 知识图谱索引
CREATE INDEX CONCURRENTLY idx_entities_type_name 
    ON entities(entity_type, name);

CREATE INDEX CONCURRENTLY idx_relationships_source_target 
    ON relationships(source_entity_id, target_entity_id);

-- 用户会话索引
CREATE INDEX CONCURRENTLY idx_user_sessions_user_active 
    ON user_sessions(user_id, is_active) 
    WHERE is_active = true;
```

**查询优化示例**
```sql
-- 优化前：慢查询
SELECT d.*, dv.embedding 
FROM documents d 
JOIN document_vectors dv ON d.id = dv.document_id 
WHERE d.workspace_id = $1 
AND d.status = 'active' 
ORDER BY d.created_at DESC 
LIMIT 50;

-- 优化后：使用索引和分页
WITH recent_docs AS (
    SELECT id, title, content, created_at
    FROM documents 
    WHERE workspace_id = $1 
    AND status = 'active'
    AND created_at > $2  -- 使用时间范围过滤
    ORDER BY created_at DESC 
    LIMIT 50
)
SELECT rd.*, dv.embedding 
FROM recent_docs rd
LEFT JOIN document_vectors dv ON rd.id = dv.document_id
ORDER BY rd.created_at DESC;
```

#### 向量数据库优化

**Weaviate性能配置**
```yaml
# weaviate-performance.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: weaviate-config
  namespace: knowledge-rag-prod
data:
  weaviate.conf: |
    # 性能优化配置
    QUERY_DEFAULTS_LIMIT: "100"
    QUERY_MAXIMUM_RESULTS: "10000"
    
    # 向量索引配置
    DEFAULT_VECTORIZER_MODULE: "none"
    ENABLE_MODULES: "backup-filesystem,text2vec-openai"
    
    # 内存配置
    GOGC: "100"
    GOMEMLIMIT: "8GiB"
    
    # 并发配置
    ASYNC_INDEXING: "true"
    MAX_IMPORT_GOROUTINE_FACTOR: "1.5"
    
    # 持久化配置
    PERSISTENCE_DATA_PATH: "/var/lib/weaviate"
    BACKUP_FILESYSTEM_PATH: "/var/lib/weaviate/backups"
    
    # 集群配置
    CLUSTER_HOSTNAME: "weaviate"
    CLUSTER_GOSSIP_BIND_PORT: "7946"
    CLUSTER_DATA_BIND_PORT: "7947"
```

### 8.4 微服务性能优化

#### 连接池优化

```python
# connection_pool.py
"""
数据库连接池优化配置
提供高性能的数据库连接管理
"""

import asyncio
import asyncpg
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

class DatabasePool:
    """异步数据库连接池管理器"""
    
    def __init__(self, database_url: str, **pool_kwargs):
        """
        初始化数据库连接池
        
        Args:
            database_url: 数据库连接URL
            **pool_kwargs: 连接池参数
        """
        self.database_url = database_url
        self.pool_kwargs = {
            'min_size': 10,          # 最小连接数
            'max_size': 50,          # 最大连接数
            'max_queries': 50000,    # 每个连接最大查询数
            'max_inactive_connection_lifetime': 300,  # 连接最大空闲时间
            'command_timeout': 30,   # 命令超时时间
            **pool_kwargs
        }
        self.pool: Optional[asyncpg.Pool] = None
    
    async def initialize(self):
        """初始化连接池"""
        self.pool = await asyncpg.create_pool(
            self.database_url,
            **self.pool_kwargs
        )
    
    async def close(self):
        """关闭连接池"""
        if self.pool:
            await self.pool.close()
    
    @asynccontextmanager
    async def acquire(self):
        """获取数据库连接"""
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
        
        async with self.pool.acquire() as connection:
            yield connection
    
    async def execute(self, query: str, *args) -> str:
        """执行SQL命令"""
        async with self.acquire() as conn:
            return await conn.execute(query, *args)
    
    async def fetch(self, query: str, *args) -> list:
        """查询多行数据"""
        async with self.acquire() as conn:
            return await conn.fetch(query, *args)
    
    async def fetchrow(self, query: str, *args) -> Optional[Dict[str, Any]]:
        """查询单行数据"""
        async with self.acquire() as conn:
            row = await conn.fetchrow(query, *args)
            return dict(row) if row else None
    
    async def get_pool_stats(self) -> Dict[str, Any]:
        """获取连接池统计信息"""
        if not self.pool:
            return {}
        
        return {
            'size': self.pool.get_size(),
            'min_size': self.pool.get_min_size(),
            'max_size': self.pool.get_max_size(),
            'idle_size': self.pool.get_idle_size()
        }
```

#### 异步处理优化

```python
# async_processor.py
"""
异步任务处理器
提供高性能的异步任务处理和队列管理
"""

import asyncio
import aioredis
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import json
import time
from concurrent.futures import ThreadPoolExecutor

class TaskPriority(Enum):
    """任务优先级枚举"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class Task:
    """异步任务数据类"""
    id: str
    type: str
    payload: Dict[str, Any]
    priority: TaskPriority = TaskPriority.NORMAL
    retry_count: int = 0
    max_retries: int = 3
    created_at: float = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()

class AsyncTaskProcessor:
    """异步任务处理器"""
    
    def __init__(self, redis_url: str, max_workers: int = 10):
        """
        初始化异步任务处理器
        
        Args:
            redis_url: Redis连接URL
            max_workers: 最大工作线程数
        """
        self.redis_url = redis_url
        self.max_workers = max_workers
        self.redis: Optional[aioredis.Redis] = None
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.task_handlers: Dict[str, Callable] = {}
        self.running = False
        
        # 队列名称
        self.queues = {
            TaskPriority.CRITICAL: "tasks:critical",
            TaskPriority.HIGH: "tasks:high",
            TaskPriority.NORMAL: "tasks:normal",
            TaskPriority.LOW: "tasks:low"
        }
    
    async def initialize(self):
        """初始化Redis连接"""
        self.redis = aioredis.from_url(self.redis_url)
    
    async def close(self):
        """关闭连接和线程池"""
        self.running = False
        if self.redis:
            await self.redis.close()
        self.executor.shutdown(wait=True)
    
    def register_handler(self, task_type: str, handler: Callable):
        """注册任务处理器"""
        self.task_handlers[task_type] = handler
    
    async def enqueue_task(self, task: Task) -> bool:
        """
        将任务加入队列
        
        Args:
            task: 要处理的任务
            
        Returns:
            是否成功加入队列
        """
        if not self.redis:
            return False
        
        try:
            queue_name = self.queues[task.priority]
            task_data = json.dumps({
                'id': task.id,
                'type': task.type,
                'payload': task.payload,
                'priority': task.priority.value,
                'retry_count': task.retry_count,
                'max_retries': task.max_retries,
                'created_at': task.created_at
            })
            
            await self.redis.lpush(queue_name, task_data)
            return True
        except Exception as e:
            print(f"Enqueue task error: {e}")
            return False
    
    async def dequeue_task(self) -> Optional[Task]:
        """
        从队列中取出任务（按优先级）
        
        Returns:
            下一个要处理的任务或None
        """
        if not self.redis:
            return None
        
        try:
            # 按优先级顺序检查队列
            for priority in [TaskPriority.CRITICAL, TaskPriority.HIGH, 
                           TaskPriority.NORMAL, TaskPriority.LOW]:
                queue_name = self.queues[priority]
                task_data = await self.redis.brpop(queue_name, timeout=1)
                
                if task_data:
                    _, data = task_data
                    task_dict = json.loads(data)
                    return Task(
                        id=task_dict['id'],
                        type=task_dict['type'],
                        payload=task_dict['payload'],
                        priority=TaskPriority(task_dict['priority']),
                        retry_count=task_dict['retry_count'],
                        max_retries=task_dict['max_retries'],
                        created_at=task_dict['created_at']
                    )
        except Exception as e:
            print(f"Dequeue task error: {e}")
        
        return None
    
    async def process_task(self, task: Task) -> bool:
        """
        处理单个任务
        
        Args:
            task: 要处理的任务
            
        Returns:
            是否处理成功
        """
        handler = self.task_handlers.get(task.type)
        if not handler:
            print(f"No handler for task type: {task.type}")
            return False
        
        try:
            # 在线程池中执行CPU密集型任务
            if asyncio.iscoroutinefunction(handler):
                await handler(task.payload)
            else:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(self.executor, handler, task.payload)
            
            return True
        except Exception as e:
            print(f"Task processing error: {e}")
            
            # 重试逻辑
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                await self.enqueue_task(task)
            
            return False
    
    async def start_processing(self):
        """开始处理任务"""
        self.running = True
        
        # 创建多个工作协程
        workers = [
            asyncio.create_task(self._worker(f"worker-{i}"))
            for i in range(self.max_workers)
        ]
        
        try:
            await asyncio.gather(*workers)
        except Exception as e:
            print(f"Task processing stopped: {e}")
        finally:
            self.running = False
    
    async def _worker(self, worker_name: str):
        """工作协程"""
        print(f"Worker {worker_name} started")
        
        while self.running:
            try:
                task = await self.dequeue_task()
                if task:
                    print(f"Worker {worker_name} processing task {task.id}")
                    success = await self.process_task(task)
                    if success:
                        print(f"Task {task.id} completed successfully")
                    else:
                        print(f"Task {task.id} failed")
            except Exception as e:
                print(f"Worker {worker_name} error: {e}")
                await asyncio.sleep(1)
        
        print(f"Worker {worker_name} stopped")
    
    async def get_queue_stats(self) -> Dict[str, Any]:
        """获取队列统计信息"""
        if not self.redis:
            return {}
        
        stats = {}
        for priority, queue_name in self.queues.items():
            try:
                length = await self.redis.llen(queue_name)
                stats[priority.name.lower()] = length
            except Exception:
                stats[priority.name.lower()] = 0
        
        return stats
```

### 8.5 负载均衡和扩展

#### 水平扩展策略

**Kubernetes HPA配置**
```yaml
# hpa-config.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: knowledge-rag-hpa
  namespace: knowledge-rag-prod
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: query-service
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  - type: Pods
    pods:
      metric:
        name: http_requests_per_second
      target:
        type: AverageValue
        averageValue: "100"
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
      - type: Pods
        value: 2
        periodSeconds: 60
      selectPolicy: Max
```

**负载均衡配置**
```yaml
# nginx-lb.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: nginx-lb-config
  namespace: knowledge-rag-prod
data:
  nginx.conf: |
    upstream query_service {
        least_conn;
        server query-service-1:8000 max_fails=3 fail_timeout=30s;
        server query-service-2:8000 max_fails=3 fail_timeout=30s;
        server query-service-3:8000 max_fails=3 fail_timeout=30s;
        keepalive 32;
    }
    
    upstream vector_service {
        ip_hash;  # 会话粘性
        server vector-service-1:8000 max_fails=3 fail_timeout=30s;
        server vector-service-2:8000 max_fails=3 fail_timeout=30s;
        keepalive 16;
    }
    
    server {
        listen 80;
        server_name api.knowledge-rag.com;
        
        # 连接超时配置
        proxy_connect_timeout 5s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
        
        # 缓冲区配置
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
        
        # 压缩配置
        gzip on;
        gzip_vary on;
        gzip_min_length 1000;
        gzip_types text/plain application/json application/xml;
        
        # API路由
        location /api/v1/query {
            proxy_pass http://query_service;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            
            # 限流配置
            limit_req zone=api burst=20 nodelay;
        }
        
        location /api/v1/vectors {
            proxy_pass http://vector_service;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            
            # 大文件上传配置
            client_max_body_size 100M;
            proxy_request_buffering off;
        }
    }
    
    # 限流配置
    http {
        limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    }
```

### 8.6 性能监控和调优

#### 性能监控仪表板

```json
{
  "dashboard": {
    "title": "Knowledge RAG Performance Dashboard",
    "panels": [
      {
        "title": "API Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{job=\"api-gateway\"}[5m]))",
            "legendFormat": "95th percentile"
          },
          {
            "expr": "histogram_quantile(0.50, rate(http_request_duration_seconds_bucket{job=\"api-gateway\"}[5m]))",
            "legendFormat": "50th percentile"
          }
        ],
        "yAxes": [{
          "unit": "s",
          "max": 5
        }]
      },
      {
        "title": "Database Performance",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(pg_stat_database_tup_fetched[5m])",
            "legendFormat": "Rows fetched/sec"
          },
          {
            "expr": "rate(pg_stat_database_tup_inserted[5m])",
            "legendFormat": "Rows inserted/sec"
          },
          {
            "expr": "pg_stat_activity_count",
            "legendFormat": "Active connections"
          }
        ]
      },
      {
        "title": "Cache Hit Rate",
        "type": "stat",
        "targets": [
          {
            "expr": "(rate(redis_keyspace_hits_total[5m]) / (rate(redis_keyspace_hits_total[5m]) + rate(redis_keyspace_misses_total[5m]))) * 100",
            "legendFormat": "Cache Hit Rate %"
          }
        ],
        "thresholds": {
          "steps": [
            {"color": "red", "value": 0},
            {"color": "yellow", "value": 80},
            {"color": "green", "value": 95}
          ]
        }
      },
      {
        "title": "Vector Search Performance",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(weaviate_query_duration_seconds_bucket[5m]))",
            "legendFormat": "Vector search P95"
          },
          {
            "expr": "rate(weaviate_queries_total[5m])",
            "legendFormat": "Queries/sec"
          }
        ]
      },
      {
        "title": "Resource Utilization",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(container_cpu_usage_seconds_total{pod=~\"knowledge-rag-.*\"}[5m]) * 100",
            "legendFormat": "CPU % - {{pod}}"
          },
          {
            "expr": "(container_memory_working_set_bytes{pod=~\"knowledge-rag-.*\"} / container_spec_memory_limit_bytes{pod=~\"knowledge-rag-.*\"}) * 100",
            "legendFormat": "Memory % - {{pod}}"
          }
        ]
      }
    ]
  }
}
```

### 8.7 性能优化总结

#### 优化效果预期

**响应时间优化**
- API网关响应时间：从200ms降至50ms（P95）
- 向量搜索响应时间：从2s降至300ms（P95）
- 问答生成响应时间：从8s降至2s（P95）
- 文档上传处理时间：从30s降至5s（P95）

**吞吐量提升**
- 并发用户数：从100提升至1000+
- 查询处理能力：从10 QPS提升至100+ QPS
- 文档处理能力：从100/小时提升至10000+/小时
- 向量操作能力：从100 OPS提升至1000+ OPS

**资源利用率优化**
- CPU利用率：保持在70%以下
- 内存利用率：保持在80%以下
- 缓存命中率：提升至95%以上
- 数据库连接利用率：保持在80%以下

#### 性能优化检查清单

**应用层优化**
- [ ] 实施多层缓存策略
- [ ] 优化数据库查询和索引
- [ ] 配置连接池和异步处理
- [ ] 实现负载均衡和水平扩展
- [ ] 优化API响应格式和压缩

**数据层优化**
- [ ] PostgreSQL性能调优
- [ ] Weaviate向量索引优化
- [ ] Redis集群配置优化
- [ ] Neo4j图数据库调优
- [ ] 数据分片和分区策略

**基础设施优化**
- [ ] Kubernetes资源配置优化
- [ ] 存储I/O性能优化
- [ ] 网络延迟优化
- [ ] 容器镜像优化
- [ ] 监控和告警配置

**代码层优化**
- [ ] 异步编程模式
- [ ] 内存管理优化
- [ ] 算法复杂度优化
- [ ] 并发处理优化
- [ ] 错误处理和重试机制

---

---

## 9. 错误处理机制

本节详细阐述Knowledge RAG系统的统一错误处理和故障恢复机制，包括错误分类、异常处理策略、故障恢复方案和监控告警等关键技术。

### 9.1 错误分类和处理策略

#### 错误分类体系

**系统级错误**
- **基础设施故障**：服务器宕机、网络中断、存储故障
- **服务不可用**：数据库连接失败、外部API超时、内存溢出
- **资源耗尽**：CPU过载、内存不足、磁盘空间满
- **配置错误**：环境变量缺失、配置文件错误、权限问题

**业务级错误**
- **数据验证错误**：输入参数无效、数据格式错误、业务规则违反
- **权限错误**：认证失败、授权不足、访问被拒绝
- **业务逻辑错误**：工作流异常、状态转换错误、依赖服务失败
- **数据一致性错误**：并发冲突、事务回滚、数据不一致

**用户级错误**
- **请求错误**：参数缺失、格式错误、请求过大
- **操作错误**：重复操作、非法操作、超出限制
- **会话错误**：会话过期、令牌无效、状态丢失

#### 错误码标准化

```yaml
# 错误码规范
error_codes:
  # 系统级错误 (1000-1999)
  system_errors:
    1001: "服务不可用"
    1002: "数据库连接失败"
    1003: "外部服务超时"
    1004: "内存不足"
    1005: "磁盘空间不足"
    1006: "网络连接异常"
    1007: "配置错误"
    1008: "服务启动失败"
  
  # 业务级错误 (2000-2999)
  business_errors:
    2001: "数据验证失败"
    2002: "业务规则违反"
    2003: "工作流异常"
    2004: "数据不一致"
    2005: "并发冲突"
    2006: "依赖服务失败"
    2007: "状态转换错误"
    2008: "资源已存在"
  
  # 用户级错误 (3000-3999)
  user_errors:
    3001: "参数缺失"
    3002: "参数格式错误"
    3003: "认证失败"
    3004: "权限不足"
    3005: "会话过期"
    3006: "请求过大"
    3007: "操作频率过高"
    3008: "资源不存在"
  
  # 外部服务错误 (4000-4999)
  external_errors:
    4001: "LLM服务异常"
    4002: "向量数据库错误"
    4003: "文件存储服务异常"
    4004: "消息队列异常"
    4005: "缓存服务异常"
    4006: "第三方API异常"
    4007: "网络服务异常"
    4008: "认证服务异常"
```

### 9.2 统一异常处理框架

#### 异常处理中间件

```python
# error_handler.py
"""
Knowledge RAG系统统一异常处理框架
提供标准化的错误处理、日志记录和故障恢复功能
"""

import traceback
import logging
import json
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, asdict
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

class ErrorSeverity(Enum):
    """错误严重程度枚举"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    """错误类别枚举"""
    SYSTEM = "system"
    BUSINESS = "business"
    USER = "user"
    EXTERNAL = "external"

@dataclass
class ErrorContext:
    """错误上下文信息"""
    request_id: str
    user_id: Optional[str]
    service_name: str
    endpoint: str
    method: str
    timestamp: datetime
    client_ip: str
    user_agent: str
    additional_data: Dict[str, Any] = None

@dataclass
class StandardError:
    """标准化错误对象"""
    code: int
    message: str
    category: ErrorCategory
    severity: ErrorSeverity
    context: ErrorContext
    details: Optional[Dict[str, Any]] = None
    stack_trace: Optional[str] = None
    correlation_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "category": self.category.value,
                "severity": self.severity.value,
                "timestamp": self.context.timestamp.isoformat(),
                "request_id": self.context.request_id,
                "correlation_id": self.correlation_id,
                "details": self.details or {}
            }
        }
    
    def to_user_response(self) -> Dict[str, Any]:
        """转换为用户友好的响应格式"""
        # 过滤敏感信息，只返回用户需要的错误信息
        user_message = self.message
        if self.category == ErrorCategory.SYSTEM:
            user_message = "系统暂时不可用，请稍后重试"
        
        return {
            "success": False,
            "error": {
                "code": self.code,
                "message": user_message,
                "request_id": self.context.request_id
            }
        }

class KnowledgeRAGException(Exception):
    """Knowledge RAG系统自定义异常基类"""
    
    def __init__(self, code: int, message: str, category: ErrorCategory, 
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM, 
                 details: Optional[Dict[str, Any]] = None):
        self.code = code
        self.message = message
        self.category = category
        self.severity = severity
        self.details = details or {}
        super().__init__(self.message)

class SystemException(KnowledgeRAGException):
    """系统级异常"""
    def __init__(self, code: int, message: str, 
                 severity: ErrorSeverity = ErrorSeverity.HIGH, 
                 details: Optional[Dict[str, Any]] = None):
        super().__init__(code, message, ErrorCategory.SYSTEM, severity, details)

class BusinessException(KnowledgeRAGException):
    """业务级异常"""
    def __init__(self, code: int, message: str, 
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM, 
                 details: Optional[Dict[str, Any]] = None):
        super().__init__(code, message, ErrorCategory.BUSINESS, severity, details)

class UserException(KnowledgeRAGException):
    """用户级异常"""
    def __init__(self, code: int, message: str, 
                 severity: ErrorSeverity = ErrorSeverity.LOW, 
                 details: Optional[Dict[str, Any]] = None):
        super().__init__(code, message, ErrorCategory.USER, severity, details)

class ExternalException(KnowledgeRAGException):
    """外部服务异常"""
    def __init__(self, code: int, message: str, 
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM, 
                 details: Optional[Dict[str, Any]] = None):
        super().__init__(code, message, ErrorCategory.EXTERNAL, severity, details)

class ErrorHandler:
    """统一错误处理器"""
    
    def __init__(self, service_name: str, logger: logging.Logger):
        self.service_name = service_name
        self.logger = logger
        self.error_callbacks: Dict[ErrorCategory, List[Callable]] = {
            ErrorCategory.SYSTEM: [],
            ErrorCategory.BUSINESS: [],
            ErrorCategory.USER: [],
            ErrorCategory.EXTERNAL: []
        }
    
    def register_callback(self, category: ErrorCategory, callback: Callable):
        """注册错误处理回调函数"""
        self.error_callbacks[category].append(callback)
    
    def create_error_context(self, request: Request) -> ErrorContext:
        """创建错误上下文"""
        return ErrorContext(
            request_id=getattr(request.state, 'request_id', 'unknown'),
            user_id=getattr(request.state, 'user_id', None),
            service_name=self.service_name,
            endpoint=str(request.url.path),
            method=request.method,
            timestamp=datetime.utcnow(),
            client_ip=request.client.host if request.client else 'unknown',
            user_agent=request.headers.get('user-agent', 'unknown')
        )
    
    def handle_exception(self, exception: Exception, context: ErrorContext) -> StandardError:
        """处理异常并返回标准化错误对象"""
        if isinstance(exception, KnowledgeRAGException):
            # 处理自定义异常
            error = StandardError(
                code=exception.code,
                message=exception.message,
                category=exception.category,
                severity=exception.severity,
                context=context,
                details=exception.details,
                correlation_id=context.request_id
            )
        else:
            # 处理未知异常
            error = StandardError(
                code=1001,
                message="系统内部错误",
                category=ErrorCategory.SYSTEM,
                severity=ErrorSeverity.HIGH,
                context=context,
                stack_trace=traceback.format_exc(),
                correlation_id=context.request_id
            )
        
        # 记录错误日志
        self._log_error(error)
        
        # 执行错误处理回调
        self._execute_callbacks(error)
        
        return error
    
    def _log_error(self, error: StandardError):
        """记录错误日志"""
        log_data = {
            "error_code": error.code,
            "error_message": error.message,
            "category": error.category.value,
            "severity": error.severity.value,
            "service": error.context.service_name,
            "endpoint": error.context.endpoint,
            "method": error.context.method,
            "request_id": error.context.request_id,
            "user_id": error.context.user_id,
            "timestamp": error.context.timestamp.isoformat(),
            "details": error.details
        }
        
        if error.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            self.logger.error(f"Error occurred: {json.dumps(log_data, ensure_ascii=False)}")
            if error.stack_trace:
                self.logger.error(f"Stack trace: {error.stack_trace}")
        elif error.severity == ErrorSeverity.MEDIUM:
            self.logger.warning(f"Warning: {json.dumps(log_data, ensure_ascii=False)}")
        else:
            self.logger.info(f"Info: {json.dumps(log_data, ensure_ascii=False)}")
    
    def _execute_callbacks(self, error: StandardError):
        """执行错误处理回调函数"""
        callbacks = self.error_callbacks.get(error.category, [])
        for callback in callbacks:
            try:
                callback(error)
            except Exception as e:
                self.logger.error(f"Error callback execution failed: {e}")

class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """错误处理中间件"""
    
    def __init__(self, app, service_name: str, logger: logging.Logger):
        super().__init__(app)
        self.error_handler = ErrorHandler(service_name, logger)
    
    async def dispatch(self, request: Request, call_next):
        """处理请求并捕获异常"""
        try:
            response = await call_next(request)
            return response
        except Exception as exception:
            # 创建错误上下文
            context = self.error_handler.create_error_context(request)
            
            # 处理异常
            error = self.error_handler.handle_exception(exception, context)
            
            # 返回标准化错误响应
            status_code = self._get_http_status_code(error)
            return JSONResponse(
                status_code=status_code,
                content=error.to_user_response()
            )
    
    def _get_http_status_code(self, error: StandardError) -> int:
        """根据错误类型返回HTTP状态码"""
        if error.category == ErrorCategory.USER:
            if error.code in [3003, 3004]:  # 认证/授权错误
                return 401
            elif error.code in [3001, 3002, 3006]:  # 参数错误
                return 400
            elif error.code == 3008:  # 资源不存在
                return 404
            else:
                return 400
        elif error.category == ErrorCategory.BUSINESS:
            return 422  # 业务逻辑错误
        elif error.category in [ErrorCategory.SYSTEM, ErrorCategory.EXTERNAL]:
            return 500  # 服务器错误
        else:
            return 500
```

### 9.3 故障恢复机制

#### 重试策略

```python
# retry_mechanism.py
"""
故障恢复和重试机制
提供智能重试、熔断器和降级策略
"""

import asyncio
import random
import time
from typing import Any, Callable, Optional, Dict, List
from dataclasses import dataclass
from enum import Enum
import logging
from functools import wraps

class RetryStrategy(Enum):
    """重试策略枚举"""
    FIXED = "fixed"
    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    RANDOM = "random"

@dataclass
class RetryConfig:
    """重试配置"""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    backoff_multiplier: float = 2.0
    jitter: bool = True
    retryable_exceptions: List[type] = None

class CircuitBreakerState(Enum):
    """熔断器状态枚举"""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

@dataclass
class CircuitBreakerConfig:
    """熔断器配置"""
    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    expected_exception: type = Exception
    success_threshold: int = 3

class CircuitBreaker:
    """熔断器实现"""
    
    def __init__(self, config: CircuitBreakerConfig, name: str = "default"):
        self.config = config
        self.name = name
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.logger = logging.getLogger(f"circuit_breaker.{name}")
    
    def __call__(self, func: Callable) -> Callable:
        """装饰器模式使用熔断器"""
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await self.call(func, *args, **kwargs)
        return wrapper
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """执行函数调用并应用熔断器逻辑"""
        if self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitBreakerState.HALF_OPEN
                self.logger.info(f"Circuit breaker {self.name} moved to HALF_OPEN")
            else:
                raise SystemException(
                    code=1001,
                    message=f"Circuit breaker {self.name} is OPEN",
                    details={"circuit_breaker": self.name, "state": self.state.value}
                )
        
        try:
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            self._on_success()
            return result
        except self.config.expected_exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """判断是否应该尝试重置熔断器"""
        return (
            self.last_failure_time and 
            time.time() - self.last_failure_time >= self.config.recovery_timeout
        )
    
    def _on_success(self):
        """成功调用处理"""
        self.failure_count = 0
        
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitBreakerState.CLOSED
                self.success_count = 0
                self.logger.info(f"Circuit breaker {self.name} moved to CLOSED")
    
    def _on_failure(self):
        """失败调用处理"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.state = CircuitBreakerState.OPEN
            self.success_count = 0
            self.logger.warning(f"Circuit breaker {self.name} moved to OPEN (half-open failure)")
        elif self.failure_count >= self.config.failure_threshold:
            self.state = CircuitBreakerState.OPEN
            self.logger.warning(f"Circuit breaker {self.name} moved to OPEN (threshold reached)")

class RetryManager:
    """重试管理器"""
    
    def __init__(self, config: RetryConfig):
        self.config = config
        self.logger = logging.getLogger("retry_manager")
    
    def __call__(self, func: Callable) -> Callable:
        """装饰器模式使用重试机制"""
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await self.execute_with_retry(func, *args, **kwargs)
        return wrapper
    
    async def execute_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """执行函数并应用重试逻辑"""
        last_exception = None
        
        for attempt in range(self.config.max_attempts):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                # 检查是否为可重试异常
                if self.config.retryable_exceptions and not any(
                    isinstance(e, exc_type) for exc_type in self.config.retryable_exceptions
                ):
                    self.logger.info(f"Non-retryable exception: {type(e).__name__}")
                    raise e
                
                # 如果是最后一次尝试，直接抛出异常
                if attempt == self.config.max_attempts - 1:
                    self.logger.error(f"All retry attempts failed. Last exception: {e}")
                    raise e
                
                # 计算延迟时间
                delay = self._calculate_delay(attempt)
                self.logger.warning(
                    f"Attempt {attempt + 1} failed: {e}. Retrying in {delay:.2f} seconds..."
                )
                
                await asyncio.sleep(delay)
        
        # 理论上不会到达这里，但为了类型安全
        raise last_exception
    
    def _calculate_delay(self, attempt: int) -> float:
        """计算重试延迟时间"""
        if self.config.strategy == RetryStrategy.FIXED:
            delay = self.config.base_delay
        elif self.config.strategy == RetryStrategy.EXPONENTIAL:
            delay = self.config.base_delay * (self.config.backoff_multiplier ** attempt)
        elif self.config.strategy == RetryStrategy.LINEAR:
            delay = self.config.base_delay * (attempt + 1)
        elif self.config.strategy == RetryStrategy.RANDOM:
            delay = random.uniform(self.config.base_delay, self.config.max_delay)
        else:
            delay = self.config.base_delay
        
        # 应用最大延迟限制
        delay = min(delay, self.config.max_delay)
        
        # 添加抖动
        if self.config.jitter:
            jitter_range = delay * 0.1
            delay += random.uniform(-jitter_range, jitter_range)
        
        return max(0, delay)

class FallbackManager:
    """降级管理器"""
    
    def __init__(self):
        self.fallback_handlers: Dict[str, Callable] = {}
        self.logger = logging.getLogger("fallback_manager")
    
    def register_fallback(self, service_name: str, handler: Callable):
        """注册降级处理器"""
        self.fallback_handlers[service_name] = handler
        self.logger.info(f"Registered fallback handler for service: {service_name}")
    
    async def execute_with_fallback(self, service_name: str, primary_func: Callable, 
                                  *args, **kwargs) -> Any:
        """执行主要功能，失败时使用降级方案"""
        try:
            if asyncio.iscoroutinefunction(primary_func):
                return await primary_func(*args, **kwargs)
            else:
                return primary_func(*args, **kwargs)
        except Exception as e:
            self.logger.warning(f"Primary function failed for {service_name}: {e}")
            
            fallback_handler = self.fallback_handlers.get(service_name)
            if fallback_handler:
                self.logger.info(f"Executing fallback for service: {service_name}")
                try:
                    if asyncio.iscoroutinefunction(fallback_handler):
                        return await fallback_handler(*args, **kwargs)
                    else:
                        return fallback_handler(*args, **kwargs)
                except Exception as fallback_error:
                    self.logger.error(f"Fallback also failed for {service_name}: {fallback_error}")
                    raise e  # 抛出原始异常
            else:
                self.logger.error(f"No fallback handler registered for service: {service_name}")
                raise e
```

### 9.4 健康检查和监控

#### 服务健康检查

```python
# health_check.py
"""
服务健康检查和监控系统
提供全面的服务状态监控和健康评估功能
"""

import asyncio
import time
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import json
from datetime import datetime, timedelta

class HealthStatus(Enum):
    """健康状态枚举"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

@dataclass
class HealthCheckResult:
    """健康检查结果"""
    name: str
    status: HealthStatus
    message: str
    duration_ms: float
    timestamp: datetime
    details: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "duration_ms": self.duration_ms,
            "timestamp": self.timestamp.isoformat(),
            "details": self.details or {}
        }

@dataclass
class SystemHealthReport:
    """系统健康报告"""
    overall_status: HealthStatus
    timestamp: datetime
    checks: List[HealthCheckResult]
    summary: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "overall_status": self.overall_status.value,
            "timestamp": self.timestamp.isoformat(),
            "checks": [check.to_dict() for check in self.checks],
            "summary": self.summary
        }

class HealthChecker:
    """健康检查器基类"""
    
    def __init__(self, name: str, timeout: float = 5.0):
        self.name = name
        self.timeout = timeout
        self.logger = logging.getLogger(f"health_check.{name}")
    
    async def check(self) -> HealthCheckResult:
        """执行健康检查"""
        start_time = time.time()
        
        try:
            # 使用超时控制
            result = await asyncio.wait_for(
                self._perform_check(),
                timeout=self.timeout
            )
            
            duration_ms = (time.time() - start_time) * 1000
            
            return HealthCheckResult(
                name=self.name,
                status=result.get("status", HealthStatus.UNKNOWN),
                message=result.get("message", "Health check completed"),
                duration_ms=duration_ms,
                timestamp=datetime.utcnow(),
                details=result.get("details")
            )
        
        except asyncio.TimeoutError:
            duration_ms = (time.time() - start_time) * 1000
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Health check timed out after {self.timeout}s",
                duration_ms=duration_ms,
                timestamp=datetime.utcnow()
            )
        
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Health check failed: {str(e)}",
                duration_ms=duration_ms,
                timestamp=datetime.utcnow(),
                details={"error": str(e)}
            )
    
    async def _perform_check(self) -> Dict[str, Any]:
        """执行具体的健康检查逻辑（子类实现）"""
        raise NotImplementedError

class DatabaseHealthChecker(HealthChecker):
    """数据库健康检查器"""
    
    def __init__(self, name: str, database_pool, timeout: float = 5.0):
        super().__init__(name, timeout)
        self.database_pool = database_pool
    
    async def _perform_check(self) -> Dict[str, Any]:
        """检查数据库连接和基本查询"""
        try:
            async with self.database_pool.acquire() as conn:
                # 执行简单查询测试连接
                result = await conn.fetchval("SELECT 1")
                
                if result == 1:
                    # 获取连接池统计信息
                    pool_stats = await self.database_pool.get_pool_stats()
                    
                    return {
                        "status": HealthStatus.HEALTHY,
                        "message": "Database connection is healthy",
                        "details": {
                            "pool_size": pool_stats.get("size", 0),
                            "idle_connections": pool_stats.get("idle_size", 0)
                        }
                    }
                else:
                    return {
                        "status": HealthStatus.UNHEALTHY,
                        "message": "Database query returned unexpected result"
                    }
        
        except Exception as e:
            return {
                "status": HealthStatus.UNHEALTHY,
                "message": f"Database connection failed: {str(e)}"
            }

class RedisHealthChecker(HealthChecker):
    """Redis健康检查器"""
    
    def __init__(self, name: str, redis_client, timeout: float = 5.0):
        super().__init__(name, timeout)
        self.redis_client = redis_client
    
    async def _perform_check(self) -> Dict[str, Any]:
        """检查Redis连接和基本操作"""
        try:
            # 执行PING命令
            pong = await self.redis_client.ping()
            
            if pong:
                # 获取Redis信息
                info = await self.redis_client.info()
                
                return {
                    "status": HealthStatus.HEALTHY,
                    "message": "Redis connection is healthy",
                    "details": {
                        "connected_clients": info.get("connected_clients", 0),
                        "used_memory_human": info.get("used_memory_human", "unknown")
                    }
                }
            else:
                return {
                    "status": HealthStatus.UNHEALTHY,
                    "message": "Redis PING failed"
                }
        
        except Exception as e:
            return {
                "status": HealthStatus.UNHEALTHY,
                "message": f"Redis connection failed: {str(e)}"
            }

class ExternalServiceHealthChecker(HealthChecker):
    """外部服务健康检查器"""
    
    def __init__(self, name: str, service_url: str, timeout: float = 10.0):
        super().__init__(name, timeout)
        self.service_url = service_url
    
    async def _perform_check(self) -> Dict[str, Any]:
        """检查外部服务可用性"""
        import aiohttp
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.get(f"{self.service_url}/health") as response:
                    if response.status == 200:
                        return {
                            "status": HealthStatus.HEALTHY,
                            "message": "External service is healthy",
                            "details": {
                                "status_code": response.status,
                                "response_time_ms": response.headers.get("X-Response-Time")
                            }
                        }
                    else:
                        return {
                            "status": HealthStatus.DEGRADED,
                            "message": f"External service returned status {response.status}",
                            "details": {"status_code": response.status}
                        }
        
        except Exception as e:
            return {
                "status": HealthStatus.UNHEALTHY,
                "message": f"External service check failed: {str(e)}"
            }

class HealthMonitor:
    """健康监控管理器"""
    
    def __init__(self):
        self.checkers: List[HealthChecker] = []
        self.logger = logging.getLogger("health_monitor")
        self.last_report: Optional[SystemHealthReport] = None
    
    def register_checker(self, checker: HealthChecker):
        """注册健康检查器"""
        self.checkers.append(checker)
        self.logger.info(f"Registered health checker: {checker.name}")
    
    async def check_all(self) -> SystemHealthReport:
        """执行所有健康检查"""
        self.logger.info("Starting comprehensive health check")
        
        # 并发执行所有健康检查
        check_tasks = [checker.check() for checker in self.checkers]
        results = await asyncio.gather(*check_tasks, return_exceptions=True)
        
        # 处理结果
        check_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # 处理检查器本身的异常
                check_results.append(HealthCheckResult(
                    name=self.checkers[i].name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Health checker failed: {str(result)}",
                    duration_ms=0,
                    timestamp=datetime.utcnow()
                ))
            else:
                check_results.append(result)
        
        # 计算整体健康状态
        overall_status = self._calculate_overall_status(check_results)
        
        # 生成摘要
        summary = self._generate_summary(check_results)
        
        # 创建健康报告
        report = SystemHealthReport(
            overall_status=overall_status,
            timestamp=datetime.utcnow(),
            checks=check_results,
            summary=summary
        )
        
        self.last_report = report
        self.logger.info(f"Health check completed. Overall status: {overall_status.value}")
        
        return report
    
    def _calculate_overall_status(self, results: List[HealthCheckResult]) -> HealthStatus:
        """计算整体健康状态"""
        if not results:
            return HealthStatus.UNKNOWN
        
        status_counts = {
            HealthStatus.HEALTHY: 0,
            HealthStatus.DEGRADED: 0,
            HealthStatus.UNHEALTHY: 0,
            HealthStatus.UNKNOWN: 0
        }
        
        for result in results:
            status_counts[result.status] += 1
        
        total_checks = len(results)
        
        # 如果有任何不健康的服务，整体状态为不健康
        if status_counts[HealthStatus.UNHEALTHY] > 0:
            return HealthStatus.UNHEALTHY
        
        # 如果有降级服务，整体状态为降级
        if status_counts[HealthStatus.DEGRADED] > 0:
            return HealthStatus.DEGRADED
        
        # 如果所有服务都健康，整体状态为健康
        if status_counts[HealthStatus.HEALTHY] == total_checks:
            return HealthStatus.HEALTHY
        
        # 其他情况为未知
        return HealthStatus.UNKNOWN
    
    def _generate_summary(self, results: List[HealthCheckResult]) -> Dict[str, Any]:
        """生成健康检查摘要"""
        total_checks = len(results)
        status_counts = {
            "healthy": sum(1 for r in results if r.status == HealthStatus.HEALTHY),
            "degraded": sum(1 for r in results if r.status == HealthStatus.DEGRADED),
            "unhealthy": sum(1 for r in results if r.status == HealthStatus.UNHEALTHY),
            "unknown": sum(1 for r in results if r.status == HealthStatus.UNKNOWN)
        }
        
        avg_duration = sum(r.duration_ms for r in results) / total_checks if total_checks > 0 else 0
        
        return {
            "total_checks": total_checks,
            "status_distribution": status_counts,
            "average_duration_ms": round(avg_duration, 2),
            "failed_checks": [r.name for r in results if r.status == HealthStatus.UNHEALTHY]
        }
    
    def get_last_report(self) -> Optional[SystemHealthReport]:
        """获取最后一次健康检查报告"""
        return self.last_report
```

### 9.5 告警和通知机制

#### 告警配置

```yaml
# alerting-rules.yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: knowledge-rag-alerts
  namespace: knowledge-rag-prod
  labels:
    app: knowledge-rag
    role: alert-rules
spec:
  groups:
  - name: knowledge-rag.system
    rules:
    # 系统级告警
    - alert: ServiceDown
      expr: up{job=~"knowledge-rag-.*"} == 0
      for: 1m
      labels:
        severity: critical
        category: system
      annotations:
        summary: "Knowledge RAG service is down"
        description: "Service {{ $labels.job }} has been down for more than 1 minute."
    
    - alert: HighErrorRate
      expr: |
        (
          rate(http_requests_total{job=~"knowledge-rag-.*",code=~"5.."}[5m]) /
          rate(http_requests_total{job=~"knowledge-rag-.*"}[5m])
        ) > 0.1
      for: 5m
      labels:
        severity: warning
        category: business
      annotations:
        summary: "High error rate detected"
        description: "Error rate is {{ $value | humanizePercentage }} for service {{ $labels.job }}."
    
    - alert: HighResponseTime
      expr: |
        histogram_quantile(0.95, 
          rate(http_request_duration_seconds_bucket{job=~"knowledge-rag-.*"}[5m])
        ) > 5
      for: 10m
      labels:
        severity: warning
        category: performance
      annotations:
        summary: "High response time detected"
        description: "95th percentile response time is {{ $value }}s for service {{ $labels.job }}."
    
    - alert: DatabaseConnectionFailure
      expr: pg_up == 0
      for: 1m
      labels:
        severity: critical
        category: system
      annotations:
        summary: "Database connection failure"
        description: "PostgreSQL database is not accessible."
    
    - alert: RedisConnectionFailure
      expr: redis_up == 0
      for: 1m
      labels:
        severity: high
        category: system
      annotations:
        summary: "Redis connection failure"
        description: "Redis cache is not accessible."
    
    - alert: HighMemoryUsage
      expr: |
        (
          container_memory_working_set_bytes{pod=~"knowledge-rag-.*"} /
          container_spec_memory_limit_bytes{pod=~"knowledge-rag-.*"}
        ) > 0.9
      for: 5m
      labels:
        severity: warning
        category: resource
      annotations:
        summary: "High memory usage"
        description: "Memory usage is {{ $value | humanizePercentage }} for pod {{ $labels.pod }}."
    
    - alert: HighCPUUsage
      expr: |
        rate(container_cpu_usage_seconds_total{pod=~"knowledge-rag-.*"}[5m]) > 0.8
      for: 10m
      labels:
        severity: warning
        category: resource
      annotations:
        summary: "High CPU usage"
        description: "CPU usage is {{ $value | humanizePercentage }} for pod {{ $labels.pod }}."
    
    - alert: LowCacheHitRate
      expr: |
        (
          rate(redis_keyspace_hits_total[5m]) /
          (rate(redis_keyspace_hits_total[5m]) + rate(redis_keyspace_misses_total[5m]))
        ) < 0.8
      for: 15m
      labels:
        severity: warning
        category: performance
      annotations:
        summary: "Low cache hit rate"
        description: "Cache hit rate is {{ $value | humanizePercentage }}."
    
    - alert: VectorSearchSlowdown
      expr: |
        histogram_quantile(0.95,
          rate(weaviate_query_duration_seconds_bucket[5m])
        ) > 2
      for: 10m
      labels:
        severity: warning
        category: performance
      annotations:
        summary: "Vector search performance degradation"
        description: "95th percentile vector search time is {{ $value }}s."
    
    - alert: DiskSpaceRunningOut
      expr: |
        (
          node_filesystem_avail_bytes{mountpoint="/"} /
          node_filesystem_size_bytes{mountpoint="/"}
        ) < 0.1
      for: 5m
      labels:
        severity: critical
        category: resource
      annotations:
        summary: "Disk space running out"
        description: "Available disk space is {{ $value | humanizePercentage }}."
```

### 9.6 错误处理最佳实践

#### 错误处理检查清单

**设计原则**
- [ ] 实施统一的错误分类和编码标准
- [ ] 建立标准化的异常处理框架
- [ ] 设计合理的重试和熔断机制
- [ ] 实现全面的健康检查和监控
- [ ] 配置及时的告警和通知机制

**实现要求**
- [ ] 所有API都返回标准化的错误响应格式
- [ ] 关键服务都配置了熔断器保护
- [ ] 外部依赖都实现了重试和降级策略
- [ ] 系统组件都有健康检查端点
- [ ] 错误日志包含足够的上下文信息

**监控和告警**
- [ ] 配置了系统级、业务级和性能级告警规则
- [ ] 建立了多渠道的告警通知机制
- [ ] 实现了告警的自动升级和降级
- [ ] 配置了告警的抑制和静默规则
- [ ] 建立了故障处理的标准操作程序

**故障恢复**
- [ ] 关键数据都有备份和恢复机制
- [ ] 服务支持优雅启动和关闭
- [ ] 实现了自动故障转移和负载均衡
- [ ] 配置了数据一致性检查和修复
- [ ] 建立了灾难恢复计划和演练机制

---

## 开发工作流程

### 概述

Knowledge RAG系统采用现代化的DevOps开发工作流程，确保代码质量、快速交付和系统稳定性。本章节详细描述了从代码开发到生产部署的完整流程。

### 开发环境设置

#### 本地开发环境

```bash
# 环境要求
- Python 3.11+
- Node.js 18+
- Docker Desktop
- Kubernetes (minikube/kind)
- Git

# 项目初始化
git clone <repository-url>
cd knowledge-rag

# 后端环境设置
cd backend
curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync --prerelease=allow

# 数据库初始化
docker-compose up -d postgres redis
alembic upgrade head

# 启动开发服务器
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### 开发工具配置

```yaml
# .vscode/settings.json
{
  "python.defaultInterpreterPath": "./backend/venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",
  "python.testing.pytestEnabled": true,
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  }
}
```

### Git工作流程

#### 分支策略

```
main (生产分支)
├── develop (开发分支)
│   ├── feature/user-auth (功能分支)
│   ├── feature/document-parsing (功能分支)
│   └── feature/rag-engine (功能分支)
├── release/v1.0.0 (发布分支)
└── hotfix/critical-bug (热修复分支)
```

#### 提交规范

```bash
# 提交消息格式
<type>(<scope>): <subject>

<body>

<footer>

# 示例
feat(auth): add JWT token validation middleware

- Implement JWT token validation
- Add token expiration check
- Handle invalid token scenarios

Closes #123
```

#### 代码审查流程

```yaml
# .github/pull_request_template.md
## 变更描述
- [ ] 功能实现
- [ ] Bug修复
- [ ] 性能优化
- [ ] 文档更新

## 测试清单
- [ ] 单元测试通过
- [ ] 集成测试通过
- [ ] 手动测试完成
- [ ] 性能测试通过

## 部署清单
- [ ] 数据库迁移脚本
- [ ] 配置文件更新
- [ ] 环境变量变更
- [ ] 依赖包更新
```

### 代码质量保证

#### 静态代码分析

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: ["--profile", "black"]

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: ["--max-line-length=88"]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.3.0
    hooks:
      - id: mypy
        additional_dependencies: [types-requests]
```

#### 代码覆盖率要求

```python
# pytest.ini
[tool:pytest]
addopts = 
    --cov=src
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=80
    --strict-markers
    --disable-warnings

markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    slow: Slow running tests
```

### 测试策略

#### 测试金字塔

```
        E2E Tests (10%)
       /              \
    Integration Tests (20%)
   /                      \
  Unit Tests (70%)
```

#### 单元测试

```python
# tests/unit/test_document_service.py
import pytest
from unittest.mock import Mock, patch
from src.services.document_service import DocumentService

class TestDocumentService:
    """文档服务单元测试"""
    
    @pytest.fixture
    def document_service(self):
        """创建文档服务实例"""
        return DocumentService()
    
    @patch('src.services.document_service.extract_text')
    def test_parse_pdf_document(self, mock_extract, document_service):
        """测试PDF文档解析"""
        # Arrange
        mock_extract.return_value = "Test content"
        file_path = "/path/to/test.pdf"
        
        # Act
        result = document_service.parse_document(file_path)
        
        # Assert
        assert result.content == "Test content"
        assert result.file_type == "pdf"
        mock_extract.assert_called_once_with(file_path)
```

#### 集成测试

```python
# tests/integration/test_api_endpoints.py
import pytest
from fastapi.testclient import TestClient
from src.main import app

class TestDocumentAPI:
    """文档API集成测试"""
    
    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        return TestClient(app)
    
    def test_upload_document_success(self, client):
        """测试文档上传成功场景"""
        with open("tests/fixtures/sample.pdf", "rb") as f:
            response = client.post(
                "/api/v1/documents/upload",
                files={"file": ("sample.pdf", f, "application/pdf")}
            )
        
        assert response.status_code == 201
        assert "document_id" in response.json()
```

#### E2E测试

```python
# tests/e2e/test_rag_workflow.py
import pytest
from playwright.sync_api import sync_playwright

class TestRAGWorkflow:
    """RAG工作流程端到端测试"""
    
    def test_complete_rag_workflow(self):
        """测试完整的RAG工作流程"""
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            
            # 1. 上传文档
            page.goto("http://localhost:3000/upload")
            page.set_input_files("input[type=file]", "tests/fixtures/sample.pdf")
            page.click("button[type=submit]")
            
            # 2. 等待处理完成
            page.wait_for_selector(".upload-success")
            
            # 3. 执行查询
            page.goto("http://localhost:3000/chat")
            page.fill("textarea[name=question]", "What is the main topic?")
            page.click("button[type=submit]")
            
            # 4. 验证结果
            response = page.wait_for_selector(".chat-response")
            assert len(response.text_content()) > 0
            
            browser.close()
```

### CI/CD流水线

#### GitHub Actions配置

```yaml
# .github/workflows/ci.yml
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        curl -LsSf https://astral.sh/uv/install.sh | sh
        cd backend
        uv sync --prerelease=allow
    
    - name: Run linting
      run: |
        flake8 backend/src
        black --check backend/src
        isort --check-only backend/src
    
    - name: Run type checking
      run: mypy backend/src
    
    - name: Run tests
      run: |
        cd backend
        pytest tests/ -v --cov=src --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./backend/coverage.xml

  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Build Docker image
      run: |
        docker build -t knowledge-rag:${{ github.sha }} .
        docker tag knowledge-rag:${{ github.sha }} knowledge-rag:latest
    
    - name: Push to registry
      run: |
        echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
        docker push knowledge-rag:${{ github.sha }}
        docker push knowledge-rag:latest

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - name: Deploy to staging
      run: |
        kubectl set image deployment/knowledge-rag knowledge-rag=knowledge-rag:${{ github.sha }}
        kubectl rollout status deployment/knowledge-rag
```

### 发布管理

#### 版本控制策略

```bash
# 语义化版本控制
MAJOR.MINOR.PATCH

# 示例
v1.0.0 - 初始发布
v1.0.1 - 补丁版本（Bug修复）
v1.1.0 - 次要版本（新功能）
v2.0.0 - 主要版本（破坏性变更）
```

#### 发布流程

```yaml
# .github/workflows/release.yml
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  release:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Create Release
      uses: actions/create-release@v1
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      with:
        tag_name: ${{ github.ref }}
        release_name: Release ${{ github.ref }}
        draft: false
        prerelease: false
    
    - name: Deploy to production
      run: |
        helm upgrade --install knowledge-rag ./helm/knowledge-rag \
          --namespace production \
          --set image.tag=${{ github.ref_name }} \
          --set environment=production
```

### 环境管理

#### 环境配置

```yaml
# environments/development.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: development
data:
  DATABASE_URL: "postgresql://user:pass@postgres:5432/knowledge_rag_dev"
  REDIS_URL: "redis://redis:6379/0"
  LOG_LEVEL: "DEBUG"
  ENVIRONMENT: "development"

---
# environments/staging.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: staging
data:
  DATABASE_URL: "postgresql://user:pass@postgres:5432/knowledge_rag_staging"
  REDIS_URL: "redis://redis:6379/1"
  LOG_LEVEL: "INFO"
  ENVIRONMENT: "staging"

---
# environments/production.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: production
data:
  DATABASE_URL: "postgresql://user:pass@postgres:5432/knowledge_rag_prod"
  REDIS_URL: "redis://redis:6379/2"
  LOG_LEVEL: "WARNING"
  ENVIRONMENT: "production"
```

### 数据库迁移管理

#### Alembic配置

```python
# alembic/versions/001_initial_schema.py
"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2024-01-01 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    """创建初始数据库架构"""
    op.create_table(
        'documents',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('file_path', sa.String(500), nullable=False),
        sa.Column('file_type', sa.String(50), nullable=False),
        sa.Column('file_size', sa.BigInteger(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_index('idx_documents_created_at', 'documents', ['created_at'])
    op.create_index('idx_documents_file_type', 'documents', ['file_type'])

def downgrade():
    """回滚数据库架构"""
    op.drop_index('idx_documents_file_type')
    op.drop_index('idx_documents_created_at')
    op.drop_table('documents')
```

#### 迁移脚本

```bash
#!/bin/bash
# scripts/migrate.sh

set -e

ENVIRONMENT=${1:-development}

echo "Running database migrations for $ENVIRONMENT environment..."

# 设置环境变量
export ENVIRONMENT=$ENVIRONMENT

# 运行迁移
alembic upgrade head

echo "Database migration completed successfully!"
```

### 监控和日志

#### 应用监控

```python
# src/monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge
import time
from functools import wraps

# 定义监控指标
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

ACTIVE_CONNECTIONS = Gauge(
    'active_connections',
    'Active database connections'
)

def monitor_endpoint(func):
    """端点监控装饰器"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = await func(*args, **kwargs)
            REQUEST_COUNT.labels(
                method='POST',
                endpoint=func.__name__,
                status='success'
            ).inc()
            return result
        except Exception as e:
            REQUEST_COUNT.labels(
                method='POST',
                endpoint=func.__name__,
                status='error'
            ).inc()
            raise
        finally:
            REQUEST_DURATION.labels(
                method='POST',
                endpoint=func.__name__
            ).observe(time.time() - start_time)
    
    return wrapper
```

### 开发工作流程最佳实践

#### 代码开发规范

1. **功能开发流程**
   - 从develop分支创建feature分支
   - 遵循TDD（测试驱动开发）原则
   - 编写单元测试和集成测试
   - 代码审查通过后合并到develop

2. **Bug修复流程**
   - 创建bug复现测试用例
   - 修复bug并确保测试通过
   - 更新相关文档
   - 通过代码审查后合并

3. **发布准备流程**
   - 从develop创建release分支
   - 执行完整测试套件
   - 更新版本号和变更日志
   - 部署到staging环境验证
   - 合并到main分支并打标签

#### 质量保证检查清单

- [ ] **代码质量**
  - [ ] 静态代码分析通过
  - [ ] 代码覆盖率达到80%以上
  - [ ] 无安全漏洞
  - [ ] 性能测试通过

- [ ] **测试完整性**
  - [ ] 单元测试覆盖核心逻辑
  - [ ] 集成测试覆盖API端点
  - [ ] E2E测试覆盖关键用户流程
  - [ ] 负载测试验证性能指标

- [ ] **部署准备**
  - [ ] 数据库迁移脚本准备
  - [ ] 配置文件更新
  - [ ] 监控告警配置
  - [ ] 回滚计划制定

- [ ] **文档更新**
  - [ ] API文档更新
  - [ ] 部署文档更新
  - [ ] 用户手册更新
  - [ ] 变更日志记录

---

## 多环境管理

### 概述

Knowledge RAG系统采用多环境部署策略，确保开发、测试和生产环境的隔离性和一致性。本章节详细描述了多环境配置管理、部署策略和环境间的数据同步机制。

### 环境架构设计

#### 环境分层策略

```
生产环境 (Production)
    ↑ 发布部署
预生产环境 (Staging)
    ↑ 集成测试
测试环境 (Testing)
    ↑ 功能测试
开发环境 (Development)
    ↑ 日常开发
本地环境 (Local)
```

#### 环境特性对比

| 环境类型 | 用途 | 数据来源 | 访问权限 | 监控级别 | 备份策略 |
|---------|------|----------|----------|----------|----------|
| Local | 本地开发 | 模拟数据 | 开发者 | 基础 | 无 |
| Development | 功能开发 | 测试数据 | 开发团队 | 标准 | 每日 |
| Testing | 集成测试 | 测试数据 | QA团队 | 标准 | 每日 |
| Staging | 预生产验证 | 生产副本 | 核心团队 | 完整 | 实时 |
| Production | 生产服务 | 真实数据 | 运维团队 | 完整 | 实时+归档 |

### 环境配置管理

#### Kubernetes命名空间设计

```yaml
# namespaces/environments.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: knowledge-rag-local
  labels:
    environment: local
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
  name: knowledge-rag-test
  labels:
    environment: testing
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
  name: knowledge-rag-prod
  labels:
    environment: production
    project: knowledge-rag
```

#### 环境配置文件

```yaml
# config/environments/local.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: knowledge-rag-local
data:
  # 应用配置
  APP_NAME: "Knowledge RAG Local"
  APP_VERSION: "dev"
  DEBUG: "true"
  LOG_LEVEL: "DEBUG"
  
  # 数据库配置
  DATABASE_URL: "postgresql://postgres:password@localhost:5432/knowledge_rag_local"
  DATABASE_POOL_SIZE: "5"
  DATABASE_MAX_OVERFLOW: "10"
  
  # Redis配置
  REDIS_URL: "redis://localhost:6379/0"
  REDIS_MAX_CONNECTIONS: "10"
  
  # 向量数据库配置
  WEAVIATE_URL: "http://localhost:8080"
  WEAVIATE_API_KEY: "local-dev-key"
  
  # LLM配置
  OPENAI_API_KEY: "sk-local-test-key"
  OPENAI_MODEL: "gpt-3.5-turbo"
  OPENAI_MAX_TOKENS: "1000"
  
  # 文件存储配置
  STORAGE_TYPE: "local"
  STORAGE_PATH: "/tmp/knowledge-rag/uploads"
  
  # 监控配置
  METRICS_ENABLED: "false"
  TRACING_ENABLED: "false"

---
# config/environments/development.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: knowledge-rag-dev
data:
  # 应用配置
  APP_NAME: "Knowledge RAG Development"
  APP_VERSION: "dev"
  DEBUG: "true"
  LOG_LEVEL: "DEBUG"
  
  # 数据库配置
  DATABASE_URL: "postgresql://dev_user:dev_pass@postgres-dev:5432/knowledge_rag_dev"
  DATABASE_POOL_SIZE: "10"
  DATABASE_MAX_OVERFLOW: "20"
  
  # Redis配置
  REDIS_URL: "redis://redis-dev:6379/0"
  REDIS_MAX_CONNECTIONS: "20"
  
  # 向量数据库配置
  WEAVIATE_URL: "http://weaviate-dev:8080"
  WEAVIATE_API_KEY: "dev-environment-key"
  
  # LLM配置
  OPENAI_API_KEY: "sk-dev-test-key"
  OPENAI_MODEL: "gpt-3.5-turbo"
  OPENAI_MAX_TOKENS: "2000"
  
  # 文件存储配置
  STORAGE_TYPE: "minio"
  MINIO_ENDPOINT: "minio-dev:9000"
  MINIO_BUCKET: "knowledge-rag-dev"
  
  # 监控配置
  METRICS_ENABLED: "true"
  TRACING_ENABLED: "true"
  JAEGER_ENDPOINT: "http://jaeger-dev:14268"

---
# config/environments/testing.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: knowledge-rag-test
data:
  # 应用配置
  APP_NAME: "Knowledge RAG Testing"
  APP_VERSION: "test"
  DEBUG: "false"
  LOG_LEVEL: "INFO"
  
  # 数据库配置
  DATABASE_URL: "postgresql://test_user:test_pass@postgres-test:5432/knowledge_rag_test"
  DATABASE_POOL_SIZE: "15"
  DATABASE_MAX_OVERFLOW: "30"
  
  # Redis配置
  REDIS_URL: "redis://redis-test:6379/0"
  REDIS_MAX_CONNECTIONS: "30"
  
  # 向量数据库配置
  WEAVIATE_URL: "http://weaviate-test:8080"
  WEAVIATE_API_KEY: "test-environment-key"
  
  # LLM配置
  OPENAI_API_KEY: "sk-test-environment-key"
  OPENAI_MODEL: "gpt-4"
  OPENAI_MAX_TOKENS: "3000"
  
  # 文件存储配置
  STORAGE_TYPE: "minio"
  MINIO_ENDPOINT: "minio-test:9000"
  MINIO_BUCKET: "knowledge-rag-test"
  
  # 监控配置
  METRICS_ENABLED: "true"
  TRACING_ENABLED: "true"
  JAEGER_ENDPOINT: "http://jaeger-test:14268"

---
# config/environments/staging.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: knowledge-rag-staging
data:
  # 应用配置
  APP_NAME: "Knowledge RAG Staging"
  APP_VERSION: "staging"
  DEBUG: "false"
  LOG_LEVEL: "INFO"
  
  # 数据库配置
  DATABASE_URL: "postgresql://staging_user:staging_pass@postgres-staging:5432/knowledge_rag_staging"
  DATABASE_POOL_SIZE: "20"
  DATABASE_MAX_OVERFLOW: "40"
  
  # Redis配置
  REDIS_URL: "redis://redis-staging:6379/0"
  REDIS_MAX_CONNECTIONS: "40"
  
  # 向量数据库配置
  WEAVIATE_URL: "http://weaviate-staging:8080"
  WEAVIATE_API_KEY: "staging-environment-key"
  
  # LLM配置
  OPENAI_API_KEY: "sk-staging-environment-key"
  OPENAI_MODEL: "gpt-4"
  OPENAI_MAX_TOKENS: "4000"
  
  # 文件存储配置
  STORAGE_TYPE: "s3"
  AWS_S3_BUCKET: "knowledge-rag-staging"
  AWS_REGION: "us-west-2"
  
  # 监控配置
  METRICS_ENABLED: "true"
  TRACING_ENABLED: "true"
  JAEGER_ENDPOINT: "http://jaeger-staging:14268"

---
# config/environments/production.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: knowledge-rag-prod
data:
  # 应用配置
  APP_NAME: "Knowledge RAG Production"
  APP_VERSION: "v1.0.0"
  DEBUG: "false"
  LOG_LEVEL: "WARNING"
  
  # 数据库配置
  DATABASE_URL: "postgresql://prod_user:prod_pass@postgres-prod:5432/knowledge_rag_prod"
  DATABASE_POOL_SIZE: "50"
  DATABASE_MAX_OVERFLOW: "100"
  
  # Redis配置
  REDIS_URL: "redis://redis-prod:6379/0"
  REDIS_MAX_CONNECTIONS: "100"
  
  # 向量数据库配置
  WEAVIATE_URL: "http://weaviate-prod:8080"
  WEAVIATE_API_KEY: "production-environment-key"
  
  # LLM配置
  OPENAI_API_KEY: "sk-production-environment-key"
  OPENAI_MODEL: "gpt-4"
  OPENAI_MAX_TOKENS: "4000"
  
  # 文件存储配置
  STORAGE_TYPE: "s3"
  AWS_S3_BUCKET: "knowledge-rag-production"
  AWS_REGION: "us-west-2"
  
  # 监控配置
  METRICS_ENABLED: "true"
  TRACING_ENABLED: "true"
  JAEGER_ENDPOINT: "http://jaeger-prod:14268"
```

### 密钥管理

#### Kubernetes Secrets

```yaml
# secrets/database-secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: database-secrets
  namespace: knowledge-rag-dev
type: Opaque
data:
  username: ZGV2X3VzZXI=  # base64 encoded
  password: ZGV2X3Bhc3M=  # base64 encoded

---
apiVersion: v1
kind: Secret
metadata:
  name: database-secrets
  namespace: knowledge-rag-prod
type: Opaque
data:
  username: cHJvZF91c2Vy  # base64 encoded
  password: cHJvZF9wYXNz  # base64 encoded

---
# secrets/api-keys.yaml
apiVersion: v1
kind: Secret
metadata:
  name: api-keys
  namespace: knowledge-rag-dev
type: Opaque
data:
  openai-api-key: c2stZGV2LXRlc3Qta2V5  # base64 encoded
  weaviate-api-key: ZGV2LWVudmlyb25tZW50LWtleQ==  # base64 encoded

---
apiVersion: v1
kind: Secret
metadata:
  name: api-keys
  namespace: knowledge-rag-prod
type: Opaque
data:
  openai-api-key: c2stcHJvZHVjdGlvbi1lbnZpcm9ubWVudC1rZXk=  # base64 encoded
  weaviate-api-key: cHJvZHVjdGlvbi1lbnZpcm9ubWVudC1rZXk=  # base64 encoded
```

#### 外部密钥管理集成

```yaml
# external-secrets/vault-integration.yaml
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: vault-backend
  namespace: knowledge-rag-prod
spec:
  provider:
    vault:
      server: "https://vault.company.com"
      path: "secret"
      version: "v2"
      auth:
        kubernetes:
          mountPath: "kubernetes"
          role: "knowledge-rag-prod"

---
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: database-credentials
  namespace: knowledge-rag-prod
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: vault-backend
    kind: SecretStore
  target:
    name: database-secrets
    creationPolicy: Owner
  data:
  - secretKey: username
    remoteRef:
      key: knowledge-rag/database
      property: username
  - secretKey: password
    remoteRef:
      key: knowledge-rag/database
      property: password
```

### 部署配置

#### Helm Values文件

```yaml
# helm/values-dev.yaml
replicaCount: 1

image:
  repository: knowledge-rag
  tag: "dev"
  pullPolicy: Always

service:
  type: ClusterIP
  port: 8000

ingress:
  enabled: true
  className: "nginx"
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
  hosts:
    - host: knowledge-rag-dev.company.com
      paths:
        - path: /
          pathType: Prefix

resources:
  limits:
    cpu: 500m
    memory: 1Gi
  requests:
    cpu: 250m
    memory: 512Mi

autoscaling:
  enabled: false

environment: development

database:
  host: postgres-dev
  port: 5432
  name: knowledge_rag_dev

redis:
  host: redis-dev
  port: 6379

weaviate:
  host: weaviate-dev
  port: 8080

monitoring:
  enabled: true
  serviceMonitor:
    enabled: true

---
# helm/values-staging.yaml
replicaCount: 2

image:
  repository: knowledge-rag
  tag: "staging"
  pullPolicy: Always

service:
  type: ClusterIP
  port: 8000

ingress:
  enabled: true
  className: "nginx"
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
  hosts:
    - host: knowledge-rag-staging.company.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: knowledge-rag-staging-tls
      hosts:
        - knowledge-rag-staging.company.com

resources:
  limits:
    cpu: 1000m
    memory: 2Gi
  requests:
    cpu: 500m
    memory: 1Gi

autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 5
  targetCPUUtilizationPercentage: 70

environment: staging

database:
  host: postgres-staging
  port: 5432
  name: knowledge_rag_staging

redis:
  host: redis-staging
  port: 6379

weaviate:
  host: weaviate-staging
  port: 8080

monitoring:
  enabled: true
  serviceMonitor:
    enabled: true

---
# helm/values-prod.yaml
replicaCount: 3

image:
  repository: knowledge-rag
  tag: "v1.0.0"
  pullPolicy: IfNotPresent

service:
  type: ClusterIP
  port: 8000

ingress:
  enabled: true
  className: "nginx"
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/rate-limit: "100"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
  hosts:
    - host: api.knowledge-rag.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: knowledge-rag-prod-tls
      hosts:
        - api.knowledge-rag.com

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
  targetCPUUtilizationPercentage: 60
  targetMemoryUtilizationPercentage: 70

environment: production

database:
  host: postgres-prod
  port: 5432
  name: knowledge_rag_prod

redis:
  host: redis-prod
  port: 6379

weaviate:
  host: weaviate-prod
  port: 8080

monitoring:
  enabled: true
  serviceMonitor:
    enabled: true

security:
  podSecurityContext:
    runAsNonRoot: true
    runAsUser: 1000
    fsGroup: 2000
  securityContext:
    allowPrivilegeEscalation: false
    readOnlyRootFilesystem: true
    capabilities:
      drop:
      - ALL
```

### 环境部署流水线

#### GitLab CI/CD配置

```yaml
# .gitlab-ci.yml
stages:
  - build
  - test
  - deploy-dev
  - deploy-test
  - deploy-staging
  - deploy-prod

variables:
  DOCKER_REGISTRY: registry.company.com
  PROJECT_NAME: knowledge-rag

build:
  stage: build
  script:
    - docker build -t $DOCKER_REGISTRY/$PROJECT_NAME:$CI_COMMIT_SHA .
    - docker push $DOCKER_REGISTRY/$PROJECT_NAME:$CI_COMMIT_SHA
  only:
    - develop
    - main

test:
  stage: test
  script:
    - pytest tests/ --cov=src --cov-report=xml
    - sonar-scanner
  coverage: '/TOTAL.+ ([0-9]{1,3}%)$/'
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml

deploy-dev:
  stage: deploy-dev
  script:
    - helm upgrade --install knowledge-rag-dev ./helm/knowledge-rag \
        --namespace knowledge-rag-dev \
        --values helm/values-dev.yaml \
        --set image.tag=$CI_COMMIT_SHA
  environment:
    name: development
    url: https://knowledge-rag-dev.company.com
  only:
    - develop

deploy-test:
  stage: deploy-test
  script:
    - helm upgrade --install knowledge-rag-test ./helm/knowledge-rag \
        --namespace knowledge-rag-test \
        --values helm/values-test.yaml \
        --set image.tag=$CI_COMMIT_SHA
  environment:
    name: testing
    url: https://knowledge-rag-test.company.com
  when: manual
  only:
    - develop

deploy-staging:
  stage: deploy-staging
  script:
    - helm upgrade --install knowledge-rag-staging ./helm/knowledge-rag \
        --namespace knowledge-rag-staging \
        --values helm/values-staging.yaml \
        --set image.tag=$CI_COMMIT_SHA
  environment:
    name: staging
    url: https://knowledge-rag-staging.company.com
  when: manual
  only:
    - main

deploy-prod:
  stage: deploy-prod
  script:
    - helm upgrade --install knowledge-rag-prod ./helm/knowledge-rag \
        --namespace knowledge-rag-prod \
        --values helm/values-prod.yaml \
        --set image.tag=$CI_COMMIT_TAG
  environment:
    name: production
    url: https://api.knowledge-rag.com
  when: manual
  only:
    - tags
```

### 数据管理策略

#### 数据同步脚本

```python
#!/usr/bin/env python3
# scripts/data_sync.py
"""
多环境数据同步脚本
用于在不同环境间同步测试数据和配置
"""

import os
import sys
import argparse
import subprocess
from typing import Dict, List
from datetime import datetime

class EnvironmentDataSync:
    """环境数据同步管理器"""
    
    def __init__(self):
        """初始化数据同步管理器"""
        self.environments = {
            'local': {
                'db_host': 'localhost',
                'db_port': '5432',
                'db_name': 'knowledge_rag_local',
                'namespace': 'knowledge-rag-local'
            },
            'dev': {
                'db_host': 'postgres-dev',
                'db_port': '5432',
                'db_name': 'knowledge_rag_dev',
                'namespace': 'knowledge-rag-dev'
            },
            'test': {
                'db_host': 'postgres-test',
                'db_port': '5432',
                'db_name': 'knowledge_rag_test',
                'namespace': 'knowledge-rag-test'
            },
            'staging': {
                'db_host': 'postgres-staging',
                'db_port': '5432',
                'db_name': 'knowledge_rag_staging',
                'namespace': 'knowledge-rag-staging'
            }
        }
    
    def sync_database_schema(self, source_env: str, target_env: str) -> bool:
        """同步数据库架构"""
        try:
            print(f"Syncing database schema from {source_env} to {target_env}...")
            
            source_config = self.environments[source_env]
            target_config = self.environments[target_env]
            
            # 导出源环境架构
            dump_cmd = [
                'pg_dump',
                '-h', source_config['db_host'],
                '-p', source_config['db_port'],
                '-d', source_config['db_name'],
                '--schema-only',
                '-f', f'/tmp/{source_env}_schema.sql'
            ]
            
            subprocess.run(dump_cmd, check=True)
            
            # 导入到目标环境
            restore_cmd = [
                'psql',
                '-h', target_config['db_host'],
                '-p', target_config['db_port'],
                '-d', target_config['db_name'],
                '-f', f'/tmp/{source_env}_schema.sql'
            ]
            
            subprocess.run(restore_cmd, check=True)
            
            print(f"Schema sync completed: {source_env} -> {target_env}")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"Error syncing schema: {e}")
            return False
    
    def sync_test_data(self, source_env: str, target_env: str, tables: List[str] = None) -> bool:
        """同步测试数据"""
        try:
            print(f"Syncing test data from {source_env} to {target_env}...")
            
            source_config = self.environments[source_env]
            target_config = self.environments[target_env]
            
            # 默认同步的表
            if tables is None:
                tables = ['users', 'documents', 'knowledge_graphs']
            
            for table in tables:
                print(f"Syncing table: {table}")
                
                # 导出表数据
                dump_cmd = [
                    'pg_dump',
                    '-h', source_config['db_host'],
                    '-p', source_config['db_port'],
                    '-d', source_config['db_name'],
                    '--data-only',
                    '--table', table,
                    '-f', f'/tmp/{table}_data.sql'
                ]
                
                subprocess.run(dump_cmd, check=True)
                
                # 清空目标表
                truncate_cmd = [
                    'psql',
                    '-h', target_config['db_host'],
                    '-p', target_config['db_port'],
                    '-d', target_config['db_name'],
                    '-c', f'TRUNCATE TABLE {table} CASCADE;'
                ]
                
                subprocess.run(truncate_cmd, check=True)
                
                # 导入数据
                restore_cmd = [
                    'psql',
                    '-h', target_config['db_host'],
                    '-p', target_config['db_port'],
                    '-d', target_config['db_name'],
                    '-f', f'/tmp/{table}_data.sql'
                ]
                
                subprocess.run(restore_cmd, check=True)
            
            print(f"Data sync completed: {source_env} -> {target_env}")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"Error syncing data: {e}")
            return False
    
    def sync_config_maps(self, source_env: str, target_env: str) -> bool:
        """同步Kubernetes ConfigMaps"""
        try:
            print(f"Syncing ConfigMaps from {source_env} to {target_env}...")
            
            source_namespace = self.environments[source_env]['namespace']
            target_namespace = self.environments[target_env]['namespace']
            
            # 导出ConfigMap
            export_cmd = [
                'kubectl', 'get', 'configmap', 'app-config',
                '-n', source_namespace,
                '-o', 'yaml',
                '--export'
            ]
            
            result = subprocess.run(export_cmd, capture_output=True, text=True, check=True)
            
            # 修改namespace
            config_yaml = result.stdout.replace(
                f'namespace: {source_namespace}',
                f'namespace: {target_namespace}'
            )
            
            # 应用到目标环境
            apply_cmd = ['kubectl', 'apply', '-f', '-']
            subprocess.run(apply_cmd, input=config_yaml, text=True, check=True)
            
            print(f"ConfigMap sync completed: {source_env} -> {target_env}")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"Error syncing ConfigMaps: {e}")
            return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Environment Data Sync Tool')
    parser.add_argument('--source', required=True, choices=['local', 'dev', 'test', 'staging'],
                       help='Source environment')
    parser.add_argument('--target', required=True, choices=['local', 'dev', 'test', 'staging'],
                       help='Target environment')
    parser.add_argument('--sync-type', choices=['schema', 'data', 'config', 'all'], default='all',
                       help='Type of sync to perform')
    parser.add_argument('--tables', nargs='*', help='Specific tables to sync (for data sync)')
    
    args = parser.parse_args()
    
    if args.source == args.target:
        print("Error: Source and target environments cannot be the same")
        sys.exit(1)
    
    sync_manager = EnvironmentDataSync()
    
    success = True
    
    if args.sync_type in ['schema', 'all']:
        success &= sync_manager.sync_database_schema(args.source, args.target)
    
    if args.sync_type in ['data', 'all']:
        success &= sync_manager.sync_test_data(args.source, args.target, args.tables)
    
    if args.sync_type in ['config', 'all']:
        success &= sync_manager.sync_config_maps(args.source, args.target)
    
    if success:
        print("\nSync completed successfully!")
        sys.exit(0)
    else:
        print("\nSync failed!")
        sys.exit(1)

if __name__ == '__main__':
    main()
```

### 环境监控和告警

#### 环境特定监控配置

```yaml
# monitoring/environment-alerts.yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: environment-specific-alerts
  namespace: knowledge-rag-prod
spec:
  groups:
  - name: production.rules
    rules:
    - alert: HighErrorRate
      expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
      for: 5m
      labels:
        severity: critical
        environment: production
      annotations:
        summary: "High error rate in production"
        description: "Error rate is {{ $value }} errors per second"
    
    - alert: HighMemoryUsage
      expr: container_memory_usage_bytes / container_spec_memory_limit_bytes > 0.8
      for: 10m
      labels:
        severity: warning
        environment: production
      annotations:
        summary: "High memory usage in production"
        description: "Memory usage is {{ $value | humanizePercentage }}"

---
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: environment-specific-alerts
  namespace: knowledge-rag-dev
spec:
  groups:
  - name: development.rules
    rules:
    - alert: ServiceDown
      expr: up == 0
      for: 15m
      labels:
        severity: warning
        environment: development
      annotations:
        summary: "Service down in development"
        description: "Service {{ $labels.instance }} has been down for more than 15 minutes"
```

### 环境管理最佳实践

#### 环境一致性检查

```bash
#!/bin/bash
# scripts/environment_check.sh

# 环境一致性检查脚本
# 验证不同环境间的配置一致性

set -e

ENVIRONMENTS=("dev" "test" "staging" "prod")
CHECK_ITEMS=("configmaps" "secrets" "deployments" "services")

echo "Starting environment consistency check..."

for item in "${CHECK_ITEMS[@]}"; do
    echo "\nChecking $item across environments:"
    
    for env in "${ENVIRONMENTS[@]}"; do
        namespace="knowledge-rag-$env"
        
        case $item in
            "configmaps")
                kubectl get configmap app-config -n $namespace -o yaml > /tmp/${env}_configmap.yaml
                ;;
            "secrets")
                kubectl get secret database-secrets -n $namespace -o yaml > /tmp/${env}_secrets.yaml
                ;;
            "deployments")
                kubectl get deployment knowledge-rag -n $namespace -o yaml > /tmp/${env}_deployment.yaml
                ;;
            "services")
                kubectl get service knowledge-rag -n $namespace -o yaml > /tmp/${env}_service.yaml
                ;;
        esac
        
        echo "  ✓ Exported $item from $env environment"
    done
    
    # 比较配置差异
    echo "  Comparing configurations..."
    for i in "${!ENVIRONMENTS[@]}"; do
        for j in "${!ENVIRONMENTS[@]}"; do
            if [ $i -lt $j ]; then
                env1=${ENVIRONMENTS[$i]}
                env2=${ENVIRONMENTS[$j]}
                
                diff_output=$(diff /tmp/${env1}_${item}.yaml /tmp/${env2}_${item}.yaml || true)
                
                if [ -n "$diff_output" ]; then
                    echo "    ⚠️  Differences found between $env1 and $env2:"
                    echo "$diff_output" | head -20
                else
                    echo "    ✓ $env1 and $env2 configurations match"
                fi
            fi
        done
    done
done

echo "\nEnvironment consistency check completed!"
```

#### 环境管理检查清单

- [ ] **配置管理**
  - [ ] 所有环境使用统一的配置模板
  - [ ] 敏感信息通过Secrets管理
  - [ ] 环境特定配置正确设置
  - [ ] 配置版本控制和审计

- [ ] **部署一致性**
  - [ ] 使用相同的容器镜像构建流程
  - [ ] Helm Chart模板化部署
  - [ ] 环境间资源配置合理
  - [ ] 自动化部署流水线

- [ ] **数据管理**
  - [ ] 测试数据定期同步
  - [ ] 生产数据脱敏处理
  - [ ] 数据备份和恢复策略
  - [ ] 数据迁移脚本测试

- [ ] **监控和告警**
  - [ ] 环境特定监控指标
  - [ ] 告警规则环境差异化
  - [ ] 日志聚合和分析
  - [ ] 性能基线建立

- [ ] **安全和合规**
  - [ ] 网络隔离和访问控制
  - [ ] 密钥轮换策略
  - [ ] 安全扫描和漏洞管理
  - [ ] 合规性检查和审计

---

## API文档生成

### 概述

Knowledge RAG系统采用自动化API文档生成策略，确保API文档与代码实现保持同步，提供完整、准确、易用的API接口规范。本章节详细描述了API文档生成工具链、文档规范和自动化流程。

### API文档架构设计

#### 文档生成策略

```
API代码注释 → OpenAPI规范 → 多格式文档 → 在线文档平台
     ↓              ↓              ↓              ↓
  代码注解      Swagger/OAS     HTML/PDF      文档网站
  类型定义      JSON Schema     Markdown      交互式API
  示例代码      API测试         多语言SDK     版本管理
```

#### 文档生成工具链

| 工具类型 | 工具名称 | 用途 | 输出格式 | 集成方式 |
|---------|---------|------|----------|----------|
| 代码注释 | Pydantic | 数据模型定义 | JSON Schema | 装饰器 |
| API规范 | FastAPI | OpenAPI生成 | JSON/YAML | 自动生成 |
| 文档渲染 | Swagger UI | 交互式文档 | HTML | 内嵌服务 |
| 文档生成 | Redoc | 美观文档 | HTML | 静态生成 |
| SDK生成 | OpenAPI Generator | 多语言SDK | 多语言 | CI/CD |
| 文档托管 | GitBook | 在线文档 | Web | Git集成 |

### API文档规范

#### OpenAPI规范配置

```python
# src/api/main.py
"""
Knowledge RAG API主应用
提供完整的RESTful API接口和自动化文档生成
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles
from typing import Dict, List, Optional, Any
import uvicorn

# API元数据配置
API_METADATA = {
    "title": "Knowledge RAG API",
    "description": """
    Knowledge RAG系统提供智能文档处理和问答服务的RESTful API接口。
    
    ## 主要功能
    
    * **文档管理** - 文档上传、解析、存储和检索
    * **知识图谱** - 实体提取、关系构建和图谱查询
    * **智能问答** - 基于RAG的智能问答和上下文管理
    * **向量搜索** - 语义搜索和相似度匹配
    * **用户管理** - 用户认证、授权和权限控制
    
    ## 认证方式
    
    API使用JWT Bearer Token进行认证：
    ```
    Authorization: Bearer <your-jwt-token>
    ```
    
    ## 错误处理
    
    API遵循标准HTTP状态码，错误响应格式：
    ```json
    {
        "error": {
            "code": "ERROR_CODE",
            "message": "Error description",
            "details": {}
        }
    }
    ```
    
    ## 版本控制
    
    API版本通过URL路径进行管理：`/api/v1/`
    """,
    "version": "1.0.0",
    "contact": {
        "name": "Knowledge RAG Team",
        "email": "support@knowledge-rag.com",
        "url": "https://knowledge-rag.com"
    },
    "license": {
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT"
    },
    "servers": [
        {
            "url": "https://api.knowledge-rag.com",
            "description": "Production server"
        },
        {
            "url": "https://staging-api.knowledge-rag.com",
            "description": "Staging server"
        },
        {
            "url": "http://localhost:8000",
            "description": "Development server"
        }
    ]
}

# 创建FastAPI应用实例
app = FastAPI(
    title=API_METADATA["title"],
    description=API_METADATA["description"],
    version=API_METADATA["version"],
    contact=API_METADATA["contact"],
    license_info=API_METADATA["license"],
    docs_url=None,  # 禁用默认文档
    redoc_url=None,  # 禁用默认Redoc
    openapi_url="/api/v1/openapi.json"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 自定义OpenAPI配置
def custom_openapi() -> Dict[str, Any]:
    """
    生成自定义OpenAPI规范
    
    Returns:
        Dict[str, Any]: OpenAPI规范字典
    """
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=API_METADATA["title"],
        version=API_METADATA["version"],
        description=API_METADATA["description"],
        routes=app.routes,
        servers=API_METADATA["servers"]
    )
    
    # 添加安全定义
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT Bearer Token认证"
        }
    }
    
    # 添加全局安全要求
    openapi_schema["security"] = [{"BearerAuth": []}]
    
    # 添加标签分组
    openapi_schema["tags"] = [
        {
            "name": "Authentication",
            "description": "用户认证和授权相关接口"
        },
        {
            "name": "Documents",
            "description": "文档管理相关接口"
        },
        {
            "name": "Knowledge Graph",
            "description": "知识图谱相关接口"
        },
        {
            "name": "Question Answering",
            "description": "智能问答相关接口"
        },
        {
            "name": "Search",
            "description": "搜索和检索相关接口"
        },
        {
            "name": "Analytics",
            "description": "分析和监控相关接口"
        }
    ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# 自定义文档路由
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """
    自定义Swagger UI文档页面
    
    Returns:
        HTMLResponse: Swagger UI HTML页面
    """
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{API_METADATA['title']} - Swagger UI",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@4.15.5/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@4.15.5/swagger-ui.css",
        swagger_favicon_url="https://fastapi.tiangolo.com/img/favicon.png"
    )

@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    """
    自定义Redoc文档页面
    
    Returns:
        HTMLResponse: Redoc HTML页面
    """
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=f"{API_METADATA['title']} - ReDoc",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@2.0.0/bundles/redoc.standalone.js",
        redoc_favicon_url="https://fastapi.tiangolo.com/img/favicon.png"
    )
```

#### 数据模型定义

```python
# src/api/models/schemas.py
"""
API数据模型和Schema定义
提供完整的请求/响应数据结构和验证规则
"""

from pydantic import BaseModel, Field, validator, EmailStr
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum

class DocumentStatus(str, Enum):
    """
    文档状态枚举
    
    Attributes:
        PENDING: 待处理
        PROCESSING: 处理中
        COMPLETED: 处理完成
        FAILED: 处理失败
    """
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class QuestionType(str, Enum):
    """
    问题类型枚举
    
    Attributes:
        FACTUAL: 事实性问题
        ANALYTICAL: 分析性问题
        COMPARATIVE: 比较性问题
        SUMMARIZATION: 总结性问题
    """
    FACTUAL = "factual"
    ANALYTICAL = "analytical"
    COMPARATIVE = "comparative"
    SUMMARIZATION = "summarization"

# 基础响应模型
class BaseResponse(BaseModel):
    """
    API基础响应模型
    
    Attributes:
        success: 请求是否成功
        message: 响应消息
        timestamp: 响应时间戳
    """
    success: bool = Field(..., description="请求是否成功")
    message: str = Field(..., description="响应消息")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="响应时间戳")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ErrorResponse(BaseModel):
    """
    API错误响应模型
    
    Attributes:
        error: 错误信息对象
    """
    error: Dict[str, Any] = Field(
        ...,
        description="错误信息",
        example={
            "code": "VALIDATION_ERROR",
            "message": "请求参数验证失败",
            "details": {
                "field": "email",
                "issue": "格式不正确"
            }
        }
    )

# 用户相关模型
class UserCreate(BaseModel):
    """
    用户创建请求模型
    
    Attributes:
        username: 用户名
        email: 邮箱地址
        password: 密码
        full_name: 全名
    """
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        regex=r"^[a-zA-Z0-9_]+$",
        description="用户名，3-50个字符，只能包含字母、数字和下划线",
        example="john_doe"
    )
    email: EmailStr = Field(
        ...,
        description="邮箱地址",
        example="john.doe@example.com"
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="密码，至少8个字符",
        example="SecurePassword123!"
    )
    full_name: Optional[str] = Field(
        None,
        max_length=100,
        description="用户全名",
        example="John Doe"
    )
    
    @validator('password')
    def validate_password(cls, v):
        """
        密码强度验证
        
        Args:
            v: 密码值
            
        Returns:
            str: 验证通过的密码
            
        Raises:
            ValueError: 密码不符合要求
        """
        if not any(c.isupper() for c in v):
            raise ValueError('密码必须包含至少一个大写字母')
        if not any(c.islower() for c in v):
            raise ValueError('密码必须包含至少一个小写字母')
        if not any(c.isdigit() for c in v):
            raise ValueError('密码必须包含至少一个数字')
        return v

class UserResponse(BaseResponse):
    """
    用户信息响应模型
    
    Attributes:
        data: 用户数据
    """
    data: Dict[str, Any] = Field(
        ...,
        description="用户数据",
        example={
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "username": "john_doe",
            "email": "john.doe@example.com",
            "full_name": "John Doe",
            "is_active": True,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
    )

# 文档相关模型
class DocumentUpload(BaseModel):
    """
    文档上传请求模型
    
    Attributes:
        title: 文档标题
        description: 文档描述
        tags: 文档标签
        category: 文档分类
    """
    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="文档标题",
        example="Knowledge RAG系统架构设计"
    )
    description: Optional[str] = Field(
        None,
        max_length=1000,
        description="文档描述",
        example="详细描述Knowledge RAG系统的架构设计和实现方案"
    )
    tags: Optional[List[str]] = Field(
        None,
        description="文档标签列表",
        example=["架构", "设计", "RAG"]
    )
    category: Optional[str] = Field(
        None,
        max_length=50,
        description="文档分类",
        example="技术文档"
    )

class DocumentResponse(BaseResponse):
    """
    文档信息响应模型
    
    Attributes:
        data: 文档数据
    """
    data: Dict[str, Any] = Field(
        ...,
        description="文档数据",
        example={
            "id": "doc_123e4567-e89b-12d3-a456-426614174000",
            "title": "Knowledge RAG系统架构设计",
            "description": "详细描述Knowledge RAG系统的架构设计和实现方案",
            "status": "completed",
            "file_size": 1024000,
            "file_type": "application/pdf",
            "tags": ["架构", "设计", "RAG"],
            "category": "技术文档",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "processing_stats": {
                "pages": 25,
                "chunks": 150,
                "entities": 45,
                "relationships": 78
            }
        }
    )

# 问答相关模型
class QuestionRequest(BaseModel):
    """
    问答请求模型
    
    Attributes:
        question: 用户问题
        context_ids: 上下文文档ID列表
        question_type: 问题类型
        max_tokens: 最大回答长度
        temperature: 生成温度
    """
    question: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="用户问题",
        example="Knowledge RAG系统的核心架构是什么？"
    )
    context_ids: Optional[List[str]] = Field(
        None,
        description="相关文档ID列表，用于限定搜索范围",
        example=["doc_123", "doc_456"]
    )
    question_type: Optional[QuestionType] = Field(
        QuestionType.FACTUAL,
        description="问题类型"
    )
    max_tokens: Optional[int] = Field(
        500,
        ge=50,
        le=2000,
        description="最大回答长度（token数）"
    )
    temperature: Optional[float] = Field(
        0.7,
        ge=0.0,
        le=2.0,
        description="生成温度，控制回答的创造性"
    )

class AnswerResponse(BaseResponse):
    """
    问答响应模型
    
    Attributes:
        data: 回答数据
    """
    data: Dict[str, Any] = Field(
        ...,
        description="回答数据",
        example={
            "answer": "Knowledge RAG系统采用微服务架构，包含文档处理、向量存储、知识图谱和问答引擎四个核心模块...",
            "confidence_score": 0.92,
            "sources": [
                {
                    "document_id": "doc_123",
                    "title": "系统架构文档",
                    "relevance_score": 0.95,
                    "excerpt": "系统采用微服务架构设计..."
                }
            ],
            "related_entities": [
                {
                    "name": "微服务架构",
                    "type": "concept",
                    "confidence": 0.88
                }
            ],
            "processing_time": 1.23,
            "token_usage": {
                "prompt_tokens": 1500,
                "completion_tokens": 300,
                "total_tokens": 1800
            }
        }
    )
```

### 自动化文档生成

#### CI/CD集成配置

```yaml
# .github/workflows/api-docs.yml
name: API Documentation Generation

on:
  push:
    branches: [ main, develop ]
    paths:
      - 'src/api/**'
      - 'docs/api/**'
  pull_request:
    branches: [ main ]
    paths:
      - 'src/api/**'
      - 'docs/api/**'

jobs:
  generate-docs:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v3
      
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
        
    - name: Install dependencies
      run: |
        curl -LsSf https://astral.sh/uv/install.sh | sh
        uv sync --prerelease=allow
        uv tool install openapi-generator-cli
        
    - name: Generate OpenAPI spec
      run: |
        python scripts/generate_openapi.py
        
    - name: Validate OpenAPI spec
      run: |
        npx @apidevtools/swagger-parser validate docs/api/openapi.json
        
    - name: Generate API documentation
      run: |
        # 生成HTML文档
        npx redoc-cli build docs/api/openapi.json --output docs/api/index.html
        
        # 生成Markdown文档
        npx widdershins docs/api/openapi.json -o docs/api/README.md
        
        # 生成Postman集合
        openapi-generator generate -i docs/api/openapi.json -g postman-collection -o docs/api/postman/
        
    - name: Generate SDK
      run: |
        # 生成Python SDK
        openapi-generator generate \
          -i docs/api/openapi.json \
          -g python \
          -o sdks/python \
          --additional-properties=packageName=knowledge_rag_client,projectName=knowledge-rag-python-client
          
        # 生成JavaScript SDK
        openapi-generator generate \
          -i docs/api/openapi.json \
          -g javascript \
          -o sdks/javascript \
          --additional-properties=projectName=knowledge-rag-js-client
          
        # 生成TypeScript SDK
        openapi-generator generate \
          -i docs/api/openapi.json \
          -g typescript-axios \
          -o sdks/typescript \
          --additional-properties=npmName=@knowledge-rag/client
          
    - name: Run API tests
      run: |
        # 启动API服务
        python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 &
        sleep 10
        
        # 运行API测试
        pytest tests/api/ -v
        
        # 运行文档测试
        python scripts/test_api_examples.py
        
    - name: Deploy documentation
      if: github.ref == 'refs/heads/main'
      run: |
        # 部署到GitHub Pages
        cp -r docs/api/* gh-pages/
        
        # 部署到GitBook
        curl -X POST "$GITBOOK_WEBHOOK_URL" \
          -H "Content-Type: application/json" \
          -d '{"ref": "main"}'
      env:
        GITBOOK_WEBHOOK_URL: ${{ secrets.GITBOOK_WEBHOOK_URL }}
        
    - name: Create release artifacts
      if: github.ref == 'refs/heads/main'
      run: |
        # 创建文档压缩包
        tar -czf api-docs-${{ github.sha }}.tar.gz docs/api/
        tar -czf api-sdks-${{ github.sha }}.tar.gz sdks/
        
    - name: Upload artifacts
      uses: actions/upload-artifact@v4
      with:
        name: api-documentation
        path: |
          docs/api/
          sdks/
          *.tar.gz
```

#### 文档生成脚本

```python
#!/usr/bin/env python3
# scripts/generate_openapi.py
"""
OpenAPI规范生成脚本
自动从FastAPI应用生成OpenAPI规范文件
"""

import json
import yaml
import os
from pathlib import Path
from typing import Dict, Any

# 导入FastAPI应用
sys.path.append(str(Path(__file__).parent.parent))
from src.api.main import app

def generate_openapi_spec() -> Dict[str, Any]:
    """
    生成OpenAPI规范
    
    Returns:
        Dict[str, Any]: OpenAPI规范字典
    """
    return app.openapi()

def save_openapi_spec(spec: Dict[str, Any], output_dir: str = "docs/api") -> None:
    """
    保存OpenAPI规范到文件
    
    Args:
        spec: OpenAPI规范字典
        output_dir: 输出目录
    """
    # 确保输出目录存在
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # 保存JSON格式
    json_path = Path(output_dir) / "openapi.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(spec, f, indent=2, ensure_ascii=False)
    
    # 保存YAML格式
    yaml_path = Path(output_dir) / "openapi.yaml"
    with open(yaml_path, 'w', encoding='utf-8') as f:
        yaml.dump(spec, f, default_flow_style=False, allow_unicode=True)
    
    print(f"OpenAPI规范已生成：")
    print(f"  JSON: {json_path}")
    print(f"  YAML: {yaml_path}")

def generate_api_examples() -> None:
    """
    生成API使用示例
    """
    examples = {
        "authentication": {
            "login": {
                "request": {
                    "method": "POST",
                    "url": "/api/v1/auth/login",
                    "headers": {
                        "Content-Type": "application/json"
                    },
                    "body": {
                        "username": "john_doe",
                        "password": "SecurePassword123!"
                    }
                },
                "response": {
                    "status": 200,
                    "body": {
                        "success": True,
                        "message": "登录成功",
                        "data": {
                            "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                            "token_type": "bearer",
                            "expires_in": 3600
                        }
                    }
                }
            }
        },
        "documents": {
            "upload": {
                "request": {
                    "method": "POST",
                    "url": "/api/v1/documents/upload",
                    "headers": {
                        "Authorization": "Bearer <token>",
                        "Content-Type": "multipart/form-data"
                    },
                    "body": {
                        "file": "<binary-data>",
                        "title": "系统架构文档",
                        "description": "Knowledge RAG系统架构设计",
                        "tags": ["架构", "设计"]
                    }
                },
                "response": {
                    "status": 201,
                    "body": {
                        "success": True,
                        "message": "文档上传成功",
                        "data": {
                            "id": "doc_123e4567-e89b-12d3-a456-426614174000",
                            "title": "系统架构文档",
                            "status": "processing",
                            "upload_url": "https://api.knowledge-rag.com/api/v1/documents/doc_123e4567-e89b-12d3-a456-426614174000"
                        }
                    }
                }
            }
        },
        "question_answering": {
            "ask": {
                "request": {
                    "method": "POST",
                    "url": "/api/v1/qa/ask",
                    "headers": {
                        "Authorization": "Bearer <token>",
                        "Content-Type": "application/json"
                    },
                    "body": {
                        "question": "Knowledge RAG系统的核心架构是什么？",
                        "context_ids": ["doc_123"],
                        "max_tokens": 500,
                        "temperature": 0.7
                    }
                },
                "response": {
                    "status": 200,
                    "body": {
                        "success": True,
                        "message": "问答完成",
                        "data": {
                            "answer": "Knowledge RAG系统采用微服务架构...",
                            "confidence_score": 0.92,
                            "sources": [
                                {
                                    "document_id": "doc_123",
                                    "title": "系统架构文档",
                                    "relevance_score": 0.95
                                }
                            ]
                        }
                    }
                }
            }
        }
    }
    
    # 保存示例文件
    examples_path = Path("docs/api") / "examples.json"
    with open(examples_path, 'w', encoding='utf-8') as f:
        json.dump(examples, f, indent=2, ensure_ascii=False)
    
    print(f"API示例已生成：{examples_path}")

def main():
    """
    主函数
    """
    print("开始生成API文档...")
    
    # 生成OpenAPI规范
    spec = generate_openapi_spec()
    save_openapi_spec(spec)
    
    # 生成API示例
    generate_api_examples()
    
    print("API文档生成完成！")

if __name__ == "__main__":
    main()
```

### 文档部署和托管

#### Docker化文档服务

```dockerfile
# docs/Dockerfile
FROM nginx:alpine

# 安装Node.js用于构建文档
RUN apk add --no-cache nodejs npm

# 复制文档源文件
COPY api/ /usr/share/nginx/html/api/
COPY static/ /usr/share/nginx/html/static/

# 安装文档生成工具
RUN npm install -g redoc-cli swagger-ui-dist

# 生成静态文档
RUN redoc-cli build /usr/share/nginx/html/api/openapi.json \
    --output /usr/share/nginx/html/index.html

# 复制Nginx配置
COPY nginx.conf /etc/nginx/nginx.conf

# 暴露端口
EXPOSE 80

# 启动Nginx
CMD ["nginx", "-g", "daemon off;"]
```

```nginx
# docs/nginx.conf
events {
    worker_connections 1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;
    
    # 启用gzip压缩
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
    
    server {
        listen 80;
        server_name localhost;
        
        # 文档根目录
        root /usr/share/nginx/html;
        index index.html;
        
        # API文档主页
        location / {
            try_files $uri $uri/ /index.html;
        }
        
        # OpenAPI规范文件
        location /api/openapi.json {
            add_header Access-Control-Allow-Origin *;
            add_header Content-Type application/json;
        }
        
        # Swagger UI
        location /swagger/ {
            alias /usr/share/nginx/html/swagger-ui/;
            try_files $uri $uri/ /swagger-ui/index.html;
        }
        
        # API示例
        location /examples {
            add_header Content-Type application/json;
            try_files $uri $uri.json =404;
        }
        
        # 健康检查
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }
    }
}
```

#### Kubernetes部署配置

```yaml
# k8s/api-docs-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-docs
  namespace: knowledge-rag-prod
  labels:
    app: api-docs
    component: documentation
spec:
  replicas: 2
  selector:
    matchLabels:
      app: api-docs
  template:
    metadata:
      labels:
        app: api-docs
        component: documentation
    spec:
      containers:
      - name: api-docs
        image: knowledge-rag/api-docs:latest
        ports:
        - containerPort: 80
        resources:
          requests:
            memory: "64Mi"
            cpu: "50m"
          limits:
            memory: "128Mi"
            cpu: "100m"
        livenessProbe:
          httpGet:
            path: /health
            port: 80
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 80
          initialDelaySeconds: 5
          periodSeconds: 10

---
apiVersion: v1
kind: Service
metadata:
  name: api-docs-service
  namespace: knowledge-rag-prod
spec:
  selector:
    app: api-docs
  ports:
  - port: 80
    targetPort: 80
  type: ClusterIP

---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: api-docs-ingress
  namespace: knowledge-rag-prod
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - docs.knowledge-rag.com
    secretName: api-docs-tls
  rules:
  - host: docs.knowledge-rag.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api-docs-service
            port:
              number: 80
```

### 文档质量保证

#### 文档测试脚本

```python
#!/usr/bin/env python3
# scripts/test_api_examples.py
"""
API文档示例测试脚本
验证API文档中的示例是否正确
"""

import json
import requests
import pytest
from typing import Dict, Any
from pathlib import Path

class APIDocumentationTester:
    """
    API文档测试器
    
    Attributes:
        base_url: API基础URL
        examples: API示例数据
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        初始化测试器
        
        Args:
            base_url: API基础URL
        """
        self.base_url = base_url
        self.examples = self._load_examples()
        self.session = requests.Session()
    
    def _load_examples(self) -> Dict[str, Any]:
        """
        加载API示例数据
        
        Returns:
            Dict[str, Any]: 示例数据字典
        """
        examples_path = Path("docs/api/examples.json")
        if not examples_path.exists():
            raise FileNotFoundError(f"示例文件不存在: {examples_path}")
        
        with open(examples_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def test_openapi_spec_validity(self):
        """
        测试OpenAPI规范有效性
        """
        response = self.session.get(f"{self.base_url}/api/v1/openapi.json")
        assert response.status_code == 200
        
        spec = response.json()
        assert "openapi" in spec
        assert "info" in spec
        assert "paths" in spec
        
        print("✓ OpenAPI规范有效性测试通过")
    
    def test_documentation_accessibility(self):
        """
        测试文档可访问性
        """
        # 测试Swagger UI
        response = self.session.get(f"{self.base_url}/docs")
        assert response.status_code == 200
        assert "swagger" in response.text.lower()
        
        # 测试Redoc
        response = self.session.get(f"{self.base_url}/redoc")
        assert response.status_code == 200
        assert "redoc" in response.text.lower()
        
        print("✓ 文档可访问性测试通过")
    
    def test_api_examples(self):
        """
        测试API示例的正确性
        """
        # 注意：这里只测试请求格式，不执行实际API调用
        # 实际测试需要有效的认证和测试数据
        
        for category, endpoints in self.examples.items():
            for endpoint_name, example in endpoints.items():
                request_example = example.get("request", {})
                response_example = example.get("response", {})
                
                # 验证请求示例结构
                assert "method" in request_example
                assert "url" in request_example
                assert "headers" in request_example
                
                # 验证响应示例结构
                assert "status" in response_example
                assert "body" in response_example
                
                print(f"✓ {category}.{endpoint_name} 示例结构正确")
    
    def test_schema_consistency(self):
        """
        测试Schema一致性
        """
        # 获取OpenAPI规范
        response = self.session.get(f"{self.base_url}/api/v1/openapi.json")
        spec = response.json()
        
        # 检查所有路径都有对应的Schema定义
        paths = spec.get("paths", {})
        components = spec.get("components", {}).get("schemas", {})
        
        for path, methods in paths.items():
            for method, details in methods.items():
                # 检查请求体Schema
                request_body = details.get("requestBody", {})
                if request_body:
                    content = request_body.get("content", {})
                    for media_type, schema_info in content.items():
                        schema_ref = schema_info.get("schema", {}).get("$ref")
                        if schema_ref:
                            schema_name = schema_ref.split("/")[-1]
                            assert schema_name in components, f"Schema {schema_name} 未定义"
                
                # 检查响应Schema
                responses = details.get("responses", {})
                for status_code, response_info in responses.items():
                    content = response_info.get("content", {})
                    for media_type, schema_info in content.items():
                        schema_ref = schema_info.get("schema", {}).get("$ref")
                        if schema_ref:
                            schema_name = schema_ref.split("/")[-1]
                            assert schema_name in components, f"Schema {schema_name} 未定义"
        
        print("✓ Schema一致性测试通过")
    
    def run_all_tests(self):
        """
        运行所有测试
        """
        print("开始API文档测试...")
        
        try:
            self.test_openapi_spec_validity()
            self.test_documentation_accessibility()
            self.test_api_examples()
            self.test_schema_consistency()
            
            print("\n🎉 所有API文档测试通过！")
            return True
            
        except Exception as e:
            print(f"\n❌ 测试失败: {e}")
            return False

def main():
    """
    主函数
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="API文档测试工具")
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="API基础URL"
    )
    
    args = parser.parse_args()
    
    tester = APIDocumentationTester(args.base_url)
    success = tester.run_all_tests()
    
    exit(0 if success else 1)

if __name__ == "__main__":
    main()
```

### API文档最佳实践

#### 文档维护检查清单

- [ ] **代码注释和文档同步**
  - [ ] 所有API端点都有完整的docstring
  - [ ] 数据模型都有详细的字段说明
  - [ ] 示例代码保持最新
  - [ ] 错误码和消息准确描述

- [ ] **OpenAPI规范质量**
  - [ ] 规范文件语法正确
  - [ ] 所有端点都有适当的标签分组
  - [ ] 安全定义完整配置
  - [ ] 服务器信息准确设置

- [ ] **文档内容完整性**
  - [ ] 认证和授权说明清晰
  - [ ] 错误处理机制详细描述
  - [ ] 限流和配额政策说明
  - [ ] 版本控制策略明确

- [ ] **用户体验优化**
  - [ ] 交互式文档功能正常
  - [ ] 代码示例可直接运行
  - [ ] 多语言SDK可用
  - [ ] 搜索功能有效

- [ ] **自动化和集成**
  - [ ] CI/CD流水线包含文档生成
  - [ ] 文档测试自动化执行
  - [ ] 版本发布自动更新文档
  - [ ] 监控文档访问和使用情况

---

**下一步操作选项：**

1. **完善监控体系** - 添加更多监控指标和告警规则
2. **设计安全架构** - 深入的安全策略和合规要求
3. **添加运维手册** - 日常运维操作和故障排查指南
4. **成本优化策略** - 资源使用优化和成本控制
5. **容量规划指南** - 系统容量评估和扩展规划
9. **生成完整文档** - 输出最终的全栈架构文档

请选择您希望继续的方向（输入数字1-9）：