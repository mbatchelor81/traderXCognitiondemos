# Placeholder image for people-service.
# Process B hardens this: non-root user, HEALTHCHECK, pinned base digest.
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1

EXPOSE 8005

CMD ["python", "run.py"]
