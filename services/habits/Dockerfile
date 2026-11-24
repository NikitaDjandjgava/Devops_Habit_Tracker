FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY services/habits/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --requirement requirements.txt

COPY services/habits/app.py ./app.py
COPY services/habits/wsgi.py ./wsgi.py
COPY habits/schedule.py ./schedule.py
COPY services/habits/migrations ./migrations

RUN useradd --system --no-create-home appuser
USER appuser

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "1", "wsgi:app"]
