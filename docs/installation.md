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

## Configuration

### Environment Variables (For UV/Pip installations)
```bash
# Azure authentication (Service Principal method)
export ARM_CLIENT_ID=<your_client_id>           # Required for Azure operations
export ARM_CLIENT_SECRET=<your_client_secret>   # Required for Azure operations  
export ARM_SUBSCRIPTION_ID=<your_subscription_id> # Required for Azure operations
export ARM_TENANT_ID=<your_tenant_id>           # Required for Azure operations

# Optional: GitHub token for AVM module access (to avoid rate limiting)
export GITHUB_TOKEN=<your_github_token_here>

# For HTTP server mode (non-MCP)
export MCP_HOST=localhost          # Default: localhost
export MCP_PORT=8000              # Default: 8000
export MCP_DEBUG=false            # Default: false
```

### Configuration File (.env.local)
Create a `.env.local` file in the project root for local configuration:
```bash
# Azure authentication (Service Principal method)
ARM_CLIENT_ID=<your_client_id>
ARM_CLIENT_SECRET=<your_client_secret>
ARM_SUBSCRIPTION_ID=<your_subscription_id>
ARM_TENANT_ID=<your_tenant_id>

# Optional: GitHub token for AVM module access (to avoid rate limiting)
GITHUB_TOKEN=<your_github_token_here>

# For HTTP server mode (non-MCP) - only needed for UV/Pip installations
MCP_HOST=localhost
MCP_PORT=8000
MCP_DEBUG=false
```

## Troubleshooting

### Common Installation Issues

1. **Import Errors**
   ```bash
   # Make sure dependencies are installed
   pip install -r requirements.txt
   ```

2. **Port Conflicts (UV/Pip HTTP mode only)**
   ```bash
   # Change port via environment variable
   export MCP_PORT=8002
   python main.py
   ```

3. **Missing Dependencies**
   ```bash
   # Install optional dependencies
   pip install beautifulsoup4
   ```

4. **AVM Module Access Issues**
   ```bash
   # If you encounter GitHub API rate limiting for AVM modules
   export GITHUB_TOKEN=your_github_token_here
   
   # Clear AVM cache if modules seem outdated (cache expires after 24 hours)
   rm -rf __avm_data_cache__
   ```

5. **Azure Authentication Issues**
   ```bash
   # Verify service principal environment variables are set
   echo $ARM_CLIENT_ID $ARM_CLIENT_SECRET $ARM_SUBSCRIPTION_ID $ARM_TENANT_ID
   
   # Test authentication with Azure REST API
   curl -X POST "https://login.microsoftonline.com/$ARM_TENANT_ID/oauth2/v2.0/token" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "grant_type=client_credentials&client_id=$ARM_CLIENT_ID&client_secret=$ARM_CLIENT_SECRET&scope=https://management.azure.com/.default"
   ```

6. **Limited Functionality Without Authentication**
   
   If you see errors like "Azure credentials not found" or tools fail with authentication errors:
   - **Documentation tools work**: AzureRM docs, AzAPI docs, AVM module info, TFLint analysis, HCL formatting
   - **These tools require Azure auth**: Terraform plan/apply, Conftest validation, resource analysis
   - **Solution**: Set up authentication using one of the methods in the Configuration section above

7. **Windows Path Length Limitations**
   ```powershell
   # If you encounter path length issues on Windows when extracting AVM modules
   # Run this PowerShell command as Administrator to enable long paths:
   Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1
   ```

### Debug Mode

Enable debug logging:
```bash
export MCP_DEBUG=true
python main.py
```

Check logs in `tf-mcp-server.log` for detailed information.

## Next Steps

After installation:
1. **Configure VS Code MCP**: Add the server configuration to your workspace `mcp.json`
2. **Set up Azure authentication**: Configure service principal credentials (if using Azure features)
3. **Test the integration**: Try the MCP tools in VS Code
4. **Explore the tools**: Check out the [main README](../README.md) for available tools and usage examples

For more information:
- **VS Code MCP integration**: See the [main README](../README.md) 
- **Docker deployment patterns**: See the [Docker guide](docker.md)
- **Azure authentication setup**: See the [Azure authentication guide](azure-authentication.md)