# Troubleshooting Guide

This guide helps you diagnose and resolve common issues with the Azure Terraform MCP Server.

## 🚨 Quick Diagnostics

### Basic Health Check

1. **Test server startup:**
   ```bash
   docker run --rm ghcr.io/liuwuliuyun/tf-mcp-server:latest --version
   ```

2. **Test VS Code MCP connection:**
   - Open VS Code with MCP extension
   - Look for server connection in MCP logs
   - Try a simple tool call

3. **Test Azure authentication:**
   ```bash
   az account show
   ```

---

## 🔍 Common Issues

### 1. MCP Server Connection Issues

#### Symptoms
- VS Code MCP extension shows server as disconnected
- Tool calls timeout or fail
- "Server not responding" errors

#### Diagnosis
```json
# Test basic tool call
{
  "tool": "get_avm_modules",
  "arguments": {}
}
```

#### Solutions

**Check Docker setup:**
```bash
# Verify Docker is running
docker --version

# Test server image
docker run --rm ghcr.io/liuwuliuyun/tf-mcp-server:latest --test
```

**VS Code MCP configuration:**
```json
{
  "mcpServers": {
    "tf-mcp-server": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "--name", "tf-mcp-server-debug",
        "-v", "${workspaceFolder}:/workspace",
        "-e", "LOG_LEVEL=DEBUG",
        "ghcr.io/liuwuliuyun/tf-mcp-server:latest"
      ]
    }
  }
}
```

**Check VS Code logs:**
1. Open VS Code Command Palette (`Ctrl+Shift+P`)
2. Run "Developer: Open Extension Host Console"
3. Look for MCP-related messages

---

### 2. Azure Authentication Failures

#### Symptoms
- "Authentication failed" errors
- Azure resource export tools fail
- "Invalid credentials" messages

#### Diagnosis
```bash
# Test Azure CLI authentication
az account show
az account list-locations

# Test service principal
az login --service-principal \
  --username $ARM_CLIENT_ID \
  --password $ARM_CLIENT_SECRET \
  --tenant $ARM_TENANT_ID
```

#### Solutions

**Service Principal Issues:**
```bash
# Create new service principal
az ad sp create-for-rbac \
  --name "tf-mcp-server-$(date +%s)" \
  --role="Contributor" \
  --scopes="/subscriptions/${ARM_SUBSCRIPTION_ID}"

# Assign additional roles if needed
az role assignment create \
  --assignee $ARM_CLIENT_ID \
  --role "Reader" \
  --scope "/subscriptions/${ARM_SUBSCRIPTION_ID}"
```

**Environment Variable Issues:**
```bash
# Windows PowerShell
$env:ARM_CLIENT_ID="your-client-id"
$env:ARM_CLIENT_SECRET="your-client-secret"
$env:ARM_SUBSCRIPTION_ID="your-subscription-id"
$env:ARM_TENANT_ID="your-tenant-id"

# Verify variables are set
echo $env:ARM_CLIENT_ID

# Linux/macOS
export ARM_CLIENT_ID="your-client-id"
export ARM_CLIENT_SECRET="your-client-secret"
export ARM_SUBSCRIPTION_ID="your-subscription-id" 
export ARM_TENANT_ID="your-tenant-id"

# Verify variables are set
echo $ARM_CLIENT_ID
```

**Docker Environment Variables:**
```bash
# Test environment variable passing
docker run --rm -it \
  -e ARM_CLIENT_ID="$ARM_CLIENT_ID" \
  -e ARM_CLIENT_SECRET="$ARM_CLIENT_SECRET" \
  -e ARM_SUBSCRIPTION_ID="$ARM_SUBSCRIPTION_ID" \
  -e ARM_TENANT_ID="$ARM_TENANT_ID" \
  ghcr.io/liuwuliuyun/tf-mcp-server:latest \
  env | grep ARM
```

---

### 3. Terraform Command Failures

#### Symptoms
- Terraform init/plan/apply fails
- "Terraform not found" errors
- Provider installation issues

#### Diagnosis
```json
# Test Terraform installation
{
  "tool": "run_terraform_command",
  "arguments": {
    "command": "version",
    "workspace_folder": "."
  }
}
```

#### Solutions

**Workspace Issues:**
```bash
# Verify workspace structure
ls -la workspace/
# Should contain .tf files

# Create minimal test workspace
mkdir -p workspace/test
cat > workspace/test/main.tf << EOF
terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
  }
}

provider "azurerm" {
  features {}
}
EOF
```

**Provider Installation:**
```json
# Initialize with upgrade
{
  "tool": "run_terraform_command",
  "arguments": {
    "command": "init",
    "workspace_folder": "workspace/test",
    "upgrade": true
  }
}
```

---

### 4. Docker-Related Issues

#### Symptoms
- "Docker not found" errors
- Permission denied errors
- Container startup failures

#### Solutions

**Docker Installation:**
```bash
# Verify Docker installation
docker --version
docker run hello-world

# Linux: Fix permissions
sudo usermod -aG docker $USER
# Log out and back in
```

**Windows Docker Desktop:**
- Ensure Docker Desktop is running
- Check Windows containers vs Linux containers mode
- Verify WSL2 integration if using WSL

**Volume Mount Issues:**
```bash
# Test volume mounting
docker run --rm -it \
  -v $(pwd):/test \
  alpine:latest \
  ls -la /test

# Windows PowerShell
docker run --rm -it \
  -v ${PWD}:/test \
  alpine:latest \
  ls -la /test
```

---

### 5. Tool-Specific Issues

#### TFLint Issues

**Symptoms:**
- TFLint analysis fails
- Rules not loading
- Plugin errors

**Solutions:**
```bash
# Test TFLint installation in container
docker run --rm -it ghcr.io/liuwuliuyun/tf-mcp-server:latest tflint --version

# Check TFLint configuration
cat > .tflint.hcl << EOF
config {
  module = false
}

plugin "azurerm" {
  enabled = true
  version = "0.24.0"
  source  = "github.com/terraform-linters/tflint-ruleset-azurerm"
}
EOF
```

#### Conftest Issues

**Symptoms:**
- Policy validation fails
- Policies not found
- Rego syntax errors

**Solutions:**
```json
# Test Conftest installation
{
  "tool": "check_conftest_installation",
  "arguments": {}
}

# Test with minimal policy
{
  "tool": "run_conftest_workspace_validation",
  "arguments": {
    "workspace_folder": "workspace/test",
    "policy_set": "avmsec",
    "severity_filter": "high"
  }
}
```

#### aztfexport Issues

**Symptoms:**
- Export commands fail
- Resource not found errors
- Authentication issues

**Solutions:**
```json
# Test aztfexport installation
{
  "tool": "check_aztfexport_installation",
  "arguments": {}
}

# Test with simple resource export
{
  "tool": "export_azure_resource",
  "arguments": {
    "resource_id": "/subscriptions/your-sub-id/resourceGroups/test-rg",
    "dry_run": true
  }
}
```

---

## 🐛 Debug Mode

### Enable Debug Logging

**Environment Variables:**
```bash
export MCP_DEBUG=true
export LOG_LEVEL=DEBUG
```

**VS Code MCP config:**
```json
{
  "mcpServers": {
    "tf-mcp-server": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-v", "${workspaceFolder}:/workspace",
        "-e", "LOG_LEVEL=DEBUG",
        "-e", "MCP_DEBUG=true",
        "ghcr.io/liuwuliuyun/tf-mcp-server:latest"
      ]
    }
  }
}
```

### Debug Output Analysis

**Look for these log patterns:**
```
DEBUG: Server starting with config...
DEBUG: Tool call received: get_avm_modules
DEBUG: Azure authentication successful
ERROR: Failed to execute terraform command
```

### Collect Debug Information

```bash
# Create debug bundle
mkdir debug-info
cd debug-info

# System information
echo "=== SYSTEM INFO ===" > debug.log
uname -a >> debug.log
docker --version >> debug.log

# Environment variables
echo "=== ENVIRONMENT ===" >> debug.log
env | grep ARM >> debug.log
env | grep MCP >> debug.log

# Container logs
echo "=== CONTAINER LOGS ===" >> debug.log
docker logs tf-mcp-server-instance >> debug.log 2>&1

# VS Code logs (if applicable)
echo "=== VS CODE MCP LOGS ===" >> debug.log
# Copy from VS Code Developer Console
```

---

## 🔧 Performance Issues

### Slow Response Times

**Symptoms:**
- Tool calls take too long
- Timeouts occur frequently
- High CPU/memory usage

**Solutions:**

**Optimize Docker resources:**
```bash
# Increase Docker memory limit
docker run --rm -it \
  --memory=4g \
  --cpus=2 \
  -v $(pwd):/workspace \
  ghcr.io/liuwuliuyun/tf-mcp-server:latest
```

**Use caching:**
```bash
# Use persistent volumes for caching
docker volume create tf-mcp-cache
docker run --rm -it \
  -v $(pwd):/workspace \
  -v tf-mcp-cache:/app/cache \
  ghcr.io/liuwuliuyun/tf-mcp-server:latest
```

**Network optimization:**
```bash
# Use local network for Docker
docker run --rm -it \
  --network host \
  -v $(pwd):/workspace \
  ghcr.io/liuwuliuyun/tf-mcp-server:latest
```

---

## 🚀 Platform-Specific Issues

### Windows Issues

**Path Problems:**
```powershell
# Use forward slashes in VS Code config
"-v", "${workspaceFolder}:/workspace"

# Not backward slashes
"-v", "${workspaceFolder}:\\workspace"  # ❌ Wrong
```

**PowerShell Execution Policy:**
```powershell
# Allow script execution
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**WSL2 Integration:**
```bash
# Ensure Docker Desktop WSL2 integration is enabled
# Use WSL2 paths for volume mounts
docker run --rm -it \
  -v /mnt/c/Users/username/project:/workspace \
  ghcr.io/liuwuliuyun/tf-mcp-server:latest
```

### macOS Issues

**Docker Desktop Settings:**
- Enable "Use gRPC FUSE for file sharing"
- Increase resource allocations
- Enable Kubernetes if needed

**Permission Issues:**
```bash
# Fix volume mount permissions
chmod -R 755 workspace/
```

### Linux Issues

**Docker Socket Permissions:**
```bash
# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

**SELinux Issues:**
```bash
# Temporarily disable SELinux
sudo setenforce 0

# Or add SELinux labels to volumes
docker run --rm -it \
  -v $(pwd):/workspace:Z \
  ghcr.io/liuwuliuyun/tf-mcp-server:latest
```

---

## 📞 Getting Help

### Information to Provide

When seeking help, include:

1. **Environment Details:**
   - Operating system and version
   - Docker version
   - VS Code version and MCP extension version

2. **Configuration:**
   - MCP configuration (sanitized)
   - Environment variables (without secrets)
   - Docker run command used

3. **Error Details:**
   - Full error messages
   - Debug logs
   - Steps to reproduce

4. **Context:**
   - What you were trying to do
   - Expected vs actual behavior
   - When the issue started

### Support Channels

1. **GitHub Issues:** [Report bugs and feature requests](https://github.com/liuwuliuyun/tf-mcp-server/issues)
2. **Documentation:** Check existing documentation for solutions
3. **Community Discussions:** Join community discussions for help

### Self-Help Resources

1. **Enable debug logging** and analyze output
2. **Check recent changes** to configuration or environment
3. **Test with minimal configuration** to isolate issues
4. **Review similar issues** in GitHub repository
5. **Verify prerequisites** are properly installed

---

## ✅ Health Check Script

Create a health check script to verify everything is working:

```bash
#!/bin/bash
echo "=== Azure Terraform MCP Server Health Check ==="

# Check Docker
echo "Checking Docker..."
docker --version || echo "❌ Docker not found"

# Check Azure CLI
echo "Checking Azure CLI..."
az --version || echo "⚠️  Azure CLI not found (optional)"

# Check environment variables
echo "Checking environment variables..."
[ -n "$ARM_CLIENT_ID" ] && echo "✅ ARM_CLIENT_ID set" || echo "⚠️  ARM_CLIENT_ID not set"
[ -n "$ARM_CLIENT_SECRET" ] && echo "✅ ARM_CLIENT_SECRET set" || echo "⚠️  ARM_CLIENT_SECRET not set"
[ -n "$ARM_SUBSCRIPTION_ID" ] && echo "✅ ARM_SUBSCRIPTION_ID set" || echo "⚠️  ARM_SUBSCRIPTION_ID not set"
[ -n "$ARM_TENANT_ID" ] && echo "✅ ARM_TENANT_ID set" || echo "⚠️  ARM_TENANT_ID not set"

# Test server image
echo "Testing server image..."
docker run --rm ghcr.io/liuwuliuyun/tf-mcp-server:latest --version && echo "✅ Server image works" || echo "❌ Server image failed"

echo "=== Health check complete ==="
```

---

## 🔗 Related Documentation

- **[Configuration Guide](configuration.md)**: Complete configuration reference
- **[Installation Guide](installation.md)**: Installation instructions
- **[Azure Authentication](azure-authentication.md)**: Authentication setup
- **[API Reference](api-reference.md)**: Tool reference and examples