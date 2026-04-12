FROM python:3.12-slim AS base

WORKDIR /app

# System deps for asyncpg / psycopg
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

COPY pyproject.toml .

# ---- Development ----
FROM base AS development
COPY . .
RUN uv pip install --system -e ".[dev]"
RUN chmod +x /app/entrypoint.sh
RUN adduser --disabled-password --no-create-home --gecos '' appuser
USER appuser
EXPOSE 8000
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ---- Production ----
FROM base AS production
COPY . .
RUN uv pip install --system -e .
RUN chmod +x /app/entrypoint.sh
RUN adduser --disabled-password --no-create-home --gecos '' appuser
USER appuser
EXPOSE 8000
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
