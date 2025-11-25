# Git AI & Indexer Service

A comprehensive RAG-to-Write pipeline for automated code modification using Git and Vector Databases.

## Project Overview

This repository contains a modular system designed to assist with software development tasks by integrating Large Language Models (LLMs) with local Git repositories. It uses a "Retrieval-Augmented Generation" (RAG) approach to understand the codebase and generating semantic JSON Patches to modify code safely.

### Components

The project is divided into two main components:

*   **`git-ai`**: A Python CLI tool and [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server. It handles the logic of interacting with Git, applying patches, and communicating with the Indexer.
*   **`indexer-service`**: A FastAPI microservice wrapping [Qdrant](https://qdrant.tech/). It handles the indexing of code chunks and semantic search operations.

## Architecture

The system follows a strict **Object of Importance (OOI)** design pattern, emphasizing:
*   **Immutable State**: Uses frozen Pydantic models for predictable state management.
*   **Type Safety**: Leveraging Python type hints and runtime validation.
*   **State Transitions**: Centralized factory logic for transitioning between task states (e.g., from `TaskDefined` to `ContextRetrieved` to `PatchGenerated`).

For a detailed audit of the system design, please refer to [AUDIT_REPORT.md](./AUDIT_REPORT.md).

## Quick Start

### Prerequisites
*   Docker and Docker Compose
*   Python 3.9+ (for local development)

### Running with Docker

1.  Build and start the services:
    ```bash
    docker-compose up --build -d
    ```
2.  The services will be available at:
    *   **Indexer Service**: `http://localhost:8000`
    *   **Qdrant**: `http://localhost:6333`

### Running Locally (CLI)

To run the `git-ai` tool locally against a running indexer:

1.  Install the package:
    ```bash
    pip install -e git-ai
    ```
2.  Run the tool:
    ```bash
    export INDEXER_URL=http://localhost:8000
    git-ai --help
    ```

For detailed deployment instructions, see [DEPLOYMENT.md](./DEPLOYMENT.md).

## Model Context Protocol (MCP)

`git-ai` can function as an MCP server, allowing it to be used directly by AI assistants (like Claude Desktop).

To configure the MCP server, see [git-ai/MCP_CONFIG.md](./git-ai/MCP_CONFIG.md).

## AI Guidance

We utilize structured YAML files to provide guidance for AI agents working on this codebase. These files leverage YAML features like anchors and aliases to define reusable patterns and rules.

See [AGENTS.yaml](./AGENTS.yaml) and the `ai-guidance/` directory for more details.

## License

[License Information Here - TBD]
