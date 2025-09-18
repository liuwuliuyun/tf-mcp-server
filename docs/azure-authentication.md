## Azure Authentication

### Overview

The Azure Terraform MCP Server can operate in different modes depending on your Azure authentication setup:

- **🔓 No Authentication**: Basic documentation retrieval, HCL formatting, and static analysis work without Azure credentials
- **🔐 With Authentication**: Full functionality including Terraform plan execution, Azure resource analysis, and Conftest policy validation

### Authentication Methods

#### Method 1: Azure CLI Authentication (Recommended for Development)

First, authenticate with Azure CLI:
```bash
# Install Azure CLI (if not already installed)
# Windows
winget install Microsoft.AzureCLI
# macOS  
brew install azure-cli
# Linux
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Login to Azure
az login

# Set default subscription (optional)
az account set --subscription "<subscription-id>"

# Verify authentication
az account show
```

**Docker with Azure CLI:**
```bash
# Mount Azure CLI credentials
docker run -d \
  --name tf-mcp-server \
  -p 8000:8000 \
  -v ~/.azure:/home/mcpuser/.azure:ro \
  ghcr.io/liuwuliuyun/tf-mcp-server:latest
```

**MCP Configuration for VS Code:**
```json
{
  "command": "docker",
  "args": [
    "run", "-d", "--name", "azure-terraform-mcp-server", "-p", "8000:8000",
    "-v", "~/.azure:/home/mcpuser/.azure:ro",
    "ghcr.io/liuwuliuyun/tf-mcp-server:latest"
  ],
  "env": {
    "MCP_SERVER_HOST": "0.0.0.0",
    "MCP_SERVER_PORT": "8000"
  },
  "transport": "http",
  "host": "localhost",
  "port": 8000
}
```

#### Method 2: Service Principal Authentication (Recommended for Production)

Create a service principal:
```bash
# Create service principal
az ad sp create-for-rbac --name "terraform-mcp-server" --role "Contributor"

# Output will include:
# - appId (ARM_CLIENT_ID)
# - password (ARM_CLIENT_SECRET)  
# - tenant (ARM_TENANT_ID)
# Get your subscription ID:
az account show --query id -o tsv
```

**Docker with Service Principal:**
```bash
docker run -d \
  --name tf-mcp-server \
  -p 8000:8000 \
  -e ARM_CLIENT_ID=<your_client_id> \
  -e ARM_CLIENT_SECRET=<your_client_secret> \
  -e ARM_SUBSCRIPTION_ID=<your_subscription_id> \
  -e ARM_TENANT_ID=<your_tenant_id> \
  ghcr.io/liuwuliuyun/tf-mcp-server:latest
```

**MCP Configuration for VS Code:**
```json
{
  "command": "docker",
  "args": [
    "run", "-d", "--name", "azure-terraform-mcp-server", "-p", "8000:8000",
    "ghcr.io/liuwuliuyun/tf-mcp-server:latest"
  ],
  "env": {
    "ARM_CLIENT_ID": "<your_client_id>",
    "ARM_CLIENT_SECRET": "<your_client_secret>",
    "ARM_SUBSCRIPTION_ID": "<your_subscription_id>",
    "ARM_TENANT_ID": "<your_tenant_id>",
    "MCP_SERVER_HOST": "0.0.0.0",
    "MCP_SERVER_PORT": "8000"
  },
  "transport": "http", 
  "host": "localhost",
  "port": 8000
}
```

#### Method 3: Managed Identity (For Azure VMs)

When running on Azure VMs with managed identity:
```bash
# No additional authentication needed - uses VM's managed identity
docker run -d \
  --name tf-mcp-server \
  -p 8000:8000 \
  ghcr.io/liuwuliuyun/tf-mcp-server:latest
```

### Feature Availability by Authentication Mode

| Feature | No Auth | Azure CLI | Service Principal | Managed Identity |
|---------|---------|-----------|-------------------|------------------|
| 📖 AzureRM Documentation | ✅ | ✅ | ✅ | ✅ |
| 📖 AzAPI Documentation | ✅ | ✅ | ✅ | ✅ |
| 📖 AVM Module Info | ✅ | ✅ | ✅ | ✅ |
| 🔍 TFLint Analysis | ✅ | ✅ | ✅ | ✅ |
| 📝 HCL Formatting | ✅ | ✅ | ✅ | ✅ |
| ✅ HCL Validation | ✅ | ✅ | ✅ | ✅ |
| 🛡️ Conftest Validation | ❌ | ✅ | ✅ | ✅ |
| ⚙️ Terraform Plan | ❌ | ✅ | ✅ | ✅ |
| 🚀 Terraform Apply | ❌ | ✅ | ✅ | ✅ |
| 🔍 Resource Analysis | ❌ | ✅ | ✅ | ✅ |

### Docker Compose with Authentication

Create a `docker-compose.yml` with your preferred authentication method:

**With Azure CLI (Development):**
```yaml
version: '3.8'
services:
  tf-mcp-server:
    image: ghcr.io/liuwuliuyun/tf-mcp-server:latest
    container_name: tf-mcp-server
    ports:
      - "8000:8000"
    volumes:
      - ~/.azure:/home/mcpuser/.azure:ro
    environment:
      - MCP_SERVER_HOST=0.0.0.0
      - MCP_SERVER_PORT=8000
    restart: unless-stopped
```

**With Service Principal (Production):**
```yaml
version: '3.8'
services:
  tf-mcp-server:
    image: ghcr.io/liuwuliuyun/tf-mcp-server:latest
    container_name: tf-mcp-server
    ports:
      - "8000:8000"
    environment:
      - ARM_CLIENT_ID=${ARM_CLIENT_ID}
      - ARM_CLIENT_SECRET=${ARM_CLIENT_SECRET}
      - ARM_SUBSCRIPTION_ID=${ARM_SUBSCRIPTION_ID}
      - ARM_TENANT_ID=${ARM_TENANT_ID}
      - MCP_SERVER_HOST=0.0.0.0
      - MCP_SERVER_PORT=8000
    restart: unless-stopped
```

Create a `.env` file for the service principal method:
```bash
ARM_CLIENT_ID=your_client_id_here
ARM_CLIENT_SECRET=your_client_secret_here
ARM_SUBSCRIPTION_ID=your_subscription_id_here
ARM_TENANT_ID=your_tenant_id_here
```