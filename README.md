# arxiv-rag-tutorial

This project is a small end-to-end Retrieval-Augmented Generation (RAG) example for exploring arXiv papers. It combines a FastAPI backend, a React frontend, a Celery-based ingestion worker, and supporting services such as PostgreSQL, Redis, Qdrant, and LocalStack so you can search, index, and query paper content locally.

## What it includes

- A backend API for searching and retrieving paper-related answers
- A frontend UI for interacting with the assistant
- A background ingestion pipeline that prepares and indexes arXiv content
- Local infrastructure for databases, queues, vector search, and object storage

## Prerequisites

Before you start, make sure you have:

- Docker and Docker Compose
- Python 3.12
- uv

## Local setup

1. Clone the repository and change into the project folder.
2. Copy the example environment files:

   ```bash
   cp .env.example .env
   cp arxiv_backend/.env.example arxiv_backend/.env
   cp data_ingestion/.env.example data_ingestion/.env
   cp migrations/.env.example migrations/.env
   cp frontend/.env.example frontend/.env
   ```

3. Review the copied files and update any values you need, especially API keys or passwords.
4. Install the workspace dependencies:

   ```bash
   make local-install
   ```

5. Start the full local stack:

   ```bash
   make local-up
   ```

   This will build the containers, bootstrap LocalStack, and start the backend, worker, database, Redis, Qdrant, and frontend.

6. Open the app in your browser:

   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - Adminer: http://localhost:8080
   - Qdrant: http://localhost:6333

## Useful commands

- Stop the stack:

  ```bash
  make local-down
  ```

- Start the stack in watch mode with live sync:

  ```bash
  make local-watch
  ```

- Clean the built wheel artifacts:

  ```bash
  make local-clean-wheels
  ```

## Notes

The local workflow is defined in the Docker Compose configuration and the Makefile. If you want to run the production deployment flow later, the repository also includes Terraform and AWS deployment targets.
