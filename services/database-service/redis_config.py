# -*- coding: utf-8 -*-
"""
Redis缓存和会话存储配置管理模块

提供Redis连接管理、缓存操作、会话存储、
消息队列和性能监控功能。

Author: Knowledge RAG System
Date: 2025-01-16
"""

import os
import json
import asyncio
import logging
from typing import Optional, Dict, Any, List, Union
from contextlib import asynccontextmanager
import redis.asyncio as redis
from redis.asyncio import ConnectionPool
from redis.exceptions import ConnectionError, TimeoutError
import pickle
from datetime import datetime, timedelta

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RedisConfig:
    """
    Redis配置类
    
    管理Redis连接参数、连接池配置和性能优化设置。
    """
    
    def __init__(self):
        """初始化Redis配置"""
        self.host = os.getenv('REDIS_HOST', 'localhost')
        self.port = int(os.getenv('REDIS_PORT', 6379))
        self.password = os.getenv('REDIS_PASSWORD', None)
        self.db = int(os.getenv('REDIS_DB', 0))
        
        # 连接池配置
        self.max_connections = int(os.getenv('REDIS_MAX_CONNECTIONS', 50))
        self.retry_on_timeout = os.getenv('REDIS_RETRY_ON_TIMEOUT', 'true').lower() == 'true'
        self.socket_timeout = int(os.getenv('REDIS_SOCKET_TIMEOUT', 5))
        self.socket_connect_timeout = int(os.getenv('REDIS_SOCKET_CONNECT_TIMEOUT', 5))
        
        # 性能配置
        self.decode_responses = True
        self.encoding = 'utf-8'
        
        # 缓存配置
        self.default_ttl = int(os.getenv('REDIS_DEFAULT_TTL', 3600))  # 1小时
        self.session_ttl = int(os.getenv('REDIS_SESSION_TTL', 86400))  # 24小时
        
    def get_connection_kwargs(self) -> Dict[str, Any]:
        """
        获取Redis连接参数
        
        Returns:
            Dict[str, Any]: 连接参数
        """
        kwargs = {
            'host': self.host,
            'port': self.port,
            'db': self.db,
            'decode_responses': self.decode_responses,
            'encoding': self.encoding,
            'socket_timeout': self.socket_timeout,
            'socket_connect_timeout': self.socket_connect_timeout,
            'retry_on_timeout': self.retry_on_timeout
        }
        
        if self.password:
            kwargs['password'] = self.password
            
        return kwargs

class RedisManager:
    """
    Redis管理器
    
    提供Redis连接管理、缓存操作、会话管理和监控功能。
    """
    
    def __init__(self, config: RedisConfig):
        """初始化Redis管理器"""
        self.config = config
        self.connection_pool = None
        self.redis_client = None
        self._is_connected = False
        
        # 数据库分配
        self.cache_db = 0      # 缓存数据库
        self.session_db = 1    # 会话数据库
        self.queue_db = 2      # 消息队列数据库
        self.metrics_db = 3    # 监控指标数据库
        
    async def initialize(self):
        """
        初始化Redis连接
        """
        try:
            # 创建连接池
            self.connection_pool = ConnectionPool(
                max_connections=self.config.max_connections,
                **self.config.get_connection_kwargs()
            )
            
            # 创建Redis客户端
            self.redis_client = redis.Redis(connection_pool=self.connection_pool)
            
            # 验证连接
            await self._verify_connectivity()
            self._is_connected = True
            
            logger.info("Redis管理器初始化完成")
            
        except Exception as e:
            logger.error(f"Redis初始化失败: {e}")
            raise
    
    async def _verify_connectivity(self):
        """
        验证Redis连接
        """
        try:
            pong = await self.redis_client.ping()
            if not pong:
                raise Exception("Redis连接验证失败")
        except Exception as e:
            logger.error(f"Redis连接验证失败: {e}")
            raise
    
    def get_client(self, db: int = None) -> redis.Redis:
        """
        获取Redis客户端
        
        Args:
            db: 数据库编号
            
        Returns:
            redis.Redis: Redis客户端
        """
        if not self._is_connected:
            raise Exception("Redis未连接")
            
        if db is not None:
            # 创建指定数据库的客户端
            kwargs = self.config.get_connection_kwargs()
            kwargs['db'] = db
            return redis.Redis(**kwargs)
        
        return self.redis_client
    
    # ==================== 缓存操作 ====================
    
    async def set_cache(self, key: str, value: Any, ttl: Optional[int] = None, db: int = None) -> bool:
        """
        设置缓存
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒）
            db: 数据库编号
            
        Returns:
            bool: 设置是否成功
        """
        client = self.get_client(db or self.cache_db)
        ttl = ttl or self.config.default_ttl
        
        try:
            # 序列化值
            if isinstance(value, (dict, list)):
                serialized_value = json.dumps(value, ensure_ascii=False)
            elif isinstance(value, (int, float, str, bool)):
                serialized_value = str(value)
            else:
                serialized_value = pickle.dumps(value)
            
            return await client.setex(key, ttl, serialized_value)
        except Exception as e:
            logger.error(f"设置缓存失败 {key}: {e}")
            return False
    
    async def get_cache(self, key: str, default: Any = None, db: int = None) -> Any:
        """
        获取缓存
        
        Args:
            key: 缓存键
            default: 默认值
            db: 数据库编号
            
        Returns:
            Any: 缓存值
        """
        client = self.get_client(db or self.cache_db)
        
        try:
            value = await client.get(key)
            if value is None:
                return default
            
            # 尝试反序列化
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                try:
                    return pickle.loads(value)
                except (pickle.PickleError, TypeError):
                    return value
                    
        except Exception as e:
            logger.error(f"获取缓存失败 {key}: {e}")
            return default
    
    async def delete_cache(self, key: str, db: int = None) -> bool:
        """
        删除缓存
        
        Args:
            key: 缓存键
            db: 数据库编号
            
        Returns:
            bool: 删除是否成功
        """
        client = self.get_client(db or self.cache_db)
        
        try:
            return bool(await client.delete(key))
        except Exception as e:
            logger.error(f"删除缓存失败 {key}: {e}")
            return False
    
    async def exists_cache(self, key: str, db: int = None) -> bool:
        """
        检查缓存是否存在
        
        Args:
            key: 缓存键
            db: 数据库编号
            
        Returns:
            bool: 是否存在
        """
        client = self.get_client(db or self.cache_db)
        
        try:
            return bool(await client.exists(key))
        except Exception as e:
            logger.error(f"检查缓存存在性失败 {key}: {e}")
            return False
    
    # ==================== 会话管理 ====================
    
    async def set_session(self, session_id: str, session_data: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """
        设置会话数据
        
        Args:
            session_id: 会话ID
            session_data: 会话数据
            ttl: 过期时间（秒）
            
        Returns:
            bool: 设置是否成功
        """
        key = f"session:{session_id}"
        ttl = ttl or self.config.session_ttl
        return await self.set_cache(key, session_data, ttl, self.session_db)
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        获取会话数据
        
        Args:
            session_id: 会话ID
            
        Returns:
            Optional[Dict[str, Any]]: 会话数据
        """
        key = f"session:{session_id}"
        return await self.get_cache(key, {}, self.session_db)
    
    async def delete_session(self, session_id: str) -> bool:
        """
        删除会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            bool: 删除是否成功
        """
        key = f"session:{session_id}"
        return await self.delete_cache(key, self.session_db)
    
    # ==================== 消息队列 ====================
    
    async def push_queue(self, queue_name: str, message: Any) -> bool:
        """
        推送消息到队列
        
        Args:
            queue_name: 队列名称
            message: 消息内容
            
        Returns:
            bool: 推送是否成功
        """
        client = self.get_client(self.queue_db)
        
        try:
            serialized_message = json.dumps(message, ensure_ascii=False)
            return bool(await client.lpush(queue_name, serialized_message))
        except Exception as e:
            logger.error(f"推送消息到队列失败 {queue_name}: {e}")
            return False
    
    async def pop_queue(self, queue_name: str, timeout: int = 0) -> Optional[Any]:
        """
        从队列弹出消息
        
        Args:
            queue_name: 队列名称
            timeout: 超时时间（秒），0表示阻塞
            
        Returns:
            Optional[Any]: 消息内容
        """
        client = self.get_client(self.queue_db)
        
        try:
            if timeout > 0:
                result = await client.brpop(queue_name, timeout)
            else:
                result = await client.rpop(queue_name)
            
            if result:
                if isinstance(result, tuple):
                    _, message = result
                else:
                    message = result
                return json.loads(message)
            return None
        except Exception as e:
            logger.error(f"从队列弹出消息失败 {queue_name}: {e}")
            return None
    
    # ==================== 监控和统计 ====================
    
    async def health_check(self) -> bool:
        """
        Redis健康检查
        
        Returns:
            bool: 健康状态
        """
        try:
            pong = await self.redis_client.ping()
            return pong
        except Exception as e:
            logger.error(f"Redis健康检查失败: {e}")
            return False
    
    async def get_info(self) -> Dict[str, Any]:
        """
        获取Redis信息
        
        Returns:
            Dict[str, Any]: Redis信息
        """
        try:
            info = await self.redis_client.info()
            return {
                'redis_version': info.get('redis_version'),
                'connected_clients': info.get('connected_clients'),
                'used_memory': info.get('used_memory'),
                'used_memory_human': info.get('used_memory_human'),
                'total_commands_processed': info.get('total_commands_processed'),
                'keyspace_hits': info.get('keyspace_hits'),
                'keyspace_misses': info.get('keyspace_misses')
            }
        except Exception as e:
            logger.error(f"获取Redis信息失败: {e}")
            return {}
    
    async def get_memory_usage(self) -> Dict[str, Any]:
        """
        获取内存使用情况
        
        Returns:
            Dict[str, Any]: 内存使用信息
        """
        try:
            info = await self.redis_client.info('memory')
            return {
                'used_memory': info.get('used_memory', 0),
                'used_memory_human': info.get('used_memory_human', '0B'),
                'used_memory_rss': info.get('used_memory_rss', 0),
                'used_memory_peak': info.get('used_memory_peak', 0),
                'used_memory_peak_human': info.get('used_memory_peak_human', '0B'),
                'mem_fragmentation_ratio': info.get('mem_fragmentation_ratio', 0)
            }
        except Exception as e:
            logger.error(f"获取Redis内存使用情况失败: {e}")
            return {}
    
    async def close(self):
        """
        关闭Redis连接
        """
        if self.redis_client:
            await self.redis_client.close()
        if self.connection_pool:
            await self.connection_pool.disconnect()
        
        self._is_connected = False
        logger.info("Redis连接已关闭")

# 全局Redis管理器实例
redis_config = RedisConfig()
redis_manager = RedisManager(redis_config)

# 便捷函数
async def get_redis_client(db: int = None) -> redis.Redis:
    """
    获取Redis客户端
    
    Args:
        db: 数据库编号
        
    Returns:
        redis.Redis: Redis客户端
    """
    return redis_manager.get_client(db)

async def redis_health_check() -> bool:
    """
    Redis健康检查
    
    Returns:
        bool: 健康状态
    """
    return await redis_manager.health_check()

# 缓存装饰器
def cache_result(key_prefix: str, ttl: Optional[int] = None, db: int = None):
    """
    缓存结果装饰器
    
    Args:
        key_prefix: 缓存键前缀
        ttl: 过期时间（秒）
        db: 数据库编号
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = f"{key_prefix}:{hash(str(args) + str(kwargs))}"
            
            # 尝试从缓存获取
            cached_result = await redis_manager.get_cache(cache_key, db=db)
            if cached_result is not None:
                return cached_result
            
            # 执行函数并缓存结果
            result = await func(*args, **kwargs)
            await redis_manager.set_cache(cache_key, result, ttl, db)
            return result
        
        return wrapper
    return decorator