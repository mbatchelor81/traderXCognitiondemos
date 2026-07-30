# Placeholder image for the trading-service.
# Process B hardens this: non-root user, HEALTHCHECK instruction, pinned base
# image digest, and multi-stage build.
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8002

CMD ["python", "run.py"]
