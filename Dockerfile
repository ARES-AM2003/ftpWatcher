FROM python:3.11-slim

# Metadata
LABEL maintainer="rochaksulu2002@gmail.com"
LABEL description="FTP File Processor - Automated file upload to S3 via backend API"
LABEL version="1.0.0"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmagic1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py config.py logger.py watcher.py processor.py \
     api_client.py storage_client.py utils.py ./
# Create group with GID 1005 and user with UID 1005 in that group
RUN groupadd -g 1005 ftpUsers && \
    useradd -m -u 1005 -g 1005 -s /bin/bash ftpprocessor && \
    chown -R ftpprocessor:ftpUsers /app && \
    mkdir -p /app/logs && \
    chown ftpprocessor:ftpUsers /app/logs

# Switch to non-root user
USER ftpprocessor

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; from pathlib import Path; sys.exit(0 if Path('main.py').exists() else 1)"

# Run application
CMD ["python", "-u", "main.py"]
