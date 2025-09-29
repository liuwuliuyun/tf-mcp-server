# Terraform & Golang Source Code Analysis Tools

This document describes the integrated Terraform Source Code Analysis Tools and Golang Source Code Analysis Tools that have been added to the Azure Terraform MCP Server.

## Overview

The integration adds powerful tools for analyzing Terraform providers and their underlying Go source code implementations. These tools are based on the terraform-mcp-eva project and provide comprehensive access to:

- **Terraform Implementation Source Code**: Read the actual source code of how Terraform resources are implemented
- **Golang Source Code Analysis**: Analyze the underlying Go code implementation of Terraform providers

## Available Tools

### Terraform Source Code Analysis Tools

#### `get_terraform_source_providers`
Get all supported Terraform provider names available for source code query.

**Parameters:** None

**Returns:** Dictionary with supported providers list

**Use Cases:**
- Discover what Terraform providers have been indexed
- Find available providers before querying specific functions or methods
- Understand the scope of providers available for source code analysis

#### `query_terraform_source_code`
Read Terraform provider source code for a given Terraform block.

**Parameters:**
- `block_type` (required): Terraform block type - one of: `resource`, `data`, `ephemeral`
- `terraform_type` (required): Terraform type (e.g., `azurerm_resource_group`)
- `entrypoint_name` (required): Function/method name:
  - For `resource`: `create`, `read`, `update`, `delete`, `schema`, `attribute`
  - For `data`: `read`, `schema`, `attribute`
  - For `ephemeral`: `open`, `close`, `renew`, `schema`
- `tag` (optional): Version tag (defaults to latest)

**Returns:** Source code as string

**Use Cases:**
- Understand how Terraform providers implement specific resources
- See how providers call underlying APIs
- Debug issues related to specific Terraform resources
- Learn provider implementation patterns

**Example:**
```json
{
  "block_type": "resource",
  "terraform_type": "azurerm_resource_group",
  "entrypoint_name": "create"
}
```

### Golang Source Code Analysis Tools

#### `get_golang_namespaces`
Get all indexed golang namespaces available for source code analysis.

**Parameters:** None

**Returns:** Dictionary with supported namespaces

**Use Cases:**
- Discover what golang projects/packages have been indexed
- Find available namespaces before querying specific code symbols
- Understand the scope of indexed golang codebases

#### `get_golang_namespace_tags`
Get all supported tags/versions for a specific golang namespace.

**Parameters:**
- `namespace` (required): Golang namespace to get tags for

**Returns:** Dictionary with supported tags for the namespace

**Use Cases:**
- Discover available versions/tags for a specific golang namespace
- Find the latest or specific versions before analyzing code
- Understand version history for indexed golang projects

**Example:**
```json
{
  "namespace": "github.com/hashicorp/terraform-provider-azurerm/internal"
}
```

#### `query_golang_source_code`
Read golang source code for given type, variable, constant, function or method definition.

**Parameters:**
- `namespace` (required): Golang namespace to query
- `symbol` (required): Symbol type - one of: `func`, `method`, `type`, `var`
- `name` (required): Name of the symbol to read
- `receiver` (optional): Method receiver type (required for methods)
- `tag` (optional): Version tag (defaults to latest)

**Returns:** Source code as string

**Use Cases:**
- See function, method, type, or variable definitions while reading golang source code
- Understand how Terraform providers expand or flatten structs
- Map schema to API calls
- Debug issues related to specific Terraform resources

**Example:**
```json
{
  "namespace": "github.com/hashicorp/terraform-provider-azurerm/internal/services/resource",
  "symbol": "type",
  "name": "ResourceGroupResource"
}
```

## Workflow Examples

### Analyzing a Terraform Resource Implementation

1. **Discover available providers:**
   ```json
   Use: get_terraform_source_providers
   ```

2. **Find the resource implementation:**
   ```json
   Use: query_terraform_source_code
   Parameters: {
     "block_type": "resource",
     "terraform_type": "azurerm_resource_group", 
     "entrypoint_name": "create"
   }
   ```

3. **Explore related Go functions:**
   ```json
   Use: query_golang_source_code
   Parameters: {
     "namespace": "github.com/hashicorp/terraform-provider-azurerm/internal/services/resource",
     "symbol": "func",
     "name": "resourceGroupCreateFunc"
   }
   ```

## Technical Implementation

### Golang Source Provider
The `GolangSourceProvider` class provides mock implementations for golang source code analysis. In a production environment, this would be connected to:

- A golang source code indexing service
- Git repositories with provider source code
- Version-specific code analysis tools

### Requirements
- Internet connection for provider downloads (for source code queries)
- Proper provider credentials (for some providers)

## Error Handling

All tools include comprehensive error handling and will return meaningful error messages when:
- Required parameters are missing
- Invalid parameter values are provided
- Providers are not available
- Network issues occur

## Performance Considerations

- Network connectivity affects provider download times
- Results should be cached when possible
- Large source files may take time to process

## Future Enhancements

Potential improvements include:
- Integration with real golang source code indexing services
- Caching of source code results
- Support for private provider registries
- Enhanced error reporting and diagnostics
- Performance optimizations for large source files