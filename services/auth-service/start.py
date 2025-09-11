#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
认证服务启动脚本

负责初始化数据库、创建默认数据并启动认证服务。

作者: Knowledge RAG Team
创建时间: 2024
"""

import uvicorn
import asyncio
from database import init_database
from config import get_config


def setup_service():
    """
    设置认证服务
    
    初始化数据库和默认数据。
    """
    print("正在初始化认证服务...")
    
    # 初始化数据库
    print("初始化数据库...")
    init_database()
    print("数据库初始化完成")
    
    print("认证服务设置完成")


def start_server():
    """
    启动认证服务器
    """
    config = get_config()
    
    print(f"启动认证服务器...")
    print(f"服务地址: http://0.0.0.0:{config.app_port}")
    print(f"API文档: http://0.0.0.0:{config.app_port}/docs")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=config.app_port,
        reload=config.app_debug,
        log_level="info" if not config.app_debug else "debug"
    )


if __name__ == "__main__":
    # 设置服务
    setup_service()
    
    # 启动服务器
    start_server()