#!/usr/bin/env python3
"""
Knowledge RAG 系统环境变量验证脚本

作者: Knowledge RAG Team
描述: 验证环境变量配置是否正确，检查必要的服务连接
"""

import asyncio
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

import aiohttp
import asyncpg
import redis.asyncio as redis


# 颜色定义
class Colors:
    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[1;33m"
    BLUE = "\033[0;34m"
    PURPLE = "\033[0;35m"
    CYAN = "\033[0;36m"
    WHITE = "\033[1;37m"
    NC = "\033[0m"  # No Color


def log_info(message: str) -> None:
    """输出信息日志"""
    print(f"{Colors.BLUE}[INFO]{Colors.NC} {message}")


def log_success(message: str) -> None:
    """输出成功日志"""
    print(f"{Colors.GREEN}[SUCCESS]{Colors.NC} {message}")


def log_warning(message: str) -> None:
    """输出警告日志"""
    print(f"{Colors.YELLOW}[WARNING]{Colors.NC} {message}")


def log_error(message: str) -> None:
    """输出错误日志"""
    print(f"{Colors.RED}[ERROR]{Colors.NC} {message}")


def load_env_file(env_path: str = ".env") -> Dict[str, str]:
    """加载环境变量文件"""
    env_vars = {}

    if not os.path.exists(env_path):
        log_error(f"环境变量文件 {env_path} 不存在")
        return env_vars

    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()

                # 跳过空行和注释
                if not line or line.startswith("#"):
                    continue

                # 解析环境变量
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    env_vars[key] = value
                else:
                    log_warning(f"第 {line_num} 行格式不正确: {line}")

    except Exception as e:
        log_error(f"读取环境变量文件失败: {e}")

    return env_vars


def validate_required_vars(env_vars: Dict[str, str]) -> List[str]:
    """验证必需的环境变量"""
    required_vars = [
        "DATABASE_URL",
        "REDIS_URL",
        "OPENAI_API_KEY",
        "JWT_SECRET_KEY",
        "NEO4J_URI",
        "NEO4J_USER",
        "NEO4J_PASSWORD",
    ]

    missing_vars = []

    for var in required_vars:
        if (
            var not in env_vars
            or not env_vars[var]
            or env_vars[var].startswith("your_")
        ):
            missing_vars.append(var)

    return missing_vars


def validate_url_format(url: str, scheme: Optional[str] = None) -> bool:
    """验证URL格式"""
    try:
        parsed = urlparse(url)
        if scheme and parsed.scheme != scheme:
            return False
        return bool(parsed.netloc)
    except Exception:
        return False


def validate_database_url(url: str) -> Tuple[bool, str]:
    """验证数据库URL格式"""
    if not url.startswith("postgresql"):
        return False, "数据库URL必须以 postgresql 开头"

    try:
        parsed = urlparse(url)
        if not parsed.hostname or not parsed.port or not parsed.username:
            return False, "数据库URL缺少必要信息（主机、端口、用户名）"
        return True, "格式正确"
    except Exception as e:
        return False, f"URL解析失败: {e}"


def validate_port_range(port_str: str) -> bool:
    """验证端口范围"""
    try:
        port = int(port_str)
        return 1 <= port <= 65535
    except ValueError:
        return False


def validate_file_paths(env_vars: Dict[str, str]) -> List[str]:
    """验证文件路径配置"""
    issues = []

    path_vars = [
        "UPLOAD_DIR",
        "TEMP_DIR",
        "PROCESSED_DIR",
        "LOCAL_MODEL_PATH",
        "HUGGINGFACE_CACHE_DIR",
        "GRAPHRAG_STORAGE_BASE_DIR",
    ]

    for var in path_vars:
        if var in env_vars:
            path = env_vars[var]
            if path and not os.path.isabs(path):
                # 相对路径，检查是否可以创建
                try:
                    Path(path).mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    issues.append(f"{var}: 无法创建目录 {path} - {e}")

    return issues


async def test_database_connection(database_url: str) -> Tuple[bool, str]:
    """测试数据库连接"""
    try:
        conn = await asyncpg.connect(database_url)
        await conn.execute("SELECT 1")
        await conn.close()
        return True, "连接成功"
    except Exception as e:
        return False, f"连接失败: {e}"


async def test_redis_connection(redis_url: str) -> Tuple[bool, str]:
    """测试Redis连接"""
    try:
        r = redis.from_url(redis_url)
        await r.ping()
        await r.close()
        return True, "连接成功"
    except Exception as e:
        return False, f"连接失败: {e}"


async def test_http_service(url: str, timeout: int = 5) -> Tuple[bool, str]:
    """测试HTTP服务连接"""
    try:
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=timeout)
        ) as session:
            async with session.get(url) as response:
                return True, f"响应状态: {response.status}"
    except Exception as e:
        return False, f"连接失败: {e}"


async def run_connectivity_tests(env_vars: Dict[str, str]) -> None:
    """运行连接性测试"""
    log_info("开始连接性测试...")

    tests = []

    # 数据库连接测试
    if "DATABASE_URL" in env_vars:
        tests.append(("PostgreSQL", test_database_connection(env_vars["DATABASE_URL"])))

    # Redis连接测试
    if "REDIS_URL" in env_vars:
        tests.append(("Redis", test_redis_connection(env_vars["REDIS_URL"])))

    # HTTP服务测试
    http_services = {
        "Elasticsearch": env_vars.get("ELASTICSEARCH_URL"),
        "Weaviate": env_vars.get("WEAVIATE_URL"),
        "Neo4j HTTP": env_vars.get("NEO4J_URI", "")
        .replace("bolt://", "http://")
        .replace(":7687", ":7474"),
    }

    for service_name, url in http_services.items():
        if url and validate_url_format(url, "http"):
            tests.append((service_name, test_http_service(url)))

    # 执行测试
    results = await asyncio.gather(*[test for _, test in tests], return_exceptions=True)

    # 输出结果
    for i, (service_name, _) in enumerate(tests):
        if isinstance(results[i], Exception):
            log_error(f"{service_name}: 测试异常 - {results[i]}")
        else:
            success, message = results[i]
            if success:
                log_success(f"{service_name}: {message}")
            else:
                log_error(f"{service_name}: {message}")


def validate_api_keys(env_vars: Dict[str, str]) -> List[str]:
    """验证API密钥格式"""
    issues = []

    # OpenAI API Key 格式验证
    openai_key = env_vars.get("OPENAI_API_KEY", "")
    if openai_key and not openai_key.startswith("sk-"):
        issues.append("OPENAI_API_KEY 格式不正确，应该以 'sk-' 开头")

    # JWT Secret Key 长度验证
    jwt_secret = env_vars.get("JWT_SECRET_KEY", "")
    if jwt_secret and len(jwt_secret) < 32:
        issues.append("JWT_SECRET_KEY 长度不足，建议至少32个字符")

    return issues


def generate_report(env_vars: Dict[str, str]) -> None:
    """生成验证报告"""
    print(f"\n{Colors.CYAN}{'='*60}{Colors.NC}")
    print(f"{Colors.CYAN}环境变量验证报告{Colors.NC}")
    print(f"{Colors.CYAN}{'='*60}{Colors.NC}\n")

    # 基本信息
    print(f"{Colors.WHITE}基本配置:{Colors.NC}")
    print(f"  环境: {env_vars.get('ENVIRONMENT', 'unknown')}")
    print(f"  调试模式: {env_vars.get('DEBUG', 'false')}")
    print(f"  日志级别: {env_vars.get('LOG_LEVEL', 'INFO')}")
    print()

    # 服务端口
    print(f"{Colors.WHITE}微服务端口配置:{Colors.NC}")
    port_vars = [
        "API_GATEWAY_PORT",
        "AUTH_SERVICE_PORT",
        "DOCUMENT_SERVICE_PORT",
        "VECTOR_SERVICE_PORT",
        "LLM_SERVICE_PORT",
        "QA_SERVICE_PORT",
        "KNOWLEDGE_GRAPH_SERVICE_PORT",
        "NOTIFICATION_SERVICE_PORT",
        "GRAPH_SERVICE_PORT",
    ]

    for var in port_vars:
        port = env_vars.get(var, "not set")
        service_name = var.replace("_PORT", "").replace("_", "-").lower()
        print(f"  {service_name}: {port}")
    print()

    # 数据库配置
    print(f"{Colors.WHITE}数据库配置:{Colors.NC}")
    db_vars = ["DATABASE_URL", "REDIS_URL", "ELASTICSEARCH_URL", "NEO4J_URI"]
    for var in db_vars:
        if var in env_vars:
            url = env_vars[var]
            parsed = urlparse(url)
            masked_url = (
                f"{parsed.scheme}://{parsed.hostname}:{parsed.port}{parsed.path}"
            )
            print(f"  {var}: {masked_url}")
    print()


async def main() -> None:
    """主函数"""
    print(f"{Colors.PURPLE}🔍 Knowledge RAG 系统环境验证{Colors.NC}")
    print(f"{Colors.PURPLE}{'='*40}{Colors.NC}\n")

    # 加载环境变量
    log_info("加载环境变量文件...")
    env_vars = load_env_file()

    if not env_vars:
        log_error("无法加载环境变量，请检查 .env 文件")
        sys.exit(1)

    log_success(f"成功加载 {len(env_vars)} 个环境变量")

    # 验证必需变量
    log_info("验证必需的环境变量...")
    missing_vars = validate_required_vars(env_vars)

    if missing_vars:
        log_error("缺少必需的环境变量:")
        for var in missing_vars:
            print(f"  - {var}")
    else:
        log_success("所有必需的环境变量都已设置")

    # 验证URL格式
    log_info("验证URL格式...")
    url_issues = []

    # 数据库URL验证
    if "DATABASE_URL" in env_vars:
        valid, msg = validate_database_url(env_vars["DATABASE_URL"])
        if not valid:
            url_issues.append(f"DATABASE_URL: {msg}")

    # 其他URL验证
    url_vars = ["REDIS_URL", "ELASTICSEARCH_URL", "WEAVIATE_URL"]
    for var in url_vars:
        if var in env_vars and env_vars[var]:
            if not validate_url_format(env_vars[var]):
                url_issues.append(f"{var}: URL格式不正确")

    if url_issues:
        log_error("URL格式问题:")
        for issue in url_issues:
            print(f"  - {issue}")
    else:
        log_success("所有URL格式正确")

    # 验证API密钥
    log_info("验证API密钥格式...")
    api_issues = validate_api_keys(env_vars)

    if api_issues:
        log_warning("API密钥格式问题:")
        for issue in api_issues:
            print(f"  - {issue}")
    else:
        log_success("API密钥格式正确")

    # 验证文件路径
    log_info("验证文件路径配置...")
    path_issues = validate_file_paths(env_vars)

    if path_issues:
        log_warning("文件路径问题:")
        for issue in path_issues:
            print(f"  - {issue}")
    else:
        log_success("文件路径配置正确")

    # 连接性测试
    await run_connectivity_tests(env_vars)

    # 生成报告
    generate_report(env_vars)

    # 总结
    total_issues = (
        len(missing_vars) + len(url_issues) + len(api_issues) + len(path_issues)
    )

    if total_issues == 0:
        log_success("✅ 环境配置验证通过！")
        sys.exit(0)
    else:
        log_warning(f"⚠️  发现 {total_issues} 个配置问题，请检查并修复")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log_info("验证被用户中断")
        sys.exit(1)
    except Exception as e:
        log_error(f"验证过程中发生错误: {e}")
        sys.exit(1)
