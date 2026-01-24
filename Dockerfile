FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY prompts/ ./prompts/
COPY data/ ./data/

# Create data directories
RUN mkdir -p data/downloads data/processed data/trash data/checkpoints data/logs

ENV PYTHONPATH=/app

CMD ["python", "-m", "src.main"]
