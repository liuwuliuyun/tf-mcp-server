# Azure Best Practices Tool

The `get_azure_best_practices` tool provides comprehensive best practices for working with Azure resources using Terraform, including specialized guidance for code cleanup and production-ready transformations.

## 🚀 Overview

This tool delivers context-aware best practices recommendations for:
- Writing Terraform code for Azure resources
- Transforming exported code to production-ready
- Managing state files safely
- Security hardening and compliance
- Provider-specific optimizations (AzureRM 4.x, AzAPI 2.x)

## 📋 Tool Reference

### `get_azure_best_practices`

**Parameters:**
- `resource` (optional): Resource type or area (default: "general")
  - Options: `general`, `azurerm`, `azapi`, `aztfexport`, `security`, `networking`, `storage`, `compute`, `database`, `monitoring`, `deployment`
- `action` (optional): Action type (default: "code-generation")
  - Options: `code-generation`, `code-cleanup`, `deployment`, `configuration`, `security`, `performance`, `cost-optimization`

**Returns:** Formatted markdown with categorized best practices and recommendations

---

## 🆕 Featured: Code Cleanup Workflow

### Aztfexport Code Cleanup

Transform exported Terraform code to production-ready:

```json
{
  "tool": "get_azure_best_practices",
  "arguments": {
    "resource": "aztfexport",
    "action": "code-cleanup"
  }
}
```

**This returns comprehensive guidance on:**

#### 1. Resource Naming and Renaming
- Replace generic names (res-0, res-1) with meaningful names
- Use consistent naming conventions
- Safe resource renaming using terraform state commands

#### 2. Variables vs Locals
- **Use VARIABLES for**: location, names, IP ranges, SKU sizes (user-changeable values)
- **Use LOCALS for**: computed values, tags, naming patterns, transformations
- Clear examples and recommendations

#### 3. Code Structure
- File organization (variables.tf, locals.tf, main.tf, outputs.tf)
- Logical grouping of resources
- Comment best practices

#### 4. Production Readiness
- Lifecycle blocks (prevent_destroy, ignore_changes)
- Comprehensive tagging
- Output definitions
- Validation blocks

#### 5. Security Hardening
- Network security reviews
- Diagnostic settings and logging
- Key Vault integration
- Private endpoints

#### 6. State File Management
- Safe state operations using run_terraform_command
- Backup procedures
- Testing strategies
- Audit trail documentation

**Example Complete Workflow:**
```json
# Step 1: Export resources
{
  "tool": "export_azure_resource_group",
  "arguments": {
    "resource_group_name": "myapp-rg",
    "output_folder_name": "myapp"
  }
}

# Step 2: Get code cleanup guidance
{
  "tool": "get_azure_best_practices",
  "arguments": {
    "resource": "aztfexport",
    "action": "code-cleanup"
  }
}

# Step 3: List resources
{
  "tool": "run_terraform_command",
  "arguments": {
    "command": "state",
    "workspace_folder": "myapp",
    "state_subcommand": "list"
  }
}

# Step 4: Refactor .tf files based on guidance

# Step 5: Rename resources in state
{
  "tool": "run_terraform_command",
  "arguments": {
    "command": "state",
    "workspace_folder": "myapp",
    "state_subcommand": "mv",
    "state_args": "azurerm_resource_group.res-0 azurerm_resource_group.main"
  }
}

# Step 6: Verify
{
  "tool": "run_terraform_command",
  "arguments": {
    "command": "plan",
    "workspace_folder": "myapp"
  }
}
```

---

## 📖 Usage Examples

### Basic Usage

### Get general Azure Terraform best practices:
```
get_azure_best_practices(resource="general", action="code-generation")
```

### Get deployment best practices:
```
get_azure_best_practices(resource="general", action="deployment")
```

## Provider-Specific Best Practices

### AzureRM Provider 4.x Best Practices:
```
get_azure_best_practices(resource="azurerm", action="code-generation")
```

### AzAPI Provider 2.x Best Practices:
```
get_azure_best_practices(resource="azapi", action="code-generation")
```

## Resource-Specific Best Practices

### Security Best Practices:
```
get_azure_best_practices(resource="security", action="security")
```

### Compute Resources:
```
get_azure_best_practices(resource="compute", action="code-generation")
```

### Database Resources:
```
get_azure_best_practices(resource="database", action="code-generation")
```

### Storage Resources:
```
get_azure_best_practices(resource="storage", action="code-generation")
```

### Networking:
```
get_azure_best_practices(resource="networking", action="code-generation")
```

### Monitoring and Observability:
```
get_azure_best_practices(resource="monitoring", action="code-generation")
```

## Key Features Implemented

### 1. **Provider Version Recommendations**
- **AzureRM 4.x**: Latest features, improved error handling, better resource lifecycle management
- **AzAPI 2.x**: Direct ARM API access, simplified HCL object usage (no more `jsonencode()` needed)

### 2. **AzAPI 2.x Specific Improvements**
The tool specifically highlights that in AzAPI 2.x:
- Use HCL objects directly: `body = { properties = { enabled = true } }`
- Instead of: `body = jsonencode({ properties = { enabled = true } })`

### 3. **Comprehensive Coverage**
- Infrastructure organization and naming conventions
- State management best practices
- Security fundamentals
- Resource-specific recommendations
- Deployment strategies
- Monitoring and observability

### 4. **Structured Output**
- Clear categorization of recommendations
- Numbered lists for easy reference
- Links to additional resources
- Context-specific advice based on resource type and action

## Available Parameters

### Resource Types:
- `general` - General Azure Terraform best practices
- `azurerm` - AzureRM provider specific
- `azapi` - AzAPI provider specific
- `aztfexport` - **NEW**: Export and code cleanup workflow
- `security` - Security best practices
- `networking` - Network configuration
- `storage` - Storage account configuration
- `compute` - Virtual machines and container services
- `database` - SQL Database and Cosmos DB
- `monitoring` - Azure Monitor and observability

### Action Types:
- `code-generation` - Best practices for writing Terraform code
- `code-cleanup` - **NEW**: Transform exported code to production-ready (especially for aztfexport)
- `deployment` - Deployment and CI/CD best practices
- `configuration` - Configuration management
- `security` - Security-focused recommendations
- `performance` - Performance optimization
- `cost-optimization` - Cost management strategies

---

## 🔗 Related Documentation

- **[Terraform State Management](terraform-state-management.md)** - Detailed state operations guide
- **[Terraform Commands](terraform-commands.md)** - Complete command reference
- **[Azure Export Integration](aztfexport-integration.md)** - Export existing resources
- **[Quick Start Guide](../QUICK_START_STATE_MANAGEMENT.md)** - 5-minute code cleanup workflow

---

## 💡 Integration with Existing Tools

This tool complements the existing Terraform MCP server tools:
- Use alongside `get_azurerm_provider_documentation` for detailed resource documentation
- Combine with `get_azapi_provider_documentation` for AzAPI-specific resources
- Use before and after `export_azure_resource_group` for complete export-to-production workflow
- Reference before using `run_terraform_command` for proper configuration
- Apply recommendations when using `tflint` for code quality checks
- Integrate with `run_conftest_workspace_validation` for security compliance