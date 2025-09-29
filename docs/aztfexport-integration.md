# Azure Export for Terraform (aztfexport) Integration

The Azure Terraform MCP Server now includes comprehensive integration with [Azure Export for Terraform (aztfexport)](https://github.com/Azure/aztfexport), Microsoft's official tool for exporting existing Azure resources to Terraform configuration and state.

## Overview

Azure Export for Terraform (aztfexport) is a powerful command-line tool that helps you migrate existing Azure infrastructure to Terraform management. The integration in this MCP server provides programmatic access to aztfexport functionality through standardized API endpoints.

### Key Features

- **Single Resource Export**: Export individual Azure resources by resource ID
- **Resource Group Export**: Export entire resource groups and their contained resources
- **Query-Based Export**: Use Azure Resource Graph queries for complex resource selection
- **Multi-Provider Support**: Works with both AzureRM and AzAPI Terraform providers
- **Configuration Management**: Get and set aztfexport configuration options
- **Installation Validation**: Check aztfexport installation and dependencies
- **Container-Friendly**: All generated files are returned in the API response, making it ideal for containerized environments

## Prerequisites

### 1. Install aztfexport

Choose one of the following installation methods:

#### Windows
```powershell
winget install aztfexport
```

#### macOS
```bash
brew install aztfexport
```

#### Linux (Ubuntu/Debian)
```bash
# Import Microsoft repository key
curl -sSL https://packages.microsoft.com/keys/microsoft.asc | sudo tee /etc/apt/trusted.gpg.d/microsoft.asc

# Add repository
echo "deb [arch=amd64,arm64,armhf signed-by=/etc/apt/trusted.gpg.d/microsoft.asc] https://packages.microsoft.com/repos/microsoft-ubuntu-$(lsb_release -cs)-prod $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/microsoft-prod.list

# Install
sudo apt update
sudo apt install aztfexport
```

#### Go (any platform)
```bash
go install github.com/Azure/aztfexport@latest
```

#### From GitHub Releases
Download precompiled binaries from: https://github.com/Azure/aztfexport/releases

### 2. Install Terraform

aztfexport requires Terraform >= v0.12:

#### Windows
```powershell
choco install terraform
# or
winget install HashiCorp.Terraform
```

#### macOS
```bash
brew install terraform
```

#### Linux
```bash
# Download and install from https://terraform.io/downloads
wget https://releases.hashicorp.com/terraform/1.5.0/terraform_1.5.0_linux_amd64.zip
unzip terraform_1.5.0_linux_amd64.zip
sudo mv terraform /usr/local/bin/
```

### 3. Azure Authentication

Configure Azure authentication for aztfexport:

#### Service Principal (Required)
```bash
export ARM_CLIENT_ID="your-client-id"
export ARM_CLIENT_SECRET="your-client-secret"
export ARM_SUBSCRIPTION_ID="your-subscription-id"
export ARM_TENANT_ID="your-tenant-id"
```

#### Managed Identity
When running on Azure resources, managed identity is automatically used.

## Available Tools

### 1. check_aztfexport_installation

Check if aztfexport and its dependencies are properly installed.

**Parameters:** None

**Returns:**
- `installed` (boolean): Whether aztfexport is available
- `aztfexport_version` (string): Version of aztfexport
- `terraform_version` (string): Version of terraform
- `status` (string): Installation status message
- `installation_help` (object): Installation commands for different platforms (if not installed)

**Example:**
```python
result = await mcp_client.call_tool("check_aztfexport_installation")
```

### 2. export_azure_resource

Export a single Azure resource to Terraform configuration.

**Parameters:**
- `resource_id` (required): Azure resource ID to export
- `output_folder_name` (optional): Output folder name (created under the workspace root, auto-generated if not specified)
- `provider` (optional): Terraform provider to use ("azurerm" or "azapi", default: "azurerm")
- `resource_name` (optional): Custom resource name in Terraform
- `resource_type` (optional): Custom resource type in Terraform
- `dry_run` (optional): Perform validation without creating files (default: false)
- `include_role_assignment` (optional): Include role assignments (default: false)
- `parallelism` (optional): Number of parallel operations (default: 10)
- `continue_on_error` (optional): Continue if some resources fail (default: false)

**Returns:**
- `success` (boolean): Whether the export succeeded
- `exit_code` (number): Command exit code
- `generated_files` (object): Generated Terraform files and their contents (all file contents are returned in the response)
- `stdout` (string): Command output
- `stderr` (string): Command error output

**Example:**
```python
result = await mcp_client.call_tool("export_azure_resource", {
    "resource_id": "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/my-rg/providers/Microsoft.Storage/storageAccounts/mystorageacct",
    "output_folder_name": "exported-storage-account",
    "provider": "azurerm",
    "dry_run": false
})
```

### 3. export_azure_resource_group

Export an entire Azure resource group and its resources.

**Parameters:**
- `resource_group_name` (required): Name of the resource group to export
- `output_folder_name` (optional): Output folder name (created under the workspace root, auto-generated if not specified)
- `provider` (optional): Terraform provider to use ("azurerm" or "azapi")
- `name_pattern` (optional): Pattern for resource naming in Terraform
- `type_pattern` (optional): Pattern for resource type filtering
- `dry_run` (optional): Perform validation without creating files
- `include_role_assignment` (optional): Include role assignments
- `parallelism` (optional): Number of parallel operations
- `continue_on_error` (optional): Continue if some resources fail

**Returns:** Same structure as `export_azure_resource`

**Example:**
```python
result = await mcp_client.call_tool("export_azure_resource_group", {
    "resource_group_name": "my-production-rg",
    "output_folder_name": "exported-production-rg",
    "provider": "azurerm",
    "parallelism": 5,
    "continue_on_error": true
})
```

### 4. export_azure_resources_by_query

Export Azure resources using Azure Resource Graph queries.

**Parameters:**
- `query` (required): Azure Resource Graph WHERE clause
- `output_folder_name` (optional): Output folder name (created under the workspace root, auto-generated if not specified)
- `provider` (optional): Terraform provider to use
- `name_pattern` (optional): Pattern for resource naming
- `type_pattern` (optional): Pattern for resource type filtering
- `dry_run` (optional): Perform validation without creating files
- `include_role_assignment` (optional): Include role assignments
- `parallelism` (optional): Number of parallel operations
- `continue_on_error` (optional): Continue if some resources fail

**Returns:** Same structure as `export_azure_resource`

**Query Examples:**
- All storage accounts: `"type =~ 'Microsoft.Storage/storageAccounts'"`
- Resources in East US: `"location == 'eastus'"`
- Production resources: `"tags['Environment'] == 'Production'"`
- Complex query: `"type =~ 'Microsoft.Compute/virtualMachines' and location == 'westus2' and tags['Team'] == 'DevOps'"`

**Example:**
```python
result = await mcp_client.call_tool("export_azure_resources_by_query", {
    "query": "type =~ 'Microsoft.Storage/storageAccounts' and location == 'eastus'",
    "output_folder_name": "exported-eastus-storage",
    "provider": "azurerm",
    "dry_run": true
})
```

### 5. get_aztfexport_config

Get aztfexport configuration settings.

**Parameters:**
- `key` (optional): Specific configuration key to retrieve

**Returns:**
- `success` (boolean): Whether the operation succeeded
- `config` (object/string): Configuration data

**Common configuration keys:**
- `installation_id`: Unique installation identifier
- `telemetry_enabled`: Whether telemetry is enabled

**Example:**
```python
# Get all configuration
result = await mcp_client.call_tool("get_aztfexport_config")

# Get specific key
result = await mcp_client.call_tool("get_aztfexport_config", {
    "key": "telemetry_enabled"
})
```

### 6. set_aztfexport_config

Set aztfexport configuration settings.

**Parameters:**
- `key` (required): Configuration key to set
- `value` (required): Configuration value to set

**Returns:**
- `success` (boolean): Whether the operation succeeded
- `exit_code` (number): Command exit code
- `stdout` (string): Command output
- `stderr` (string): Command error output

**Example:**
```python
# Disable telemetry
result = await mcp_client.call_tool("set_aztfexport_config", {
    "key": "telemetry_enabled",
    "value": "false"
})
```

## Best Practices

### 1. Start with Dry Runs

Always use `dry_run: true` first to validate your export without creating files:

```python
result = await mcp_client.call_tool("export_azure_resource", {
    "resource_id": "/subscriptions/.../my-resource",
    "dry_run": true
})
```

### 2. Use Appropriate Parallelism

- For single resources: Use default parallelism (10)
- For resource groups: Adjust based on size (3-15)
- For large queries: Start with lower values (3-5)

### 3. Handle Errors Gracefully

Enable `continue_on_error` for bulk operations:

```python
result = await mcp_client.call_tool("export_azure_resource_group", {
    "resource_group_name": "large-rg",
    "continue_on_error": true,
    "parallelism": 5
})
```

### 4. Choose the Right Provider

- Use `azurerm` for standard Azure resources
- Use `azapi` for preview features or complex configurations

### 5. Review Generated Files

Always review the generated Terraform configuration before applying:

```python
result = await mcp_client.call_tool("export_azure_resource_group", {
    "resource_group_name": "my-rg"
})

if result["success"]:
    for filename, content in result["generated_files"].items():
        print(f"=== {filename} ===")
        print(content)
```

## Common Use Cases

### 1. Migrate Single Resource

```python
# Export a storage account
result = await mcp_client.call_tool("export_azure_resource", {
    "resource_id": "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/storage-rg/providers/Microsoft.Storage/storageAccounts/mystorageacct",
    "resource_name": "primary_storage",
    "provider": "azurerm"
})
```

### 2. Migrate Complete Environment

```python
# Export entire resource group
result = await mcp_client.call_tool("export_azure_resource_group", {
    "resource_group_name": "production-environment",
    "provider": "azurerm",
    "include_role_assignment": true,
    "parallelism": 8,
    "continue_on_error": true
})
```

### 3. Export Specific Resource Types

```python
# Export all App Services across subscriptions
result = await mcp_client.call_tool("export_azure_resources_by_query", {
    "query": "type =~ 'Microsoft.Web/sites'",
    "name_pattern": "app_service_{name}",
    "provider": "azurerm"
})
```

### 4. Export Resources by Tags

```python
# Export all production resources
result = await mcp_client.call_tool("export_azure_resources_by_query", {
    "query": "tags['Environment'] == 'Production'",
    "provider": "azurerm",
    "continue_on_error": true
})
```

## Troubleshooting

### Common Issues

1. **Authentication Failed**
   - Ensure you have Azure Service Principal credentials configured
   - Verify subscription access
   - Check service principal credentials

2. **Resource Not Found**
   - Verify the resource ID is correct
   - Ensure you have read access to the resource
   - Check if the resource still exists

3. **Terraform Provider Issues**
   - Ensure the correct provider version is configured
   - Check provider authentication
   - Verify provider supports the resource type

4. **Permission Errors**
   - Ensure you have appropriate Azure RBAC permissions
   - For resource groups: Reader access minimum
   - For role assignments: User Access Administrator or Owner

### Debugging

Enable verbose output by checking the `stdout` and `stderr` fields in responses:

```python
result = await mcp_client.call_tool("export_azure_resource", {
    "resource_id": "/subscriptions/.../my-resource"
})

if not result["success"]:
    print("Error:", result["stderr"])
    print("Output:", result["stdout"])
```

## Integration Examples

See the complete example in `examples/aztfexport_example.py` for detailed usage patterns and error handling.

## Limitations

- aztfexport has some limitations with certain Azure resources
- Generated configurations may need manual adjustments
- State files should be reviewed before applying changes
- Some resources may require specific provider versions

For detailed limitations, see the [official aztfexport documentation](https://learn.microsoft.com/en-us/azure/developer/terraform/azure-export-for-terraform/export-terraform-concepts#limitations).

## Related Tools

The aztfexport integration works well with other tools in the MCP server:

- Use `run_terraform_command` to run Terraform (init/plan/apply/fmt) inside the exported workspace directory
- Use `run_tflint_workspace_analysis` to lint the generated Terraform code
- Use `run_conftest_workspace_validation` to check compliance and security policies
```