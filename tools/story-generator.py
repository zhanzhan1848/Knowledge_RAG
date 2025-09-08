#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Knowledge_RAG 用户故事生成器（简化版）

基于Epic结构和故事模板自动生成符合标准的用户故事文档。
支持故事验证、质量检查和批量生成功能。

作者: Knowledge_RAG团队
创建时间: 2024
"""

import json
import os
from datetime import datetime
from pathlib import Path


class StoryGenerator:
    """用户故事生成器核心类"""

    def __init__(self, project_root: str):
        """
        初始化故事生成器

        Args:
            project_root: 项目根目录路径
        """
        self.project_root = Path(project_root)
        self.stories_dir = self.project_root / "docs" / "stories"

        # 确保目录存在
        self.stories_dir.mkdir(parents=True, exist_ok=True)

    def generate_epic1_stories(self):
        """生成Epic 1的所有用户故事"""

        return self._generate_stories_from_data(self._get_epic1_data())

    def generate_epic2_stories(self):
        """生成Epic 2的所有用户故事"""

        return self._generate_stories_from_data(self._get_epic2_data())

    def _generate_stories_from_data(self, stories_data):
        """从故事数据生成文件"""
        generated_files = []

        for story_data in stories_data:
            filepath = self.create_story_file(story_data)
            generated_files.append(filepath)
            print(f"✓ 生成故事: {filepath}")

        return generated_files

    def _get_epic1_data(self):
        """获取Epic 1的故事数据"""

        return [
            {
                "id": "1.1",
                "title_short": "project_infrastructure",
                "title_full": "项目基础架构搭建",
                "role": "系统管理员",
                "action": "建立完整的项目基础架构和开发环境",
                "benefit": "开发团队能够高效地进行后续功能开发",
                "acceptance_criteria": [
                    "创建monorepo项目结构，包含所有微服务目录",
                    "配置Docker容器化环境，支持本地开发和部署",
                    "建立CI/CD流水线，支持自动化测试和部署",
                    "配置代码质量检查工具（ESLint、Black、pytest等）",
                    "创建开发文档和README，包含环境搭建指南",
                    "配置日志系统和基础监控",
                ],
                "tasks": [
                    {
                        "name": "创建项目结构",
                        "ac_ref": "1",
                        "subtasks": [
                            "初始化Git仓库和.gitignore配置",
                            "创建微服务目录结构（api-gateway, auth-service, document-service等）",
                            "配置Python项目依赖管理（requirements.txt, pyproject.toml）",
                            "创建共享库和工具目录",
                        ],
                    },
                    {
                        "name": "配置容器化环境",
                        "ac_ref": "2",
                        "subtasks": [
                            "编写各微服务的Dockerfile",
                            "创建docker-compose.yml用于本地开发",
                            "配置开发环境的环境变量模板",
                            "设置容器网络和数据卷配置",
                        ],
                    },
                    {
                        "name": "建立CI/CD流水线",
                        "ac_ref": "3",
                        "subtasks": [
                            "配置GitHub Actions工作流",
                            "设置自动化测试流水线",
                            "配置代码覆盖率报告",
                            "设置自动化部署到测试环境",
                        ],
                    },
                ],
                "dev_notes": """**架构参考**:
- 参考docs/architecture.md中的微服务架构设计
- 遵循12-Factor App原则进行配置管理
- 使用FastAPI作为主要Web框架

**技术栈**:
- Python 3.11+
- FastAPI + Uvicorn
- Docker + Docker Compose
- PostgreSQL + Redis + Weaviate + Neo4j""",
                "testing_standards": """**测试要求**:
- 单元测试覆盖率 > 80%
- 使用pytest作为测试框架
- 集成测试使用testcontainers
- 性能测试使用locust""",
            },
            {
                "id": "1.2",
                "title_short": "api_gateway",
                "title_full": "API网关服务实现",
                "role": "后端开发者",
                "action": "实现统一的API网关服务",
                "benefit": "为所有微服务提供统一的入口和路由管理",
                "acceptance_criteria": [
                    "使用Kong或Nginx实现API网关",
                    "配置服务发现和负载均衡",
                    "实现请求路由到各个微服务",
                    "添加基础的请求日志和监控",
                    "配置CORS和基础安全策略",
                    "提供健康检查端点",
                ],
                "tasks": [
                    {
                        "name": "选择和配置网关技术",
                        "ac_ref": "1",
                        "subtasks": [
                            "评估Kong vs Nginx vs Traefik",
                            "安装和配置选定的网关",
                            "创建网关配置文件",
                            "设置网关管理界面",
                        ],
                    },
                    {
                        "name": "实现服务路由",
                        "ac_ref": "2,3",
                        "subtasks": [
                            "配置微服务注册和发现",
                            "设置路由规则和负载均衡",
                            "实现健康检查机制",
                            "配置故障转移策略",
                        ],
                    },
                ],
                "dev_notes": """**技术选择**:
- 推荐使用Kong作为API网关（功能丰富，插件生态好）
- 备选方案：Nginx + Lua脚本（轻量级）
- 服务发现：Consul或etcd""",
                "testing_standards": """**测试重点**:
- 路由正确性测试
- 负载均衡测试
- 故障转移测试
- 性能压力测试""",
            },
            {
                "id": "1.3",
                "title_short": "auth_system",
                "title_full": "用户认证和授权系统",
                "role": "用户",
                "action": "安全地注册、登录和管理我的账户",
                "benefit": "保护我的个人数据和文档安全",
                "acceptance_criteria": [
                    "实现用户注册、登录、登出功能",
                    "使用JWT token进行身份验证",
                    "实现密码加密存储和验证",
                    "添加邮箱验证功能",
                    "实现基础的角色权限管理（用户、管理员）",
                    "提供密码重置功能",
                    "添加登录失败次数限制和账户锁定",
                ],
                "tasks": [
                    {
                        "name": "实现用户管理基础功能",
                        "ac_ref": "1,3",
                        "subtasks": [
                            "设计用户数据模型",
                            "实现用户注册API",
                            "实现用户登录/登出API",
                            "添加密码哈希和验证",
                        ],
                    },
                    {
                        "name": "实现JWT认证机制",
                        "ac_ref": "2",
                        "subtasks": [
                            "配置JWT密钥和算法",
                            "实现token生成和验证",
                            "添加token刷新机制",
                            "实现认证中间件",
                        ],
                    },
                ],
                "dev_notes": """**技术实现**:
- 使用bcrypt进行密码哈希
- JWT使用RS256算法
- 邮件服务使用SendGrid或SMTP
- Redis存储会话和限流数据""",
                "testing_standards": """**测试场景**:
- 正常注册/登录流程
- 密码错误处理
- Token过期处理
- 权限验证测试""",
            },
            {
                "id": "1.4",
                "title_short": "document_storage",
                "title_full": "文档存储服务基础架构",
                "role": "系统架构师",
                "action": "建立可扩展的文档存储服务",
                "benefit": "支持大量文档的安全存储和高效访问",
                "acceptance_criteria": [
                    "配置MinIO或AWS S3作为对象存储",
                    "实现文档上传、下载、删除的基础API",
                    "添加文档元数据管理（文件名、大小、类型、上传时间）",
                    "实现文档访问权限控制",
                    "配置存储空间配额管理",
                    "添加文档备份和恢复机制",
                ],
                "tasks": [
                    {
                        "name": "配置对象存储服务",
                        "ac_ref": "1",
                        "subtasks": [
                            "部署MinIO服务器",
                            "配置存储桶和访问策略",
                            "设置存储加密",
                            "配置CDN加速（可选）",
                        ],
                    },
                    {
                        "name": "实现文档管理API",
                        "ac_ref": "2,3",
                        "subtasks": [
                            "设计文档元数据模型",
                            "实现文档上传API（支持分片上传）",
                            "实现文档下载和预览API",
                            "实现文档删除和批量操作",
                        ],
                    },
                ],
                "dev_notes": """**存储架构**:
- 主存储：MinIO集群（3节点）
- 备份存储：AWS S3或阿里云OSS
- 缓存层：Redis缓存热点文件元数据""",
                "testing_standards": """**测试重点**:
- 大文件上传测试
- 并发访问测试
- 权限验证测试
- 存储配额测试""",
            },
            {
                "id": "1.5",
                "title_short": "database_services",
                "title_full": "数据库服务初始化",
                "role": "数据库管理员",
                "action": "建立稳定可靠的数据库服务",
                "benefit": "支持系统的数据持久化需求",
                "acceptance_criteria": [
                    "配置PostgreSQL作为主数据库",
                    "配置Neo4j作为图数据库",
                    "配置Redis作为缓存和会话存储",
                    "创建数据库迁移脚本和版本管理",
                    "实现数据库连接池和性能优化",
                    "配置数据库备份和恢复策略",
                    "添加数据库监控和告警",
                ],
                "tasks": [
                    {
                        "name": "部署PostgreSQL数据库",
                        "ac_ref": "1",
                        "subtasks": [
                            "安装PostgreSQL 14+",
                            "配置数据库参数优化",
                            "创建应用数据库和用户",
                            "设置连接池（PgBouncer）",
                        ],
                    },
                    {
                        "name": "部署Neo4j图数据库",
                        "ac_ref": "2",
                        "subtasks": [
                            "安装Neo4j企业版",
                            "配置图数据库参数",
                            "创建图数据库实例",
                            "设置访问权限和安全策略",
                        ],
                    },
                ],
                "dev_notes": """**数据库架构**:
- PostgreSQL：用户数据、文档元数据、系统配置
- Neo4j：知识图谱、实体关系
- Redis：会话存储、缓存、任务队列
- Weaviate：向量存储（在Epic 2中部署）""",
                "testing_standards": """**测试内容**:
- 数据库连接测试
- 性能基准测试
- 备份恢复测试
- 故障转移测试""",
            },
        ]

    def _get_epic2_data(self):
        """获取Epic 2的故事数据"""

        return [
            {
                "id": "2.1",
                "title_short": "document_parsing",
                "title_full": "文档解析和预处理服务",
                "role": "数据工程师",
                "action": "实现多格式文档的智能解析和预处理",
                "benefit": "为后续的向量化和知识抽取提供高质量的文本数据",
                "acceptance_criteria": [
                    "支持PDF、Word、PPT、Excel、TXT等常见格式解析",
                    "实现OCR文字识别处理扫描文档和图片",
                    "提供文本清洗和格式化功能",
                    "支持文档结构识别（标题、段落、表格、图片）",
                    "实现文档元数据提取和管理",
                    "添加解析错误处理和重试机制",
                    "提供解析进度和状态反馈",
                ],
                "tasks": [
                    {
                        "name": "实现多格式文档解析",
                        "ac_ref": "1",
                        "subtasks": [
                            "集成PyPDF2/pdfplumber处理PDF文档",
                            "使用python-docx处理Word文档",
                            "集成python-pptx处理PowerPoint",
                            "使用openpyxl/pandas处理Excel文件",
                            "实现纯文本文件的编码检测和处理",
                        ],
                    },
                    {
                        "name": "集成OCR文字识别",
                        "ac_ref": "2",
                        "subtasks": [
                            "集成Tesseract OCR引擎",
                            "配置中英文OCR模型",
                            "实现图片预处理优化识别效果",
                            "添加OCR结果的后处理和校正",
                        ],
                    },
                    {
                        "name": "实现文本预处理",
                        "ac_ref": "3,4",
                        "subtasks": [
                            "实现文本清洗（去除特殊字符、格式化）",
                            "文档结构化解析（标题层级、段落分割）",
                            "表格和图片内容的结构化提取",
                            "实现文档摘要和关键信息提取",
                        ],
                    },
                ],
                "dev_notes": """**技术栈选择**:
- PDF解析: pdfplumber（更好的表格支持）
- OCR引擎: PaddleOCR（中文效果好）或Tesseract
- 文档处理: python-docx, python-pptx, openpyxl
- 图像处理: Pillow, OpenCV

**性能考虑**:
- 大文件分块处理，避免内存溢出
- 异步处理支持并发解析
- 缓存解析结果，避免重复处理""",
                "testing_standards": """**测试重点**:
- 各种格式文档的解析准确性
- OCR识别质量和速度测试
- 大文件处理的内存和性能测试
- 异常文档的错误处理测试""",
            },
            {
                "id": "2.2",
                "title_short": "vectorization_service",
                "title_full": "向量化和嵌入服务",
                "role": "AI工程师",
                "action": "实现高质量的文本向量化服务",
                "benefit": "为语义检索提供准确的向量表示",
                "acceptance_criteria": [
                    "集成预训练的中英文嵌入模型（如BGE、OpenAI Embedding）",
                    "实现文档分块策略（按段落、句子或固定长度）",
                    "生成文档和查询的向量表示",
                    "支持批量向量化处理",
                    "实现向量缓存机制提高效率",
                    "添加向量质量评估和监控",
                    "支持多种嵌入模型的切换和比较",
                ],
                "tasks": [
                    {
                        "name": "集成嵌入模型",
                        "ac_ref": "1",
                        "subtasks": [
                            "集成BGE中文嵌入模型",
                            "集成OpenAI text-embedding-ada-002",
                            "配置Sentence-Transformers框架",
                            "实现模型加载和推理优化",
                        ],
                    },
                    {
                        "name": "实现文档分块策略",
                        "ac_ref": "2",
                        "subtasks": [
                            "实现基于段落的智能分块",
                            "支持固定长度分块（重叠窗口）",
                            "实现语义边界感知分块",
                            "添加分块质量评估指标",
                        ],
                    },
                    {
                        "name": "构建向量化服务",
                        "ac_ref": "3,4,5",
                        "subtasks": [
                            "实现批量向量化API",
                            "添加向量缓存和存储",
                            "实现向量化任务队列",
                            "添加向量化进度跟踪",
                        ],
                    },
                ],
                "dev_notes": """**模型选择**:
- 中文: BGE-large-zh, text2vec-large-chinese
- 英文: OpenAI ada-002, sentence-transformers/all-MiniLM-L6-v2
- 多语言: multilingual-e5-large

**优化策略**:
- GPU加速推理
- 模型量化减少内存占用
- 批处理提高吞吐量""",
                "testing_standards": """**测试内容**:
- 向量质量评估（相似性测试）
- 不同分块策略的效果对比
- 批量处理的性能基准测试
- 缓存命中率和效果测试""",
            },
            {
                "id": "2.3",
                "title_short": "vector_database",
                "title_full": "向量数据库集成",
                "role": "系统架构师",
                "action": "集成高性能的向量数据库",
                "benefit": "支持大规模向量的存储和快速相似性搜索",
                "acceptance_criteria": [
                    "集成Weaviate或Qdrant向量数据库",
                    "实现向量的增删改查操作",
                    "配置向量索引和搜索参数优化",
                    "实现相似性搜索和混合搜索",
                    "支持向量数据的备份和恢复",
                    "添加搜索性能监控和调优",
                    "实现向量数据库的水平扩展",
                ],
                "tasks": [
                    {
                        "name": "部署向量数据库",
                        "ac_ref": "1",
                        "subtasks": [
                            "评估Weaviate vs Qdrant vs Milvus",
                            "部署选定的向量数据库集群",
                            "配置数据库连接和认证",
                            "设置数据库备份策略",
                        ],
                    },
                    {
                        "name": "实现向量操作API",
                        "ac_ref": "2,3",
                        "subtasks": [
                            "实现向量插入和批量导入",
                            "实现向量更新和删除操作",
                            "配置向量索引（HNSW、IVF等）",
                            "实现向量搜索和过滤功能",
                        ],
                    },
                    {
                        "name": "优化搜索性能",
                        "ac_ref": "4,6",
                        "subtasks": [
                            "实现混合搜索（向量+关键词）",
                            "配置搜索参数调优",
                            "添加搜索性能监控",
                            "实现搜索结果缓存",
                        ],
                    },
                ],
                "dev_notes": """**技术选择**:
- 推荐Weaviate（功能丰富，GraphQL支持）
- 备选Qdrant（性能优秀，Rust实现）
- 索引算法：HNSW（平衡精度和速度）

**扩展策略**:
- 分片存储支持水平扩展
- 读写分离提高并发性能""",
                "testing_standards": """**性能指标**:
- 搜索延迟 < 100ms（P95）
- 吞吐量 > 1000 QPS
- 索引构建时间测试
- 内存使用效率评估""",
            },
            {
                "id": "2.4",
                "title_short": "entity_extraction",
                "title_full": "实体识别和关系抽取",
                "role": "知识工程师",
                "action": "从文档中自动识别实体和关系",
                "benefit": "构建结构化的知识图谱",
                "acceptance_criteria": [
                    "实现命名实体识别（人名、地名、机构、概念等）",
                    "抽取实体间的语义关系",
                    "支持领域特定的实体类型定制",
                    "实现实体链接和消歧",
                    "提供实体和关系的置信度评分",
                    "支持多语言实体识别",
                    "添加人工标注和模型训练接口",
                ],
                "tasks": [
                    {
                        "name": "实现命名实体识别",
                        "ac_ref": "1,6",
                        "subtasks": [
                            "集成spaCy中英文NER模型",
                            "集成BERT-based NER模型",
                            "实现自定义实体类型识别",
                            "添加实体识别后处理和过滤",
                        ],
                    },
                    {
                        "name": "实现关系抽取",
                        "ac_ref": "2,5",
                        "subtasks": [
                            "实现基于规则的关系抽取",
                            "集成深度学习关系抽取模型",
                            "实现关系类型分类",
                            "添加关系置信度评估",
                        ],
                    },
                    {
                        "name": "实现实体链接",
                        "ac_ref": "3,4",
                        "subtasks": [
                            "构建实体知识库",
                            "实现实体消歧算法",
                            "添加实体标准化处理",
                            "实现实体合并和去重",
                        ],
                    },
                ],
                "dev_notes": """**技术栈**:
- NER: spaCy, transformers (BERT-NER)
- 关系抽取: OpenIE, DeepKE
- 实体链接: 基于相似度的匹配算法

**模型选择**:
- 中文NER: BERT-base-chinese-ner
- 英文NER: en_core_web_sm (spaCy)
- 关系抽取: 预训练RE模型 + 规则增强""",
                "testing_standards": """**评估指标**:
- NER准确率、召回率、F1分数
- 关系抽取的精确度评估
- 实体链接的准确性测试
- 处理速度和内存使用评估""",
            },
            {
                "id": "2.5",
                "title_short": "knowledge_graph",
                "title_full": "知识图谱构建和存储",
                "role": "数据科学家",
                "action": "将抽取的实体和关系构建成知识图谱",
                "benefit": "支持复杂的关系查询和推理",
                "acceptance_criteria": [
                    "在Neo4j中创建实体节点和关系边",
                    "实现图谱的增量更新和版本管理",
                    "建立实体属性和关系类型的本体结构",
                    "实现图谱数据的去重和融合",
                    "提供图谱统计信息和质量评估",
                    "支持图谱的导入导出功能",
                    "实现图谱数据的备份和恢复",
                ],
                "tasks": [
                    {
                        "name": "设计图谱数据模型",
                        "ac_ref": "1,3",
                        "subtasks": [
                            "设计实体节点的属性结构",
                            "定义关系类型和属性",
                            "建立本体和模式约束",
                            "创建索引优化查询性能",
                        ],
                    },
                    {
                        "name": "实现图谱构建",
                        "ac_ref": "2,4",
                        "subtasks": [
                            "实现实体节点的创建和更新",
                            "实现关系边的建立和维护",
                            "添加图谱增量更新机制",
                            "实现实体去重和合并算法",
                        ],
                    },
                    {
                        "name": "图谱质量管理",
                        "ac_ref": "5,6,7",
                        "subtasks": [
                            "实现图谱统计和质量指标",
                            "添加图谱导入导出功能",
                            "配置图谱备份和恢复",
                            "实现图谱版本管理",
                        ],
                    },
                ],
                "dev_notes": """**图谱设计**:
- 节点类型: Person, Organization, Location, Concept, Document
- 关系类型: WORKS_FOR, LOCATED_IN, MENTIONS, RELATED_TO
- 属性: name, type, confidence, source, timestamp

**性能优化**:
- 创建适当的索引（name, type等）
- 使用批量操作提高写入性能
- 实现图谱分区存储""",
                "testing_standards": """**质量指标**:
- 图谱完整性检查
- 实体去重效果评估
- 关系一致性验证
- 查询性能基准测试""",
            },
        ]

    def _get_epic3_data(self):
        """获取Epic 3的故事数据"""

        return [
            {
                "id": "3.1",
                "title_short": "graphrag_engine",
                "title_full": "GraphRAG核心引擎开发",
                "role": "AI架构师",
                "action": "实现基于知识图谱的检索增强生成引擎",
                "benefit": "提供准确、可解释的智能问答能力",
                "acceptance_criteria": [
                    "实现图谱遍历和子图提取算法",
                    "集成向量检索和图谱检索的混合策略",
                    "实现上下文窗口管理和信息压缩",
                    "支持多跳推理和关系链路追踪",
                    "提供检索结果的相关性评分",
                    "实现检索缓存和性能优化",
                    "添加检索过程的可视化和调试功能",
                ],
                "tasks": [
                    {
                        "name": "实现图谱检索算法",
                        "ac_ref": "1,4",
                        "subtasks": [
                            "实现基于实体的子图提取",
                            "开发关系路径搜索算法",
                            "实现多跳邻居节点遍历",
                            "添加图谱检索的深度和广度控制",
                        ],
                    },
                    {
                        "name": "构建混合检索策略",
                        "ac_ref": "2,5",
                        "subtasks": [
                            "实现向量相似性检索",
                            "集成图谱结构化检索",
                            "开发检索结果融合算法",
                            "实现相关性评分机制",
                        ],
                    },
                    {
                        "name": "优化上下文管理",
                        "ac_ref": "3,6",
                        "subtasks": [
                            "实现动态上下文窗口管理",
                            "开发信息压缩和摘要算法",
                            "添加检索结果缓存机制",
                            "实现检索性能监控",
                        ],
                    },
                ],
                "dev_notes": """**核心算法**:
- 图遍历: BFS/DFS + 启发式剪枝
- 子图提取: 基于中心性和相关性的节点选择
- 混合检索: 向量相似度 + 图结构相似度

**性能优化**:
- 图索引: 预计算常用路径和邻接关系
- 缓存策略: LRU缓存检索结果
- 并行处理: 多线程图遍历""",
                "testing_standards": """**测试重点**:
- 检索准确性和召回率测试
- 多跳推理的正确性验证
- 检索性能和延迟基准测试
- 大规模图谱的扩展性测试""",
            },
            {
                "id": "3.2",
                "title_short": "llm_integration",
                "title_full": "大语言模型集成服务",
                "role": "AI工程师",
                "action": "集成多种大语言模型提供生成能力",
                "benefit": "支持高质量的自然语言生成和推理",
                "acceptance_criteria": [
                    "集成OpenAI GPT、Claude、国产大模型等多种LLM",
                    "实现模型切换和负载均衡",
                    "支持流式输出和实时响应",
                    "实现prompt工程和模板管理",
                    "添加模型调用的监控和限流",
                    "支持模型微调和适配",
                    "实现生成质量评估和优化",
                ],
                "tasks": [
                    {
                        "name": "集成多种LLM",
                        "ac_ref": "1,2",
                        "subtasks": [
                            "集成OpenAI GPT-4/GPT-3.5 API",
                            "集成Anthropic Claude API",
                            "集成国产大模型（如文心一言、通义千问）",
                            "实现统一的模型调用接口",
                        ],
                    },
                    {
                        "name": "实现模型管理",
                        "ac_ref": "3,4,5",
                        "subtasks": [
                            "开发模型选择和路由策略",
                            "实现流式输出处理",
                            "构建prompt模板管理系统",
                            "添加API调用监控和限流",
                        ],
                    },
                    {
                        "name": "优化生成质量",
                        "ac_ref": "6,7",
                        "subtasks": [
                            "实现模型微调接口",
                            "开发生成质量评估指标",
                            "添加输出后处理和优化",
                            "实现A/B测试框架",
                        ],
                    },
                ],
                "dev_notes": """**模型选择策略**:
- 通用任务: GPT-4 (高质量) / GPT-3.5 (高性能)
- 中文优化: 文心一言、通义千问
- 代码生成: GitHub Copilot, CodeT5

**性能考虑**:
- 异步调用减少延迟
- 连接池管理API连接
- 智能缓存减少重复调用""",
                "testing_standards": """**评估指标**:
- 生成质量: BLEU, ROUGE, 人工评估
- 响应速度: 平均延迟、P95延迟
- 可用性: API成功率、错误处理
- 成本效益: 每次调用成本分析""",
            },
            {
                "id": "3.3",
                "title_short": "qa_api",
                "title_full": "问答API接口开发",
                "role": "后端工程师",
                "action": "开发RESTful问答API接口",
                "benefit": "为前端和第三方应用提供标准化的问答服务",
                "acceptance_criteria": [
                    "实现问答API的RESTful接口设计",
                    "支持同步和异步问答模式",
                    "提供问答历史和会话管理",
                    "实现API认证和权限控制",
                    "添加请求限流和防护机制",
                    "支持批量问答和并发处理",
                    "提供详细的API文档和SDK",
                ],
                "tasks": [
                    {
                        "name": "设计API接口",
                        "ac_ref": "1,2",
                        "subtasks": [
                            "设计RESTful API规范",
                            "实现同步问答接口",
                            "开发异步问答和轮询接口",
                            "添加WebSocket实时通信支持",
                        ],
                    },
                    {
                        "name": "实现会话管理",
                        "ac_ref": "3,6",
                        "subtasks": [
                            "开发会话创建和管理",
                            "实现问答历史存储",
                            "添加批量问答处理",
                            "实现并发请求控制",
                        ],
                    },
                    {
                        "name": "安全和文档",
                        "ac_ref": "4,5,7",
                        "subtasks": [
                            "实现JWT认证和权限控制",
                            "添加API限流和防护",
                            "编写API文档和示例",
                            "开发Python/JavaScript SDK",
                        ],
                    },
                ],
                "dev_notes": """**API设计原则**:
- RESTful风格，语义化URL
- 统一的响应格式和错误码
- 支持分页和过滤参数
- 版本控制和向后兼容

**技术栈**:
- 框架: FastAPI (高性能异步)
- 认证: JWT + OAuth2
- 文档: OpenAPI/Swagger自动生成""",
                "testing_standards": """**测试内容**:
- API功能测试和集成测试
- 并发性能和压力测试
- 安全性和权限测试
- API文档的准确性验证""",
            },
            {
                "id": "3.4",
                "title_short": "context_management",
                "title_full": "上下文管理系统",
                "role": "系统设计师",
                "action": "实现智能的对话上下文管理",
                "benefit": "支持多轮对话和上下文感知的问答",
                "acceptance_criteria": [
                    "实现对话状态跟踪和管理",
                    "支持多轮对话的上下文保持",
                    "实现上下文相关性评估",
                    "支持上下文压缩和摘要",
                    "添加上下文冲突检测和解决",
                    "实现个性化上下文适配",
                    "提供上下文分析和可视化",
                ],
                "tasks": [
                    {
                        "name": "实现对话状态管理",
                        "ac_ref": "1,2",
                        "subtasks": [
                            "设计对话状态数据结构",
                            "实现多轮对话跟踪",
                            "开发上下文继承机制",
                            "添加对话分支和合并",
                        ],
                    },
                    {
                        "name": "上下文智能处理",
                        "ac_ref": "3,4,5",
                        "subtasks": [
                            "实现上下文相关性评分",
                            "开发上下文压缩算法",
                            "添加冲突检测和解决",
                            "实现上下文自动摘要",
                        ],
                    },
                    {
                        "name": "个性化和分析",
                        "ac_ref": "6,7",
                        "subtasks": [
                            "实现用户画像和偏好学习",
                            "开发个性化上下文适配",
                            "添加上下文分析工具",
                            "实现上下文可视化界面",
                        ],
                    },
                ],
                "dev_notes": """**核心算法**:
- 相关性评估: 基于语义相似度和时间衰减
- 上下文压缩: 关键信息提取 + 摘要生成
- 冲突解决: 基于置信度和时间戳的优先级

**存储策略**:
- 短期上下文: Redis (快速访问)
- 长期上下文: PostgreSQL (持久化)
- 上下文索引: Elasticsearch (快速检索)""",
                "testing_standards": """**测试重点**:
- 多轮对话的上下文一致性
- 上下文压缩的信息保留率
- 个性化适配的效果评估
- 系统性能和内存使用""",
            },
            {
                "id": "3.5",
                "title_short": "answer_quality",
                "title_full": "答案质量评估系统",
                "role": "质量工程师",
                "action": "实现自动化的答案质量评估和优化",
                "benefit": "确保问答系统输出的准确性和可靠性",
                "acceptance_criteria": [
                    "实现答案准确性自动评估",
                    "支持多维度质量指标评估",
                    "提供答案可信度评分",
                    "实现答案来源追溯和引用",
                    "添加质量异常检测和告警",
                    "支持人工标注和反馈收集",
                    "实现质量报告和分析dashboard",
                ],
                "tasks": [
                    {
                        "name": "实现质量评估算法",
                        "ac_ref": "1,2,3",
                        "subtasks": [
                            "开发答案准确性评估模型",
                            "实现多维度质量指标",
                            "构建可信度评分算法",
                            "添加答案一致性检查",
                        ],
                    },
                    {
                        "name": "构建追溯和监控",
                        "ac_ref": "4,5",
                        "subtasks": [
                            "实现答案来源追溯",
                            "开发引用和证据链接",
                            "添加质量异常检测",
                            "实现实时质量监控",
                        ],
                    },
                    {
                        "name": "人工反馈和分析",
                        "ac_ref": "6,7",
                        "subtasks": [
                            "构建人工标注平台",
                            "实现用户反馈收集",
                            "开发质量分析dashboard",
                            "添加质量趋势报告",
                        ],
                    },
                ],
                "dev_notes": """**评估维度**:
- 准确性: 事实正确性、逻辑一致性
- 完整性: 信息覆盖度、细节丰富度
- 相关性: 问题匹配度、上下文适配
- 可读性: 语言流畅度、结构清晰度

**技术实现**:
- 评估模型: BERT-based分类器
- 相似度计算: 语义向量相似度
- 异常检测: 统计方法 + 机器学习""",
                "testing_standards": """**验证方法**:
- 人工评估与自动评估的一致性
- 不同质量指标的相关性分析
- 质量评估的稳定性和可重复性
- 异常检测的准确率和召回率""",
            },
        ]

    def _get_epic4_data(self):
        """获取Epic 4的故事数据 - API接口和服务集成"""
        return [
            {
                "id": "4.1",
                "filename": "restful_api_design.md",
                "title": "RESTful API接口设计",
                "title_short": "restful_api_design",
                "title_full": "RESTful API接口设计 - 标准化接口规范与文档",
                "role": "开发者",
                "action": "使用标准化的RESTful API接口",
                "benefit": "能够高效地集成和使用系统功能",
                "acceptance_criteria": [
                    "实现标准RESTful API设计规范",
                    "集成OpenAPI 3.0规范和自动文档生成",
                    "实现统一的错误处理和状态码",
                    "添加API版本控制和向后兼容",
                    "实现请求参数验证和响应格式标准化",
                    "优化API性能和响应时间",
                    "添加API安全认证和权限控制",
                ],
                "tasks": [
                    {
                        "name": "设计API接口规范",
                        "acceptance_criteria": [1, 7],
                        "subtasks": [
                            "定义RESTful资源和HTTP方法映射",
                            "设计统一的URL路径和命名规范",
                            "实现JWT认证和权限中间件",
                            "添加API限流和安全防护机制",
                        ],
                    },
                    {
                        "name": "构建API文档系统",
                        "acceptance_criteria": [2, 4],
                        "subtasks": [
                            "集成Swagger/OpenAPI文档生成",
                            "实现API版本控制策略",
                            "创建交互式API测试界面",
                            "设计API使用示例和SDK",
                        ],
                    },
                    {
                        "name": "实现数据验证和格式化",
                        "acceptance_criteria": [3, 5],
                        "subtasks": [
                            "开发请求参数验证中间件",
                            "实现统一的响应格式标准",
                            "添加数据类型检查和转换",
                            "创建错误码和错误信息规范",
                        ],
                    },
                    {
                        "name": "性能优化和监控",
                        "acceptance_criteria": [6],
                        "subtasks": [
                            "实现API响应缓存策略",
                            "优化数据库查询和连接池",
                            "添加API性能监控和日志",
                            "进行跨浏览器兼容性测试",
                        ],
                    },
                ],
                "dev_notes": {
                    "技术栈": "Python + FastAPI + Pydantic + SQLAlchemy",
                    "API规范": "OpenAPI 3.0 + JWT认证 + 限流控制",
                    "性能目标": "API响应 < 200ms, 并发支持 > 1000 QPS",
                },
            },
            {
                "id": "4.2",
                "filename": "document_management_api.md",
                "title": "文档管理API服务",
                "title_short": "document_management_api",
                "title_full": "文档管理API服务 - 上传存储与元数据管理",
                "role": "开发者",
                "action": "通过API管理和操作文档",
                "benefit": "能够高效地集成文档管理功能",
                "acceptance_criteria": [
                    "实现文档上传和批量处理API",
                    "提供文档元数据查询和管理接口",
                    "支持文档分类、标签和搜索API",
                    "实现文档版本管理和历史记录接口",
                    "添加文档权限控制和访问管理API",
                    "优化大文件处理和异步任务接口",
                    "实现文档内容检索和全文搜索API",
                ],
                "tasks": [
                    {
                        "name": "开发文档上传API",
                        "acceptance_criteria": [1, 6],
                        "subtasks": [
                            "实现多文件上传和分片上传接口",
                            "添加上传进度查询和状态管理",
                            "支持文件类型验证和大小限制",
                            "实现异步文档处理任务队列",
                        ],
                    },
                    {
                        "name": "构建文档元数据API",
                        "acceptance_criteria": [2, 7],
                        "subtasks": [
                            "设计文档元数据模型和存储结构",
                            "实现文档信息CRUD操作接口",
                            "添加文档内容提取和索引API",
                            "创建全文搜索和语义检索接口",
                        ],
                    },
                    {
                        "name": "实现文档组织API",
                        "acceptance_criteria": [3, 4],
                        "subtasks": [
                            "开发文档分类和标签管理接口",
                            "实现文档版本控制和历史API",
                            "添加文档关系和依赖管理",
                            "创建高级查询和过滤接口",
                        ],
                    },
                    {
                        "name": "添加权限和安全API",
                        "acceptance_criteria": [5],
                        "subtasks": [
                            "实现文档访问权限控制接口",
                            "添加用户和角色管理API",
                            "支持文档分享和临时访问令牌",
                            "实现审计日志和操作记录API",
                        ],
                    },
                ],
                "dev_notes": {
                    "文件处理": "异步任务队列 + 分片存储 + CDN集成",
                    "数据存储": "PostgreSQL + MinIO + Redis缓存",
                    "安全策略": "JWT认证 + RBAC权限 + API限流",
                },
            },
            {
                "id": "4.3",
                "filename": "search_api.md",
                "title": "智能搜索API服务",
                "title_short": "search_api",
                "title_full": "智能搜索API服务 - 实时搜索与语义检索",
                "role": "开发者",
                "action": "通过API实现强大的搜索功能",
                "benefit": "能够为各种客户端提供统一的搜索服务",
                "acceptance_criteria": [
                    "实现实时搜索建议和自动补全API",
                    "支持高级搜索语法和过滤器接口",
                    "提供搜索结果的多维度排序API",
                    "实现搜索历史和用户偏好接口",
                    "添加语义搜索和相关推荐API",
                    "优化搜索性能和响应速度",
                    "支持多语言搜索和国际化API",
                ],
                "tasks": [
                    {
                        "name": "开发智能搜索API",
                        "acceptance_criteria": [1, 4],
                        "subtasks": [
                            "实现搜索建议和自动补全接口",
                            "添加搜索历史管理API",
                            "支持多模态搜索输入接口",
                            "实现搜索配置和个性化API",
                        ],
                    },
                    {
                        "name": "构建高级搜索接口",
                        "acceptance_criteria": [2, 3],
                        "subtasks": [
                            "实现复杂查询语法解析API",
                            "添加多维度过滤器接口",
                            "支持多种排序算法API",
                            "创建搜索结果聚合接口",
                        ],
                    },
                    {
                        "name": "实现语义搜索API",
                        "acceptance_criteria": [5, 7],
                        "subtasks": [
                            "集成向量搜索引擎接口",
                            "实现相关文档推荐API",
                            "添加多语言搜索支持接口",
                            "优化搜索结果相关性算法",
                        ],
                    },
                    {
                        "name": "性能优化和监控",
                        "acceptance_criteria": [6],
                        "subtasks": [
                            "实现搜索结果分页和流式返回",
                            "添加搜索性能监控接口",
                            "优化搜索请求缓存策略",
                            "实现搜索负载均衡和限流",
                        ],
                    },
                ],
                "dev_notes": {
                    "搜索引擎": "Elasticsearch + 向量数据库 + 全文检索",
                    "API优化": "缓存策略 + 异步处理 + 负载均衡",
                    "服务架构": "微服务 + 消息队列 + 实时索引",
                },
            },
            {
                "id": "4.4",
                "filename": "chat_api.md",
                "title": "智能对话API服务",
                "title_short": "chat_api",
                "title_full": "智能对话API服务 - 多模态支持与会话管理",
                "role": "开发者",
                "action": "通过API实现自然对话功能",
                "benefit": "能够为各种客户端提供智能对话服务",
                "acceptance_criteria": [
                    "实现流式对话和实时响应API",
                    "支持多模态消息和富文本接口",
                    "提供对话历史和会话管理API",
                    "实现消息搜索和引用功能接口",
                    "添加语音处理和转换API",
                    "优化API性能和并发处理",
                    "支持多轮对话和上下文理解API",
                ],
                "tasks": [
                    {
                        "name": "开发对话核心API",
                        "acceptance_criteria": [1, 6],
                        "subtasks": [
                            "实现消息发送和接收接口",
                            "添加流式响应和WebSocket支持",
                            "支持消息状态和进度查询",
                            "优化API并发处理和负载均衡",
                        ],
                    },
                    {
                        "name": "实现多模态支持API",
                        "acceptance_criteria": [2, 5],
                        "subtasks": [
                            "支持图片、文件上传和处理接口",
                            "实现富文本和Markdown解析API",
                            "添加语音识别和合成接口",
                            "集成多模态内容理解服务",
                        ],
                    },
                    {
                        "name": "构建会话管理API",
                        "acceptance_criteria": [3, 4],
                        "subtasks": [
                            "实现会话CRUD操作接口",
                            "添加消息搜索和过滤API",
                            "支持消息引用和回复接口",
                            "创建会话导出和数据同步API",
                        ],
                    },
                    {
                        "name": "优化对话服务",
                        "acceptance_criteria": [7],
                        "subtasks": [
                            "实现上下文感知和记忆管理",
                            "添加对话模板和预设回复",
                            "支持消息编辑和撤回API",
                            "优化长对话的存储和检索",
                        ],
                    },
                ],
                "dev_notes": {
                    "实时通信": "WebSocket + Server-Sent Events + 消息队列",
                    "数据存储": "MongoDB + Redis缓存 + 会话持久化",
                    "语音处理": "语音识别API + TTS服务 + 音频转码",
                },
            },
            {
                "id": "4.5",
                "filename": "knowledge_graph_api.md",
                "title": "知识图谱API服务",
                "title_short": "knowledge_graph_api",
                "title_full": "知识图谱API服务 - 图数据管理与分析接口",
                "role": "开发者",
                "action": "通过API管理和查询知识图谱",
                "benefit": "能够为各种应用提供图数据服务",
                "acceptance_criteria": [
                    "实现图谱节点和边的CRUD操作API",
                    "支持图谱查询和遍历接口",
                    "提供节点详情和关系信息API",
                    "实现图谱搜索和路径查找接口",
                    "添加图谱分析算法和统计API",
                    "优化大规模图谱的查询性能",
                    "支持图谱数据的导入导出API",
                ],
                "tasks": [
                    {
                        "name": "构建图数据管理API",
                        "acceptance_criteria": [1, 6],
                        "subtasks": [
                            "实现节点和边的增删改查接口",
                            "添加批量操作和事务支持",
                            "支持图数据验证和约束检查",
                            "优化大规模数据的写入性能",
                        ],
                    },
                    {
                        "name": "实现图查询接口",
                        "acceptance_criteria": [2, 3],
                        "subtasks": [
                            "支持Cypher或GraphQL查询语言",
                            "实现图遍历和邻居查询API",
                            "添加条件过滤和分页支持",
                            "创建实体关系详情查询接口",
                        ],
                    },
                    {
                        "name": "开发图分析API",
                        "acceptance_criteria": [4, 5],
                        "subtasks": [
                            "实现最短路径和路径查找算法",
                            "添加中心性和社区检测分析",
                            "支持图统计和度量计算",
                            "创建自定义分析算法接口",
                        ],
                    },
                    {
                        "name": "添加数据交换API",
                        "acceptance_criteria": [7],
                        "subtasks": [
                            "支持多种格式的数据导入导出",
                            "实现增量同步和备份接口",
                            "添加数据转换和映射服务",
                            "创建图数据版本管理API",
                        ],
                    },
                ],
                "dev_notes": {
                    "图数据库": "Neo4j + ArangoDB + 自定义图存储",
                    "性能优化": "索引优化 + 查询缓存 + 分布式存储",
                    "查询引擎": "Cypher + GraphQL + 自定义DSL",
                },
            },
        ]

    def create_story_file(self, story_data):
        """创建单个故事文件"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 生成文件名
        filename = f"{story_data['id']}.{story_data['title_short']}.md"
        filepath = self.stories_dir / filename

        # 生成Markdown内容
        content = f"""# Story {story_data['id']}: {story_data['title_full']}

## Status
Draft

## Story
**As a** {story_data['role']},  
**I want** {story_data['action']},  
**so that** {story_data['benefit']}

## Acceptance Criteria
"""

        # 添加验收标准
        for i, criteria in enumerate(story_data["acceptance_criteria"], 1):
            content += f"{i}. {criteria}\n"

        content += "\n## Tasks / Subtasks\n"

        # 添加任务和子任务
        for task in story_data["tasks"]:
            task_name = task["name"]
            ac_ref = task.get("ac_ref", "")
            ac_text = f" (AC: {ac_ref})" if ac_ref else ""
            content += f"- [ ] {task_name}{ac_text}\n"

            # 添加子任务
            for subtask in task.get("subtasks", []):
                content += f"  - [ ] {subtask}\n"

        content += f"""\n## Dev Notes
{story_data['dev_notes']}

### Testing
{story_data['testing_standards']}

## Change Log
| Date | Version | Description | Author |
|------|---------|-------------|--------|
| {timestamp} | 1.0 | Initial story creation | Story Generator |

## Dev Agent Record
*This section will be populated by the development agent during implementation*

### Agent Model Used
*TBD*

### Debug Log References
*TBD*

### Completion Notes List
*TBD*

### File List
*TBD*

## QA Results
*Results from QA Agent review will be added here*
"""

        # 写入文件
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        return str(filepath)


class StoryValidator:
    """用户故事验证器"""

    def __init__(self):
        self.validation_criteria = {
            "goal_context_clarity": "目标和上下文清晰度",
            "technical_guidance": "技术实施指导",
            "reference_effectiveness": "引用有效性",
            "self_containment": "自包含性评估",
            "testing_guidance": "测试指导",
        }

    def validate_story(self, story_path):
        """验证单个用户故事"""
        try:
            with open(story_path, "r", encoding="utf-8") as f:
                content = f.read()
        except FileNotFoundError:
            return {"error": f"故事文件未找到: {story_path}"}

        # 简化的验证逻辑
        issues = []

        # 检查基本结构
        required_sections = [
            "## Story",
            "## Acceptance Criteria",
            "## Tasks / Subtasks",
            "## Dev Notes",
        ]
        for section in required_sections:
            if section not in content:
                issues.append(f"缺少必需部分: {section}")

        # 检查故事格式
        if (
            "**As a**" not in content
            or "**I want**" not in content
            or "**so that**" not in content
        ):
            issues.append("故事格式不完整，缺少标准的用户故事结构")

        # 检查验收标准
        ac_lines = [
            line for line in content.split("\n") if line.strip() and line[0].isdigit()
        ]
        if len(ac_lines) < 3:
            issues.append("验收标准数量不足，建议至少3个")

        status = (
            "READY"
            if len(issues) == 0
            else "NEEDS REVISION" if len(issues) <= 2 else "BLOCKED"
        )
        clarity_score = max(1, 10 - len(issues) * 2)

        return {
            "story_path": story_path,
            "overall_status": status,
            "clarity_score": clarity_score,
            "issues": issues,
        }

    def generate_validation_report(self, validation_results):
        """生成验证报告"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        report = f"""# 用户故事验证报告

**生成时间**: {timestamp}  
**验证故事数量**: {len(validation_results)}

## 验证摘要

"""

        ready_count = sum(
            1 for r in validation_results if r.get("overall_status") == "READY"
        )
        needs_revision_count = sum(
            1 for r in validation_results if r.get("overall_status") == "NEEDS REVISION"
        )
        blocked_count = sum(
            1 for r in validation_results if r.get("overall_status") == "BLOCKED"
        )

        report += f"- ✅ 准备就绪: {ready_count}\n"
        report += f"- ⚠️ 需要修订: {needs_revision_count}\n"
        report += f"- 🚫 阻塞状态: {blocked_count}\n\n"

        # 详细结果
        report += "## 详细验证结果\n\n"

        for result in validation_results:
            if "error" in result:
                continue

            story_name = Path(result["story_path"]).name
            status_icon = {"READY": "✅", "NEEDS REVISION": "⚠️", "BLOCKED": "🚫"}.get(
                result["overall_status"], "❓"
            )

            report += f"### {status_icon} {story_name}\n\n"
            report += f"**状态**: {result['overall_status']}  \n"
            report += f"**清晰度评分**: {result['clarity_score']}/10\n\n"

            if result.get("issues"):
                report += "**问题列表**:\n"
                for issue in result["issues"]:
                    report += f"- {issue}\n"
                report += "\n"

        return report


def main(epic_number=1):
    """主函数"""
    project_root = "/Users/zhanyuanwei/Desktop/Knowledge_RAG"

    print("Knowledge_RAG 用户故事生成器")
    print("=" * 40)

    # 创建生成器和验证器
    generator = StoryGenerator(project_root)
    validator = StoryValidator()

    print(f"项目根目录: {project_root}")
    print(f"故事目录: {generator.stories_dir}")
    print()

    # 根据参数生成对应Epic的故事
    if epic_number == 1:
        print("正在生成Epic 1的用户故事...")
        generated_files = generator.generate_epic1_stories()
        report_name = "epic1-story-validation-report.md"
        epic_name = "Epic 1"
    elif epic_number == 2:
        print("正在生成Epic 2的用户故事...")
        generated_files = generator.generate_epic2_stories()
        report_name = "epic2-story-validation-report.md"
        epic_name = "Epic 2"
    elif epic_number == 3:
        print("正在生成Epic 3的用户故事...")
        generated_files = generator._generate_stories_from_data(
            generator._get_epic3_data()
        )
        report_name = "epic3-story-validation-report.md"
        epic_name = "Epic 3"
    elif epic_number == 4:
        print("正在生成Epic 4的用户故事...")
        generated_files = generator._generate_stories_from_data(
            generator._get_epic4_data()
        )
        report_name = "epic4-story-validation-report.md"
        epic_name = "Epic 4"
    else:
        print(f"❌ 不支持的Epic编号: {epic_number}")
        return

    print(f"\n✅ 成功生成 {len(generated_files)} 个故事文件")

    # 验证生成的故事
    print("\n正在验证生成的故事...")
    validation_results = []
    for filepath in generated_files:
        result = validator.validate_story(filepath)
        validation_results.append(result)

        if "error" not in result:
            status_icon = {"READY": "✅", "NEEDS REVISION": "⚠️", "BLOCKED": "🚫"}.get(
                result["overall_status"], "❓"
            )
            print(
                f"  {status_icon} {Path(filepath).name} - {result['overall_status']} (评分: {result['clarity_score']}/10)"
            )

    # 生成验证报告
    report = validator.generate_validation_report(validation_results)
    report_path = Path(project_root) / "docs" / report_name

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\n📋 验证报告已保存: {report_path}")

    # 统计信息
    ready_count = sum(
        1 for r in validation_results if r.get("overall_status") == "READY"
    )
    total_count = len([r for r in validation_results if "error" not in r])

    print(f"\n📊 验证统计:")
    print(f"   总故事数: {total_count}")
    print(f"   准备就绪: {ready_count}")
    print(
        f"   成功率: {ready_count/total_count*100:.1f}%"
        if total_count > 0
        else "   成功率: 0%"
    )

    print(f"\n🎉 {epic_name} 用户故事生成和验证完成！")


if __name__ == "__main__":
    import sys

    # 解析命令行参数
    epic_number = 1  # 默认值
    if len(sys.argv) > 1:
        for i, arg in enumerate(sys.argv):
            if arg == "--epic" and i + 1 < len(sys.argv):
                try:
                    epic_number = int(sys.argv[i + 1])
                except ValueError:
                    print(f"❌ 无效的Epic编号: {sys.argv[i + 1]}")
                    sys.exit(1)
                break

    main(epic_number)
