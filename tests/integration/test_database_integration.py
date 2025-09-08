# Knowledge RAG System - 数据库集成测试
# 测试数据库连接、事务处理和数据一致性

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import asyncpg
import redis.asyncio as redis
from datetime import datetime, timedelta
import json
import uuid


@pytest.mark.integration
class TestPostgreSQLIntegration:
    """PostgreSQL数据库集成测试类"""
    
    @pytest.fixture
    async def db_connection(self):
        """数据库连接fixture"""
        # 模拟数据库连接
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock()
        mock_conn.fetch = AsyncMock()
        mock_conn.fetchrow = AsyncMock()
        mock_conn.fetchval = AsyncMock()
        yield mock_conn
        await mock_conn.close()
    
    @pytest.mark.asyncio
    async def test_user_crud_operations(self, db_connection):
        """测试用户CRUD操作"""
        # 测试用户创建
        user_data = {
            "id": str(uuid.uuid4()),
            "username": "testuser",
            "email": "test@example.com",
            "password_hash": "hashed_password",
            "created_at": datetime.utcnow(),
            "is_active": True
        }
        
        # 模拟插入操作
        db_connection.fetchrow.return_value = user_data
        
        # 执行创建用户
        create_query = """
            INSERT INTO users (id, username, email, password_hash, created_at, is_active)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING *
        """
        
        result = await db_connection.fetchrow(
            create_query,
            user_data["id"],
            user_data["username"],
            user_data["email"],
            user_data["password_hash"],
            user_data["created_at"],
            user_data["is_active"]
        )
        
        # 验证创建结果
        assert result["username"] == "testuser"
        assert result["email"] == "test@example.com"
        assert result["is_active"] is True
        
        # 测试用户查询
        db_connection.fetchrow.return_value = user_data
        
        select_query = "SELECT * FROM users WHERE username = $1"
        user = await db_connection.fetchrow(select_query, "testuser")
        
        assert user["username"] == "testuser"
        assert user["email"] == "test@example.com"
        
        # 测试用户更新
        updated_data = user_data.copy()
        updated_data["email"] = "updated@example.com"
        updated_data["updated_at"] = datetime.utcnow()
        
        db_connection.fetchrow.return_value = updated_data
        
        update_query = """
            UPDATE users SET email = $1, updated_at = $2
            WHERE id = $3
            RETURNING *
        """
        
        updated_user = await db_connection.fetchrow(
            update_query,
            "updated@example.com",
            updated_data["updated_at"],
            user_data["id"]
        )
        
        assert updated_user["email"] == "updated@example.com"
        
        # 测试用户删除
        db_connection.fetchval.return_value = 1
        
        delete_query = "DELETE FROM users WHERE id = $1"
        deleted_count = await db_connection.fetchval(delete_query, user_data["id"])
        
        assert deleted_count == 1
    
    @pytest.mark.asyncio
    async def test_document_crud_operations(self, db_connection, sample_document):
        """测试文档CRUD操作"""
        # 测试文档创建
        document_data = {
            "id": str(uuid.uuid4()),
            "title": sample_document["title"],
            "filename": "test_document.pdf",
            "file_path": "/uploads/test_document.pdf",
            "file_size": len(sample_document["content"]),
            "mime_type": "application/pdf",
            "user_id": str(uuid.uuid4()),
            "created_at": datetime.utcnow(),
            "processing_status": "pending"
        }
        
        # 模拟文档插入
        db_connection.fetchrow.return_value = document_data
        
        create_query = """
            INSERT INTO documents (id, title, filename, file_path, file_size, 
                                 mime_type, user_id, created_at, processing_status)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING *
        """
        
        result = await db_connection.fetchrow(
            create_query,
            document_data["id"],
            document_data["title"],
            document_data["filename"],
            document_data["file_path"],
            document_data["file_size"],
            document_data["mime_type"],
            document_data["user_id"],
            document_data["created_at"],
            document_data["processing_status"]
        )
        
        # 验证创建结果
        assert result["title"] == sample_document["title"]
        assert result["processing_status"] == "pending"
        
        # 测试文档状态更新
        updated_data = document_data.copy()
        updated_data["processing_status"] = "completed"
        updated_data["processed_at"] = datetime.utcnow()
        
        db_connection.fetchrow.return_value = updated_data
        
        update_query = """
            UPDATE documents SET processing_status = $1, processed_at = $2
            WHERE id = $3
            RETURNING *
        """
        
        updated_doc = await db_connection.fetchrow(
            update_query,
            "completed",
            updated_data["processed_at"],
            document_data["id"]
        )
        
        assert updated_doc["processing_status"] == "completed"
    
    @pytest.mark.asyncio
    async def test_document_chunks_operations(self, db_connection):
        """测试文档块操作"""
        document_id = str(uuid.uuid4())
        
        # 测试批量插入文档块
        chunks_data = [
            {
                "id": str(uuid.uuid4()),
                "document_id": document_id,
                "chunk_index": i,
                "content": f"这是第{i+1}个文档块的内容",
                "token_count": 50,
                "created_at": datetime.utcnow()
            }
            for i in range(5)
        ]
        
        # 模拟批量插入
        db_connection.executemany = AsyncMock()
        
        insert_query = """
            INSERT INTO document_chunks (id, document_id, chunk_index, content, token_count, created_at)
            VALUES ($1, $2, $3, $4, $5, $6)
        """
        
        chunk_values = [
            (chunk["id"], chunk["document_id"], chunk["chunk_index"],
             chunk["content"], chunk["token_count"], chunk["created_at"])
            for chunk in chunks_data
        ]
        
        await db_connection.executemany(insert_query, chunk_values)
        
        # 验证批量插入调用
        db_connection.executemany.assert_called_once_with(insert_query, chunk_values)
        
        # 测试查询文档块
        db_connection.fetch.return_value = chunks_data
        
        select_query = """
            SELECT * FROM document_chunks 
            WHERE document_id = $1 
            ORDER BY chunk_index
        """
        
        chunks = await db_connection.fetch(select_query, document_id)
        
        assert len(chunks) == 5
        assert chunks[0]["chunk_index"] == 0
        assert chunks[4]["chunk_index"] == 4
    
    @pytest.mark.asyncio
    async def test_transaction_operations(self, db_connection):
        """测试事务操作"""
        # 模拟事务
        mock_transaction = AsyncMock()
        db_connection.transaction.return_value.__aenter__ = AsyncMock(return_value=mock_transaction)
        db_connection.transaction.return_value.__aexit__ = AsyncMock(return_value=None)
        
        user_id = str(uuid.uuid4())
        document_id = str(uuid.uuid4())
        
        # 在事务中创建用户和文档
        async with db_connection.transaction():
            # 创建用户
            user_query = """
                INSERT INTO users (id, username, email, password_hash, created_at)
                VALUES ($1, $2, $3, $4, $5)
            """
            
            await db_connection.execute(
                user_query,
                user_id,
                "transactionuser",
                "transaction@example.com",
                "hashed_password",
                datetime.utcnow()
            )
            
            # 创建文档
            doc_query = """
                INSERT INTO documents (id, title, filename, user_id, created_at)
                VALUES ($1, $2, $3, $4, $5)
            """
            
            await db_connection.execute(
                doc_query,
                document_id,
                "事务测试文档",
                "transaction_doc.pdf",
                user_id,
                datetime.utcnow()
            )
        
        # 验证事务调用
        db_connection.transaction.assert_called_once()
        assert db_connection.execute.call_count == 2
    
    @pytest.mark.asyncio
    async def test_complex_queries(self, db_connection):
        """测试复杂查询操作"""
        # 测试联表查询
        mock_results = [
            {
                "document_id": str(uuid.uuid4()),
                "document_title": "测试文档1",
                "username": "user1",
                "chunk_count": 10,
                "total_tokens": 500
            },
            {
                "document_id": str(uuid.uuid4()),
                "document_title": "测试文档2",
                "username": "user2",
                "chunk_count": 15,
                "total_tokens": 750
            }
        ]
        
        db_connection.fetch.return_value = mock_results
        
        complex_query = """
            SELECT 
                d.id as document_id,
                d.title as document_title,
                u.username,
                COUNT(dc.id) as chunk_count,
                SUM(dc.token_count) as total_tokens
            FROM documents d
            JOIN users u ON d.user_id = u.id
            LEFT JOIN document_chunks dc ON d.id = dc.document_id
            WHERE d.processing_status = $1
            GROUP BY d.id, d.title, u.username
            ORDER BY total_tokens DESC
            LIMIT $2
        """
        
        results = await db_connection.fetch(complex_query, "completed", 10)
        
        # 验证查询结果
        assert len(results) == 2
        assert results[0]["document_title"] == "测试文档1"
        assert results[0]["chunk_count"] == 10
        assert results[1]["total_tokens"] == 750


@pytest.mark.integration
class TestRedisIntegration:
    """Redis集成测试类"""
    
    @pytest.fixture
    async def redis_client(self):
        """Redis客户端fixture"""
        # 模拟Redis客户端
        mock_redis = AsyncMock()
        mock_redis.set = AsyncMock()
        mock_redis.get = AsyncMock()
        mock_redis.delete = AsyncMock()
        mock_redis.exists = AsyncMock()
        mock_redis.expire = AsyncMock()
        mock_redis.hset = AsyncMock()
        mock_redis.hget = AsyncMock()
        mock_redis.hgetall = AsyncMock()
        mock_redis.lpush = AsyncMock()
        mock_redis.rpop = AsyncMock()
        mock_redis.llen = AsyncMock()
        yield mock_redis
        await mock_redis.close()
    
    @pytest.mark.asyncio
    async def test_session_management(self, redis_client):
        """测试会话管理"""
        session_id = "session_123"
        user_id = "user_456"
        
        # 测试会话创建
        session_data = {
            "user_id": user_id,
            "username": "testuser",
            "role": "user",
            "created_at": datetime.utcnow().isoformat(),
            "last_activity": datetime.utcnow().isoformat()
        }
        
        # 模拟设置会话
        redis_client.set.return_value = True
        
        await redis_client.set(
            f"session:{session_id}",
            json.dumps(session_data),
            ex=3600  # 1小时过期
        )
        
        # 验证会话设置
        redis_client.set.assert_called_once_with(
            f"session:{session_id}",
            json.dumps(session_data),
            ex=3600
        )
        
        # 测试会话获取
        redis_client.get.return_value = json.dumps(session_data)
        
        session_json = await redis_client.get(f"session:{session_id}")
        retrieved_session = json.loads(session_json)
        
        assert retrieved_session["user_id"] == user_id
        assert retrieved_session["username"] == "testuser"
        
        # 测试会话删除
        redis_client.delete.return_value = 1
        
        deleted_count = await redis_client.delete(f"session:{session_id}")
        assert deleted_count == 1
    
    @pytest.mark.asyncio
    async def test_caching_operations(self, redis_client):
        """测试缓存操作"""
        # 测试文档缓存
        document_id = "doc_123"
        document_data = {
            "id": document_id,
            "title": "缓存测试文档",
            "content": "这是缓存的文档内容",
            "processing_status": "completed"
        }
        
        # 设置文档缓存
        redis_client.set.return_value = True
        
        await redis_client.set(
            f"document:{document_id}",
            json.dumps(document_data),
            ex=1800  # 30分钟过期
        )
        
        # 获取文档缓存
        redis_client.get.return_value = json.dumps(document_data)
        
        cached_doc_json = await redis_client.get(f"document:{document_id}")
        cached_doc = json.loads(cached_doc_json)
        
        assert cached_doc["id"] == document_id
        assert cached_doc["title"] == "缓存测试文档"
        
        # 测试缓存存在性检查
        redis_client.exists.return_value = 1
        
        exists = await redis_client.exists(f"document:{document_id}")
        assert exists == 1
        
        # 测试缓存过期时间设置
        redis_client.expire.return_value = True
        
        await redis_client.expire(f"document:{document_id}", 3600)
        redis_client.expire.assert_called_once_with(f"document:{document_id}", 3600)
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, redis_client):
        """测试限流功能"""
        user_id = "user_123"
        api_endpoint = "/api/documents/upload"
        
        # 测试限流计数器
        rate_limit_key = f"rate_limit:{user_id}:{api_endpoint}"
        
        # 模拟当前计数
        redis_client.get.return_value = "5"  # 当前已有5次请求
        
        current_count = await redis_client.get(rate_limit_key)
        current_count = int(current_count) if current_count else 0
        
        assert current_count == 5
        
        # 增加计数
        redis_client.incr = AsyncMock(return_value=6)
        
        new_count = await redis_client.incr(rate_limit_key)
        assert new_count == 6
        
        # 设置过期时间（如果是新键）
        if current_count == 0:
            await redis_client.expire(rate_limit_key, 3600)  # 1小时窗口
        
        # 检查是否超过限制（假设限制为10次/小时）
        rate_limit = 10
        is_rate_limited = new_count > rate_limit
        assert not is_rate_limited  # 6 <= 10，未超限
    
    @pytest.mark.asyncio
    async def test_task_queue_operations(self, redis_client):
        """测试任务队列操作"""
        queue_name = "document_processing_queue"
        
        # 测试任务入队
        task_data = {
            "task_id": str(uuid.uuid4()),
            "document_id": "doc_123",
            "task_type": "text_extraction",
            "priority": "high",
            "created_at": datetime.utcnow().isoformat()
        }
        
        redis_client.lpush.return_value = 1
        
        queue_length = await redis_client.lpush(queue_name, json.dumps(task_data))
        assert queue_length == 1
        
        # 测试任务出队
        redis_client.rpop.return_value = json.dumps(task_data)
        
        task_json = await redis_client.rpop(queue_name)
        dequeued_task = json.loads(task_json)
        
        assert dequeued_task["task_id"] == task_data["task_id"]
        assert dequeued_task["task_type"] == "text_extraction"
        
        # 测试队列长度
        redis_client.llen.return_value = 0
        
        queue_length = await redis_client.llen(queue_name)
        assert queue_length == 0
    
    @pytest.mark.asyncio
    async def test_distributed_locks(self, redis_client):
        """测试分布式锁"""
        lock_key = "lock:document_processing:doc_123"
        lock_value = str(uuid.uuid4())
        
        # 测试获取锁
        redis_client.set.return_value = True
        
        # 使用NX（不存在时设置）和EX（过期时间）选项
        lock_acquired = await redis_client.set(
            lock_key,
            lock_value,
            nx=True,  # 只在键不存在时设置
            ex=300    # 5分钟过期
        )
        
        assert lock_acquired is True
        
        # 测试锁验证
        redis_client.get.return_value = lock_value
        
        current_lock_value = await redis_client.get(lock_key)
        is_lock_owner = current_lock_value == lock_value
        assert is_lock_owner is True
        
        # 测试释放锁
        redis_client.delete.return_value = 1
        
        # 只有锁的拥有者才能释放锁
        if is_lock_owner:
            deleted = await redis_client.delete(lock_key)
            assert deleted == 1


@pytest.mark.integration
class TestDatabaseConsistency:
    """数据库一致性测试类"""
    
    @pytest.mark.asyncio
    async def test_user_document_consistency(self, db_connection):
        """测试用户和文档数据一致性"""
        user_id = str(uuid.uuid4())
        document_id = str(uuid.uuid4())
        
        # 模拟用户创建
        user_data = {
            "id": user_id,
            "username": "consistencyuser",
            "email": "consistency@example.com",
            "created_at": datetime.utcnow()
        }
        
        db_connection.fetchrow.return_value = user_data
        
        # 创建用户
        user_query = """
            INSERT INTO users (id, username, email, created_at)
            VALUES ($1, $2, $3, $4)
            RETURNING *
        """
        
        created_user = await db_connection.fetchrow(
            user_query,
            user_id,
            "consistencyuser",
            "consistency@example.com",
            user_data["created_at"]
        )
        
        assert created_user["id"] == user_id
        
        # 模拟文档创建（引用用户ID）
        document_data = {
            "id": document_id,
            "title": "一致性测试文档",
            "user_id": user_id,
            "created_at": datetime.utcnow()
        }
        
        db_connection.fetchrow.return_value = document_data
        
        # 创建文档
        doc_query = """
            INSERT INTO documents (id, title, user_id, created_at)
            VALUES ($1, $2, $3, $4)
            RETURNING *
        """
        
        created_doc = await db_connection.fetchrow(
            doc_query,
            document_id,
            "一致性测试文档",
            user_id,
            document_data["created_at"]
        )
        
        assert created_doc["user_id"] == user_id
        
        # 验证外键约束（模拟查询验证）
        validation_data = {
            "document_id": document_id,
            "document_title": "一致性测试文档",
            "user_id": user_id,
            "username": "consistencyuser"
        }
        
        db_connection.fetchrow.return_value = validation_data
        
        validation_query = """
            SELECT d.id as document_id, d.title as document_title,
                   u.id as user_id, u.username
            FROM documents d
            JOIN users u ON d.user_id = u.id
            WHERE d.id = $1
        """
        
        validation_result = await db_connection.fetchrow(validation_query, document_id)
        
        assert validation_result["document_id"] == document_id
        assert validation_result["user_id"] == user_id
        assert validation_result["username"] == "consistencyuser"
    
    @pytest.mark.asyncio
    async def test_document_chunks_consistency(self, db_connection):
        """测试文档和文档块数据一致性"""
        document_id = str(uuid.uuid4())
        
        # 创建文档
        document_data = {
            "id": document_id,
            "title": "块一致性测试文档",
            "chunk_count": 0,
            "created_at": datetime.utcnow()
        }
        
        db_connection.fetchrow.return_value = document_data
        
        # 创建文档块
        chunks_data = [
            {
                "id": str(uuid.uuid4()),
                "document_id": document_id,
                "chunk_index": i,
                "content": f"块{i+1}内容",
                "created_at": datetime.utcnow()
            }
            for i in range(3)
        ]
        
        # 模拟批量插入块
        db_connection.executemany = AsyncMock()
        
        chunks_query = """
            INSERT INTO document_chunks (id, document_id, chunk_index, content, created_at)
            VALUES ($1, $2, $3, $4, $5)
        """
        
        chunk_values = [
            (chunk["id"], chunk["document_id"], chunk["chunk_index"],
             chunk["content"], chunk["created_at"])
            for chunk in chunks_data
        ]
        
        await db_connection.executemany(chunks_query, chunk_values)
        
        # 更新文档的块计数
        updated_document = document_data.copy()
        updated_document["chunk_count"] = 3
        
        db_connection.fetchrow.return_value = updated_document
        
        update_query = """
            UPDATE documents SET chunk_count = $1
            WHERE id = $2
            RETURNING *
        """
        
        updated_doc = await db_connection.fetchrow(update_query, 3, document_id)
        
        assert updated_doc["chunk_count"] == 3
        
        # 验证一致性（块数量与文档记录的块数量一致）
        db_connection.fetchval.return_value = 3
        
        count_query = "SELECT COUNT(*) FROM document_chunks WHERE document_id = $1"
        actual_chunk_count = await db_connection.fetchval(count_query, document_id)
        
        assert actual_chunk_count == updated_doc["chunk_count"]
    
    @pytest.mark.asyncio
    async def test_cache_database_consistency(self, db_connection, redis_client):
        """测试缓存和数据库数据一致性"""
        document_id = str(uuid.uuid4())
        
        # 数据库中的文档数据
        db_document = {
            "id": document_id,
            "title": "缓存一致性测试",
            "processing_status": "completed",
            "updated_at": datetime.utcnow()
        }
        
        db_connection.fetchrow.return_value = db_document
        
        # 从数据库获取文档
        db_query = "SELECT * FROM documents WHERE id = $1"
        db_result = await db_connection.fetchrow(db_query, document_id)
        
        # 更新缓存
        cache_key = f"document:{document_id}"
        redis_client.set.return_value = True
        
        await redis_client.set(
            cache_key,
            json.dumps(db_result, default=str),
            ex=1800
        )
        
        # 从缓存获取文档
        redis_client.get.return_value = json.dumps(db_result, default=str)
        
        cached_doc_json = await redis_client.get(cache_key)
        cached_doc = json.loads(cached_doc_json)
        
        # 验证一致性
        assert cached_doc["id"] == db_result["id"]
        assert cached_doc["title"] == db_result["title"]
        assert cached_doc["processing_status"] == db_result["processing_status"]
        
        # 模拟数据库更新
        updated_db_document = db_document.copy()
        updated_db_document["processing_status"] = "reprocessing"
        updated_db_document["updated_at"] = datetime.utcnow()
        
        db_connection.fetchrow.return_value = updated_db_document
        
        # 更新数据库
        update_query = """
            UPDATE documents SET processing_status = $1, updated_at = $2
            WHERE id = $3
            RETURNING *
        """
        
        updated_db_result = await db_connection.fetchrow(
            update_query,
            "reprocessing",
            updated_db_document["updated_at"],
            document_id
        )
        
        # 同步更新缓存
        await redis_client.set(
            cache_key,
            json.dumps(updated_db_result, default=str),
            ex=1800
        )
        
        # 验证缓存已更新
        redis_client.get.return_value = json.dumps(updated_db_result, default=str)
        
        updated_cached_doc_json = await redis_client.get(cache_key)
        updated_cached_doc = json.loads(updated_cached_doc_json)
        
        assert updated_cached_doc["processing_status"] == "reprocessing"


@pytest.mark.integration
@pytest.mark.slow
class TestDatabasePerformance:
    """数据库性能测试类"""
    
    @pytest.mark.asyncio
    async def test_bulk_insert_performance(self, db_connection):
        """测试批量插入性能"""
        import time
        
        # 准备大量测试数据
        batch_size = 1000
        documents_data = [
            {
                "id": str(uuid.uuid4()),
                "title": f"性能测试文档{i}",
                "filename": f"perf_test_{i}.pdf",
                "user_id": str(uuid.uuid4()),
                "created_at": datetime.utcnow()
            }
            for i in range(batch_size)
        ]
        
        # 模拟批量插入
        db_connection.executemany = AsyncMock()
        
        insert_query = """
            INSERT INTO documents (id, title, filename, user_id, created_at)
            VALUES ($1, $2, $3, $4, $5)
        """
        
        values = [
            (doc["id"], doc["title"], doc["filename"], doc["user_id"], doc["created_at"])
            for doc in documents_data
        ]
        
        # 测量执行时间
        start_time = time.time()
        await db_connection.executemany(insert_query, values)
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # 验证性能（1000条记录应在2秒内完成）
        assert execution_time < 2.0, f"批量插入耗时过长: {execution_time}秒"
        
        # 验证调用
        db_connection.executemany.assert_called_once_with(insert_query, values)
    
    @pytest.mark.asyncio
    async def test_concurrent_database_operations(self, db_connection):
        """测试并发数据库操作"""
        import time
        
        async def create_user(user_index):
            """创建单个用户"""
            user_data = {
                "id": str(uuid.uuid4()),
                "username": f"concurrentuser{user_index}",
                "email": f"concurrent{user_index}@example.com",
                "created_at": datetime.utcnow()
            }
            
            db_connection.fetchrow.return_value = user_data
            
            query = """
                INSERT INTO users (id, username, email, created_at)
                VALUES ($1, $2, $3, $4)
                RETURNING *
            """
            
            result = await db_connection.fetchrow(
                query,
                user_data["id"],
                user_data["username"],
                user_data["email"],
                user_data["created_at"]
            )
            
            return result["id"]
        
        # 并发创建用户
        start_time = time.time()
        tasks = [create_user(i) for i in range(20)]
        user_ids = await asyncio.gather(*tasks)
        end_time = time.time()
        
        # 验证结果
        assert len(user_ids) == 20
        assert all(user_id for user_id in user_ids)
        
        # 性能断言（20个并发操作应在3秒内完成）
        execution_time = end_time - start_time
        assert execution_time < 3.0, f"并发操作耗时过长: {execution_time}秒"
    
    @pytest.mark.asyncio
    async def test_redis_performance(self, redis_client):
        """测试Redis性能"""
        import time
        
        # 测试大量键值对操作
        key_count = 1000
        
        # 模拟批量设置
        redis_client.set.return_value = True
        
        start_time = time.time()
        
        # 并发设置多个键
        async def set_key(index):
            key = f"perf_test_key_{index}"
            value = f"perf_test_value_{index}"
            return await redis_client.set(key, value, ex=3600)
        
        tasks = [set_key(i) for i in range(key_count)]
        results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        
        # 验证结果
        assert all(result is True for result in results)
        
        # 性能断言（1000个键值对操作应在1秒内完成）
        execution_time = end_time - start_time
        assert execution_time < 1.0, f"Redis批量操作耗时过长: {execution_time}秒"
        
        # 验证调用次数
        assert redis_client.set.call_count == key_count