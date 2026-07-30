FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Non-root runtime user; /app must stay writable for the default
# sqlite:///accounts_${TENANT_ID}.db database file.
RUN useradd --system --uid 10001 --gid 0 --no-create-home --shell /usr/sbin/nologin appuser \
    && chown -R 10001:0 /app \
    && chmod -R g+rwX /app

USER 10001

EXPOSE 8001

HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=3 \
    CMD ["python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8001/health', timeout=4).status == 200 else 1)"]

CMD ["python", "run.py"]
