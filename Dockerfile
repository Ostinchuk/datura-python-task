# syntax=docker/dockerfile:1
###############################
# Build Stage
###############################
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

ENV POETRY_VERSION=2.1.1
RUN curl -sSL https://install.python-poetry.org | python3 - --version $POETRY_VERSION
ENV PATH="/root/.local/bin:${PATH}"

WORKDIR /app

COPY pyproject.toml poetry.lock ./
RUN poetry self add poetry-plugin-export
RUN poetry export -f requirements.txt --without-hashes -o requirements.txt

###############################
# Runtime Stage
###############################
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    rustc \
    cargo \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    apt-get purge -y rustc cargo && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

COPY app/ ./app

EXPOSE 8000

ENV GUNICORN_WORKERS=4
ENV UVICORN_RELOAD=false

ENTRYPOINT ["/bin/sh", "-c"]
CMD exec gunicorn app.main:app \
    -k uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --workers ${GUNICORN_WORKERS} \
    --log-level ${LOG_LEVEL} \
    ${UVICORN_RELOAD:+--reload}
