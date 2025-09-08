# Document Service Dockerfile
# 基于Python 3.10的官方镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    UV_CACHE_DIR=/tmp/uv-cache

# 安装系统依赖和uv（文档处理需要额外的系统库）
RUN DEBIAN_FRONTEND=noninteractive apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    poppler-utils \
    tesseract-ocr \
    tesseract-ocr-chi-sim \
    tesseract-ocr-eng \
    libreoffice \
    pandoc \
    && curl -LsSf https://astral.sh/uv/install.sh | sh \
    && rm -rf /var/lib/apt/lists/*

# 添加uv到PATH
ENV PATH="/root/.cargo/bin:$PATH"

# 复制项目配置文件
COPY pyproject.toml uv.lock ./

# 安装Python依赖
RUN uv sync --frozen --no-dev --prerelease=allow

# 复制共享库
COPY shared/ ./shared/

# 复制文档服务代码
COPY services/document-service/ ./services/document-service/

# 创建上传目录
RUN mkdir -p /app/data/uploads /app/data/temp /app/data/processed

# 创建非root用户
RUN addgroup --system appuser && adduser --system --group appuser
RUN chown -R appuser:appuser /app
USER appuser

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8002/health || exit 1

# 暴露端口
EXPOSE 8002

# 启动命令
CMD ["uvicorn", "services.document-service.main:app", "--host", "0.0.0.0", "--port", "8002", "--workers", "2"]