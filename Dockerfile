# EquineSync Dockerfile
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY config/ ./config/
COPY .env.example .env

# Create non-root user
RUN useradd -m -u 1000 equinesync && \
    chown -R equinesync:equinesync /app

USER equinesync

# Default command (can be overridden)
CMD ["python", "src/stream_processor.py"]
