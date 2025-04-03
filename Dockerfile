###############################
# Build Stage (Builder)
###############################
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    pkg-config \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

ENV POETRY_VERSION=2.0.1
RUN curl -sSL https://install.python-poetry.org | python3 - --version $POETRY_VERSION
ENV PATH="/root/.local/bin:${PATH}"

WORKDIR /app

COPY pyproject.toml poetry.lock ./
RUN poetry self add poetry-plugin-export
RUN poetry export -f requirements.txt --without-hashes -o requirements.txt

RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

RUN python -m venv /venv
ENV VIRTUAL_ENV=/venv
ENV PATH="/venv/bin:${PATH}"
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

###############################
# Final Stage (Runtime)
###############################
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libssl3 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /venv /venv
ENV VIRTUAL_ENV=/venv
ENV PATH="/venv/bin:${PATH}"

COPY app/ ./app

EXPOSE 8000

CMD ["gunicorn", "app.main:app", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--workers", "4", "--log-level", "info"]

