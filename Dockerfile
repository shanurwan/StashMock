# syntax=docker/dockerfile:1

FROM python:3.11-slim

# System deps (keep minimal)
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first (better layer caching)
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . /app

# Ensure start.sh is executable inside the image
RUN chmod +x /app/start.sh

# Useful for relative imports
ENV PYTHONPATH=/app

EXPOSE 8000
CMD ["/app/start.sh"]
