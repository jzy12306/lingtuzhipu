# 使用官方Python镜像作为基础镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 设置Python环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制requirements.txt文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# 复制项目代码
COPY . .

# 创建日志目录
RUN mkdir -p /app/logs

# 设置日志目录权限
RUN chmod 777 /app/logs

# 暴露应用端口
EXPOSE 8000

# 设置环境变量默认值
ENV ENVIRONMENT=production \
    DEBUG=False \
    DB_URL="sqlite:///./app.db" \
    SECRET_KEY="your-secret-key-change-in-production" \
    CORS_ORIGINS="http://localhost:3000,http://localhost:8080" \
    RATE_LIMIT_ENABLED=True \
    RATE_LIMIT_PER_MINUTE=60 \
    RATE_LIMIT_PER_HOUR=1000

# 启动应用
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]