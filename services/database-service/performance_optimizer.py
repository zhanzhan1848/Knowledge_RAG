# -*- coding: utf-8 -*-
"""
数据库连接池和性能优化模块

提供数据库连接池管理、查询优化、性能监控、
慢查询分析和自动调优功能。

Author: Knowledge RAG System
Date: 2025-01-16
"""

import os
import asyncio
import logging
import time
from typing import Optional, Dict, Any, List, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import defaultdict, deque
import statistics
from sqlalchemy import text, event
from sqlalchemy.engine import Engine
from sqlalchemy.pool import QueuePool, StaticPool
from .postgres_config import postgres_manager
from .redis_config import redis_manager

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class QueryMetrics:
    """
    查询性能指标
    """
    query_hash: str
    sql: str
    execution_time: float
    timestamp: datetime
    database: str
    rows_affected: int = 0
    error: Optional[str] = None

@dataclass
class ConnectionPoolMetrics:
    """
    连接池性能指标
    """
    database: str
    pool_size: int
    checked_out: int
    checked_in: int
    overflow: int
    invalid: int
    total_connections: int
    utilization_rate: float

class PerformanceOptimizer:
    """
    数据库性能优化器
    
    提供连接池优化、查询性能监控、慢查询分析和自动调优功能。
    """
    
    def __init__(self):
        """初始化性能优化器"""
        self.query_metrics: deque = deque(maxlen=10000)  # 保留最近10000条查询记录
        self.slow_query_threshold = float(os.getenv('SLOW_QUERY_THRESHOLD', 1.0))  # 慢查询阈值（秒）
        self.monitoring_enabled = os.getenv('DB_MONITORING_ENABLED', 'true').lower() == 'true'
        
        # 性能统计
        self.query_stats = defaultdict(list)
        self.connection_stats = defaultdict(list)
        
        # 优化建议缓存
        self.optimization_cache = {}
        
    async def initialize(self):
        """
        初始化性能优化器
        """
        if self.monitoring_enabled:
            # 注册查询监听器
            await self._register_query_listeners()
            
            # 启动性能监控任务
            asyncio.create_task(self._performance_monitoring_task())
            
        logger.info("性能优化器初始化完成")
    
    async def _register_query_listeners(self):
        """
        注册查询性能监听器
        """
        for db_name, engine in postgres_manager.engines.items():
            # 注册查询开始事件
            @event.listens_for(engine.sync_engine, "before_cursor_execute")
            def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
                context._query_start_time = time.time()
                context._query_statement = statement
                context._query_database = db_name
            
            # 注册查询结束事件
            @event.listens_for(engine.sync_engine, "after_cursor_execute")
            def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
                if hasattr(context, '_query_start_time'):
                    execution_time = time.time() - context._query_start_time
                    
                    # 记录查询指标
                    asyncio.create_task(self._record_query_metrics(
                        statement=statement,
                        execution_time=execution_time,
                        database=getattr(context, '_query_database', 'unknown'),
                        rows_affected=cursor.rowcount if hasattr(cursor, 'rowcount') else 0
                    ))
    
    async def _record_query_metrics(self, statement: str, execution_time: float, 
                                   database: str, rows_affected: int = 0, error: str = None):
        """
        记录查询性能指标
        
        Args:
            statement: SQL语句
            execution_time: 执行时间
            database: 数据库名称
            rows_affected: 影响行数
            error: 错误信息
        """
        import hashlib
        
        # 生成查询哈希（用于去重和统计）
        query_hash = hashlib.md5(statement.encode()).hexdigest()[:16]
        
        metrics = QueryMetrics(
            query_hash=query_hash,
            sql=statement,
            execution_time=execution_time,
            timestamp=datetime.now(),
            database=database,
            rows_affected=rows_affected,
            error=error
        )
        
        # 添加到指标队列
        self.query_metrics.append(metrics)
        
        # 更新统计信息
        self.query_stats[query_hash].append(execution_time)
        
        # 检查是否为慢查询
        if execution_time > self.slow_query_threshold:
            await self._handle_slow_query(metrics)
        
        # 缓存到Redis（可选）
        if redis_manager._is_connected:
            try:
                await redis_manager.set_cache(
                    f"query_metrics:{query_hash}:{int(time.time())}",
                    {
                        'sql': statement[:500],  # 截断长SQL
                        'execution_time': execution_time,
                        'database': database,
                        'timestamp': metrics.timestamp.isoformat()
                    },
                    ttl=3600,  # 1小时
                    db=redis_manager.metrics_db
                )
            except Exception as e:
                logger.warning(f"缓存查询指标失败: {e}")
    
    async def _handle_slow_query(self, metrics: QueryMetrics):
        """
        处理慢查询
        
        Args:
            metrics: 查询指标
        """
        logger.warning(
            f"慢查询检测: {metrics.database} - {metrics.execution_time:.3f}s - "
            f"{metrics.sql[:100]}{'...' if len(metrics.sql) > 100 else ''}"
        )
        
        # 生成优化建议
        suggestions = await self._generate_optimization_suggestions(metrics)
        
        if suggestions:
            logger.info(f"优化建议: {', '.join(suggestions)}")
    
    async def _generate_optimization_suggestions(self, metrics: QueryMetrics) -> List[str]:
        """
        生成查询优化建议
        
        Args:
            metrics: 查询指标
            
        Returns:
            List[str]: 优化建议列表
        """
        suggestions = []
        sql_lower = metrics.sql.lower()
        
        # 检查常见的性能问题
        if 'select *' in sql_lower:
            suggestions.append("避免使用SELECT *，明确指定需要的列")
        
        if 'order by' in sql_lower and 'limit' not in sql_lower:
            suggestions.append("ORDER BY查询建议添加LIMIT限制结果集大小")
        
        if sql_lower.count('join') > 3:
            suggestions.append("考虑减少JOIN操作或优化JOIN条件")
        
        if 'where' not in sql_lower and ('select' in sql_lower or 'update' in sql_lower or 'delete' in sql_lower):
            suggestions.append("考虑添加WHERE条件限制查询范围")
        
        if 'group by' in sql_lower and 'having' in sql_lower:
            suggestions.append("考虑将HAVING条件移到WHERE中以提前过滤")
        
        # 检查是否需要索引
        if metrics.execution_time > 2.0 and 'where' in sql_lower:
            suggestions.append("考虑为WHERE条件中的列添加索引")
        
        return suggestions
    
    async def _performance_monitoring_task(self):
        """
        性能监控后台任务
        """
        while True:
            try:
                await asyncio.sleep(60)  # 每分钟执行一次
                
                # 收集连接池指标
                await self._collect_connection_pool_metrics()
                
                # 分析查询性能趋势
                await self._analyze_performance_trends()
                
                # 清理过期指标
                await self._cleanup_old_metrics()
                
            except Exception as e:
                logger.error(f"性能监控任务错误: {e}")
    
    async def _collect_connection_pool_metrics(self):
        """
        收集连接池性能指标
        """
        for db_name in postgres_manager.engines.keys():
            try:
                pool_info = await postgres_manager.get_connection_info(db_name)
                
                if pool_info:
                    metrics = ConnectionPoolMetrics(
                        database=db_name,
                        pool_size=pool_info.get('pool_size', 0),
                        checked_out=pool_info.get('checked_out', 0),
                        checked_in=pool_info.get('checked_in', 0),
                        overflow=pool_info.get('overflow', 0),
                        invalid=pool_info.get('invalid', 0),
                        total_connections=pool_info.get('checked_out', 0) + pool_info.get('checked_in', 0),
                        utilization_rate=pool_info.get('checked_out', 0) / max(pool_info.get('pool_size', 1), 1)
                    )
                    
                    self.connection_stats[db_name].append(metrics)
                    
                    # 检查连接池使用率
                    if metrics.utilization_rate > 0.8:
                        logger.warning(f"连接池使用率过高: {db_name} - {metrics.utilization_rate:.2%}")
                    
            except Exception as e:
                logger.error(f"收集连接池指标失败 {db_name}: {e}")
    
    async def _analyze_performance_trends(self):
        """
        分析性能趋势
        """
        try:
            # 分析最近的查询性能
            recent_metrics = [m for m in self.query_metrics if m.timestamp > datetime.now() - timedelta(minutes=10)]
            
            if len(recent_metrics) < 10:
                return
            
            # 计算平均执行时间
            avg_execution_time = statistics.mean([m.execution_time for m in recent_metrics])
            
            # 检查性能退化
            if avg_execution_time > 2.0:
                logger.warning(f"检测到性能退化，平均查询时间: {avg_execution_time:.3f}s")
                
                # 生成性能报告
                await self._generate_performance_report(recent_metrics)
            
        except Exception as e:
            logger.error(f"性能趋势分析失败: {e}")
    
    async def _cleanup_old_metrics(self):
        """
        清理过期的性能指标
        """
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        # 清理查询指标
        self.query_metrics = deque(
            [m for m in self.query_metrics if m.timestamp > cutoff_time],
            maxlen=10000
        )
        
        # 清理连接池统计
        for db_name in list(self.connection_stats.keys()):
            self.connection_stats[db_name] = [
                m for m in self.connection_stats[db_name][-100:]  # 保留最近100条记录
            ]
    
    async def _generate_performance_report(self, metrics: List[QueryMetrics]):
        """
        生成性能报告
        
        Args:
            metrics: 查询指标列表
        """
        try:
            # 按数据库分组
            db_metrics = defaultdict(list)
            for m in metrics:
                db_metrics[m.database].append(m)
            
            report = {
                'timestamp': datetime.now().isoformat(),
                'total_queries': len(metrics),
                'databases': {}
            }
            
            for db_name, db_queries in db_metrics.items():
                execution_times = [m.execution_time for m in db_queries]
                
                report['databases'][db_name] = {
                    'query_count': len(db_queries),
                    'avg_execution_time': statistics.mean(execution_times),
                    'max_execution_time': max(execution_times),
                    'min_execution_time': min(execution_times),
                    'slow_queries': len([m for m in db_queries if m.execution_time > self.slow_query_threshold])
                }
            
            # 缓存报告到Redis
            if redis_manager._is_connected:
                await redis_manager.set_cache(
                    f"performance_report:{int(time.time())}",
                    report,
                    ttl=86400,  # 24小时
                    db=redis_manager.metrics_db
                )
            
            logger.info(f"性能报告已生成: {report['total_queries']}个查询")
            
        except Exception as e:
            logger.error(f"生成性能报告失败: {e}")
    
    # ==================== 公共API ====================
    
    async def get_query_statistics(self, database: str = None, hours: int = 24) -> Dict[str, Any]:
        """
        获取查询统计信息
        
        Args:
            database: 数据库名称
            hours: 统计时间范围（小时）
            
        Returns:
            Dict[str, Any]: 查询统计信息
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        # 过滤指标
        filtered_metrics = [
            m for m in self.query_metrics 
            if m.timestamp > cutoff_time and (not database or m.database == database)
        ]
        
        if not filtered_metrics:
            return {'message': '没有找到查询数据'}
        
        execution_times = [m.execution_time for m in filtered_metrics]
        
        return {
            'total_queries': len(filtered_metrics),
            'avg_execution_time': statistics.mean(execution_times),
            'max_execution_time': max(execution_times),
            'min_execution_time': min(execution_times),
            'median_execution_time': statistics.median(execution_times),
            'slow_queries': len([m for m in filtered_metrics if m.execution_time > self.slow_query_threshold]),
            'databases': list(set(m.database for m in filtered_metrics)),
            'time_range_hours': hours
        }
    
    async def get_slow_queries(self, database: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取慢查询列表
        
        Args:
            database: 数据库名称
            limit: 返回数量限制
            
        Returns:
            List[Dict[str, Any]]: 慢查询列表
        """
        slow_queries = [
            m for m in self.query_metrics 
            if m.execution_time > self.slow_query_threshold and (not database or m.database == database)
        ]
        
        # 按执行时间排序
        slow_queries.sort(key=lambda x: x.execution_time, reverse=True)
        
        return [
            {
                'sql': query.sql[:200] + ('...' if len(query.sql) > 200 else ''),
                'execution_time': query.execution_time,
                'database': query.database,
                'timestamp': query.timestamp.isoformat(),
                'rows_affected': query.rows_affected
            }
            for query in slow_queries[:limit]
        ]
    
    async def get_connection_pool_status(self) -> Dict[str, Any]:
        """
        获取连接池状态
        
        Returns:
            Dict[str, Any]: 连接池状态信息
        """
        status = {}
        
        for db_name in postgres_manager.engines.keys():
            pool_info = await postgres_manager.get_connection_info(db_name)
            
            if pool_info:
                utilization_rate = pool_info.get('checked_out', 0) / max(pool_info.get('pool_size', 1), 1)
                
                status[db_name] = {
                    'pool_size': pool_info.get('pool_size', 0),
                    'checked_out': pool_info.get('checked_out', 0),
                    'checked_in': pool_info.get('checked_in', 0),
                    'overflow': pool_info.get('overflow', 0),
                    'invalid': pool_info.get('invalid', 0),
                    'utilization_rate': f"{utilization_rate:.2%}",
                    'status': 'healthy' if utilization_rate < 0.8 else 'warning' if utilization_rate < 0.95 else 'critical'
                }
        
        return status
    
    async def optimize_connection_pools(self) -> Dict[str, Any]:
        """
        优化连接池配置
        
        Returns:
            Dict[str, Any]: 优化结果
        """
        results = {}
        
        for db_name in postgres_manager.engines.keys():
            try:
                # 获取连接池统计
                recent_stats = self.connection_stats.get(db_name, [])[-10:]  # 最近10次统计
                
                if not recent_stats:
                    continue
                
                # 计算平均使用率
                avg_utilization = statistics.mean([s.utilization_rate for s in recent_stats])
                
                suggestions = []
                
                if avg_utilization > 0.9:
                    suggestions.append("建议增加连接池大小")
                elif avg_utilization < 0.3:
                    suggestions.append("可以考虑减少连接池大小以节省资源")
                
                if any(s.overflow > 0 for s in recent_stats):
                    suggestions.append("检测到连接池溢出，建议增加max_overflow")
                
                results[db_name] = {
                    'avg_utilization': f"{avg_utilization:.2%}",
                    'suggestions': suggestions
                }
                
            except Exception as e:
                results[db_name] = {'error': str(e)}
        
        return results

# 全局性能优化器实例
performance_optimizer = PerformanceOptimizer()