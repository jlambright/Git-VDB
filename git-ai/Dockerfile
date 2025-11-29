FROM python:3.9-slim

WORKDIR /app

# Install git and other system dependencies
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir .

# Set entrypoint
ENTRYPOINT ["git-ai"]
