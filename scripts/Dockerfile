FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install Ollama CLI for model management
RUN curl -fsSL https://ollama.ai/install.sh | sh

# Install basic dependencies
RUN pip install --no-cache-dir neo4j requests httpx

# Copy initialization scripts
COPY . .

# Make scripts executable
RUN chmod +x *.py *.sh

# Set Python path
ENV PYTHONPATH=/app

# Default command runs system initialization
CMD ["python", "init.py"]