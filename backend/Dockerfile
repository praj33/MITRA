FROM python:3.10-slim AS build

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install torch==2.0.1+cpu -r requirements.txt --index-url https://download.pytorch.org/whl/cpu --extra-index-url https://pypi.org/simple

# Clean up any accidental CUDA packages, compiler caches, and test files
RUN rm -rf /install/lib/python3.10/site-packages/nvidia* && \
    rm -rf /install/lib/python3.10/site-packages/triton* && \
    find /install -name '__pycache__' -type d -exec rm -rf {} + && \
    find /install -name 'tests' -type d -exec rm -rf {} +

FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends libgomp1 curl && \
    rm -rf /var/lib/apt/lists/*

COPY --from=build /install /usr/local

COPY . .

RUN adduser --disabled-password --gecos "" backend && \
    mkdir -p /app/data/cache /app/logs && \
    chown -R backend:backend /app

USER backend

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}