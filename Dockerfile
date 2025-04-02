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

ENV VIRTUAL_ENV=.venv \
    PATH=/home/demo/app/.venv/bin:$PATH

COPY --from=builder /home/demo/app/${VIRTUAL_ENV} ${VIRTUAL_ENV}

COPY . .

ENTRYPOINT ["python", "main.py"]