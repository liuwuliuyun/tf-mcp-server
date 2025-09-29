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
- **Azure Export for Terraform (aztfexport)**: Export existing Azure resources to Terraform configuration and state

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

The server provides comprehensive tools across multiple categories. For complete tool reference with examples, see the [API Reference](docs/api-reference.md).

#### Documentation Tools
- **`get_azurerm_provider_documentation`**: Retrieve specific AzureRM resource or data source documentation with optional argument/attribute lookup
- **`get_azapi_provider_documentation`**: Retrieve AzAPI resource schemas and documentation
- **`get_avm_modules`**: Retrieve all available Azure Verified Modules with descriptions and source information
- **`get_avm_latest_version`**: Get the latest version of a specific Azure Verified Module
- **`get_avm_versions`**: Get all available versions of a specific Azure Verified Module
- **`get_avm_variables`**: Retrieve the input variables schema for a specific AVM module version
- **`get_avm_outputs`**: Retrieve the output definitions for a specific AVM module version

#### Terraform Command Tools
- **`run_terraform_command`**: Execute Terraform CLI commands (init, plan, apply, destroy, validate, fmt) inside a workspace folder

#### Security & Validation Tools
- **`check_conftest_installation`**: Check Conftest installation status and get version information
- **`run_conftest_workspace_validation`**: Validate Terraform files in a workspace folder against Azure security policies
- **`run_conftest_workspace_plan_validation`**: Validate Terraform plan files against Azure security policies
- **`check_tflint_installation`**: Check TFLint installation status and get version information
- **`run_tflint_workspace_analysis`**: Run TFLint static analysis on workspace folders containing Terraform files

#### Azure Export Tools
- **`check_aztfexport_installation`**: Check Azure Export for Terraform (aztfexport) installation status and version
- **`export_azure_resource`**: Export a single Azure resource to Terraform configuration using aztfexport
- **`export_azure_resource_group`**: Export an entire Azure resource group and its resources to Terraform configuration
- **`export_azure_resources_by_query`**: Export Azure resources using Azure Resource Graph queries to Terraform configuration
- **`get_aztfexport_config`**: Get aztfexport configuration settings
- **`set_aztfexport_config`**: Set aztfexport configuration settings

#### Source Code Analysis Tools
- **`get_terraform_source_providers`**: Get supported providers for source code analysis
- **`query_terraform_source_code`**: Read Terraform provider source code implementations
- **`get_golang_namespaces`**: Get available golang namespaces for analysis
- **`get_golang_namespace_tags`**: Get supported version tags for a golang namespace
- **`query_golang_source_code`**: Read golang source code for functions, methods, types, and variables

#### Best Practices Tools
- **`get_azure_best_practices`**: Get comprehensive Azure and Terraform best practices for specific resources and actions (supports AzureRM 4.x and AzAPI 2.x recommendations)

## 📚 Documentation

For comprehensive guides and examples:

- **[📖 Documentation Index](docs/README.md)** - Complete documentation overview
- **[🚀 Installation Guide](docs/installation.md)** - Setup instructions for all platforms
- **[🔧 Configuration Guide](docs/configuration.md)** - Environment variables and settings
- **[📋 API Reference](docs/api-reference.md)** - Complete tool reference with examples
- **[❓ Troubleshooting](docs/troubleshooting.md)** - Common issues and solutions

### Feature Guides

- **[Azure Documentation Tools](docs/azure-documentation-tools.md)** - AzureRM, AzAPI, and AVM documentation access
- **[Terraform Commands](docs/terraform-commands.md)** - Execute Terraform operations
- **[Security Policies](docs/security-policies.md)** - Policy-based validation and compliance
- **[Azure Export Integration](docs/aztfexport-integration.md)** - Export existing Azure resources
- **[Source Code Analysis](docs/terraform-golang-source-tools.md)** - Terraform and Golang code analysis
- **[Azure Best Practices](docs/azure-best-practices-tool.md)** - Get Azure-specific recommendations

### Example Usage

For complete examples and workflows, see the [API Reference](docs/api-reference.md).



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

For comprehensive troubleshooting including:
- Docker and VS Code MCP setup issues
- Azure authentication problems  
- Tool installation and configuration
- Performance optimization
- Platform-specific solutions

**👉 See the detailed [Troubleshooting Guide](docs/troubleshooting.md)**

### Quick Debug

Enable debug logging:
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

Check logs for detailed information and error diagnosis.

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
