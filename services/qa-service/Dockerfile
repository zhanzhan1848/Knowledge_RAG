# QA Service Dockerfile
# 基于Python 3.11的官方镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 安装系统依赖
RUN DEBIAN_FRONTEND=noninteractive apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy uv binary from the official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# 复制依赖文件
COPY pyproject.toml uv.lock README.md ./

# 安装Python依赖
RUN uv sync --frozen --no-dev

# 复制共享库
COPY shared/ ./shared/

# 复制QA服务代码
COPY services/qa-service/ ./services/qa-service/

# 创建非root用户和设置HOME目录
RUN addgroup --system appuser && adduser --system --group appuser --home /home/appuser
RUN mkdir -p /home/appuser/.cache/uv && chown -R appuser:appuser /app /home/appuser
USER appuser

# 设置用户环境变量
ENV HOME=/home/appuser \
    UV_CACHE_DIR=/home/appuser/.cache/uv

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8005/health || exit 1

# 暴露端口
EXPOSE 8005

# 启动命令
CMD ["uv", "run", "uvicorn", "services.qa-service.main:app", "--host", "0.0.0.0", "--port", "8004", "--workers", "2"]