FROM python:3.11-slim

WORKDIR /app

COPY ./frontend /app/frontend

COPY ./backend /app/backend

COPY requirements.txt .
RUN pip install -r requirements.txt

CMD ["uvicorn", "frontend.main:app", "--host", "0.0.0.0", "--port", "8000"]