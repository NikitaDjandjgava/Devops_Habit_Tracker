FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY services/insights/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --requirement requirements.txt

COPY services/insights/app.py ./app.py
COPY services/insights/wsgi.py ./wsgi.py
COPY insights/stats.py ./stats.py
COPY services/insights/migrations ./migrations

RUN useradd --system --no-create-home appuser
USER appuser

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "1", "wsgi:app"]
