# TFLint Integration

This document describes how to use TFLint static analysis with the Azure Terraform MCP Server.

## Overview

TFLint is a Terraform static analysis tool that finds possible errors (like invalid instance types), warns about deprecated syntax, and enforces best practices. The Azure Terraform MCP Server runs TFLint against Terraform workspaces that you provide on disk.

## Prerequisites

### Install TFLint

TFLint must be installed and available in your system PATH.

#### Installation Methods

**macOS (Homebrew):**
```bash
brew install tflint
```

**Windows (Chocolatey):**
```powershell
choco install tflint
```

**Linux:**
```bash
curl -s https://raw.githubusercontent.com/terraform-linters/tflint/master/install_linux.sh | bash
```

**Direct Download:**
Download from the [GitHub releases page](https://github.com/terraform-linters/tflint/releases)

### Verify Installation

```bash
tflint --version
```

## Available Tools

### `run_tflint_workspace_analysis`

Analyzes a workspace folder containing Terraform configuration files.

**Parameters:**
- `workspace_folder` (required): Path to the workspace folder containing Terraform files
- `output_format` (optional): Output format - json, default, checkstyle, junit, compact, sarif (default: json)
- `enable_azure_plugin` (optional): Enable Azure ruleset plugin (default: true)
- `enable_rules` (optional): Comma-separated list of rules to enable
- `disable_rules` (optional): Comma-separated list of rules to disable
- `initialize_plugins` (optional): Whether to initialize plugins (default: true)
- `recursive` (optional): Whether to recursively analyze subdirectories (default: false)

**Example:**
```
workspace_folder: "/path/to/terraform/project"
```

The workspace folder should contain `.tf` or `.tf.json` files:
```
terraform-project/
├── main.tf
├── variables.tf
├── outputs.tf
└── modules/
    └── network/
        └── network.tf
```

### `check_tflint_installation`

Checks if TFLint is installed and returns version information.

## Usage Examples

### Preparing a Workspace

Save your Terraform configuration to a workspace directory that the server can access. Create the folder manually or reuse aztfexport output.

```
terraform-project/
├── main.tf
├── variables.tf
└── modules/
    └── storage/
        └── storage.tf
```

### Analyzing Workspace Folders

Use `run_tflint_workspace_analysis` to scan the directory:

#### Non-Recursive Analysis
```python
result = await run_tflint_workspace_analysis(
    workspace_folder="/path/to/terraform/project",
    output_format="json",
    enable_azure_plugin=True,
    recursive=False
)
```

#### Recursive Analysis
```python
result = await run_tflint_workspace_analysis(
    workspace_folder="/path/to/terraform/project",
    output_format="json",
    enable_azure_plugin=True,
    recursive=True
)
```

### Custom Rule Configuration

Enable or disable specific rules while scanning the workspace:

```python
result = await run_tflint_workspace_analysis(
  workspace_folder="/path/to/terraform/project",
  enable_rules=["terraform_required_providers", "terraform_required_version"],
  disable_rules=["terraform_unused_declarations"],
  output_format="json"
)
```

## Output Formats

### JSON Format (Recommended)
Provides structured output with detailed issue information:

```json
{
  "success": true,
  "issues": [
    {
      "rule": {
        "name": "terraform_required_version",
        "severity": "warning"
      },
      "message": "terraform \"required_version\" attribute is required",
      "range": {
        "filename": "main.tf",
        "start": {"line": 1, "column": 1},
        "end": {"line": 1, "column": 1}
      }
    }
  ],
  "summary": {
    "total_issues": 1,
    "errors": 0,
    "warnings": 1,
    "notices": 0
  }
}
```

### Compact Format
Human-readable format for quick review:

```
main.tf:1:1: Warning - terraform "required_version" attribute is required (terraform_required_version)
```

### Other Formats
- `default`: Standard TFLint output
- `checkstyle`: Checkstyle XML format
- `junit`: JUnit XML format
- `sarif`: SARIF JSON format

## Azure Ruleset Plugin

The Azure ruleset plugin provides Azure-specific best practices and security rules.

### Features
- Validates Azure resource configurations
- Enforces Azure security best practices
- Checks for deprecated Azure resource properties
- Validates Azure resource naming conventions

### Plugin Initialization
The plugin is automatically initialized when `initialize_plugins=True` (default). This requires:
- Internet connectivity
- Access to GitHub API (may require authentication token for high usage)

### Common Issues
- **401 Bad credentials**: GitHub API rate limiting. Consider using a GitHub token.
- **Plugin installation failed**: Check internet connectivity and GitHub access.

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Terraform Validation
on: [push, pull_request]

jobs:
  tflint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup TFLint
        uses: terraform-linters/setup-tflint@v3
        
      - name: Run TFLint Analysis
        run: |
          # Use the MCP server to run TFLint analysis
          # This would typically be integrated with your MCP client
```

### Azure DevOps Example

```yaml
trigger:
- main

pool:
  vmImage: 'ubuntu-latest'

steps:
- task: TerraformInstaller@0
  inputs:
    terraformVersion: 'latest'
    
- script: |
    curl -s https://raw.githubusercontent.com/terraform-linters/tflint/master/install_linux.sh | bash
  displayName: 'Install TFLint'
  
- script: |
    # Use MCP server for TFLint analysis
    # Integration would depend on your MCP client setup
  displayName: 'Run TFLint Analysis'
```

## Best Practices

### Rule Configuration
1. **Start with defaults**: Begin with the default ruleset
2. **Gradually customize**: Add or disable rules based on your needs
3. **Document exceptions**: Clearly document any disabled rules

### Plugin Management
1. **Pre-install plugins**: In CI/CD, pre-install plugins to avoid API rate limits
2. **Use GitHub tokens**: Set `GITHUB_TOKEN` environment variable for authentication
3. **Cache plugin installations**: Cache plugins between runs

### Output Processing
1. **Use JSON format**: Easier to parse and integrate with other tools
2. **Set up notifications**: Configure alerts for critical issues
3. **Track metrics**: Monitor code quality trends over time

### Workspace Organization
1. **Consistent structure**: Use consistent directory structures
2. **Modular design**: Organize code into reusable modules
3. **Recursive analysis**: Use recursive analysis for complex projects

## Troubleshooting

### Common Issues

1. **TFLint not found**
   - Ensure TFLint is installed and in PATH
   - Check `tflint --version` works

2. **Plugin initialization failed**
   - Check internet connectivity
   - Verify GitHub API access
   - Consider disabling Azure plugin temporarily

3. **No Terraform files found**
   - Ensure directory contains `.tf` or `.tf.json` files
   - Check file permissions
   - Verify correct workspace path

4. **Analysis timeout**
   - Large projects may need longer timeout
   - Consider analyzing smaller modules separately
   - Use non-recursive analysis for better performance

### Debug Tips

1. **Enable verbose output**: Use different output formats for debugging
2. **Test incrementally**: Start with simple configurations
3. **Check logs**: Review error messages for specific issues
4. **Validate separately**: Run TFLint directly to isolate issues

## Additional Resources

- [TFLint Documentation](https://github.com/terraform-linters/tflint)
- [Azure Ruleset Plugin](https://github.com/terraform-linters/tflint-ruleset-azurerm)
- [TFLint Rules Reference](https://github.com/terraform-linters/tflint/tree/master/docs/rules)
- [Terraform Best Practices](https://www.terraform.io/docs/extend/best-practices/index.html)