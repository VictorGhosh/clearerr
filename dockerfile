FROM python:3.11-slim

WORKDIR /app

COPY ./frontend /app/frontend
COPY ./backend /app/backend

COPY requirements.txt .
RUN pip install -r requirements.txt

# Make sure its real, Do not copy empty db over existing one
RUN mkdir -p /app/db

CMD ["uvicorn", "frontend.main:app", "--host", "0.0.0.0", "--port", "8000"]