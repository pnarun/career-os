FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Initialize Playwright browsers for future automation (no workflows yet).
RUN playwright install --with-deps chromium

COPY app ./app
# Brand PNGs for /brand on API dev pages (logs, /uptime)

ENV PORT=8000
EXPOSE 8000

# Render injects PORT at runtime
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
