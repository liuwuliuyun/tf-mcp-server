# Installation Guide

This guide provides detailed installation instructions for the Azure Terraform MCP Server using different methods.

## 🚀 Choose Your Installation Method

| Method | Best For | Setup Time | What You Need |
|--------|----------|------------|---------------|
| **🐳 Docker** | VS Code MCP integration | 2 minutes | Docker + VS Code |
| **⚡ UV** | Development, customization | 5 minutes | Python 3.11+ |
| **🐍 Pip** | Traditional Python setup | 5 minutes | Python 3.11+ |

### 📋 What's the Difference?

- **Docker**: Run as MCP server for VS Code integration (stdio transport)
- **UV/Pip**: Run locally or as HTTP server for direct API access

**→ For VS Code MCP integration? Use Docker with stdio transport**

## 🐳 Option 1: Docker (For VS Code MCP Integration)

**What you need:**
- Docker installed and running
- VS Code with MCP support
- (Optional) Azure Service Principal for full functionality

**What's included automatically:**
- Python 3.11+ runtime
- All Python dependencies  
- TFLint (latest version)
- Conftest (latest version)
- aztfexport (latest version)
- Terraform CLI
- All security policies and configurations

### 1️⃣ Basic Setup (No Azure needed)
Perfect for trying out documentation features:

**Create docker command for VS Code MCP integration:**
```bash
# This is the command VS Code will run via MCP
docker run --rm -i -v /path/to/your/workspace:/workspace ghcr.io/liuwuliuyun/tf-mcp-server:latest
```

### 2️⃣ With Azure Service Principal (Recommended for production)

**For VS Code MCP integration with Azure features:**
```bash
# This is the command VS Code will run via MCP
docker run --rm -i \
  -v /path/to/your/workspace:/workspace \
  -e ARM_CLIENT_ID=your-client-id \
  -e ARM_CLIENT_SECRET=your-client-secret \
  -e ARM_SUBSCRIPTION_ID=your-subscription-id \
  -e ARM_TENANT_ID=your-tenant-id \
  ghcr.io/liuwuliuyun/tf-mcp-server:latest
```

### ✅ VS Code MCP Configuration:

Add this to your VS Code `mcp.json`:
```json
{
  "mcpServers": {
    "tf-mcp-server": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-v", "${workspaceFolder}:/workspace",
        "-e", "ARM_CLIENT_ID=your-client-id",
        "-e", "ARM_CLIENT_SECRET=your-client-secret", 
        "-e", "ARM_SUBSCRIPTION_ID=your-subscription-id",
        "-e", "ARM_TENANT_ID=your-tenant-id",
        "ghcr.io/liuwuliuyun/tf-mcp-server:latest"
      ]
    }
  }
}
```

**📦 What's in the Docker image:**
- **Runtime**: Python 3.11+, all dependencies
- **Tools**: TFLint, Conftest, aztfexport, Terraform CLI  
- **Policies**: Pre-loaded security validation rules
- **Transport**: FastMCP stdio for VS Code integration

**💡 Pro Tip**: For direct API access (not VS Code), see our [Docker guide](docker.md) for HTTP server setup.

## ⚡ Option 2: UV Installation (For Development)

**What you need:**

### 1️⃣ Install UV

**Windows PowerShell:**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2️⃣ Get the Code & Run
```bash
git clone https://github.com/liuwuliuyun/tf-mcp-server.git
cd tf-mcp-server
uv sync                    # Install dependencies
uv run tf-mcp-server      # Start the server
```

**For development with tests:**
```bash
uv sync --dev             # Install dev dependencies
uv run pytest            # Run tests
```


## 🐍 Option 3: Traditional Python Installation

**What you need:**

### Step-by-step:

**Linux/macOS:**
```bash
# 1. Get the code
git clone https://github.com/liuwuliuyun/tf-mcp-server.git
cd tf-mcp-server

# 2. Create virtual environment
python -m venv venv

# 3. Activate it
source venv/bin/activate

# 4. Install and run
pip install -e .
python -m tf_mcp_server
```

**Windows PowerShell:**
```powershell
# 1. Get the code
git clone https://github.com/liuwuliuyun/tf-mcp-server.git
Set-Location tf-mcp-server

# 2. Create virtual environment
python -m venv venv

# 3. Activate it
venv\Scripts\activate

# 4. Install and run
pip install -e .
python -m tf_mcp_server
```

## VS Code MCP Setup

Once you have the Docker command ready, configure VS Code MCP integration by creating or editing `mcp.json` in your workspace root:

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
        "-e", "ARM_CLIENT_ID=your-client-id",
        "-e", "ARM_CLIENT_SECRET=your-client-secret",
        "-e", "ARM_SUBSCRIPTION_ID=your-subscription-id", 
        "-e", "ARM_TENANT_ID=your-tenant-id",
        "ghcr.io/liuwuliuyun/tf-mcp-server:latest"
      ]
    }
  }
}
```

**💡 Note:** The MCP server uses stdio transport, not HTTP. VS Code communicates directly via stdin/stdout.


## 🔧 Optional Tools (For Full Features)

**Only needed for UV/Pip installations - Docker has these built-in!**

### TFLint (Static Analysis)

**Windows (Chocolatey):**
```powershell
choco install tflint
```

**macOS (Homebrew):**
```bash
brew install tflint
```

**Linux:**
```bash
curl -s https://raw.githubusercontent.com/terraform-linters/tflint/master/install_linux.sh | bash
```

### Conftest (Policy Validation)

**Windows (Scoop):**
```powershell
scoop install conftest
```

**macOS (Homebrew):**
```bash
brew install conftest
```

**Manual Download:**
Download from: https://github.com/open-policy-agent/conftest/releases

### Azure Export for Terraform (aztfexport)

**Windows (Chocolatey):**
```powershell
choco install aztfexport
```

**macOS (Homebrew):**
```bash
brew install aztfexport
```

**Linux/Manual Download:**
Download from: https://github.com/Azure/aztfexport/releases

### Terraform CLI

**All Platforms:**
Download from: https://www.terraform.io/downloads

## Configuration

### Environment Variables

For Azure-enabled features, configure these environment variables:

```bash
# Azure Authentication (Service Principal method)
export ARM_CLIENT_ID=<your_client_id>           # Required for Azure operations
export ARM_CLIENT_SECRET=<your_client_secret>   # Required for Azure operations  
export ARM_SUBSCRIPTION_ID=<your_subscription_id> # Required for Azure operations
export ARM_TENANT_ID=<your_tenant_id>           # Required for Azure operations

# Optional: GitHub token for enhanced AVM module access
export GITHUB_TOKEN=<your_github_token_here>

# Optional: Server configuration (for UV/Pip installations in HTTP mode)
export MCP_HOST=localhost          # Default: localhost
export MCP_PORT=8000              # Default: 8000
export MCP_DEBUG=false            # Default: false
export LOG_LEVEL=INFO             # Default: INFO
```

### Configuration File (.env.local)

For development with UV/Pip installations, create `.env.local`:

```bash
# Azure Authentication
ARM_CLIENT_ID=<your_client_id>
ARM_CLIENT_SECRET=<your_client_secret>
ARM_SUBSCRIPTION_ID=<your_subscription_id>
ARM_TENANT_ID=<your_tenant_id>

# Optional: GitHub token
GITHUB_TOKEN=<your_github_token_here>

# Optional: Development settings
MCP_HOST=localhost
MCP_PORT=8000
MCP_DEBUG=true
LOG_LEVEL=DEBUG
```

**Note:** For VS Code MCP integration with Docker, use environment variables in the MCP configuration rather than `.env.local` files.

## Troubleshooting

For comprehensive troubleshooting information, see the [Troubleshooting Guide](troubleshooting.md).

### Quick Fixes

1. **Docker Issues**
   ```bash
   # Verify Docker is running
   docker --version
   docker run hello-world
   
   # Test server image
   docker run --rm ghcr.io/liuwuliuyun/tf-mcp-server:latest --version
   ```

2. **Azure Authentication Issues**
   ```bash
   # Test Azure CLI authentication
   az account show
   
   # Test service principal
   az login --service-principal \
     --username $ARM_CLIENT_ID \
     --password $ARM_CLIENT_SECRET \
     --tenant $ARM_TENANT_ID
   ```

3. **VS Code MCP Integration**
   - Check VS Code MCP extension is installed and enabled
   - Verify `mcp.json` configuration is correct
   - Look at VS Code Developer Console for MCP logs

4. **Limited Functionality Without Authentication**
   
   **Works without Azure auth:**
   - AzureRM/AzAPI/AVM documentation
   - Terraform source code analysis
   - TFLint static analysis
   - Terraform command execution (with local auth)
   
   **Requires Azure authentication:**
   - Azure resource export (aztfexport)
   - Azure-specific best practices
   - Conftest policy validation with Azure context

### Debug Mode

Enable debug logging:

**Docker:**
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

**UV/Pip:**
```bash
export MCP_DEBUG=true
export LOG_LEVEL=DEBUG
uv run tf-mcp-server
```

Check logs in `tf-mcp-server.log` for detailed information.

## Next Steps

After installation:

1. **📖 Read the Documentation**: 
   - [Documentation Index](README.md) - Overview of all documentation
   - [API Reference](api-reference.md) - Complete tool reference
   - [Configuration Guide](configuration.md) - Advanced configuration options

2. **🔧 Configure VS Code MCP**: 
   - Add server configuration to your workspace `.vscode/mcp.json`
   - See examples in the VS Code MCP Setup section above

3. **🔐 Set up Azure Authentication** (for Azure features):
   - [Azure Authentication Guide](azure-authentication.md) - Detailed authentication setup
   - Configure service principal credentials
   - Test with basic Azure operations

4. **🧪 Test the Integration**:
   - Try basic tools like `get_avm_modules`
   - Test documentation lookup with `get_azurerm_provider_documentation`
   - Validate workspace with `run_terraform_command`

5. **🎯 Explore Key Features**:
   - [Azure Documentation Tools](azure-documentation-tools.md) - AzureRM, AzAPI, AVM docs
   - [Terraform Commands](terraform-commands.md) - Execute Terraform operations
   - [Security Policies](security-policies.md) - Policy-based validation
   - [Azure Export Integration](aztfexport-integration.md) - Export existing resources

6. **🔍 Advanced Usage**:
   - [Source Code Analysis](terraform-golang-source-tools.md) - Analyze provider implementations
   - [Azure Best Practices](azure-best-practices-tool.md) - Get Azure recommendations
   - [TFLint Integration](tflint-integration.md) - Static code analysis

### Quick Verification

Test your installation with these commands:

```json
// Test basic functionality (no Azure auth needed)
{
  "tool": "get_avm_modules",
  "arguments": {}
}

// Test Azure documentation (no Azure auth needed)  
{
  "tool": "get_azurerm_provider_documentation",
  "arguments": {
    "resource_type_name": "storage_account",
    "doc_type": "resource"
  }
}

// Test Azure integration (requires Azure auth)
{
  "tool": "check_aztfexport_installation",
  "arguments": {}
}
```

### Need Help?

- **📚 Documentation**: Check the [docs](README.md) directory for comprehensive guides
- **❓ Troubleshooting**: See the [Troubleshooting Guide](troubleshooting.md) for common issues
- **🐛 Issues**: Report bugs on the [GitHub repository](https://github.com/liuwuliuyun/tf-mcp-server/issues)
- **💬 Discussions**: Join community discussions for help and tips

### What's Next?

Once you have the server running:

- **🏗️ Export Existing Resources**: Use aztfexport to convert existing Azure infrastructure to Terraform
- **🛡️ Implement Security Policies**: Set up automated policy validation with Conftest
- **📊 Analyze Code Quality**: Use TFLint for static analysis and best practices
- **🔍 Explore Implementations**: Use source code analysis to understand how Terraform providers work
- **⚡ Optimize Workflows**: Integrate the tools into your CI/CD pipelines