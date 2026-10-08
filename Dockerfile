FROM python:3.10-slim

# Prevent Python from writing .pyc files and buffer output
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Ensure entrypoint script is executable
RUN chmod +x /app/entrypoint.sh

# Cloud Run default port
EXPOSE 8080

ENTRYPOINT ["/app/entrypoint.sh"]
