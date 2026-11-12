FROM python:3.12-slim

ENV PORT=8000 \
    DATA_DIR=/data

WORKDIR /app

RUN useradd --system --no-create-home appuser \
    && mkdir -p /data \
    && chown appuser:appuser /data

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py db.py schema.sql seed.json ./
COPY habits/ ./habits/
COPY insights/ ./insights/
COPY ui/ ./ui/
COPY templates/ ./templates/
COPY static/ ./static/

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:' + os.environ.get('PORT', '8000') + '/health', timeout=2)"]

CMD ["python", "app.py"]
