FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /workspace

COPY requirements.txt ./requirements.txt

RUN pip install --upgrade pip \
    && pip install -r requirements.txt \
    && python -m spacy download en_core_web_sm

COPY . .

CMD ["sh", "-c", "alembic -c alembic/alembic.ini upgrade head && uvicorn backend.app.main:app --host ${APP_HOST:-0.0.0.0} --port ${APP_PORT:-8000}"]
