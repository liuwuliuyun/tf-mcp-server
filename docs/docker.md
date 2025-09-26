# Docker Guide

This guide explains how to run the Azure Terraform MCP Server in a Docker container, from quick start examples to detailed deployment and troubleshooting.

> **Important:** This server implements the **Model Context Protocol     -v "$PWD\logs:/app/logs" `
     -e LOG_LEVEL=INFO `
     ghcr.io/liuwuliuyun/tf-mcp-server:latest
   ```CP)** using **stdio transport**, not HTTP. All examples use `--rm -i` flags and volume mounting instead of port mapping.

## Quick Start

### Using Pre-built Docker Image (Recommended)

The easiest way to get started is using the pre-built Docker image from GitHub Container Registry:

#### 1. Basic Usage

For MCP (Model Context Protocol) integration with VS Code or other MCP clients:

**Linux/macOS:**
```bash
# For MCP stdio transport (recommended)
docker run --rm -i \
  --name tf-mcp-server-instance \
  -v "$(pwd):/workspace" \
  -e LOG_LEVEL=INFO \
  ghcr.io/liuwuliuyun/tf-mcp-server:latest
```

**Windows PowerShell:**
```powershell
# For MCP stdio transport (recommended)
docker run --rm -i `
  --name tf-mcp-server-instance `
  -v "${PWD}:/workspace" `
  -e LOG_LEVEL=INFO `
  ghcr.io/liuwuliuyun/tf-mcp-server:latest
```

#### 2. With Azure Service Principal

**Linux/macOS:**
```bash
# With Azure authentication for full functionality
docker run --rm -i \
  --name tf-mcp-server-instance \
  -v "$(pwd):/workspace" \
  -e ARM_CLIENT_ID=your-client-id \
  -e ARM_CLIENT_SECRET=your-client-secret \
  -e ARM_SUBSCRIPTION_ID=your-subscription-id \
  -e ARM_TENANT_ID=your-tenant-id \
  -e LOG_LEVEL=INFO \
  ghcr.io/liuwuliuyun/tf-mcp-server:latest
```

**Windows PowerShell:**
```powershell
# With Azure authentication for full functionality
docker run --rm -i `
  --name tf-mcp-server-instance `
  -v "${PWD}:/workspace" `
  -e ARM_CLIENT_ID=your-client-id `
  -e ARM_CLIENT_SECRET=your-client-secret `
  -e ARM_SUBSCRIPTION_ID=your-subscription-id `
  -e ARM_TENANT_ID=your-tenant-id `
  -e LOG_LEVEL=INFO `
  ghcr.io/liuwuliuyun/tf-mcp-server:latest
```

#### 3. With Environment Variables from Host

**Linux/macOS:**
```bash
# Using environment variables from host system
docker run --rm -i \
  --name tf-mcp-server-instance \
  -v "$(pwd):/workspace" \
  -e ARM_CLIENT_ID=$ARM_CLIENT_ID \
  -e ARM_CLIENT_SECRET=$ARM_CLIENT_SECRET \
  -e ARM_TENANT_ID=$ARM_TENANT_ID \
  -e ARM_SUBSCRIPTION_ID=$ARM_SUBSCRIPTION_ID \
  -e LOG_LEVEL=INFO \
  ghcr.io/liuwuliuyun/tf-mcp-server:latest
```

**Windows PowerShell:**
```powershell
# Using environment variables from host system
docker run --rm -i `
  --name tf-mcp-server-instance `
  -v "${PWD}:/workspace" `
  -e ARM_CLIENT_ID=$Env:ARM_CLIENT_ID `
  -e ARM_CLIENT_SECRET=$Env:ARM_CLIENT_SECRET `
  -e ARM_TENANT_ID=$Env:ARM_TENANT_ID `
  -e ARM_SUBSCRIPTION_ID=$Env:ARM_SUBSCRIPTION_ID `
  -e LOG_LEVEL=INFO `
  ghcr.io/liuwuliuyun/tf-mcp-server:latest
```

#### 4. VS Code MCP Integration

The recommended way to use this server is with VS Code's MCP integration. Create or edit `.vscode/mcp.json` in your workspace:

```json
{
  "servers": {
    "tf-mcp-server": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "--name", "tf-mcp-server-instance",
        "-v", "${workspaceFolder}:/workspace",
        "-e", "ARM_CLIENT_ID=${env:ARM_CLIENT_ID}",
        "-e", "ARM_CLIENT_SECRET=${env:ARM_CLIENT_SECRET}",
        "-e", "ARM_SUBSCRIPTION_ID=${env:ARM_SUBSCRIPTION_ID}",
        "-e", "ARM_TENANT_ID=${env:ARM_TENANT_ID}",
        "-e", "LOG_LEVEL=INFO",
        "ghcr.io/liuwuliuyun/tf-mcp-server:latest"
      ],
      "env": {
        "ARM_CLIENT_ID": "${env:ARM_CLIENT_ID}",
        "ARM_CLIENT_SECRET": "${env:ARM_CLIENT_SECRET}",
        "ARM_SUBSCRIPTION_ID": "${env:ARM_SUBSCRIPTION_ID}",
        "ARM_TENANT_ID": "${env:ARM_TENANT_ID}"
      }
    }
  }
}
```

## Important Notes

### MCP vs HTTP Server

This server is designed to work with the **Model Context Protocol (MCP)** using **stdio transport**, not as an HTTP server. The examples above show the correct usage patterns:

- ✅ **Use `--rm -i`** for stdio transport (MCP)  
- ✅ **Mount workspace** with `-v` for file access
- ✅ **No port mapping** needed (MCP uses stdin/stdout)
- ❌ **Avoid `-d -p 8000:8000`** (that's for HTTP servers)

### Workspace Mounting

The server expects Terraform files to be accessible at `/workspace` inside the container. The `-v` flag mounts your local directory:

- **VS Code**: Uses `${workspaceFolder}:/workspace` automatically
- **Manual Docker**: Use `-v "$(pwd):/workspace"` to mount current directory
- **Custom Path**: Use `-v "/path/to/your/terraform:/workspace"`

#### 5. Custom Workspace Path

You can mount a different directory and set a custom workspace root:

**Linux/macOS:**
```bash
docker run --rm -i \
  --name tf-mcp-server-instance \
  -v "/path/to/your/terraform:/workspaces/projects" \
  -e MCP_WORKSPACE_ROOT=/workspaces/projects \
  -e LOG_LEVEL=INFO \
  ghcr.io/liuwuliuyun/tf-mcp-server:latest
```

**Windows PowerShell:**
```powershell
docker run --rm -i `
  --name tf-mcp-server-instance `
  -v "C:\terraform:/workspaces/projects" `
  -e MCP_WORKSPACE_ROOT=/workspaces/projects `
  -e LOG_LEVEL=INFO `
  ghcr.io/liuwuliuyun/tf-mcp-server:latest
```

This setup allows tools like TFLint, Conftest, and aztfexport to resolve relative paths against `/workspaces/projects`.

### Testing the MCP Server

To test if the server is working correctly with MCP:

1. **Test basic functionality:**
   ```bash
   # Run a simple command that should work without Azure auth
   echo '{"method":"get_avm_modules","params":{}}' | \
   docker run --rm -i ghcr.io/liuwuliuyun/tf-mcp-server:latest
   ```

2. **Check server logs:**
   ```bash
   # View any error messages
   docker logs tf-mcp-server-instance 2>&1 | grep -i error
   ```

3. **Test with workspace:**
   ```bash
   # Create test workspace with terraform file
   mkdir test-workspace
   echo 'resource "azurerm_storage_account" "test" {}' > test-workspace/main.tf
   
   # Test server with mounted workspace
   docker run --rm -i \
     -v "$(pwd)/test-workspace:/workspace" \
     ghcr.io/liuwuliuyun/tf-mcp-server:latest
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
   docker run --rm -i \
     -v $(pwd):/workspace \
     -v $(pwd)/logs:/app/logs \
     -e LOG_LEVEL=INFO \
     ghcr.io/liuwuliuyun/tf-mcp-server:latest
   ```

   **Windows PowerShell:**
   ```powershell
   docker run --rm -i `
     -v "$PWD:/workspace" `
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
docker run --rm -i --name tf-mcp-server-instance \
  -v "$(pwd):/workspace" \
  ghcr.io/liuwuliuyun/tf-mcp-server:v1.0.0

# Use main branch build
docker run --rm -i --name tf-mcp-server-instance \
  -v "$(pwd):/workspace" \
  ghcr.io/liuwuliuyun/tf-mcp-server:main

# Use latest stable
docker run --rm -i --name tf-mcp-server-instance \
  -v "$(pwd):/workspace" \
  ghcr.io/liuwuliuyun/tf-mcp-server:latest
```

**Windows PowerShell:**
```powershell
# Use a specific version
docker run --rm -i --name tf-mcp-server-instance `
  -v "${PWD}:/workspace" `
  ghcr.io/liuwuliuyun/tf-mcp-server:v1.0.0

# Use main branch build
docker run --rm -i --name tf-mcp-server-instance `
  -v "${PWD}:/workspace" `
  ghcr.io/liuwuliuyun/tf-mcp-server:main

# Use latest stable
docker run --rm -i --name tf-mcp-server-instance `
  -v "${PWD}:/workspace" `
  ghcr.io/liuwuliuyun/tf-mcp-server:latest
```

### Basic Container Management

For MCP stdio servers, containers are typically short-lived and managed by the MCP client:

**All platforms (same commands):**
```bash
# Kill a running stdio server (if needed)
docker kill tf-mcp-server-instance

# Remove stopped containers
docker container prune

# Pull latest image
docker pull ghcr.io/liuwuliuyun/tf-mcp-server:latest

# List running containers
docker ps

# View container logs (for debugging)
docker logs tf-mcp-server-instance
```

### Health Checks

The container includes health checks that verify dependencies are available:

**All platforms (same commands):**
```bash
# Check if image has required tools
docker run --rm ghcr.io/liuwuliuyun/tf-mcp-server:latest which terraform
docker run --rm ghcr.io/liuwuliuyun/tf-mcp-server:latest which tflint
docker run --rm ghcr.io/liuwuliuyun/tf-mcp-server:latest which conftest
docker run --rm ghcr.io/liuwuliuyun/tf-mcp-server:latest which aztfexport
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | `INFO` |
| `MCP_WORKSPACE_ROOT` | Root directory for workspace operations | `/workspace` |
| `ARM_CLIENT_ID` | Azure service principal client ID | - |
| `ARM_CLIENT_SECRET` | Azure service principal secret | - |
| `ARM_TENANT_ID` | Azure tenant ID | - |
| `ARM_SUBSCRIPTION_ID` | Azure subscription ID | - |
| `TF_LOG` | Terraform logging level | - |
| `TF_LOG_PATH` | Terraform log file path | - |

### Azure Authentication (Optional)

| `ARM_CLIENT_ID` | Azure Service Principal Client ID | None |
| `ARM_CLIENT_SECRET` | Azure Service Principal Client Secret | None |  
| `ARM_SUBSCRIPTION_ID` | Azure Subscription ID | None |
| `ARM_TENANT_ID` | Azure Tenant ID | None |

For Azure integration, you can provide Azure Service Principal credentials via environment variables:

```env
ARM_CLIENT_ID=your-client-id
ARM_CLIENT_SECRET=your-client-secret
ARM_TENANT_ID=your-tenant-id
ARM_SUBSCRIPTION_ID=your-subscription-id
```

Example with Azure Service Principal:

**Linux/macOS:**
```bash
docker run --rm -i \
  --name tf-mcp-server-instance \
  -v "$(pwd):/workspace" \
  -e ARM_CLIENT_ID=your-client-id \
  -e ARM_CLIENT_SECRET=your-client-secret \
  -e ARM_SUBSCRIPTION_ID=your-subscription-id \
  -e ARM_TENANT_ID=your-tenant-id \
  ghcr.io/liuwuliuyun/tf-mcp-server:latest
```

**Windows PowerShell:**
```powershell
docker run --rm -i `
  --name tf-mcp-server-instance `
  -v "${PWD}:/workspace" `
  -e ARM_CLIENT_ID=your-client-id `
  -e ARM_CLIENT_SECRET=your-client-secret `
  -e ARM_SUBSCRIPTION_ID=your-subscription-id `
  -e ARM_TENANT_ID=your-tenant-id `
  ghcr.io/liuwuliuyun/tf-mcp-server:latest
```

## Volume Mounting

### Workspace Volume (Required)

The server requires access to your Terraform files via volume mounting:

**Linux/macOS:**
```bash
# Mount current directory as workspace
-v "$(pwd):/workspace"

# Mount specific directory
-v "/path/to/terraform:/workspace" 

# Mount with custom workspace root
-v "/path/to/terraform:/custom/path" -e MCP_WORKSPACE_ROOT=/custom/path
```

**Windows PowerShell:**
```powershell
# Mount current directory as workspace
-v "${PWD}:/workspace"

# Mount specific directory  
-v "C:\terraform:/workspace"

# Mount with custom workspace root
-v "C:\terraform:/custom/path" -e MCP_WORKSPACE_ROOT=/custom/path
```

### Optional Volume Mounts

**Linux/macOS:**
```bash
# Mount logs directory (for debugging)
-v "./logs:/app/logs"

# Mount custom policy files
-v "./custom-policies:/app/custom-policies:ro"
```

**Windows PowerShell:**
```powershell
# Mount logs directory (for debugging)
-v ".\logs:/app/logs"

# Mount custom policy files
-v ".\custom-policies:/app/custom-policies:ro"
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

For debugging, you can run commands inside the container:

**All platforms (same commands):**
```bash
# Check tool versions
docker run --rm ghcr.io/liuwuliuyun/tf-mcp-server:latest terraform version
docker run --rm ghcr.io/liuwuliuyun/tf-mcp-server:latest tflint --version
docker run --rm ghcr.io/liuwuliuyun/tf-mcp-server:latest conftest --version
docker run --rm ghcr.io/liuwuliuyun/tf-mcp-server:latest aztfexport version

# Get a shell for debugging
docker run --rm -it ghcr.io/liuwuliuyun/tf-mcp-server:latest /bin/bash
```

## Troubleshooting

### Common Issues

1. **MCP communication fails:**

   **All platforms (same commands):**
   ```bash
   # Check if server starts correctly
   echo '{"method":"get_avm_modules","params":{}}' | \
   docker run --rm -i ghcr.io/liuwuliuyun/tf-mcp-server:latest
   
   # Check container logs
   docker logs tf-mcp-server-instance
   ```

2. **Workspace mount issues:**

   **All platforms (same commands):**
   ```bash
   # Verify mount is working
   docker run --rm -i -v "$(pwd):/workspace" \
     ghcr.io/liuwuliuyun/tf-mcp-server:latest ls -la /workspace
   ```

3. **Permission issues:**

   **Linux/macOS:**
   ```bash
   # Check workspace permissions
   ls -la /path/to/your/workspace
   
   # Fix permissions if needed
   chmod -R 755 /path/to/your/workspace
   ```

   **Windows PowerShell:**
   ```powershell
   # Check workspace permissions
   Get-ChildItem -Path "C:\your\workspace" -Force
   
   # Ensure directory exists and is accessible
   New-Item -ItemType Directory -Path "C:\your\workspace" -Force
   ```

4. **Azure authentication issues:**

   **All platforms (same commands):**
   ```bash
   # Test Azure credentials
   docker run --rm -i \
     -e ARM_CLIENT_ID=your-client-id \
     -e ARM_CLIENT_SECRET=your-client-secret \
     -e ARM_SUBSCRIPTION_ID=your-subscription-id \
     -e ARM_TENANT_ID=your-tenant-id \
     ghcr.io/liuwuliuyun/tf-mcp-server:latest \
     az account show
   ```

### Debug Mode

Run container in debug mode:

**Linux/macOS:**
```bash
docker run --rm -i \
  -e LOG_LEVEL=DEBUG \
  -v "$(pwd):/workspace" \
  ghcr.io/liuwuliuyun/tf-mcp-server:latest
```

**Windows PowerShell:**
```powershell
docker run --rm -i `
  -e LOG_LEVEL=DEBUG `
  -v "${PWD}:/workspace" `
  ghcr.io/liuwuliuyun/tf-mcp-server:latest
```
## Best Practices

### MCP Server Usage

1. **Use --rm flag:** Always use `--rm` to automatically remove containers when they stop:
   ```bash
   docker run --rm -i ghcr.io/liuwuliuyun/tf-mcp-server:latest
   ```

2. **Mount workspace correctly:** Ensure your Terraform files are accessible:
   ```bash
   -v "$(pwd):/workspace"  # Current directory
   -v "/path/to/terraform:/workspace"  # Specific directory
   ```

3. **Set proper logging level:**
   ```bash
   -e LOG_LEVEL=INFO  # For production
   -e LOG_LEVEL=DEBUG  # For troubleshooting
   ```

4. **Secure Azure credentials:** Use environment variables or VS Code env substitution:
   ```bash
   -e ARM_CLIENT_ID=${ARM_CLIENT_ID}
   ```

## Updates and Maintenance

### Updating the Image

1. **Pull latest image:**
   ```bash
   docker pull ghcr.io/liuwuliuyun/tf-mcp-server:latest
   ```

2. **VS Code MCP:** Update automatically uses latest when restarting

3. **Manual usage:** Simply use the new image tag in your commands

### Backup

Important data to backup:
- Your Terraform configuration files
- Azure service principal credentials
- Custom policy files (if any)
- VS Code MCP configuration (`.vscode/mcp.json`)

## Support

For issues and questions:
- Check the troubleshooting section above  
- Review the main README.md for tool-specific help
- Test with debug logging: `-e LOG_LEVEL=DEBUG`
- Open an issue in the project repository
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
docker run --rm -i \
  -v $(pwd):/workspace \
  --security-opt no-new-privileges:true \
  --read-only \
  ghcr.io/liuwuliuyun/tf-mcp-server:latest
```

**Windows PowerShell:**
```powershell
docker run --rm -i `
  -v "$PWD:/workspace" `
  --security-opt no-new-privileges:true `
  --read-only `
  ghcr.io/liuwuliuyun/tf-mcp-server:latest
```

### Network Security

- No port exposure needed for MCP stdio transport
- MCP communication happens via stdin/stdout
- For HTTP mode (non-MCP), use proper network isolation

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
   docker run --rm -i \
     -v $(pwd):/workspace \
     --memory=1g \
     --cpus=0.5 \
     ghcr.io/liuwuliuyun/tf-mcp-server:latest
   ```

   **Windows PowerShell:**
   ```powershell
   docker run --rm -i `
     -v "$PWD:/workspace" `
     --memory=1g `
     --cpus=0.5 `
     ghcr.io/liuwuliuyun/tf-mcp-server:latest
   ```

3. **Configure log rotation:**

   **Linux/macOS:**
   ```bash
   docker run --rm -i \
     -v $(pwd):/workspace \
     --log-driver json-file \
     --log-opt max-size=10m \
     --log-opt max-file=3 \
     ghcr.io/liuwuliuyun/tf-mcp-server:latest
   ```

   **Windows PowerShell:**
   ```powershell
   docker run --rm -i `
     -v "$PWD:/workspace" `
     --log-driver json-file `
     --log-opt max-size=10m `
     --log-opt max-file=3 `
     ghcr.io/liuwuliuyun/tf-mcp-server:latest
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
   docker run --rm -i -v $(pwd):/workspace ghcr.io/liuwuliuyun/tf-mcp-server:latest
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