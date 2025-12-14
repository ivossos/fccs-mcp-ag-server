FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# Copy application code
COPY fccs_agent/ fccs_agent/
COPY web/ web/
COPY cli/ cli/

# Set environment variables
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# Expose port (Cloud Run will set PORT env var)
EXPOSE 8080

# Run web server (will use PORT from environment)
CMD ["python", "-m", "web.server"]
