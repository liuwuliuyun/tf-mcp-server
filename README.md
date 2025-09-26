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
- **TFLint Integration**: Static analysis with TFLint including Azure ruleset support for Terraform workspaces
- **Resource Analysis**: Analyze Azure resources in Terraform configurations
- **Azure Export for Terraform (aztfexport)**: Export existing Azure resources to Terraform configuration and state

### 🚀 Integration
- **MCP Protocol**: Full Model Context Protocol compliance for AI assistant integration
- **FastMCP Framework**: Built on FastMCP for high-performance async operations

## Quick Start

Create or edit `.vscode/mcp.json` in your workspace:

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
- **`run_terraform_command`**: Execute Terraform CLI commands (init, plan, apply, destroy, validate, fmt) inside a workspace folder that already contains configuration files

#### Security Tools
- **`run_conftest_workspace_validation`**: Validate Terraform files in a workspace folder against Azure security policies (works with aztfexport folders)
- **`run_conftest_workspace_plan_validation`**: Validate Terraform plan files in a workspace folder against Azure security policies

#### Static Analysis Tools
- **`run_tflint_workspace_analysis`**: Run TFLint static analysis on workspace folders containing Terraform files (supports recursive analysis)
- **`check_tflint_installation`**: Check TFLint installation status and get version information

#### Analysis Tools
- **`analyze_azure_resources`**: Analyze Azure resources in Terraform configurations

#### Azure Export Tools (aztfexport Integration)
- **`check_aztfexport_installation`**: Check Azure Export for Terraform (aztfexport) installation status and version
- **`aztfexport_resource`**: Export a single Azure resource to Terraform configuration using aztfexport
- **`aztfexport_resource_group`**: Export an entire Azure resource group and its resources to Terraform configuration
- **`aztfexport_query`**: Export Azure resources using Azure Resource Graph queries to Terraform configuration
- **`aztfexport_get_config`**: Get aztfexport configuration settings
- **`aztfexport_set_config`**: Set aztfexport configuration settings

### Example Usage

#### Execute Terraform Commands
Prepare a workspace directory (for example `workspace/demo`) containing your Terraform configuration files before invoking the tool.

```python
# Initialize Terraform in a workspace directory
{
  "tool": "run_terraform_command",
  "arguments": {
    "command": "init",
    "workspace_folder": "workspace/demo",
    "upgrade": true
  }
}

# Generate an execution plan
{
  "tool": "run_terraform_command",
  "arguments": {
    "command": "plan",
    "workspace_folder": "workspace/demo"
  }
}

# Apply changes (auto-approve optional)
{
  "tool": "run_terraform_command",
  "arguments": {
    "command": "apply",
    "workspace_folder": "workspace/demo",
    "auto_approve": true
  }
}

# Format Terraform files in the workspace
{
  "tool": "run_terraform_command",
  "arguments": {
    "command": "fmt",
    "workspace_folder": "workspace/demo"
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
Conftest validation operates on Terraform workspaces or plan files. Save your configuration to disk (for example, using aztfexport or manual edits) and point the tools at those files. You can use `run_terraform_command` to run Terraform inside that workspace for init/plan/apply steps:

```python
# Validate Terraform files in a workspace folder (works with aztfexport folders)
{
  "tool": "run_conftest_workspace_validation",
  "arguments": {
    "workspace_folder": "exported-rg-acctest0001",
    "policy_set": "avmsec",
    "severity_filter": "high"
  }
}

# Validate plan files stored in a workspace folder
{
  "tool": "run_conftest_workspace_plan_validation",
  "arguments": {
    "folder_name": "exported-rg-acctest0001",
    "policy_set": "all"
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

## Integrated Workflows

### Export and Validate Azure Resources

The conftest tools are designed to work seamlessly with aztfexport for a complete export-and-validate workflow:

```python
# 1. Export Azure resource to workspace folder
{
  "tool": "aztfexport_resource",
  "arguments": {
    "resource_id": "/subscriptions/12345678-1234-1234-1234-123456789abc/resourceGroups/my-rg/providers/Microsoft.Storage/storageAccounts/mystorageaccount",
    "output_folder_name": "exported-storage-account",
    "provider": "azurerm"
  }
}

# 2. Validate exported Terraform files
{
  "tool": "run_conftest_workspace_validation", 
  "arguments": {
    "workspace_folder": "exported-storage-account",
    "policy_set": "avmsec",
    "severity_filter": "high"
  }
}

# 3. Optionally validate just the plan file
{
  "tool": "run_conftest_workspace_plan_validation",
  "arguments": {
    "folder_name": "exported-storage-account", 
    "policy_set": "Azure-Proactive-Resiliency-Library-v2"
  }
}
```

This workflow allows you to:
1. Export existing Azure infrastructure as Terraform code
2. Immediately validate it against Azure security policies and best practices
3. Identify compliance issues before applying changes

#### TFLint Static Analysis
TFLint now runs against Terraform workspaces. Save your configuration to disk, then invoke the workspace analysis tool:

```python
# Run TFLint analysis on a workspace folder
{
  "tool": "run_tflint_workspace_analysis",
  "arguments": {
    "workspace_folder": "/path/to/terraform/project",
    "output_format": "json",
    "recursive": true,
    "enable_azure_plugin": true,
    "enable_rules": ["azurerm_storage_account_min_tls_version"],
    "disable_rules": ["terraform_unused_declarations"]
  }
}

# Check TFLint installation
{
  "tool": "check_tflint_installation",
  "arguments": {}
}
```

#### Azure Export for Terraform (aztfexport)
```python
# Check if aztfexport is installed
{
  "tool": "check_aztfexport_installation",
  "arguments": {}
}

# Export a single Azure resource to Terraform configuration
{
  "tool": "aztfexport_resource",
  "arguments": {
    "resource_id": "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/my-rg/providers/Microsoft.Storage/storageAccounts/mystorageacct",
    "provider": "azurerm",
    "dry_run": false,
    "resource_name": "primary_storage"
  }
}

# Export an entire resource group
{
  "tool": "aztfexport_resource_group",
  "arguments": {
    "resource_group_name": "production-environment",
    "provider": "azurerm",
    "include_role_assignment": true,
    "parallelism": 5,
    "continue_on_error": true
  }
}

# Export resources using Azure Resource Graph query
{
  "tool": "aztfexport_query",
  "arguments": {
    "query": "type =~ 'Microsoft.Storage/storageAccounts' and location == 'eastus'",
    "provider": "azurerm",
    "dry_run": true,
    "name_pattern": "storage_{name}"
  }
}

# Get aztfexport configuration
{
  "tool": "aztfexport_get_config",
  "arguments": {
    "key": "telemetry_enabled"
  }
}

# Set aztfexport configuration (disable telemetry)
{
  "tool": "aztfexport_set_config",
  "arguments": {
    "key": "telemetry_enabled",
    "value": "false"
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
│           ├── aztfexport_runner.py     # Azure Export for Terraform (aztfexport) integration
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
