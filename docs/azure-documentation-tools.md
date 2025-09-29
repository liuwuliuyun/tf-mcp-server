# Azure Documentation Tools

This guide covers the Azure documentation tools available in the MCP server for accessing AzureRM, AzAPI, and Azure Verified Modules (AVM) documentation.

## 📚 Available Documentation Sources

| Tool | Description | Use Cases |
|------|-------------|-----------|
| **AzureRM Provider** | Comprehensive resource documentation | Resource configuration, arguments, attributes |
| **AzAPI Provider** | Azure API schemas and references | Direct Azure API access, latest features |
| **Azure Verified Modules** | Verified module definitions | Module discovery, variables, outputs |

## 🔍 AzureRM Provider Documentation

### `get_azurerm_provider_documentation`

The primary tool for accessing AzureRM provider documentation.

**Parameters:**
- `resource_type_name` (required): Resource name without "azurerm_" prefix
- `doc_type` (required): "resource" or "data-source" 
- `argument_name` (optional): Specific argument/attribute lookup

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
- `resource_type_name` (required): Full Azure API resource type with version

### Examples

#### Storage Account Schema
```json
{
  "tool": "get_azapi_provider_documentation",
  "arguments": {
    "resource_type_name": "Microsoft.Storage/storageAccounts@2023-01-01"
  }
}
```

#### Virtual Machine Schema
```json
{
  "tool": "get_azapi_provider_documentation", 
  "arguments": {
    "resource_type_name": "Microsoft.Compute/virtualMachines@2023-03-01"
  }
}
```

#### Key Vault Schema
```json
{
  "tool": "get_azapi_provider_documentation",
  "arguments": {
    "resource_type_name": "Microsoft.KeyVault/vaults@2023-07-01"
  }
}
```

### Common Azure API Types

#### Microsoft.Storage
- `Microsoft.Storage/storageAccounts@2023-01-01`
- `Microsoft.Storage/storageAccounts/blobServices@2023-01-01`
- `Microsoft.Storage/storageAccounts/fileServices@2023-01-01`

#### Microsoft.Compute  
- `Microsoft.Compute/virtualMachines@2023-03-01`
- `Microsoft.Compute/virtualMachineScaleSets@2023-03-01`
- `Microsoft.Compute/disks@2023-01-02`

#### Microsoft.Network
- `Microsoft.Network/virtualNetworks@2023-05-01`
- `Microsoft.Network/networkSecurityGroups@2023-05-01` 
- `Microsoft.Network/publicIPAddresses@2023-05-01`

---

## 🏗️ Azure Verified Modules (AVM)

### Module Discovery

#### `get_avm_modules`
List all available Azure Verified Modules.

```json
{
  "tool": "get_avm_modules",
  "arguments": {}
}
```

**Returns:**
```json
[
  {
    "module_name": "avm-res-compute-virtualmachine",
    "description": "Creates a virtual machine with optional extensions",
    "source": "Azure/avm-res-compute-virtualmachine/azurerm"
  }
]
```

### Version Management

#### `get_avm_latest_version`
Get the latest version of a specific module.

```json
{
  "tool": "get_avm_latest_version",
  "arguments": {
    "module_name": "avm-res-compute-virtualmachine" 
  }
}
```

#### `get_avm_versions`  
Get all available versions of a module.

```json
{
  "tool": "get_avm_versions",
  "arguments": {
    "module_name": "avm-res-storage-storageaccount"
  }
}
```

### Module Schema

#### `get_avm_variables`
Get input variables schema for a module version.

```json
{
  "tool": "get_avm_variables",
  "arguments": {
    "module_name": "avm-res-compute-virtualmachine",
    "module_version": "0.19.3"
  }
}
```

#### `get_avm_outputs`
Get output definitions for a module version.

```json
{
  "tool": "get_avm_outputs", 
  "arguments": {
    "module_name": "avm-res-compute-virtualmachine",
    "module_version": "0.19.3"
  }
}
```

---

## 🎯 Common Workflows

### 1. Exploring a New Resource Type

```json
# Step 1: Get general resource documentation
{
  "tool": "get_azurerm_provider_documentation",
  "arguments": {
    "resource_type_name": "container_group",
    "doc_type": "resource"
  }
}

# Step 2: Get specific argument details  
{
  "tool": "get_azurerm_provider_documentation",
  "arguments": {
    "resource_type_name": "container_group", 
    "doc_type": "resource",
    "argument_name": "container"
  }
}

# Step 3: Check AzAPI for latest features
{
  "tool": "get_azapi_provider_documentation",
  "arguments": {
    "resource_type_name": "Microsoft.ContainerInstance/containerGroups@2023-05-01"
  }
}
```

### 2. Finding and Using AVM Modules

```json  
# Step 1: Discover available modules
{
  "tool": "get_avm_modules",
  "arguments": {}
}

# Step 2: Get latest version
{
  "tool": "get_avm_latest_version", 
  "arguments": {
    "module_name": "avm-res-compute-virtualmachine"
  }
}

# Step 3: Understand module inputs
{
  "tool": "get_avm_variables",
  "arguments": {
    "module_name": "avm-res-compute-virtualmachine",
    "module_version": "0.19.3"
  }
}

# Step 4: Understand module outputs
{
  "tool": "get_avm_outputs",
  "arguments": {
    "module_name": "avm-res-compute-virtualmachine", 
    "module_version": "0.19.3"
  }
}
```

### 3. Comparing Providers

```json
# AzureRM approach
{
  "tool": "get_azurerm_provider_documentation",
  "arguments": {
    "resource_type_name": "storage_account",
    "doc_type": "resource"
  }
}

# AzAPI approach (for latest features)
{
  "tool": "get_azapi_provider_documentation", 
  "arguments": {
    "resource_type_name": "Microsoft.Storage/storageAccounts@2023-01-01"
  }
}
```

---

## 💡 Tips and Best Practices

### Resource Name Conventions
- **AzureRM**: Use resource name without "azurerm_" prefix (e.g., "storage_account")
- **AzAPI**: Use full Azure API resource type with version (e.g., "Microsoft.Storage/storageAccounts@2023-01-01")

### When to Use Each Tool
- **AzureRM**: Standard Terraform configurations, well-established patterns
- **AzAPI**: Latest Azure features, preview APIs, complex configurations  
- **AVM**: Standardized, tested modules for common patterns

### Documentation Quality
- AzureRM docs include Terraform-specific examples and patterns
- AzAPI docs reflect the raw Azure API schema
- AVM docs focus on module interfaces and best practices

### Performance Tips
- Cache frequently used documentation locally
- Use specific argument lookups when possible
- Combine with best practices tools for comprehensive guidance

---

## ⚠️ Limitations

### AzureRM Provider
- Documentation reflects provider version in use
- Some preview features may not be available
- Deprecated resources may still appear

### AzAPI Provider  
- Requires knowledge of Azure API versions
- Schema complexity can be high for some resources
- Less Terraform-specific guidance

### Azure Verified Modules
- Module availability depends on community contributions
- Version compatibility with provider versions
- May not cover all Azure services

---

## 🔗 Related Tools

- **[Best Practices](azure-best-practices-tool.md)**: Get Azure-specific best practices
- **[Source Code Analysis](terraform-golang-source-tools.md)**: Understand provider implementation
- **[Azure Export](aztfexport-integration.md)**: Export existing resources to Terraform