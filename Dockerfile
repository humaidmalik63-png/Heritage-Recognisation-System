# ==============================================================================
# Production Dockerfile for Visual Heritage Recognition Platform
# Two-Tier Hybrid Architecture (PyTorch CPU + FAISS + Gemini VLM)
# ==============================================================================

FROM python:3.12-slim

# Set system environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000 \
    TORCH_NUM_THREADS=2 \
    OMP_NUM_THREADS=2

# Install minimal OS runtime libraries for OpenCV headless and networking
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root application user for secure execution
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Copy dependency requirements first for Docker layer caching
COPY requirements.txt .

# Install lightweight CPU-only PyTorch first (speeds up build 5x, saves ~2GB)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Install remaining Python production dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application backend source code and essential assets
COPY backend/ /app/backend/

# Ensure non-root ownership of application files
RUN chown -R appuser:appuser /app

USER appuser

# Health check to ensure container readiness
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://127.0.0.1:${PORT}/api/health || exit 1

EXPOSE 8000

# Production startup with signal handling
STOPSIGNAL SIGTERM

CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT}"]

