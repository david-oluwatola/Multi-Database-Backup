# Use a slim Python image
FROM python:3.11-slim

# Install OS packages for DB client tools and common utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    postgresql-client \
    default-mysql-client \
    gzip \
    tar \
    iproute2 \
 && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements file if present (optional)
COPY requirements.txt /app/requirements.txt
RUN if [ -f /app/requirements.txt ]; then pip install --no-cache-dir -r /app/requirements.txt; fi

# Copy scripts folder into the image (mounted volume can override in dev)
COPY scripts /app/scripts

# Ensure scripts are executable
RUN chmod -R +x /app/scripts

# Default entrypoint (can be overridden by docker-compose run ...)
ENTRYPOINT ["python3"]
CMD ["--version"]

