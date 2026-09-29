# =====================================================================
# POLAR-TWIN Backend Dockerfile
# Production-ready container for Antarctic Digital Twin (Maitri & Bharati)
# =====================================================================

FROM python:3.11-slim

# Set environment flags
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000

# Install minimal OS dependencies and libpq for PostgreSQL/TimescaleDB
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create dedicated non-root application user for container security
RUN groupadd -r polar && useradd -r -g polar -d /home/polar -m polar

# Set working directory
WORKDIR /app

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy backend codebase
COPY app ./app
COPY alembic.ini* ./
COPY database ./database

# Set proper permissions
RUN chown -R polar:polar /app

# Switch to non-root user
USER polar

# Expose FastAPI port
EXPOSE 8000

# Docker healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Launch application with production ASGI server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
