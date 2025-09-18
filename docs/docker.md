# Docker Guide

This guide explains how to run the Azure Terraform MCP Server in a Docker container, from quick start examples to detailed deployment and troubleshooting.

## Quick Start

### Using Pre-built Docker Image (Recommended)

The easiest way to get started is using the pre-built Docker image from GitHub Container Registry:

#### 1. Basic Usage

**Linux/macOS:**
```bash
# Pull and run the latest image
docker run -d \
  --name tf-mcp-server \
  -p 8000:8000 \
  ghcr.io/liuwuliuyun/tf-mcp-server:latest
```

**Windows PowerShell:**
```powershell
# Pull and run the latest image
docker run -d `
  --name tf-mcp-server `
  -p 8000:8000 `
  ghcr.io/liuwuliuyun/tf-mcp-server:latest
```

#### 2. With Azure Credentials

**Linux/macOS:**
```bash
# Mount Azure credentials from host
docker run -d \
  --name tf-mcp-server \
  -p 8000:8000 \
  -v ~/.azure:/home/mcpuser/.azure:ro \
  ghcr.io/liuwuliuyun/tf-mcp-server:latest
```

**Windows PowerShell:**
```powershell
# Mount Azure credentials from host
docker run -d `
  --name tf-mcp-server `
  -p 8000:8000 `
  -v "$env:USERPROFILE\.azure:/home/mcpuser/.azure:ro" `
  ghcr.io/liuwuliuyun/tf-mcp-server:latest
```

#### 3. With Environment Variables

**Linux/macOS:**
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

**Windows PowerShell:**
```powershell
# Using Azure service principal
docker run -d `
  --name tf-mcp-server `
  -p 8000:8000 `
  -e AZURE_CLIENT_ID=your-client-id `
  -e AZURE_CLIENT_SECRET=your-client-secret `
  -e AZURE_TENANT_ID=your-tenant-id `
  -e AZURE_SUBSCRIPTION_ID=your-subscription-id `
  ghcr.io/liuwuliuyun/tf-mcp-server:latest
```

#### 4. Full Configuration

**Linux/macOS:**
```bash
# Recommended production setup
docker run -d \
  --name tf-mcp-server \
  -p 8000:8000 \
  -e MCP_SERVER_HOST=0.0.0.0 \
  -e MCP_SERVER_PORT=8000 \
  -e LOG_LEVEL=INFO \
  -v ~/.azure:/home/mcpuser/.azure:ro \
  -v ./logs:/app/logs \
  --restart unless-stopped \
  ghcr.io/liuwuliuyun/tf-mcp-server:latest
```

**Windows PowerShell:**
```powershell
# Recommended production setup
docker run -d `
  --name tf-mcp-server `
  -p 8000:8000 `
  -e MCP_SERVER_HOST=0.0.0.0 `
  -e MCP_SERVER_PORT=8000 `
  -e LOG_LEVEL=INFO `
  -v "$env:USERPROFILE\.azure:/home/mcpuser/.azure:ro" `
  -v ".\logs:/app/logs" `
  --restart unless-stopped `
  ghcr.io/liuwuliuyun/tf-mcp-server:latest
```

#### 5. Using Docker Compose (Recommended)

**Linux/macOS:**
```bash
# Download the docker-compose.yml file
curl -O https://raw.githubusercontent.com/liuwuliuyun/tf-mcp-server/main/docker-compose.yml

# Start the service
docker-compose up -d

# Check if it's running
docker-compose ps
```

**Windows PowerShell:**
```powershell
# Download the docker-compose.yml file
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/liuwuliuyun/tf-mcp-server/main/docker-compose.yml" -OutFile "docker-compose.yml"

# Start the service
docker-compose up -d

# Check if it's running
docker-compose ps
```

### Testing the Server

Once running, test the server:

**Linux/macOS:**
```bash
# Check if server is running
curl http://localhost:8000/health

# View logs
docker logs tf-mcp-server

# Check container status
docker ps | grep tf-mcp-server
```

**Windows PowerShell:**
```powershell
# Check if server is running
Invoke-RestMethod -Uri "http://localhost:8000/health"

# View logs
docker logs tf-mcp-server

# Check container status
docker ps | Select-String "tf-mcp-server"
```

## Building from Source

If you prefer to build the image yourself:

1. **Clone the repository:**

   **Linux/macOS:**
   ```bash
   git clone https://github.com/liuwuliuyun/tf-mcp-server.git
   cd tf-mcp-server
   ```

   **Windows PowerShell:**
   ```powershell
   git clone https://github.com/liuwuliuyun/tf-mcp-server.git
   Set-Location tf-mcp-server
   ```

2. **Build the image:**
   ```bash
   docker build -t tf-mcp-server .
   ```

3. **Run the container:**

   **Linux/macOS:**
   ```bash
   docker run -d \
     --name tf-mcp-server \
     -p 8000:8000 \
     -e MCP_SERVER_HOST=0.0.0.0 \
     -e MCP_SERVER_PORT=8000 \
     -e LOG_LEVEL=INFO \
     -v $(pwd)/logs:/app/logs \
     --restart unless-stopped \
     tf-mcp-server
   ```

   **Windows PowerShell:**
   ```powershell
   docker run -d `
     --name tf-mcp-server `
     -p 8000:8000 `
     -e MCP_SERVER_HOST=0.0.0.0 `
     -e MCP_SERVER_PORT=8000 `
     -e LOG_LEVEL=INFO `
     -v "$PWD\logs:/app/logs" `
     --restart unless-stopped `
     tf-mcp-server
   ```

## Container Management

### Available Images

- **Latest**: `ghcr.io/liuwuliuyun/tf-mcp-server:latest` - Latest stable version
- **Specific version**: `ghcr.io/liuwuliuyun/tf-mcp-server:v1.0.0` - Tagged releases
- **Branch builds**: `ghcr.io/liuwuliuyun/tf-mcp-server:main` - Latest from main branch

### Using Different Tags

**Linux/macOS:**
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

**Windows PowerShell:**
```powershell
# Use a specific version
docker run -d --name tf-mcp-server -p 8000:8000 `
  ghcr.io/liuwuliuyun/tf-mcp-server:v1.0.0

# Use main branch build
docker run -d --name tf-mcp-server -p 8000:8000 `
  ghcr.io/liuwuliuyun/tf-mcp-server:main

# Use latest stable
docker run -d --name tf-mcp-server -p 8000:8000 `
  ghcr.io/liuwuliuyun/tf-mcp-server:latest
```

### Basic Container Commands

**All platforms (same commands):**
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

# Check container status
docker ps
docker logs tf-mcp-server
```

### Health Checks

The container includes health checks that verify the MCP server is running:

**All platforms (same commands):**
```bash
# Check health status
docker inspect --format='{{.State.Health.Status}}' tf-mcp-server

# View health logs
docker inspect --format='{{range .State.Health.Log}}{{.Output}}{{end}}' tf-mcp-server
```

Health check details:
- **Interval**: 30 seconds
- **Timeout**: 10 seconds
- **Start Period**: 40 seconds
- **Retries**: 3

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MCP_SERVER_HOST` | Server bind address | `0.0.0.0` |
| `MCP_SERVER_PORT` | Server port | `8000` |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | `INFO` |
| `AZURE_CLIENT_ID` | Azure service principal client ID | - |
| `AZURE_CLIENT_SECRET` | Azure service principal secret | - |
| `AZURE_TENANT_ID` | Azure tenant ID | - |
| `AZURE_SUBSCRIPTION_ID` | Azure subscription ID | - |
| `TF_LOG` | Terraform logging level | - |
| `TF_LOG_PATH` | Terraform log file path | - |

### Azure Authentication (Optional)

For Azure CLI integration, you can provide Azure credentials via environment variables:

```env
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
AZURE_TENANT_ID=your-tenant-id
AZURE_SUBSCRIPTION_ID=your-subscription-id
```

Alternatively, you can mount Azure credentials from the host:

**Linux/macOS:**
```bash
docker run -d \
  --name tf-mcp-server \
  -p 8000:8000 \
  -v ~/.azure:/home/mcpuser/.azure:ro \
  tf-mcp-server
```

**Windows PowerShell:**
```powershell
docker run -d `
  --name tf-mcp-server `
  -p 8000:8000 `
  -v "$env:USERPROFILE\.azure:/home/mcpuser/.azure:ro" `
  tf-mcp-server
```

## Volumes and Persistence

### Recommended Volume Mounts

**Linux/macOS:**
```bash
# Persistent logs
-v ./logs:/app/logs

# Azure credentials (alternative to environment variables)
-v ~/.azure:/home/mcpuser/.azure:ro

# Policy files (if you want to update externally)
-v ./policy:/app/policy:ro
```

**Windows PowerShell:**
```powershell
# Persistent logs
-v ".\logs:/app/logs"

# Azure credentials (alternative to environment variables)
-v "$env:USERPROFILE\.azure:/home/mcpuser/.azure:ro"

# Policy files (if you want to update externally)
-v ".\policy:/app/policy:ro"
```

## Included Tools

The Docker image includes the following tools:

- **Python 3.11+** - Runtime environment
- **Terraform** - Infrastructure as Code tool
- **TFLint** - Terraform linter and static analysis
- **Conftest** - Policy testing tool for structured configuration data
- **Azure Terraform MCP Server** - The main application

### Tool Versions

| Tool | Version |
|------|---------|
| Terraform | latest |
| TFLint | latest |
| Conftest | latest |

> **Note:** The Dockerfile installs the latest available versions of these tools at build time. Actual versions may differ from those listed above. For reproducibility, consider pinning tool versions in the Dockerfile.

### Execute Commands Inside Container

**All platforms (same commands):**
```bash
# Get a shell inside the container
docker exec -it tf-mcp-server /bin/bash

# Check Terraform version
docker exec tf-mcp-server terraform version

# Check TFLint version
docker exec tf-mcp-server tflint --version
```

## Troubleshooting

### Common Issues

1. **Container fails to start:**

   **All platforms (same commands):**
   ```bash
   # Check logs
   docker logs tf-mcp-server
   
   # Check container status
   docker inspect tf-mcp-server
   ```

2. **Port already in use:**

   **All platforms (same commands):**
   ```bash
   # Use different port
   docker run -p 8001:8000 tf-mcp-server
   ```

3. **Permission issues:**

   **Linux/macOS:**
   ```bash
   # Check volume permissions
   ls -la logs/
   
   # Fix permissions if needed
   chmod 755 logs/
   ```

   **Windows PowerShell:**
   ```powershell
   # Check volume permissions
   Get-ChildItem -Path logs -Force
   
   # Fix permissions if needed (create directory if it doesn't exist)
   New-Item -ItemType Directory -Path "logs" -Force
   ```

4. **Resource constraints:**

   **All platforms (same commands):**
   ```bash
   # Monitor resource usage
   docker stats tf-mcp-server
   
   # Increase limits in docker-compose.yml
   deploy:
     resources:
       limits:
         memory: 2G
         cpus: '1.0'
   ```

### Debug Mode

Run container in debug mode:

**Linux/macOS:**
```bash
docker run -it --rm \
  -e LOG_LEVEL=DEBUG \
  -p 8000:8000 \
  tf-mcp-server
```

**Windows PowerShell:**
```powershell
docker run -it --rm `
  -e LOG_LEVEL=DEBUG `
  -p 8000:8000 `
  tf-mcp-server
```

Access container shell:
**All platforms (same commands):**
```bash
docker exec -it tf-mcp-server /bin/bash
```

### Logs

View different types of logs:

**All platforms (same commands):**
```bash
# Application logs
docker logs tf-mcp-server

# Terraform logs (if TF_LOG_PATH is set)
docker exec tf-mcp-server cat /app/logs/terraform.log

# System logs
docker exec tf-mcp-server journalctl --no-pager
```

## Security Considerations

### Non-root User

The container runs as a non-root user (`mcpuser`) for security:

```dockerfile
RUN groupadd -r mcpuser && useradd -r -g mcpuser mcpuser
USER mcpuser
```

### Security Options

Additional security options for production:

**Linux/macOS:**
```bash
docker run -d \
  --name tf-mcp-server \
  -p 8000:8000 \
  --security-opt no-new-privileges:true \
  --read-only \
  tf-mcp-server
```

**Windows PowerShell:**
```powershell
docker run -d `
  --name tf-mcp-server `
  -p 8000:8000 `
  --security-opt no-new-privileges:true `
  --read-only `
  tf-mcp-server
```

### Network Security

- Only expose necessary ports
- Use Docker networks for container communication
- Consider using reverse proxy for production

## Production Deployment

### Recommendations

1. **Use specific image tags:**

   **All platforms (same commands):**
   ```bash
   docker build -t tf-mcp-server:v1.0.0 .
   ```

2. **Set resource limits:**

   **Linux/macOS:**
   ```bash
   docker run -d \
     --name tf-mcp-server \
     -p 8000:8000 \
     --memory=1g \
     --cpus=0.5 \
     tf-mcp-server
   ```

   **Windows PowerShell:**
   ```powershell
   docker run -d `
     --name tf-mcp-server `
     -p 8000:8000 `
     --memory=1g `
     --cpus=0.5 `
     tf-mcp-server
   ```

3. **Configure log rotation:**

   **Linux/macOS:**
   ```bash
   docker run -d \
     --name tf-mcp-server \
     -p 8000:8000 \
     --log-driver json-file \
     --log-opt max-size=10m \
     --log-opt max-file=3 \
     tf-mcp-server
   ```

   **Windows PowerShell:**
   ```powershell
   docker run -d `
     --name tf-mcp-server `
     -p 8000:8000 `
     --log-driver json-file `
     --log-opt max-size=10m `
     --log-opt max-file=3 `
     tf-mcp-server
   ```

4. **Use secrets for sensitive data:**
   ```yaml
   secrets:
     azure_client_secret:
       external: true
   ```

5. **Monitor container health:**
   ```bash
   # Set up monitoring with tools like Prometheus
   # Use health check endpoints
   # Configure alerting
   ```

## Updates and Maintenance

### Updating the Image

1. **Pull latest changes:**

   **All platforms (same commands):**
   ```bash
   git pull
   ```

2. **Rebuild image:**

   **All platforms (same commands):**
   ```bash
   docker-compose build --no-cache
   ```

3. **Restart services:**

   **All platforms (same commands):**
   ```bash
   docker stop tf-mcp-server
   docker rm tf-mcp-server
   docker build -t tf-mcp-server .
   docker run -d --name tf-mcp-server -p 8000:8000 tf-mcp-server
   ```

### Backup

Important data to backup:
- Application logs in `logs/` directory
- Custom policies in `policy/` directory
- Terraform state files (if stored locally)
- Container configuration commands

## Support

For issues and questions:
- Check the troubleshooting section above
- Review application logs
- Check the main README.md for application-specific help
- Open an issue in the project repository