FROM python:3.11-slim

WORKDIR /app

COPY ./frontend /app/frontend
COPY ./backend /app/backend
COPY ./settings /app/settings

COPY requirements.txt .
RUN pip install -r requirements.txt

# Make sure its real, Do not copy empty db over existing one
RUN mkdir -p /app/db
RUN mkdir -p /app/logs

# CMD ["uvicorn", "frontend.main:app", "--host", "0.0.0.0", "--port", "8000"]

# cron
COPY . .
RUN apt-get update && apt-get install -y cron && rm -rf /var/lib/apt/lists/*
RUN chmod +x /app/docker-entrypoint.sh
ENTRYPOINT ["/app/docker-entrypoint.sh"]