FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv==0.9.5

COPY pyproject.toml uv.lock ./
COPY app/ ./app/
RUN uv sync --frozen --no-dev --no-editable


FROM python:3.11-slim AS runtime

LABEL version="0.1.0" \
      description="Askora 私人自用学习 App 后端"

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --system --uid 1001 appuser

COPY --from=builder /build/.venv /app/.venv
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini ./

RUN mkdir -p /app/data/documents \
    && chown -R appuser:appuser /app

USER appuser

ENV APP_ENV=production \
    PRIVATE_APP=true \
    DEBUG=false \
    HOST=0.0.0.0 \
    PORT=8000 \
    DATABASE_POOL_SIZE=10 \
    DATABASE_MAX_OVERFLOW=10 \
    LOG_LEVEL=INFO \
    LOG_FORMAT=json \
    ENABLE_ORCHESTRATOR_DEBUG_API=false \
    PATH="/app/.venv/bin:$PATH"

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl --fail --silent http://127.0.0.1:8000/ready || exit 1

EXPOSE 8000

# 单进程是当前实现的安全约束：对话串行锁和本地降级状态位于进程内。
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1"]
