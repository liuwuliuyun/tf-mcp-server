# Terraform State Management with MCP Server

This document describes how to use the `run_terraform_command` tool for Terraform state management operations, which are essential for making exported code production-ready.

## Overview

The `run_terraform_command` tool now supports the full range of Terraform state management commands through the `state` command with various subcommands. This is particularly useful when refactoring exported Terraform code to use meaningful resource names instead of generic names like `res-0`, `res-1`, etc.

## State Subcommands Supported

### 1. `state list` - List All Resources

Lists all resources in the current state file.

**Usage:**
```
run_terraform_command(
    command="state",
    workspace_folder="exported-rg-myapp",
    state_subcommand="list"
)
```

**Example Output:**
```
azurerm_resource_group.res-0
azurerm_storage_account.res-1
azurerm_virtual_network.res-2
azurerm_subnet.res-3
```

**When to use:**
- Initial inspection of exported resources
- Understanding the current state structure
- Before planning resource renames

---

### 2. `state show` - Show Resource Details

Displays detailed information about a specific resource in the state.

**Usage:**
```
run_terraform_command(
    command="state",
    workspace_folder="exported-rg-myapp",
    state_subcommand="show",
    state_args="azurerm_resource_group.res-0"
)
```

**Example Output:**
```
# azurerm_resource_group.res-0:
resource "azurerm_resource_group" "res-0" {
    id       = "/subscriptions/xxx/resourceGroups/myapp-rg"
    location = "eastus"
    name     = "myapp-rg"
    tags     = {
        "environment" = "production"
    }
}
```

**When to use:**
- Inspecting resource properties before refactoring
- Understanding resource dependencies
- Verifying resource addresses before moving

---

### 3. `state mv` - Move/Rename Resources

Moves or renames a resource in the state file. This is the most critical command for the code cleanup workflow.

**Usage:**
```
run_terraform_command(
    command="state",
    workspace_folder="exported-rg-myapp",
    state_subcommand="mv",
    state_args="azurerm_resource_group.res-0 azurerm_resource_group.main"
)
```

**Important:**
- Always update your `.tf` files FIRST before running `state mv`
- The state_args format is: `<source_address> <destination_address>`
- Source and destination must use the full resource address including type

**Example Workflow:**

1. **Initial exported code:**
```hcl
resource "azurerm_resource_group" "res-0" {
  name     = "myapp-rg"
  location = "eastus"
}
```

2. **Update .tf file with meaningful name:**
```hcl
resource "azurerm_resource_group" "main" {
  name     = "myapp-rg"
  location = "eastus"
}
```

3. **Run state mv command:**
```
run_terraform_command(
    command="state",
    workspace_folder="exported-rg-myapp",
    state_subcommand="mv",
    state_args="azurerm_resource_group.res-0 azurerm_resource_group.main"
)
```

4. **Verify with plan:**
```
run_terraform_command(
    command="plan",
    workspace_folder="exported-rg-myapp"
)
```

Expected output: `No changes. Your infrastructure matches the configuration.`

**When to use:**
- Renaming resources from generic names to meaningful names
- Restructuring resource organization
- Moving resources between modules

---

### 4. `state rm` - Remove Resources from State

Removes a resource from the state file without destroying the actual resource in Azure.

**Usage:**
```
run_terraform_command(
    command="state",
    workspace_folder="exported-rg-myapp",
    state_subcommand="rm",
    state_args="azurerm_storage_account.res-1"
)
```

**Warning:** This removes the resource from Terraform management but does NOT delete it from Azure.

**When to use:**
- Removing resources that should be managed by another Terraform configuration
- Excluding resources from Terraform management
- Cleaning up orphaned state entries

---

### 5. `state pull` - Pull Current State

Retrieves the current state and outputs it to stdout. Useful for remote backends.

**Usage:**
```
run_terraform_command(
    command="state",
    workspace_folder="exported-rg-myapp",
    state_subcommand="pull"
)
```

**When to use:**
- Inspecting remote state contents
- Creating state backups
- Debugging state issues

---

### 6. `state push` - Push Local State

Uploads a local state file to the remote backend. **USE WITH EXTREME CAUTION.**

**Usage:**
```
run_terraform_command(
    command="state",
    workspace_folder="exported-rg-myapp",
    state_subcommand="push"
)
```

**Warning:** This can overwrite remote state. Always backup before using.

**When to use:**
- Restoring from a backup
- Migrating state between backends
- Emergency state recovery

---

## Complete Code Cleanup Workflow

Here's a complete example of cleaning up exported Terraform code:

### Step 1: Export Resources
```
export_azure_resource_group(
    resource_group_name="myapp-rg",
    output_folder_name="myapp-infrastructure"
)
```

### Step 2: List All Resources
```
run_terraform_command(
    command="state",
    workspace_folder="myapp-infrastructure",
    state_subcommand="list"
)
```

Output:
```
azurerm_resource_group.res-0
azurerm_storage_account.res-1
azurerm_app_service_plan.res-2
azurerm_app_service.res-3
```

### Step 3: Get Best Practices
```
get_azure_best_practices(
    resource="aztfexport",
    action="code-cleanup"
)
```

### Step 4: Update .tf Files

Edit the Terraform files to use meaningful names:

**Before:**
```hcl
resource "azurerm_resource_group" "res-0" {
  name     = "myapp-rg"
  location = "eastus"
}

resource "azurerm_storage_account" "res-1" {
  name                     = "myappstg001"
  resource_group_name      = azurerm_resource_group.res-0.name
  location                 = azurerm_resource_group.res-0.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
}
```

**After:**
```hcl
resource "azurerm_resource_group" "main" {
  name     = "myapp-rg"
  location = "eastus"
  
  tags = local.common_tags
}

resource "azurerm_storage_account" "app_storage" {
  name                     = "myappstg001"
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  
  tags = local.common_tags
}
```

### Step 5: Rename Resources in State

```
# Rename resource group
run_terraform_command(
    command="state",
    workspace_folder="myapp-infrastructure",
    state_subcommand="mv",
    state_args="azurerm_resource_group.res-0 azurerm_resource_group.main"
)

# Rename storage account
run_terraform_command(
    command="state",
    workspace_folder="myapp-infrastructure",
    state_subcommand="mv",
    state_args="azurerm_storage_account.res-1 azurerm_storage_account.app_storage"
)

# Rename app service plan
run_terraform_command(
    command="state",
    workspace_folder="myapp-infrastructure",
    state_subcommand="mv",
    state_args="azurerm_app_service_plan.res-2 azurerm_app_service_plan.main"
)

# Rename app service
run_terraform_command(
    command="state",
    workspace_folder="myapp-infrastructure",
    state_subcommand="mv",
    state_args="azurerm_app_service.res-3 azurerm_app_service.webapp"
)
```

### Step 6: Verify No Changes
```
run_terraform_command(
    command="plan",
    workspace_folder="myapp-infrastructure"
)
```

Expected output:
```
No changes. Your infrastructure matches the configuration.
```

If you see any resources being recreated, you likely missed a state mv command or have a typo in resource references.

### Step 7: Add Variables and Locals

Create `variables.tf`:
```hcl
variable "location" {
  description = "Azure region for resources"
  type        = string
  default     = "eastus"
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "app_name" {
  description = "Application name"
  type        = string
}
```

Create `locals.tf`:
```hcl
locals {
  common_tags = {
    environment = var.environment
    application = var.app_name
    managed_by  = "terraform"
  }
  
  resource_group_name = "${var.environment}-${var.app_name}-rg"
}
```

### Step 8: Final Verification
```
run_terraform_command(
    command="validate",
    workspace_folder="myapp-infrastructure"
)

run_terraform_command(
    command="plan",
    workspace_folder="myapp-infrastructure"
)
```

---

## Best Practices

1. **Always Backup State First**
   ```
   run_terraform_command(
       command="state",
       workspace_folder="myapp-infrastructure",
       state_subcommand="pull"
   )
   # Save the output to a backup file
   ```

2. **Test in Development First**
   - Never test state operations directly on production
   - Use a copy of the exported code in a test environment
   - Verify the workflow before applying to production

3. **Document All Changes**
   - Keep a log of all `state mv` commands
   - Document the mapping: old name → new name
   - Include reasoning for name changes

4. **Verify After Each Change**
   - Run `terraform plan` after each state mv
   - Ensure "No changes" appears
   - Fix any issues before proceeding

5. **Use Consistent Naming**
   - Follow organizational naming conventions
   - Use meaningful, descriptive names
   - Be consistent across resources

6. **Handle Dependencies Carefully**
   - Update dependent resources after primary resources
   - Check for resource references in other files
   - Update data source references if needed

---

## Common Errors and Solutions

### Error: "Resource not found in state"
**Cause:** Typo in resource address or resource doesn't exist

**Solution:** 
```
# List all resources to find correct address
run_terraform_command(
    command="state",
    workspace_folder="myapp-infrastructure",
    state_subcommand="list"
)
```

### Error: "Destination resource already exists"
**Cause:** Target resource name already used in state

**Solution:**
- Choose a different destination name
- Or remove the existing resource first if it's orphaned

### Error: Plan shows resource recreation
**Cause:** Resource references not updated or state mv not executed

**Solution:**
1. Check all resource references in .tf files
2. Verify state mv commands were successful
3. Run `terraform state list` to see current addresses

### Error: "Cannot move to the same address"
**Cause:** Source and destination are identical

**Solution:**
- Double-check your source and destination addresses
- Ensure you're actually changing the resource name

---

## Integration with Best Practices Tool

The `get_azure_best_practices` tool provides comprehensive guidance for using state commands:

```
get_azure_best_practices(
    resource="aztfexport",
    action="code-cleanup"
)
```

This returns detailed recommendations including:
- Resource naming conventions
- When to use variables vs locals
- Complete state management workflow
- Security hardening steps
- Production readiness checklist

---

## Summary

The enhanced `run_terraform_command` tool with state management capabilities enables a complete workflow for cleaning up exported Terraform code:

1. **Export** - Use aztfexport to export existing resources
2. **Inspect** - Use `state list` and `state show` to understand structure
3. **Refactor** - Update .tf files with meaningful names
4. **Rename** - Use `state mv` to update state file
5. **Verify** - Use `plan` to ensure no unintended changes
6. **Enhance** - Add variables, locals, tags, and best practices

This workflow transforms exported code from a simple dump into production-ready infrastructure as code that's maintainable, well-organized, and follows best practices.
