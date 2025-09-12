# -*- coding: utf-8 -*-
"""
数据库服务测试用例

提供PostgreSQL、Neo4j、Redis数据库服务的
单元测试、集成测试和性能测试。

Author: Knowledge RAG System
Date: 2025-01-16
"""

import pytest
import asyncio
import os
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

# 导入被测试的模块
from .postgres_config import PostgreSQLManager, PostgreSQLConfig
from .neo4j_config import Neo4jManager, Neo4jConfig
from .redis_config import RedisManager, RedisConfig
from .migration_manager import MigrationManager
from .performance_optimizer import PerformanceOptimizer
from .health_monitor import DatabaseHealthMonitor, HealthStatus
from .backup_manager import DatabaseBackupManager, BackupType, BackupStatus

# 测试配置
TEST_POSTGRES_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'username': 'test_user',
    'password': 'test_pass',
    'database': 'test_db'
}

TEST_NEO4J_CONFIG = {
    'uri': 'bolt://localhost:7687',
    'username': 'neo4j',
    'password': 'test_pass'
}

TEST_REDIS_CONFIG = {
    'host': 'localhost',
    'port': 6379,
    'password': None,
    'db': 0
}

class TestPostgreSQLManager:
    """
    PostgreSQL管理器测试类
    """
    
    @pytest.fixture
    async def postgres_manager(self):
        """创建PostgreSQL管理器测试实例"""
        config = PostgreSQLConfig(**TEST_POSTGRES_CONFIG)
        manager = PostgreSQLManager(config)
        yield manager
        await manager.close_all_connections()
    
    @pytest.mark.asyncio
    async def test_config_initialization(self):
        """测试配置初始化"""
        config = PostgreSQLConfig(**TEST_POSTGRES_CONFIG)
        
        assert config.host == 'localhost'
        assert config.port == 5432
        assert config.username == 'test_user'
        assert config.database == 'test_db'
        assert config.pool_size == 10  # 默认值
        assert config.max_overflow == 20  # 默认值
    
    @pytest.mark.asyncio
    async def test_connection_string_generation(self):
        """测试连接字符串生成"""
        config = PostgreSQLConfig(**TEST_POSTGRES_CONFIG)
        
        expected = "postgresql+asyncpg://test_user:test_pass@localhost:5432/test_db"
        assert config.get_connection_string() == expected
    
    @pytest.mark.asyncio
    async def test_manager_initialization(self, postgres_manager):
        """测试管理器初始化"""
        assert postgres_manager.config is not None
        assert postgres_manager.engines == {}
        assert postgres_manager.sessions == {}
    
    @pytest.mark.asyncio
    @patch('sqlalchemy.ext.asyncio.create_async_engine')
    async def test_initialize_database(self, mock_create_engine, postgres_manager):
        """测试数据库初始化"""
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine
        
        await postgres_manager.initialize_database('test_db')
        
        assert 'test_db' in postgres_manager.engines
        mock_create_engine.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_session_without_initialization(self, postgres_manager):
        """测试未初始化时获取会话"""
        with pytest.raises(Exception, match="数据库未初始化"):
            async with postgres_manager.get_session('test_db'):
                pass
    
    @pytest.mark.asyncio
    @patch('sqlalchemy.ext.asyncio.create_async_engine')
    async def test_connection_info(self, mock_create_engine, postgres_manager):
        """测试连接信息获取"""
        mock_engine = Mock()
        mock_pool = Mock()
        mock_pool.size.return_value = 10
        mock_pool.checked_out.return_value = 3
        mock_pool.checked_in.return_value = 7
        mock_pool.overflow.return_value = 0
        mock_pool.invalid.return_value = 0
        mock_engine.pool = mock_pool
        mock_create_engine.return_value = mock_engine
        
        await postgres_manager.initialize_database('test_db')
        info = await postgres_manager.get_connection_info('test_db')
        
        assert info['pool_size'] == 10
        assert info['checked_out'] == 3
        assert info['checked_in'] == 7

class TestNeo4jManager:
    """
    Neo4j管理器测试类
    """
    
    @pytest.fixture
    async def neo4j_manager(self):
        """创建Neo4j管理器测试实例"""
        config = Neo4jConfig(**TEST_NEO4J_CONFIG)
        manager = Neo4jManager(config)
        yield manager
        await manager.close()
    
    @pytest.mark.asyncio
    async def test_config_initialization(self):
        """测试配置初始化"""
        config = Neo4jConfig(**TEST_NEO4J_CONFIG)
        
        assert config.uri == 'bolt://localhost:7687'
        assert config.username == 'neo4j'
        assert config.password == 'test_pass'
        assert config.max_connection_lifetime == 3600  # 默认值
        assert config.max_connection_pool_size == 100  # 默认值
    
    @pytest.mark.asyncio
    @patch('neo4j.AsyncGraphDatabase.driver')
    async def test_initialize(self, mock_driver, neo4j_manager):
        """测试初始化"""
        mock_driver_instance = Mock()
        mock_driver.return_value = mock_driver_instance
        
        await neo4j_manager.initialize()
        
        assert neo4j_manager.driver is not None
        mock_driver.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_query_without_initialization(self, neo4j_manager):
        """测试未初始化时执行查询"""
        with pytest.raises(Exception, match="Neo4j驱动未初始化"):
            await neo4j_manager.execute_query("RETURN 1")
    
    @pytest.mark.asyncio
    @patch('neo4j.AsyncGraphDatabase.driver')
    async def test_create_index(self, mock_driver, neo4j_manager):
        """测试创建索引"""
        mock_driver_instance = Mock()
        mock_session = AsyncMock()
        mock_driver_instance.session.return_value.__aenter__.return_value = mock_session
        mock_driver.return_value = mock_driver_instance
        
        await neo4j_manager.initialize()
        await neo4j_manager.create_index('Person', 'name')
        
        mock_session.run.assert_called_once()

class TestRedisManager:
    """
    Redis管理器测试类
    """
    
    @pytest.fixture
    async def redis_manager(self):
        """创建Redis管理器测试实例"""
        config = RedisConfig(**TEST_REDIS_CONFIG)
        manager = RedisManager(config)
        yield manager
        await manager.close()
    
    @pytest.mark.asyncio
    async def test_config_initialization(self):
        """测试配置初始化"""
        config = RedisConfig(**TEST_REDIS_CONFIG)
        
        assert config.host == 'localhost'
        assert config.port == 6379
        assert config.db == 0
        assert config.max_connections == 100  # 默认值
        assert config.socket_timeout == 5.0  # 默认值
    
    @pytest.mark.asyncio
    @patch('redis.asyncio.ConnectionPool')
    @patch('redis.asyncio.Redis')
    async def test_initialize(self, mock_redis, mock_pool, redis_manager):
        """测试初始化"""
        mock_pool_instance = Mock()
        mock_redis_instance = Mock()
        mock_pool.return_value = mock_pool_instance
        mock_redis.return_value = mock_redis_instance
        
        await redis_manager.initialize()
        
        assert redis_manager.pool is not None
        assert redis_manager.client is not None
        mock_pool.assert_called_once()
        mock_redis.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cache_operations_without_initialization(self, redis_manager):
        """测试未初始化时的缓存操作"""
        with pytest.raises(Exception, match="Redis未连接"):
            await redis_manager.set_cache('test_key', 'test_value')
    
    @pytest.mark.asyncio
    @patch('redis.asyncio.ConnectionPool')
    @patch('redis.asyncio.Redis')
    async def test_cache_operations(self, mock_redis, mock_pool, redis_manager):
        """测试缓存操作"""
        mock_client = AsyncMock()
        mock_redis.return_value = mock_client
        
        await redis_manager.initialize()
        
        # 测试设置缓存
        await redis_manager.set_cache('test_key', 'test_value', ttl=60)
        mock_client.setex.assert_called_once_with('test_key', 60, 'test_value')
        
        # 测试获取缓存
        mock_client.get.return_value = b'test_value'
        result = await redis_manager.get_cache('test_key')
        assert result == 'test_value'
        
        # 测试删除缓存
        await redis_manager.delete_cache('test_key')
        mock_client.delete.assert_called_once_with('test_key')

class TestMigrationManager:
    """
    迁移管理器测试类
    """
    
    @pytest.fixture
    def temp_migrations_dir(self):
        """创建临时迁移目录"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    async def migration_manager(self, temp_migrations_dir):
        """创建迁移管理器测试实例"""
        with patch('services.database_service.migration_manager.postgres_manager') as mock_pg:
            mock_pg.get_session.return_value.__aenter__ = AsyncMock()
            mock_pg.get_session.return_value.__aexit__ = AsyncMock()
            
            manager = MigrationManager(str(temp_migrations_dir))
            yield manager
    
    @pytest.mark.asyncio
    async def test_create_migration_file(self, migration_manager, temp_migrations_dir):
        """测试创建迁移文件"""
        migration_name = "add_user_table"
        file_path = await migration_manager.create_migration(migration_name)
        
        assert file_path.exists()
        assert migration_name in file_path.name
        assert file_path.suffix == '.sql'
    
    @pytest.mark.asyncio
    async def test_parse_migration_file(self, migration_manager, temp_migrations_dir):
        """测试解析迁移文件"""
        # 创建测试迁移文件
        migration_content = """
-- Migration: Test Migration
-- Author: Test
-- Date: 2025-01-16

-- Up
CREATE TABLE test_table (id SERIAL PRIMARY KEY);

-- Down
DROP TABLE test_table;
"""
        
        migration_file = temp_migrations_dir / "001_test_migration.sql"
        migration_file.write_text(migration_content)
        
        up_sql, down_sql = await migration_manager._parse_migration_file(migration_file)
        
        assert "CREATE TABLE test_table" in up_sql
        assert "DROP TABLE test_table" in down_sql
    
    @pytest.mark.asyncio
    async def test_get_pending_migrations(self, migration_manager, temp_migrations_dir):
        """测试获取待执行迁移"""
        # 创建测试迁移文件
        (temp_migrations_dir / "001_first.sql").touch()
        (temp_migrations_dir / "002_second.sql").touch()
        
        with patch.object(migration_manager, '_get_applied_migrations', return_value=['001_first.sql']):
            pending = await migration_manager.get_pending_migrations()
            
            assert len(pending) == 1
            assert "002_second.sql" in pending[0].name

class TestPerformanceOptimizer:
    """
    性能优化器测试类
    """
    
    @pytest.fixture
    async def performance_optimizer(self):
        """创建性能优化器测试实例"""
        optimizer = PerformanceOptimizer()
        yield optimizer
    
    @pytest.mark.asyncio
    async def test_record_query_metrics(self, performance_optimizer):
        """测试记录查询指标"""
        await performance_optimizer._record_query_metrics(
            statement="SELECT * FROM users",
            execution_time=0.5,
            database="test_db",
            rows_affected=10
        )
        
        assert len(performance_optimizer.query_metrics) == 1
        metric = performance_optimizer.query_metrics[0]
        assert metric.sql == "SELECT * FROM users"
        assert metric.execution_time == 0.5
        assert metric.database == "test_db"
        assert metric.rows_affected == 10
    
    @pytest.mark.asyncio
    async def test_slow_query_detection(self, performance_optimizer):
        """测试慢查询检测"""
        performance_optimizer.slow_query_threshold = 1.0
        
        with patch.object(performance_optimizer, '_handle_slow_query') as mock_handle:
            await performance_optimizer._record_query_metrics(
                statement="SELECT * FROM large_table",
                execution_time=2.0,
                database="test_db"
            )
            
            mock_handle.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_optimization_suggestions(self, performance_optimizer):
        """测试优化建议生成"""
        from services.database_service.performance_optimizer import QueryMetrics
        
        metrics = QueryMetrics(
            query_hash="test_hash",
            sql="SELECT * FROM users ORDER BY created_at",
            execution_time=2.0,
            timestamp=datetime.now(),
            database="test_db"
        )
        
        suggestions = await performance_optimizer._generate_optimization_suggestions(metrics)
        
        assert "避免使用SELECT *" in suggestions
        assert "ORDER BY查询建议添加LIMIT" in suggestions
    
    @pytest.mark.asyncio
    async def test_get_query_statistics(self, performance_optimizer):
        """测试获取查询统计"""
        # 添加测试数据
        await performance_optimizer._record_query_metrics(
            statement="SELECT id FROM users",
            execution_time=0.1,
            database="test_db"
        )
        await performance_optimizer._record_query_metrics(
            statement="SELECT name FROM users",
            execution_time=0.2,
            database="test_db"
        )
        
        stats = await performance_optimizer.get_query_statistics(database="test_db")
        
        assert stats['total_queries'] == 2
        assert stats['avg_execution_time'] == 0.15
        assert stats['max_execution_time'] == 0.2
        assert stats['min_execution_time'] == 0.1

class TestHealthMonitor:
    """
    健康监控器测试类
    """
    
    @pytest.fixture
    async def health_monitor(self):
        """创建健康监控器测试实例"""
        monitor = DatabaseHealthMonitor()
        yield monitor
        await monitor.stop_monitoring()
    
    @pytest.mark.asyncio
    async def test_initialization(self, health_monitor):
        """测试初始化"""
        await health_monitor.initialize()
        
        assert 'postgresql' in health_monitor.health_history
        assert 'neo4j' in health_monitor.health_history
        assert 'redis' in health_monitor.health_history
        assert health_monitor.is_monitoring
    
    @pytest.mark.asyncio
    @patch('services.database_service.health_monitor.postgres_manager')
    async def test_postgresql_health_check(self, mock_postgres, health_monitor):
        """测试PostgreSQL健康检查"""
        mock_postgres.check_connection.return_value = True
        mock_postgres.get_session.return_value.__aenter__ = AsyncMock()
        mock_postgres.get_session.return_value.__aexit__ = AsyncMock()
        
        mock_session = Mock()
        mock_result = Mock()
        mock_result.scalar.return_value = 1
        mock_session.execute.return_value = mock_result
        mock_postgres.get_session.return_value.__aenter__.return_value = mock_session
        
        mock_postgres.get_connection_info.return_value = {
            'pool_size': 10,
            'checked_out': 2,
            'checked_in': 8
        }
        
        result = await health_monitor._check_postgresql_health()
        
        assert result.service == 'postgresql'
        assert result.status == HealthStatus.HEALTHY
        assert result.response_time > 0
    
    @pytest.mark.asyncio
    @patch('services.database_service.health_monitor.postgres_manager')
    async def test_postgresql_health_check_failure(self, mock_postgres, health_monitor):
        """测试PostgreSQL健康检查失败"""
        mock_postgres.check_connection.return_value = False
        
        result = await health_monitor._check_postgresql_health()
        
        assert result.service == 'postgresql'
        assert result.status == HealthStatus.CRITICAL
        assert "无法连接到PostgreSQL" in result.message
    
    @pytest.mark.asyncio
    async def test_alert_callback(self, health_monitor):
        """测试告警回调"""
        callback_called = False
        alert_data = None
        
        async def test_callback(data):
            nonlocal callback_called, alert_data
            callback_called = True
            alert_data = data
        
        health_monitor.add_alert_callback(test_callback)
        
        # 模拟告警
        from services.database_service.health_monitor import HealthCheckResult
        
        result = HealthCheckResult(
            service='test_service',
            status=HealthStatus.CRITICAL,
            response_time=1.0,
            timestamp=datetime.now(),
            message='Test alert'
        )
        
        health_monitor.failure_counts['test_service'] = 3  # 达到告警阈值
        await health_monitor._send_alert(result)
        
        assert callback_called
        assert alert_data['service'] == 'test_service'
        assert alert_data['status'] == 'critical'

class TestBackupManager:
    """
    备份管理器测试类
    """
    
    @pytest.fixture
    def temp_backup_dir(self):
        """创建临时备份目录"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    async def backup_manager(self, temp_backup_dir):
        """创建备份管理器测试实例"""
        with patch.dict(os.environ, {'BACKUP_ROOT_DIR': str(temp_backup_dir)}):
            manager = DatabaseBackupManager()
            yield manager
    
    @pytest.mark.asyncio
    async def test_initialization(self, backup_manager, temp_backup_dir):
        """测试初始化"""
        await backup_manager.initialize()
        
        assert backup_manager.backup_root == temp_backup_dir
        assert (temp_backup_dir / 'postgresql').exists()
        assert (temp_backup_dir / 'neo4j').exists()
        assert (temp_backup_dir / 'redis').exists()
    
    @pytest.mark.asyncio
    async def test_calculate_checksum(self, backup_manager, temp_backup_dir):
        """测试校验和计算"""
        test_file = temp_backup_dir / 'test.txt'
        test_content = 'Hello, World!'
        test_file.write_text(test_content)
        
        checksum = await backup_manager._calculate_checksum(test_file)
        
        import hashlib
        expected = hashlib.md5(test_content.encode()).hexdigest()
        assert checksum == expected
    
    @pytest.mark.asyncio
    async def test_backup_record_management(self, backup_manager):
        """测试备份记录管理"""
        from services.database_service.backup_manager import BackupRecord
        
        record = BackupRecord(
            backup_id='test_backup_001',
            service='postgresql',
            backup_type=BackupType.FULL,
            status=BackupStatus.COMPLETED,
            file_path='/tmp/test_backup.sql',
            file_size=1024,
            checksum='abc123',
            created_at=datetime.now()
        )
        
        backup_manager.backup_records.append(record)
        
        # 测试获取备份状态
        status = await backup_manager.get_backup_status('test_backup_001')
        assert status is not None
        assert status['backup_id'] == 'test_backup_001'
        assert status['service'] == 'postgresql'
        
        # 测试列出备份
        backups = await backup_manager.list_backups(service='postgresql')
        assert len(backups) == 1
        assert backups[0]['backup_id'] == 'test_backup_001'
    
    @pytest.mark.asyncio
    async def test_backup_statistics(self, backup_manager):
        """测试备份统计"""
        from services.database_service.backup_manager import BackupRecord
        
        # 添加测试备份记录
        records = [
            BackupRecord(
                backup_id=f'backup_{i}',
                service='postgresql' if i % 2 == 0 else 'redis',
                backup_type=BackupType.FULL,
                status=BackupStatus.COMPLETED,
                file_path=f'/tmp/backup_{i}.sql',
                file_size=1024 * (i + 1),
                checksum=f'hash_{i}',
                created_at=datetime.now() - timedelta(days=i)
            )
            for i in range(5)
        ]
        
        backup_manager.backup_records.extend(records)
        
        stats = await backup_manager.get_backup_statistics()
        
        assert stats['total_backups'] == 5
        assert 'postgresql' in stats['services']
        assert 'redis' in stats['services']
        assert stats['services']['postgresql']['count'] == 3
        assert stats['services']['redis']['count'] == 2
        assert stats['total_size'] == sum(r.file_size for r in records)

# 集成测试
class TestDatabaseServiceIntegration:
    """
    数据库服务集成测试
    """
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_full_service_lifecycle(self):
        """测试完整服务生命周期"""
        # 这个测试需要真实的数据库连接，通常在CI/CD环境中运行
        pass
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_cross_service_operations(self):
        """测试跨服务操作"""
        # 测试PostgreSQL、Neo4j和Redis之间的协作
        pass
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_performance_under_load(self):
        """测试负载下的性能"""
        # 性能测试，模拟高并发场景
        pass

# 测试运行配置
if __name__ == '__main__':
    # 运行测试
    pytest.main([
        __file__,
        '-v',
        '--tb=short',
        '--asyncio-mode=auto'
    ])