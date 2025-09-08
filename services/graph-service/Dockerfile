# GraphRAG服务Dockerfile
# 基于Python 3.10构建GraphRAG知识图谱服务

FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_CACHE_DIR=/tmp/uv-cache

# 安装系统依赖和uv
RUN DEBIAN_FRONTEND=noninteractive apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# 安装uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# 复制项目配置文件
COPY pyproject.toml uv.lock README.md ./

# 安装Python依赖
RUN uv sync --frozen --no-dev --prerelease=allow

# 复制共享库
COPY shared/ /app/shared/

# 复制应用代码
COPY services/graph-service/app/ /app/app/

# 创建必要的目录
RUN mkdir -p /app/data /app/logs /app/temp

# 创建非root用户
RUN addgroup --system appuser && adduser --system --group appuser
RUN chown -R appuser:appuser /app
USER appuser

# 设置权限
RUN chmod -R 755 /app

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]