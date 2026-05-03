FROM python:3.12-slim

WORKDIR /code

RUN apt-get update && apt-get install -y --no-install-recommends libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Dependencies layer (cached while pyproject.toml unchanged)
# INSTALL_DEV=true ставит [dev] extras (pytest, ruff, mypy) — для локальной разработки
ARG INSTALL_DEV=false
COPY pyproject.toml .
RUN if [ "$INSTALL_DEV" = "true" ]; then \
        pip install --no-cache-dir ".[dev]"; \
    else \
        pip install --no-cache-dir .; \
    fi

# App code (changes frequently — separate layer)
COPY . .

# Non-root user
RUN useradd --create-home appuser && chown -R appuser:appuser /code
USER appuser

CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${APP_PORT:-8010}"]
