# Placeholder image for Process B, which will harden it (non-root user,
# HEALTHCHECK instruction, pinned base image digest, multi-stage build).
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8004

CMD ["python", "run.py"]
