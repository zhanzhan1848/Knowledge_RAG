# Azure OpenAI集成技术方案

## 文档信息
- **创建日期**: 2024年1月
- **版本**: v1.0
- **负责人**: AI工程师团队
- **项目**: Knowledge_RAG智能知识管理系统

## 1. 执行摘要

本文档详细说明了Knowledge_RAG项目中Azure OpenAI服务的集成方案，包括模型选择、架构设计、API配置、成本控制和性能优化策略。通过Azure OpenAI服务，系统将实现高质量的文本嵌入、智能问答和GraphRAG增强检索功能。

## 2. 技术选型决策

### 2.1 Azure OpenAI vs 其他方案

| 评估维度 | Azure OpenAI | OpenAI直连 | 开源模型 |
|----------|--------------|------------|----------|
| **企业级安全** | ✅ 优秀 | ⚠️ 一般 | ✅ 优秀 |
| **数据隐私** | ✅ 符合企业要求 | ❌ 数据可能用于训练 | ✅ 完全控制 |
| **服务稳定性** | ✅ 99.9% SLA | ⚠️ 无SLA保证 | ❌ 需自维护 |
| **成本控制** | ✅ 企业定价 | ⚠️ 按量付费 | ✅ 硬件成本 |
| **模型性能** | ✅ GPT-4/3.5-turbo | ✅ 最新模型 | ⚠️ 性能差异大 |
| **合规认证** | ✅ SOC2/ISO27001 | ⚠️ 部分认证 | ❌ 需自建 |

**决策结果**: 选择Azure OpenAI，理由如下：
- 企业级安全和合规要求
- 数据隐私保护（数据不用于模型训练）
- 稳定的SLA保证和技术支持
- 与Azure生态系统的无缝集成

### 2.2 模型选择策略

#### 文本嵌入模型
- **主选**: `text-embedding-ada-002`
  - 向量维度: 1536
  - 最大输入: 8191 tokens
  - 成本: $0.0001/1K tokens
  - 适用场景: 文档向量化、语义检索

#### 对话生成模型
- **主选**: `gpt-4-turbo` (gpt-4-1106-preview)
  - 上下文窗口: 128K tokens
  - 输出限制: 4096 tokens
  - 成本: $0.01/1K input tokens, $0.03/1K output tokens
  - 适用场景: 复杂推理、GraphRAG问答

- **备选**: `gpt-35-turbo-16k`
  - 上下文窗口: 16K tokens
  - 成本: $0.003/1K input tokens, $0.004/1K output tokens
  - 适用场景: 简单问答、成本敏感场景

## 3. 系统架构设计

### 3.1 整体架构

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  客户端应用     │    │   API网关        │    │  LLM服务层      │
│                 │    │                  │    │                 │
│ - REST API      │◄──►│ - 路由管理       │◄──►│ - Azure OpenAI  │
│ - GraphQL API   │    │ - 认证授权       │    │ - 请求管理      │
│ - Webhook API   │    │ - 限流控制       │    │ - 缓存层        │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                ▲                        ▲
                                │                        │
                                ▼                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  GraphRAG引擎   │    │   向量数据库     │    │   知识图谱      │
│                 │    │                  │    │                 │
│ - 混合检索      │◄──►│ - Weaviate       │◄──►│ - Neo4j         │
│ - 上下文构建    │    │ - 向量索引       │    │ - 实体关系      │
│ - 答案生成      │    │ - 相似性搜索     │    │ - 图谱推理      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### 3.2 LLM服务层架构

```python
# LLM服务层组件设计

# 1. Azure OpenAI客户端管理
class AzureOpenAIClient:
    """
    Azure OpenAI客户端管理器
    负责连接管理、请求路由和错误处理
    """
    def __init__(self, endpoint: str, api_key: str, api_version: str)
    def get_embedding(self, text: str, model: str) -> List[float]
    def chat_completion(self, messages: List[dict], model: str, **kwargs) -> str
    def stream_completion(self, messages: List[dict], model: str) -> Iterator[str]

# 2. 请求管理和缓存
class LLMRequestManager:
    """
    LLM请求管理器
    实现请求缓存、限流和重试机制
    """
    def __init__(self, cache_backend: str, rate_limiter: RateLimiter)
    def cached_embedding(self, text: str) -> List[float]
    def cached_completion(self, prompt: str, cache_key: str) -> str

# 3. 成本监控和控制
class CostMonitor:
    """
    成本监控器
    跟踪API使用量和成本，实现预算控制
    """
    def track_usage(self, model: str, input_tokens: int, output_tokens: int)
    def check_budget_limit(self, user_id: str) -> bool
    def generate_cost_report(self, period: str) -> dict
```

## 4. API配置和集成

### 4.1 Azure OpenAI服务配置

```yaml
# config/azure_openai.yaml
azure_openai:
  # 基础配置
  endpoint: "https://your-resource.openai.azure.com/"
  api_version: "2024-02-15-preview"
  
  # 模型部署配置
  deployments:
    embedding:
      model: "text-embedding-ada-002"
      deployment_name: "text-embedding-ada-002"
      max_tokens: 8191
      
    chat_gpt4:
      model: "gpt-4-turbo"
      deployment_name: "gpt-4-turbo"
      max_tokens: 128000
      temperature: 0.1
      
    chat_gpt35:
      model: "gpt-35-turbo-16k"
      deployment_name: "gpt-35-turbo-16k"
      max_tokens: 16000
      temperature: 0.1

  # 限流配置
  rate_limits:
    embedding:
      requests_per_minute: 3000
      tokens_per_minute: 1000000
    chat_gpt4:
      requests_per_minute: 300
      tokens_per_minute: 40000
    chat_gpt35:
      requests_per_minute: 3000
      tokens_per_minute: 240000

  # 重试配置
  retry:
    max_attempts: 3
    backoff_factor: 2
    timeout: 30
```

### 4.2 环境变量配置

```bash
# .env 文件
# Azure OpenAI配置
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# 部署名称
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002
AZURE_OPENAI_GPT4_DEPLOYMENT=gpt-4-turbo
AZURE_OPENAI_GPT35_DEPLOYMENT=gpt-35-turbo-16k

# 缓存配置
REDIS_URL=redis://localhost:6379/0
CACHE_TTL=3600

# 成本控制
DAILY_BUDGET_LIMIT=100.00
MONTHLY_BUDGET_LIMIT=3000.00
```

## 5. 核心功能实现

### 5.1 文档向量化服务

```python
# services/embedding_service.py

from typing import List, Dict, Optional
from dataclasses import dataclass
import hashlib
import json

@dataclass
class EmbeddingRequest:
    """
    向量化请求数据结构
    """
    text: str
    document_id: Optional[str] = None
    chunk_id: Optional[str] = None
    metadata: Optional[Dict] = None

class DocumentEmbeddingService:
    """
    文档向量化服务
    负责文档分块、向量化和存储
    """
    
    def __init__(self, 
                 azure_client: AzureOpenAIClient,
                 vector_db: VectorDatabase,
                 cache_manager: CacheManager):
        self.azure_client = azure_client
        self.vector_db = vector_db
        self.cache_manager = cache_manager
    
    async def process_document(self, 
                              document: str, 
                              document_id: str,
                              chunk_size: int = 1000,
                              overlap: int = 200) -> List[str]:
        """
        处理文档：分块、向量化、存储
        
        Args:
            document: 文档内容
            document_id: 文档唯一标识
            chunk_size: 分块大小
            overlap: 重叠大小
            
        Returns:
            List[str]: 分块ID列表
        """
        # 1. 文档分块
        chunks = self._chunk_document(document, chunk_size, overlap)
        
        # 2. 批量向量化
        embeddings = await self._batch_embed_chunks(chunks)
        
        # 3. 存储到向量数据库
        chunk_ids = await self._store_embeddings(
            document_id, chunks, embeddings
        )
        
        return chunk_ids
    
    def _chunk_document(self, 
                       document: str, 
                       chunk_size: int, 
                       overlap: int) -> List[str]:
        """
        文档分块算法
        使用滑动窗口方式进行分块，保持语义连贯性
        """
        # 按句子分割
        sentences = self._split_sentences(document)
        chunks = []
        current_chunk = ""
        current_length = 0
        
        for sentence in sentences:
            sentence_length = len(sentence)
            
            # 如果加入当前句子超过chunk_size，保存当前chunk
            if current_length + sentence_length > chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                
                # 计算重叠部分
                overlap_text = self._get_overlap_text(current_chunk, overlap)
                current_chunk = overlap_text + " " + sentence
                current_length = len(current_chunk)
            else:
                current_chunk += " " + sentence
                current_length += sentence_length
        
        # 添加最后一个chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks
    
    async def _batch_embed_chunks(self, chunks: List[str]) -> List[List[float]]:
        """
        批量向量化文本块
        实现缓存和并发处理
        """
        embeddings = []
        batch_size = 16  # Azure OpenAI建议的批处理大小
        
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            batch_embeddings = []
            
            for chunk in batch:
                # 检查缓存
                cache_key = self._get_embedding_cache_key(chunk)
                cached_embedding = await self.cache_manager.get(cache_key)
                
                if cached_embedding:
                    batch_embeddings.append(cached_embedding)
                else:
                    # 调用Azure OpenAI API
                    embedding = await self.azure_client.get_embedding(
                        text=chunk,
                        model="text-embedding-ada-002"
                    )
                    batch_embeddings.append(embedding)
                    
                    # 缓存结果
                    await self.cache_manager.set(
                        cache_key, embedding, ttl=86400  # 24小时
                    )
            
            embeddings.extend(batch_embeddings)
        
        return embeddings
    
    def _get_embedding_cache_key(self, text: str) -> str:
        """
        生成嵌入向量的缓存键
        """
        text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
        return f"embedding:ada002:{text_hash}"
```

### 5.2 GraphRAG问答服务

```python
# services/graphrag_service.py

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import asyncio

@dataclass
class GraphRAGContext:
    """
    GraphRAG上下文数据结构
    """
    vector_results: List[Dict]  # 向量检索结果
    graph_results: List[Dict]   # 图谱检索结果
    entities: List[str]         # 识别的实体
    relationships: List[Dict]   # 相关关系
    confidence_score: float     # 置信度分数

class GraphRAGService:
    """
    GraphRAG问答服务
    结合向量检索和知识图谱进行增强检索生成
    """
    
    def __init__(self,
                 azure_client: AzureOpenAIClient,
                 vector_db: VectorDatabase,
                 graph_db: GraphDatabase,
                 entity_extractor: EntityExtractor):
        self.azure_client = azure_client
        self.vector_db = vector_db
        self.graph_db = graph_db
        self.entity_extractor = entity_extractor
    
    async def answer_question(self, 
                             question: str, 
                             user_id: str,
                             conversation_history: Optional[List[Dict]] = None) -> Dict:
        """
        回答用户问题
        
        Args:
            question: 用户问题
            user_id: 用户ID
            conversation_history: 对话历史
            
        Returns:
            Dict: 包含答案、来源、置信度等信息
        """
        # 1. 问题预处理和实体识别
        processed_question = await self._preprocess_question(
            question, conversation_history
        )
        entities = await self.entity_extractor.extract_entities(processed_question)
        
        # 2. 混合检索
        context = await self._hybrid_retrieval(
            processed_question, entities, top_k=10
        )
        
        # 3. 上下文构建和答案生成
        answer_data = await self._generate_answer(
            processed_question, context, user_id
        )
        
        return answer_data
    
    async def _hybrid_retrieval(self, 
                               question: str, 
                               entities: List[str],
                               top_k: int = 10) -> GraphRAGContext:
        """
        混合检索：结合向量检索和图谱检索
        """
        # 并行执行向量检索和图谱检索
        vector_task = self._vector_retrieval(question, top_k)
        graph_task = self._graph_retrieval(entities, top_k)
        
        vector_results, graph_results = await asyncio.gather(
            vector_task, graph_task
        )
        
        # 获取相关关系
        relationships = await self._get_entity_relationships(entities)
        
        # 计算整体置信度
        confidence_score = self._calculate_confidence(
            vector_results, graph_results, entities
        )
        
        return GraphRAGContext(
            vector_results=vector_results,
            graph_results=graph_results,
            entities=entities,
            relationships=relationships,
            confidence_score=confidence_score
        )
    
    async def _generate_answer(self, 
                              question: str, 
                              context: GraphRAGContext,
                              user_id: str) -> Dict:
        """
        基于检索上下文生成答案
        """
        # 构建提示词
        prompt = self._build_rag_prompt(question, context)
        
        # 选择合适的模型
        model = self._select_model(context, user_id)
        
        # 生成答案
        messages = [
            {"role": "system", "content": self._get_system_prompt()},
            {"role": "user", "content": prompt}
        ]
        
        response = await self.azure_client.chat_completion(
            messages=messages,
            model=model,
            temperature=0.1,
            max_tokens=1000
        )
        
        # 提取引用来源
        sources = self._extract_sources(context)
        
        return {
            "answer": response,
            "sources": sources,
            "confidence": context.confidence_score,
            "entities": context.entities,
            "model_used": model,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _build_rag_prompt(self, question: str, context: GraphRAGContext) -> str:
        """
        构建RAG提示词
        """
        prompt_parts = [
            "基于以下知识库内容回答问题：\n",
            "\n=== 相关文档片段 ==="
        ]
        
        # 添加向量检索结果
        for i, result in enumerate(context.vector_results[:5]):
            prompt_parts.append(
                f"\n[文档{i+1}] {result['content']}\n来源: {result['source']}"
            )
        
        # 添加知识图谱信息
        if context.entities:
            prompt_parts.append("\n=== 相关实体和关系 ===")
            for entity in context.entities[:5]:
                prompt_parts.append(f"\n实体: {entity}")
            
            for rel in context.relationships[:5]:
                prompt_parts.append(
                    f"\n关系: {rel['source']} -> {rel['relation']} -> {rel['target']}"
                )
        
        prompt_parts.extend([
            "\n\n=== 回答要求 ===",
            "1. 基于上述内容回答问题，确保答案准确可靠",
            "2. 如果信息不足，请明确说明",
            "3. 引用具体的文档来源支持你的答案",
            "4. 保持回答简洁明了，重点突出\n",
            f"\n问题: {question}\n\n答案:"
        ])
        
        return "".join(prompt_parts)
```

## 6. 成本控制和监控

### 6.1 成本预算管理

```python
# services/cost_management.py

from typing import Dict, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

@dataclass
class UsageMetrics:
    """
    使用量指标数据结构
    """
    model: str
    input_tokens: int
    output_tokens: int
    requests: int
    cost: float
    timestamp: datetime

class CostManagementService:
    """
    成本管理服务
    实现预算控制、使用量监控和成本优化
    """
    
    def __init__(self, 
                 redis_client: Redis,
                 database: Database,
                 budget_config: Dict):
        self.redis = redis_client
        self.db = database
        self.budget_config = budget_config
        
        # 模型定价（每1K tokens）
        self.pricing = {
            "text-embedding-ada-002": {"input": 0.0001, "output": 0},
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
            "gpt-35-turbo-16k": {"input": 0.003, "output": 0.004}
        }
    
    async def check_budget_limit(self, 
                                user_id: str, 
                                estimated_cost: float) -> bool:
        """
        检查预算限制
        
        Args:
            user_id: 用户ID
            estimated_cost: 预估成本
            
        Returns:
            bool: 是否在预算范围内
        """
        # 获取当前使用量
        daily_usage = await self._get_daily_usage(user_id)
        monthly_usage = await self._get_monthly_usage(user_id)
        
        # 检查日预算
        daily_limit = self.budget_config.get("daily_limit", 10.0)
        if daily_usage + estimated_cost > daily_limit:
            return False
        
        # 检查月预算
        monthly_limit = self.budget_config.get("monthly_limit", 300.0)
        if monthly_usage + estimated_cost > monthly_limit:
            return False
        
        return True
    
    async def track_usage(self, 
                         user_id: str,
                         model: str,
                         input_tokens: int,
                         output_tokens: int = 0) -> float:
        """
        跟踪API使用量和成本
        
        Returns:
            float: 本次请求的成本
        """
        # 计算成本
        pricing = self.pricing.get(model, {"input": 0.01, "output": 0.03})
        cost = (
            (input_tokens / 1000) * pricing["input"] +
            (output_tokens / 1000) * pricing["output"]
        )
        
        # 记录使用量
        metrics = UsageMetrics(
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            requests=1,
            cost=cost,
            timestamp=datetime.utcnow()
        )
        
        # 存储到数据库
        await self._store_usage_metrics(user_id, metrics)
        
        # 更新Redis缓存
        await self._update_usage_cache(user_id, cost)
        
        return cost
    
    async def generate_cost_report(self, 
                                  period: str = "monthly",
                                  user_id: Optional[str] = None) -> Dict:
        """
        生成成本报告
        
        Args:
            period: 报告周期 (daily/weekly/monthly)
            user_id: 用户ID（可选，为空则生成全局报告）
            
        Returns:
            Dict: 成本报告数据
        """
        # 计算时间范围
        end_date = datetime.utcnow()
        if period == "daily":
            start_date = end_date - timedelta(days=1)
        elif period == "weekly":
            start_date = end_date - timedelta(weeks=1)
        else:  # monthly
            start_date = end_date - timedelta(days=30)
        
        # 查询使用数据
        usage_data = await self._query_usage_data(
            start_date, end_date, user_id
        )
        
        # 生成报告
        report = {
            "period": period,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_cost": sum(item["cost"] for item in usage_data),
            "total_requests": sum(item["requests"] for item in usage_data),
            "total_tokens": sum(
                item["input_tokens"] + item["output_tokens"] 
                for item in usage_data
            ),
            "model_breakdown": self._calculate_model_breakdown(usage_data),
            "daily_trend": self._calculate_daily_trend(usage_data),
            "top_users": self._get_top_users(usage_data) if not user_id else None
        }
        
        return report
```

### 6.2 性能监控和优化

```python
# services/performance_monitor.py

from typing import Dict, List, Optional
import time
import asyncio
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class PerformanceMetrics:
    """
    性能指标数据结构
    """
    endpoint: str
    model: str
    response_time: float
    token_count: int
    cache_hit: bool
    error_occurred: bool
    timestamp: datetime

class PerformanceMonitor:
    """
    性能监控服务
    监控API响应时间、缓存命中率、错误率等指标
    """
    
    def __init__(self, metrics_storage: MetricsStorage):
        self.metrics_storage = metrics_storage
        self.response_times = defaultdict(list)
        self.cache_stats = defaultdict(int)
        self.error_counts = defaultdict(int)
    
    async def monitor_request(self, 
                             endpoint: str,
                             model: str,
                             func, 
                             *args, 
                             **kwargs):
        """
        监控API请求性能
        
        Args:
            endpoint: API端点
            model: 使用的模型
            func: 要监控的函数
            *args, **kwargs: 函数参数
            
        Returns:
            函数执行结果
        """
        start_time = time.time()
        cache_hit = kwargs.get('from_cache', False)
        error_occurred = False
        token_count = 0
        
        try:
            result = await func(*args, **kwargs)
            
            # 提取token数量
            if hasattr(result, 'usage'):
                token_count = result.usage.total_tokens
            
            return result
            
        except Exception as e:
            error_occurred = True
            self.error_counts[f"{endpoint}:{model}"] += 1
            raise
            
        finally:
            # 记录性能指标
            response_time = time.time() - start_time
            
            metrics = PerformanceMetrics(
                endpoint=endpoint,
                model=model,
                response_time=response_time,
                token_count=token_count,
                cache_hit=cache_hit,
                error_occurred=error_occurred,
                timestamp=datetime.utcnow()
            )
            
            await self._record_metrics(metrics)
    
    async def get_performance_summary(self, 
                                    period_hours: int = 24) -> Dict:
        """
        获取性能摘要报告
        
        Args:
            period_hours: 统计周期（小时）
            
        Returns:
            Dict: 性能摘要数据
        """
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=period_hours)
        
        metrics = await self.metrics_storage.query_metrics(
            start_time, end_time
        )
        
        # 计算统计指标
        summary = {
            "period": f"{period_hours}h",
            "total_requests": len(metrics),
            "avg_response_time": self._calculate_avg_response_time(metrics),
            "p95_response_time": self._calculate_percentile(metrics, 95),
            "p99_response_time": self._calculate_percentile(metrics, 99),
            "cache_hit_rate": self._calculate_cache_hit_rate(metrics),
            "error_rate": self._calculate_error_rate(metrics),
            "model_performance": self._analyze_model_performance(metrics),
            "slowest_endpoints": self._get_slowest_endpoints(metrics)
        }
        
        return summary
    
    def _calculate_avg_response_time(self, metrics: List[PerformanceMetrics]) -> float:
        """
        计算平均响应时间
        """
        if not metrics:
            return 0.0
        
        total_time = sum(m.response_time for m in metrics)
        return total_time / len(metrics)
    
    def _calculate_cache_hit_rate(self, metrics: List[PerformanceMetrics]) -> float:
        """
        计算缓存命中率
        """
        if not metrics:
            return 0.0
        
        cache_hits = sum(1 for m in metrics if m.cache_hit)
        return cache_hits / len(metrics) * 100
```

## 7. 安全和合规

### 7.1 数据安全措施

1. **API密钥管理**
   - 使用Azure Key Vault存储API密钥
   - 实现密钥轮换机制
   - 限制密钥访问权限

2. **数据传输安全**
   - 所有API调用使用HTTPS/TLS 1.2+
   - 实现请求签名验证
   - 敏感数据加密传输

3. **数据隐私保护**
   - 用户数据不用于模型训练
   - 实现数据脱敏和匿名化
   - 遵循GDPR和数据保护法规

### 7.2 访问控制

```python
# security/access_control.py

from typing import Dict, List, Optional
from enum import Enum

class UserRole(Enum):
    """
    用户角色枚举
    """
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"

class AccessControlService:
    """
    访问控制服务
    实现基于角色的访问控制（RBAC）
    """
    
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        
        # 角色权限配置
        self.role_permissions = {
            UserRole.ADMIN: {
                "daily_requests": 10000,
                "monthly_budget": 1000.0,
                "models": ["gpt-4-turbo", "gpt-35-turbo-16k", "text-embedding-ada-002"],
                "features": ["graphrag", "embedding", "chat", "admin"]
            },
            UserRole.USER: {
                "daily_requests": 1000,
                "monthly_budget": 100.0,
                "models": ["gpt-35-turbo-16k", "text-embedding-ada-002"],
                "features": ["graphrag", "embedding", "chat"]
            },
            UserRole.GUEST: {
                "daily_requests": 100,
                "monthly_budget": 10.0,
                "models": ["gpt-35-turbo-16k"],
                "features": ["chat"]
            }
        }
    
    async def check_permission(self, 
                              user_id: str, 
                              action: str,
                              resource: Optional[str] = None) -> bool:
        """
        检查用户权限
        
        Args:
            user_id: 用户ID
            action: 操作类型
            resource: 资源类型（可选）
            
        Returns:
            bool: 是否有权限
        """
        user_role = await self._get_user_role(user_id)
        permissions = self.role_permissions.get(user_role, {})
        
        # 检查功能权限
        if action not in permissions.get("features", []):
            return False
        
        # 检查模型权限
        if resource and resource not in permissions.get("models", []):
            return False
        
        # 检查请求限制
        daily_requests = await self._get_daily_requests(user_id)
        if daily_requests >= permissions.get("daily_requests", 0):
            return False
        
        return True
```

## 8. 基础设施部署规划

### 8.1 部署架构总览

#### 8.1.1 多环境部署策略

```
┌─────────────────────────────────────────────────────────────────┐
│                        生产环境 (Production)                    │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────┐ │
│  │   CDN/WAF   │  │ Load Balancer│  │  API Gateway │  │ Ingress │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────┘ │
│           │               │               │               │      │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                 Kubernetes集群 (AKS)                      │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐    │ │
│  │  │LLM服务Pod│ │GraphRAG  │ │向量服务  │ │缓存服务  │    │ │
│  │  │(3副本)   │ │服务Pod   │ │Pod       │ │Pod       │    │ │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘    │ │
│  └─────────────────────────────────────────────────────────────┘ │
│           │               │               │               │      │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │
│  │   Redis     │ │  PostgreSQL │ │   Weaviate  │ │    Neo4j    │ │
│  │   集群      │ │    集群     │ │    集群     │ │    集群     │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                        预发环境 (Staging)                       │
├─────────────────────────────────────────────────────────────────┤
│  相同架构，资源配置减半，用于集成测试和性能验证                  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                        开发环境 (Development)                   │
├─────────────────────────────────────────────────────────────────┤
│  单节点部署，Docker Compose，用于功能开发和单元测试             │
└─────────────────────────────────────────────────────────────────┘
```

#### 8.1.2 环境配置规格

| 环境 | 节点数量 | CPU核数 | 内存 | 存储 | 网络带宽 | 预估成本/月 |
|------|----------|---------|------|------|----------|-------------|
| **生产环境** | 6节点 | 48核 | 192GB | 2TB SSD | 10Gbps | $3,500 |
| **预发环境** | 3节点 | 24核 | 96GB | 1TB SSD | 5Gbps | $1,800 |
| **开发环境** | 1节点 | 8核 | 32GB | 500GB SSD | 1Gbps | $400 |

### 8.2 容器化和镜像管理

#### 8.2.1 多阶段Dockerfile优化

```dockerfile
# Dockerfile.llm-service
# 多阶段构建，优化镜像大小和安全性

# 第一阶段：构建阶段
FROM python:3.11-slim as builder

# 设置构建参数
ARG BUILD_ENV=production
ARG VERSION=latest

# 安装构建依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# 创建虚拟环境
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 复制uv二进制文件和依赖配置
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock ./

# 安装Python依赖
RUN if [ "$BUILD_ENV" = "development" ]; then \
        uv sync --frozen; \
    else \
        uv sync --frozen --no-dev; \
    fi

# 第二阶段：运行阶段
FROM python:3.11-slim as runtime

# 设置标签
LABEL maintainer="Knowledge_RAG Team" \
      version="$VERSION" \
      description="LLM Integration Service for Knowledge_RAG"

# 安装运行时依赖
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 复制虚拟环境
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 创建应用用户
RUN groupadd -r appgroup && useradd -r -g appgroup -u 1000 appuser

# 设置工作目录
WORKDIR /app

# 复制应用代码
COPY --chown=appuser:appgroup . .

# 设置权限
RUN chmod +x scripts/entrypoint.sh

# 切换到非root用户
USER appuser

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 暴露端口
EXPOSE 8000

# 启动脚本
ENTRYPOINT ["./scripts/entrypoint.sh"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

#### 8.2.2 启动脚本优化

```bash
#!/bin/bash
# scripts/entrypoint.sh
# 容器启动脚本，处理初始化和优雅关闭

set -e

# 环境变量验证
required_vars=(
    "AZURE_OPENAI_ENDPOINT"
    "AZURE_OPENAI_API_KEY"
    "REDIS_URL"
    "DATABASE_URL"
)

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "错误: 环境变量 $var 未设置"
        exit 1
    fi
done

# 数据库连接检查
echo "检查数据库连接..."
python -c "from services.database import check_connection; check_connection()" || {
    echo "数据库连接失败"
    exit 1
}

# Redis连接检查
echo "检查Redis连接..."
python -c "from services.cache import check_redis_connection; check_redis_connection()" || {
    echo "Redis连接失败"
    exit 1
}

# Azure OpenAI连接检查
echo "检查Azure OpenAI连接..."
python -c "from services.azure_client import check_azure_connection; check_azure_connection()" || {
    echo "Azure OpenAI连接失败"
    exit 1
}

echo "所有依赖服务连接正常，启动应用..."

# 优雅关闭处理
trap 'echo "接收到关闭信号，正在优雅关闭..."; kill -TERM $PID; wait $PID' TERM INT

# 启动应用
exec "$@" &
PID=$!
wait $PID
```

#### 8.2.3 镜像构建和推送流水线

```yaml
# .github/workflows/build-and-push.yml
name: Build and Push Docker Images

on:
  push:
    branches: [main, develop]
    tags: ['v*']
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: knowledge-rag/llm-service

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    
    steps:
    - name: Checkout代码
      uses: actions/checkout@v4
    
    - name: 设置Docker Buildx
      uses: docker/setup-buildx-action@v3
    
    - name: 登录容器注册表
      uses: docker/login-action@v3
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}
    
    - name: 提取元数据
      id: meta
      uses: docker/metadata-action@v5
      with:
        images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
        tags: |
          type=ref,event=branch
          type=ref,event=pr
          type=semver,pattern={{version}}
          type=semver,pattern={{major}}.{{minor}}
          type=sha,prefix={{branch}}-
    
    - name: 构建并推送镜像
      uses: docker/build-push-action@v5
      with:
        context: .
        file: ./Dockerfile.llm-service
        platforms: linux/amd64,linux/arm64
        push: ${{ github.event_name != 'pull_request' }}
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}
        cache-from: type=gha
        cache-to: type=gha,mode=max
        build-args: |
          BUILD_ENV=${{ github.ref == 'refs/heads/main' && 'production' || 'development' }}
          VERSION=${{ steps.meta.outputs.version }}
```

### 8.3 Kubernetes集群配置

#### 8.3.1 命名空间和资源配额

```yaml
# k8s/namespaces.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: knowledge-rag-prod
  labels:
    environment: production
    project: knowledge-rag
---
apiVersion: v1
kind: ResourceQuota
metadata:
  name: compute-quota
  namespace: knowledge-rag-prod
spec:
  hard:
    requests.cpu: "20"
    requests.memory: 80Gi
    limits.cpu: "40"
    limits.memory: 160Gi
    persistentvolumeclaims: "10"
    services: "20"
    secrets: "50"
    configmaps: "50"
---
apiVersion: v1
kind: LimitRange
metadata:
  name: mem-limit-range
  namespace: knowledge-rag-prod
spec:
  limits:
  - default:
      memory: "1Gi"
      cpu: "500m"
    defaultRequest:
      memory: "256Mi"
      cpu: "100m"
    type: Container
```

#### 8.3.2 LLM服务部署配置

```yaml
# k8s/llm-service-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: llm-service
  namespace: knowledge-rag-prod
  labels:
    app: llm-service
    version: v1.0.0
    component: ai-backend
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: llm-service
  template:
    metadata:
      labels:
        app: llm-service
        version: v1.0.0
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8000"
        prometheus.io/path: "/metrics"
    spec:
      serviceAccountName: llm-service-sa
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
      containers:
      - name: llm-service
        image: ghcr.io/knowledge-rag/llm-service:v1.0.0
        imagePullPolicy: Always
        ports:
        - name: http
          containerPort: 8000
          protocol: TCP
        - name: metrics
          containerPort: 9090
          protocol: TCP
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: LOG_LEVEL
          value: "INFO"
        - name: AZURE_OPENAI_ENDPOINT
          valueFrom:
            secretKeyRef:
              name: azure-openai-secret
              key: endpoint
        - name: AZURE_OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: azure-openai-secret
              key: api-key
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: redis-secret
              key: url
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: url
        - name: WEAVIATE_URL
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: weaviate-url
        - name: NEO4J_URL
          valueFrom:
            secretKeyRef:
              name: neo4j-secret
              key: url
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
            ephemeral-storage: "1Gi"
          limits:
            memory: "2Gi"
            cpu: "1000m"
            ephemeral-storage: "2Gi"
        livenessProbe:
          httpGet:
            path: /health
            port: http
          initialDelaySeconds: 60
          periodSeconds: 30
          timeoutSeconds: 10
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /ready
            port: http
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 5
          failureThreshold: 3
        startupProbe:
          httpGet:
            path: /startup
            port: http
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 10
        volumeMounts:
        - name: app-config
          mountPath: /app/config
          readOnly: true
        - name: logs
          mountPath: /app/logs
        - name: tmp
          mountPath: /tmp
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop:
            - ALL
      volumes:
      - name: app-config
        configMap:
          name: app-config
      - name: logs
        emptyDir:
          sizeLimit: 1Gi
      - name: tmp
        emptyDir:
          sizeLimit: 500Mi
      nodeSelector:
        kubernetes.io/arch: amd64
        node-type: compute
      tolerations:
      - key: "compute-node"
        operator: "Equal"
        value: "true"
        effect: "NoSchedule"
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - llm-service
              topologyKey: kubernetes.io/hostname
---
apiVersion: v1
kind: Service
metadata:
  name: llm-service
  namespace: knowledge-rag-prod
  labels:
    app: llm-service
  annotations:
    service.beta.kubernetes.io/aws-load-balancer-type: nlb
spec:
  type: ClusterIP
  ports:
  - name: http
    port: 80
    targetPort: http
    protocol: TCP
  - name: metrics
    port: 9090
    targetPort: metrics
    protocol: TCP
  selector:
    app: llm-service
```

#### 8.3.3 水平自动扩缩容配置

```yaml
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: llm-service-hpa
  namespace: knowledge-rag-prod
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: llm-service
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

### 8.4 配置管理和密钥管理

#### 8.4.1 ConfigMap配置

```yaml
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: knowledge-rag-prod
data:
  # 应用配置
  app.yaml: |
    server:
      host: "0.0.0.0"
      port: 8000
      workers: 4
      timeout: 30
    
    logging:
      level: "INFO"
      format: "json"
      handlers:
        - console
        - file
    
    cache:
      ttl: 3600
      max_size: 1000
    
    rate_limiting:
      enabled: true
      requests_per_minute: 1000
      burst_size: 100
  
  # 服务发现配置
  weaviate-url: "http://weaviate-service:8080"
  neo4j-url: "bolt://neo4j-service:7687"
  
  # 监控配置
  prometheus.yml: |
    global:
      scrape_interval: 15s
    scrape_configs:
    - job_name: 'llm-service'
      static_configs:
      - targets: ['localhost:9090']
```

#### 8.4.2 密钥管理

```yaml
# k8s/secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: azure-openai-secret
  namespace: knowledge-rag-prod
type: Opaque
stringData:
  endpoint: "https://your-resource.openai.azure.com/"
  api-key: "your-api-key-here"
  api-version: "2024-02-15-preview"
---
apiVersion: v1
kind: Secret
metadata:
  name: redis-secret
  namespace: knowledge-rag-prod
type: Opaque
stringData:
  url: "redis://redis-master:6379/0"
  password: "your-redis-password"
---
apiVersion: v1
kind: Secret
metadata:
  name: postgres-secret
  namespace: knowledge-rag-prod
type: Opaque
stringData:
  url: "postgresql://user:password@postgres-service:5432/knowledge_rag"
  username: "knowledge_rag_user"
  password: "your-postgres-password"
---
apiVersion: v1
kind: Secret
metadata:
  name: neo4j-secret
  namespace: knowledge-rag-prod
type: Opaque
stringData:
  url: "bolt://neo4j-service:7687"
  username: "neo4j"
  password: "your-neo4j-password"
```

### 8.5 网络和安全配置

#### 8.5.1 网络策略

```yaml
# k8s/network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: llm-service-netpol
  namespace: knowledge-rag-prod
spec:
  podSelector:
    matchLabels:
      app: llm-service
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    - podSelector:
        matchLabels:
          app: api-gateway
    ports:
    - protocol: TCP
      port: 8000
  - from:
    - namespaceSelector:
        matchLabels:
          name: monitoring
    ports:
    - protocol: TCP
      port: 9090
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: redis
    ports:
    - protocol: TCP
      port: 6379
  - to:
    - podSelector:
        matchLabels:
          app: postgres
    ports:
    - protocol: TCP
      port: 5432
  - to:
    - podSelector:
        matchLabels:
          app: weaviate
    ports:
    - protocol: TCP
      port: 8080
  - to:
    - podSelector:
        matchLabels:
          app: neo4j
    ports:
    - protocol: TCP
      port: 7687
  - to: []
    ports:
    - protocol: TCP
      port: 443  # HTTPS出站流量（Azure OpenAI）
    - protocol: TCP
      port: 53   # DNS
    - protocol: UDP
      port: 53   # DNS
```

#### 8.5.2 Pod安全策略

```yaml
# k8s/pod-security-policy.yaml
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: llm-service-psp
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
```

### 8.6 存储和数据管理

#### 8.6.1 持久化存储配置

```yaml
# k8s/storage.yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-ssd
provisioner: kubernetes.io/aws-ebs
parameters:
  type: gp3
  iops: "3000"
  throughput: "125"
  encrypted: "true"
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: llm-service-logs
  namespace: knowledge-rag-prod
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: fast-ssd
  resources:
    requests:
      storage: 10Gi
```

#### 8.6.2 数据备份策略

```yaml
# k8s/backup-cronjob.yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: llm-service-backup
  namespace: knowledge-rag-prod
spec:
  schedule: "0 2 * * *"  # 每天凌晨2点执行
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: backup-tool:latest
            env:
            - name: BACKUP_TARGET
              value: "s3://knowledge-rag-backups/llm-service"
            - name: AWS_ACCESS_KEY_ID
              valueFrom:
                secretKeyRef:
                  name: aws-secret
                  key: access-key-id
            - name: AWS_SECRET_ACCESS_KEY
              valueFrom:
                secretKeyRef:
                  name: aws-secret
                  key: secret-access-key
            command:
            - /bin/bash
            - -c
            - |
              echo "开始备份LLM服务数据..."
              # 备份配置文件
              kubectl get configmap app-config -o yaml > /tmp/configmap-backup.yaml
              # 备份到S3
              aws s3 cp /tmp/configmap-backup.yaml $BACKUP_TARGET/$(date +%Y%m%d)/
              echo "备份完成"
          restartPolicy: OnFailure
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 1
```

### 8.7 CI/CD流水线

#### 8.7.1 GitOps部署流程

```yaml
# .github/workflows/deploy.yml
name: Deploy to Kubernetes

on:
  push:
    branches: [main]
    paths:
    - 'src/**'
    - 'k8s/**'
    - 'Dockerfile*'
  workflow_dispatch:
    inputs:
      environment:
        description: '部署环境'
        required: true
        default: 'staging'
        type: choice
        options:
        - staging
        - production

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: knowledge-rag/llm-service

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: 设置Python环境
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: 安装依赖
      run: |
        curl -LsSf https://astral.sh/uv/install.sh | sh
        uv sync --prerelease=allow
    
    - name: 运行测试
      run: |
        pytest tests/ --cov=src/ --cov-report=xml
    
    - name: 代码质量检查
      run: |
        flake8 src/
        black --check src/
        mypy src/
  
  security-scan:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: 安全扫描
      uses: securecodewarrior/github-action-add-sarif@v1
      with:
        sarif-file: 'security-scan-results.sarif'
    
    - name: 依赖漏洞扫描
      run: |
        pip install safety
        safety check -r requirements.txt
  
  build-and-deploy:
    needs: [test, security-scan]
    runs-on: ubuntu-latest
    environment: ${{ github.event.inputs.environment || 'staging' }}
    
    steps:
    - uses: actions/checkout@v4
    
    - name: 设置kubectl
      uses: azure/setup-kubectl@v3
      with:
        version: 'v1.28.0'
    
    - name: 配置Kubernetes上下文
      run: |
        echo "${{ secrets.KUBECONFIG }}" | base64 -d > kubeconfig
        export KUBECONFIG=kubeconfig
        kubectl config use-context ${{ vars.K8S_CONTEXT }}
    
    - name: 构建并推送镜像
      run: |
        docker build -t $REGISTRY/$IMAGE_NAME:$GITHUB_SHA .
        echo ${{ secrets.GITHUB_TOKEN }} | docker login $REGISTRY -u ${{ github.actor }} --password-stdin
        docker push $REGISTRY/$IMAGE_NAME:$GITHUB_SHA
    
    - name: 更新Kubernetes配置
      run: |
        sed -i "s|image: .*|image: $REGISTRY/$IMAGE_NAME:$GITHUB_SHA|" k8s/llm-service-deployment.yaml
        kubectl apply -f k8s/ -n knowledge-rag-${{ vars.ENVIRONMENT }}
    
    - name: 等待部署完成
      run: |
        kubectl rollout status deployment/llm-service -n knowledge-rag-${{ vars.ENVIRONMENT }} --timeout=600s
    
    - name: 部署后测试
      run: |
        # 等待服务就绪
        kubectl wait --for=condition=ready pod -l app=llm-service -n knowledge-rag-${{ vars.ENVIRONMENT }} --timeout=300s
        
        # 健康检查
        SERVICE_URL=$(kubectl get svc llm-service -n knowledge-rag-${{ vars.ENVIRONMENT }} -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
        curl -f http://$SERVICE_URL/health || exit 1
        
        # 功能测试
        python tests/integration/test_deployment.py --service-url http://$SERVICE_URL
```

#### 8.7.2 蓝绿部署策略

```yaml
# k8s/blue-green-deployment.yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: llm-service-rollout
  namespace: knowledge-rag-prod
spec:
  replicas: 6
  strategy:
    blueGreen:
      activeService: llm-service-active
      previewService: llm-service-preview
      autoPromotionEnabled: false
      scaleDownDelaySeconds: 30
      prePromotionAnalysis:
        templates:
        - templateName: success-rate
        args:
        - name: service-name
          value: llm-service-preview
      postPromotionAnalysis:
        templates:
        - templateName: success-rate
        args:
        - name: service-name
          value: llm-service-active
  selector:
    matchLabels:
      app: llm-service
  template:
    metadata:
      labels:
        app: llm-service
    spec:
      containers:
      - name: llm-service
        image: ghcr.io/knowledge-rag/llm-service:latest
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
---
apiVersion: v1
kind: Service
metadata:
  name: llm-service-active
  namespace: knowledge-rag-prod
spec:
  ports:
  - port: 80
    targetPort: 8000
  selector:
    app: llm-service
---
apiVersion: v1
kind: Service
metadata:
  name: llm-service-preview
  namespace: knowledge-rag-prod
spec:
  ports:
  - port: 80
    targetPort: 8000
  selector:
    app: llm-service
```

### 8.8 运维和监控

#### 8.8.1 日志收集配置

```yaml
# k8s/logging.yaml
apiVersion: logging.coreos.com/v1
kind: ClusterLogForwarder
metadata:
  name: llm-service-logs
  namespace: openshift-logging
spec:
  outputs:
  - name: elasticsearch-llm
    type: elasticsearch
    url: https://elasticsearch.knowledge-rag.com:9200
    secret:
      name: elasticsearch-secret
  - name: s3-archive
    type: s3
    s3:
      bucket: knowledge-rag-logs
      region: us-west-2
    secret:
      name: s3-secret
  pipelines:
  - name: llm-service-pipeline
    inputRefs:
    - application
    filterRefs:
    - llm-service-filter
    outputRefs:
    - elasticsearch-llm
    - s3-archive
---
apiVersion: logging.coreos.com/v1
kind: ClusterLogFilter
metadata:
  name: llm-service-filter
spec:
  type: json
  json:
    javascript: |
      const log = record.log;
      if (log && log.kubernetes && log.kubernetes.labels && 
          log.kubernetes.labels.app === 'llm-service') {
        // 添加自定义字段
        log.service = 'llm-service';
        log.environment = log.kubernetes.namespace_name.split('-').pop();
        return log;
      }
      return null;
```

#### 8.8.2 监控和告警配置

```yaml
# k8s/monitoring.yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: llm-service-monitor
  namespace: knowledge-rag-prod
  labels:
    app: llm-service
spec:
  selector:
    matchLabels:
      app: llm-service
  endpoints:
  - port: metrics
    interval: 30s
    path: /metrics
---
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: llm-service-alerts
  namespace: knowledge-rag-prod
spec:
  groups:
  - name: llm-service.rules
    rules:
    - alert: LLMServiceHighLatency
      expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{job="llm-service"}[5m])) > 5
      for: 2m
      labels:
        severity: warning
        service: llm-service
      annotations:
        summary: "LLM服务延迟过高"
        description: "LLM服务95%分位延迟超过5秒，当前值: {{ $value }}秒"
    
    - alert: LLMServiceHighErrorRate
      expr: rate(http_requests_total{job="llm-service",status=~"5.."}[5m]) / rate(http_requests_total{job="llm-service"}[5m]) > 0.05
      for: 1m
      labels:
        severity: critical
        service: llm-service
      annotations:
        summary: "LLM服务错误率过高"
        description: "LLM服务错误率超过5%，当前值: {{ $value | humanizePercentage }}"
    
    - alert: LLMServicePodCrashLooping
      expr: rate(kube_pod_container_status_restarts_total{container="llm-service"}[15m]) > 0
      for: 5m
      labels:
        severity: critical
        service: llm-service
      annotations:
        summary: "LLM服务Pod频繁重启"
        description: "LLM服务Pod在过去15分钟内重启了 {{ $value }} 次"
    
    - alert: AzureOpenAIQuotaExceeded
      expr: azure_openai_quota_usage_ratio > 0.9
      for: 1m
      labels:
        severity: warning
        service: llm-service
      annotations:
        summary: "Azure OpenAI配额即将耗尽"
         description: "Azure OpenAI配额使用率超过90%，当前值: {{ $value | humanizePercentage }}"
 ```

### 8.9 灾难恢复和高可用性

#### 8.9.1 多区域部署架构

```yaml
# k8s/multi-region-deployment.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: region-config
  namespace: knowledge-rag-prod
data:
  regions.yaml: |
    primary_region: "us-west-2"
    secondary_regions:
      - "us-east-1"
      - "eu-west-1"
    
    failover_policy:
      automatic: true
      health_check_interval: 30
      failure_threshold: 3
      recovery_threshold: 2
    
    data_replication:
      postgres:
        mode: "streaming"
        lag_threshold: "10MB"
      redis:
        mode: "sentinel"
        quorum: 2
      weaviate:
        mode: "cluster"
        replication_factor: 3
      neo4j:
        mode: "causal_cluster"
        core_servers: 3
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: llm-service-dr
  namespace: knowledge-rag-prod
  labels:
    app: llm-service
    deployment-type: disaster-recovery
spec:
  replicas: 2  # 灾备环境保持最小副本数
  selector:
    matchLabels:
      app: llm-service
      deployment-type: disaster-recovery
  template:
    metadata:
      labels:
        app: llm-service
        deployment-type: disaster-recovery
    spec:
      containers:
      - name: llm-service
        image: ghcr.io/knowledge-rag/llm-service:latest
        env:
        - name: DEPLOYMENT_MODE
          value: "disaster-recovery"
        - name: PRIMARY_REGION_ENDPOINT
          value: "https://api-primary.knowledge-rag.com"
        resources:
          requests:
            memory: "256Mi"
            cpu: "125m"
          limits:
            memory: "1Gi"
            cpu: "500m"
```

#### 8.9.2 自动故障转移配置

```yaml
# k8s/failover-controller.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: failover-controller
  namespace: knowledge-rag-prod
spec:
  replicas: 1
  selector:
    matchLabels:
      app: failover-controller
  template:
    metadata:
      labels:
        app: failover-controller
    spec:
      containers:
      - name: controller
        image: failover-controller:latest
        env:
        - name: HEALTH_CHECK_ENDPOINTS
          value: |
            - https://api-primary.knowledge-rag.com/health
            - https://api-secondary.knowledge-rag.com/health
        - name: DNS_PROVIDER
          value: "route53"
        - name: NOTIFICATION_WEBHOOK
          valueFrom:
            secretKeyRef:
              name: notification-secret
              key: webhook-url
        command:
        - /bin/bash
        - -c
        - |
          #!/bin/bash
          # 故障转移控制脚本
          
          PRIMARY_ENDPOINT="https://api-primary.knowledge-rag.com/health"
          SECONDARY_ENDPOINT="https://api-secondary.knowledge-rag.com/health"
          DNS_RECORD="api.knowledge-rag.com"
          
          check_health() {
              local endpoint=$1
              local response=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 $endpoint)
              if [ "$response" = "200" ]; then
                  return 0
              else
                  return 1
              fi
          }
          
          update_dns() {
              local target=$1
              echo "更新DNS记录指向: $target"
              aws route53 change-resource-record-sets --hosted-zone-id Z123456789 --change-batch file://dns-change.json
          }
          
          send_notification() {
              local message=$1
              curl -X POST $NOTIFICATION_WEBHOOK -H "Content-Type: application/json" -d "{\"text\": \"$message\"}"
          }
          
          while true; do
              if check_health $PRIMARY_ENDPOINT; then
                  echo "主区域健康检查通过"
                  # 确保DNS指向主区域
                  current_target=$(dig +short $DNS_RECORD)
                  if [ "$current_target" != "primary-lb.knowledge-rag.com" ]; then
                      update_dns "primary-lb.knowledge-rag.com"
                      send_notification "故障恢复：DNS已切换回主区域"
                  fi
              else
                  echo "主区域健康检查失败，检查备用区域"
                  if check_health $SECONDARY_ENDPOINT; then
                      echo "备用区域健康，执行故障转移"
                      update_dns "secondary-lb.knowledge-rag.com"
                      send_notification "故障转移：DNS已切换到备用区域"
                  else
                      echo "所有区域都不可用！"
                      send_notification "严重告警：所有区域都不可用！"
                  fi
              fi
              sleep 30
          done
```

#### 8.9.3 数据备份和恢复策略

```yaml
# k8s/backup-strategy.yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: full-backup
  namespace: knowledge-rag-prod
spec:
  schedule: "0 1 * * 0"  # 每周日凌晨1点执行完整备份
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: backup-orchestrator:latest
            env:
            - name: BACKUP_TYPE
              value: "full"
            - name: S3_BUCKET
              value: "knowledge-rag-backups"
            - name: RETENTION_DAYS
              value: "90"
            command:
            - /bin/bash
            - -c
            - |
              #!/bin/bash
              # 全量备份脚本
              
              TIMESTAMP=$(date +%Y%m%d_%H%M%S)
              BACKUP_DIR="/tmp/backup_$TIMESTAMP"
              mkdir -p $BACKUP_DIR
              
              echo "开始全量备份: $TIMESTAMP"
              
              # 1. PostgreSQL备份
              echo "备份PostgreSQL数据库..."
              pg_dump $DATABASE_URL > $BACKUP_DIR/postgres_dump.sql
              
              # 2. Redis备份
              echo "备份Redis数据..."
              redis-cli --rdb $BACKUP_DIR/redis_dump.rdb
              
              # 3. Weaviate备份
              echo "备份Weaviate向量数据库..."
              curl -X POST "http://weaviate-service:8080/v1/backups" \
                -H "Content-Type: application/json" \
                -d '{"id": "backup_'$TIMESTAMP'"}'
              
              # 4. Neo4j备份
              echo "备份Neo4j图数据库..."
              neo4j-admin dump --database=neo4j --to=$BACKUP_DIR/neo4j_dump.dump
              
              # 5. 配置文件备份
              echo "备份Kubernetes配置..."
              kubectl get all -o yaml > $BACKUP_DIR/k8s_resources.yaml
              kubectl get secrets -o yaml > $BACKUP_DIR/k8s_secrets.yaml
              kubectl get configmaps -o yaml > $BACKUP_DIR/k8s_configmaps.yaml
              
              # 6. 压缩并上传到S3
              echo "压缩备份文件..."
              tar -czf backup_$TIMESTAMP.tar.gz -C /tmp backup_$TIMESTAMP
              
              echo "上传到S3..."
              aws s3 cp backup_$TIMESTAMP.tar.gz s3://$S3_BUCKET/full-backups/
              
              # 7. 清理本地文件
              rm -rf $BACKUP_DIR backup_$TIMESTAMP.tar.gz
              
              # 8. 清理过期备份
              echo "清理过期备份..."
              aws s3 ls s3://$S3_BUCKET/full-backups/ | while read -r line; do
                  createDate=$(echo $line | awk '{print $1" "$2}')
                  createDate=$(date -d "$createDate" +%s)
                  olderThan=$(date -d "$RETENTION_DAYS days ago" +%s)
                  if [[ $createDate -lt $olderThan ]]; then
                      fileName=$(echo $line | awk '{print $4}')
                      if [[ $fileName != "" ]]; then
                          aws s3 rm s3://$S3_BUCKET/full-backups/$fileName
                      fi
                  fi
              done
              
              echo "全量备份完成: $TIMESTAMP"
          restartPolicy: OnFailure
---
apiVersion: batch/v1
kind: CronJob
metadata:
  name: incremental-backup
  namespace: knowledge-rag-prod
spec:
  schedule: "0 */6 * * *"  # 每6小时执行增量备份
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: backup-orchestrator:latest
            env:
            - name: BACKUP_TYPE
              value: "incremental"
            command:
            - /bin/bash
            - -c
            - |
              #!/bin/bash
              # 增量备份脚本
              
              TIMESTAMP=$(date +%Y%m%d_%H%M%S)
              echo "开始增量备份: $TIMESTAMP"
              
              # PostgreSQL WAL备份
              pg_receivewal -D /tmp/wal_backup -h postgres-service -U postgres
              tar -czf wal_backup_$TIMESTAMP.tar.gz -C /tmp wal_backup
              aws s3 cp wal_backup_$TIMESTAMP.tar.gz s3://$S3_BUCKET/incremental-backups/
              
              # Redis AOF备份
              redis-cli BGREWRITEAOF
              sleep 10
              cp /data/appendonly.aof /tmp/redis_aof_$TIMESTAMP.aof
              aws s3 cp /tmp/redis_aof_$TIMESTAMP.aof s3://$S3_BUCKET/incremental-backups/
              
              echo "增量备份完成: $TIMESTAMP"
          restartPolicy: OnFailure
```

### 8.10 性能优化和调优

#### 8.10.1 资源调优配置

```yaml
# k8s/performance-tuning.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: performance-config
  namespace: knowledge-rag-prod
data:
  jvm-opts: |
    -Xms2g
    -Xmx4g
    -XX:+UseG1GC
    -XX:MaxGCPauseMillis=200
    -XX:+UseStringDeduplication
    -XX:+OptimizeStringConcat
  
  python-opts: |
    PYTHONOPTIMIZE=2
    PYTHONUNBUFFERED=1
    PYTHONDONTWRITEBYTECODE=1
    PYTHONASYNCIODEBUG=0
  
  nginx-config: |
    worker_processes auto;
    worker_connections 4096;
    
    http {
        sendfile on;
        tcp_nopush on;
        tcp_nodelay on;
        keepalive_timeout 65;
        keepalive_requests 1000;
        
        gzip on;
        gzip_vary on;
        gzip_min_length 1024;
        gzip_types text/plain text/css application/json application/javascript;
        
        # 连接池配置
        upstream llm_backend {
            least_conn;
            server llm-service-1:8000 max_fails=3 fail_timeout=30s;
            server llm-service-2:8000 max_fails=3 fail_timeout=30s;
            server llm-service-3:8000 max_fails=3 fail_timeout=30s;
            keepalive 32;
        }
        
        # 缓存配置
        proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:10m max_size=1g inactive=60m;
        
        server {
            listen 80;
            
            location /api/v1/embeddings {
                proxy_pass http://llm_backend;
                proxy_cache api_cache;
                proxy_cache_valid 200 5m;
                proxy_cache_key "$request_uri$request_body";
            }
            
            location /api/v1/chat {
                proxy_pass http://llm_backend;
                proxy_buffering off;
                proxy_read_timeout 300s;
            }
        }
    }
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-proxy
  namespace: knowledge-rag-prod
spec:
  replicas: 2
  selector:
    matchLabels:
      app: nginx-proxy
  template:
    metadata:
      labels:
        app: nginx-proxy
    spec:
      containers:
      - name: nginx
        image: nginx:1.25-alpine
        ports:
        - containerPort: 80
        volumeMounts:
        - name: nginx-config
          mountPath: /etc/nginx/nginx.conf
          subPath: nginx-config
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
      volumes:
      - name: nginx-config
        configMap:
          name: performance-config
```

#### 8.10.2 缓存优化策略

```python
# src/services/cache_optimizer.py
"""
LLM服务缓存优化模块
实现多级缓存策略，提升响应性能
"""

import asyncio
import hashlib
import json
from typing import Any, Dict, Optional, Tuple
from datetime import datetime, timedelta

import redis.asyncio as redis
from fastapi import BackgroundTasks

class CacheOptimizer:
    """
    缓存优化器
    实现L1(内存) + L2(Redis) + L3(预计算)三级缓存架构
    """
    
    def __init__(self, redis_client: redis.Redis):
        self.redis_client = redis_client
        self.l1_cache = {}  # 内存缓存
        self.l1_max_size = 1000
        self.l1_ttl = 300  # 5分钟
        
        # 缓存统计
        self.stats = {
            'l1_hits': 0,
            'l2_hits': 0,
            'l3_hits': 0,
            'misses': 0,
            'total_requests': 0
        }
    
    def _generate_cache_key(self, prefix: str, data: Dict[str, Any]) -> str:
        """
        生成缓存键
        
        Args:
            prefix: 缓存键前缀
            data: 用于生成键的数据
            
        Returns:
            str: 缓存键
        """
        # 对数据进行排序和序列化，确保一致性
        sorted_data = json.dumps(data, sort_keys=True, ensure_ascii=False)
        hash_value = hashlib.md5(sorted_data.encode()).hexdigest()
        return f"{prefix}:{hash_value}"
    
    async def get_cached_embedding(self, text: str, model: str) -> Optional[Tuple[list, Dict]]:
        """
        获取缓存的向量嵌入
        
        Args:
            text: 输入文本
            model: 模型名称
            
        Returns:
            Optional[Tuple[list, Dict]]: (向量, 元数据) 或 None
        """
        self.stats['total_requests'] += 1
        
        cache_key = self._generate_cache_key('embedding', {
            'text': text,
            'model': model
        })
        
        # L1缓存检查
        if cache_key in self.l1_cache:
            cache_data = self.l1_cache[cache_key]
            if datetime.now() < cache_data['expires_at']:
                self.stats['l1_hits'] += 1
                return cache_data['embedding'], cache_data['metadata']
            else:
                # 过期删除
                del self.l1_cache[cache_key]
        
        # L2缓存检查
        try:
            cached_data = await self.redis_client.get(cache_key)
            if cached_data:
                data = json.loads(cached_data)
                self.stats['l2_hits'] += 1
                
                # 回填L1缓存
                await self._set_l1_cache(cache_key, data['embedding'], data['metadata'])
                
                return data['embedding'], data['metadata']
        except Exception as e:
            print(f"Redis缓存读取失败: {e}")
        
        self.stats['misses'] += 1
        return None
    
    async def set_cached_embedding(self, text: str, model: str, embedding: list, metadata: Dict):
        """
        设置向量嵌入缓存
        
        Args:
            text: 输入文本
            model: 模型名称
            embedding: 向量嵌入
            metadata: 元数据
        """
        cache_key = self._generate_cache_key('embedding', {
            'text': text,
            'model': model
        })
        
        cache_data = {
            'embedding': embedding,
            'metadata': metadata,
            'created_at': datetime.now().isoformat()
        }
        
        # 设置L1缓存
        await self._set_l1_cache(cache_key, embedding, metadata)
        
        # 设置L2缓存
        try:
            await self.redis_client.setex(
                cache_key,
                3600,  # 1小时TTL
                json.dumps(cache_data, ensure_ascii=False)
            )
        except Exception as e:
            print(f"Redis缓存写入失败: {e}")
    
    async def _set_l1_cache(self, cache_key: str, embedding: list, metadata: Dict):
        """
        设置L1内存缓存
        
        Args:
            cache_key: 缓存键
            embedding: 向量嵌入
            metadata: 元数据
        """
        # LRU淘汰策略
        if len(self.l1_cache) >= self.l1_max_size:
            # 删除最旧的条目
            oldest_key = min(self.l1_cache.keys(), 
                           key=lambda k: self.l1_cache[k]['created_at'])
            del self.l1_cache[oldest_key]
        
        self.l1_cache[cache_key] = {
            'embedding': embedding,
            'metadata': metadata,
            'created_at': datetime.now(),
            'expires_at': datetime.now() + timedelta(seconds=self.l1_ttl)
        }
    
    async def precompute_popular_embeddings(self, background_tasks: BackgroundTasks):
        """
        预计算热门查询的向量嵌入
        
        Args:
            background_tasks: FastAPI后台任务
        """
        # 获取热门查询
        popular_queries = await self._get_popular_queries()
        
        for query_data in popular_queries:
            background_tasks.add_task(
                self._precompute_embedding,
                query_data['text'],
                query_data['model']
            )
    
    async def _get_popular_queries(self) -> list:
        """
        获取热门查询列表
        
        Returns:
            list: 热门查询数据
        """
        try:
            # 从Redis获取查询统计
            query_stats = await self.redis_client.zrevrange(
                'query_stats', 0, 99, withscores=True
            )
            
            popular_queries = []
            for query_key, score in query_stats:
                if score > 10:  # 查询次数超过10次
                    query_data = json.loads(query_key)
                    popular_queries.append(query_data)
            
            return popular_queries
        except Exception as e:
            print(f"获取热门查询失败: {e}")
            return []
    
    async def _precompute_embedding(self, text: str, model: str):
        """
        预计算向量嵌入
        
        Args:
            text: 输入文本
            model: 模型名称
        """
        # 检查是否已缓存
        cached = await self.get_cached_embedding(text, model)
        if cached:
            return
        
        try:
            # 调用实际的嵌入服务
            from .azure_client import AzureOpenAIClient
            client = AzureOpenAIClient()
            
            embedding = await client.get_embedding(text, model)
            metadata = {
                'model': model,
                'text_length': len(text),
                'precomputed': True,
                'computed_at': datetime.now().isoformat()
            }
            
            await self.set_cached_embedding(text, model, embedding, metadata)
            
        except Exception as e:
            print(f"预计算嵌入失败: {e}")
    
    async def update_query_stats(self, text: str, model: str):
        """
        更新查询统计
        
        Args:
            text: 查询文本
            model: 模型名称
        """
        try:
            query_key = json.dumps({
                'text': text,
                'model': model
            }, ensure_ascii=False)
            
            await self.redis_client.zincrby('query_stats', 1, query_key)
            
        except Exception as e:
            print(f"更新查询统计失败: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Returns:
            Dict[str, Any]: 缓存统计数据
        """
        total_requests = self.stats['total_requests']
        if total_requests == 0:
            return self.stats
        
        hit_rate = (
            self.stats['l1_hits'] + 
            self.stats['l2_hits'] + 
            self.stats['l3_hits']
        ) / total_requests
        
        return {
            **self.stats,
            'hit_rate': hit_rate,
            'l1_size': len(self.l1_cache)
        }
    
    async def clear_cache(self, pattern: Optional[str] = None):
        """
        清理缓存
        
        Args:
            pattern: 可选的键模式，如果不提供则清理所有缓存
        """
        # 清理L1缓存
        if pattern:
            keys_to_delete = [k for k in self.l1_cache.keys() if pattern in k]
            for key in keys_to_delete:
                del self.l1_cache[key]
        else:
            self.l1_cache.clear()
        
        # 清理L2缓存
        try:
            if pattern:
                keys = await self.redis_client.keys(f"*{pattern}*")
                if keys:
                    await self.redis_client.delete(*keys)
            else:
                await self.redis_client.flushdb()
        except Exception as e:
            print(f"清理Redis缓存失败: {e}")
```

### 8.11 成本管理和优化

#### 8.11.1 成本监控配置

```yaml
# k8s/cost-monitoring.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cost-monitor
  namespace: knowledge-rag-prod
spec:
  replicas: 1
  selector:
    matchLabels:
      app: cost-monitor
  template:
    metadata:
      labels:
        app: cost-monitor
    spec:
      containers:
      - name: cost-monitor
        image: cost-monitor:latest
        env:
        - name: AZURE_SUBSCRIPTION_ID
          valueFrom:
            secretKeyRef:
              name: azure-secret
              key: subscription-id
        - name: COST_ALERT_THRESHOLD
          value: "2500"  # 月度成本告警阈值
        - name: DAILY_BUDGET
          value: "100"   # 日预算
        command:
        - /bin/bash
        - -c
        - |
          #!/bin/bash
          # 成本监控脚本
          
          while true; do
              echo "开始成本监控检查..."
              
              # 获取当前月度成本
              CURRENT_COST=$(az consumption usage list --start-date $(date -d "$(date +%Y-%m-01)" +%Y-%m-%d) --end-date $(date +%Y-%m-%d) --query "[].{Cost:pretaxCost}" --output tsv | awk '{sum += $1} END {print sum}')
              
              # 获取今日成本
              TODAY_COST=$(az consumption usage list --start-date $(date +%Y-%m-%d) --end-date $(date +%Y-%m-%d) --query "[].{Cost:pretaxCost}" --output tsv | awk '{sum += $1} END {print sum}')
              
              echo "当前月度成本: $CURRENT_COST USD"
              echo "今日成本: $TODAY_COST USD"
              
              # 成本告警检查
              if (( $(echo "$CURRENT_COST > $COST_ALERT_THRESHOLD" | bc -l) )); then
                  curl -X POST $WEBHOOK_URL -H "Content-Type: application/json" -d "{
                      \"text\": \"🚨 成本告警：月度成本已超过阈值！\\n当前成本: $CURRENT_COST USD\\n阈值: $COST_ALERT_THRESHOLD USD\"
                  }"
              fi
              
              if (( $(echo "$TODAY_COST > $DAILY_BUDGET" | bc -l) )); then
                  curl -X POST $WEBHOOK_URL -H "Content-Type: application/json" -d "{
                      \"text\": \"⚠️ 日预算告警：今日成本已超过预算！\\n今日成本: $TODAY_COST USD\\n日预算: $DAILY_BUDGET USD\"
                  }"
              fi
              
              # 更新成本指标
              echo "# HELP azure_cost_current_month Current month cost in USD" > /tmp/metrics.prom
              echo "# TYPE azure_cost_current_month gauge" >> /tmp/metrics.prom
              echo "azure_cost_current_month $CURRENT_COST" >> /tmp/metrics.prom
              
              echo "# HELP azure_cost_today Today cost in USD" >> /tmp/metrics.prom
              echo "# TYPE azure_cost_today gauge" >> /tmp/metrics.prom
              echo "azure_cost_today $TODAY_COST" >> /tmp/metrics.prom
              
              # 等待1小时后再次检查
              sleep 3600
          done
        volumeMounts:
        - name: metrics
          mountPath: /tmp
      volumes:
      - name: metrics
        emptyDir: {}
```

#### 8.11.2 资源优化策略

```python
# src/services/resource_optimizer.py
"""
资源优化服务
根据使用模式动态调整资源配置
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import kubernetes
from kubernetes import client, config

class ResourceOptimizer:
    """
    资源优化器
    实现基于使用模式的动态资源调整
    """
    
    def __init__(self):
        # 加载Kubernetes配置
        try:
            config.load_incluster_config()
        except:
            config.load_kube_config()
        
        self.apps_v1 = client.AppsV1Api()
        self.core_v1 = client.CoreV1Api()
        self.autoscaling_v2 = client.AutoscalingV2Api()
        
        # 优化策略配置
        self.optimization_rules = {
            'low_traffic_hours': {
                'start': 22,  # 晚上10点
                'end': 6,     # 早上6点
                'cpu_scale': 0.5,
                'memory_scale': 0.7,
                'replica_scale': 0.5
            },
            'high_traffic_hours': {
                'start': 9,   # 早上9点
                'end': 18,    # 晚上6点
                'cpu_scale': 1.2,
                'memory_scale': 1.1,
                'replica_scale': 1.5
            },
            'weekend_scale': {
                'cpu_scale': 0.6,
                'memory_scale': 0.8,
                'replica_scale': 0.7
            }
        }
    
    async def optimize_resources(self, namespace: str = "knowledge-rag-prod"):
        """
        执行资源优化
        
        Args:
            namespace: Kubernetes命名空间
        """
        current_time = datetime.now()
        current_hour = current_time.hour
        is_weekend = current_time.weekday() >= 5
        
        # 确定当前时段的优化策略
        if is_weekend:
            strategy = self.optimization_rules['weekend_scale']
        elif self._is_low_traffic_hour(current_hour):
            strategy = self.optimization_rules['low_traffic_hours']
        elif self._is_high_traffic_hour(current_hour):
            strategy = self.optimization_rules['high_traffic_hours']
        else:
            # 正常时段，不进行调整
            return
        
        print(f"应用优化策略: {strategy}")
        
        # 获取所有部署
        deployments = self.apps_v1.list_namespaced_deployment(namespace)
        
        for deployment in deployments.items:
            if deployment.metadata.labels.get('optimize') == 'true':
                await self._optimize_deployment(deployment, strategy, namespace)
    
    def _is_low_traffic_hour(self, hour: int) -> bool:
        """
        判断是否为低流量时段
        
        Args:
            hour: 当前小时
            
        Returns:
            bool: 是否为低流量时段
        """
        low_start = self.optimization_rules['low_traffic_hours']['start']
        low_end = self.optimization_rules['low_traffic_hours']['end']
        
        if low_start > low_end:  # 跨天情况
            return hour >= low_start or hour < low_end
        else:
            return low_start <= hour < low_end
    
    def _is_high_traffic_hour(self, hour: int) -> bool:
        """
        判断是否为高流量时段
        
        Args:
            hour: 当前小时
            
        Returns:
            bool: 是否为高流量时段
        """
        high_start = self.optimization_rules['high_traffic_hours']['start']
        high_end = self.optimization_rules['high_traffic_hours']['end']
        
        return high_start <= hour < high_end
    
    async def _optimize_deployment(self, deployment, strategy: Dict, namespace: str):
        """
        优化单个部署的资源配置
        
        Args:
            deployment: Kubernetes部署对象
            strategy: 优化策略
            namespace: 命名空间
        """
        deployment_name = deployment.metadata.name
        print(f"优化部署: {deployment_name}")
        
        # 获取当前资源配置
        current_resources = deployment.spec.template.spec.containers[0].resources
        current_replicas = deployment.spec.replicas
        
        # 计算新的资源配置
        new_resources = self._calculate_new_resources(current_resources, strategy)
        new_replicas = max(1, int(current_replicas * strategy.get('replica_scale', 1)))
        
        # 更新部署配置
        try:
            # 更新副本数
            deployment.spec.replicas = new_replicas
            
            # 更新资源限制
            deployment.spec.template.spec.containers[0].resources = new_resources
            
            # 应用更新
            self.apps_v1.patch_namespaced_deployment(
                name=deployment_name,
                namespace=namespace,
                body=deployment
            )
            
            print(f"部署 {deployment_name} 优化完成:")
            print(f"  副本数: {current_replicas} -> {new_replicas}")
            print(f"  资源配置已更新")
            
        except Exception as e:
            print(f"优化部署 {deployment_name} 失败: {e}")
    
    def _calculate_new_resources(self, current_resources, strategy: Dict):
        """
        计算新的资源配置
        
        Args:
            current_resources: 当前资源配置
            strategy: 优化策略
            
        Returns:
            新的资源配置
        """
        cpu_scale = strategy.get('cpu_scale', 1)
        memory_scale = strategy.get('memory_scale', 1)
        
        new_resources = client.V1ResourceRequirements()
        
        if current_resources.requests:
            new_resources.requests = {}
            if 'cpu' in current_resources.requests:
                current_cpu = self._parse_cpu(current_resources.requests['cpu'])
                new_cpu = int(current_cpu * cpu_scale)
                new_resources.requests['cpu'] = f"{new_cpu}m"
            
            if 'memory' in current_resources.requests:
                current_memory = self._parse_memory(current_resources.requests['memory'])
                new_memory = int(current_memory * memory_scale)
                new_resources.requests['memory'] = f"{new_memory}Mi"
        
        if current_resources.limits:
            new_resources.limits = {}
            if 'cpu' in current_resources.limits:
                current_cpu = self._parse_cpu(current_resources.limits['cpu'])
                new_cpu = int(current_cpu * cpu_scale)
                new_resources.limits['cpu'] = f"{new_cpu}m"
            
            if 'memory' in current_resources.limits:
                current_memory = self._parse_memory(current_resources.limits['memory'])
                new_memory = int(current_memory * memory_scale)
                new_resources.limits['memory'] = f"{new_memory}Mi"
        
        return new_resources
    
    def _parse_cpu(self, cpu_str: str) -> int:
        """
        解析CPU字符串为毫核数
        
        Args:
            cpu_str: CPU字符串（如 "500m" 或 "1"）
            
        Returns:
            int: 毫核数
        """
        if cpu_str.endswith('m'):
            return int(cpu_str[:-1])
        else:
            return int(float(cpu_str) * 1000)
    
    def _parse_memory(self, memory_str: str) -> int:
        """
        解析内存字符串为MB数
        
        Args:
            memory_str: 内存字符串（如 "512Mi" 或 "1Gi"）
            
        Returns:
            int: MB数
        """
        if memory_str.endswith('Mi'):
            return int(memory_str[:-2])
        elif memory_str.endswith('Gi'):
            return int(memory_str[:-2]) * 1024
        elif memory_str.endswith('Ki'):
            return int(memory_str[:-2]) // 1024
        else:
            return int(memory_str) // (1024 * 1024)
    
    async def get_optimization_recommendations(self, namespace: str = "knowledge-rag-prod") -> List[Dict]:
        """
        获取资源优化建议
        
        Args:
            namespace: Kubernetes命名空间
            
        Returns:
            List[Dict]: 优化建议列表
        """
        recommendations = []
        
        # 获取Pod指标
        pods = self.core_v1.list_namespaced_pod(namespace)
        
        for pod in pods.items:
            if pod.status.phase == 'Running':
                recommendation = await self._analyze_pod_usage(pod)
                if recommendation:
                    recommendations.append(recommendation)
        
        return recommendations
    
    async def _analyze_pod_usage(self, pod) -> Optional[Dict]:
        """
        分析Pod使用情况并生成建议
        
        Args:
            pod: Pod对象
            
        Returns:
            Optional[Dict]: 优化建议
        """
        pod_name = pod.metadata.name
        
        try:
            # 这里应该集成Prometheus指标获取实际使用情况
            # 简化示例，实际应该查询Prometheus
            
            recommendation = {
                'pod_name': pod_name,
                'current_resources': {},
                'recommended_resources': {},
                'potential_savings': 0,
                'confidence': 0.8
            }
            
            # 获取当前资源配置
            if pod.spec.containers:
                container = pod.spec.containers[0]
                if container.resources:
                    if container.resources.requests:
                        recommendation['current_resources']['requests'] = dict(container.resources.requests)
                    if container.resources.limits:
                        recommendation['current_resources']['limits'] = dict(container.resources.limits)
            
            # 基于历史使用情况生成建议（这里是示例逻辑）
            # 实际应该基于Prometheus指标数据
            
            return recommendation
            
        except Exception as e:
            print(f"分析Pod {pod_name} 使用情况失败: {e}")
            return None

# 定时任务配置
async def run_resource_optimizer():
    """
    运行资源优化器的定时任务
    """
    optimizer = ResourceOptimizer()
    
    while True:
        try:
            await optimizer.optimize_resources()
            # 每小时执行一次
            await asyncio.sleep(3600)
        except Exception as e:
            print(f"资源优化执行失败: {e}")
            await asyncio.sleep(300)  # 出错后5分钟重试
```

### 8.12 部署实施计划

#### 8.12.1 分阶段部署时间表

| 阶段 | 时间周期 | 主要任务 | 交付物 | 负责团队 |
|------|----------|----------|--------|----------|
| **阶段1：基础设施准备** | 第1-2周 | • 云资源申请和配置<br>• Kubernetes集群搭建<br>• 网络和安全配置<br>• 监控系统部署 | • AKS集群<br>• 网络策略<br>• 监控仪表板<br>• 安全基线 | DevOps团队 |
| **阶段2：核心服务部署** | 第3-4周 | • 数据库集群部署<br>• Redis缓存集群<br>• LLM服务部署<br>• API网关配置 | • 数据库集群<br>• 缓存服务<br>• LLM API服务<br>• 负载均衡器 | 后端团队 |
| **阶段3：集成测试** | 第5周 | • 端到端测试<br>• 性能测试<br>• 安全测试<br>• 灾难恢复测试 | • 测试报告<br>• 性能基准<br>• 安全评估<br>• DR演练报告 | QA团队 |
| **阶段4：生产发布** | 第6周 | • 蓝绿部署<br>• 流量切换<br>• 监控验证<br>• 文档交付 | • 生产环境<br>• 运维手册<br>• 监控告警<br>• 用户文档 | 全团队 |

#### 8.12.2 部署检查清单

```yaml
# deployment-checklist.yaml
deployment_checklist:
  pre_deployment:
    infrastructure:
      - name: "Kubernetes集群就绪"
        status: "pending"
        owner: "DevOps"
        deadline: "2024-02-15"
      - name: "网络策略配置"
        status: "pending"
        owner: "DevOps"
        deadline: "2024-02-16"
      - name: "存储类配置"
        status: "pending"
        owner: "DevOps"
        deadline: "2024-02-17"
    
    security:
      - name: "密钥管理配置"
        status: "pending"
        owner: "Security"
        deadline: "2024-02-18"
      - name: "RBAC策略配置"
        status: "pending"
        owner: "Security"
        deadline: "2024-02-19"
      - name: "Pod安全策略"
        status: "pending"
        owner: "Security"
        deadline: "2024-02-20"
    
    monitoring:
      - name: "Prometheus部署"
        status: "pending"
        owner: "DevOps"
        deadline: "2024-02-21"
      - name: "Grafana仪表板"
        status: "pending"
        owner: "DevOps"
        deadline: "2024-02-22"
      - name: "告警规则配置"
        status: "pending"
        owner: "DevOps"
        deadline: "2024-02-23"
  
  deployment:
    database:
      - name: "PostgreSQL集群部署"
        status: "pending"
        owner: "Backend"
        deadline: "2024-02-24"
      - name: "Redis集群部署"
        status: "pending"
        owner: "Backend"
        deadline: "2024-02-25"
      - name: "Weaviate部署"
        status: "pending"
        owner: "Backend"
        deadline: "2024-02-26"
      - name: "Neo4j集群部署"
        status: "pending"
        owner: "Backend"
        deadline: "2024-02-27"
    
    services:
      - name: "LLM服务部署"
        status: "pending"
        owner: "Backend"
        deadline: "2024-02-28"
      - name: "API网关配置"
        status: "pending"
        owner: "Backend"
        deadline: "2024-03-01"
      - name: "负载均衡器配置"
        status: "pending"
        owner: "DevOps"
        deadline: "2024-03-02"
  
  post_deployment:
    testing:
      - name: "健康检查验证"
        status: "pending"
        owner: "QA"
        deadline: "2024-03-03"
      - name: "API功能测试"
        status: "pending"
        owner: "QA"
        deadline: "2024-03-04"
      - name: "性能基准测试"
        status: "pending"
        owner: "QA"
        deadline: "2024-03-05"
      - name: "安全扫描"
        status: "pending"
        owner: "Security"
        deadline: "2024-03-06"
    
    documentation:
      - name: "部署文档更新"
        status: "pending"
        owner: "DevOps"
        deadline: "2024-03-07"
      - name: "运维手册编写"
        status: "pending"
        owner: "DevOps"
        deadline: "2024-03-08"
      - name: "故障排除指南"
        status: "pending"
        owner: "DevOps"
        deadline: "2024-03-09"
    
    handover:
      - name: "运维团队培训"
        status: "pending"
        owner: "DevOps"
        deadline: "2024-03-10"
      - name: "监控告警测试"
        status: "pending"
        owner: "DevOps"
        deadline: "2024-03-11"
      - name: "生产环境交接"
        status: "pending"
        owner: "All"
        deadline: "2024-03-12"
```

## 9. 总结

本基础设施部署规划文档详细描述了Knowledge_RAG项目LLM集成服务的完整部署架构和实施方案。主要特点包括：

### 9.1 架构优势

1. **高可用性**：多区域部署、自动故障转移、数据备份策略
2. **可扩展性**：水平自动扩缩容、负载均衡、微服务架构
3. **安全性**：网络策略、Pod安全策略、密钥管理、RBAC
4. **可观测性**：全面监控、日志收集、性能指标、告警机制
5. **成本优化**：资源动态调整、成本监控、预算控制

### 9.2 技术栈

- **容器编排**：Kubernetes (AKS)
- **服务网格**：Istio (可选)
- **监控**：Prometheus + Grafana
- **日志**：ELK Stack
- **CI/CD**：GitHub Actions + ArgoCD
- **存储**：Azure Disk (SSD)
- **网络**：Azure CNI
- **安全**：Azure Key Vault + Pod Security Standards

### 9.3 运维保障

- **自动化部署**：GitOps流程、蓝绿部署
- **监控告警**：多维度指标、智能告警
- **灾难恢复**：自动备份、快速恢复
- **性能优化**：缓存策略、资源调优
- **成本控制**：预算监控、资源优化

该部署方案确保了Knowledge_RAG项目能够在生产环境中稳定、高效、安全地运行，同时具备良好的可维护性和扩展性。

## 9. 测试策略

### 9.1 单元测试

```python
# tests/test_llm_service.py

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from services.llm_service import LLMService

class TestLLMService:
    """
    LLM服务单元测试
    """
    
    @pytest.fixture
    def mock_azure_client(self):
        """
        模拟Azure OpenAI客户端
        """
        client = Mock()
        client.get_embedding = AsyncMock(return_value=[0.1] * 1536)
        client.chat_completion = AsyncMock(return_value="测试回答")
        return client
    
    @pytest.fixture
    def llm_service(self, mock_azure_client):
        """
        创建LLM服务实例
        """
        return LLMService(
            azure_client=mock_azure_client,
            cache_manager=Mock(),
            cost_monitor=Mock()
        )
    
    @pytest.mark.asyncio
    async def test_get_embedding(self, llm_service, mock_azure_client):
        """
        测试文本嵌入功能
        """
        # 准备测试数据
        text = "这是一个测试文本"
        
        # 执行测试
        embedding = await llm_service.get_embedding(text)
        
        # 验证结果
        assert len(embedding) == 1536
        assert all(isinstance(x, float) for x in embedding)
        mock_azure_client.get_embedding.assert_called_once_with(
            text=text, model="text-embedding-ada-002"
        )
    
    @pytest.mark.asyncio
    async def test_chat_completion(self, llm_service, mock_azure_client):
        """
        测试对话完成功能
        """
        # 准备测试数据
        messages = [
            {"role": "user", "content": "你好"}
        ]
        
        # 执行测试
        response = await llm_service.chat_completion(messages)
        
        # 验证结果
        assert response == "测试回答"
        mock_azure_client.chat_completion.assert_called_once()
```

### 9.2 集成测试

```python
# tests/test_integration.py

import pytest
import asyncio
from httpx import AsyncClient
from main import app

class TestLLMIntegration:
    """
    LLM服务集成测试
    """
    
    @pytest.mark.asyncio
    async def test_embedding_endpoint(self):
        """
        测试嵌入向量API端点
        """
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/embeddings",
                json={
                    "text": "测试文本",
                    "model": "text-embedding-ada-002"
                },
                headers={"Authorization": "Bearer test-token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "embedding" in data
            assert len(data["embedding"]) == 1536
    
    @pytest.mark.asyncio
    async def test_chat_endpoint(self):
        """
        测试聊天API端点
        """
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/chat/completions",
                json={
                    "messages": [
                        {"role": "user", "content": "你好"}
                    ],
                    "model": "gpt-35-turbo-16k"
                },
                headers={"Authorization": "Bearer test-token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "choices" in data
            assert len(data["choices"]) > 0
```

## 10. 监控和告警

### 10.1 监控指标

```yaml
# monitoring/prometheus-config.yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'llm-service'
    static_configs:
      - targets: ['llm-service:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s

rule_files:
  - "alert_rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

### 10.2 告警规则

```yaml
# monitoring/alert_rules.yml
groups:
- name: llm_service_alerts
  rules:
  - alert: HighResponseTime
    expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 5
    for: 2m
    labels:
      severity: warning
    annotations:
      summary: "LLM服务响应时间过高"
      description: "95%的请求响应时间超过5秒"
  
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.05
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "LLM服务错误率过高"
      description: "错误率超过5%"
  
  - alert: BudgetExceeded
    expr: daily_cost_usd > 100
    for: 0m
    labels:
      severity: warning
    annotations:
      summary: "日预算超限"
      description: "当日API调用成本超过100美元"
```

## 11. 实施时间线

### 第一阶段：基础设施搭建（1-2周）
- [ ] Azure OpenAI服务申请和配置
- [ ] 开发环境搭建和依赖安装
- [ ] 基础API框架和认证系统
- [ ] Docker容器化和CI/CD流水线

### 第二阶段：核心功能开发（2-3周）
- [ ] Azure OpenAI客户端封装
- [ ] 文档嵌入服务实现
- [ ] 缓存和限流机制
- [ ] 成本监控和预算控制

### 第三阶段：GraphRAG集成（2-3周）
- [ ] 混合检索算法实现
- [ ] 上下文构建和答案生成
- [ ] 对话管理和历史记录
- [ ] 性能优化和调试

### 第四阶段：测试和部署（1-2周）
- [ ] 单元测试和集成测试
- [ ] 性能测试和负载测试
- [ ] 生产环境部署
- [ ] 监控和告警配置

## 12. 风险评估和缓解

### 12.1 技术风险

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| Azure OpenAI服务不可用 | 高 | 低 | 实现多模型备份，本地模型降级 |
| API配额限制 | 中 | 中 | 实现智能限流，用户分级管理 |
| 响应延迟过高 | 中 | 中 | 缓存优化，异步处理 |
| 成本超预算 | 高 | 中 | 严格预算控制，实时监控 |

### 12.2 业务风险

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| 用户体验不佳 | 高 | 中 | 充分测试，用户反馈收集 |
| 数据安全问题 | 高 | 低 | 严格安全措施，合规审计 |
| 竞争对手优势 | 中 | 中 | 持续技术创新，差异化功能 |

## 13. 总结

本技术方案详细规划了Knowledge_RAG项目中Azure OpenAI的集成实施，涵盖了从技术选型到部署运维的完整流程。通过采用Azure OpenAI服务，项目将获得：

1. **企业级安全保障**：符合SOC2、ISO27001等合规要求
2. **稳定的服务质量**：99.9% SLA保证和专业技术支持
3. **灵活的成本控制**：基于使用量的定价和预算管理
4. **强大的技术能力**：GPT-4级别的理解和生成能力

**下一步行动**：
1. 申请Azure OpenAI服务访问权限
2. 搭建开发环境和基础框架
3. 实现核心API封装和缓存机制
4. 开发GraphRAG集成功能
5. 进行全面测试和性能优化

通过严格按照本方案执行，预计在6-8周内完成Azure OpenAI的完整集成，为Knowledge_RAG系统提供强大的AI能力支撑。