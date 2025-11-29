# Deployment Guide

## Architecture
The system consists of two main components:
1. **Indexer Service**: A FastAPI service that wraps Qdrant (Vector DB). It handles document indexing and semantic search.
2. **Git AI CLI**: A Python CLI tool that uses the Indexer Service to retrieve context and generate patches.

## Prerequisites
- Docker and Docker Compose
- Python 3.9+ (if running locally without Docker)

## Deployment Steps

1. **Build and Start Services**
   ```bash
   docker-compose up --build -d
   ```
   This will start:
   - `qdrant` on port 6333
   - `indexer-service` on port 8000
   - `git-ai` (as a container, though usually run ad-hoc)

2. **Verify Services**
   - Check Qdrant: `curl http://localhost:6333/dashboard` (if enabled) or `curl http://localhost:6333/collections`
   - Check Indexer: `curl http://localhost:8000/` should return `{"message": "Indexer Service"}`

3. **Running Git AI CLI**
   You can run the CLI inside the container or locally.

   **Locally:**
   ```bash
   export INDEXER_URL=http://localhost:8000
   pip install -e git-ai
   git-ai --help
   ```

   **Via Docker:**
   ```bash
   docker-compose run --rm git-ai --help
   ```

## Configuration
- `QDRANT_HOST`: Hostname of Qdrant service (default: `qdrant` in docker, `localhost` locally).
- `QDRANT_PORT`: Port of Qdrant (default: 6333).
- `INDEXER_URL`: URL of the indexer service (used by git-ai).

## Monitoring
- Logs can be viewed via `docker-compose logs -f`.
- Qdrant metrics are available at `http://localhost:6333/metrics` (if configured).
