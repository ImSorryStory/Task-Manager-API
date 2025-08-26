FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# системные пакеты могут понадобиться для некоторых зависимостей
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl bash ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .
RUN chmod +x /app/entrypoint.sh

EXPOSE 8001
CMD ["/app/entrypoint.sh"]
