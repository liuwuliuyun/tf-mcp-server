# Docker Deployment Guide

This guide explains how to run the Azure Terraform MCP Server in a Docker container.

## Quick Start

### Using Docker CLI

1. **Build the image:**
   ```bash
   docker build -t tf-mcp-server .
   ```

2. **Run the container:**
   ```bash
   docker run -d \
     --name tf-mcp-server \
     -p 8000:8000 \
     -e MCP_SERVER_HOST=0.0.0.0 \
     -e MCP_SERVER_PORT=8000 \
     -e LOG_LEVEL=INFO \
     -v $(pwd)/logs:/app/logs \
     --restart unless-stopped \
   ```

3. **Check container status:**
   ```bash
   docker ps
   docker logs tf-mcp-server
   ```

4. **Stop the container:**
   ```bash
   docker stop tf-mcp-server
   docker rm tf-mcp-server
   ```

### Using Build Scripts (Recommended)

1. **Clone the repository and navigate to the project directory:**
   ```bash
   git clone <repository-url>
   cd tf-mcp-server
   ```

2. **Build and run using scripts:**
   
   **Linux/macOS:**
   ```bash
   ./docker-build.sh build
   ./docker-build.sh run
   ```
   
   **Windows PowerShell:**
   ```powershell
   .\docker-build.ps1 build
   .\docker-build.ps1 run
   ```

3. **Check service status:**
   ```bash
   # Linux/macOS
   ./docker-build.sh logs
   
   # Windows PowerShell
   .\docker-build.ps1 logs
   ```

4. **Stop the service:**
   ```bash
   # Linux/macOS
   ./docker-build.sh stop
   
   # Windows PowerShell
   .\docker-build.ps1 stop
   ```

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

```bash
docker run -d \
  --name tf-mcp-server \
  -p 8000:8000 \
  -v ~/.azure:/home/mcpuser/.azure:ro \
  tf-mcp-server
```

## Volumes and Persistence

### Recommended Volume Mounts

```bash
# Persistent logs
-v ./logs:/app/logs

# Azure credentials (alternative to environment variables)
-v ~/.azure:/home/mcpuser/.azure:ro

# Policy files (if you want to update externally)
-v ./policy:/app/policy:ro
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
| Terraform | 1.9.8 |
| TFLint | 0.53.0 |
| Conftest | 0.58.1 |

## Health Checks

The container includes built-in health checks that monitor:

- Server process status
- Port availability
- Application readiness

Health check details:
- **Interval**: 30 seconds
- **Timeout**: 10 seconds
- **Start Period**: 40 seconds
- **Retries**: 3

Check health status:
```bash
docker inspect --format='{{.State.Health.Status}}' tf-mcp-server
```

## Troubleshooting

### Common Issues

1. **Container fails to start:**
   ```bash
   # Check logs
   docker logs tf-mcp-server
   
   # Check container status
   docker inspect tf-mcp-server
   ```

2. **Port already in use:**
   ```bash
   # Use different port
   docker run -p 8001:8000 tf-mcp-server
   ```

3. **Permission issues:**
   ```bash
   # Check volume permissions
   ls -la logs/
   
   # Fix permissions if needed
   chmod 755 logs/
   ```

4. **Resource constraints:**
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

```bash
docker run -it --rm \
  -e LOG_LEVEL=DEBUG \
  -p 8000:8000 \
  tf-mcp-server
```

Access container shell:
```bash
docker exec -it tf-mcp-server /bin/bash
```

### Logs

View different types of logs:

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

```bash
docker run -d \
  --name tf-mcp-server \
  -p 8000:8000 \
  --security-opt no-new-privileges:true \
  --read-only \
  tf-mcp-server
```

### Network Security

- Only expose necessary ports
- Use Docker networks for container communication
- Consider using reverse proxy for production

## Production Deployment

### Recommendations

1. **Use specific image tags:**
   ```bash
   docker build -t tf-mcp-server:v1.0.0 .
   ```

2. **Set resource limits:**
   ```bash
   docker run -d \
     --name tf-mcp-server \
     -p 8000:8000 \
     --memory=1g \
     --cpus=0.5 \
     tf-mcp-server
   ```

3. **Configure log rotation:**
   ```bash
   docker run -d \
     --name tf-mcp-server \
     -p 8000:8000 \
     --log-driver json-file \
     --log-opt max-size=10m \
     --log-opt max-file=3 \
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
   ```bash
   git pull
   ```

2. **Rebuild image:**
   ```bash
   docker-compose build --no-cache
   ```

3. **Restart services:**
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
