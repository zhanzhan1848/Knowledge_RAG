# Knowledge RAG System - API集成测试
# 测试API网关与各微服务之间的集成功能

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from httpx import AsyncClient
import json
from datetime import datetime, timedelta


@pytest.mark.integration
class TestAuthenticationIntegration:
    """认证集成测试类"""

    @pytest.mark.asyncio
    async def test_user_registration_flow(self, async_client):
        """测试用户注册完整流程"""
        # 模拟用户注册数据
        registration_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "SecurePass123!",
            "confirm_password": "SecurePass123!",
        }

        # 模拟注册API响应
        mock_response = {
            "user_id": "user_123",
            "username": "testuser",
            "email": "test@example.com",
            "created_at": datetime.utcnow().isoformat(),
            "is_active": True,
        }

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value.status_code = 201
            mock_post.return_value.json.return_value = mock_response

            # 发送注册请求
            response = await async_client.post("/auth/register", json=registration_data)

            # 验证响应
            assert response.status_code == 201
            data = response.json()
            assert data["username"] == "testuser"
            assert data["email"] == "test@example.com"
            assert "user_id" in data
            assert data["is_active"] is True

    @pytest.mark.asyncio
    async def test_login_and_token_flow(self, async_client):
        """测试登录和令牌获取流程"""
        # 模拟登录数据
        login_data = {"username": "testuser", "password": "SecurePass123!"}

        # 模拟登录API响应
        mock_login_response = {
            "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
            "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
            "token_type": "bearer",
            "expires_in": 3600,
            "user": {
                "id": "user_123",
                "username": "testuser",
                "email": "test@example.com",
                "role": "user",
            },
        }

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_login_response

            # 发送登录请求
            response = await async_client.post("/auth/login", json=login_data)

            # 验证响应
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert "refresh_token" in data
            assert data["token_type"] == "bearer"
            assert data["expires_in"] == 3600
            assert data["user"]["username"] == "testuser"

    @pytest.mark.asyncio
    async def test_protected_endpoint_access(self, async_client):
        """测试受保护端点访问"""
        # 模拟有效的访问令牌
        access_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
        headers = {"Authorization": f"Bearer {access_token}"}

        # 模拟受保护端点响应
        mock_response = {
            "message": "访问成功",
            "user_info": {"id": "user_123", "username": "testuser", "role": "user"},
        }

        with patch("httpx.AsyncClient.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_response

            # 访问受保护端点
            response = await async_client.get("/auth/profile", headers=headers)

            # 验证响应
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "访问成功"
            assert data["user_info"]["username"] == "testuser"

    @pytest.mark.asyncio
    async def test_token_refresh_flow(self, async_client):
        """测试令牌刷新流程"""
        # 模拟刷新令牌数据
        refresh_data = {"refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."}

        # 模拟刷新响应
        mock_refresh_response = {
            "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9_new...",
            "token_type": "bearer",
            "expires_in": 3600,
        }

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_refresh_response

            # 发送刷新请求
            response = await async_client.post("/auth/refresh", json=refresh_data)

            # 验证响应
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert data["token_type"] == "bearer"
            assert data["expires_in"] == 3600


@pytest.mark.integration
class TestDocumentServiceIntegration:
    """文档服务集成测试类"""

    @pytest.mark.asyncio
    async def test_document_upload_flow(self, async_client, sample_document):
        """测试文档上传完整流程"""
        # 模拟文件上传数据
        files = {
            "file": ("test_document.pdf", sample_document["content"], "application/pdf")
        }

        data = {
            "title": sample_document["title"],
            "description": sample_document["description"],
            "tags": json.dumps(sample_document["tags"]),
        }

        # 模拟上传响应
        mock_upload_response = {
            "document_id": "doc_123",
            "title": sample_document["title"],
            "filename": "test_document.pdf",
            "file_size": len(sample_document["content"]),
            "upload_status": "success",
            "processing_status": "pending",
            "created_at": datetime.utcnow().isoformat(),
        }

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value.status_code = 201
            mock_post.return_value.json.return_value = mock_upload_response

            # 发送上传请求
            response = await async_client.post(
                "/documents/upload",
                files=files,
                data=data,
                headers={"Authorization": "Bearer test_token"},
            )

            # 验证响应
            assert response.status_code == 201
            result = response.json()
            assert result["document_id"] == "doc_123"
            assert result["upload_status"] == "success"
            assert result["processing_status"] == "pending"

    @pytest.mark.asyncio
    async def test_document_processing_status(self, async_client):
        """测试文档处理状态查询"""
        document_id = "doc_123"

        # 模拟处理状态响应
        mock_status_response = {
            "document_id": document_id,
            "processing_status": "completed",
            "processing_progress": 100,
            "extracted_text_length": 5000,
            "chunk_count": 25,
            "vector_count": 25,
            "processing_time": 45.2,
            "completed_at": datetime.utcnow().isoformat(),
        }

        with patch("httpx.AsyncClient.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_status_response

            # 查询处理状态
            response = await async_client.get(
                f"/documents/{document_id}/status",
                headers={"Authorization": "Bearer test_token"},
            )

            # 验证响应
            assert response.status_code == 200
            data = response.json()
            assert data["processing_status"] == "completed"
            assert data["processing_progress"] == 100
            assert data["chunk_count"] == 25

    @pytest.mark.asyncio
    async def test_document_search_integration(self, async_client):
        """测试文档搜索集成"""
        # 模拟搜索请求
        search_data = {
            "query": "机器学习算法",
            "filters": {
                "tags": ["AI", "机器学习"],
                "date_range": {"start": "2024-01-01", "end": "2024-12-31"},
            },
            "limit": 10,
            "offset": 0,
        }

        # 模拟搜索响应
        mock_search_response = {
            "total_count": 15,
            "results": [
                {
                    "document_id": "doc_123",
                    "title": "机器学习基础",
                    "relevance_score": 0.95,
                    "matched_chunks": [
                        {
                            "chunk_id": "chunk_456",
                            "content": "机器学习是人工智能的一个重要分支...",
                            "score": 0.92,
                        }
                    ],
                }
            ],
            "search_time": 0.15,
        }

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_search_response

            # 发送搜索请求
            response = await async_client.post(
                "/documents/search",
                json=search_data,
                headers={"Authorization": "Bearer test_token"},
            )

            # 验证响应
            assert response.status_code == 200
            data = response.json()
            assert data["total_count"] == 15
            assert len(data["results"]) == 1
            assert data["results"][0]["relevance_score"] == 0.95


@pytest.mark.integration
class TestVectorServiceIntegration:
    """向量服务集成测试类"""

    @pytest.mark.asyncio
    async def test_vector_embedding_flow(self, async_client):
        """测试向量嵌入生成流程"""
        # 模拟文本嵌入请求
        embedding_data = {
            "texts": ["这是第一段测试文本", "这是第二段测试文本"],
            "model": "text-embedding-ada-002",
        }

        # 模拟嵌入响应
        mock_embedding_response = {
            "embeddings": [
                {
                    "text": "这是第一段测试文本",
                    "vector": [0.1, 0.2, 0.3] * 512,  # 1536维向量
                    "model": "text-embedding-ada-002",
                },
                {
                    "text": "这是第二段测试文本",
                    "vector": [0.2, 0.3, 0.4] * 512,
                    "model": "text-embedding-ada-002",
                },
            ],
            "processing_time": 0.25,
        }

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_embedding_response

            # 发送嵌入请求
            response = await async_client.post(
                "/vectors/embed",
                json=embedding_data,
                headers={"Authorization": "Bearer test_token"},
            )

            # 验证响应
            assert response.status_code == 200
            data = response.json()
            assert len(data["embeddings"]) == 2
            assert len(data["embeddings"][0]["vector"]) == 1536

    @pytest.mark.asyncio
    async def test_vector_similarity_search(self, async_client):
        """测试向量相似性搜索"""
        # 模拟相似性搜索请求
        search_data = {
            "query_vector": [0.1, 0.2, 0.3] * 512,
            "top_k": 5,
            "threshold": 0.7,
            "filters": {"document_ids": ["doc_123", "doc_456"]},
        }

        # 模拟搜索响应
        mock_search_response = {
            "results": [
                {
                    "chunk_id": "chunk_789",
                    "document_id": "doc_123",
                    "similarity_score": 0.95,
                    "content": "相关的文档内容片段",
                    "metadata": {"page": 1, "section": "introduction"},
                },
                {
                    "chunk_id": "chunk_101",
                    "document_id": "doc_456",
                    "similarity_score": 0.87,
                    "content": "另一个相关的内容片段",
                    "metadata": {"page": 3, "section": "methodology"},
                },
            ],
            "search_time": 0.08,
        }

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_search_response

            # 发送搜索请求
            response = await async_client.post(
                "/vectors/search",
                json=search_data,
                headers={"Authorization": "Bearer test_token"},
            )

            # 验证响应
            assert response.status_code == 200
            data = response.json()
            assert len(data["results"]) == 2
            assert data["results"][0]["similarity_score"] == 0.95
            assert data["results"][1]["similarity_score"] == 0.87


@pytest.mark.integration
class TestQAServiceIntegration:
    """问答服务集成测试类"""

    @pytest.mark.asyncio
    async def test_question_answering_flow(self, async_client, sample_qa):
        """测试问答完整流程"""
        # 模拟问答请求
        qa_data = {
            "question": sample_qa["question"],
            "context_documents": ["doc_123", "doc_456"],
            "max_context_length": 4000,
            "temperature": 0.7,
            "model": "gpt-3.5-turbo",
        }

        # 模拟问答响应
        mock_qa_response = {
            "question": sample_qa["question"],
            "answer": sample_qa["answer"],
            "confidence_score": 0.92,
            "sources": [
                {
                    "document_id": "doc_123",
                    "chunk_id": "chunk_789",
                    "relevance_score": 0.95,
                    "content_snippet": "相关的上下文内容...",
                }
            ],
            "model_used": "gpt-3.5-turbo",
            "processing_time": 2.3,
            "token_usage": {
                "prompt_tokens": 1500,
                "completion_tokens": 200,
                "total_tokens": 1700,
            },
        }

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_qa_response

            # 发送问答请求
            response = await async_client.post(
                "/qa/ask", json=qa_data, headers={"Authorization": "Bearer test_token"}
            )

            # 验证响应
            assert response.status_code == 200
            data = response.json()
            assert data["question"] == sample_qa["question"]
            assert data["answer"] == sample_qa["answer"]
            assert data["confidence_score"] == 0.92
            assert len(data["sources"]) == 1

    @pytest.mark.asyncio
    async def test_conversation_flow(self, async_client):
        """测试对话流程"""
        # 模拟对话请求
        conversation_data = {
            "messages": [{"role": "user", "content": "什么是机器学习？"}],
            "conversation_id": "conv_123",
            "context_documents": ["doc_123"],
            "model": "gpt-3.5-turbo",
        }

        # 模拟对话响应
        mock_conversation_response = {
            "conversation_id": "conv_123",
            "messages": [
                {
                    "role": "user",
                    "content": "什么是机器学习？",
                    "timestamp": datetime.utcnow().isoformat(),
                },
                {
                    "role": "assistant",
                    "content": "机器学习是人工智能的一个分支...",
                    "timestamp": datetime.utcnow().isoformat(),
                    "sources": [{"document_id": "doc_123", "relevance_score": 0.9}],
                },
            ],
            "model_used": "gpt-3.5-turbo",
            "processing_time": 1.8,
        }

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_conversation_response

            # 发送对话请求
            response = await async_client.post(
                "/qa/conversation",
                json=conversation_data,
                headers={"Authorization": "Bearer test_token"},
            )

            # 验证响应
            assert response.status_code == 200
            data = response.json()
            assert data["conversation_id"] == "conv_123"
            assert len(data["messages"]) == 2
            assert data["messages"][1]["role"] == "assistant"


@pytest.mark.integration
class TestKnowledgeGraphIntegration:
    """知识图谱集成测试类"""

    @pytest.mark.asyncio
    async def test_entity_extraction_flow(self, async_client):
        """测试实体提取流程"""
        # 模拟实体提取请求
        extraction_data = {
            "text": "苹果公司由史蒂夫·乔布斯创立于1976年，总部位于加利福尼亚州库比蒂诺。",
            "language": "zh",
            "entity_types": ["PERSON", "ORG", "DATE", "GPE"],
        }

        # 模拟提取响应
        mock_extraction_response = {
            "entities": [
                {
                    "text": "苹果公司",
                    "label": "ORG",
                    "start": 0,
                    "end": 4,
                    "confidence": 0.95,
                },
                {
                    "text": "史蒂夫·乔布斯",
                    "label": "PERSON",
                    "start": 5,
                    "end": 12,
                    "confidence": 0.98,
                },
                {
                    "text": "1976年",
                    "label": "DATE",
                    "start": 15,
                    "end": 20,
                    "confidence": 0.92,
                },
                {
                    "text": "加利福尼亚州库比蒂诺",
                    "label": "GPE",
                    "start": 24,
                    "end": 35,
                    "confidence": 0.89,
                },
            ],
            "processing_time": 0.45,
        }

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_extraction_response

            # 发送实体提取请求
            response = await async_client.post(
                "/knowledge-graph/extract-entities",
                json=extraction_data,
                headers={"Authorization": "Bearer test_token"},
            )

            # 验证响应
            assert response.status_code == 200
            data = response.json()
            assert len(data["entities"]) == 4
            assert data["entities"][0]["text"] == "苹果公司"
            assert data["entities"][0]["label"] == "ORG"

    @pytest.mark.asyncio
    async def test_relationship_extraction_flow(self, async_client):
        """测试关系提取流程"""
        # 模拟关系提取请求
        relation_data = {
            "text": "苹果公司由史蒂夫·乔布斯创立于1976年",
            "entities": [
                {"text": "苹果公司", "label": "ORG", "start": 0, "end": 4},
                {"text": "史蒂夫·乔布斯", "label": "PERSON", "start": 5, "end": 12},
                {"text": "1976年", "label": "DATE", "start": 15, "end": 20},
            ],
        }

        # 模拟关系提取响应
        mock_relation_response = {
            "relationships": [
                {
                    "subject": "史蒂夫·乔布斯",
                    "predicate": "创立",
                    "object": "苹果公司",
                    "confidence": 0.94,
                },
                {
                    "subject": "苹果公司",
                    "predicate": "成立时间",
                    "object": "1976年",
                    "confidence": 0.91,
                },
            ],
            "processing_time": 0.32,
        }

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_relation_response

            # 发送关系提取请求
            response = await async_client.post(
                "/knowledge-graph/extract-relations",
                json=relation_data,
                headers={"Authorization": "Bearer test_token"},
            )

            # 验证响应
            assert response.status_code == 200
            data = response.json()
            assert len(data["relationships"]) == 2
            assert data["relationships"][0]["subject"] == "史蒂夫·乔布斯"
            assert data["relationships"][0]["predicate"] == "创立"
            assert data["relationships"][0]["object"] == "苹果公司"


@pytest.mark.integration
class TestEndToEndWorkflow:
    """端到端工作流测试类"""

    @pytest.mark.asyncio
    async def test_complete_document_processing_workflow(
        self, async_client, sample_document
    ):
        """测试完整的文档处理工作流"""
        # 1. 用户登录
        login_response = await self._mock_login(async_client)
        access_token = login_response["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}

        # 2. 上传文档
        upload_response = await self._mock_document_upload(
            async_client, headers, sample_document
        )
        document_id = upload_response["document_id"]

        # 3. 等待文档处理完成
        processing_response = await self._mock_document_processing(
            async_client, headers, document_id
        )
        assert processing_response["processing_status"] == "completed"

        # 4. 搜索文档
        search_response = await self._mock_document_search(async_client, headers)
        assert len(search_response["results"]) > 0

        # 5. 问答查询
        qa_response = await self._mock_qa_query(async_client, headers, document_id)
        assert qa_response["confidence_score"] > 0.8

        # 6. 知识图谱构建
        kg_response = await self._mock_knowledge_graph_build(
            async_client, headers, document_id
        )
        assert len(kg_response["entities"]) > 0
        assert len(kg_response["relationships"]) > 0

    async def _mock_login(self, async_client):
        """模拟用户登录"""
        login_data = {"username": "testuser", "password": "password123"}
        mock_response = {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "token_type": "bearer",
            "expires_in": 3600,
        }

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response

            response = await async_client.post("/auth/login", json=login_data)
            return response.json()

    async def _mock_document_upload(self, async_client, headers, sample_document):
        """模拟文档上传"""
        mock_response = {
            "document_id": "doc_test_123",
            "title": sample_document["title"],
            "upload_status": "success",
            "processing_status": "pending",
        }

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value.status_code = 201
            mock_post.return_value.json.return_value = mock_response

            files = {
                "file": ("test.pdf", sample_document["content"], "application/pdf")
            }
            response = await async_client.post(
                "/documents/upload", files=files, headers=headers
            )
            return response.json()

    async def _mock_document_processing(self, async_client, headers, document_id):
        """模拟文档处理状态查询"""
        mock_response = {
            "document_id": document_id,
            "processing_status": "completed",
            "processing_progress": 100,
            "chunk_count": 20,
            "vector_count": 20,
        }

        with patch("httpx.AsyncClient.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_response

            response = await async_client.get(
                f"/documents/{document_id}/status", headers=headers
            )
            return response.json()

    async def _mock_document_search(self, async_client, headers):
        """模拟文档搜索"""
        search_data = {"query": "测试查询", "limit": 10}
        mock_response = {
            "total_count": 1,
            "results": [
                {
                    "document_id": "doc_test_123",
                    "title": "测试文档",
                    "relevance_score": 0.95,
                }
            ],
        }

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response

            response = await async_client.post(
                "/documents/search", json=search_data, headers=headers
            )
            return response.json()

    async def _mock_qa_query(self, async_client, headers, document_id):
        """模拟问答查询"""
        qa_data = {
            "question": "这个文档讲的是什么？",
            "context_documents": [document_id],
        }
        mock_response = {
            "question": "这个文档讲的是什么？",
            "answer": "这个文档主要讲述了...",
            "confidence_score": 0.92,
            "sources": [{"document_id": document_id, "relevance_score": 0.9}],
        }

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response

            response = await async_client.post("/qa/ask", json=qa_data, headers=headers)
            return response.json()

    async def _mock_knowledge_graph_build(self, async_client, headers, document_id):
        """模拟知识图谱构建"""
        kg_data = {"document_id": document_id}
        mock_response = {
            "document_id": document_id,
            "entities": [
                {"text": "实体1", "label": "PERSON", "confidence": 0.9},
                {"text": "实体2", "label": "ORG", "confidence": 0.85},
            ],
            "relationships": [
                {
                    "subject": "实体1",
                    "predicate": "工作于",
                    "object": "实体2",
                    "confidence": 0.88,
                }
            ],
        }

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response

            response = await async_client.post(
                "/knowledge-graph/build", json=kg_data, headers=headers
            )
            return response.json()


@pytest.mark.integration
@pytest.mark.slow
class TestPerformanceIntegration:
    """性能集成测试类"""

    @pytest.mark.asyncio
    async def test_concurrent_requests_performance(self, async_client):
        """测试并发请求性能"""
        import time

        async def make_request():
            """发送单个请求"""
            with patch("httpx.AsyncClient.get") as mock_get:
                mock_get.return_value.status_code = 200
                mock_get.return_value.json.return_value = {"status": "ok"}

                response = await async_client.get("/health")
                return response.status_code

        # 测试并发请求
        start_time = time.time()
        tasks = [make_request() for _ in range(50)]
        results = await asyncio.gather(*tasks)
        end_time = time.time()

        # 验证结果
        assert all(status == 200 for status in results)
        assert len(results) == 50

        # 性能断言（50个请求应在5秒内完成）
        total_time = end_time - start_time
        assert total_time < 5.0, f"并发请求耗时过长: {total_time}秒"

    @pytest.mark.asyncio
    async def test_large_document_processing_performance(self, async_client):
        """测试大文档处理性能"""
        # 模拟大文档（1MB文本）
        large_content = "这是一个大文档的内容。" * 50000  # 约1MB

        mock_response = {
            "document_id": "large_doc_123",
            "file_size": len(large_content.encode("utf-8")),
            "processing_status": "pending",
            "estimated_processing_time": 30,
        }

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value.status_code = 201
            mock_post.return_value.json.return_value = mock_response

            start_time = time.time()
            files = {"file": ("large_doc.txt", large_content, "text/plain")}
            response = await async_client.post(
                "/documents/upload",
                files=files,
                headers={"Authorization": "Bearer test_token"},
            )
            end_time = time.time()

            # 验证响应
            assert response.status_code == 201
            data = response.json()
            assert data["file_size"] > 1000000  # 大于1MB

            # 上传时间应在合理范围内（10秒内）
            upload_time = end_time - start_time
            assert upload_time < 10.0, f"大文档上传耗时过长: {upload_time}秒"
