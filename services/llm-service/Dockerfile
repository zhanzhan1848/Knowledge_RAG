# LLM Service Dockerfile
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

# 安装uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# 复制依赖文件
COPY pyproject.toml uv.lock README.md ./

# 安装Python依赖
RUN uv sync --frozen --no-dev --prerelease=allow

# 复制共享库
COPY shared/ ./shared/

# 复制LLM服务代码
COPY services/llm-service/ ./services/llm-service/

# 创建模型缓存目录
RUN mkdir -p /app/models /app/data/cache

# 创建非root用户
RUN addgroup --system appuser && adduser --system --group appuser
RUN chown -R appuser:appuser /app
USER appuser

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8004/health || exit 1

# 暴露端口
EXPOSE 8004

# 启动命令
CMD ["uvicorn", "services.llm-service.main:app", "--host", "0.0.0.0", "--port", "8004", "--workers", "2"]