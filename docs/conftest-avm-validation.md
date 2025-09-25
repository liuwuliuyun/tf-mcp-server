# Conftest Azure Policy Validation

This document describes the Conftest Azure policy validation tools in the Azure Terraform MCP Server.

## Overview

The Conftest Azure policy validation tools provide integration with Azure security policies and best practices, allowing you to validate your Terraform configurations against comprehensive policy sets using Conftest. This includes validation for azurerm, azapi, and AVM (Azure Verified Modules) providers.

## Features

- **Comprehensive Azure Policy Validation**: Validate Terraform configurations against Azure security policies and best practices
- **Multiple Provider Support**: Works with azurerm, azapi, and AVM (Azure Verified Modules) providers
- **Multiple Policy Sets**: Support for different policy sets including:
  - `all`: All available policies
  - `Azure-Proactive-Resiliency-Library-v2`: Resiliency-focused policies
  - `avmsec`: Security-focused policies
- **Severity Filtering**: Filter avmsec policies by severity level (high, medium, low, info)
- **Flexible Input**: Support for both Terraform HCL content and pre-generated plan JSON
- **Custom Policies**: Support for additional custom policy paths

## Prerequisites

1. **Conftest**: The tool requires Conftest to be installed and available in your system PATH.
   
   Installation options:
   - Windows: `scoop install conftest` or download from [releases](https://github.com/open-policy-agent/conftest/releases)
   - macOS: `brew install conftest`
   - Linux: Download from [releases](https://github.com/open-policy-agent/conftest/releases)
   - Go: `go install github.com/open-policy-agent/conftest@latest`

2. **Terraform**: Required for HCL validation (when not providing pre-generated plan JSON)

## Available Tools

### 1. `run_conftest_validation`

Validate Terraform HCL content against Azure security policies and best practices using Conftest.

This tool supports comprehensive validation of Azure resources using azurerm, azapi, and AVM (Azure Verified Modules) providers with security checks, compliance rules, and operational best practices.

**Parameters:**
- `hcl_content` (required): Terraform HCL content to validate
- `policy_set` (optional, default: "all"): Policy set to use
- `severity_filter` (optional): Severity filter for avmsec policies
- `custom_policies` (optional): Comma-separated list of custom policy paths

**Returns:**
- Validation success status
- List of policy violations
- Summary with violation counts

### 2. `run_conftest_workspace_validation`

Validate Terraform files in a workspace folder against Azure security policies and best practices using Conftest.

This tool validates all `.tf` files in the specified workspace folder, similar to how aztfexport creates folders under `/workspace`. It automatically runs `terraform init`, `terraform plan`, and validates the resulting plan.

**Parameters:**
- `folder_name` (required): Name of the folder under `/workspace` to validate (e.g., "exported-rg-acctest0001")
- `policy_set` (optional, default: "all"): Policy set to use
- `severity_filter` (optional): Severity filter for avmsec policies  
- `custom_policies` (optional): Comma-separated list of custom policy paths

**Returns:**
- Validation success status
- List of policy violations
- Summary with violation counts
- Workspace folder information and list of Terraform files

### 3. `run_conftest_plan_validation`

Validate Terraform plan JSON against Azure security policies and best practices using Conftest.

This tool validates a pre-generated Terraform plan in JSON format, useful when you already have a plan file.

**Parameters:**
- `terraform_plan_json` (required): Terraform plan in JSON format
- `policy_set` (optional, default: "all"): Policy set to use
- `severity_filter` (optional): Severity filter for avmsec policies
- `custom_policies` (optional): Comma-separated list of custom policy paths

**Returns:**
- Validation success status
- List of policy violations
- Summary with violation counts

### 4. `run_conftest_workspace_plan_validation`

Validate Terraform plan files in a workspace folder against Azure security policies using Conftest.

This tool validates existing plan files (`.tfplan`, `tfplan.binary`) in the specified workspace folder, or creates a new plan if only `.tf` files are present. Works with folders created by aztfexport or other Terraform operations in the `/workspace` directory.

**Parameters:**
- `folder_name` (required): Name of the folder under `/workspace` containing the plan file (e.g., "exported-rg-acctest0001")
- `policy_set` (optional, default: "all"): Policy set to use
- `severity_filter` (optional): Severity filter for avmsec policies
- `custom_policies` (optional): Comma-separated list of custom policy paths

**Returns:**
- Validation success status  
- List of policy violations
- Summary with violation counts
- Workspace folder information and plan file path
- Detailed violation information

### 2. `run_conftest_plan_validation`

Validate pre-generated Terraform plan JSON against Azure security policies and best practices using Conftest.

This tool supports comprehensive validation of Azure resources using azurerm, azapi, and AVM (Azure Verified Modules) providers with security checks, compliance rules, and operational best practices.

**Parameters:**
- `terraform_plan_json` (required): Terraform plan in JSON format
- `policy_set` (optional, default: "all"): Policy set to use
- `severity_filter` (optional): Severity filter for avmsec policies
- `custom_policies` (optional): Comma-separated list of custom policy paths

**Returns:**
- Same as `run_conftest_validation`

## Policy Sets

### 1. All Policies (`all`)
Runs all available policies from the Azure Policy Library AVM.

### 2. Azure Proactive Resiliency Library v2 (`Azure-Proactive-Resiliency-Library-v2`)
Focuses on resilience and reliability best practices for Azure resources.

### 3. Azure Verified Module Security Ruleset (`avmsec`)
Security-focused policies inspired by Bridgecrew Checkov rules.

#### Severity Levels for avmsec:
- `high`: Critical security issues
- `medium`: Important security considerations  
- `low`: Minor security improvements
- `info`: Informational security notices

## Usage Examples

### Example 1: Basic Validation with All Policies

```python
from tf_mcp_server.tools.conftest_avm_runner import get_conftest_avm_runner
import asyncio

async def validate_terraform():
    runner = get_conftest_avm_runner()
    
    hcl_content = '''
    resource "azurerm_storage_account" "example" {
      name                     = "examplestorageacct"
      resource_group_name      = "example-rg"
      location                 = "West Europe"
      account_tier             = "Standard"
      account_replication_type = "LRS"
    }
    '''
    
    result = await runner.validate_terraform_hcl_with_avm_policies(
        hcl_content=hcl_content,
        policy_set="all"
    )
    
    print(f"Validation Success: {result['success']}")
    print(f"Total Violations: {result['summary']['total_violations']}")
    
    for violation in result['violations']:
        print(f"- {violation['policy']}: {violation['message']}")

asyncio.run(validate_terraform())
```

### Example 2: Security-Only Validation with High Severity Filter

```python
result = await runner.validate_terraform_hcl_with_avm_policies(
    hcl_content=hcl_content,
    policy_set="avmsec",
    severity_filter="high"
)
```

### Example 3: Resiliency-Only Validation

```python
result = await runner.validate_terraform_hcl_with_avm_policies(
    hcl_content=hcl_content,
    policy_set="Azure-Proactive-Resiliency-Library-v2"
)
```

### Example 4: Validating Pre-Generated Plan JSON

```python
# Generate plan JSON first
# terraform plan -out=tfplan.binary && terraform show -json tfplan.binary > tfplan.json

with open('tfplan.json', 'r') as f:
    plan_json = f.read()

result = await runner.validate_with_avm_policies(
    terraform_plan_json=plan_json,
    policy_set="avmsec"
)
```

## Common Policy Violations

### Security Violations (avmsec)
- Storage accounts without customer-managed encryption keys
- Resources allowing public access
- Missing network security groups
- Insecure authentication configurations

### Resiliency Violations (Azure-Proactive-Resiliency-Library-v2)
- Resources not configured for zone redundancy
- Missing backup configurations
- Single points of failure
- Inadequate disaster recovery settings

## Response Format

All validation tools return a standardized response format:

```json
{
  "success": boolean,
  "policy_set": "string",
  "severity_filter": "string|null",
  "total_violations": number,
  "violations": [
    {
      "filename": "string",
      "level": "failure|warning",
      "policy": "string",
      "message": "string",
      "metadata": {}
    }
  ],
  "summary": {
    "total_violations": number,
    "failures": number,
    "warnings": number,
    "policy_set_used": "string"
  },
  "command_output": "string|null",
  "command_error": "string|null"
}
```

## Error Handling

The tools provide comprehensive error handling for common scenarios:

- Missing Conftest installation
- Invalid Terraform syntax
- Network issues when downloading policies
- Timeout during policy execution
- Invalid policy set names

## Best Practices

1. **Start with High Severity**: Begin validation with `avmsec` high severity policies to focus on critical security issues.

2. **Use Multiple Policy Sets**: Run validation against different policy sets to get comprehensive coverage.

3. **Integrate into CI/CD**: Use these tools in your CI/CD pipeline to catch policy violations early.

4. **Review Violations Regularly**: Regularly review and address policy violations to maintain security and compliance.

5. **Custom Policies**: Consider adding organization-specific policies alongside AVM policies.

## Troubleshooting

### Conftest Not Found
If you get "Conftest not found" errors:
1. Ensure Conftest is installed
2. Verify it's in your system PATH
3. Check the installation using `conftest --version`

### Policy Download Issues
If policies fail to download:
1. Check your internet connection
2. Verify access to GitHub
3. Consider using a VPN if behind corporate firewall

### Terraform Errors
If Terraform operations fail:
1. Ensure Terraform is installed and in PATH
2. Check that your HCL syntax is valid
3. Verify provider configurations are correct

## Integration with MCP Server

These tools are automatically integrated into the Azure Terraform MCP Server and can be accessed via the MCP protocol. The tools are registered as:

- `run_conftest_validation` - Validate raw HCL content
- `run_conftest_workspace_validation` - Validate .tf files in a workspace folder
- `run_conftest_plan_validation` - Validate raw plan JSON content  
- `run_conftest_workspace_plan_validation` - Validate plan files in a workspace folder

### Workflow Integration

The workspace-based tools are designed to work seamlessly with other tools in the MCP server:

1. **With AzTFExport**: After using `aztfexport_resource` to export Azure resources to a workspace folder, use `run_conftest_workspace_validation` to validate the exported Terraform files.

2. **Continuous Validation**: Run workspace validation after making changes to Terraform files in workspace folders to ensure compliance with Azure policies.

3. **Plan Validation**: Use `run_conftest_workspace_plan_validation` when you have existing plan files or want to validate plans without re-running Terraform operations.

## Contributing

To contribute to the Conftest AVM integration:

1. Follow the existing code patterns in `conftest_avm_runner.py`
2. Add comprehensive tests for new functionality
3. Update documentation for any new features
4. Ensure compatibility with the latest Conftest and AVM policy versions

## References

- [Azure Policy Library AVM](https://github.com/Azure/policy-library-avm)
- [Conftest Documentation](https://www.conftest.dev/)
- [Open Policy Agent](https://www.openpolicyagent.org/)
- [Azure Proactive Resiliency Library v2](https://azure.github.io/Azure-Proactive-Resiliency-Library-v2/)
