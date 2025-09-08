# API Gateway Service Dockerfile
# 基于Python 3.10的官方镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    UV_CACHE_DIR=/tmp/uv-cache

# 安装系统依赖
RUN DEBIAN_FRONTEND=noninteractive apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# 复制项目配置文件
COPY pyproject.toml uv.lock README.md ./

# 安装Python依赖
RUN uv sync --frozen --no-dev --prerelease=allow

# 复制共享库
COPY shared/ ./shared/

# 复制API网关服务代码
COPY services/api-gateway/ ./services/api-gateway/

# 创建非root用户
RUN addgroup --system appuser && adduser --system --group appuser
RUN chown -R appuser:appuser /app
USER appuser

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "services.api-gateway.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]