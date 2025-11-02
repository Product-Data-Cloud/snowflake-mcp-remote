FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy server
COPY server.py .

# Environment
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

EXPOSE 8080

# Start with uvicorn directly
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8080"]
