# Azure Terraform MCP Server

A Model Context Protocol (MCP) server for Azure Terraform operations, providing intelligent assistance for infrastructure as code development with Azure resources.

## Overview

This MCP server provides support for Azure Terraform development, including:
- Azure provider documentation retrieval of AzureRM, AzAPI and Azure Verified Module(AVM)
- HCL code validation and static analysis with TFLint
- Security scanning and compliance checking
- Best practices guidance
- Resource analysis and recommendations

## Features

### 🔍 Documentation & Discovery
- **Azure Provider Docs**: Comprehensive documentation retrieval for AzureRM resources
- **AzAPI Schema**: Schema lookup for Azure API resources
- **Azure Verified Modules (AVM)**: Discovery and documentation for verified Terraform modules including module listings, versions, variables, and outputs
- **Resource Documentation**: Detailed arguments, attributes, and examples

### 🛡️ Security & Compliance
- **Security Scanning**: Built-in security rule validation for Azure resources
- **Azure Verified Modules (AVM) Policies**: Integration with Conftest and Azure Policy Library AVM for comprehensive policy validation
- **Best Practices**: Azure-specific best practices and recommendations

### 🔧 Development Tools
- **Unified Terraform Commands**: Single tool to execute all Terraform commands (init, plan, apply, destroy, validate, fmt)
- **HCL Validation**: Syntax validation and error reporting for Terraform code
- **HCL Formatting**: Automatic code formatting for Terraform configurations
- **TFLint Integration**: Static analysis with TFLint including Azure ruleset support
- **Resource Analysis**: Analyze Azure resources in Terraform configurations

### 🚀 Integration
- **MCP Protocol**: Full Model Context Protocol compliance for AI assistant integration
- **FastMCP Framework**: Built on FastMCP for high-performance async operations

## Installation

### Prerequisites
- Python 3.11 or higher
- [UV](https://docs.astral.sh/uv/) (recommended) or pip
- [TFLint](https://github.com/terraform-linters/tflint) (optional, for static analysis features)
- [Conftest](https://www.conftest.dev/) (optional, for Azure AVM policy validation)

### Optional Tool Installation

#### TFLint (Recommended for Static Analysis)
TFLint provides advanced static analysis for Terraform configurations. Install it for best experience:

```bash
# Windows (Chocolatey)
choco install tflint

# macOS (Homebrew)
brew install tflint

# Linux (Script)
curl -s https://raw.githubusercontent.com/terraform-linters/tflint/master/install_linux.sh | bash

# Manual download
# Download from: https://github.com/terraform-linters/tflint/releases
```

#### Conftest (Recommended for Azure AVM Policy Validation)
Conftest enables policy validation using the Azure Policy Library AVM:

```bash
# Windows (Scoop)
scoop install conftest

# macOS (Homebrew)
brew install conftest

# Linux (Download binary)
# Download from: https://github.com/open-policy-agent/conftest/releases

# Go install
go install github.com/open-policy-agent/conftest@latest
```

### Quick Start with UV (Recommended)

1. **Install UV** (if not already installed):
   ```bash
   # On Windows
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   
   # On macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Clone and Setup**:
   ```bash
   git clone <repository-url>
   cd tf-mcp-server
   
   # Install dependencies and create virtual environment
   uv sync
   
   # Run the server
   uv run tf-mcp-server
   ```

3. **Development Setup**:
   ```bash
   # Install with development dependencies
   uv sync --dev
   
   # Run tests
   uv run pytest
   
   # Format code
   uv run black .
   
   # Run linting
   uv run flake8
   ```

### Alternative: Traditional pip Installation

1. **Clone and Setup**:
   ```bash
   git clone <repository-url>
   cd tf-mcp-server
   
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install the package
   pip install -e .
   ```

### Docker Installation (Recommended for Production)

The easiest way to run the Azure Terraform MCP Server is using Docker:

1. **Using Docker with pre-built image:**
   ```bash
   # Run the server directly
   docker run -d \
     --name tf-mcp-server \
     -p 8000:8000 \
     -v ~/.azure:/home/mcpuser/.azure:ro \
     ghcr.io/liuwuliuyun/tf-mcp-server:latest
   ```

2. **Using Docker Compose (Recommended):**
   ```bash
   # Download docker-compose.yml
   curl -O https://raw.githubusercontent.com/liuwuliuyun/tf-mcp-server/main/docker-compose.yml
   
   # Start the service
   docker-compose up -d
   ```

3. **Build from source:**
   ```bash
   git clone <repository-url>
   cd tf-mcp-server
   docker build -t tf-mcp-server .
   docker run -d --name tf-mcp-server -p 8000:8000 tf-mcp-server
   ```

📖 **For detailed Docker usage, see [DOCKER.md](DOCKER.md)**

## Configuration

### Environment Variables
```bash
# Server configuration
export MCP_HOST=localhost          # Default: localhost
export MCP_PORT=6801              # Default: 6801
export MCP_DEBUG=false            # Default: false

# Optional: GitHub token for AVM module access (to avoid rate limiting)
export GITHUB_TOKEN=<your_github_token_here>
```

### Configuration File (.env.local)
Create a `.env.local` file in the project root for local configuration:
```bash
MCP_HOST=localhost
MCP_PORT=6801
MCP_DEBUG=false

# Optional: GitHub token for AVM module access (to avoid rate limiting)
GITHUB_TOKEN=<your_github_token_here>
```

## Usage

### Starting the Server

```bash
# Using UV (recommended)
uv run tf-mcp-server

# Using the package entry point
python -m tf_mcp_server

# Using the main script (legacy)
python main.py
```

The server will start on `http://localhost:6801` by default.

### Available Tools

The server provides the following MCP tools:

#### Documentation Tools
- **`azurerm_terraform_documentation_retriever`**: Retrieve specific AzureRM resource or data source documentation with optional argument/attribute lookup
- **`azapi_terraform_documentation_retriever`**: Retrieve AzAPI resource schemas and documentation
- **`get_avm_modules`**: Retrieve all available Azure Verified Modules with descriptions and source information
- **`get_avm_latest_version`**: Get the latest version of a specific Azure Verified Module
- **`get_avm_versions`**: Get all available versions of a specific Azure Verified Module
- **`get_avm_variables`**: Retrieve the input variables schema for a specific AVM module version
- **`get_avm_outputs`**: Retrieve the output definitions for a specific AVM module version

#### Terraform Command Tools
- **`run_terraform_command`**: Execute any Terraform command (init, plan, apply, destroy, validate, fmt) with provided HCL content

#### Security Tools
- **`run_conftest_validation`**: Validate Terraform HCL against Azure security policies and best practices using Conftest (supports azurerm, azapi, and AVM providers)
- **`run_conftest_plan_validation`**: Validate Terraform plan JSON against Azure security policies and best practices using Conftest

#### Static Analysis Tools
- **`run_tflint_analysis`**: Run TFLint static analysis on Terraform configurations with Azure plugin support
- **`check_tflint_installation`**: Check TFLint installation status and get version information

#### Analysis Tools
- **`analyze_azure_resources`**: Analyze Azure resources in Terraform configurations

### Example Usage

#### Execute Terraform Commands
```python
# Initialize Terraform with HCL content
{
  "tool": "run_terraform_command",
  "arguments": {
    "command": "init",
    "hcl_content": "resource \"azurerm_storage_account\" \"example\" {\n  name = \"mystorageaccount\"\n  resource_group_name = \"myresourcegroup\"\n  location = \"East US\"\n  account_tier = \"Standard\"\n  account_replication_type = \"LRS\"\n}",
    "upgrade": true
  }
}

# Validate HCL code
{
  "tool": "run_terraform_command",
  "arguments": {
    "command": "validate",
    "hcl_content": "resource \"azurerm_storage_account\" \"example\" {\n  name = \"mystorageaccount\"\n  resource_group_name = \"myresourcegroup\"\n  location = \"East US\"\n  account_tier = \"Standard\"\n  account_replication_type = \"LRS\"\n}"
  }
}

# Format HCL code
{
  "tool": "run_terraform_command",
  "arguments": {
    "command": "fmt",
    "hcl_content": "resource\"azurerm_storage_account\"\"example\"{\nname=\"mystorageaccount\"\n}"
  }
}
```

#### Get Documentation
```python
# Get detailed resource documentation
{
  "tool": "azurerm_terraform_documentation_retriever",
  "arguments": {
    "resource_type_name": "storage_account",
    "doc_type": "resource"
  }
}

# Get specific argument details
{
  "tool": "azurerm_terraform_documentation_retriever",
  "arguments": {
    "resource_type_name": "storage_account",
    "doc_type": "resource",
    "argument_name": "account_tier"
  }
}
```

#### Get Data Source Documentation
```python
# Using the main documentation tool for data sources
{
  "tool": "azurerm_terraform_documentation_retriever",
  "arguments": {
    "resource_type_name": "virtual_machine",
    "doc_type": "data-source"
  }
}
```

#### Azure Policy Validation
```python
# Validate with all Azure policies
{
  "tool": "run_conftest_validation",
  "arguments": {
    "hcl_content": "resource \"azurerm_storage_account\" \"example\" {\n  name = \"mystorageaccount\"\n  resource_group_name = \"myresourcegroup\"\n  location = \"East US\"\n  account_tier = \"Standard\"\n  account_replication_type = \"LRS\"\n}",
    "policy_set": "all"
  }
}

# Validate with high severity security policies only
{
  "tool": "run_conftest_validation",
  "arguments": {
    "hcl_content": "resource \"azurerm_storage_account\" \"example\" {\n  name = \"mystorageaccount\"\n  resource_group_name = \"myresourcegroup\"\n  location = \"East US\"\n  account_tier = \"Standard\"\n  account_replication_type = \"LRS\"\n}",
    "policy_set": "avmsec",
    "severity_filter": "high"
  }
}

# Validate plan JSON directly
{
  "tool": "run_conftest_plan_validation", 
  "arguments": {
    "terraform_plan_json": "{\"planned_values\": {\"root_module\": {\"resources\": [...]}}}",
    "policy_set": "Azure-Proactive-Resiliency-Library-v2"
  }
}
```

#### AzAPI Documentation
```python
# Get AzAPI resource schema
{
  "tool": "azapi_terraform_documentation_retriever",
  "arguments": {
    "resource_type_name": "Microsoft.Storage/storageAccounts@2021-04-01"
  }
}
```

#### Azure Verified Modules (AVM)
```python
# Get all available Azure Verified Modules
{
  "tool": "get_avm_modules",
  "arguments": {}
}

# Get the latest version of a specific AVM module
{
  "tool": "get_avm_latest_version",
  "arguments": {
    "module_name": "avm-res-compute-virtualmachine"
  }
}

# Get all available versions of an AVM module
{
  "tool": "get_avm_versions",
  "arguments": {
    "module_name": "avm-res-storage-storageaccount"
  }
}

# Get input variables for a specific AVM module version
{
  "tool": "get_avm_variables",
  "arguments": {
    "module_name": "avm-res-compute-virtualmachine",
    "module_version": "0.19.3"
  }
}

# Get outputs for a specific AVM module version
{
  "tool": "get_avm_outputs",
  "arguments": {
    "module_name": "avm-res-compute-virtualmachine",
    "module_version": "0.19.3"
  }
}
```

#### Analyze Azure Resources
```python
# Analyze Terraform configuration for Azure resources
{
  "tool": "analyze_azure_resources",
  "arguments": {
    "hcl_content": "resource \"azurerm_storage_account\" \"example\" {\n  name = \"mystorageaccount\"\n  resource_group_name = \"myresourcegroup\"\n}\n\nresource \"azurerm_virtual_machine\" \"example\" {\n  name = \"myvm\"\n  resource_group_name = \"myresourcegroup\"\n}"
  }
}
```

#### TFLint Static Analysis
```python
# Run TFLint analysis with Azure plugin
{
  "tool": "run_tflint_analysis",
  "arguments": {
    "hcl_content": "resource \"azurerm_storage_account\" \"example\" {\n  name = \"mystorageaccount\"\n  resource_group_name = \"myresourcegroup\"\n  location = \"East US\"\n  account_tier = \"Standard\"\n  account_replication_type = \"LRS\"\n}",
    "output_format": "json",
    "enable_azure_plugin": true
  }
}

# Check TFLint installation
{
  "tool": "check_tflint_installation",
  "arguments": {}
}

# Run with specific rules configuration
{
  "tool": "run_tflint_analysis",
  "arguments": {
    "hcl_content": "resource \"azurerm_storage_account\" \"example\" {\n  name = \"mystorageaccount\"\n}",
    "output_format": "compact",
    "enable_azure_plugin": true,
    "disable_rules": "terraform_unused_declarations",
    "enable_rules": "azurerm_storage_account_min_tls_version"
  }
}
```

## Project Structure

```
tf-mcp-server/
├── src/                            # Main package
│   └── tf_mcp_server/              # Core package
│       ├── __init__.py
│       ├── __main__.py             # Package entry point
│       ├── launcher.py             # Server launcher
│       ├── core/                   # Core functionality
│       │   ├── __init__.py
│       │   ├── config.py           # Configuration management
│       │   ├── models.py           # Data models
│       │   ├── server.py           # FastMCP server implementation
│       │   ├── terraform_executor.py    # Terraform execution utilities
│       │   └── utils.py            # Utility functions
│       ├── tools/                  # Tool implementations
│       │   ├── __init__.py
│       │   ├── avm_docs_provider.py     # Azure Verified Modules documentation provider
│       │   ├── azapi_docs_provider.py    # AzAPI documentation provider
│       │   ├── azurerm_docs_provider.py # AzureRM documentation provider
│       │   └── terraform_runner.py # Terraform command runner
│       └── data/                   # Data files
│           └── azapi_schemas.json  # AzAPI schemas
├── tests/                          # Test suite
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_azurerm_docs_provider.py
│   ├── test_datasource.py
│   ├── test_detailed_attributes.py
│   ├── test_summaries.py
│   └── test_utils.py
├── scripts/                        # Utility scripts
├── main.py                         # Legacy entry point
├── pyproject.toml                  # Project configuration (UV/pip)
├── uv.lock                         # UV lockfile
├── README.md                       # This file
└── CONTRIBUTE.md                   # Contributing guidelines
```

## Development

### Setting Up Development Environment

```bash
# Clone the repository
git clone <repository-url>
cd tf-mcp-server

# Using UV (recommended)
uv sync --dev

# Or using traditional pip
pip install -r requirements-dev.txt

# Install in development mode
pip install -e .

# Run tests
pytest tests/

# Run with debug logging
export MCP_DEBUG=true
uv run tf-mcp-server
# or
python -m tf_mcp_server
```

### Adding New Tools

To add new MCP tools, extend the server in `src/tf_mcp_server/core/server.py`:

```python
@mcp.tool("your_new_tool")
async def your_new_tool(
    param: str = Field(..., description="Parameter description")
) -> Dict[str, Any]:
    """Tool description."""
    # Implementation
    return {"result": "success"}
```

### Running Tests

```bash
# Run tests (if available)
pytest tests/

# Run with coverage (if pytest-cov is installed)
pytest --cov=src tests/

# Run specific test file
pytest tests/test_utils.py
```

## Security Scanning

The server includes security scanning capabilities with built-in Azure security rules for common misconfigurations and security issues.

## Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Make sure dependencies are installed
   pip install -r requirements.txt
   ```

2. **Port Conflicts**
   ```bash
   # Change port via environment variable
   export MCP_PORT=6802
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

5. **Windows Path Length Limitations**
   ```powershell
   # If you encounter path length issues on Windows when extracting AVM modules
   # Run this PowerShell command as Administrator to enable long paths:
   Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1

### Debug Mode

Enable debug logging:
```bash
export MCP_DEBUG=true
python main.py
```

Check logs in `tf-mcp-server.log` for detailed information.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Run the test suite: `pytest`
5. Format code: `black src/ tests/`
6. Submit a pull request

## License

This project is licensed under the MIT License. See LICENSE file for details.

## Support

For issues and questions:
- Create an issue in the repository
- Check the troubleshooting section above
- Review existing documentation and tests

## Related Projects

- [FastMCP Framework](https://github.com/jlowin/fastmcp)
- [Azure Terraform Provider](https://github.com/hashicorp/terraform-provider-azurerm)
- [AzAPI Provider](https://github.com/Azure/terraform-provider-azapi)
- [Model Context Protocol](https://modelcontextprotocol.io)
