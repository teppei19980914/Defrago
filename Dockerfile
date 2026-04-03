FROM python:3.12-slim

WORKDIR /app

# bcrypt等のCエクステンションビルドに必要なパッケージ + PostgreSQLクライアント
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev --frozen

COPY . .

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "study_python.gtd.web.app:app", "--host", "0.0.0.0", "--port", "8000"]
