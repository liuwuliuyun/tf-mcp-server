# Azure Terraform MCP Server

A Model Context Protocol (MCP) server for Azure Terraform operations, providing intelligent assistance for infrastructure as code development with Azure resources.

## Overview

This MCP server provides support for Azure Terraform development, including:
- Azure provider documentation retrieval for AzureRM and AzAPI
- Azure resource export to Terraform using aztfexport
- Terraform coverage auditing to identify infrastructure gaps
- Resource analysis and recommendations

## Features

### 🔍 Documentation & Discovery
- **Azure Provider Docs**: Comprehensive documentation retrieval for AzureRM resources
- **AzAPI Schema**: Schema lookup for Azure API resources
- **Resource Documentation**: Detailed arguments, attributes, and examples

### 🚀 Azure Resource Export
- **Azure Export for Terraform (aztfexport)**: Export existing Azure resources to Terraform configuration and state
- **Resource Export**: Export individual Azure resources
- **Resource Group Export**: Export entire resource groups
- **Query-based Export**: Export resources using Azure Resource Graph queries

### 📊 Infrastructure Analysis
- **Terraform Coverage Audit**: Audit Terraform coverage of Azure resources
- **Gap Analysis**: Identify Azure resources not under Terraform management
- **Orphan Detection**: Find Terraform resources that no longer exist in Azure

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

## Telemetry

This tool collects **anonymous usage telemetry** to help improve quality and performance. We collect:

- ✅ Tool usage counts and performance metrics
- ✅ Anonymous user ID (randomly generated UUID)
- ✅ Error types and success rates

We **DO NOT** collect:
- ❌ Personal information or identifiers
- ❌ File paths, resource names, or configuration content
- ❌ Azure subscription IDs or credentials

### Opt-Out

Telemetry is **optional** and can be disabled anytime:

```bash
# Disable telemetry via environment variable
export TELEMETRY_ENABLED=false
```

Or add to your `.vscode/mcp.json`:

```json
{
  "servers": {
    "tf-mcp-server": {
      "env": {
        "TELEMETRY_ENABLED": "false"
      }
    }
  }
}
```

**📖 For complete details, see [Telemetry Documentation](docs/telemetry.md)**

### Available Tools

The server provides tools for Azure Terraform development. For complete tool reference with examples, see the [API Reference](docs/api-reference.md).

#### Documentation Tools
- **`get_azurerm_provider_documentation`**: Retrieve specific AzureRM resource or data source documentation with optional argument/attribute lookup
- **`get_azapi_provider_documentation`**: Retrieve AzAPI resource schemas and documentation

#### Azure Export Tools
- **`check_aztfexport_installation`**: Check Azure Export for Terraform (aztfexport) installation status and version
- **`export_azure_resource`**: Export a single Azure resource to Terraform configuration using aztfexport
- **`export_azure_resource_group`**: Export an entire Azure resource group and its resources to Terraform configuration
- **`export_azure_resources_by_query`**: Export Azure resources using Azure Resource Graph queries to Terraform configuration

#### Coverage Audit Tools
- **`audit_terraform_coverage`**: Audit Terraform coverage of Azure resources, compare state against Azure Resource Graph to identify gaps, orphaned resources, and get actionable recommendations

## 📚 Documentation

For comprehensive guides and examples:

- **[📖 Documentation Index](docs/README.md)** - Complete documentation overview
- **[🚀 Installation Guide](docs/installation.md)** - Setup instructions for all platforms
- **[🔧 Configuration Guide](docs/configuration.md)** - Environment variables and settings
- **[📋 API Reference](docs/api-reference.md)** - Complete tool reference with examples
- **[❓ Troubleshooting](docs/troubleshooting.md)** - Common issues and solutions

### Feature Guides

- **[Azure Documentation Tools](docs/azure-documentation-tools.md)** - AzureRM and AzAPI documentation access
- **[Terraform Coverage Audit](docs/terraform-coverage-audit.md)** - Audit Terraform coverage and identify infrastructure gaps
- **[Azure Export Integration](docs/aztfexport-integration.md)** - Export existing Azure resources to Terraform

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
│           ├── azapi_docs_provider.py   # AzAPI documentation provider  
│           ├── azurerm_docs_provider.py # AzureRM documentation provider
│           ├── aztfexport_runner.py     # Azure Export for Terraform (aztfexport) integration
│           ├── coverage_auditor.py      # Terraform coverage audit tool
│           └── terraform_runner.py      # Terraform command execution
├── tests/                          # Test suite
│   ├── __init__.py
│   ├── conftest.py                 # Test configuration
│   └── test_*.py                   # Unit tests
├── tfsample/                       # Sample Terraform configurations
├── workspace/                      # Default workspace directory for operations
├── docs/                           # Comprehensive documentation
├── pyproject.toml                  # Project configuration (UV/pip)
├── uv.lock                         # UV dependency lockfile
├── Dockerfile                      # Docker container configuration
├── docker-compose.yml              # Docker Compose setup
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
