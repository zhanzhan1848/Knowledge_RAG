# Knowledge RAG System

一个基于 FastAPI 微服务架构的智能知识检索增强生成（RAG）系统，支持多种文档格式处理、向量化存储、知识图谱构建和智能问答。

## 🚀 项目特性

### 核心功能
- **多格式文档处理**: 支持 PDF、Word、Excel、PowerPoint、Markdown、HTML 等格式
- **智能文档解析**: 基于 OCR 和 NLP 的文档内容提取和结构化
- **向量化存储**: 集成 ChromaDB、FAISS、Weaviate 等向量数据库
- **知识图谱**: 基于 Neo4j 的实体关系抽取和图谱构建
- **多模型支持**: 集成 OpenAI、Anthropic、本地模型等多种 LLM
- **智能问答**: 基于检索增强生成的高质量问答系统
- **实时处理**: 异步任务队列和实时文档处理

### 技术架构
- **微服务架构**: 基于 FastAPI 的松耦合微服务设计
- **容器化部署**: Docker 和 Docker Compose 支持
- **数据库支持**: PostgreSQL、Redis、Elasticsearch、Neo4j
- **消息队列**: RabbitMQ 和 Celery 异步任务处理
- **监控体系**: Prometheus + Grafana 完整监控方案
- **CI/CD**: GitHub Actions 自动化部署流水线

## 🏗️ 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend UI   │    │   Mobile App    │    │  Third Party    │
│                 │    │                 │    │   Integration   │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   API Gateway   │
                    │   (Kong/Nginx)  │
                    └─────────┬───────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────▼───────┐    ┌────────▼────────┐    ┌──────▼──────┐
│ Auth Service   │    │Document Service │    │ QA Service  │
│   (FastAPI)    │    │   (FastAPI)     │    │ (FastAPI)   │
└───────┬───────┘    └────────┬────────┘    └──────┬──────┘
        │                     │                     │
┌───────▼───────┐    ┌────────▼────────┐    ┌──────▼──────┐
│Vector Service  │    │  LLM Service    │    │Knowledge    │
│   (FastAPI)    │    │   (FastAPI)     │    │Graph Service│
└───────┬───────┘    └────────┬────────┘    └──────┬──────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
    ┌─────────────────────────┼─────────────────────────┐
    │                         │                         │
┌───▼────┐ ┌─────▼─────┐ ┌───▼────┐ ┌─────▼─────┐ ┌───▼────┐
│PostgreSQL│ │   Redis   │ │ Neo4j  │ │Elasticsearch│ │RabbitMQ│
│          │ │           │ │        │ │           │ │        │
└──────────┘ └───────────┘ └────────┘ └───────────┘ └────────┘
```

## 🛠️ 技术栈

### 后端服务
- **Web框架**: FastAPI 0.104+
- **异步运行时**: Uvicorn
- **数据库ORM**: SQLAlchemy 2.0 (异步)
- **数据库迁移**: Alembic
- **任务队列**: Celery + Redis
- **缓存**: Redis

### 数据存储
- **关系数据库**: PostgreSQL 15
- **向量数据库**: ChromaDB, FAISS
- **图数据库**: Neo4j 5.14
- **搜索引擎**: Elasticsearch 8.11
- **消息队列**: RabbitMQ 3.12

### AI/ML 组件
- **LLM集成**: OpenAI GPT, Anthropic Claude
- **嵌入模型**: Sentence Transformers
- **文档处理**: PyPDF2, python-docx, BeautifulSoup
- **NLP处理**: spaCy, NLTK

### 开发工具
- **代码质量**: Black, isort, Flake8, MyPy
- **测试框架**: Pytest, pytest-asyncio
- **安全扫描**: Bandit, Trivy
- **容器化**: Docker, Docker Compose
- **CI/CD**: GitHub Actions

### 监控运维
- **指标监控**: Prometheus
- **可视化**: Grafana
- **链路追踪**: Jaeger
- **日志管理**: Structured Logging

## 🚀 快速开始

### 环境要求
- Python 3.10+
- uv 包管理器 (推荐) 或 pip
- Docker 20.0+
- Docker Compose 2.0+
- Git

### 1. 克隆项目
```bash
git clone https://github.com/your-org/knowledge-rag.git
cd knowledge-rag
```

### 2. 环境配置
```bash
# 复制环境变量模板
cp .env.template .env

# 编辑环境变量（必须配置 LLM API Keys）
vim .env
```

### 3. 启动服务
```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 4. 验证部署
```bash
# 检查 API 网关健康状态
curl http://localhost:8000/health

# 访问 API 文档
open http://localhost:8000/docs

# 访问监控面板
open http://localhost:3000  # Grafana (admin/admin123)
open http://localhost:9090  # Prometheus
```

## 📚 服务端口

| 服务 | 端口 | 描述 |
|------|------|------|
| API Gateway | 8000 | 主要 API 入口 |
| Auth Service | 8001 | 用户认证服务 |
| Document Service | 8002 | 文档处理服务 |
| Vector Service | 8003 | 向量化服务 |
| LLM Service | 8004 | 大语言模型服务 |
| QA Service | 8005 | 问答服务 |
| Knowledge Graph | 8006 | 知识图谱服务 |
| Notification | 8007 | 通知服务 |
| PostgreSQL | 5432 | 主数据库 |
| Redis | 6379 | 缓存和消息队列 |
| Elasticsearch | 9200 | 全文搜索 |
| Neo4j | 7474/7687 | 图数据库 |
| RabbitMQ | 5672/15672 | 消息队列 |
| Prometheus | 9090 | 监控指标 |
| Grafana | 3000 | 监控面板 |

## 🔧 开发指南

### 本地开发环境
```bash
# 使用 uv 创建虚拟环境和安装依赖 (推荐)
uv sync --dev

# 或者使用传统方式
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 安装开发依赖
uv pip install -r requirements-dev.txt

# 安装 pre-commit 钩子
pre-commit install

# 运行代码格式化
black .
isort .

# 运行类型检查
mypy services/ shared/ libs/

# 运行测试
pytest tests/ -v --cov
```

### 添加新服务
1. 在 `services/` 目录下创建新服务目录
2. 复制现有服务的结构和 Dockerfile
3. 更新 `docker-compose.yml` 添加新服务配置
4. 更新 `pyproject.toml` 添加服务特定依赖
5. 编写服务代码和测试

### 数据库迁移
```bash
# 生成迁移文件
alembic revision --autogenerate -m "描述变更"

# 应用迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1
```

## 🧪 测试

### 运行测试套件
```bash
# 运行所有测试
pytest

# 运行单元测试
pytest tests/unit/ -v

# 运行集成测试
pytest tests/integration/ -v

# 运行端到端测试
pytest tests/e2e/ -v

# 生成覆盖率报告
pytest --cov=services --cov=shared --cov=libs --cov-report=html
```

### 性能测试
```bash
# 使用 Locust 进行负载测试
locust -f tests/performance/locustfile.py --host=http://localhost:8000
```

## 📊 监控和运维

### 监控指标
- **应用指标**: 请求量、响应时间、错误率
- **系统指标**: CPU、内存、磁盘、网络使用率
- **业务指标**: 文档处理量、问答准确率、用户活跃度

### 日志管理
- 结构化日志输出（JSON 格式）
- 分级日志记录（DEBUG、INFO、WARNING、ERROR）
- 集中化日志收集和分析

### 健康检查
每个服务都提供 `/health` 端点用于健康检查，包括：
- 服务状态
- 数据库连接状态
- 外部依赖状态
- 资源使用情况

## 🔒 安全考虑

### 认证和授权
- JWT Token 认证
- RBAC 角色权限控制
- API 密钥管理
- OAuth 2.0 集成

### 数据安全
- 数据库连接加密
- 敏感数据脱敏
- 文件上传安全检查
- API 访问限流

### 网络安全
- HTTPS 强制使用
- CORS 跨域配置
- 防火墙规则
- 容器网络隔离

## 📈 性能优化

### 缓存策略
- Redis 多级缓存
- 查询结果缓存
- 向量检索缓存
- CDN 静态资源缓存

### 数据库优化
- 连接池配置
- 索引优化
- 查询优化
- 读写分离

### 异步处理
- 异步 I/O 操作
- 后台任务队列
- 批量处理优化
- 流式数据处理

## 🤝 贡献指南

### 开发流程
1. Fork 项目到个人仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交变更 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

### 代码规范
- 遵循 PEP 8 Python 代码规范
- 使用 Black 进行代码格式化
- 编写完整的类型注解
- 添加详细的文档字符串
- 保持测试覆盖率 > 80%

### 提交规范
使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：
- `feat:` 新功能
- `fix:` 错误修复
- `docs:` 文档更新
- `style:` 代码格式调整
- `refactor:` 代码重构
- `test:` 测试相关
- `chore:` 构建过程或辅助工具的变动

## 📄 许可证

本项目采用 GPL-3.0 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

### 许可证说明
本项目使用 GPL-3.0 许可证，主要原因是集成了以下组件：
- **Neo4j**: 图数据库，采用 GPL-3.0 许可证
- **Weaviate**: 向量数据库，采用 BSD-3-Clause 许可证（与 GPL-3.0 兼容）

根据 GPL-3.0 的要求，任何基于本项目的衍生作品也必须采用 GPL-3.0 或兼容的许可证开源。

## 🙋‍♂️ 支持

### 文档
- [API 文档](http://localhost:8000/docs)
- [架构设计](docs/architecture.md)
- [部署指南](docs/deployment.md)
- [开发指南](docs/development.md)

### 社区
- [GitHub Issues](https://github.com/your-org/knowledge-rag/issues)
- [GitHub Discussions](https://github.com/your-org/knowledge-rag/discussions)
- [Wiki](https://github.com/your-org/knowledge-rag/wiki)

### 联系方式
- 邮箱: 270428890@qq.com
- 官网: https://no_net_now.knowledge-rag.com

---

**Knowledge RAG System** - 让知识更智能，让问答更精准 🚀