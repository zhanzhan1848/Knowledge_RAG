# Knowledge RAG System - 测试配置文件
# 包含 pytest 的全局配置和 fixtures

import os
import sys
import asyncio
import pytest
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 测试环境配置
os.environ.setdefault("ENVIRONMENT", "testing")
os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://postgres:postgres123@localhost:5432/test_db"
)
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("JWT_SECRET_KEY", "test_jwt_secret_key_for_testing_only")
os.environ.setdefault("OPENAI_API_KEY", "test_openai_key")
os.environ.setdefault("LOG_LEVEL", "DEBUG")


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """创建事件循环用于异步测试"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def async_client():
    """创建异步 HTTP 客户端用于 API 测试"""
    from httpx import AsyncClient

    async with AsyncClient() as client:
        yield client


@pytest.fixture
def mock_database():
    """模拟数据库连接"""
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock()
    mock_db.fetch = AsyncMock()
    mock_db.fetchrow = AsyncMock()
    mock_db.fetchval = AsyncMock()
    return mock_db


@pytest.fixture
def mock_redis():
    """模拟 Redis 连接"""
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock()
    mock_redis.set = AsyncMock()
    mock_redis.delete = AsyncMock()
    mock_redis.exists = AsyncMock()
    mock_redis.expire = AsyncMock()
    return mock_redis


@pytest.fixture
def mock_openai_client():
    """模拟 OpenAI 客户端"""
    mock_client = MagicMock()

    # 模拟 chat completions
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Test response from OpenAI"
    mock_client.chat.completions.create.return_value = mock_response

    # 模拟 embeddings
    mock_embedding_response = MagicMock()
    mock_embedding_response.data = [MagicMock()]
    mock_embedding_response.data[0].embedding = [0.1] * 1536  # 模拟 1536 维向量
    mock_client.embeddings.create.return_value = mock_embedding_response

    return mock_client


@pytest.fixture
def mock_weaviate_client():
    """模拟 Weaviate 客户端"""
    mock_client = MagicMock()

    # 模拟查询结果
    mock_client.query.get.return_value.with_near_vector.return_value.with_limit.return_value.do.return_value = {
        "data": {
            "Get": {
                "Document": [
                    {
                        "content": "Test document content",
                        "metadata": {"source": "test.pdf"},
                        "_additional": {"distance": 0.1},
                    }
                ]
            }
        }
    }

    # 模拟数据插入
    mock_client.data_object.create.return_value = {"id": "test-uuid-123"}

    return mock_client


@pytest.fixture
def mock_neo4j_driver():
    """模拟 Neo4j 驱动"""
    mock_driver = MagicMock()
    mock_session = MagicMock()
    mock_result = MagicMock()

    # 模拟查询结果
    mock_result.single.return_value = {"count": 1}
    mock_result.data.return_value = [{"n": {"name": "Test Node", "type": "Entity"}}]

    mock_session.run.return_value = mock_result
    mock_driver.session.return_value.__enter__.return_value = mock_session

    return mock_driver


@pytest.fixture
def mock_elasticsearch_client():
    """模拟 Elasticsearch 客户端"""
    mock_client = AsyncMock()

    # 模拟搜索结果
    mock_client.search.return_value = {
        "hits": {
            "total": {"value": 1},
            "hits": [
                {
                    "_id": "test-doc-1",
                    "_source": {
                        "content": "Test document content",
                        "title": "Test Document",
                        "metadata": {"source": "test.pdf"},
                    },
                    "_score": 0.9,
                }
            ],
        }
    }

    # 模拟索引操作
    mock_client.index.return_value = {"_id": "test-doc-1", "result": "created"}

    return mock_client


@pytest.fixture
def mock_rabbitmq_connection():
    """模拟 RabbitMQ 连接"""
    mock_connection = AsyncMock()
    mock_channel = AsyncMock()
    mock_queue = AsyncMock()

    mock_connection.channel.return_value = mock_channel
    mock_channel.declare_queue.return_value = mock_queue

    return mock_connection


@pytest.fixture
def sample_document_data():
    """示例文档数据"""
    return {
        "id": "doc-123",
        "title": "Test Document",
        "content": "This is a test document for Knowledge RAG system.",
        "metadata": {
            "source": "test.pdf",
            "author": "Test Author",
            "created_at": "2024-01-01T00:00:00Z",
            "file_size": 1024,
            "mime_type": "application/pdf",
        },
        "chunks": [
            {
                "id": "chunk-1",
                "content": "This is the first chunk of the test document.",
                "start_index": 0,
                "end_index": 50,
                "embedding": [0.1] * 1536,
            },
            {
                "id": "chunk-2",
                "content": "This is the second chunk of the test document.",
                "start_index": 51,
                "end_index": 100,
                "embedding": [0.2] * 1536,
            },
        ],
    }


@pytest.fixture
def sample_user_data():
    """示例用户数据"""
    return {
        "id": "user-123",
        "username": "testuser",
        "email": "test@example.com",
        "full_name": "Test User",
        "is_active": True,
        "is_superuser": False,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
    }


@pytest.fixture
def sample_qa_data():
    """示例问答数据"""
    return {
        "question": "What is Knowledge RAG?",
        "answer": "Knowledge RAG is a Retrieval-Augmented Generation system for knowledge management.",
        "context": [
            "Knowledge RAG combines retrieval and generation capabilities.",
            "It helps users find and generate relevant information from documents.",
        ],
        "sources": [
            {"document_id": "doc-123", "chunk_id": "chunk-1", "relevance_score": 0.9}
        ],
        "metadata": {
            "model_used": "gpt-4",
            "response_time": 1.5,
            "confidence_score": 0.85,
        },
    }


@pytest.fixture
def sample_graph_data():
    """示例知识图谱数据"""
    return {
        "entities": [
            {
                "id": "entity-1",
                "name": "Knowledge RAG",
                "type": "System",
                "properties": {
                    "description": "A retrieval-augmented generation system",
                    "category": "AI System",
                },
            },
            {
                "id": "entity-2",
                "name": "Document Processing",
                "type": "Process",
                "properties": {
                    "description": "Process for handling documents",
                    "category": "Data Processing",
                },
            },
        ],
        "relationships": [
            {
                "id": "rel-1",
                "source": "entity-1",
                "target": "entity-2",
                "type": "USES",
                "properties": {
                    "strength": 0.8,
                    "description": "Knowledge RAG uses document processing",
                },
            }
        ],
    }


# 测试标记
pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.filterwarnings("ignore::DeprecationWarning"),
    pytest.mark.filterwarnings("ignore::PendingDeprecationWarning"),
]


# 测试配置
def pytest_configure(config):
    """pytest 配置"""
    config.addinivalue_line("markers", "unit: 标记单元测试")
    config.addinivalue_line("markers", "integration: 标记集成测试")
    config.addinivalue_line("markers", "e2e: 标记端到端测试")
    config.addinivalue_line("markers", "slow: 标记慢速测试")
    config.addinivalue_line("markers", "performance: 标记性能测试")


# 测试收集配置
def pytest_collection_modifyitems(config, items):
    """修改测试收集配置"""
    # 为没有标记的测试添加 unit 标记
    for item in items:
        if not any(
            mark.name in ["unit", "integration", "e2e", "performance"]
            for mark in item.iter_markers()
        ):
            item.add_marker(pytest.mark.unit)
