#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据库连接和会话管理

该模块负责数据库连接的创建、会话管理和数据库初始化。
"""

import logging
from typing import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from sqlalchemy.engine import Engine

from .config import get_settings
from .models import Base

# 配置日志
logger = logging.getLogger(__name__)

# 全局变量
engine = None
SessionLocal = None


def get_database_url() -> str:
    """获取数据库连接URL
    
    Returns:
        str: 数据库连接URL
    """
    settings = get_settings()
    
    if settings.DATABASE_TYPE == "sqlite":
        return f"sqlite:///{settings.DATABASE_PATH}"
    elif settings.DATABASE_TYPE == "postgresql":
        return (
            f"postgresql://{settings.DATABASE_USER}:{settings.DATABASE_PASSWORD}"
            f"@{settings.DATABASE_HOST}:{settings.DATABASE_PORT}/{settings.DATABASE_NAME}"
        )
    elif settings.DATABASE_TYPE == "mysql":
        return (
            f"mysql+pymysql://{settings.DATABASE_USER}:{settings.DATABASE_PASSWORD}"
            f"@{settings.DATABASE_HOST}:{settings.DATABASE_PORT}/{settings.DATABASE_NAME}"
        )
    else:
        raise ValueError(f"不支持的数据库类型: {settings.DATABASE_TYPE}")


def create_database_engine() -> Engine:
    """创建数据库引擎
    
    Returns:
        Engine: SQLAlchemy数据库引擎
    """
    settings = get_settings()
    database_url = get_database_url()
    
    # 根据数据库类型设置不同的引擎参数
    engine_kwargs = {
        "echo": settings.DATABASE_ECHO,
        "pool_pre_ping": True,  # 连接前检查连接是否有效
    }
    
    if settings.DATABASE_TYPE == "sqlite":
        # SQLite特殊配置
        engine_kwargs.update({
            "poolclass": StaticPool,
            "connect_args": {
                "check_same_thread": False,
                "timeout": 20
            }
        })
    else:
        # PostgreSQL/MySQL配置
        engine_kwargs.update({
            "pool_size": settings.DATABASE_POOL_SIZE,
            "max_overflow": settings.DATABASE_MAX_OVERFLOW,
            "pool_timeout": settings.DATABASE_POOL_TIMEOUT,
            "pool_recycle": settings.DATABASE_POOL_RECYCLE,
        })
    
    engine = create_engine(database_url, **engine_kwargs)
    
    # 添加事件监听器
    if settings.DATABASE_TYPE == "sqlite":
        # 为SQLite启用外键约束
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA cache_size=1000")
            cursor.execute("PRAGMA temp_store=MEMORY")
            cursor.close()
    
    return engine


def init_database() -> None:
    """初始化数据库
    
    创建所有表和索引
    """
    global engine, SessionLocal
    
    try:
        # 创建数据库引擎
        engine = create_database_engine()
        
        # 创建会话工厂
        SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine
        )
        
        # 创建所有表
        logger.info("正在创建数据库表...")
        Base.metadata.create_all(bind=engine)
        logger.info("数据库表创建完成")
        
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        raise


def get_db() -> Generator[Session, None, None]:
    """获取数据库会话
    
    这是一个依赖注入函数，用于FastAPI的Depends
    
    Yields:
        Session: 数据库会话
    """
    if SessionLocal is None:
        raise RuntimeError("数据库未初始化，请先调用 init_database()")
    
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"数据库会话错误: {e}")
        db.rollback()
        raise
    finally:
        db.close()


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """获取数据库会话的上下文管理器
    
    用于在非FastAPI环境中使用数据库会话
    
    Yields:
        Session: 数据库会话
    """
    if SessionLocal is None:
        raise RuntimeError("数据库未初始化，请先调用 init_database()")
    
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        logger.error(f"数据库会话错误: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def close_database() -> None:
    """关闭数据库连接
    
    清理资源，关闭连接池
    """
    global engine, SessionLocal
    
    if engine:
        logger.info("正在关闭数据库连接...")
        engine.dispose()
        engine = None
        SessionLocal = None
        logger.info("数据库连接已关闭")


def check_database_connection() -> bool:
    """检查数据库连接是否正常
    
    Returns:
        bool: 连接是否正常
    """
    try:
        with get_db_session() as db:
            # 执行简单查询测试连接
            db.execute("SELECT 1")
            return True
    except Exception as e:
        logger.error(f"数据库连接检查失败: {e}")
        return False


def get_database_info() -> dict:
    """获取数据库信息
    
    Returns:
        dict: 数据库信息
    """
    if engine is None:
        return {"status": "未初始化"}
    
    try:
        with get_db_session() as db:
            # 获取数据库版本等信息
            result = db.execute("SELECT 1 as test")
            result.fetchone()
            
            return {
                "status": "已连接",
                "url": str(engine.url).replace(engine.url.password or "", "***"),
                "pool_size": getattr(engine.pool, 'size', None),
                "checked_out": getattr(engine.pool, 'checkedout', None),
                "overflow": getattr(engine.pool, 'overflow', None),
                "checked_in": getattr(engine.pool, 'checkedin', None)
            }
    except Exception as e:
        return {
            "status": "连接错误",
            "error": str(e)
        }


# 数据库操作辅助函数
class DatabaseManager:
    """数据库管理器
    
    提供常用的数据库操作方法
    """
    
    @staticmethod
    def create_tables() -> None:
        """创建所有表"""
        if engine is None:
            raise RuntimeError("数据库引擎未初始化")
        Base.metadata.create_all(bind=engine)
    
    @staticmethod
    def drop_tables() -> None:
        """删除所有表"""
        if engine is None:
            raise RuntimeError("数据库引擎未初始化")
        Base.metadata.drop_all(bind=engine)
    
    @staticmethod
    def recreate_tables() -> None:
        """重新创建所有表"""
        DatabaseManager.drop_tables()
        DatabaseManager.create_tables()
    
    @staticmethod
    def get_table_names() -> list:
        """获取所有表名
        
        Returns:
            list: 表名列表
        """
        if engine is None:
            raise RuntimeError("数据库引擎未初始化")
        
        with get_db_session() as db:
            if "sqlite" in str(engine.url):
                result = db.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            elif "postgresql" in str(engine.url):
                result = db.execute(
                    "SELECT tablename FROM pg_tables WHERE schemaname='public'"
                )
            elif "mysql" in str(engine.url):
                result = db.execute("SHOW TABLES")
            else:
                return []
            
            return [row[0] for row in result.fetchall()]
    
    @staticmethod
    def get_table_count(table_name: str) -> int:
        """获取表记录数
        
        Args:
            table_name: 表名
            
        Returns:
            int: 记录数
        """
        with get_db_session() as db:
            result = db.execute(f"SELECT COUNT(*) FROM {table_name}")
            return result.scalar()