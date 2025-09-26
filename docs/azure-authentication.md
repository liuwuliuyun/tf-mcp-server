## Azure Authentication

### Overview

The Azure Terraform MCP Server can operate in different modes depending on your Azure authentication setup:

- **🔓 No Authentication**: Basic documentation retrieval, HCL formatting, and static analysis work without Azure credentials
- **🔐 With Authentication**: Full functionality including Terraform plan execution, Azure resource analysis, and Conftest policy validation

### Authentication Methods

#### Service Principal Authentication (Required)

Create a service principal using Azure Portal or Azure PowerShell:

**Using Azure Portal:**
1. Go to Azure Active Directory > App registrations
2. Click "New registration"
3. Provide a name for your application
4. Select account types (usually "Accounts in this organizational directory only")
5. Click "Register"
6. Note the "Application (client) ID" and "Directory (tenant) ID"
7. Go to "Certificates & secrets" > "New client secret"
8. Create a secret and note the value (this is your ARM_CLIENT_SECRET)
9. Go to your subscription > Access control (IAM) > Add role assignment
10. Assign "Contributor" role to your service principal

**Using Azure PowerShell:**
```powershell
# Connect to Azure
Connect-AzAccount

# Create service principal
$sp = New-AzADServicePrincipal -DisplayName "terraform-mcp-server" -Role "Contributor"

# Get the values you need:
# - Application ID: $sp.AppId (ARM_CLIENT_ID)
# - Secret: $sp.PasswordCredentials.SecretText (ARM_CLIENT_SECRET)
# - Tenant ID: (Get-AzContext).Tenant.Id (ARM_TENANT_ID)
# - Subscription ID: (Get-AzContext).Subscription.Id (ARM_SUBSCRIPTION_ID)
```

**Docker with Service Principal (VS Code MCP):**
```bash
docker run --rm -i \
  -v $(pwd):/workspace \
  -e ARM_CLIENT_ID=<your_client_id> \
  -e ARM_CLIENT_SECRET=<your_client_secret> \
  -e ARM_SUBSCRIPTION_ID=<your_subscription_id> \
  -e ARM_TENANT_ID=<your_tenant_id> \
  ghcr.io/liuwuliuyun/tf-mcp-server:latest
```

**MCP Configuration for VS Code:**
```json
{
  "mcpServers": {
    "tf-mcp-server": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-v", "${workspaceFolder}:/workspace",
        "-e", "ARM_CLIENT_ID=<your_client_id>",
        "-e", "ARM_CLIENT_SECRET=<your_client_secret>",
        "-e", "ARM_SUBSCRIPTION_ID=<your_subscription_id>",
        "-e", "ARM_TENANT_ID=<your_tenant_id>",
        "ghcr.io/liuwuliuyun/tf-mcp-server:latest"
      ]
    }
  }
}
```

#### Managed Identity Authentication (Azure Resources Only)

When running on Azure VMs with managed identity:
```bash
# For VS Code MCP integration (no additional authentication needed)  
docker run --rm -i \
  -v $(pwd):/workspace \
  ghcr.io/liuwuliuyun/tf-mcp-server:latest
```

### Feature Availability by Authentication Mode

| Feature | No Auth | Service Principal | Managed Identity |
|---------|---------|-------------------|------------------|
| Documentation | ✅ | ✅ | ✅ |
| HCL Formatting | ✅ | ✅ | ✅ |
| Static Analysis | ✅ | ✅ | ✅ |
| Terraform Plan | ❌ | ✅ | ✅ |
| Azure Resource Export | ❌ | ✅ | ✅ |
| Policy Validation | ❌ | ✅ | ✅ |
| Use Case | Development/Testing | Production/Automation | Azure Resources |

### Docker Compose with Authentication

**💡 Note:** Docker Compose is for HTTP server mode, not VS Code MCP integration.

Create a `docker-compose.yml` with your preferred authentication method:

**With Service Principal:**
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
      - ARM_CLIENT_ID=your-client-id
      - ARM_CLIENT_SECRET=your-client-secret
      - ARM_SUBSCRIPTION_ID=your-subscription-id
      - ARM_TENANT_ID=your-tenant-id
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