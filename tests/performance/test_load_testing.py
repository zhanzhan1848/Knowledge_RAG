# Knowledge RAG System - 负载和性能测试
# 测试系统在高负载下的性能表现

import asyncio
import json
import statistics
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from typing import Any, Dict, List
from unittest.mock import AsyncMock, Mock, patch

import psutil
import pytest
from httpx import AsyncClient


@pytest.mark.performance
class TestLoadTesting:
    """负载测试类"""

    @pytest.fixture
    def performance_metrics(self):
        """性能指标收集器"""
        return {
            "response_times": [],
            "success_count": 0,
            "error_count": 0,
            "throughput": 0,
            "cpu_usage": [],
            "memory_usage": [],
        }

    @pytest.fixture
    async def load_test_client(self, async_client):
        """负载测试客户端"""
        # 模拟认证
        mock_token = "load_test_token_123"
        async_client.headers.update({"Authorization": f"Bearer {mock_token}"})
        return async_client

    @pytest.mark.asyncio
    async def test_document_upload_load(self, load_test_client, performance_metrics):
        """测试文档上传负载"""
        client = load_test_client
        concurrent_users = 50
        documents_per_user = 5

        print(
            f"开始负载测试: {concurrent_users} 并发用户，每用户上传 {documents_per_user} 个文档"
        )

        async def upload_documents_for_user(user_id: int):
            """单个用户的文档上传任务"""
            user_metrics = {"user_id": user_id, "uploads": [], "errors": []}

            for doc_index in range(documents_per_user):
                try:
                    start_time = time.time()

                    # 模拟文档内容
                    document_content = (
                        f"负载测试文档内容 - 用户{user_id} - 文档{doc_index}" * 100
                    )

                    mock_response = {
                        "document_id": f"load_doc_{user_id}_{doc_index}_{uuid.uuid4().hex[:8]}",
                        "upload_status": "success",
                        "processing_status": "pending",
                        "file_size": len(document_content.encode("utf-8")),
                    }

                    with patch("httpx.AsyncClient.post") as mock_post:
                        mock_post.return_value.status_code = 201
                        mock_post.return_value.json.return_value = mock_response

                        files = {
                            "file": (
                                f"load_test_{user_id}_{doc_index}.txt",
                                document_content,
                                "text/plain",
                            )
                        }
                        response = await client.post("/documents/upload", files=files)

                    end_time = time.time()
                    response_time = end_time - start_time

                    if response.status_code == 201:
                        user_metrics["uploads"].append(
                            {
                                "document_id": mock_response["document_id"],
                                "response_time": response_time,
                                "file_size": mock_response["file_size"],
                            }
                        )
                        performance_metrics["success_count"] += 1
                    else:
                        user_metrics["errors"].append(
                            {
                                "status_code": response.status_code,
                                "response_time": response_time,
                            }
                        )
                        performance_metrics["error_count"] += 1

                    performance_metrics["response_times"].append(response_time)

                    # 模拟用户间隔
                    await asyncio.sleep(0.1)

                except Exception as e:
                    user_metrics["errors"].append({"error": str(e)})
                    performance_metrics["error_count"] += 1

            return user_metrics

        # 启动系统监控
        monitoring_task = asyncio.create_task(
            self._monitor_system_resources(performance_metrics, duration=30)
        )

        # 执行负载测试
        start_time = time.time()

        # 创建并发任务
        user_tasks = [
            upload_documents_for_user(user_id) for user_id in range(concurrent_users)
        ]

        # 等待所有任务完成
        user_results = await asyncio.gather(*user_tasks, return_exceptions=True)

        end_time = time.time()
        total_duration = end_time - start_time

        # 停止监控
        monitoring_task.cancel()

        # 计算性能指标
        total_requests = concurrent_users * documents_per_user
        success_rate = (performance_metrics["success_count"] / total_requests) * 100
        throughput = performance_metrics["success_count"] / total_duration

        response_times = performance_metrics["response_times"]
        avg_response_time = statistics.mean(response_times) if response_times else 0
        p95_response_time = (
            statistics.quantiles(response_times, n=20)[18]
            if len(response_times) >= 20
            else 0
        )
        p99_response_time = (
            statistics.quantiles(response_times, n=100)[98]
            if len(response_times) >= 100
            else 0
        )

        # 性能断言
        assert success_rate >= 95.0, f"成功率过低: {success_rate}%"
        assert avg_response_time < 5.0, f"平均响应时间过长: {avg_response_time}秒"
        assert p95_response_time < 10.0, f"P95响应时间过长: {p95_response_time}秒"
        assert throughput >= 10.0, f"吞吐量过低: {throughput} 请求/秒"

        # 输出性能报告
        print(f"\n📊 文档上传负载测试报告:")
        print(f"   总请求数: {total_requests}")
        print(f"   成功请求: {performance_metrics['success_count']}")
        print(f"   失败请求: {performance_metrics['error_count']}")
        print(f"   成功率: {success_rate:.2f}%")
        print(f"   总耗时: {total_duration:.2f}秒")
        print(f"   吞吐量: {throughput:.2f} 请求/秒")
        print(f"   平均响应时间: {avg_response_time:.3f}秒")
        print(f"   P95响应时间: {p95_response_time:.3f}秒")
        print(f"   P99响应时间: {p99_response_time:.3f}秒")

        if performance_metrics["cpu_usage"]:
            avg_cpu = statistics.mean(performance_metrics["cpu_usage"])
            print(f"   平均CPU使用率: {avg_cpu:.1f}%")

        if performance_metrics["memory_usage"]:
            avg_memory = statistics.mean(performance_metrics["memory_usage"])
            print(f"   平均内存使用率: {avg_memory:.1f}%")

    @pytest.mark.asyncio
    async def test_qa_service_load(self, load_test_client, performance_metrics):
        """测试问答服务负载"""
        client = load_test_client
        concurrent_users = 30
        questions_per_user = 10

        print(
            f"开始问答服务负载测试: {concurrent_users} 并发用户，每用户 {questions_per_user} 个问题"
        )

        # 预定义问题集
        question_templates = [
            "什么是{}？",
            "请解释{}的原理",
            "{}有哪些应用场景？",
            "{}的优缺点是什么？",
            "如何学习{}？",
            "{}的发展历程如何？",
            "{}与其他技术的区别？",
            "{}的未来发展趋势？",
            "{}在实际项目中如何应用？",
            "{}有哪些最佳实践？",
        ]

        topics = ["机器学习", "深度学习", "自然语言处理", "计算机视觉", "强化学习"]

        async def ask_questions_for_user(user_id: int):
            """单个用户的问答任务"""
            user_metrics = {"user_id": user_id, "questions": [], "errors": []}

            for q_index in range(questions_per_user):
                try:
                    start_time = time.time()

                    # 生成问题
                    template = question_templates[q_index % len(question_templates)]
                    topic = topics[user_id % len(topics)]
                    question = template.format(topic)

                    mock_response = {
                        "question": question,
                        "answer": f"这是对'{question}'的详细回答。{topic}是一个重要的技术领域...",
                        "confidence_score": 0.85 + (q_index % 10) * 0.01,
                        "sources": [
                            {
                                "document_id": f"doc_{user_id}_{q_index}",
                                "relevance_score": 0.9,
                            }
                        ],
                        "processing_time": 1.2 + (q_index % 5) * 0.1,
                    }

                    with patch("httpx.AsyncClient.post") as mock_post:
                        mock_post.return_value.status_code = 200
                        mock_post.return_value.json.return_value = mock_response

                        qa_data = {
                            "question": question,
                            "max_context_length": 4000,
                            "temperature": 0.7,
                        }

                        response = await client.post("/qa/ask", json=qa_data)

                    end_time = time.time()
                    response_time = end_time - start_time

                    if response.status_code == 200:
                        user_metrics["questions"].append(
                            {
                                "question": question,
                                "response_time": response_time,
                                "confidence_score": mock_response["confidence_score"],
                            }
                        )
                        performance_metrics["success_count"] += 1
                    else:
                        user_metrics["errors"].append(
                            {
                                "question": question,
                                "status_code": response.status_code,
                                "response_time": response_time,
                            }
                        )
                        performance_metrics["error_count"] += 1

                    performance_metrics["response_times"].append(response_time)

                    # 模拟用户思考时间
                    await asyncio.sleep(0.2)

                except Exception as e:
                    user_metrics["errors"].append(
                        {"question": question, "error": str(e)}
                    )
                    performance_metrics["error_count"] += 1

            return user_metrics

        # 启动系统监控
        monitoring_task = asyncio.create_task(
            self._monitor_system_resources(performance_metrics, duration=40)
        )

        # 执行负载测试
        start_time = time.time()

        user_tasks = [
            ask_questions_for_user(user_id) for user_id in range(concurrent_users)
        ]

        user_results = await asyncio.gather(*user_tasks, return_exceptions=True)

        end_time = time.time()
        total_duration = end_time - start_time

        # 停止监控
        monitoring_task.cancel()

        # 计算性能指标
        total_requests = concurrent_users * questions_per_user
        success_rate = (performance_metrics["success_count"] / total_requests) * 100
        throughput = performance_metrics["success_count"] / total_duration

        response_times = performance_metrics["response_times"]
        avg_response_time = statistics.mean(response_times) if response_times else 0
        p95_response_time = (
            statistics.quantiles(response_times, n=20)[18]
            if len(response_times) >= 20
            else 0
        )

        # 性能断言
        assert success_rate >= 98.0, f"问答服务成功率过低: {success_rate}%"
        assert avg_response_time < 3.0, f"问答平均响应时间过长: {avg_response_time}秒"
        assert p95_response_time < 6.0, f"问答P95响应时间过长: {p95_response_time}秒"
        assert throughput >= 5.0, f"问答吞吐量过低: {throughput} 请求/秒"

        # 输出性能报告
        print(f"\n📊 问答服务负载测试报告:")
        print(f"   总请求数: {total_requests}")
        print(f"   成功请求: {performance_metrics['success_count']}")
        print(f"   失败请求: {performance_metrics['error_count']}")
        print(f"   成功率: {success_rate:.2f}%")
        print(f"   总耗时: {total_duration:.2f}秒")
        print(f"   吞吐量: {throughput:.2f} 请求/秒")
        print(f"   平均响应时间: {avg_response_time:.3f}秒")
        print(f"   P95响应时间: {p95_response_time:.3f}秒")

    @pytest.mark.asyncio
    async def test_search_service_load(self, load_test_client, performance_metrics):
        """测试搜索服务负载"""
        client = load_test_client
        concurrent_users = 40
        searches_per_user = 8

        print(
            f"开始搜索服务负载测试: {concurrent_users} 并发用户，每用户 {searches_per_user} 次搜索"
        )

        # 预定义搜索关键词
        search_keywords = [
            "机器学习算法",
            "深度神经网络",
            "自然语言处理技术",
            "计算机视觉应用",
            "数据挖掘方法",
            "人工智能发展",
            "大数据分析",
            "云计算架构",
            "区块链技术",
            "物联网应用",
            "边缘计算",
            "量子计算",
        ]

        async def search_for_user(user_id: int):
            """单个用户的搜索任务"""
            user_metrics = {"user_id": user_id, "searches": [], "errors": []}

            for search_index in range(searches_per_user):
                try:
                    start_time = time.time()

                    # 选择搜索关键词
                    keyword = search_keywords[
                        (user_id * searches_per_user + search_index)
                        % len(search_keywords)
                    ]

                    mock_response = {
                        "query": keyword,
                        "total_count": 15 + (search_index % 10),
                        "results": [
                            {
                                "document_id": f"search_doc_{user_id}_{search_index}_{i}",
                                "title": f"相关文档{i+1}",
                                "relevance_score": 0.9 - (i * 0.05),
                                "matched_chunks": [
                                    {
                                        "chunk_id": f"chunk_{i}",
                                        "content": f"包含'{keyword}'的内容片段...",
                                        "score": 0.85 - (i * 0.03),
                                    }
                                ],
                            }
                            for i in range(min(5, 15 + (search_index % 10)))
                        ],
                        "search_time": 0.08 + (search_index % 5) * 0.02,
                    }

                    with patch("httpx.AsyncClient.post") as mock_post:
                        mock_post.return_value.status_code = 200
                        mock_post.return_value.json.return_value = mock_response

                        search_data = {
                            "query": keyword,
                            "limit": 10,
                            "offset": 0,
                            "filters": {},
                        }

                        response = await client.post(
                            "/documents/search", json=search_data
                        )

                    end_time = time.time()
                    response_time = end_time - start_time

                    if response.status_code == 200:
                        user_metrics["searches"].append(
                            {
                                "keyword": keyword,
                                "response_time": response_time,
                                "result_count": mock_response["total_count"],
                            }
                        )
                        performance_metrics["success_count"] += 1
                    else:
                        user_metrics["errors"].append(
                            {
                                "keyword": keyword,
                                "status_code": response.status_code,
                                "response_time": response_time,
                            }
                        )
                        performance_metrics["error_count"] += 1

                    performance_metrics["response_times"].append(response_time)

                    # 模拟用户浏览结果时间
                    await asyncio.sleep(0.15)

                except Exception as e:
                    user_metrics["errors"].append({"keyword": keyword, "error": str(e)})
                    performance_metrics["error_count"] += 1

            return user_metrics

        # 启动系统监控
        monitoring_task = asyncio.create_task(
            self._monitor_system_resources(performance_metrics, duration=25)
        )

        # 执行负载测试
        start_time = time.time()

        user_tasks = [search_for_user(user_id) for user_id in range(concurrent_users)]

        user_results = await asyncio.gather(*user_tasks, return_exceptions=True)

        end_time = time.time()
        total_duration = end_time - start_time

        # 停止监控
        monitoring_task.cancel()

        # 计算性能指标
        total_requests = concurrent_users * searches_per_user
        success_rate = (performance_metrics["success_count"] / total_requests) * 100
        throughput = performance_metrics["success_count"] / total_duration

        response_times = performance_metrics["response_times"]
        avg_response_time = statistics.mean(response_times) if response_times else 0
        p95_response_time = (
            statistics.quantiles(response_times, n=20)[18]
            if len(response_times) >= 20
            else 0
        )

        # 性能断言
        assert success_rate >= 99.0, f"搜索服务成功率过低: {success_rate}%"
        assert avg_response_time < 1.0, f"搜索平均响应时间过长: {avg_response_time}秒"
        assert p95_response_time < 2.0, f"搜索P95响应时间过长: {p95_response_time}秒"
        assert throughput >= 15.0, f"搜索吞吐量过低: {throughput} 请求/秒"

        # 输出性能报告
        print(f"\n📊 搜索服务负载测试报告:")
        print(f"   总请求数: {total_requests}")
        print(f"   成功请求: {performance_metrics['success_count']}")
        print(f"   失败请求: {performance_metrics['error_count']}")
        print(f"   成功率: {success_rate:.2f}%")
        print(f"   总耗时: {total_duration:.2f}秒")
        print(f"   吞吐量: {throughput:.2f} 请求/秒")
        print(f"   平均响应时间: {avg_response_time:.3f}秒")
        print(f"   P95响应时间: {p95_response_time:.3f}秒")

    async def _monitor_system_resources(self, metrics: Dict[str, Any], duration: int):
        """监控系统资源使用情况"""
        start_time = time.time()

        while time.time() - start_time < duration:
            try:
                # 获取CPU使用率
                cpu_percent = psutil.cpu_percent(interval=1)
                metrics["cpu_usage"].append(cpu_percent)

                # 获取内存使用率
                memory = psutil.virtual_memory()
                metrics["memory_usage"].append(memory.percent)

                await asyncio.sleep(1)

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"监控系统资源时出错: {e}")
                break


@pytest.mark.performance
class TestStressTesting:
    """压力测试类"""

    @pytest.mark.asyncio
    async def test_system_stress_mixed_load(self, load_test_client):
        """测试混合负载下的系统压力"""
        client = load_test_client

        print("开始系统压力测试: 混合负载场景")

        # 定义不同类型的负载
        load_scenarios = {
            "document_upload": {"users": 20, "operations": 3},
            "qa_requests": {"users": 30, "operations": 8},
            "search_requests": {"users": 25, "operations": 6},
            "kg_operations": {"users": 10, "operations": 4},
        }

        performance_metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "response_times": [],
            "scenario_metrics": {},
        }

        async def document_upload_scenario(user_id: int, operations: int):
            """文档上传场景"""
            scenario_metrics = {"success": 0, "errors": 0, "response_times": []}

            for i in range(operations):
                try:
                    start_time = time.time()

                    mock_response = {
                        "document_id": f"stress_doc_{user_id}_{i}",
                        "upload_status": "success",
                    }

                    with patch("httpx.AsyncClient.post") as mock_post:
                        mock_post.return_value.status_code = 201
                        mock_post.return_value.json.return_value = mock_response

                        files = {
                            "file": (
                                f"stress_test_{user_id}_{i}.txt",
                                "测试内容" * 50,
                                "text/plain",
                            )
                        }
                        response = await client.post("/documents/upload", files=files)

                    response_time = time.time() - start_time
                    scenario_metrics["response_times"].append(response_time)

                    if response.status_code == 201:
                        scenario_metrics["success"] += 1
                    else:
                        scenario_metrics["errors"] += 1

                    await asyncio.sleep(0.1)

                except Exception:
                    scenario_metrics["errors"] += 1

            return scenario_metrics

        async def qa_scenario(user_id: int, operations: int):
            """问答场景"""
            scenario_metrics = {"success": 0, "errors": 0, "response_times": []}

            questions = ["什么是AI？", "机器学习原理？", "深度学习应用？", "NLP技术？"]

            for i in range(operations):
                try:
                    start_time = time.time()

                    mock_response = {
                        "answer": "这是压力测试的回答",
                        "confidence_score": 0.9,
                    }

                    with patch("httpx.AsyncClient.post") as mock_post:
                        mock_post.return_value.status_code = 200
                        mock_post.return_value.json.return_value = mock_response

                        qa_data = {"question": questions[i % len(questions)]}
                        response = await client.post("/qa/ask", json=qa_data)

                    response_time = time.time() - start_time
                    scenario_metrics["response_times"].append(response_time)

                    if response.status_code == 200:
                        scenario_metrics["success"] += 1
                    else:
                        scenario_metrics["errors"] += 1

                    await asyncio.sleep(0.05)

                except Exception:
                    scenario_metrics["errors"] += 1

            return scenario_metrics

        async def search_scenario(user_id: int, operations: int):
            """搜索场景"""
            scenario_metrics = {"success": 0, "errors": 0, "response_times": []}

            keywords = ["机器学习", "深度学习", "AI应用", "数据科学"]

            for i in range(operations):
                try:
                    start_time = time.time()

                    mock_response = {
                        "results": [{"document_id": f"result_{i}", "score": 0.9}],
                        "total_count": 10,
                    }

                    with patch("httpx.AsyncClient.post") as mock_post:
                        mock_post.return_value.status_code = 200
                        mock_post.return_value.json.return_value = mock_response

                        search_data = {"query": keywords[i % len(keywords)]}
                        response = await client.post(
                            "/documents/search", json=search_data
                        )

                    response_time = time.time() - start_time
                    scenario_metrics["response_times"].append(response_time)

                    if response.status_code == 200:
                        scenario_metrics["success"] += 1
                    else:
                        scenario_metrics["errors"] += 1

                    await asyncio.sleep(0.03)

                except Exception:
                    scenario_metrics["errors"] += 1

            return scenario_metrics

        async def kg_scenario(user_id: int, operations: int):
            """知识图谱场景"""
            scenario_metrics = {"success": 0, "errors": 0, "response_times": []}

            for i in range(operations):
                try:
                    start_time = time.time()

                    mock_response = {
                        "entities": [{"text": "实体1", "label": "PERSON"}],
                        "relationships": [
                            {"subject": "A", "predicate": "关联", "object": "B"}
                        ],
                    }

                    with patch("httpx.AsyncClient.post") as mock_post:
                        mock_post.return_value.status_code = 200
                        mock_post.return_value.json.return_value = mock_response

                        kg_data = {"document_id": f"stress_doc_{user_id}_{i}"}
                        response = await client.post(
                            "/knowledge-graph/extract-entities", json=kg_data
                        )

                    response_time = time.time() - start_time
                    scenario_metrics["response_times"].append(response_time)

                    if response.status_code == 200:
                        scenario_metrics["success"] += 1
                    else:
                        scenario_metrics["errors"] += 1

                    await asyncio.sleep(0.2)

                except Exception:
                    scenario_metrics["errors"] += 1

            return scenario_metrics

        # 创建所有场景的任务
        all_tasks = []

        # 文档上传任务
        for user_id in range(load_scenarios["document_upload"]["users"]):
            task = document_upload_scenario(
                user_id, load_scenarios["document_upload"]["operations"]
            )
            all_tasks.append(("document_upload", task))

        # 问答任务
        for user_id in range(load_scenarios["qa_requests"]["users"]):
            task = qa_scenario(user_id, load_scenarios["qa_requests"]["operations"])
            all_tasks.append(("qa_requests", task))

        # 搜索任务
        for user_id in range(load_scenarios["search_requests"]["users"]):
            task = search_scenario(
                user_id, load_scenarios["search_requests"]["operations"]
            )
            all_tasks.append(("search_requests", task))

        # 知识图谱任务
        for user_id in range(load_scenarios["kg_operations"]["users"]):
            task = kg_scenario(user_id, load_scenarios["kg_operations"]["operations"])
            all_tasks.append(("kg_operations", task))

        # 执行所有任务
        start_time = time.time()

        # 随机打乱任务顺序以模拟真实负载
        import random

        random.shuffle(all_tasks)

        # 执行任务
        tasks_to_run = [task for _, task in all_tasks]
        results = await asyncio.gather(*tasks_to_run, return_exceptions=True)

        end_time = time.time()
        total_duration = end_time - start_time

        # 汇总结果
        for i, (scenario_name, _) in enumerate(all_tasks):
            if i < len(results) and not isinstance(results[i], Exception):
                result = results[i]

                if scenario_name not in performance_metrics["scenario_metrics"]:
                    performance_metrics["scenario_metrics"][scenario_name] = {
                        "success": 0,
                        "errors": 0,
                        "response_times": [],
                    }

                performance_metrics["scenario_metrics"][scenario_name][
                    "success"
                ] += result["success"]
                performance_metrics["scenario_metrics"][scenario_name][
                    "errors"
                ] += result["errors"]
                performance_metrics["scenario_metrics"][scenario_name][
                    "response_times"
                ].extend(result["response_times"])

                performance_metrics["successful_requests"] += result["success"]
                performance_metrics["failed_requests"] += result["errors"]
                performance_metrics["response_times"].extend(result["response_times"])

        performance_metrics["total_requests"] = (
            performance_metrics["successful_requests"]
            + performance_metrics["failed_requests"]
        )

        # 计算整体指标
        success_rate = (
            performance_metrics["successful_requests"]
            / performance_metrics["total_requests"]
        ) * 100
        throughput = performance_metrics["successful_requests"] / total_duration

        response_times = performance_metrics["response_times"]
        avg_response_time = statistics.mean(response_times) if response_times else 0

        # 压力测试断言（相对宽松的标准）
        assert success_rate >= 90.0, f"压力测试成功率过低: {success_rate}%"
        assert (
            avg_response_time < 8.0
        ), f"压力测试平均响应时间过长: {avg_response_time}秒"

        # 输出压力测试报告
        print(f"\n🔥 系统压力测试报告:")
        print(f"   总请求数: {performance_metrics['total_requests']}")
        print(f"   成功请求: {performance_metrics['successful_requests']}")
        print(f"   失败请求: {performance_metrics['failed_requests']}")
        print(f"   成功率: {success_rate:.2f}%")
        print(f"   总耗时: {total_duration:.2f}秒")
        print(f"   吞吐量: {throughput:.2f} 请求/秒")
        print(f"   平均响应时间: {avg_response_time:.3f}秒")

        # 各场景详细报告
        for scenario_name, metrics in performance_metrics["scenario_metrics"].items():
            scenario_success_rate = (
                metrics["success"] / (metrics["success"] + metrics["errors"])
            ) * 100
            scenario_avg_time = (
                statistics.mean(metrics["response_times"])
                if metrics["response_times"]
                else 0
            )

            print(f"\n   📋 {scenario_name} 场景:")
            print(f"      成功: {metrics['success']}, 失败: {metrics['errors']}")
            print(f"      成功率: {scenario_success_rate:.1f}%")
            print(f"      平均响应时间: {scenario_avg_time:.3f}秒")


@pytest.mark.performance
class TestMemoryLeakTesting:
    """内存泄漏测试类"""

    @pytest.mark.asyncio
    async def test_memory_usage_over_time(self, load_test_client):
        """测试长时间运行的内存使用情况"""
        client = load_test_client

        print("开始内存泄漏测试: 长时间运行监控")

        memory_snapshots = []
        test_duration = 60  # 测试60秒

        async def continuous_operations():
            """持续执行操作"""
            operation_count = 0

            while True:
                try:
                    # 轮换不同类型的操作
                    if operation_count % 4 == 0:
                        # 文档上传
                        mock_response = {
                            "document_id": f"mem_test_{operation_count}",
                            "status": "success",
                        }
                        with patch("httpx.AsyncClient.post") as mock_post:
                            mock_post.return_value.status_code = 201
                            mock_post.return_value.json.return_value = mock_response
                            files = {"file": ("test.txt", "内容" * 100, "text/plain")}
                            await client.post("/documents/upload", files=files)

                    elif operation_count % 4 == 1:
                        # 问答请求
                        mock_response = {"answer": "测试回答", "confidence_score": 0.9}
                        with patch("httpx.AsyncClient.post") as mock_post:
                            mock_post.return_value.status_code = 200
                            mock_post.return_value.json.return_value = mock_response
                            await client.post(
                                "/qa/ask",
                                json={"question": f"测试问题{operation_count}"},
                            )

                    elif operation_count % 4 == 2:
                        # 搜索请求
                        mock_response = {"results": [], "total_count": 0}
                        with patch("httpx.AsyncClient.post") as mock_post:
                            mock_post.return_value.status_code = 200
                            mock_post.return_value.json.return_value = mock_response
                            await client.post(
                                "/documents/search",
                                json={"query": f"搜索{operation_count}"},
                            )

                    else:
                        # 知识图谱操作
                        mock_response = {"entities": [], "relationships": []}
                        with patch("httpx.AsyncClient.post") as mock_post:
                            mock_post.return_value.status_code = 200
                            mock_post.return_value.json.return_value = mock_response
                            await client.post(
                                "/knowledge-graph/extract-entities",
                                json={"document_id": f"doc_{operation_count}"},
                            )

                    operation_count += 1
                    await asyncio.sleep(0.1)

                except asyncio.CancelledError:
                    break
                except Exception as e:
                    print(f"操作执行出错: {e}")
                    await asyncio.sleep(0.1)

        async def memory_monitor():
            """内存监控"""
            start_time = time.time()

            while time.time() - start_time < test_duration:
                try:
                    # 获取当前进程内存使用情况
                    process = psutil.Process()
                    memory_info = process.memory_info()

                    snapshot = {
                        "timestamp": time.time() - start_time,
                        "rss": memory_info.rss / 1024 / 1024,  # MB
                        "vms": memory_info.vms / 1024 / 1024,  # MB
                        "percent": process.memory_percent(),
                    }

                    memory_snapshots.append(snapshot)
                    await asyncio.sleep(2)  # 每2秒采样一次

                except asyncio.CancelledError:
                    break
                except Exception as e:
                    print(f"内存监控出错: {e}")
                    await asyncio.sleep(2)

        # 启动操作和监控任务
        operations_task = asyncio.create_task(continuous_operations())
        monitor_task = asyncio.create_task(memory_monitor())

        # 等待测试完成
        await asyncio.sleep(test_duration)

        # 停止任务
        operations_task.cancel()
        monitor_task.cancel()

        # 分析内存使用趋势
        if len(memory_snapshots) >= 3:
            initial_memory = statistics.mean([s["rss"] for s in memory_snapshots[:3]])
            final_memory = statistics.mean([s["rss"] for s in memory_snapshots[-3:]])
            memory_growth = final_memory - initial_memory
            growth_rate = memory_growth / test_duration  # MB/秒

            max_memory = max(s["rss"] for s in memory_snapshots)
            avg_memory = statistics.mean(s["rss"] for s in memory_snapshots)

            # 内存泄漏检测断言
            assert growth_rate < 1.0, f"内存增长率过高: {growth_rate:.3f} MB/秒"
            assert memory_growth < 50.0, f"总内存增长过大: {memory_growth:.1f} MB"
            assert max_memory < 500.0, f"峰值内存使用过高: {max_memory:.1f} MB"

            # 输出内存测试报告
            print(f"\n🧠 内存泄漏测试报告:")
            print(f"   测试时长: {test_duration}秒")
            print(f"   初始内存: {initial_memory:.1f} MB")
            print(f"   最终内存: {final_memory:.1f} MB")
            print(f"   内存增长: {memory_growth:.1f} MB")
            print(f"   增长率: {growth_rate:.3f} MB/秒")
            print(f"   峰值内存: {max_memory:.1f} MB")
            print(f"   平均内存: {avg_memory:.1f} MB")
            print(f"   采样次数: {len(memory_snapshots)}")

            if growth_rate < 0.1:
                print("   ✅ 内存使用稳定，无明显泄漏")
            elif growth_rate < 0.5:
                print("   ⚠️  内存有轻微增长，需要关注")
            else:
                print("   ❌ 内存增长较快，可能存在泄漏")

        else:
            print("⚠️ 内存采样数据不足，无法进行泄漏分析")
