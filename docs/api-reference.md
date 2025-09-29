# API Reference

This document provides a complete reference for all available tools in the Azure Terraform MCP Server.

## Tool Categories

- [Documentation Tools](#documentation-tools)
- [Terraform Command Tools](#terraform-command-tools)
- [Security & Validation Tools](#security--validation-tools)
- [Azure Export Tools](#azure-export-tools)
- [Source Code Analysis Tools](#source-code-analysis-tools)
- [Best Practices Tools](#best-practices-tools)

---

## Documentation Tools

### `get_avm_modules`

Retrieves all available Azure Verified Modules.

**Parameters:** None

**Returns:**
```json
[
  {
    "module_name": "avm-res-compute-virtualmachine",
    "description": "Azure Virtual Machine module",
    "source": "Azure/avm-res-compute-virtualmachine/azurerm"
  }
]
```

**Example:**
```json
{
  "tool": "get_avm_modules",
  "arguments": {}
}
```

### `get_avm_latest_version`

Retrieves the latest version of a specified Azure Verified Module.

**Parameters:**
- `module_name` (required): Module name (e.g., "avm-res-compute-virtualmachine")

**Returns:** Latest version string

**Example:**
```json
{
  "tool": "get_avm_latest_version",
  "arguments": {
    "module_name": "avm-res-compute-virtualmachine"
  }
}
```

### `get_avm_versions`

Retrieves all available versions of a specified Azure Verified Module.

**Parameters:**
- `module_name` (required): Module name

**Returns:** Array of available versions

### `get_avm_variables`

Retrieves input variables schema for a specific AVM module version.

**Parameters:**
- `module_name` (required): Module name
- `module_version` (required): Module version

**Returns:** Variables schema with descriptions and types

### `get_avm_outputs`

Retrieves output definitions for a specific AVM module version.

**Parameters:**
- `module_name` (required): Module name
- `module_version` (required): Module version

**Returns:** Output definitions schema

### `get_azurerm_provider_documentation`

Retrieves specific AzureRM resource or data source documentation.

**Parameters:**
- `resource_type_name` (required): Resource name (e.g., "storage_account")
- `doc_type` (required): "resource" or "data-source"
- `argument_name` (optional): Specific argument/attribute name

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
- `resource_type_name` (required): Azure API resource type (e.g., "Microsoft.Storage/storageAccounts@2021-04-01")

**Returns:** AzAPI schema and documentation

**Example:**
```json
{
  "tool": "get_azapi_provider_documentation",
  "arguments": {
    "resource_type_name": "Microsoft.Storage/storageAccounts@2021-04-01"
  }
}
```

---

## Terraform Command Tools

### `run_terraform_command`

Execute Terraform CLI commands inside a workspace folder.

**Parameters:**
- `command` (required): Terraform command ("init", "plan", "apply", "destroy", "validate", "fmt")
- `workspace_folder` (required): Workspace folder containing Terraform files
- `auto_approve` (optional): Auto-approve for apply/destroy commands (default: false)
- `upgrade` (optional): Upgrade providers/modules for init command (default: false)

**Returns:** Command execution results including stdout, stderr, and exit code

**Example:**
```json
{
  "tool": "run_terraform_command",
  "arguments": {
    "command": "plan",
    "workspace_folder": "workspace/demo",
    "upgrade": false
  }
}
```

---

## Security & Validation Tools

### `check_conftest_installation`

Check Conftest installation status and version.

**Parameters:** None

**Returns:** Installation status and version information

### `run_conftest_workspace_validation`

Validate Terraform files in a workspace against Azure security policies.

**Parameters:**
- `workspace_folder` (required): Workspace folder path
- `policy_set` (optional): Policy set name ("avmsec", "Azure-Proactive-Resiliency-Library-v2", "all")
- `severity_filter` (optional): Severity filter ("low", "medium", "high")

**Returns:** Policy validation results

### `run_conftest_workspace_plan_validation`

Validate Terraform plan files against Azure security policies.

**Parameters:**
- `folder_name` (required): Folder containing plan files
- `policy_set` (optional): Policy set name

**Returns:** Plan validation results

### `check_tflint_installation`

Check TFLint installation status and version.

**Parameters:** None

**Returns:** Installation status and version information

### `run_tflint_workspace_analysis`

Run TFLint static analysis on workspace folders.

**Parameters:**
- `workspace_folder` (required): Workspace folder path
- `output_format` (optional): Output format ("default", "json", "checkstyle")
- `recursive` (optional): Enable recursive scanning (default: true)
- `enable_azure_plugin` (optional): Enable Azure plugin (default: true)
- `enable_rules` (optional): Array of rules to enable
- `disable_rules` (optional): Array of rules to disable

**Returns:** Static analysis results

---

## Azure Export Tools

### `check_aztfexport_installation`

Check Azure Export for Terraform installation status.

**Parameters:** None

**Returns:** Installation status and version

### `export_azure_resource`

Export a single Azure resource to Terraform configuration.

**Parameters:**
- `resource_id` (required): Azure resource ID
- `output_folder_name` (optional): Output folder name
- `provider` (optional): Terraform provider ("azurerm" or "azapi", default: "azurerm")
- `resource_name` (optional): Terraform resource name
- `dry_run` (optional): Perform dry run (default: false)

**Returns:** Export results

### `export_azure_resource_group`

Export an entire Azure resource group to Terraform configuration.

**Parameters:**
- `resource_group_name` (required): Resource group name
- `output_folder_name` (optional): Output folder name
- `provider` (optional): Terraform provider (default: "azurerm")
- `include_role_assignment` (optional): Include role assignments (default: false)
- `parallelism` (optional): Number of parallel operations (default: 10)
- `continue_on_error` (optional): Continue on errors (default: false)

**Returns:** Export results

### `export_azure_resources_by_query`

Export Azure resources using Azure Resource Graph queries.

**Parameters:**
- `query` (required): Azure Resource Graph query
- `output_folder_name` (optional): Output folder name
- `provider` (optional): Terraform provider (default: "azurerm")
- `name_pattern` (optional): Resource naming pattern
- `dry_run` (optional): Perform dry run (default: false)

**Returns:** Export results

### `get_aztfexport_config`

Get aztfexport configuration settings.

**Parameters:**
- `key` (optional): Specific config key to retrieve

**Returns:** Configuration settings

### `set_aztfexport_config`

Set aztfexport configuration settings.

**Parameters:**
- `key` (required): Configuration key
- `value` (required): Configuration value

**Returns:** Update status

---

## Source Code Analysis Tools

### `get_terraform_source_providers`

Get all supported Terraform provider names for source code analysis.

**Parameters:** None

**Returns:** Dictionary with supported providers list

### `query_terraform_source_code`

Read Terraform provider source code for a given Terraform block.

**Parameters:**
- `block_type` (required): Terraform block type ("resource", "data", "ephemeral")
- `terraform_type` (required): Terraform type (e.g., "azurerm_resource_group")
- `entrypoint_name` (required): Function/method name:
  - For `resource`: "create", "read", "update", "delete", "schema", "attribute"
  - For `data`: "read", "schema", "attribute"
  - For `ephemeral`: "open", "close", "renew", "schema"
- `tag` (optional): Version tag

**Returns:** Source code as string

**Example:**
```json
{
  "tool": "query_terraform_source_code",
  "arguments": {
    "block_type": "resource",
    "terraform_type": "azurerm_resource_group",
    "entrypoint_name": "create"
  }
}
```

### `get_golang_namespaces`

Get available golang namespaces for source code analysis.

**Parameters:** None

**Returns:** Dictionary with available namespaces

### `get_golang_namespace_tags`

Get supported version tags for a golang namespace.

**Parameters:**
- `namespace` (required): Golang namespace to get tags for

**Returns:** Dictionary with available tags

### `query_golang_source_code`

Read golang source code for functions, methods, types, and variables.

**Parameters:**
- `namespace` (required): Golang namespace to query
- `symbol` (required): Symbol type ("func", "method", "type", "var")
- `name` (required): Name of the symbol
- `receiver` (optional): Method receiver type (required for methods)
- `tag` (optional): Version tag

**Returns:** Source code as string

**Example:**
```json
{
  "tool": "query_golang_source_code",
  "arguments": {
    "namespace": "github.com/hashicorp/terraform-provider-azurerm",
    "symbol": "func",
    "name": "resourceGroupCreateFunc"
  }
}
```

---

## Best Practices Tools

### `get_azure_best_practices`

Get comprehensive Azure and Terraform best practices for specific resources and actions.

**Parameters:**
- `resource` (required): Resource type ("general", "azurerm", "azapi", "security", "compute", "database", "storage", "monitoring")
- `action` (optional): Action type ("code-generation", "deployment", "security") (default: "code-generation")

**Returns:** Formatted best practices recommendations

**Examples:**
```json
{
  "tool": "get_azure_best_practices",
  "arguments": {
    "resource": "general",
    "action": "code-generation"
  }
}
```

```json
{
  "tool": "get_azure_best_practices",
  "arguments": {
    "resource": "azapi",
    "action": "code-generation"
  }
}
```

```json
{
  "tool": "get_azure_best_practices",
  "arguments": {
    "resource": "security",
    "action": "security"
  }
}
```

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

## Rate Limiting

Some tools may implement rate limiting for external API calls. Check individual tool documentation for specific limits.

## Authentication

Tools requiring Azure authentication will use the configured Azure Service Principal credentials or Azure CLI authentication. See the [Azure Authentication Guide](azure-authentication.md) for setup instructions.