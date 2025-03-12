# 🚀 LightRAG (Postgres Edition)

This repository contains a Postgres-configured version of LightRAG. The system is designed for simplicity and fast startup using Docker.

## 🔧 How to Run

1. **Clone the Repository**

```bash
git clone https://github.com/BridgeCare-ai/AI-Assistant Branch init
cd lightrag-pg

docker-compose up --build
```

2. Access the Web UI
http://localhost:9621/webui/


3. Notes
	•	This version is configured specifically for PostgreSQL and Apache AGE.
	•	Other configurations from the original LightRAG repo (e.g., JsonKVStorage, NetworkX, Neo4J) are deprecated and no longer supported.
	•	Some legacy files remain in the repository from the original codebase but are no longer used. They will be removed in a future cleanup.
