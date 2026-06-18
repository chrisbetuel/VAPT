# =============================================================================
# VAPT Backend - Dockerfile (Multi-stage)
# =============================================================================
# Python base
FROM python:3.11-slim-bookworm AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libpq-dev \
    netcat-openbsd \
    nmap \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install nuclei, subfinder, ffuf from GitHub releases
RUN curl -sL "https://github.com/projectdiscovery/nuclei/releases/download/v3.3.9/nuclei_3.3.9_linux_amd64.zip" -o /tmp/nuclei.zip && \
    unzip /tmp/nuclei.zip -d /tmp/nuclei && \
    mv /tmp/nuclei/nuclei /usr/local/bin/nuclei && \
    chmod +x /usr/local/bin/nuclei && \
    rm -rf /tmp/nuclei*

RUN curl -sL "https://github.com/projectdiscovery/subfinder/releases/download/v2.6.7/subfinder_2.6.7_linux_amd64.zip" -o /tmp/subfinder.zip && \
    unzip /tmp/subfinder.zip -d /tmp/subfinder && \
    mv /tmp/subfinder/subfinder /usr/local/bin/subfinder && \
    chmod +x /usr/local/bin/subfinder && \
    rm -rf /tmp/subfinder*

RUN curl -sL "https://github.com/ffuf/ffuf/releases/download/v2.1.0/ffuf_2.1.0_linux_amd64.tar.gz" -o /tmp/ffuf.tar.gz && \
    tar -xzf /tmp/ffuf.tar.gz -C /tmp && \
    mv /tmp/ffuf /usr/local/bin/ffuf && \
    chmod +x /usr/local/bin/ffuf && \
    rm -rf /tmp/ffuf*

WORKDIR /app

# Dependencies stage
FROM base AS deps
COPY requirements/ requirements/
RUN pip install --no-cache-dir -r requirements/prod.txt

# Development stage
FROM base AS development
ENV ENVIRONMENT=development
COPY --from=deps /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin
COPY requirements/ requirements/
RUN pip install --no-cache-dir -r requirements/dev.txt
COPY . .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--use-colors"]

# Production stage
FROM base AS production
ENV ENVIRONMENT=production
COPY --from=deps /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin
COPY . .

RUN useradd -m -u 1000 vapt && chown -R vapt:vapt /app
USER vapt

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["gunicorn", "app.main:app", "--bind", "0.0.0.0:8000", \
     "-k", "uvicorn.workers.UvicornWorker", \
     "--workers", "4", \
     "--max-requests", "1000", \
     "--max-requests-jitter", "50", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
