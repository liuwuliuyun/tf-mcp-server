# Configuration Guide

This guide covers all configuration options for the Azure Terraform MCP Server.

## 🔧 Configuration Methods

The server supports multiple configuration approaches:
- **Environment Variables** (recommended for MCP integration)
- **Configuration Files** (for development)
- **Runtime Parameters** (for testing)

---

## 🌍 Environment Variables

### Core MCP Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `MCP_HOST` | Server host address | `localhost` | No |
| `MCP_PORT` | Server port number | `8000` | No |
| `MCP_DEBUG` | Enable debug logging | `false` | No |
| `LOG_LEVEL` | Logging level | `INFO` | No |

### Azure Authentication

| Variable | Description | Required |
|----------|-------------|----------|
| `ARM_CLIENT_ID` | Azure service principal client ID | Yes* |
| `ARM_CLIENT_SECRET` | Azure service principal client secret | Yes* |
| `ARM_SUBSCRIPTION_ID` | Azure subscription ID | Yes* |
| `ARM_TENANT_ID` | Azure tenant ID | Yes* |

*Required for Azure operations (export, authentication-based features)

### Optional Tool Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `TERRAFORM_VERSION` | Preferred Terraform version | `latest` |
| `TFLINT_VERSION` | Preferred TFLint version | `latest` |
| `CONFTEST_VERSION` | Preferred Conftest version | `latest` |
| `AZTFEXPORT_VERSION` | Preferred aztfexport version | `latest` |

---

## 📁 Configuration Files

### Development Configuration

Create `.env.local` for local development:

```bash
# MCP Configuration
MCP_HOST=localhost
MCP_PORT=8000
MCP_DEBUG=true
LOG_LEVEL=DEBUG

# Azure Authentication
ARM_CLIENT_ID=your-service-principal-id
ARM_CLIENT_SECRET=your-service-principal-secret
ARM_SUBSCRIPTION_ID=your-subscription-id
ARM_TENANT_ID=your-tenant-id

# Optional Tool Versions
TERRAFORM_VERSION=1.6.0
TFLINT_VERSION=0.48.0
CONFTEST_VERSION=0.46.0
```

### VS Code MCP Configuration

**Basic configuration (.vscode/mcp.json):**
```json
{
  "mcpServers": {
    "tf-mcp-server": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-v", "${workspaceFolder}:/workspace",
        "ghcr.io/liuwuliuyun/tf-mcp-server:latest"
      ]
    }
  }
}
```

**With Azure credentials:**
```json
{
  "mcpServers": {
    "tf-mcp-server": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
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

**Advanced configuration with custom settings:**
```json
{
  "mcpServers": {
    "tf-mcp-server": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "--name", "tf-mcp-server-instance",
        "-v", "${workspaceFolder}:/workspace",
        "-v", "tf-mcp-cache:/app/cache",
        "-e", "ARM_CLIENT_ID=${env:ARM_CLIENT_ID}",
        "-e", "ARM_CLIENT_SECRET=${env:ARM_CLIENT_SECRET}",
        "-e", "ARM_SUBSCRIPTION_ID=${env:ARM_SUBSCRIPTION_ID}",
        "-e", "ARM_TENANT_ID=${env:ARM_TENANT_ID}",
        "-e", "LOG_LEVEL=DEBUG",
        "-e", "MCP_DEBUG=true",
        "ghcr.io/liuwuliuyun/tf-mcp-server:latest"
      ]
    }
  }
}
```

---

## 🔐 Azure Authentication Setup

### Method 1: Service Principal (Recommended)

1. **Create Service Principal:**
   ```bash
   az ad sp create-for-rbac --name "terraform-mcp-server" --role="Contributor"
   ```

2. **Set Environment Variables:**
   ```bash
   export ARM_CLIENT_ID="<service-principal-app-id>"
   export ARM_CLIENT_SECRET="<service-principal-password>"
   export ARM_SUBSCRIPTION_ID="<subscription-id>"
   export ARM_TENANT_ID="<tenant-id>"
   ```

3. **Windows PowerShell:**
   ```powershell
   $env:ARM_CLIENT_ID="<service-principal-app-id>"
   $env:ARM_CLIENT_SECRET="<service-principal-password>"
   $env:ARM_SUBSCRIPTION_ID="<subscription-id>"
   $env:ARM_TENANT_ID="<tenant-id>"
   ```

### Method 2: Azure CLI (Development Only)

```bash
az login
az account set --subscription "your-subscription-id"
```

### Method 3: Managed Identity (Azure-hosted)

For Azure-hosted deployments:
```bash
export ARM_USE_MSI=true
export ARM_SUBSCRIPTION_ID="<subscription-id>"
```

---

## 🐳 Docker Configuration

### Environment Variables

```bash
# Basic Docker run with Azure auth
docker run -it --rm \
  -v $(pwd):/workspace \
  -e ARM_CLIENT_ID="$ARM_CLIENT_ID" \
  -e ARM_CLIENT_SECRET="$ARM_CLIENT_SECRET" \
  -e ARM_SUBSCRIPTION_ID="$ARM_SUBSCRIPTION_ID" \
  -e ARM_TENANT_ID="$ARM_TENANT_ID" \
  ghcr.io/liuwuliuyun/tf-mcp-server:latest
```

### Docker Compose

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  tf-mcp-server:
    image: ghcr.io/liuwuliuyun/tf-mcp-server:latest
    volumes:
      - ./workspace:/workspace
      - tf-cache:/app/cache
    environment:
      - ARM_CLIENT_ID=${ARM_CLIENT_ID}
      - ARM_CLIENT_SECRET=${ARM_CLIENT_SECRET}
      - ARM_SUBSCRIPTION_ID=${ARM_SUBSCRIPTION_ID}
      - ARM_TENANT_ID=${ARM_TENANT_ID}
      - LOG_LEVEL=INFO
      - MCP_DEBUG=false
    stdin_open: true
    tty: true

volumes:
  tf-cache:
```

### Persistent Storage

```bash
# Create named volume for caching
docker volume create tf-mcp-cache

# Use in docker run
docker run -it --rm \
  -v $(pwd):/workspace \
  -v tf-mcp-cache:/app/cache \
  ghcr.io/liuwuliuyun/tf-mcp-server:latest
```

---

## 🛠️ Development Configuration

### UV Development Setup

```bash
# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and setup
git clone https://github.com/liuwuliuyun/tf-mcp-server.git
cd tf-mcp-server

# Install dependencies
uv sync --dev

# Configure environment
cp .env.example .env.local
# Edit .env.local with your settings

# Run in development mode
uv run tf-mcp-server
```

### Python Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows

# Install development dependencies
pip install -e ".[dev]"

# Configure environment
export MCP_DEBUG=true
export LOG_LEVEL=DEBUG

# Run
python -m tf_mcp_server
```

---

## 📊 Logging Configuration

### Log Levels

| Level | Description | Use Case |
|-------|-------------|----------|
| `DEBUG` | Detailed debugging information | Development, troubleshooting |
| `INFO` | General operational messages | Production monitoring |
| `WARNING` | Warning messages | Issue detection |
| `ERROR` | Error messages only | Production, minimal logging |

### Log Formats

**Development (human-readable):**
```bash
export LOG_LEVEL=DEBUG
export MCP_DEBUG=true
```

**Production (structured):**
```bash
export LOG_LEVEL=INFO
export LOG_FORMAT=json
```

### Log Destinations

**Console output (default):**
```bash
python -m tf_mcp_server
```

**File output:**
```bash
python -m tf_mcp_server 2>&1 | tee tf-mcp-server.log
```

**Structured logging with timestamps:**
```bash
export LOG_FORMAT=json
python -m tf_mcp_server | jq .
```

---

## ⚙️ Tool-Specific Configuration

### TFLint Configuration

Create `.tflint.hcl` in your workspace:
```hcl
config {
  module = false
}

plugin "azurerm" {
  enabled = true
  version = "0.24.0"
  source  = "github.com/terraform-linters/tflint-ruleset-azurerm"
}

rule "azurerm_resource_missing_tags" {
  enabled = true
  tags = ["Environment", "Project", "Owner"]
}
```

### Conftest Configuration

The server includes pre-configured policies, but you can customize:
```bash
# Custom policy directory
export CONFTEST_POLICY_DIR="/path/to/custom/policies"
```

### aztfexport Configuration

```bash
# Disable telemetry
aztfexport config set telemetry_enabled false

# Or via tool
{
  "tool": "set_aztfexport_config",
  "arguments": {
    "key": "telemetry_enabled",
    "value": "false"
  }
}
```

---

## 🔍 Configuration Validation

### Test Configuration

```bash
# Test MCP server
python -m tf_mcp_server --test-config

# Test Azure authentication
az account show

# Test Docker setup
docker run --rm ghcr.io/liuwuliuyun/tf-mcp-server:latest --version
```

### Validate VS Code MCP

1. Open VS Code
2. Check MCP extension logs
3. Look for connection success messages
4. Test a simple tool call

### Common Validation Commands

```json
# Test basic functionality
{
  "tool": "get_avm_modules",
  "arguments": {}
}

# Test Azure authentication
{
  "tool": "check_aztfexport_installation", 
  "arguments": {}
}

# Test workspace operations
{
  "tool": "run_terraform_command",
  "arguments": {
    "command": "version",
    "workspace_folder": "."
  }
}
```

---

## 🔧 Platform-Specific Configuration

### Windows

**PowerShell environment variables:**
```powershell
$env:ARM_CLIENT_ID="your-client-id"
$env:ARM_CLIENT_SECRET="your-client-secret"
$env:ARM_SUBSCRIPTION_ID="your-subscription-id"
$env:ARM_TENANT_ID="your-tenant-id"
```

**Windows Docker paths:**
```json
{
  "mcpServers": {
    "tf-mcp-server": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-v", "${workspaceFolder}:/workspace:ro",
        "ghcr.io/liuwuliuyun/tf-mcp-server:latest"
      ]
    }
  }
}
```

### Linux/macOS

**Shell environment setup:**
```bash
# Add to ~/.bashrc or ~/.zshrc
export ARM_CLIENT_ID="your-client-id"
export ARM_CLIENT_SECRET="your-client-secret"
export ARM_SUBSCRIPTION_ID="your-subscription-id"
export ARM_TENANT_ID="your-tenant-id"

# Source the file
source ~/.bashrc
```

### WSL2

**Special considerations:**
```bash
# Use WSL2 paths in VS Code
"${workspaceFolder}" automatically resolves

# For manual docker runs:
docker run -it --rm \
  -v /mnt/c/your/project:/workspace \
  ghcr.io/liuwuliuyun/tf-mcp-server:latest
```

---

## 📋 Configuration Checklist

### ✅ Basic Setup
- [ ] Environment variables set
- [ ] Docker/Python environment working
- [ ] VS Code MCP configuration created
- [ ] Basic tool test successful

### ✅ Azure Integration  
- [ ] Service principal created
- [ ] Azure credentials configured
- [ ] Azure CLI login working (if used)
- [ ] Azure tool test successful

### ✅ Security
- [ ] Credentials stored securely
- [ ] No credentials in configuration files
- [ ] Appropriate RBAC permissions set
- [ ] Network access configured

### ✅ Performance
- [ ] Appropriate log level set
- [ ] Caching configured (if needed)
- [ ] Resource limits set (Docker)
- [ ] Monitoring configured

---

## 🔗 Related Documentation

- **[Installation Guide](installation.md)**: Complete installation instructions
- **[Azure Authentication](azure-authentication.md)**: Detailed authentication setup
- **[Docker Guide](docker.md)**: Docker-specific configuration
- **[Troubleshooting](troubleshooting.md)**: Configuration issue resolution