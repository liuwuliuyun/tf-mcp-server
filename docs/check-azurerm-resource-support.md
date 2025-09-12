# Check AzureRM Resource Support Tool

The `check_azurerm_resource_support` tool allows you to verify if a specific Azure resource type and property path is supported by the Terraform AzureRM provider.

## Overview

This tool is useful when working with Azure resources and needing to understand:
- Whether a specific Azure resource type is supported in Terraform AzureRM provider
- Which properties of an Azure resource are available in Terraform
- How Azure API properties map to Terraform AzureRM resource properties
- What Terraform resources support specific Azure resource configurations

## Usage

### Basic Usage

```json
{
  "tool": "check_azurerm_resource_support",
  "arguments": {
    "resource_type": "Microsoft.Compute/virtualMachines",
    "property_path": "properties.storageProfile.osDisk.caching"
  }
}
```

### Parameters

- **resource_type** (required): The Azure resource type in standard format (e.g., `Microsoft.Compute/virtualMachines`)
- **property_path** (required): The property path to check (e.g., `properties.storageProfile.osDisk.caching`)

## Examples

### Virtual Machine Storage Configuration

```json
{
  "tool": "check_azurerm_resource_support",
  "arguments": {
    "resource_type": "Microsoft.Compute/virtualMachines",
    "property_path": "properties.storageProfile.osDisk.caching"
  }
}
```

**Response:**
```json
{
  "resource_type": "Microsoft.Compute/virtualMachines",
  "property_path": "properties.storageProfile.osDisk.caching",
  "is_supported": true,
  "provider": "azurerm",
  "status": "success",
  "azurerm_mappings": [
    {
      "azurerm_resource": "azurerm_virtual_machine",
      "azurerm_property": "storage_os_disk/caching",
      "api_property": "properties.storageProfile.osDisk.caching"
    }
  ],
  "message": "Property path found in API definition with 1 azurerm mapping(s)"
}
```

### Virtual Network Subnet Configuration

```json
{
  "tool": "check_azurerm_resource_support",
  "arguments": {
    "resource_type": "Microsoft.Network/virtualNetworks/subnets",
    "property_path": "properties.addressPrefix"
  }
}
```

**Response:**
```json
{
  "resource_type": "Microsoft.Network/virtualNetworks/subnets",
  "property_path": "properties.addressPrefix",
  "is_supported": true,
  "provider": "azurerm",
  "status": "success",
  "azurerm_mappings": [
    {
      "azurerm_resource": "azurerm_subnet",
      "azurerm_property": "address_prefix",
      "api_property": "properties.addressPrefix"
    }
  ],
  "message": "Property path found in API definition with 1 azurerm mapping(s)"
}
```

### Unsupported Resource Type

```json
{
  "tool": "check_azurerm_resource_support",
  "arguments": {
    "resource_type": "Microsoft.NonExistent/resources",
    "property_path": "properties.someProperty"
  }
}
```

**Response:**
```json
{
  "resource_type": "Microsoft.NonExistent/resources",
  "property_path": "properties.someProperty",
  "is_supported": false,
  "provider": "azurerm",
  "status": "resource_not_found",
  "message": "No Terraform AzureRM provider support found for resource type Microsoft.NonExistent/resources"
}
```

### Unsupported Property Path

```json
{
  "tool": "check_azurerm_resource_support",
  "arguments": {
    "resource_type": "Microsoft.Compute/virtualMachines",
    "property_path": "properties.nonExistentProperty"
  }
}
```

**Response:**
```json
{
  "resource_type": "Microsoft.Compute/virtualMachines",
  "property_path": "properties.nonExistentProperty", 
  "is_supported": false,
  "provider": "azurerm",
  "status": "success",
  "api_entries_found": 4,
  "message": "Property path 'properties.nonExistentProperty' not found in Microsoft.Compute/virtualMachines API definition"
}
```

## Response Format

### Successful Response (Supported)

```json
{
  "resource_type": "string",           // The queried resource type
  "property_path": "string",           // The queried property path
  "is_supported": true,                // Whether the property is supported
  "provider": "azurerm",               // The provider name
  "status": "success",                 // Status of the operation
  "azurerm_mappings": [                // Array of Terraform mappings
    {
      "azurerm_resource": "string",    // Terraform resource name
      "azurerm_property": "string",    // Terraform property path
      "api_property": "string"         // Original API property path
    }
  ],
  "message": "string",                 // Human-readable message
  "api_entries_found": "number"       // Number of API entries found
}
```

### Unsuccessful Response (Not Supported)

```json
{
  "resource_type": "string",           // The queried resource type
  "property_path": "string",           // The queried property path
  "is_supported": false,               // Whether the property is supported
  "provider": "azurerm",               // The provider name
  "status": "string",                  // Status: "resource_not_found", "success", "error"
  "message": "string",                 // Human-readable error message
  "api_entries_found": "number"       // Number of API entries found (if applicable)
}
```

## Implementation Details

### Data Source

The tool uses the `tf.json` file located at `src/tf_mcp_server/core/tf.json` which contains Azure REST API to Terraform AzureRM provider coverage mapping data.

**Important:** The current tf.json file contains only a minimal subset for demonstration and testing. For production use, replace it with the comprehensive data from: https://github.com/magodo/azure-rest-api-cov-terraform-reports/blob/main/tf.json

### Matching Logic

1. **Case-Insensitive Matching**: Resource types and property paths are matched case-insensitively
2. **Exact Path Matching**: Property paths must match exactly (no partial matching)
3. **Multiple Mappings**: Some properties may map to multiple Terraform resources
4. **Dot Notation**: Property paths use dot notation (e.g., `properties.storageProfile.osDisk.caching`)

### Property Path Format

Property paths should follow Azure REST API property structure:
- Start with `properties.` for most Azure resources
- Use dot notation to separate nested properties
- Example: `properties.storageProfile.osDisk.caching`
- Example: `properties.networkSecurityGroup.id`

## Common Use Cases

1. **API Migration**: When migrating from direct Azure API calls to Terraform
2. **Resource Planning**: Understanding what Azure features are available in Terraform
3. **Configuration Mapping**: Finding the correct Terraform property for an Azure setting
4. **Coverage Assessment**: Evaluating Terraform support for specific Azure resource configurations

## Troubleshooting

### Property Not Found
If a property is not found, ensure:
- The property path is complete and correctly formatted
- The property exists in the Azure REST API specification
- The property is included in the tf.json coverage data

### Resource Not Found
If a resource type is not found:
- Verify the resource type format (e.g., `Microsoft.Compute/virtualMachines`)
- Check if the resource is covered in the tf.json data
- Consider updating to the full tf.json from the coverage reports repository

### Case Sensitivity
The tool performs case-insensitive matching, so these are equivalent:
- `Microsoft.Compute/virtualMachines`
- `microsoft.compute/virtualmachines`
- `MICROSOFT.COMPUTE/VIRTUALMACHINES`

## Related Tools

- **`azurerm_terraform_documentation_retriever`**: Get detailed documentation for supported resources
- **`run_terraform_command`**: Execute Terraform commands with the discovered mappings
- **`analyze_azure_resources`**: Analyze existing Terraform configurations

## Contributing

To add more Azure resource coverage:
1. Update the tf.json file with additional resource mappings
2. Add corresponding test cases in `tests/test_check_azurerm_support.py`
3. Run the test suite to verify functionality

For the most comprehensive coverage, use the tf.json from the azure-rest-api-cov-terraform-reports repository.
