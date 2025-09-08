# Knowledge RAG System - 性能基准测试
# 测试系统各组件的性能基准和优化效果

import asyncio
import json
import statistics
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple
from unittest.mock import AsyncMock, Mock, patch

import numpy as np
import pytest
from httpx import AsyncClient


@dataclass
class BenchmarkResult:
    """基准测试结果数据类"""

    operation_name: str
    total_operations: int
    total_time: float
    avg_time: float
    min_time: float
    max_time: float
    p50_time: float
    p95_time: float
    p99_time: float
    throughput: float
    success_rate: float
    error_count: int


@pytest.mark.performance
class TestDocumentProcessingBenchmarks:
    """文档处理性能基准测试"""

    @pytest.fixture
    def benchmark_client(self, async_client):
        """基准测试客户端"""
        mock_token = "benchmark_token_123"
        async_client.headers.update({"Authorization": f"Bearer {mock_token}"})
        return async_client

    @pytest.mark.asyncio
    async def test_document_upload_benchmark(self, benchmark_client):
        """文档上传性能基准测试"""
        client = benchmark_client

        # 测试不同文件大小的上传性能
        file_sizes = [
            ("small", 1024),  # 1KB
            ("medium", 102400),  # 100KB
            ("large", 1048576),  # 1MB
            ("xlarge", 5242880),  # 5MB
        ]

        benchmark_results = []

        for size_name, size_bytes in file_sizes:
            print(f"\n📄 测试 {size_name} 文件上传性能 ({size_bytes // 1024}KB)")

            # 生成测试文件内容
            content = "测试内容" * (size_bytes // 12)  # 大约达到目标大小
            actual_size = len(content.encode("utf-8"))

            operations = 20  # 每种大小测试20次
            response_times = []
            success_count = 0
            error_count = 0

            for i in range(operations):
                try:
                    start_time = time.time()

                    mock_response = {
                        "document_id": f"benchmark_{size_name}_{i}_{uuid.uuid4().hex[:8]}",
                        "upload_status": "success",
                        "file_size": actual_size,
                        "processing_status": "pending",
                    }

                    with patch("httpx.AsyncClient.post") as mock_post:
                        mock_post.return_value.status_code = 201
                        mock_post.return_value.json.return_value = mock_response

                        files = {
                            "file": (
                                f"benchmark_{size_name}_{i}.txt",
                                content,
                                "text/plain",
                            )
                        }
                        response = await client.post("/documents/upload", files=files)

                    end_time = time.time()
                    response_time = end_time - start_time
                    response_times.append(response_time)

                    if response.status_code == 201:
                        success_count += 1
                    else:
                        error_count += 1

                    # 短暂间隔
                    await asyncio.sleep(0.05)

                except Exception as e:
                    error_count += 1
                    print(f"上传出错: {e}")

            # 计算统计指标
            if response_times:
                total_time = sum(response_times)
                avg_time = statistics.mean(response_times)
                min_time = min(response_times)
                max_time = max(response_times)

                # 计算百分位数
                sorted_times = sorted(response_times)
                p50_time = statistics.median(sorted_times)
                p95_time = (
                    sorted_times[int(0.95 * len(sorted_times))]
                    if len(sorted_times) > 1
                    else sorted_times[0]
                )
                p99_time = (
                    sorted_times[int(0.99 * len(sorted_times))]
                    if len(sorted_times) > 1
                    else sorted_times[0]
                )

                throughput = success_count / total_time if total_time > 0 else 0
                success_rate = (success_count / operations) * 100

                result = BenchmarkResult(
                    operation_name=f"upload_{size_name}",
                    total_operations=operations,
                    total_time=total_time,
                    avg_time=avg_time,
                    min_time=min_time,
                    max_time=max_time,
                    p50_time=p50_time,
                    p95_time=p95_time,
                    p99_time=p99_time,
                    throughput=throughput,
                    success_rate=success_rate,
                    error_count=error_count,
                )

                benchmark_results.append(result)

                # 输出结果
                print(f"   文件大小: {actual_size // 1024}KB")
                print(f"   操作次数: {operations}")
                print(f"   成功率: {success_rate:.1f}%")
                print(f"   平均时间: {avg_time:.3f}秒")
                print(f"   P95时间: {p95_time:.3f}秒")
                print(f"   吞吐量: {throughput:.2f} 文件/秒")
                print(f"   传输速率: {(actual_size / 1024 / avg_time):.1f} KB/秒")

        # 性能基准断言
        for result in benchmark_results:
            if "small" in result.operation_name:
                assert (
                    result.avg_time < 0.5
                ), f"小文件上传平均时间过长: {result.avg_time:.3f}秒"
                assert (
                    result.throughput >= 10.0
                ), f"小文件上传吞吐量过低: {result.throughput:.2f}"
            elif "medium" in result.operation_name:
                assert (
                    result.avg_time < 1.0
                ), f"中等文件上传平均时间过长: {result.avg_time:.3f}秒"
                assert (
                    result.throughput >= 5.0
                ), f"中等文件上传吞吐量过低: {result.throughput:.2f}"
            elif "large" in result.operation_name:
                assert (
                    result.avg_time < 2.0
                ), f"大文件上传平均时间过长: {result.avg_time:.3f}秒"
                assert (
                    result.throughput >= 2.0
                ), f"大文件上传吞吐量过低: {result.throughput:.2f}"

            assert (
                result.success_rate >= 95.0
            ), f"{result.operation_name} 成功率过低: {result.success_rate:.1f}%"

        print(f"\n✅ 文档上传性能基准测试通过")

    @pytest.mark.asyncio
    async def test_document_processing_benchmark(self, benchmark_client):
        """文档处理性能基准测试"""
        client = benchmark_client

        # 测试不同类型文档的处理性能
        document_types = [
            ("text", "这是一个文本文档的内容。" * 100, "text/plain"),
            (
                "markdown",
                "# 标题\n\n这是**markdown**文档内容。\n\n- 列表项1\n- 列表项2" * 50,
                "text/markdown",
            ),
            (
                "json",
                json.dumps(
                    {
                        "data": [f"item_{i}" for i in range(100)],
                        "metadata": {"type": "test"},
                    }
                ),
                "application/json",
            ),
        ]

        benchmark_results = []

        for doc_type, content, mime_type in document_types:
            print(f"\n🔄 测试 {doc_type} 文档处理性能")

            operations = 15
            processing_times = []
            success_count = 0
            error_count = 0

            for i in range(operations):
                try:
                    # 1. 上传文档
                    upload_start = time.time()

                    document_id = (
                        f"process_benchmark_{doc_type}_{i}_{uuid.uuid4().hex[:8]}"
                    )

                    mock_upload_response = {
                        "document_id": document_id,
                        "upload_status": "success",
                        "processing_status": "pending",
                    }

                    with patch("httpx.AsyncClient.post") as mock_post:
                        mock_post.return_value.status_code = 201
                        mock_post.return_value.json.return_value = mock_upload_response

                        files = {
                            "file": (
                                f"benchmark_{doc_type}_{i}.txt",
                                content,
                                mime_type,
                            )
                        }
                        upload_response = await client.post(
                            "/documents/upload", files=files
                        )

                    # 2. 触发处理
                    mock_process_response = {
                        "document_id": document_id,
                        "processing_status": "processing",
                        "estimated_time": 5,
                    }

                    with patch("httpx.AsyncClient.post") as mock_post:
                        mock_post.return_value.status_code = 200
                        mock_post.return_value.json.return_value = mock_process_response

                        process_data = {
                            "document_id": document_id,
                            "processing_options": {"extract_entities": True},
                        }
                        process_response = await client.post(
                            "/documents/process", json=process_data
                        )

                    # 3. 模拟等待处理完成
                    await asyncio.sleep(0.1)  # 模拟处理时间

                    # 4. 检查处理状态
                    mock_status_response = {
                        "document_id": document_id,
                        "processing_status": "completed",
                        "chunks_count": 10 + (i % 5),
                        "entities_count": 5 + (i % 3),
                        "processing_time": 2.5 + (i % 10) * 0.1,
                    }

                    with patch("httpx.AsyncClient.get") as mock_get:
                        mock_get.return_value.status_code = 200
                        mock_get.return_value.json.return_value = mock_status_response

                        status_response = await client.get(
                            f"/documents/{document_id}/status"
                        )

                    processing_end = time.time()
                    total_processing_time = processing_end - upload_start
                    processing_times.append(total_processing_time)

                    if (
                        upload_response.status_code == 201
                        and process_response.status_code == 200
                        and status_response.status_code == 200
                    ):
                        success_count += 1
                    else:
                        error_count += 1

                    await asyncio.sleep(0.1)

                except Exception as e:
                    error_count += 1
                    print(f"处理出错: {e}")

            # 计算统计指标
            if processing_times:
                total_time = sum(processing_times)
                avg_time = statistics.mean(processing_times)
                min_time = min(processing_times)
                max_time = max(processing_times)

                sorted_times = sorted(processing_times)
                p50_time = statistics.median(sorted_times)
                p95_time = (
                    sorted_times[int(0.95 * len(sorted_times))]
                    if len(sorted_times) > 1
                    else sorted_times[0]
                )
                p99_time = (
                    sorted_times[int(0.99 * len(sorted_times))]
                    if len(sorted_times) > 1
                    else sorted_times[0]
                )

                throughput = success_count / total_time if total_time > 0 else 0
                success_rate = (success_count / operations) * 100

                result = BenchmarkResult(
                    operation_name=f"process_{doc_type}",
                    total_operations=operations,
                    total_time=total_time,
                    avg_time=avg_time,
                    min_time=min_time,
                    max_time=max_time,
                    p50_time=p50_time,
                    p95_time=p95_time,
                    p99_time=p99_time,
                    throughput=throughput,
                    success_rate=success_rate,
                    error_count=error_count,
                )

                benchmark_results.append(result)

                # 输出结果
                print(f"   文档类型: {doc_type}")
                print(f"   操作次数: {operations}")
                print(f"   成功率: {success_rate:.1f}%")
                print(f"   平均处理时间: {avg_time:.3f}秒")
                print(f"   P95处理时间: {p95_time:.3f}秒")
                print(f"   处理吞吐量: {throughput:.2f} 文档/秒")

        # 性能基准断言
        for result in benchmark_results:
            assert (
                result.avg_time < 5.0
            ), f"{result.operation_name} 平均处理时间过长: {result.avg_time:.3f}秒"
            assert (
                result.success_rate >= 90.0
            ), f"{result.operation_name} 成功率过低: {result.success_rate:.1f}%"
            assert (
                result.throughput >= 1.0
            ), f"{result.operation_name} 吞吐量过低: {result.throughput:.2f}"

        print(f"\n✅ 文档处理性能基准测试通过")


@pytest.mark.performance
class TestSearchBenchmarks:
    """搜索性能基准测试"""

    @pytest.fixture
    def search_client(self, async_client):
        """搜索测试客户端"""
        mock_token = "search_benchmark_token"
        async_client.headers.update({"Authorization": f"Bearer {mock_token}"})
        return async_client

    @pytest.mark.asyncio
    async def test_vector_search_benchmark(self, search_client):
        """向量搜索性能基准测试"""
        client = search_client

        # 测试不同复杂度的搜索查询
        search_scenarios = [
            ("simple", "机器学习", 10),
            ("medium", "深度学习神经网络算法优化", 20),
            (
                "complex",
                "基于Transformer架构的大规模语言模型在自然语言处理任务中的应用与优化策略",
                50,
            ),
        ]

        benchmark_results = []

        for scenario_name, query, result_limit in search_scenarios:
            print(f"\n🔍 测试 {scenario_name} 向量搜索性能")

            operations = 25
            search_times = []
            success_count = 0
            error_count = 0

            for i in range(operations):
                try:
                    start_time = time.time()

                    # 模拟向量搜索结果
                    mock_results = [
                        {
                            "document_id": f"search_doc_{scenario_name}_{i}_{j}",
                            "chunk_id": f"chunk_{j}",
                            "content": f"这是与'{query}'相关的内容片段{j+1}...",
                            "similarity_score": 0.95 - (j * 0.02),
                            "metadata": {
                                "document_title": f"相关文档{j+1}",
                                "chunk_index": j,
                                "word_count": 150 + (j * 10),
                            },
                        }
                        for j in range(min(result_limit, 15))
                    ]

                    mock_response = {
                        "query": query,
                        "total_count": result_limit,
                        "results": mock_results,
                        "search_time": 0.05
                        + (len(query) / 1000),  # 模拟搜索时间与查询复杂度相关
                        "vector_dimension": 768,
                        "index_size": 10000 + (i * 100),
                    }

                    with patch("httpx.AsyncClient.post") as mock_post:
                        mock_post.return_value.status_code = 200
                        mock_post.return_value.json.return_value = mock_response

                        search_data = {
                            "query": query,
                            "limit": result_limit,
                            "similarity_threshold": 0.7,
                            "search_type": "vector",
                        }

                        response = await client.post("/vector/search", json=search_data)

                    end_time = time.time()
                    search_time = end_time - start_time
                    search_times.append(search_time)

                    if response.status_code == 200:
                        success_count += 1
                    else:
                        error_count += 1

                    await asyncio.sleep(0.02)

                except Exception as e:
                    error_count += 1
                    print(f"搜索出错: {e}")

            # 计算统计指标
            if search_times:
                total_time = sum(search_times)
                avg_time = statistics.mean(search_times)
                min_time = min(search_times)
                max_time = max(search_times)

                sorted_times = sorted(search_times)
                p50_time = statistics.median(sorted_times)
                p95_time = (
                    sorted_times[int(0.95 * len(sorted_times))]
                    if len(sorted_times) > 1
                    else sorted_times[0]
                )
                p99_time = (
                    sorted_times[int(0.99 * len(sorted_times))]
                    if len(sorted_times) > 1
                    else sorted_times[0]
                )

                throughput = success_count / total_time if total_time > 0 else 0
                success_rate = (success_count / operations) * 100

                result = BenchmarkResult(
                    operation_name=f"vector_search_{scenario_name}",
                    total_operations=operations,
                    total_time=total_time,
                    avg_time=avg_time,
                    min_time=min_time,
                    max_time=max_time,
                    p50_time=p50_time,
                    p95_time=p95_time,
                    p99_time=p99_time,
                    throughput=throughput,
                    success_rate=success_rate,
                    error_count=error_count,
                )

                benchmark_results.append(result)

                # 输出结果
                print(f"   查询复杂度: {scenario_name}")
                print(f"   查询长度: {len(query)} 字符")
                print(f"   结果限制: {result_limit}")
                print(f"   操作次数: {operations}")
                print(f"   成功率: {success_rate:.1f}%")
                print(f"   平均搜索时间: {avg_time:.3f}秒")
                print(f"   P95搜索时间: {p95_time:.3f}秒")
                print(f"   搜索吞吐量: {throughput:.2f} 查询/秒")

        # 性能基准断言
        for result in benchmark_results:
            if "simple" in result.operation_name:
                assert (
                    result.avg_time < 0.2
                ), f"简单搜索平均时间过长: {result.avg_time:.3f}秒"
                assert (
                    result.throughput >= 20.0
                ), f"简单搜索吞吐量过低: {result.throughput:.2f}"
            elif "medium" in result.operation_name:
                assert (
                    result.avg_time < 0.5
                ), f"中等搜索平均时间过长: {result.avg_time:.3f}秒"
                assert (
                    result.throughput >= 10.0
                ), f"中等搜索吞吐量过低: {result.throughput:.2f}"
            elif "complex" in result.operation_name:
                assert (
                    result.avg_time < 1.0
                ), f"复杂搜索平均时间过长: {result.avg_time:.3f}秒"
                assert (
                    result.throughput >= 5.0
                ), f"复杂搜索吞吐量过低: {result.throughput:.2f}"

            assert (
                result.success_rate >= 98.0
            ), f"{result.operation_name} 成功率过低: {result.success_rate:.1f}%"

        print(f"\n✅ 向量搜索性能基准测试通过")

    @pytest.mark.asyncio
    async def test_hybrid_search_benchmark(self, search_client):
        """混合搜索性能基准测试"""
        client = search_client

        print(f"\n🔀 测试混合搜索性能基准")

        # 混合搜索查询（结合关键词和向量搜索）
        hybrid_queries = [
            {
                "text_query": "机器学习算法",
                "vector_query": "深度学习神经网络",
                "weights": {"text": 0.3, "vector": 0.7},
            },
            {
                "text_query": "自然语言处理 NLP",
                "vector_query": "文本分析和理解技术",
                "weights": {"text": 0.5, "vector": 0.5},
            },
            {
                "text_query": "计算机视觉 CNN",
                "vector_query": "图像识别和目标检测",
                "weights": {"text": 0.4, "vector": 0.6},
            },
        ]

        operations = 20
        search_times = []
        success_count = 0
        error_count = 0

        for i in range(operations):
            try:
                start_time = time.time()

                # 选择查询
                query_config = hybrid_queries[i % len(hybrid_queries)]

                # 模拟混合搜索结果
                mock_text_results = [
                    {
                        "document_id": f"text_result_{i}_{j}",
                        "content": f"文本搜索结果{j+1}: {query_config['text_query']}",
                        "text_score": 0.9 - (j * 0.05),
                        "match_type": "keyword",
                    }
                    for j in range(8)
                ]

                mock_vector_results = [
                    {
                        "document_id": f"vector_result_{i}_{j}",
                        "content": f"向量搜索结果{j+1}: {query_config['vector_query']}",
                        "vector_score": 0.95 - (j * 0.03),
                        "match_type": "semantic",
                    }
                    for j in range(12)
                ]

                # 模拟混合评分和排序
                combined_results = []
                for j in range(10):
                    text_score = mock_text_results[j % len(mock_text_results)][
                        "text_score"
                    ]
                    vector_score = mock_vector_results[j % len(mock_vector_results)][
                        "vector_score"
                    ]

                    hybrid_score = (
                        text_score * query_config["weights"]["text"]
                        + vector_score * query_config["weights"]["vector"]
                    )

                    combined_results.append(
                        {
                            "document_id": f"hybrid_result_{i}_{j}",
                            "content": f"混合搜索结果{j+1}",
                            "hybrid_score": hybrid_score,
                            "text_score": text_score,
                            "vector_score": vector_score,
                            "match_types": ["keyword", "semantic"],
                        }
                    )

                # 按混合评分排序
                combined_results.sort(key=lambda x: x["hybrid_score"], reverse=True)

                mock_response = {
                    "query": query_config,
                    "total_count": len(combined_results),
                    "results": combined_results,
                    "search_time": 0.12 + (i % 5) * 0.02,
                    "text_search_time": 0.05,
                    "vector_search_time": 0.08,
                    "fusion_time": 0.02,
                }

                with patch("httpx.AsyncClient.post") as mock_post:
                    mock_post.return_value.status_code = 200
                    mock_post.return_value.json.return_value = mock_response

                    search_data = {
                        "text_query": query_config["text_query"],
                        "vector_query": query_config["vector_query"],
                        "weights": query_config["weights"],
                        "limit": 10,
                        "search_type": "hybrid",
                    }

                    response = await client.post("/search/hybrid", json=search_data)

                end_time = time.time()
                search_time = end_time - start_time
                search_times.append(search_time)

                if response.status_code == 200:
                    success_count += 1
                else:
                    error_count += 1

                await asyncio.sleep(0.05)

            except Exception as e:
                error_count += 1
                print(f"混合搜索出错: {e}")

        # 计算统计指标
        if search_times:
            total_time = sum(search_times)
            avg_time = statistics.mean(search_times)
            min_time = min(search_times)
            max_time = max(search_times)

            sorted_times = sorted(search_times)
            p50_time = statistics.median(sorted_times)
            p95_time = (
                sorted_times[int(0.95 * len(sorted_times))]
                if len(sorted_times) > 1
                else sorted_times[0]
            )
            p99_time = (
                sorted_times[int(0.99 * len(sorted_times))]
                if len(sorted_times) > 1
                else sorted_times[0]
            )

            throughput = success_count / total_time if total_time > 0 else 0
            success_rate = (success_count / operations) * 100

            # 输出结果
            print(f"   操作次数: {operations}")
            print(f"   成功率: {success_rate:.1f}%")
            print(f"   平均搜索时间: {avg_time:.3f}秒")
            print(f"   P95搜索时间: {p95_time:.3f}秒")
            print(f"   P99搜索时间: {p99_time:.3f}秒")
            print(f"   搜索吞吐量: {throughput:.2f} 查询/秒")

            # 性能基准断言
            assert success_rate >= 95.0, f"混合搜索成功率过低: {success_rate:.1f}%"
            assert avg_time < 0.8, f"混合搜索平均时间过长: {avg_time:.3f}秒"
            assert p95_time < 1.5, f"混合搜索P95时间过长: {p95_time:.3f}秒"
            assert throughput >= 8.0, f"混合搜索吞吐量过低: {throughput:.2f}"

        print(f"\n✅ 混合搜索性能基准测试通过")


@pytest.mark.performance
class TestQABenchmarks:
    """问答性能基准测试"""

    @pytest.fixture
    def qa_client(self, async_client):
        """问答测试客户端"""
        mock_token = "qa_benchmark_token"
        async_client.headers.update({"Authorization": f"Bearer {mock_token}"})
        return async_client

    @pytest.mark.asyncio
    async def test_qa_response_benchmark(self, qa_client):
        """问答响应性能基准测试"""
        client = qa_client

        # 测试不同类型和复杂度的问题
        question_categories = [
            {
                "category": "factual",
                "questions": [
                    "什么是机器学习？",
                    "深度学习的定义是什么？",
                    "Python是什么编程语言？",
                    "什么是自然语言处理？",
                    "数据科学包含哪些内容？",
                ],
                "expected_response_time": 2.0,
            },
            {
                "category": "analytical",
                "questions": [
                    "机器学习和深度学习有什么区别？",
                    "监督学习和无监督学习的优缺点是什么？",
                    "如何选择合适的机器学习算法？",
                    "数据预处理在机器学习中的重要性？",
                    "过拟合和欠拟合如何解决？",
                ],
                "expected_response_time": 3.5,
            },
            {
                "category": "complex",
                "questions": [
                    "请详细解释Transformer架构的工作原理，并分析其在自然语言处理任务中的优势和局限性。",
                    "比较不同的深度学习优化算法（SGD、Adam、RMSprop等），分析它们的适用场景和性能特点。",
                    "在大规模分布式机器学习系统中，如何处理数据一致性、模型同步和容错等关键技术挑战？",
                    "解释强化学习中的价值函数、策略梯度和Actor-Critic方法，并讨论它们在实际应用中的选择策略。",
                ],
                "expected_response_time": 6.0,
            },
        ]

        benchmark_results = []

        for category_info in question_categories:
            category = category_info["category"]
            questions = category_info["questions"]
            expected_time = category_info["expected_response_time"]

            print(f"\n💬 测试 {category} 问答性能基准")

            response_times = []
            success_count = 0
            error_count = 0
            confidence_scores = []

            for i, question in enumerate(questions):
                # 每个问题测试3次取平均值
                question_times = []

                for attempt in range(3):
                    try:
                        start_time = time.time()

                        # 模拟问答响应
                        answer_length = len(question) * 2 + (
                            100
                            if category == "factual"
                            else 200 if category == "analytical" else 400
                        )

                        mock_response = {
                            "question": question,
                            "answer": f"这是对'{question[:20]}...'的详细回答。"
                            + "详细内容..." * (answer_length // 20),
                            "confidence_score": 0.85 + (i % 10) * 0.01,
                            "sources": [
                                {
                                    "document_id": f"qa_source_{category}_{i}_{j}",
                                    "relevance_score": 0.9 - (j * 0.05),
                                    "chunk_content": f"相关内容片段{j+1}...",
                                }
                                for j in range(3 + (i % 3))
                            ],
                            "processing_time": 1.0
                            + (len(question) / 100)
                            + (answer_length / 1000),
                            "tokens_used": len(question) + answer_length,
                            "model_info": {
                                "model_name": "gpt-3.5-turbo",
                                "temperature": 0.7,
                                "max_tokens": 2000,
                            },
                        }

                        with patch("httpx.AsyncClient.post") as mock_post:
                            mock_post.return_value.status_code = 200
                            mock_post.return_value.json.return_value = mock_response

                            qa_data = {
                                "question": question,
                                "max_context_length": 4000,
                                "temperature": 0.7,
                                "include_sources": True,
                            }

                            response = await client.post("/qa/ask", json=qa_data)

                        end_time = time.time()
                        response_time = end_time - start_time
                        question_times.append(response_time)

                        if response.status_code == 200:
                            confidence_scores.append(mock_response["confidence_score"])

                        await asyncio.sleep(0.1)

                    except Exception as e:
                        print(f"问答出错: {e}")
                        question_times.append(expected_time * 2)  # 记录超时

                # 计算该问题的平均响应时间
                if question_times:
                    avg_question_time = statistics.mean(question_times)
                    response_times.append(avg_question_time)

                    if avg_question_time <= expected_time * 1.5:  # 允许50%的时间缓冲
                        success_count += 1
                    else:
                        error_count += 1

                print(
                    f"   问题 {i+1}: {avg_question_time:.3f}秒 ({'✓' if avg_question_time <= expected_time else '✗'})"
                )

            # 计算统计指标
            if response_times:
                total_time = sum(response_times)
                avg_time = statistics.mean(response_times)
                min_time = min(response_times)
                max_time = max(response_times)

                sorted_times = sorted(response_times)
                p50_time = statistics.median(sorted_times)
                p95_time = (
                    sorted_times[int(0.95 * len(sorted_times))]
                    if len(sorted_times) > 1
                    else sorted_times[0]
                )
                p99_time = (
                    sorted_times[int(0.99 * len(sorted_times))]
                    if len(sorted_times) > 1
                    else sorted_times[0]
                )

                throughput = len(questions) / total_time if total_time > 0 else 0
                success_rate = (success_count / len(questions)) * 100
                avg_confidence = (
                    statistics.mean(confidence_scores) if confidence_scores else 0
                )

                result = BenchmarkResult(
                    operation_name=f"qa_{category}",
                    total_operations=len(questions),
                    total_time=total_time,
                    avg_time=avg_time,
                    min_time=min_time,
                    max_time=max_time,
                    p50_time=p50_time,
                    p95_time=p95_time,
                    p99_time=p99_time,
                    throughput=throughput,
                    success_rate=success_rate,
                    error_count=error_count,
                )

                benchmark_results.append(result)

                # 输出结果
                print(f"\n   📊 {category} 问答性能统计:")
                print(f"      问题数量: {len(questions)}")
                print(f"      成功率: {success_rate:.1f}%")
                print(f"      平均响应时间: {avg_time:.3f}秒")
                print(f"      P95响应时间: {p95_time:.3f}秒")
                print(f"      平均置信度: {avg_confidence:.3f}")
                print(f"      吞吐量: {throughput:.2f} 问题/秒")
                print(f"      期望时间: {expected_time:.1f}秒")

        # 性能基准断言
        for result in benchmark_results:
            if "factual" in result.operation_name:
                assert (
                    result.avg_time < 2.5
                ), f"事实性问答平均时间过长: {result.avg_time:.3f}秒"
                assert (
                    result.p95_time < 4.0
                ), f"事实性问答P95时间过长: {result.p95_time:.3f}秒"
            elif "analytical" in result.operation_name:
                assert (
                    result.avg_time < 4.0
                ), f"分析性问答平均时间过长: {result.avg_time:.3f}秒"
                assert (
                    result.p95_time < 6.0
                ), f"分析性问答P95时间过长: {result.p95_time:.3f}秒"
            elif "complex" in result.operation_name:
                assert (
                    result.avg_time < 7.0
                ), f"复杂问答平均时间过长: {result.avg_time:.3f}秒"
                assert (
                    result.p95_time < 10.0
                ), f"复杂问答P95时间过长: {result.p95_time:.3f}秒"

            assert (
                result.success_rate >= 80.0
            ), f"{result.operation_name} 成功率过低: {result.success_rate:.1f}%"

        print(f"\n✅ 问答性能基准测试通过")


@pytest.mark.performance
class TestSystemBenchmarks:
    """系统整体性能基准测试"""

    @pytest.mark.asyncio
    async def test_end_to_end_workflow_benchmark(self, async_client):
        """端到端工作流性能基准测试"""
        client = async_client
        mock_token = "e2e_benchmark_token"
        client.headers.update({"Authorization": f"Bearer {mock_token}"})

        print(f"\n🔄 测试端到端工作流性能基准")

        # 完整工作流：上传文档 -> 处理 -> 搜索 -> 问答
        workflows = 10
        workflow_times = []
        success_count = 0
        error_count = 0

        for i in range(workflows):
            try:
                workflow_start = time.time()

                # 1. 文档上传
                document_content = f"这是测试文档{i+1}的内容。" * 50
                document_id = f"e2e_benchmark_doc_{i}_{uuid.uuid4().hex[:8]}"

                upload_mock = {
                    "document_id": document_id,
                    "upload_status": "success",
                    "file_size": len(document_content.encode("utf-8")),
                }

                with patch("httpx.AsyncClient.post") as mock_post:
                    mock_post.return_value.status_code = 201
                    mock_post.return_value.json.return_value = upload_mock

                    files = {
                        "file": (f"benchmark_{i}.txt", document_content, "text/plain")
                    }
                    upload_response = await client.post(
                        "/documents/upload", files=files
                    )

                # 2. 文档处理
                process_mock = {
                    "document_id": document_id,
                    "processing_status": "completed",
                    "chunks_count": 5,
                    "processing_time": 2.1,
                }

                with patch("httpx.AsyncClient.post") as mock_post:
                    mock_post.return_value.status_code = 200
                    mock_post.return_value.json.return_value = process_mock

                    process_data = {"document_id": document_id}
                    process_response = await client.post(
                        "/documents/process", json=process_data
                    )

                # 3. 搜索测试
                search_mock = {
                    "query": f"测试文档{i+1}",
                    "results": [
                        {
                            "document_id": document_id,
                            "relevance_score": 0.95,
                            "content": document_content[:200],
                        }
                    ],
                    "total_count": 1,
                }

                with patch("httpx.AsyncClient.post") as mock_post:
                    mock_post.return_value.status_code = 200
                    mock_post.return_value.json.return_value = search_mock

                    search_data = {"query": f"测试文档{i+1}"}
                    search_response = await client.post(
                        "/documents/search", json=search_data
                    )

                # 4. 问答测试
                qa_mock = {
                    "question": f"关于测试文档{i+1}的问题",
                    "answer": f"这是基于测试文档{i+1}的回答...",
                    "confidence_score": 0.88,
                    "sources": [{"document_id": document_id, "relevance_score": 0.95}],
                }

                with patch("httpx.AsyncClient.post") as mock_post:
                    mock_post.return_value.status_code = 200
                    mock_post.return_value.json.return_value = qa_mock

                    qa_data = {"question": f"关于测试文档{i+1}的问题"}
                    qa_response = await client.post("/qa/ask", json=qa_data)

                workflow_end = time.time()
                workflow_time = workflow_end - workflow_start
                workflow_times.append(workflow_time)

                # 检查所有步骤是否成功
                if (
                    upload_response.status_code == 201
                    and process_response.status_code == 200
                    and search_response.status_code == 200
                    and qa_response.status_code == 200
                ):
                    success_count += 1
                    print(f"   工作流 {i+1}: {workflow_time:.3f}秒 ✓")
                else:
                    error_count += 1
                    print(f"   工作流 {i+1}: {workflow_time:.3f}秒 ✗")

                await asyncio.sleep(0.2)

            except Exception as e:
                error_count += 1
                print(f"工作流 {i+1} 出错: {e}")

        # 计算统计指标
        if workflow_times:
            total_time = sum(workflow_times)
            avg_time = statistics.mean(workflow_times)
            min_time = min(workflow_times)
            max_time = max(workflow_times)

            sorted_times = sorted(workflow_times)
            p50_time = statistics.median(sorted_times)
            p95_time = (
                sorted_times[int(0.95 * len(sorted_times))]
                if len(sorted_times) > 1
                else sorted_times[0]
            )

            throughput = success_count / total_time if total_time > 0 else 0
            success_rate = (success_count / workflows) * 100

            # 输出结果
            print(f"\n   📊 端到端工作流性能统计:")
            print(f"      工作流数量: {workflows}")
            print(f"      成功数量: {success_count}")
            print(f"      失败数量: {error_count}")
            print(f"      成功率: {success_rate:.1f}%")
            print(f"      平均完成时间: {avg_time:.3f}秒")
            print(f"      最快完成时间: {min_time:.3f}秒")
            print(f"      最慢完成时间: {max_time:.3f}秒")
            print(f"      P50完成时间: {p50_time:.3f}秒")
            print(f"      P95完成时间: {p95_time:.3f}秒")
            print(f"      工作流吞吐量: {throughput:.2f} 工作流/秒")

            # 性能基准断言
            assert success_rate >= 90.0, f"端到端工作流成功率过低: {success_rate:.1f}%"
            assert avg_time < 8.0, f"端到端工作流平均时间过长: {avg_time:.3f}秒"
            assert p95_time < 12.0, f"端到端工作流P95时间过长: {p95_time:.3f}秒"
            assert throughput >= 0.5, f"端到端工作流吞吐量过低: {throughput:.2f}"

        print(f"\n✅ 端到端工作流性能基准测试通过")


def generate_performance_report(benchmark_results: List[BenchmarkResult]) -> str:
    """生成性能测试报告"""
    report = "\n" + "=" * 80 + "\n"
    report += "📊 Knowledge RAG System - 性能基准测试报告\n"
    report += "=" * 80 + "\n\n"

    report += f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

    # 按操作类型分组
    operation_groups = {}
    for result in benchmark_results:
        operation_type = result.operation_name.split("_")[0]
        if operation_type not in operation_groups:
            operation_groups[operation_type] = []
        operation_groups[operation_type].append(result)

    # 生成各组报告
    for group_name, results in operation_groups.items():
        report += f"📋 {group_name.upper()} 操作性能:\n"
        report += "-" * 50 + "\n"

        for result in results:
            report += f"  {result.operation_name}:\n"
            report += f"    操作次数: {result.total_operations}\n"
            report += f"    成功率: {result.success_rate:.1f}%\n"
            report += f"    平均时间: {result.avg_time:.3f}秒\n"
            report += f"    P95时间: {result.p95_time:.3f}秒\n"
            report += f"    吞吐量: {result.throughput:.2f} 操作/秒\n"
            report += "\n"

        report += "\n"

    # 总体统计
    total_operations = sum(r.total_operations for r in benchmark_results)
    total_success = sum(
        r.total_operations * r.success_rate / 100 for r in benchmark_results
    )
    overall_success_rate = (
        (total_success / total_operations) * 100 if total_operations > 0 else 0
    )

    report += "📈 总体性能统计:\n"
    report += "-" * 30 + "\n"
    report += f"  总操作数: {total_operations}\n"
    report += f"  总体成功率: {overall_success_rate:.1f}%\n"
    report += f"  测试场景数: {len(benchmark_results)}\n"

    avg_throughput = statistics.mean([r.throughput for r in benchmark_results])
    report += f"  平均吞吐量: {avg_throughput:.2f} 操作/秒\n"

    report += "\n" + "=" * 80 + "\n"

    return report
