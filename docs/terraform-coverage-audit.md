# Terraform Coverage Audit

The Terraform Coverage Audit tool helps you understand how much of your Azure environment is under Terraform management. It compares your Azure resources against your Terraform state to identify gaps, orphaned resources, and provide actionable recommendations.

## Overview

When managing Azure infrastructure with Terraform, it's common to have:
- **Azure resources not yet in Terraform** - Manual resources or resources created outside of Terraform
- **Orphaned Terraform resources** - Resources in state that no longer exist in Azure
- **Managed resources** - Resources properly tracked in both Azure and Terraform

The coverage audit tool helps you:
- 📊 **Measure coverage**: Get precise percentage of Azure resources managed by Terraform
- 🔍 **Identify gaps**: Find Azure resources that should be imported into Terraform
- 🧹 **Detect drift**: Discover orphaned resources in your Terraform state
- 💡 **Get recommendations**: Receive actionable steps to improve infrastructure management

## Prerequisites

Before using the coverage audit tool, ensure:

1. **Terraform Workspace is Initialized**
   ```bash
   terraform init
   ```

2. **State File Exists**
   - The workspace must have a valid Terraform state file
   - State can be local or remote (Azure Storage, Terraform Cloud, etc.)

3. **Azure CLI is Authenticated**
   ```bash
   az login
   ```

4. **Azure Resource Graph Access**
   - Your Azure account needs permissions to query Azure Resource Graph
   - Reader role at the subscription or resource group level

## Tool: `audit_terraform_coverage`

### Basic Usage

```python
# Audit a specific resource group
audit_terraform_coverage(
    workspace_folder="workspace/my-terraform",
    scope="resource-group",
    scope_value="my-resource-group"
)
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `workspace_folder` | string | Yes | Terraform workspace folder to audit (relative to workspace root) |
| `scope` | string | Yes | Audit scope: `resource-group`, `subscription`, or `query` |
| `scope_value` | string | Yes | Scope-specific value (RG name, subscription ID, or ARG query) |
| `include_non_terraform_resources` | bool | No (default: true) | Include resources not in Terraform |
| `include_orphaned_terraform_resources` | bool | No (default: true) | Include Terraform resources not in Azure |

### Scope Options

#### Resource Group Scope
Audit all resources within a specific resource group.

```python
audit_terraform_coverage(
    workspace_folder="workspace/prod-infra",
    scope="resource-group",
    scope_value="prod-rg-eastus"
)
```

#### Subscription Scope
Audit all resources across an entire Azure subscription.

```python
audit_terraform_coverage(
    workspace_folder="workspace/subscription-infra",
    scope="subscription",
    scope_value="12345678-1234-1234-1234-123456789012"
)
```

#### Custom Query Scope
Use Azure Resource Graph queries for fine-grained resource selection.

```python
# Audit all storage accounts
audit_terraform_coverage(
    workspace_folder="workspace/storage-infra",
    scope="query",
    scope_value="type =~ 'Microsoft.Storage/storageAccounts'"
)

# Audit resources by location
audit_terraform_coverage(
    workspace_folder="workspace/regional-infra",
    scope="query",
    scope_value="location == 'eastus' and resourceGroup =~ 'prod'"
)

# Audit resources by tag
audit_terraform_coverage(
    workspace_folder="workspace/app-infra",
    scope="query",
    scope_value="tags['Environment'] == 'Production'"
)
```

## Report Structure

The audit returns a comprehensive report with the following structure:

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
      "export_command": "Use export_azure_resource with resource_id='/subscriptions/...'"
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

### Report Sections

#### Summary
- **total_azure_resources**: Total resources found in Azure (within scope)
- **total_terraform_resources**: Total resources in Terraform state
- **terraform_managed**: Resources matched between Azure and Terraform
- **coverage_percentage**: Percentage of Azure resources under Terraform management
- **missing_from_terraform**: Azure resources not in Terraform state
- **orphaned_in_terraform**: Terraform resources not found in Azure

#### Managed Resources
Resources that are properly tracked in both Azure and Terraform. Each entry includes:
- Azure resource ID, type, and name
- Terraform resource address
- Match confidence level

#### Missing Resources
Azure resources not yet under Terraform management. Each entry includes:
- Full Azure resource ID
- Resource type and name
- Suggested Terraform resource types for import
- Export command for easy import

#### Orphaned Resources
Terraform resources not found in Azure. These may indicate:
- Resources deleted manually in Azure portal
- Resources renamed or moved
- State drift or corruption

## Workflow Examples

### Example 1: Initial Infrastructure Assessment

Assess coverage of an existing resource group before migration:

```python
# Step 1: Audit current coverage
result = audit_terraform_coverage(
    workspace_folder="workspace/migration-project",
    scope="resource-group",
    scope_value="legacy-rg"
)

# Step 2: Review the report
print(f"Coverage: {result['summary']['coverage_percentage']}%")
print(f"Resources to import: {result['summary']['missing_from_terraform']}")

# Step 3: Export missing resources
for resource in result['missing_resources']:
    print(f"Export: {resource['resource_id']}")
    # Use export_azure_resource tool for each
```

### Example 2: Continuous Compliance Monitoring

Regularly audit to ensure no resources are created outside Terraform:

```python
# Run audit on production resources
result = audit_terraform_coverage(
    workspace_folder="workspace/prod",
    scope="resource-group",
    scope_value="prod-rg"
)

# Alert if coverage drops below threshold
if result['summary']['coverage_percentage'] < 95:
    print("⚠️  Coverage below 95%!")
    print(f"Unmanaged resources: {len(result['missing_resources'])}")
    for resource in result['missing_resources']:
        print(f"  - {resource['resource_name']} ({resource['resource_type']})")
```

### Example 3: Identifying Orphaned Resources

Find and clean up orphaned Terraform resources:

```python
# Audit with focus on orphaned resources
result = audit_terraform_coverage(
    workspace_folder="workspace/cleanup",
    scope="subscription",
    scope_value="12345678-1234-1234-1234-123456789012",
    include_non_terraform_resources=False,  # Only show orphaned
    include_orphaned_terraform_resources=True
)

# Review orphaned resources
if result['summary']['orphaned_in_terraform'] > 0:
    print("Found orphaned resources in Terraform state:")
    for orphaned in result['orphaned_resources']:
        print(f"  - {orphaned['terraform_address']}")
        # Consider: terraform state rm {address}
```

### Example 4: Selective Resource Audit

Audit specific resource types using custom queries:

```python
# Audit only storage accounts
result = audit_terraform_coverage(
    workspace_folder="workspace/storage",
    scope="query",
    scope_value="type =~ 'Microsoft.Storage/storageAccounts' and resourceGroup =~ 'prod'"
)

# Audit only compute resources
result = audit_terraform_coverage(
    workspace_folder="workspace/compute",
    scope="query",
    scope_value="type =~ 'Microsoft.Compute/virtualMachines' or type =~ 'Microsoft.Compute/virtualMachineScaleSets'"
)
```

## Resource Matching Logic

The tool uses intelligent, **dynamic** matching to correlate Azure resources with Terraform state by querying the actual state file rather than relying on hardcoded mappings.

### Matching Strategy

The tool uses a two-phase matching strategy for maximum accuracy:

#### Phase 1: State Inspection
For each resource in Terraform state, the tool executes `terraform state show` to extract:
- Azure resource ID from the state
- Terraform resource type
- Terraform resource name

This creates an index of all managed resources with their actual Azure resource IDs.

#### Phase 2: Intelligent Matching

Resources are matched using the following strategies, in order of preference:

1. **Azure Resource ID Match (Highest Confidence)**
   - Compares Azure resource ID from Azure Resource Graph with IDs stored in Terraform state
   - This is the most reliable method as it's an exact match
   - Confidence level: **High**
   - Match method: `azure_id`

2. **Normalized Name Match (Medium Confidence)**
   - Falls back to name-based matching when resource ID isn't available in state
   - Removes special characters (-, _, .) and converts to lowercase
   - Example: `my-storage-account` matches `my_storage_account`
   - Confidence level: **Medium**
   - Match method: `name`

3. **Name with Type Hint (Medium Confidence)**
   - When multiple resources have the same normalized name
   - Uses resource type similarity as a tiebreaker
   - Confidence level: **Medium**
   - Match method: `name_with_type_hint`

### Advantages of Dynamic Matching

✅ **Universal Support**: Works with ANY Azure resource type (not limited to predefined mappings)  
✅ **Provider Agnostic**: Supports azurerm, azapi, and even custom providers  
✅ **Accurate**: Uses actual Azure resource IDs from state for exact matching  
✅ **Future-Proof**: No need to update tool when Azure adds new resource types  
✅ **Handles Complexity**: Works with child resources, nested resources, and complex topologies

### Matching Examples

**Example 1: Perfect Match by Azure ID**
```
Azure Resource:
  ID: /subscriptions/.../storageAccounts/mystore
  
Terraform State (from state show):
  azurerm_storage_account.mystore
    id = "/subscriptions/.../storageAccounts/mystore"

Result: ✅ MATCHED (confidence: high, method: azure_id)
```

**Example 2: Name-Based Match**
```
Azure Resource:
  ID: /subscriptions/.../storageAccounts/my-storage
  Name: my-storage
  
Terraform State:
  azurerm_storage_account.my_storage
    (ID not available in output)

Result: ✅ MATCHED (confidence: medium, method: name)
  - Normalized names match: "mystorage" == "mystorage"
```

**Example 3: Resource Not in Terraform**
```
Azure Resource:
  ID: /subscriptions/.../storageAccounts/unmanaged
  
Terraform State:
  (no matching resource)

Result: ❌ MISSING from Terraform
  - Added to missing_resources list
  - Export command provided
```

**Example 4: Orphaned Terraform Resource**
```
Terraform State:
  azurerm_storage_account.deleted
    id = "/subscriptions/.../storageAccounts/deleted"
  
Azure Resources:
  (no matching resource ID)

Result: ⚠️ ORPHANED in Terraform
  - Resource exists in state but not in Azure
  - May have been deleted manually
```

## Troubleshooting

### "Failed to retrieve Terraform state"

**Cause**: Workspace not initialized or state file doesn't exist.

**Solution**:
```bash
cd workspace/your-workspace
terraform init
```

### "Failed to query Azure resources"

**Cause**: Azure CLI not authenticated or insufficient permissions.

**Solution**:
```bash
# Authenticate
az login

# Verify access
az account show
az graph query -q "Resources | take 1"
```

### "Coverage percentage is 0% but resources exist"

**Cause**: Resources exist but Azure resource IDs in state don't match Azure Resource Graph results, or state inspection failed.

**Solution**:
1. Verify Terraform state is up-to-date: `terraform refresh`
2. Check that resource names match between Azure and Terraform
3. Ensure Azure authentication has proper subscription access
4. Review the `missing_resources` and `orphaned_resources` sections for details
5. Check logs for state inspection errors

### "Orphaned resources after Azure resource rename"

**Cause**: Resources renamed in Azure portal break the Terraform linkage.

**Solution**:
```bash
# Option 1: Update Terraform resource name and use state mv
terraform state mv azurerm_storage_account.old_name azurerm_storage_account.new_name

# Option 2: Remove from state and re-import
terraform state rm azurerm_storage_account.old_name
terraform import azurerm_storage_account.new_name /subscriptions/.../resourceId
```

## Best Practices

### 1. Regular Audits
Run coverage audits regularly (weekly/monthly) to catch drift early.

### 2. Set Coverage Goals
- **New projects**: Target 100% coverage from day one
- **Migration projects**: Set incremental goals (50% → 75% → 95%)
- **Mature projects**: Maintain 95%+ coverage

### 3. Automate Remediation
Integrate audit results into CI/CD pipelines:
```yaml
# Example: Azure DevOps pipeline
- script: |
    python audit_coverage.py
    if [ $COVERAGE -lt 95 ]; then
      echo "##vso[task.logissue type=warning]Coverage below 95%"
    fi
```

### 4. Document Exceptions
Some resources may intentionally remain outside Terraform:
- Temporary development resources
- Resources managed by other tools
- Legacy resources pending migration

Document these in your coverage reports.

### 5. Combine with Other Tools

Use coverage audit alongside other MCP tools:
```python
# Step 1: Audit coverage
audit_result = audit_terraform_coverage(...)

# Step 2: Export missing resources
for resource in audit_result['missing_resources']:
    export_azure_resource(resource_id=resource['resource_id'])

# Step 3: Clean up orphaned resources
for orphaned in audit_result['orphaned_resources']:
    # Review manually before removing
    # terraform state rm {orphaned['terraform_address']}
```

## Integration with Aztfexport

The coverage audit tool works seamlessly with aztfexport tools:

```python
# Workflow: Discover → Export → Validate
# 1. Discover missing resources
audit_result = audit_terraform_coverage(
    workspace_folder="workspace/prod",
    scope="resource-group",
    scope_value="prod-rg"
)

# 2. Export missing resources
for resource in audit_result['missing_resources']:
    export_azure_resource(
        resource_id=resource['resource_id'],
        output_folder_name=f"exported-{resource['resource_name']}"
    )

# 3. Re-audit to verify coverage improved
new_audit = audit_terraform_coverage(
    workspace_folder="workspace/prod",
    scope="resource-group",
    scope_value="prod-rg"
)

print(f"Coverage improved: {audit_result['summary']['coverage_percentage']}% → {new_audit['summary']['coverage_percentage']}%")
```

## API Reference

For detailed API specifications, see [API Reference](api-reference.md#audit_terraform_coverage).

## Related Tools

- **export_azure_resource**: Export individual Azure resources to Terraform
- **export_azure_resource_group**: Export entire resource groups
- **export_azure_resources_by_query**: Bulk export using Azure Resource Graph queries

## Support

For issues, feature requests, or questions:
- GitHub Issues: [tf-mcp-server/issues](https://github.com/liuwuliuyun/tf-mcp-server/issues)
- Documentation: [README.md](../README.md)

---

**Last Updated**: October 28, 2025  
**Version**: 0.1.0
