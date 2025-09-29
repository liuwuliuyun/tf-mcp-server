# Azure Best Practices Tool Usage Examples

The new `get_azure_best_practices` tool provides comprehensive best practices for working with Azure resources using Terraform. Here are some usage examples:

## Basic Usage

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
- `security` - Security best practices
- `networking` - Network configuration
- `storage` - Storage account configuration
- `compute` - Virtual machines and container services
- `database` - SQL Database and Cosmos DB
- `monitoring` - Azure Monitor and observability

### Action Types:
- `code-generation` - Best practices for writing Terraform code
- `deployment` - Deployment and CI/CD best practices
- `configuration` - Configuration management
- `security` - Security-focused recommendations
- `performance` - Performance optimization
- `cost-optimization` - Cost management strategies

## Integration with Existing Tools

This tool complements the existing Terraform MCP server tools:
- Use alongside `get_azurerm_provider_documentation` for detailed resource documentation
- Combine with `get_azapi_provider_documentation` for AzAPI-specific resources
- Reference before using `run_terraform_command` for proper configuration
- Apply recommendations when using `tflint` for code quality checks