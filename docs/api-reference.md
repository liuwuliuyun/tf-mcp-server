# API Reference

This document provides a complete reference for all available tools in the Azure Terraform MCP Server.

## Tool Categories

- [Documentation Tools](#documentation-tools)
- [Terraform Command Tools](#terraform-command-tools)
- [Security & Validation Tools](#security--validation-tools)
- [Azure Export Tools](#azure-export-tools)
- [Terraform Coverage Audit Tools](#terraform-coverage-audit-tools)
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

Execute Terraform CLI commands and state management operations in a workspace folder.

**Description:**  
A unified tool for running all Terraform commands including initialization, planning, applying changes, validation, formatting, and comprehensive state management operations. This is the primary tool for interacting with Terraform workspaces.

**IMPORTANT:** Always use this tool to run Terraform commands instead of running them directly in bash/terminal, especially after using aztfexport or other workspace folder operations.

**Parameters:**
- `command` (required): Terraform command to execute
  - `"init"` - Initialize Terraform working directory
  - `"plan"` - Show execution plan for changes
  - `"apply"` - Apply changes to create/update resources
  - `"destroy"` - Destroy Terraform-managed resources
  - `"validate"` - Validate configuration files
  - `"fmt"` - Format configuration files
  - `"state"` - State management operations (requires `state_subcommand`)
- `workspace_folder` (required): Workspace folder containing Terraform files
- `auto_approve` (optional): Auto-approve for apply/destroy commands (default: `false`)
  - **USE WITH CAUTION!** Bypasses confirmation prompts
- `upgrade` (optional): Upgrade providers/modules during init (default: `false`)
- `state_subcommand` (optional): State operation to perform (required when `command="state"`)
  - `"list"` - List all resources in state
  - `"show"` - Show details of a specific resource
  - `"mv"` - Move/rename a resource in state
  - `"rm"` - Remove a resource from state
  - `"pull"` - Pull current state and output to stdout
  - `"push"` - Push a local state file to remote backend
- `state_args` (optional): Arguments for the state subcommand
  - For `"mv"`: `"source destination"` (e.g., `"azurerm_resource_group.old azurerm_resource_group.new"`)
  - For `"show"` or `"rm"`: resource address (e.g., `"azurerm_storage_account.main"`)
  - Leave empty for `"list"`, `"pull"`, `"push"`

**Returns:**
```json
{
  "command": "plan",
  "success": true,
  "exit_code": 0,
  "stdout": "Terraform output...",
  "stderr": "",
  "workspace_folder": "workspace/demo"
}
```

**Example - Initialize Workspace:**
```json
{
  "tool": "run_terraform_command",
  "arguments": {
    "command": "init",
    "workspace_folder": "workspace/demo"
  }
}
```

**Example - Plan with Upgrade:**
```json
{
  "tool": "run_terraform_command",
  "arguments": {
    "command": "init",
    "workspace_folder": "workspace/demo",
    "upgrade": true
  }
}
```

**Example - Plan Changes:**
```json
{
  "tool": "run_terraform_command",
  "arguments": {
    "command": "plan",
    "workspace_folder": "workspace/demo"
  }
}
```

**Example - Apply Changes:**
```json
{
  "tool": "run_terraform_command",
  "arguments": {
    "command": "apply",
    "workspace_folder": "workspace/demo",
    "auto_approve": false
  }
}
```

**Example - Format Code:**
```json
{
  "tool": "run_terraform_command",
  "arguments": {
    "command": "fmt",
    "workspace_folder": "workspace/demo"
  }
}
```

**Example - List State Resources:**
```json
{
  "tool": "run_terraform_command",
  "arguments": {
    "command": "state",
    "state_subcommand": "list",
    "workspace_folder": "workspace/demo"
  }
}
```

**Example - Show Resource Details:**
```json
{
  "tool": "run_terraform_command",
  "arguments": {
    "command": "state",
    "state_subcommand": "show",
    "state_args": "azurerm_resource_group.main",
    "workspace_folder": "workspace/demo"
  }
}
```

**Example - Rename Resource:**
```json
{
  "tool": "run_terraform_command",
  "arguments": {
    "command": "state",
    "state_subcommand": "mv",
    "state_args": "azurerm_resource_group.res-0 azurerm_resource_group.main",
    "workspace_folder": "workspace/demo"
  }
}
```

**Example - Remove Resource from State:**
```json
{
  "tool": "run_terraform_command",
  "arguments": {
    "command": "state",
    "state_subcommand": "rm",
    "state_args": "azurerm_virtual_network.old",
    "workspace_folder": "workspace/demo"
  }
}
```

**See Also:**
- [Terraform Commands Guide](terraform-commands.md)
- [State Management Guide](terraform-state-management.md)

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

## Terraform Coverage Audit Tools

### `audit_terraform_coverage`

Audit Terraform coverage of Azure resources to identify gaps, orphaned resources, and measure management coverage.

**Description:**  
Analyzes your Azure environment and compares it against your Terraform state to provide a comprehensive coverage report. Helps identify Azure resources not under Terraform management and Terraform resources that no longer exist in Azure.

**Parameters:**
- `workspace_folder` (required): Terraform workspace folder to audit
- `scope` (optional): Audit scope - "resource-group", "subscription", or "query" (default: "resource-group")
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
  "managed_resources": [
    {
      "azure_resource_id": "/subscriptions/.../storageAccounts/mystore",
      "azure_resource_type": "Microsoft.Storage/storageAccounts",
      "azure_resource_name": "mystore",
      "terraform_address": "azurerm_storage_account.mystore",
      "match_confidence": "high"
    }
  ],
  "missing_resources": [
    {
      "resource_id": "/subscriptions/.../storageAccounts/unmanaged",
      "resource_type": "Microsoft.Storage/storageAccounts",
      "resource_name": "unmanaged",
      "suggested_terraform_types": ["azurerm_storage_account"],
      "location": "eastus",
      "export_command": "Use export_azure_resource with resource_id='...'"
    }
  ],
  "orphaned_resources": [
    {
      "terraform_address": "azurerm_virtual_network.old_vnet",
      "reason": "Resource not found in Azure or could not be matched"
    }
  ],
  "recommendations": [
    "Export 9 unmanaged resources using aztfexport tools",
    "Review 2 orphaned resources in Terraform state"
  ]
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