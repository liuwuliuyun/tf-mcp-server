# Documentation Index

This directory contains comprehensive documentation for the Azure Terraform MCP Server.

## 📚 Documentation Structure

### 🚀 Getting Started
- **[Installation Guide](installation.md)** - Complete setup instructions for Docker, UV, and Python
- **[Quick Start](../README.md#quick-start)** - Get up and running in minutes

### 🔧 Core Features
- **[Azure Documentation Tools](azure-documentation-tools.md)** - AzureRM, AzAPI, and AVM documentation access
- **[Terraform Command Integration](terraform-commands.md)** - Execute Terraform CLI commands and state management
- **[Terraform State Management](terraform-state-management.md)** - Safe resource renaming and state operations
- **[Azure Best Practices](azure-best-practices-tool.md)** - Get Azure and Terraform best practices with code cleanup guidance
- **[Source Code Analysis](terraform-golang-source-tools.md)** - Terraform and Golang source code analysis

### 🛡️ Security & Validation
- **[TFLint Integration](tflint-integration.md)** - Static analysis for Terraform code
- **[Conftest AVM Validation](conftest-avm-validation.md)** - Policy-based security validation
- **[Security Policies](security-policies.md)** - Available security and compliance policies

### 🔄 Azure Integration
- **[Azure Export (aztfexport)](aztfexport-integration.md)** - Export existing Azure resources to Terraform
- **[Azure Authentication](azure-authentication.md)** - Configure Azure service principal authentication

### 🐳 Deployment & Operations
- **[Docker Guide](docker.md)** - Docker setup and configuration
- **[GitHub Registry Setup](github-registry-setup.md)** - Configure GitHub container registry
- **[GitHub Authentication](github-authentication.md)** - GitHub authentication setup

### 📋 Reference
- **[API Reference](api-reference.md)** - Complete tool reference with examples
- **[Configuration](configuration.md)** - Environment variables and settings
- **[Troubleshooting](troubleshooting.md)** - Common issues and solutions

## 🆕 What's New

The latest version includes:
- **🔄 Terraform State Management**: Full support for state operations (list, show, mv, rm, pull, push) via run_terraform_command
- **🧹 Code Cleanup Workflow**: Transform exported Terraform code to production-ready with best practices guidance
- **📋 Enhanced Best Practices**: New "code-cleanup" action for aztfexport with detailed resource naming and refactoring guidance
- **🔐 Variables vs Locals Guidance**: Clear recommendations on when to use variables versus locals
- **Enhanced Terraform Source Code Analysis**: Query provider implementations directly
- **Golang Source Code Access**: Read Go source code from Terraform providers  
- **Improved Azure Best Practices**: Comprehensive recommendations for Azure resources
- **Better Error Handling**: More detailed error messages and validation
- **Updated Dependencies**: Latest FastMCP framework and improved performance

## 📖 Quick Reference

### Most Used Tools
- `get_azurerm_provider_documentation` - Get AzureRM resource docs
- `run_terraform_command` - Execute Terraform commands and state operations
- `get_azure_best_practices` - Get Azure best practices and code cleanup guidance
- `export_azure_resource` - Export Azure resources to Terraform

### Common Workflows
1. **Documentation Lookup** → [Azure Documentation Tools](azure-documentation-tools.md)
2. **Resource Export** → [Azure Export Guide](aztfexport-integration.md)
3. **Code Cleanup** → [State Management Guide](terraform-state-management.md)
4. **Security Validation** → [Conftest Validation](conftest-avm-validation.md)
5. **Code Analysis** → [Source Code Analysis](terraform-golang-source-tools.md)

## 🤝 Contributing

See the main [Contributing Guide](../CONTRIBUTE.md) for development setup and contribution guidelines.