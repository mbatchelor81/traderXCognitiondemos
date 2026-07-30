# Placeholder image for Process B, which will harden it
# (non-root user, HEALTHCHECK, pinned base digest, multi-stage build).
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8001

CMD ["python", "run.py"]
