FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VERSION=1.8.3

WORKDIR /app

RUN pip install "poetry==$POETRY_VERSION"

COPY pyproject.toml poetry.lock ./

RUN poetry export --without dev --format requirements.txt --output requirements.txt --without-hashes


FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY --from=builder /app/requirements.txt ./requirements.txt

RUN pip install -r requirements.txt

COPY app ./app
COPY alembic ./alembic
COPY main.py ./main.py
COPY alembic.ini ./alembic.ini
COPY README.md ./README.md
COPY pyproject.toml ./pyproject.toml

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
