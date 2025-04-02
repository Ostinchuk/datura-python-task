FROM python:3.12-alpine as builder

ARG INSTALL_DEBUGPY

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/.poetry

RUN pip install poetry==2.1.1

COPY pyproject.toml poetry.lock ./

RUN poetry install --no-root;

FROM python:3.12-alpine as runtime

EXPOSE 8000

# Add demo user
RUN adduser -D demo && \
    mkdir -p /home/demo/app && \
    chown demo:demo /home/demo/app
WORKDIR /home/demo/app
USER demo

# Set environment variables
ENV VIRTUAL_ENV=.venv \
    PATH=/home/demo/app/.venv/bin:$PATH

# Copy virtual environment
COPY --from=builder /home/demo/app/${VIRTUAL_ENV} ${VIRTUAL_ENV}

# Copy server.py
COPY server.py server.py

# Set entrypoint
ENTRYPOINT ["python", "server.py"]