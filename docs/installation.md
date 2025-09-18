# Installation Guide

This guide provides detailed installation instructions for the Azure Terraform MCP Server using different methods.

## 🚀 Choose Your Installation Method

| Method | Best For | Setup Time | What You Need |
|--------|----------|------------|---------------|
| **🐳 Docker** | Production, quick start | 2 minutes | Docker only |
| **⚡ UV** | Development, customization | 5 minutes | Python 3.11+ |
| **🐍 Pip** | Traditional Python setup | 5 minutes | Python 3.11+ |

### 📋 What's the Difference?

- **🐳 Docker (Recommended)**: Everything pre-installed, just run one command
- **⚡ UV**: Modern Python package manager, great for development  
- **🐍 Pip**: Traditional Python setup, works everywhere

**→ New to this? Start with Docker** - it's the easiest way to get running immediately.

## 🐳 Option 1: Docker (Easiest & Recommended)

**What you need:**
- ✅ Docker installed on your computer
- ✅ Azure CLI (only if you want Azure authentication) - [Install guide](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli)

**What's included automatically:**
- ✅ Python, Terraform, TFLint, Conftest - all pre-installed
- ✅ No manual setup required

### 1️⃣ Basic Setup (No Azure needed)
Perfect for trying out documentation features:

**Linux/macOS:**
```bash
docker run -d --name tf-mcp-server -p 8000:8000 ghcr.io/liuwuliuyun/tf-mcp-server:latest
```

**Windows PowerShell:**
```powershell
docker run -d --name tf-mcp-server -p 8000:8000 ghcr.io/liuwuliuyun/tf-mcp-server:latest
```

### 2️⃣ With Azure CLI (Recommended for development)
First, login to Azure: `az login`, then:

**Linux/macOS:**
```bash
docker run -d --name tf-mcp-server -p 8000:8000 -v ~/.azure:/home/mcpuser/.azure:ro ghcr.io/liuwuliuyun/tf-mcp-server:latest
```

**Windows PowerShell:**
```powershell
docker run -d --name tf-mcp-server -p 8000:8000 -v "$env:USERPROFILE\.azure:/home/mcpuser/.azure:ro" ghcr.io/liuwuliuyun/tf-mcp-server:latest
```

### 3️⃣ With Service Principal (For production)

**Linux/macOS:**
```bash
docker run -d --name tf-mcp-server -p 8000:8000 \
  -e ARM_CLIENT_ID=<your_client_id> \
  -e ARM_CLIENT_SECRET=<your_client_secret> \
  -e ARM_SUBSCRIPTION_ID=<your_subscription_id> \
  -e ARM_TENANT_ID=<your_tenant_id> \
  ghcr.io/liuwuliuyun/tf-mcp-server:latest
```

**Windows PowerShell:**
```powershell
docker run -d --name tf-mcp-server -p 8000:8000 `
  -e ARM_CLIENT_ID=<your_client_id> `
  -e ARM_CLIENT_SECRET=<your_client_secret> `
  -e ARM_SUBSCRIPTION_ID=<your_subscription_id> `
  -e ARM_TENANT_ID=<your_tenant_id> `
  ghcr.io/liuwuliuyun/tf-mcp-server:latest
```

### ✅ Verify it's working:

**Linux/macOS:**
```bash
curl http://localhost:8000/health
# Should return: {"status": "healthy"}
```

**Windows PowerShell:**
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/health"
# Should return: {"status": "healthy"}
```

**📦 What's in the Docker image:**
- ✅ Python 3.11+, Terraform, TFLint, Conftest
- ✅ Alpine Linux (lightweight & secure)
- ✅ Multi-platform support (Intel & Apple Silicon)
- ✅ Auto-built from latest code

---

## ⚡ Option 2: UV Installation (For Development)

**What you need:**
- ✅ Python 3.11 or higher
- ✅ Git
- ⚠️ Optional: [TFLint](https://github.com/terraform-linters/tflint), [Conftest](https://www.conftest.dev/) for full features

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

---

## 🐍 Option 3: Traditional Python Installation

**What you need:**
- ✅ Python 3.11 or higher
- ✅ pip (usually comes with Python)
- ⚠️ Optional: [TFLint](https://github.com/terraform-linters/tflint), [Conftest](https://www.conftest.dev/)

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

## VS Code Setup

Once your server is running, create or edit `.vscode/mcp.json` in your workspace:

```json
{
    "servers": {
        "Azure Terraform MCP Server": {
            "url": "http://localhost:8000/mcp/"
        }
    }
}
```

**💡 Note:** The server runs on port `8000` by default. Make sure the URL matches your server's actual port.

---

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

### Environment Variables
```bash
# Server configuration
export MCP_HOST=localhost          # Default: localhost
export MCP_PORT=8000              # Default: 8000
export MCP_DEBUG=false            # Default: false

# Azure authentication (Service Principal method)
export ARM_CLIENT_ID=<your_client_id>           # Required for Azure operations
export ARM_CLIENT_SECRET=<your_client_secret>   # Required for Azure operations
export ARM_SUBSCRIPTION_ID=<your_subscription_id> # Required for Azure operations
export ARM_TENANT_ID=<your_tenant_id>           # Required for Azure operations

# Optional: GitHub token for AVM module access (to avoid rate limiting)
export GITHUB_TOKEN=<your_github_token_here>
```

### Configuration File (.env.local)
Create a `.env.local` file in the project root for local configuration:
```bash
# Server configuration
MCP_HOST=localhost
MCP_PORT=8000
MCP_DEBUG=false

# Azure authentication (Service Principal method)
ARM_CLIENT_ID=<your_client_id>
ARM_CLIENT_SECRET=<your_client_secret>
ARM_SUBSCRIPTION_ID=<your_subscription_id>
ARM_TENANT_ID=<your_tenant_id>

# Optional: GitHub token for AVM module access (to avoid rate limiting)
GITHUB_TOKEN=<your_github_token_here>
```

## Troubleshooting

### Common Installation Issues

1. **Import Errors**
   ```bash
   # Make sure dependencies are installed
   pip install -r requirements.txt
   ```

2. **Port Conflicts**
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
   # Check if Azure CLI is authenticated
   az account show
   
   # If using service principal, verify environment variables are set
   echo $ARM_CLIENT_ID $ARM_SUBSCRIPTION_ID $ARM_TENANT_ID
   
   # Test Azure connectivity
   az account list-locations --output table
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
1. **Test the server**: Use the health check endpoint to verify it's running
2. **Configure Azure authentication**: Set up Azure CLI or service principal credentials
3. **Integrate with VS Code**: Add the MCP configuration to your workspace
4. **Explore the tools**: Check out the [main README](../README.md) for available tools and usage examples

For more information on usage and available tools, see the [main README](../README.md).