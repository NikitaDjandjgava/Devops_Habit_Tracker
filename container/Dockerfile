# TODO 1: choose the Python base image
FROM python:3.12-slim

# TODO 2: set the application working directory
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000
ENV DATA_DIR=/data

# TODO 3: install Python dependencies
COPY requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt

# TODO 4: copy the app and start the server
COPY . .
RUN mkdir -p /data
EXPOSE 8000
CMD ["python", "app.py"]
