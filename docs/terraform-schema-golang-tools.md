# Terraform Schema & Provider Analysis Tools

This document describes the integrated Terraform Schema & Provider Analysis Tools and Golang Source Code Analysis Tools that have been added to the Azure Terraform MCP Server.

## Overview

The integration adds powerful tools for analyzing Terraform providers, schemas, and their underlying Go source code implementations. These tools are based on the terraform-mcp-eva project and provide comprehensive access to:

- **Terraform Provider Schema Information**: Query detailed schema information for resources, data sources, functions, and providers
- **Provider Item Discovery**: List all available resources, data sources, ephemeral resources, and functions for any provider
- **Golang Source Code Analysis**: Analyze the underlying Go code implementation of Terraform providers
- **Terraform Implementation Source Code**: Read the actual source code of how Terraform resources are implemented

## Available Tools

### Terraform Schema & Provider Analysis Tools

#### `query_terraform_schema`
Query fine-grained Terraform schema information for any provider available in the Terraform Registry.

**Parameters:**
- `category` (required): Terraform block type - one of: `resource`, `data`, `ephemeral`, `function`, `provider`
- `type` (optional): Terraform block type like `azurerm_resource_group` or function name. Not required for provider category.
- `path` (optional): JSON path to query specific schema parts (e.g., `default_node_pool.upgrade_settings`)
- `namespace` (optional): Provider namespace (e.g., `hashicorp`, `Azure`). Defaults to `hashicorp`.
- `name` (optional): Provider name (e.g., `azurerm`, `aws`). Will be inferred from type if not provided.
- `version` (optional): Provider version constraint (e.g., `5.0.0`, `~> 4.0`). Uses latest if not specified.

**Returns:** JSON string representing the schema with attribute descriptions

**Use Cases:**
- Get schema information about specific attributes or nested blocks
- Understand resource structure and attribute descriptions  
- Validate Terraform configuration requirements
- Query provider configuration schemas

**Example:**
```json
{
  "category": "resource",
  "type": "azurerm_resource_group",
  "path": "tags"
}
```

#### `list_terraform_provider_items`
List all available items (resources, data sources, ephemeral resources, or functions) for a specific Terraform provider.

**Parameters:**
- `category` (required): Item type - one of: `resource`, `data`, `ephemeral`, `function`
- `namespace` (optional): Provider namespace. Defaults to `hashicorp`.
- `name` (required): Provider name (e.g., `azurerm`, `aws`)
- `version` (optional): Provider version constraint

**Returns:** Dictionary with items list and metadata

**Use Cases:**
- Discover what resources/data sources/functions are available in a provider
- Find all resources that match a specific pattern
- Understand the full scope of a provider's capabilities
- Validate if a specific resource type exists

**Example:**
```json
{
  "category": "resource",
  "name": "azurerm"
}
```

#### `terraform_source_code_query_get_supported_providers`
Get all supported Terraform provider names available for source code query.

**Parameters:** None

**Returns:** Dictionary with supported providers list

**Use Cases:**
- Discover what Terraform providers have been indexed
- Find available providers before querying specific functions or methods
- Understand the scope of providers available for source code analysis

#### `query_terraform_block_implementation_source_code`
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

#### `golang_source_code_server_get_supported_golang_namespaces`
Get all indexed golang namespaces available for source code analysis.

**Parameters:** None

**Returns:** Dictionary with supported namespaces

**Use Cases:**
- Discover what golang projects/packages have been indexed
- Find available namespaces before querying specific code symbols
- Understand the scope of indexed golang codebases

#### `golang_source_code_server_get_supported_tags`
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
   Use: terraform_source_code_query_get_supported_providers
   ```

2. **Find the resource implementation:**
   ```json
   Use: query_terraform_block_implementation_source_code
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

### Getting Terraform Schema Information

1. **Query resource schema:**
   ```json
   Use: query_terraform_schema
   Parameters: {
     "category": "resource",
     "type": "azurerm_kubernetes_cluster"
   }
   ```

2. **Query specific nested block:**
   ```json
   Use: query_terraform_schema
   Parameters: {
     "category": "resource",
     "type": "azurerm_kubernetes_cluster",
     "path": "default_node_pool.upgrade_settings"
   }
   ```

3. **List all resources for a provider:**
   ```json
   Use: list_terraform_provider_items
   Parameters: {
     "category": "resource",
     "name": "azurerm"
   }
   ```

## Technical Implementation

### Terraform Schema Provider
The `TerraformSchemaProvider` class uses the `terraform providers schema -json` command to dynamically load and query provider schemas. It:

- Creates temporary Terraform configurations
- Initializes providers to download schemas
- Extracts specific schema information using JSON path queries
- Supports all providers available in the Terraform Registry

### Golang Source Provider
The `GolangSourceProvider` class provides mock implementations for golang source code analysis. In a production environment, this would be connected to:

- A golang source code indexing service
- Git repositories with provider source code
- Version-specific code analysis tools

### Requirements
- Terraform CLI installed and available in PATH
- Internet connection for provider downloads (for schema queries)
- Proper provider credentials (for some providers)

## Error Handling

All tools include comprehensive error handling and will return meaningful error messages when:
- Required parameters are missing
- Invalid parameter values are provided
- Terraform commands fail
- Providers are not available
- Network issues occur

## Performance Considerations

- Schema queries require Terraform initialization and may be slow for first-time provider downloads
- Results should be cached when possible
- Large schemas may take time to process
- Network connectivity affects provider download times

## Future Enhancements

Potential improvements include:
- Integration with real golang source code indexing services
- Caching of schema results
- Support for private provider registries
- Enhanced error reporting and diagnostics
- Performance optimizations for large schemas