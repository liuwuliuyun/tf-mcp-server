# Azure Documentation Tools

This guide covers the Azure documentation tools available in the MCP server for accessing AzureRM and AzAPI provider documentation.

## 📚 Available Documentation Sources

| Tool | Description | Use Cases |
|------|-------------|-----------|
| **AzureRM Provider** | Comprehensive resource documentation | Resource configuration, arguments, attributes |
| **AzAPI Provider** | Azure API schemas and references | Direct Azure API access, latest features |

## 🔍 AzureRM Provider Documentation

### `get_azurerm_provider_documentation`

The primary tool for accessing AzureRM provider documentation.

**Parameters:**
- `resource_type_name` (required): Resource name without "azurerm_" prefix
- `doc_type` (optional): "resource" (default) or "data-source" 
- `argument_name` (optional): Specific argument to retrieve details for
- `attribute_name` (optional): Specific attribute to retrieve details for

### Examples

#### Get Resource Documentation
```json
{
  "tool": "get_azurerm_provider_documentation",
  "arguments": {
    "resource_type_name": "storage_account",
    "doc_type": "resource"
  }
}
```

#### Get Specific Argument Details
```json
{
  "tool": "get_azurerm_provider_documentation", 
  "arguments": {
    "resource_type_name": "virtual_machine",
    "doc_type": "resource",
    "argument_name": "os_disk"
  }
}
```

#### Get Data Source Documentation
```json
{
  "tool": "get_azurerm_provider_documentation",
  "arguments": {
    "resource_type_name": "key_vault",
    "doc_type": "data-source"
  }
}
```

### Common Resource Types

#### Compute Resources
- `virtual_machine` - Virtual machines and configurations
- `virtual_machine_scale_set` - VM scale sets
- `availability_set` - Availability sets
- `disk_encryption_set` - Disk encryption
- `image` - Custom VM images

#### Storage Resources  
- `storage_account` - Storage accounts and configuration
- `storage_blob` - Blob storage containers and blobs
- `storage_queue` - Storage queues
- `storage_table` - Storage tables
- `storage_share` - File shares

#### Network Resources
- `virtual_network` - Virtual networks and subnets
- `network_security_group` - Network security groups
- `public_ip` - Public IP addresses
- `load_balancer` - Load balancers
- `application_gateway` - Application gateways

#### Database Resources
- `sql_server` - SQL Server instances
- `sql_database` - SQL databases
- `cosmosdb_account` - Cosmos DB accounts
- `mysql_server` - MySQL servers
- `postgresql_server` - PostgreSQL servers

#### Identity & Security
- `key_vault` - Key vaults
- `key_vault_secret` - Key vault secrets
- `role_assignment` - RBAC role assignments
- `user_assigned_identity` - Managed identities

---

## 🔧 AzAPI Provider Documentation

### `get_azapi_provider_documentation`

Access Azure API schemas directly for the latest Azure features.

**Parameters:**
- `resource_type_name` (required): Full Azure API resource type (e.g., "Microsoft.Storage/storageAccounts")

### Examples

#### Storage Account Schema
```json
{
  "tool": "get_azapi_provider_documentation",
  "arguments": {
    "resource_type_name": "Microsoft.Storage/storageAccounts"
  }
}
```

#### Virtual Machine Schema
```json
{
  "tool": "get_azapi_provider_documentation", 
  "arguments": {
    "resource_type_name": "Microsoft.Compute/virtualMachines"
  }
}
```

#### Key Vault Schema
```json
{
  "tool": "get_azapi_provider_documentation",
  "arguments": {
    "resource_type_name": "Microsoft.KeyVault/vaults"
  }
}
```

### Common Azure API Types

#### Microsoft.Storage
- `Microsoft.Storage/storageAccounts`
- `Microsoft.Storage/storageAccounts/blobServices`
- `Microsoft.Storage/storageAccounts/fileServices`

#### Microsoft.Compute  
- `Microsoft.Compute/virtualMachines`
- `Microsoft.Compute/virtualMachineScaleSets`
- `Microsoft.Compute/disks`

#### Microsoft.Network
- `Microsoft.Network/virtualNetworks`
- `Microsoft.Network/networkSecurityGroups` 
- `Microsoft.Network/publicIPAddresses`

---

## 🎯 Common Workflows

### 1. Exploring a New Resource Type

```json
// Step 1: Get general resource documentation
{
  "tool": "get_azurerm_provider_documentation",
  "arguments": {
    "resource_type_name": "container_group",
    "doc_type": "resource"
  }
}

// Step 2: Get specific argument details  
{
  "tool": "get_azurerm_provider_documentation",
  "arguments": {
    "resource_type_name": "container_group", 
    "doc_type": "resource",
    "argument_name": "container"
  }
}

// Step 3: Check AzAPI for latest features
{
  "tool": "get_azapi_provider_documentation",
  "arguments": {
    "resource_type_name": "Microsoft.ContainerInstance/containerGroups"
  }
}
```

### 2. Comparing AzureRM and AzAPI Providers

```json
// AzureRM approach
{
  "tool": "get_azurerm_provider_documentation",
  "arguments": {
    "resource_type_name": "storage_account",
    "doc_type": "resource"
  }
}

// AzAPI approach (for latest features)
{
  "tool": "get_azapi_provider_documentation", 
  "arguments": {
    "resource_type_name": "Microsoft.Storage/storageAccounts"
  }
}
```

---

## 💡 Tips and Best Practices

### Resource Name Conventions
- **AzureRM**: Use resource name without "azurerm_" prefix (e.g., "storage_account")
- **AzAPI**: Use full Azure API resource type (e.g., "Microsoft.Storage/storageAccounts")

### When to Use Each Tool
- **AzureRM**: Standard Terraform configurations, well-established patterns
- **AzAPI**: Latest Azure features, preview APIs, complex configurations

### Documentation Quality
- AzureRM docs include Terraform-specific examples and patterns
- AzAPI docs reflect the raw Azure API schema

### Performance Tips
- Cache frequently used documentation locally
- Use specific argument lookups when possible

---

## ⚠️ Limitations

### AzureRM Provider
- Documentation reflects provider version in use
- Some preview features may not be available
- Deprecated resources may still appear

### AzAPI Provider  
- Requires knowledge of Azure API types
- Schema complexity can be high for some resources
- Less Terraform-specific guidance

---

## 🔗 Related Tools

- **[Azure Export](aztfexport-integration.md)**: Export existing resources to Terraform
- **[Terraform Coverage Audit](terraform-coverage-audit.md)**: Audit Terraform coverage of Azure resources