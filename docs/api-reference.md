# API Reference

This document provides a complete reference for all available tools in the Azure Terraform MCP Server.

## Tool Categories

- [Documentation Tools](#documentation-tools)
- [Azure Export Tools](#azure-export-tools)
- [Terraform Coverage Audit Tools](#terraform-coverage-audit-tools)

---

## Documentation Tools

### `get_azurerm_provider_documentation`

Retrieves specific AzureRM resource or data source documentation.

**Parameters:**
- `resource_type_name` (required): Resource name (e.g., "storage_account")
- `doc_type` (optional): "resource" or "data-source" (default: "resource")
- `argument_name` (optional): Specific argument name to retrieve details for
- `attribute_name` (optional): Specific attribute name to retrieve details for

**Returns:** Comprehensive documentation including arguments, attributes, and examples

**Example:**
```json
{
  "tool": "get_azurerm_provider_documentation",
  "arguments": {
    "resource_type_name": "storage_account",
    "doc_type": "resource",
    "argument_name": "account_tier"
  }
}
```

### `get_azapi_provider_documentation`

Retrieves AzAPI resource schemas and documentation.

**Parameters:**
- `resource_type_name` (required): Azure API resource type (e.g., "Microsoft.Storage/storageAccounts")

**Returns:** AzAPI schema and documentation

**Example:**
```json
{
  "tool": "get_azapi_provider_documentation",
  "arguments": {
    "resource_type_name": "Microsoft.Storage/storageAccounts"
  }
}
```

---

## Azure Export Tools

### `check_aztfexport_installation`

Check Azure Export for Terraform installation status.

**Parameters:** None

**Returns:** Installation status and version

### `export_azure_resource`

Export a single Azure resource to Terraform configuration.

**Parameters:**
- `resource_id` (required): Azure resource ID to export (e.g., `/subscriptions/.../providers/Microsoft.Storage/storageAccounts/myaccount`)
- `output_folder_name` (optional): Output folder name (created under workspace root, auto-generated if not specified)
- `provider` (optional): Terraform provider - `"azurerm"` (default) or `"azapi"`
- `resource_name` (optional): Custom resource name in generated Terraform
- `resource_type` (optional): Custom resource type in generated Terraform
- `dry_run` (optional): Perform dry run without creating files (default: false)
- `include_role_assignment` (optional): Include role assignments (default: false)
- `parallelism` (optional): Number of parallel operations 1-50 (default: 10)
- `continue_on_error` (optional): Continue if some resources fail (default: false)

**Returns:** Export result with generated files, status, and any errors

**Example:**
```json
{
  "tool": "export_azure_resource",
  "arguments": {
    "resource_id": "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/my-rg/providers/Microsoft.Storage/storageAccounts/mystorageaccount",
    "provider": "azurerm",
    "output_folder_name": "exported-storage"
  }
}
```

### `export_azure_resource_group`

Export an entire Azure resource group to Terraform configuration.

**Parameters:**
- `resource_group_name` (required): Name of the resource group (not the full ID, just the name)
- `output_folder_name` (optional): Output folder name (created under workspace root, auto-generated if not specified)
- `provider` (optional): Terraform provider - `"azurerm"` (default) or `"azapi"`
- `name_pattern` (optional): Pattern for resource naming in Terraform
- `type_pattern` (optional): Pattern for filtering resource types
- `dry_run` (optional): Perform dry run without creating files (default: false)
- `include_role_assignment` (optional): Include role assignments (default: false)
- `parallelism` (optional): Number of parallel operations 1-50 (default: 10)
- `continue_on_error` (optional): Continue if some resources fail (default: false)

**Returns:** Export result with generated files, status, and any errors

**Example:**
```json
{
  "tool": "export_azure_resource_group",
  "arguments": {
    "resource_group_name": "my-production-rg",
    "provider": "azurerm",
    "continue_on_error": true
  }
}
```

### `export_azure_resources_by_query`

Export Azure resources using Azure Resource Graph queries.

**Parameters:**
- `query` (required): Azure Resource Graph WHERE clause (e.g., `"type =~ 'Microsoft.Storage/storageAccounts' and location == 'eastus'"`)
- `output_folder_name` (optional): Output folder name (created under workspace root, auto-generated if not specified)
- `provider` (optional): Terraform provider - `"azurerm"` (default) or `"azapi"`
- `name_pattern` (optional): Pattern for resource naming in Terraform
- `type_pattern` (optional): Pattern for filtering resource types
- `dry_run` (optional): Perform dry run without creating files (default: false)
- `include_role_assignment` (optional): Include role assignments (default: false)
- `parallelism` (optional): Number of parallel operations 1-50 (default: 10)
- `continue_on_error` (optional): Continue if some resources fail (default: false)

**Returns:** Export result with generated files, status, and any errors

**Example:**
```json
{
  "tool": "export_azure_resources_by_query",
  "arguments": {
    "query": "type =~ 'Microsoft.Compute/virtualMachines' and location == 'westus2'",
    "provider": "azurerm"
  }
}
```

---

## Terraform Coverage Audit Tools

### `audit_terraform_coverage`

Audit Terraform coverage of Azure resources to identify gaps, orphaned resources, and measure management coverage.

**Description:**  
Analyzes your Azure environment and compares it against your Terraform state to provide a comprehensive coverage report. Helps identify Azure resources not under Terraform management and Terraform resources that no longer exist in Azure.

**Parameters:**
- `workspace_folder` (required): Terraform workspace folder to audit
- `scope` (required): Audit scope - "resource-group", "subscription", or "query"
- `scope_value` (required): Scope-specific value:
  - For "resource-group": Resource group name
  - For "subscription": Azure subscription ID
  - For "query": Azure Resource Graph WHERE clause
- `include_non_terraform_resources` (optional): Include Azure resources not in Terraform (default: true)
- `include_orphaned_terraform_resources` (optional): Include Terraform resources not in Azure (default: true)

**Returns:**
```json
{
  "success": true,
  "summary": {
    "total_azure_resources": 45,
    "total_terraform_resources": 38,
    "terraform_managed": 36,
    "coverage_percentage": 80.0,
    "missing_from_terraform": 9,
    "orphaned_in_terraform": 2
  },
  "managed_resources": [...],
  "missing_resources": [...],
  "orphaned_resources": [...],
  "recommendations": [...]
}
```

**Example - Resource Group Audit:**
```json
{
  "tool": "audit_terraform_coverage",
  "arguments": {
    "workspace_folder": "workspace/prod-infra",
    "scope": "resource-group",
    "scope_value": "prod-rg-eastus"
  }
}
```

**Example - Subscription Audit:**
```json
{
  "tool": "audit_terraform_coverage",
  "arguments": {
    "workspace_folder": "workspace/subscription-infra",
    "scope": "subscription",
    "scope_value": "12345678-1234-1234-1234-123456789012"
  }
}
```

**Example - Custom Query:**
```json
{
  "tool": "audit_terraform_coverage",
  "arguments": {
    "workspace_folder": "workspace/storage-infra",
    "scope": "query",
    "scope_value": "type =~ 'Microsoft.Storage/storageAccounts' and location == 'eastus'"
  }
}
```

**Prerequisites:**
- Terraform workspace must be initialized (`terraform init`)
- Valid Terraform state file must exist
- Azure CLI must be authenticated (`az login`)
- Azure Resource Graph access permissions required

**See Also:**
- [Terraform Coverage Audit Guide](terraform-coverage-audit.md)
- [Azure Export Tools](#azure-export-tools)

---

## Error Handling

All tools return structured error responses when issues occur:

```json
{
  "error": "Error description",
  "details": "Additional error context",
  "suggestions": ["Possible solutions"]
}
```

## Authentication

Tools requiring Azure authentication will use the configured Azure Service Principal credentials or Azure CLI authentication. See the [Azure Authentication Guide](azure-authentication.md) for setup instructions.
