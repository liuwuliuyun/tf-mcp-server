# Documentation Index

This directory contains comprehensive documentation for the Azure Terraform MCP Server.

## 📚 Documentation Structure

### 🚀 Getting Started
- **[Installation Guide](installation.md)** - Complete setup instructions for Docker, UV, and Python
- **[Quick Start](../README.md#quick-start)** - Get up and running in minutes

### 🔧 Core Features
- **[Azure Documentation Tools](azure-documentation-tools.md)** - AzureRM and AzAPI documentation access
- **[Azure Export Guide](aztfexport-integration.md)** - Export existing Azure resources to Terraform
- **[Terraform Coverage Audit](terraform-coverage-audit.md)** - Audit Terraform coverage of Azure resources and identify gaps

### 🔐 Authentication & Configuration
- **[Azure Authentication](azure-authentication.md)** - Configure Azure service principal authentication
- **[GitHub Authentication](github-authentication.md)** - GitHub authentication setup
- **[Configuration](configuration.md)** - Environment variables and settings

### 🐳 Deployment & Operations
- **[Docker Guide](docker.md)** - Docker setup and configuration
- **[GitHub Registry Setup](github-registry-setup.md)** - Configure GitHub container registry
- **[Telemetry](telemetry.md)** - Telemetry configuration

### 📋 Reference
- **[API Reference](api-reference.md)** - Complete tool reference with examples
- **[Troubleshooting](troubleshooting.md)** - Common issues and solutions

## 🆕 What's New

The latest version includes:
- **📖 AzureRM Documentation**: Retrieve comprehensive resource and data source documentation
- **📖 AzAPI Documentation**: Access Azure API schemas for latest features
- **📤 Azure Export**: Export Azure resources to Terraform using aztfexport
- **🔍 Coverage Audit**: Audit Terraform coverage and identify gaps in Azure resource management
- **Improved Error Handling**: More detailed error messages and validation
- **Updated Dependencies**: Latest FastMCP framework and improved performance

## 📖 Quick Reference

### Available Tools
- `get_azurerm_provider_documentation` - Get AzureRM resource/data source docs
- `get_azapi_provider_documentation` - Get AzAPI resource schemas
- `check_aztfexport_installation` - Check aztfexport installation status
- `export_azure_resource` - Export single Azure resource to Terraform
- `export_azure_resource_group` - Export entire resource group to Terraform
- `export_azure_resources_by_query` - Export resources using ARG queries
- `audit_terraform_coverage` - Audit Terraform coverage and identify gaps

### Common Workflows
1. **Documentation Lookup** → [Azure Documentation Tools](azure-documentation-tools.md)
2. **Resource Export** → [Azure Export Guide](aztfexport-integration.md)
3. **Coverage Audit** → [Coverage Audit Guide](terraform-coverage-audit.md)

## 🤝 Contributing

See the main [Contributing Guide](../CONTRIBUTE.md) for development setup and contribution guidelines.
