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

### 📋 Schema & Provider Analysis
- **Terraform Schema Query**: Query fine-grained schema information for any Terraform provider
- **Provider Item Discovery**: List all available resources, data sources, and functions for providers
- **Provider Support Discovery**: Find which providers are available for analysis
- **Dynamic Schema Loading**: Support for all providers in the Terraform Registry

### 🔍 Golang Source Code Analysis
- **Golang Namespace Discovery**: Find available golang packages for source code analysis
- **Version/Tag Support**: Query specific versions of provider source code
- **Source Code Retrieval**: Read golang source code for functions, methods, types, and variables
- **Terraform Implementation Analysis**: Understand how Terraform resources are implemented in Go

### 🚀 Integration
- **MCP Protocol**: Full Model Context Protocol compliance for AI assistant integration
- **FastMCP Framework**: Built on FastMCP for high-performance async operations

## Quick Start

The fastest way to get started is with Docker (recommended):

```bash
# Basic setup - perfect for trying out documentation features
docker run -d --name tf-mcp-server -p 8000:8000 ghcr.io/liuwuliuyun/tf-mcp-server:latest

# Verify it's working
curl http://localhost:8000/health
# Should return: {"status": "healthy"}
```

**For Windows PowerShell users:**
```powershell
# Basic setup
docker run -d --name tf-mcp-server -p 8000:8000 ghcr.io/liuwuliuyun/tf-mcp-server:latest

# Verify it's working
Invoke-RestMethod -Uri "http://localhost:8000/health"
```

### VS Code Setup

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

### Need More Options?

For detailed installation instructions including:
- 🐳 **Docker with Azure authentication**
- ⚡ **UV installation for development**  
- 🐍 **Traditional Python setup**
- 🔧 **Optional tool installation**
- ⚙️ **Configuration options**

**👉 See the complete [Installation Guide](docs/installation.md)**

## Configuration

For detailed configuration options including environment variables, configuration files, and Azure authentication setup, see the [Installation Guide](docs/installation.md#configuration).

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

#### Terraform Schema & Provider Analysis Tools
- **`query_terraform_schema`**: Query fine-grained Terraform schema information for any provider
- **`list_terraform_provider_items`**: List all available items (resources, data sources, functions) for a provider
- **`terraform_source_code_query_get_supported_providers`**: Get supported providers for source code analysis
- **`query_terraform_block_implementation_source_code`**: Read Terraform provider source code implementations

#### Golang Source Code Analysis Tools
- **`golang_source_code_server_get_supported_golang_namespaces`**: Get available golang namespaces for analysis
- **`golang_source_code_server_get_supported_tags`**: Get supported version tags for a golang namespace
- **`query_golang_source_code`**: Read golang source code for functions, methods, types, and variables

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
├── src/                            # Main source code
│   ├── data/                       # Data files and schemas
│   │   └── azapi_schemas_v2.6.1.json # AzAPI resource schemas
│   └── tf_mcp_server/              # Core package
│       ├── __init__.py
│       ├── __main__.py             # Package entry point  
│       ├── launcher.py             # Server launcher
│       ├── core/                   # Core functionality
│       │   ├── __init__.py
│       │   ├── azapi_schema_generator.py # AzAPI schema generation
│       │   ├── config.py           # Configuration management
│       │   ├── models.py           # Data models and types
│       │   ├── server.py           # FastMCP server with all MCP tools
│       │   ├── terraform_executor.py # Terraform execution utilities
│       │   └── utils.py            # Shared utility functions
│       └── tools/                  # Tool implementations
│           ├── __init__.py
│           ├── avm_docs_provider.py     # Azure Verified Modules provider
│           ├── azapi_docs_provider.py   # AzAPI documentation provider  
│           ├── azurerm_docs_provider.py # AzureRM documentation provider
│           ├── conftest_avm_runner.py   # Conftest policy validation
│           ├── terraform_runner.py      # Terraform command execution
│           └── tflint_runner.py         # TFLint static analysis
├── tests/                          # Test suite
│   ├── __init__.py
│   ├── conftest.py                 # Test configuration
│   ├── test_*.py                   # Unit tests
│   └── integration/                # Integration tests
├── tfsample/                       # Sample Terraform configurations
├── policy/                         # Security and compliance policies
│   ├── avmsec/                     # Azure security policies
│   ├── Azure-Proactive-Resiliency-Library-v2/ # Azure resiliency policies  
│   └── common/                     # Common policy utilities
├── docs/                           # Documentation
├── examples/                       # Usage examples
├── pyproject.toml                  # Project configuration (UV/pip)
├── uv.lock                         # UV dependency lockfile
├── README.md                       # This file
└── CONTRIBUTE.md                   # Development and contribution guide
```



## Troubleshooting

### Common Issues

For comprehensive troubleshooting including:
- Import and dependency errors
- Port conflicts 
- Azure authentication issues
- Windows-specific problems
- Debug mode setup

**👉 See the detailed [Installation Guide - Troubleshooting](docs/installation.md#troubleshooting)**

### Quick Debug

Enable debug logging:
```bash
export MCP_DEBUG=true
python main.py
```

Check logs in `tf-mcp-server.log` for detailed information.

## Contributing

We welcome contributions! For development setup, coding standards, and detailed contribution guidelines:

**👉 See the complete [Contributing Guide](CONTRIBUTE.md)**

### Quick Start for Contributors

1. Fork the repository
2. Set up development environment (see [CONTRIBUTE.md](CONTRIBUTE.md#development-setup))
3. Create a feature branch: `git checkout -b feature/your-feature`
4. Make changes with tests
5. Run tests and formatting: `pytest && black src/ tests/`
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
