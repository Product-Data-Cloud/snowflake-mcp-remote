FROM python:3.12-slim

WORKDIR /app

# Copy requirements first for better caching
COPY pyproject.toml ./

# Install dependencies using pip
RUN pip install --no-cache-dir -e .

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

EXPOSE 8080

# Run the server
CMD ["python", "server.py"]
