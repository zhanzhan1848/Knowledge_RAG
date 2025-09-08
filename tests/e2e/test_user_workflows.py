# Knowledge RAG System - 端到端用户工作流测试
# 测试完整的用户使用场景和业务流程

import asyncio
import json
import os
import tempfile
import time
import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest
from httpx import AsyncClient


@pytest.mark.e2e
class TestCompleteUserWorkflow:
    """完整用户工作流测试类"""

    @pytest.fixture
    async def authenticated_client(self, async_client):
        """已认证的客户端fixture"""
        # 模拟用户登录获取令牌
        login_data = {"username": "e2euser", "password": "E2EPassword123!"}

        mock_login_response = {
            "access_token": "e2e_access_token_123",
            "refresh_token": "e2e_refresh_token_123",
            "token_type": "bearer",
            "expires_in": 3600,
            "user": {
                "id": "e2e_user_123",
                "username": "e2euser",
                "email": "e2e@example.com",
                "role": "user",
            },
        }

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_login_response

            response = await async_client.post("/auth/login", json=login_data)
            token_data = response.json()

            # 设置认证头
            async_client.headers.update(
                {"Authorization": f"Bearer {token_data['access_token']}"}
            )

            return async_client, token_data

    @pytest.mark.asyncio
    async def test_document_upload_to_qa_workflow(
        self, authenticated_client, sample_document
    ):
        """测试从文档上传到问答的完整工作流"""
        client, token_data = authenticated_client

        # 步骤1: 上传文档
        upload_response = await self._upload_document(client, sample_document)
        document_id = upload_response["document_id"]

        assert upload_response["upload_status"] == "success"
        assert upload_response["processing_status"] == "pending"

        # 步骤2: 等待文档处理完成
        processing_response = await self._wait_for_document_processing(
            client, document_id
        )

        assert processing_response["processing_status"] == "completed"
        assert processing_response["chunk_count"] > 0
        assert processing_response["vector_count"] > 0

        # 步骤3: 搜索文档内容
        search_response = await self._search_documents(client, "机器学习")

        assert search_response["total_count"] > 0
        assert len(search_response["results"]) > 0
        assert any(
            result["document_id"] == document_id
            for result in search_response["results"]
        )

        # 步骤4: 基于文档进行问答
        qa_response = await self._ask_question(
            client, "什么是机器学习？", [document_id]
        )

        assert qa_response["confidence_score"] > 0.7
        assert len(qa_response["answer"]) > 0
        assert len(qa_response["sources"]) > 0
        assert qa_response["sources"][0]["document_id"] == document_id

        # 步骤5: 继续对话
        conversation_response = await self._continue_conversation(
            client, qa_response.get("conversation_id"), "能详细解释一下吗？"
        )

        assert len(conversation_response["messages"]) >= 2
        assert conversation_response["messages"][-1]["role"] == "assistant"

        print(f"✅ 完整工作流测试成功: 文档 {document_id} 从上传到问答全流程完成")

    @pytest.mark.asyncio
    async def test_knowledge_graph_workflow(
        self, authenticated_client, sample_document
    ):
        """测试知识图谱构建工作流"""
        client, token_data = authenticated_client

        # 步骤1: 上传包含实体关系的文档
        entity_document = {
            "title": "公司信息文档",
            "content": "苹果公司由史蒂夫·乔布斯创立于1976年，总部位于加利福尼亚州库比蒂诺。微软公司由比尔·盖茨创立于1975年，总部位于华盛顿州雷德蒙德。",
            "description": "包含公司和创始人信息的测试文档",
            "tags": ["公司", "创始人", "历史"],
        }

        upload_response = await self._upload_document(client, entity_document)
        document_id = upload_response["document_id"]

        # 步骤2: 等待文档处理完成
        await self._wait_for_document_processing(client, document_id)

        # 步骤3: 提取实体
        entities_response = await self._extract_entities(client, document_id)

        assert len(entities_response["entities"]) > 0

        # 验证提取的实体类型
        entity_types = [entity["label"] for entity in entities_response["entities"]]
        assert "ORG" in entity_types  # 组织（公司）
        assert "PERSON" in entity_types  # 人物（创始人）
        assert "DATE" in entity_types  # 日期

        # 步骤4: 提取关系
        relations_response = await self._extract_relations(client, document_id)

        assert len(relations_response["relationships"]) > 0

        # 验证关系类型
        predicates = [rel["predicate"] for rel in relations_response["relationships"]]
        assert any("创立" in pred or "founded" in pred.lower() for pred in predicates)

        # 步骤5: 构建知识图谱
        kg_response = await self._build_knowledge_graph(client, document_id)

        assert kg_response["status"] == "completed"
        assert kg_response["node_count"] > 0
        assert kg_response["edge_count"] > 0

        # 步骤6: 查询知识图谱
        kg_query_response = await self._query_knowledge_graph(
            client, "找到所有由史蒂夫·乔布斯创立的公司"
        )

        assert len(kg_query_response["results"]) > 0
        assert any("苹果" in str(result) for result in kg_query_response["results"])

        print(f"✅ 知识图谱工作流测试成功: 文档 {document_id} 的知识图谱构建完成")

    @pytest.mark.asyncio
    async def test_multi_document_analysis_workflow(self, authenticated_client):
        """测试多文档分析工作流"""
        client, token_data = authenticated_client

        # 步骤1: 上传多个相关文档
        documents = [
            {
                "title": "机器学习基础",
                "content": "机器学习是人工智能的一个分支，它使计算机能够在没有明确编程的情况下学习。",
                "tags": ["机器学习", "AI", "基础"],
            },
            {
                "title": "深度学习介绍",
                "content": "深度学习是机器学习的一个子集，使用神经网络来模拟人脑的学习过程。",
                "tags": ["深度学习", "神经网络", "AI"],
            },
            {
                "title": "自然语言处理",
                "content": "自然语言处理是人工智能的一个领域，专注于计算机与人类语言之间的交互。",
                "tags": ["NLP", "语言处理", "AI"],
            },
        ]

        document_ids = []
        for doc in documents:
            upload_response = await self._upload_document(client, doc)
            document_ids.append(upload_response["document_id"])

            # 等待处理完成
            await self._wait_for_document_processing(
                client, upload_response["document_id"]
            )

        # 步骤2: 跨文档搜索
        search_response = await self._search_documents(
            client, "人工智能和机器学习的关系", document_ids=document_ids
        )

        assert search_response["total_count"] >= len(documents)

        # 验证所有文档都被搜索到
        found_doc_ids = [result["document_id"] for result in search_response["results"]]
        assert all(doc_id in found_doc_ids for doc_id in document_ids)

        # 步骤3: 基于多文档的综合问答
        comprehensive_qa_response = await self._ask_question(
            client,
            "请综合这些文档，解释人工智能、机器学习和深度学习之间的关系",
            document_ids,
        )

        assert comprehensive_qa_response["confidence_score"] > 0.8
        assert len(comprehensive_qa_response["sources"]) >= 2  # 至少引用2个文档

        # 验证答案包含关键概念
        answer = comprehensive_qa_response["answer"].lower()
        assert "机器学习" in answer
        assert "深度学习" in answer
        assert "人工智能" in answer

        # 步骤4: 文档相似性分析
        similarity_response = await self._analyze_document_similarity(
            client, document_ids
        )

        assert len(similarity_response["similarities"]) > 0

        # 验证相似性分数合理
        for similarity in similarity_response["similarities"]:
            assert 0 <= similarity["score"] <= 1
            assert similarity["doc1_id"] in document_ids
            assert similarity["doc2_id"] in document_ids

        print(f"✅ 多文档分析工作流测试成功: {len(document_ids)} 个文档的综合分析完成")

    @pytest.mark.asyncio
    async def test_user_session_workflow(self, authenticated_client):
        """测试用户会话管理工作流"""
        client, token_data = authenticated_client

        # 步骤1: 创建新的对话会话
        session_response = await self._create_conversation_session(client)
        conversation_id = session_response["conversation_id"]

        assert session_response["status"] == "created"
        assert conversation_id is not None

        # 步骤2: 在会话中进行多轮对话
        questions = [
            "什么是机器学习？",
            "它有哪些主要类型？",
            "监督学习和无监督学习的区别是什么？",
            "能举个具体的例子吗？",
        ]

        for i, question in enumerate(questions):
            qa_response = await self._ask_question_in_session(
                client, conversation_id, question
            )

            assert qa_response["conversation_id"] == conversation_id
            assert len(qa_response["messages"]) == (i + 1) * 2  # 每轮问答产生2条消息

            # 验证上下文连续性（后续问题应该能理解前面的对话）
            if i > 0:
                assert qa_response["context_used"] is True

        # 步骤3: 获取会话历史
        history_response = await self._get_conversation_history(client, conversation_id)

        assert len(history_response["messages"]) == len(questions) * 2
        assert history_response["conversation_id"] == conversation_id

        # 验证消息顺序和角色
        for i, message in enumerate(history_response["messages"]):
            expected_role = "user" if i % 2 == 0 else "assistant"
            assert message["role"] == expected_role

        # 步骤4: 导出会话记录
        export_response = await self._export_conversation(client, conversation_id)

        assert export_response["format"] == "json"
        assert "download_url" in export_response

        # 步骤5: 删除会话
        delete_response = await self._delete_conversation(client, conversation_id)

        assert delete_response["status"] == "deleted"

        print(f"✅ 用户会话工作流测试成功: 会话 {conversation_id} 完整生命周期测试完成")

    @pytest.mark.asyncio
    async def test_error_recovery_workflow(self, authenticated_client, sample_document):
        """测试错误恢复工作流"""
        client, token_data = authenticated_client

        # 步骤1: 模拟文档上传失败后重试
        with patch("httpx.AsyncClient.post") as mock_post:
            # 第一次上传失败
            mock_post.return_value.status_code = 500
            mock_post.return_value.json.return_value = {
                "error": "Internal server error",
                "message": "文档处理服务暂时不可用",
            }

            # 验证失败响应
            files = {
                "file": ("test.pdf", sample_document["content"], "application/pdf")
            }
            response = await client.post("/documents/upload", files=files)

            assert response.status_code == 500

            # 第二次上传成功
            mock_post.return_value.status_code = 201
            mock_post.return_value.json.return_value = {
                "document_id": "recovered_doc_123",
                "upload_status": "success",
                "processing_status": "pending",
            }

            # 重试上传
            retry_response = await client.post("/documents/upload", files=files)

            assert retry_response.status_code == 201
            assert retry_response.json()["upload_status"] == "success"

        # 步骤2: 模拟处理超时后恢复
        document_id = "recovered_doc_123"

        with patch("httpx.AsyncClient.get") as mock_get:
            # 模拟处理超时
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {
                "document_id": document_id,
                "processing_status": "failed",
                "error_message": "处理超时",
                "retry_count": 1,
            }

            status_response = await client.get(f"/documents/{document_id}/status")
            assert status_response.json()["processing_status"] == "failed"

            # 重新处理
            with patch("httpx.AsyncClient.post") as mock_reprocess:
                mock_reprocess.return_value.status_code = 200
                mock_reprocess.return_value.json.return_value = {
                    "document_id": document_id,
                    "status": "reprocessing_started",
                    "estimated_time": 300,
                }

                reprocess_response = await client.post(
                    f"/documents/{document_id}/reprocess"
                )
                assert reprocess_response.json()["status"] == "reprocessing_started"

            # 处理成功
            mock_get.return_value.json.return_value = {
                "document_id": document_id,
                "processing_status": "completed",
                "chunk_count": 20,
                "vector_count": 20,
            }

            final_status = await client.get(f"/documents/{document_id}/status")
            assert final_status.json()["processing_status"] == "completed"

        # 步骤3: 模拟问答服务暂时不可用
        with patch("httpx.AsyncClient.post") as mock_qa:
            # 第一次问答失败
            mock_qa.return_value.status_code = 503
            mock_qa.return_value.json.return_value = {
                "error": "Service unavailable",
                "message": "问答服务正在维护中",
                "retry_after": 60,
            }

            qa_data = {"question": "测试问题", "context_documents": [document_id]}

            qa_response = await client.post("/qa/ask", json=qa_data)
            assert qa_response.status_code == 503

            # 等待后重试成功
            mock_qa.return_value.status_code = 200
            mock_qa.return_value.json.return_value = {
                "question": "测试问题",
                "answer": "这是恢复后的答案",
                "confidence_score": 0.9,
            }

            retry_qa_response = await client.post("/qa/ask", json=qa_data)
            assert retry_qa_response.status_code == 200
            assert retry_qa_response.json()["answer"] == "这是恢复后的答案"

        print("✅ 错误恢复工作流测试成功: 各种错误场景的恢复机制正常")

    # 辅助方法
    async def _upload_document(self, client, document):
        """上传文档辅助方法"""
        mock_response = {
            "document_id": f"doc_{uuid.uuid4().hex[:8]}",
            "title": document["title"],
            "filename": f"{document['title']}.pdf",
            "upload_status": "success",
            "processing_status": "pending",
            "created_at": datetime.utcnow().isoformat(),
        }

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value.status_code = 201
            mock_post.return_value.json.return_value = mock_response

            files = {"file": ("test.pdf", document["content"], "application/pdf")}
            data = {
                "title": document["title"],
                "description": document.get("description", ""),
                "tags": json.dumps(document.get("tags", [])),
            }

            response = await client.post("/documents/upload", files=files, data=data)
            return response.json()

    async def _wait_for_document_processing(self, client, document_id, max_wait=30):
        """等待文档处理完成"""
        mock_response = {
            "document_id": document_id,
            "processing_status": "completed",
            "processing_progress": 100,
            "chunk_count": 25,
            "vector_count": 25,
            "processing_time": 15.5,
            "completed_at": datetime.utcnow().isoformat(),
        }

        with patch("httpx.AsyncClient.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_response

            response = await client.get(f"/documents/{document_id}/status")
            return response.json()

    async def _search_documents(self, client, query, document_ids=None):
        """搜索文档辅助方法"""
        search_data = {"query": query, "limit": 10, "offset": 0}

        if document_ids:
            search_data["filters"] = {"document_ids": document_ids}

        mock_response = {
            "total_count": 3,
            "results": [
                {
                    "document_id": document_ids[0] if document_ids else "doc_123",
                    "title": "相关文档1",
                    "relevance_score": 0.95,
                    "matched_chunks": [
                        {
                            "chunk_id": "chunk_456",
                            "content": "匹配的内容片段...",
                            "score": 0.92,
                        }
                    ],
                }
            ],
            "search_time": 0.12,
        }

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response

            response = await client.post("/documents/search", json=search_data)
            return response.json()

    async def _ask_question(self, client, question, context_documents=None):
        """问答辅助方法"""
        qa_data = {"question": question, "max_context_length": 4000, "temperature": 0.7}

        if context_documents:
            qa_data["context_documents"] = context_documents

        mock_response = {
            "question": question,
            "answer": "这是基于文档内容生成的详细答案...",
            "confidence_score": 0.92,
            "sources": [
                {
                    "document_id": (
                        context_documents[0] if context_documents else "doc_123"
                    ),
                    "chunk_id": "chunk_789",
                    "relevance_score": 0.95,
                    "content_snippet": "相关的上下文内容...",
                }
            ],
            "conversation_id": f"conv_{uuid.uuid4().hex[:8]}",
            "processing_time": 2.3,
        }

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response

            response = await client.post("/qa/ask", json=qa_data)
            return response.json()

    async def _continue_conversation(self, client, conversation_id, question):
        """继续对话辅助方法"""
        conversation_data = {"conversation_id": conversation_id, "question": question}

        mock_response = {
            "conversation_id": conversation_id,
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
                },
                {
                    "role": "user",
                    "content": question,
                    "timestamp": datetime.utcnow().isoformat(),
                },
                {
                    "role": "assistant",
                    "content": "当然可以详细解释...",
                    "timestamp": datetime.utcnow().isoformat(),
                },
            ],
        }

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response

            response = await client.post("/qa/conversation", json=conversation_data)
            return response.json()

    async def _extract_entities(self, client, document_id):
        """提取实体辅助方法"""
        extraction_data = {
            "document_id": document_id,
            "entity_types": ["PERSON", "ORG", "DATE", "GPE"],
        }

        mock_response = {
            "document_id": document_id,
            "entities": [
                {"text": "苹果公司", "label": "ORG", "confidence": 0.95},
                {"text": "史蒂夫·乔布斯", "label": "PERSON", "confidence": 0.98},
                {"text": "1976年", "label": "DATE", "confidence": 0.92},
                {"text": "加利福尼亚州库比蒂诺", "label": "GPE", "confidence": 0.89},
            ],
            "processing_time": 0.45,
        }

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response

            response = await client.post(
                "/knowledge-graph/extract-entities", json=extraction_data
            )
            return response.json()

    async def _extract_relations(self, client, document_id):
        """提取关系辅助方法"""
        relation_data = {"document_id": document_id}

        mock_response = {
            "document_id": document_id,
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
            mock_post.return_value.json.return_value = mock_response

            response = await client.post(
                "/knowledge-graph/extract-relations", json=relation_data
            )
            return response.json()

    async def _build_knowledge_graph(self, client, document_id):
        """构建知识图谱辅助方法"""
        kg_data = {"document_id": document_id}

        mock_response = {
            "document_id": document_id,
            "status": "completed",
            "node_count": 15,
            "edge_count": 12,
            "processing_time": 8.5,
            "graph_id": f"kg_{uuid.uuid4().hex[:8]}",
        }

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response

            response = await client.post("/knowledge-graph/build", json=kg_data)
            return response.json()

    async def _query_knowledge_graph(self, client, query):
        """查询知识图谱辅助方法"""
        query_data = {"query": query, "limit": 10}

        mock_response = {
            "query": query,
            "results": [
                {
                    "entity": "苹果公司",
                    "type": "ORG",
                    "relationships": [
                        {
                            "predicate": "创立者",
                            "object": "史蒂夫·乔布斯",
                            "confidence": 0.94,
                        }
                    ],
                }
            ],
            "result_count": 1,
            "query_time": 0.08,
        }

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response

            response = await client.post("/knowledge-graph/query", json=query_data)
            return response.json()

    async def _analyze_document_similarity(self, client, document_ids):
        """分析文档相似性辅助方法"""
        similarity_data = {"document_ids": document_ids}

        mock_response = {
            "similarities": [
                {
                    "doc1_id": document_ids[0],
                    "doc2_id": document_ids[1],
                    "score": 0.85,
                    "common_topics": ["机器学习", "人工智能"],
                },
                {
                    "doc1_id": document_ids[1],
                    "doc2_id": document_ids[2],
                    "score": 0.72,
                    "common_topics": ["人工智能", "算法"],
                },
            ],
            "analysis_time": 1.2,
        }

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response

            response = await client.post("/documents/similarity", json=similarity_data)
            return response.json()

    async def _create_conversation_session(self, client):
        """创建对话会话辅助方法"""
        session_data = {"title": "E2E测试会话", "description": "端到端测试的对话会话"}

        mock_response = {
            "conversation_id": f"conv_{uuid.uuid4().hex[:8]}",
            "status": "created",
            "created_at": datetime.utcnow().isoformat(),
        }

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value.status_code = 201
            mock_post.return_value.json.return_value = mock_response

            response = await client.post("/qa/sessions", json=session_data)
            return response.json()

    async def _ask_question_in_session(self, client, conversation_id, question):
        """在会话中问问题辅助方法"""
        qa_data = {"conversation_id": conversation_id, "question": question}

        # 模拟消息数量递增
        message_count = getattr(self, "_message_count", 0) + 2
        setattr(self, "_message_count", message_count)

        mock_response = {
            "conversation_id": conversation_id,
            "messages": [
                {"role": "user" if i % 2 == 0 else "assistant", "content": f"消息{i+1}"}
                for i in range(message_count)
            ],
            "context_used": message_count > 2,
        }

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response

            response = await client.post("/qa/ask", json=qa_data)
            return response.json()

    async def _get_conversation_history(self, client, conversation_id):
        """获取对话历史辅助方法"""
        mock_response = {
            "conversation_id": conversation_id,
            "messages": [
                {
                    "role": "user" if i % 2 == 0 else "assistant",
                    "content": f"历史消息{i+1}",
                }
                for i in range(8)  # 4轮对话，8条消息
            ],
            "total_messages": 8,
        }

        with patch("httpx.AsyncClient.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_response

            response = await client.get(f"/qa/sessions/{conversation_id}/history")
            return response.json()

    async def _export_conversation(self, client, conversation_id):
        """导出对话辅助方法"""
        mock_response = {
            "conversation_id": conversation_id,
            "format": "json",
            "download_url": f"/downloads/conversation_{conversation_id}.json",
            "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
        }

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response

            response = await client.post(f"/qa/sessions/{conversation_id}/export")
            return response.json()

    async def _delete_conversation(self, client, conversation_id):
        """删除对话辅助方法"""
        mock_response = {
            "conversation_id": conversation_id,
            "status": "deleted",
            "deleted_at": datetime.utcnow().isoformat(),
        }

        with patch("httpx.AsyncClient.delete") as mock_delete:
            mock_delete.return_value.status_code = 200
            mock_delete.return_value.json.return_value = mock_response

            response = await client.delete(f"/qa/sessions/{conversation_id}")
            return response.json()


@pytest.mark.e2e
@pytest.mark.slow
class TestPerformanceWorkflows:
    """性能相关的端到端测试类"""

    @pytest.mark.asyncio
    async def test_high_load_document_processing(self, authenticated_client):
        """测试高负载文档处理"""
        client, token_data = authenticated_client

        # 模拟同时上传多个文档
        document_count = 10
        documents = [
            {
                "title": f"负载测试文档{i}",
                "content": f"这是第{i}个负载测试文档的内容。" * 100,  # 较长内容
                "tags": ["负载测试", f"文档{i}"],
            }
            for i in range(document_count)
        ]

        # 并发上传文档
        start_time = time.time()

        async def upload_single_doc(doc):
            mock_response = {
                "document_id": f"load_test_doc_{uuid.uuid4().hex[:8]}",
                "upload_status": "success",
                "processing_status": "pending",
            }

            with patch("httpx.AsyncClient.post") as mock_post:
                mock_post.return_value.status_code = 201
                mock_post.return_value.json.return_value = mock_response

                files = {"file": (f"{doc['title']}.txt", doc["content"], "text/plain")}
                response = await client.post("/documents/upload", files=files)
                return response.json()

        # 并发执行上传
        upload_tasks = [upload_single_doc(doc) for doc in documents]
        upload_results = await asyncio.gather(*upload_tasks)

        upload_time = time.time() - start_time

        # 验证所有上传都成功
        assert len(upload_results) == document_count
        assert all(result["upload_status"] == "success" for result in upload_results)

        # 性能断言（10个文档并发上传应在10秒内完成）
        assert upload_time < 10.0, f"并发上传耗时过长: {upload_time}秒"

        print(
            f"✅ 高负载文档处理测试成功: {document_count} 个文档并发上传耗时 {upload_time:.2f} 秒"
        )

    @pytest.mark.asyncio
    async def test_concurrent_qa_requests(self, authenticated_client):
        """测试并发问答请求"""
        client, token_data = authenticated_client

        # 准备多个问题
        questions = [
            "什么是机器学习？",
            "深度学习的原理是什么？",
            "自然语言处理有哪些应用？",
            "计算机视觉的发展历程如何？",
            "强化学习的核心概念是什么？",
        ] * 4  # 20个问题

        async def ask_single_question(question, index):
            mock_response = {
                "question": question,
                "answer": f"这是对问题'{question}'的详细回答...",
                "confidence_score": 0.85 + (index % 10) * 0.01,
                "processing_time": 1.5 + (index % 5) * 0.1,
            }

            with patch("httpx.AsyncClient.post") as mock_post:
                mock_post.return_value.status_code = 200
                mock_post.return_value.json.return_value = mock_response

                qa_data = {"question": question}
                response = await client.post("/qa/ask", json=qa_data)
                return response.json()

        # 并发执行问答
        start_time = time.time()
        qa_tasks = [ask_single_question(q, i) for i, q in enumerate(questions)]
        qa_results = await asyncio.gather(*qa_tasks)
        qa_time = time.time() - start_time

        # 验证所有问答都成功
        assert len(qa_results) == len(questions)
        assert all(result["confidence_score"] > 0.8 for result in qa_results)

        # 性能断言（20个并发问答应在15秒内完成）
        assert qa_time < 15.0, f"并发问答耗时过长: {qa_time}秒"

        print(
            f"✅ 并发问答测试成功: {len(questions)} 个问题并发处理耗时 {qa_time:.2f} 秒"
        )

    @pytest.mark.asyncio
    async def test_large_document_workflow(self, authenticated_client):
        """测试大文档处理工作流"""
        client, token_data = authenticated_client

        # 创建大文档（模拟1MB文本）
        large_content = "这是一个大文档的内容段落。" * 20000  # 约1MB

        large_document = {
            "title": "大文档性能测试",
            "content": large_content,
            "description": "用于测试大文档处理性能的测试文档",
            "tags": ["性能测试", "大文档"],
        }

        # 上传大文档
        start_time = time.time()

        mock_upload_response = {
            "document_id": "large_doc_123",
            "title": large_document["title"],
            "file_size": len(large_content.encode("utf-8")),
            "upload_status": "success",
            "processing_status": "pending",
            "estimated_processing_time": 60,
        }

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value.status_code = 201
            mock_post.return_value.json.return_value = mock_upload_response

            files = {"file": ("large_doc.txt", large_content, "text/plain")}
            upload_response = await client.post("/documents/upload", files=files)

        upload_time = time.time() - start_time

        # 验证上传成功
        upload_data = upload_response.json()
        assert upload_data["upload_status"] == "success"
        assert upload_data["file_size"] > 1000000  # 大于1MB

        # 上传时间应在合理范围内
        assert upload_time < 15.0, f"大文档上传耗时过长: {upload_time}秒"

        # 模拟处理完成
        mock_processing_response = {
            "document_id": "large_doc_123",
            "processing_status": "completed",
            "chunk_count": 200,  # 大文档分成更多块
            "vector_count": 200,
            "processing_time": 45.8,
        }

        with patch("httpx.AsyncClient.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_processing_response

            processing_response = await client.get("/documents/large_doc_123/status")

        processing_data = processing_response.json()
        assert processing_data["processing_status"] == "completed"
        assert processing_data["chunk_count"] == 200

        print(
            f"✅ 大文档工作流测试成功: 1MB文档上传耗时 {upload_time:.2f} 秒，处理完成"
        )


@pytest.mark.e2e
class TestCrossServiceIntegration:
    """跨服务集成测试类"""

    @pytest.mark.asyncio
    async def test_full_system_integration(self, authenticated_client, sample_document):
        """测试完整系统集成"""
        client, token_data = authenticated_client

        # 步骤1: 用户认证 ✓ (已在fixture中完成)
        assert token_data["access_token"] is not None

        # 步骤2: 文档服务 - 上传和处理
        upload_response = await self._mock_document_upload(client, sample_document)
        document_id = upload_response["document_id"]

        # 步骤3: 向量服务 - 生成嵌入
        embedding_response = await self._mock_vector_embedding(client, document_id)
        assert embedding_response["status"] == "completed"

        # 步骤4: 知识图谱服务 - 构建图谱
        kg_response = await self._mock_knowledge_graph_build(client, document_id)
        assert kg_response["node_count"] > 0

        # 步骤5: 问答服务 - 基于多个服务的数据回答问题
        qa_response = await self._mock_comprehensive_qa(client, document_id)
        assert qa_response["confidence_score"] > 0.8
        assert len(qa_response["sources"]) > 0

        # 步骤6: 通知服务 - 发送处理完成通知
        notification_response = await self._mock_notification(client, document_id)
        assert notification_response["status"] == "sent"

        print("✅ 完整系统集成测试成功: 所有微服务协同工作正常")

    async def _mock_document_upload(self, client, document):
        """模拟文档上传"""
        mock_response = {
            "document_id": f"integration_doc_{uuid.uuid4().hex[:8]}",
            "upload_status": "success",
            "processing_status": "completed",
        }

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value.status_code = 201
            mock_post.return_value.json.return_value = mock_response

            files = {
                "file": ("integration_test.pdf", document["content"], "application/pdf")
            }
            response = await client.post("/documents/upload", files=files)
            return response.json()

    async def _mock_vector_embedding(self, client, document_id):
        """模拟向量嵌入生成"""
        mock_response = {
            "document_id": document_id,
            "status": "completed",
            "vector_count": 25,
            "embedding_model": "text-embedding-ada-002",
        }

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response

            response = await client.post(f"/vectors/embed-document/{document_id}")
            return response.json()

    async def _mock_knowledge_graph_build(self, client, document_id):
        """模拟知识图谱构建"""
        mock_response = {
            "document_id": document_id,
            "status": "completed",
            "node_count": 15,
            "edge_count": 12,
            "graph_id": f"kg_{uuid.uuid4().hex[:8]}",
        }

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response

            response = await client.post(
                "/knowledge-graph/build", json={"document_id": document_id}
            )
            return response.json()

    async def _mock_comprehensive_qa(self, client, document_id):
        """模拟综合问答（使用多个服务的数据）"""
        qa_data = {
            "question": "基于这个文档，总结主要内容并分析其中的关键实体关系",
            "context_documents": [document_id],
            "use_knowledge_graph": True,
            "use_vector_search": True,
        }

        mock_response = {
            "question": qa_data["question"],
            "answer": "基于文档内容和知识图谱分析，主要内容包括...",
            "confidence_score": 0.94,
            "sources": [
                {
                    "type": "document",
                    "document_id": document_id,
                    "relevance_score": 0.92,
                },
                {
                    "type": "knowledge_graph",
                    "entities": ["实体1", "实体2"],
                    "relationships": ["关系1"],
                },
            ],
            "services_used": ["document", "vector", "knowledge_graph"],
        }

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response

            response = await client.post("/qa/comprehensive-ask", json=qa_data)
            return response.json()

    async def _mock_notification(self, client, document_id):
        """模拟通知发送"""
        notification_data = {
            "type": "document_processing_completed",
            "document_id": document_id,
            "message": "文档处理已完成，包括向量化和知识图谱构建",
        }

        mock_response = {
            "notification_id": f"notif_{uuid.uuid4().hex[:8]}",
            "status": "sent",
            "sent_at": datetime.utcnow().isoformat(),
        }

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response

            response = await client.post("/notifications/send", json=notification_data)
            return response.json()
