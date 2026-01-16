# Multi-stage build for Arcane CLI
FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy application code
COPY . .

# Install the application
RUN pip install -e .

# Production stage
FROM python:3.11-slim as production

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.local/bin:$PATH"

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r arcane && useradd -r -g arcane arcane

# Create app directory and set ownership
WORKDIR /app
RUN chown -R arcane:arcane /app

# Copy application from builder stage
COPY --from=builder --chown=arcane:arcane /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder --chown=arcane:arcane /usr/local/bin /usr/local/bin
COPY --from=builder --chown=arcane:arcane /app /app

# Switch to non-root user
USER arcane

# Create directories for configuration and output
RUN mkdir -p /home/arcane/.arcane /home/arcane/output

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -m arcane --help || exit 1

# Set default command
ENTRYPOINT ["python", "-m", "arcane"]
CMD ["--help"]

# Labels
LABEL org.opencontainers.image.title="Arcane CLI" \
      org.opencontainers.image.description="AI-powered roadmap generation and project integration" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.authors="Arcane CLI Team" \
      org.opencontainers.image.source="https://github.com/your-org/arcane" \
      org.opencontainers.image.documentation="https://github.com/your-org/arcane/blob/main/README.md"