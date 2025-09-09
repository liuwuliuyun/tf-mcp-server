# Quick Start with Docker

This document provides quick examples for running the Azure Terraform MCP Server with Docker.

## Prerequisites

- Docker installed on your system
- (Optional) Docker Compose for easier management

## Basic Usage

### 1. Quick Start
```bash
# Pull and run the latest image
docker run -d \
  --name tf-mcp-server \
  -p 8000:8000 \
  ghcr.io/liuwuliuyun/tf-mcp-server:latest
```

### 2. With Azure Credentials
```bash
# Mount Azure credentials from host
docker run -d \
  --name tf-mcp-server \
  -p 8000:8000 \
  -v ~/.azure:/home/mcpuser/.azure:ro \
  ghcr.io/liuwuliuyun/tf-mcp-server:latest
```

### 3. With Environment Variables
```bash
# Using Azure service principal
docker run -d \
  --name tf-mcp-server \
  -p 8000:8000 \
  -e AZURE_CLIENT_ID=your-client-id \
  -e AZURE_CLIENT_SECRET=your-client-secret \
  -e AZURE_TENANT_ID=your-tenant-id \
  -e AZURE_SUBSCRIPTION_ID=your-subscription-id \
  ghcr.io/liuwuliuyun/tf-mcp-server:latest
```

### 4. With Custom Configuration
```bash
# Custom port and log level
docker run -d \
  --name tf-mcp-server \
  -p 9000:9000 \
  -e MCP_SERVER_PORT=9000 \
  -e LOG_LEVEL=DEBUG \
  ghcr.io/liuwuliuyun/tf-mcp-server:latest
```

## Docker Compose

Create a `docker-compose.yml` file:

```yaml
version: '3.8'

services:
  tf-mcp-server:
    image: ghcr.io/liuwuliuyun/tf-mcp-server:latest
    container_name: tf-mcp-server
    ports:
      - "8000:8000"
    environment:
      - MCP_SERVER_HOST=0.0.0.0
      - MCP_SERVER_PORT=8000
      - LOG_LEVEL=INFO
    volumes:
      - ~/.azure:/home/mcpuser/.azure:ro
      - ./terraform-workspace:/workspace
    restart: unless-stopped
```

Then run:
```bash
docker-compose up -d
```

## Testing the Server

Once running, test the server:

```bash
# Check if server is running
curl http://localhost:8000/health

# View logs
docker logs tf-mcp-server

# Check container status
docker ps | grep tf-mcp-server
```

## Management Commands

```bash
# Stop the server
docker stop tf-mcp-server

# Start the server
docker start tf-mcp-server

# Restart the server
docker restart tf-mcp-server

# Remove the container
docker rm tf-mcp-server

# Pull latest image
docker pull ghcr.io/liuwuliuyun/tf-mcp-server:latest
```

## Using Different Tags

```bash
# Use a specific version
docker run -d --name tf-mcp-server -p 8000:8000 \
  ghcr.io/liuwuliuyun/tf-mcp-server:v1.0.0

# Use main branch build
docker run -d --name tf-mcp-server -p 8000:8000 \
  ghcr.io/liuwuliuyun/tf-mcp-server:main

# Use latest stable
docker run -d --name tf-mcp-server -p 8000:8000 \
  ghcr.io/liuwuliuyun/tf-mcp-server:latest
```

## Troubleshooting

### Check Health Status
```bash
docker inspect --format='{{.State.Health.Status}}' tf-mcp-server
```

### View Health Logs
```bash
docker inspect --format='{{range .State.Health.Log}}{{.Output}}{{end}}' tf-mcp-server
```

### Execute Commands Inside Container
```bash
# Get a shell inside the container
docker exec -it tf-mcp-server /bin/bash

# Check Terraform version
docker exec tf-mcp-server terraform version

# Check TFLint version
docker exec tf-mcp-server tflint --version
```

For more detailed information, see [DOCKER.md](DOCKER.md).
