# Terraform Command Integration

This guide covers the Terraform command execution capabilities of the MCP server, allowing you to run Terraform CLI commands and state management operations directly through the MCP interface.

## 🚀 Overview

The `run_terraform_command` tool provides a unified interface to execute all major Terraform CLI commands and state management operations within workspace directories that contain Terraform configuration files.

## 📋 Supported Commands

| Command | Description | Common Use Cases |
|---------|-------------|------------------|
| `init` | Initialize Terraform workspace | First-time setup, provider updates |
| `plan` | Generate execution plan | Review changes before apply |
| `apply` | Apply configuration changes | Deploy infrastructure |
| `destroy` | Destroy managed infrastructure | Clean up resources |
| `validate` | Validate configuration syntax | CI/CD validation, debugging |
| `fmt` | Format configuration files | Code formatting, pre-commit hooks |
| `state` | State management operations | Resource renaming, state inspection |

## 🔧 Tool Reference

### `run_terraform_command`

Execute Terraform CLI commands inside a workspace folder.

**Parameters:**
- `command` (required): Terraform command to execute (init, plan, apply, destroy, validate, fmt, state)
- `workspace_folder` (required): Path to workspace containing Terraform files
- `auto_approve` (optional): Auto-approve for apply/destroy (default: false) ⚠️
- `upgrade` (optional): Upgrade providers/modules for init (default: false)
- `state_subcommand` (optional): State operation (list, show, mv, rm, pull, push) - required when command='state'
- `state_args` (optional): Arguments for state subcommand (required for show, mv, rm)

**Returns:**
```json
{
  "success": true,
  "stdout": "Command output...",
  "stderr": "Error output...",
  "exit_code": 0,
  "execution_time": "2.5s"
}
```

---

## 📖 Command Examples

### Initialize Terraform

```json
{
  "tool": "run_terraform_command",
  "arguments": {
    "command": "init",
    "workspace_folder": "workspace/demo"
  }
}
```

**With provider upgrade:**
```json
{
  "tool": "run_terraform_command", 
  "arguments": {
    "command": "init",
    "workspace_folder": "workspace/demo",
    "upgrade": true
  }
}
```

### Generate Execution Plan

```json
{
  "tool": "run_terraform_command",
  "arguments": {
    "command": "plan", 
    "workspace_folder": "workspace/demo"
  }
}
```

### Apply Changes

```json
{
  "tool": "run_terraform_command",
  "arguments": {
    "command": "apply",
    "workspace_folder": "workspace/demo"
  }
}
```

**With auto-approve (use with caution):**
```json
{
  "tool": "run_terraform_command",
  "arguments": {
    "command": "apply",
    "workspace_folder": "workspace/demo", 
    "auto_approve": true
  }
}
```

### Validate Configuration

```json
{
  "tool": "run_terraform_command",
  "arguments": {
    "command": "validate",
    "workspace_folder": "workspace/demo"
  }
}
```

### Format Code

```json
{
  "tool": "run_terraform_command",
  "arguments": {
    "command": "fmt",
    "workspace_folder": "workspace/demo"
  }
}
```

### Destroy Infrastructure

```json
{
  "tool": "run_terraform_command",
  "arguments": {
    "command": "destroy",
    "workspace_folder": "workspace/demo"
  }
}
```

**With auto-approve (dangerous):**
```json
{
  "tool": "run_terraform_command",
  "arguments": {
    "command": "destroy",
    "workspace_folder": "workspace/demo",
    "auto_approve": true
  }
}
```

---

## 🏗️ Workspace Setup

### Required Structure

Your workspace folder must contain valid Terraform configuration files:

```
workspace/demo/
├── main.tf          # Main configuration
├── variables.tf     # Input variables
├── outputs.tf       # Output definitions
├── terraform.tf     # Provider configuration
└── terraform.tfvars # Variable values (optional)
```

### Example Configuration

**main.tf:**
```hcl
resource "azurerm_resource_group" "main" {
  name     = var.resource_group_name
  location = var.location
}

resource "azurerm_storage_account" "main" {
  name                     = var.storage_account_name
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
}
```

**terraform.tf:**
```hcl
terraform {
  required_version = ">= 1.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
  }
}

provider "azurerm" {
  features {}
}
```

---

## 🔄 Common Workflows

### 1. New Project Setup

```json
# Step 1: Initialize workspace
{
  "tool": "run_terraform_command",
  "arguments": {
    "command": "init", 
    "workspace_folder": "workspace/new-project"
  }
}

# Step 2: Validate configuration
{
  "tool": "run_terraform_command",
  "arguments": {
    "command": "validate",
    "workspace_folder": "workspace/new-project"
  }
}

# Step 3: Generate plan
{
  "tool": "run_terraform_command",
  "arguments": {
    "command": "plan",
    "workspace_folder": "workspace/new-project"
  }
}

# Step 4: Apply changes
{
  "tool": "run_terraform_command", 
  "arguments": {
    "command": "apply",
    "workspace_folder": "workspace/new-project"
  }
}
```

### 2. Code Maintenance

```json
# Step 1: Format code
{
  "tool": "run_terraform_command",
  "arguments": {
    "command": "fmt",
    "workspace_folder": "workspace/project"
  }
}

# Step 2: Validate syntax
{
  "tool": "run_terraform_command",
  "arguments": {
    "command": "validate", 
    "workspace_folder": "workspace/project"
  }
}

# Step 3: Check for changes
{
  "tool": "run_terraform_command",
  "arguments": {
    "command": "plan",
    "workspace_folder": "workspace/project"
  }
}
```

### 3. Provider Updates

```json
# Step 1: Upgrade providers
{
  "tool": "run_terraform_command",
  "arguments": {
    "command": "init",
    "workspace_folder": "workspace/project",
    "upgrade": true
  }
}

# Step 2: Plan with new providers
{
  "tool": "run_terraform_command",
  "arguments": {
    "command": "plan",
    "workspace_folder": "workspace/project"
  }
}
```

### 4. Working with aztfexport

```json
# After using aztfexport to create workspace
# Step 1: Initialize the exported workspace
{
  "tool": "run_terraform_command",
  "arguments": {
    "command": "init",
    "workspace_folder": "exported-resources"
  }
}

# Step 2: Validate exported configuration
{
  "tool": "run_terraform_command",
  "arguments": {
    "command": "validate",
    "workspace_folder": "exported-resources"
  }
}

# Step 3: Plan to see current state
{
  "tool": "run_terraform_command",
  "arguments": {
    "command": "plan",
    "workspace_folder": "exported-resources"
  }
}
```

---

## ⚠️ Safety Features

### Auto-Approve Protection

The `auto_approve` parameter is disabled by default for safety:
- **apply**: Requires manual confirmation unless `auto_approve=true`
- **destroy**: Requires manual confirmation unless `auto_approve=true`  
- **plan**: No approval needed (read-only operation)

### Command Validation

- Only supported Terraform commands are allowed
- Workspace folder must exist and contain .tf files
- Invalid parameters are rejected with clear error messages

### Error Handling

```json
{
  "success": false,
  "error": "Terraform command failed",
  "stdout": "Partial output...",
  "stderr": "Error details...", 
  "exit_code": 1,
  "suggestions": ["Check configuration syntax", "Verify provider credentials"]
}
```

---

## 🔍 Integration with Other Tools

### With Static Analysis

```json
# Step 1: Run TFLint analysis first
{
  "tool": "run_tflint_workspace_analysis",
  "arguments": {
    "workspace_folder": "workspace/project"
  }
}

# Step 2: Format and validate
{
  "tool": "run_terraform_command",
  "arguments": {
    "command": "fmt",
    "workspace_folder": "workspace/project"
  }
}

{
  "tool": "run_terraform_command",
  "arguments": {
    "command": "validate",
    "workspace_folder": "workspace/project"
  }
}
```

### With Security Validation

```json
# Step 1: Generate plan file
{
  "tool": "run_terraform_command",
  "arguments": {
    "command": "plan",
    "workspace_folder": "workspace/project"
  }
}

# Step 2: Validate with Conftest
{
  "tool": "run_conftest_workspace_validation",
  "arguments": {
    "workspace_folder": "workspace/project",
    "policy_set": "avmsec"
  }
}

# Step 3: Apply if validation passes
{
  "tool": "run_terraform_command",
  "arguments": {
    "command": "apply",
    "workspace_folder": "workspace/project"
  }
}
```

---

## � State Management Operations

The `run_terraform_command` tool supports full Terraform state management, enabling safe resource renaming and state manipulation.

### Supported State Subcommands

| Subcommand | Description | Requires state_args |
|------------|-------------|---------------------|
| `list` | List all resources in state | No |
| `show` | Show resource details | Yes |
| `mv` | Move/rename resource | Yes |
| `rm` | Remove resource from state | Yes |
| `pull` | Pull current state | No |
| `push` | Push local state | No |

### State Parameters

When using `command="state"`:
- `state_subcommand` (required): The state operation to perform
- `state_args` (required for show/mv/rm): Arguments for the operation

### State Examples

#### List All Resources

```json
{
  "tool": "run_terraform_command",
  "arguments": {
    "command": "state",
    "workspace_folder": "workspace/demo",
    "state_subcommand": "list"
  }
}
```

**Output:**
```
azurerm_resource_group.res-0
azurerm_storage_account.res-1
azurerm_virtual_network.res-2
```

#### Show Resource Details

```json
{
  "tool": "run_terraform_command",
  "arguments": {
    "command": "state",
    "workspace_folder": "workspace/demo",
    "state_subcommand": "show",
    "state_args": "azurerm_resource_group.res-0"
  }
}
```

#### Rename Resource

```json
{
  "tool": "run_terraform_command",
  "arguments": {
    "command": "state",
    "workspace_folder": "workspace/demo",
    "state_subcommand": "mv",
    "state_args": "azurerm_resource_group.res-0 azurerm_resource_group.main"
  }
}
```

**Important:** Always update your `.tf` files BEFORE running `state mv`!

#### Remove Resource from State

```json
{
  "tool": "run_terraform_command",
  "arguments": {
    "command": "state",
    "workspace_folder": "workspace/demo",
    "state_subcommand": "rm",
    "state_args": "azurerm_storage_account.old"
  }
}
```

**Warning:** This removes from state but doesn't delete the actual Azure resource.

### Code Cleanup Workflow

Complete workflow for making exported code production-ready:

```json
# Step 1: Export resources
{
  "tool": "export_azure_resource_group",
  "arguments": {
    "resource_group_name": "myapp-rg",
    "output_folder_name": "myapp"
  }
}

# Step 2: List resources
{
  "tool": "run_terraform_command",
  "arguments": {
    "command": "state",
    "workspace_folder": "myapp",
    "state_subcommand": "list"
  }
}
# Output: azurerm_resource_group.res-0, azurerm_storage_account.res-1

# Step 3: Get best practices
{
  "tool": "get_azure_best_practices",
  "arguments": {
    "resource": "aztfexport",
    "action": "code-cleanup"
  }
}

# Step 4: Update .tf files with meaningful names
# (manually or via AI assistant)

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

{
  "tool": "run_terraform_command",
  "arguments": {
    "command": "state",
    "workspace_folder": "myapp",
    "state_subcommand": "mv",
    "state_args": "azurerm_storage_account.res-1 azurerm_storage_account.app_storage"
  }
}

# Step 6: Verify no changes
{
  "tool": "run_terraform_command",
  "arguments": {
    "command": "plan",
    "workspace_folder": "myapp"
  }
}
# Expected: "No changes. Your infrastructure matches the configuration."
```

For comprehensive state management guidance, see [Terraform State Management Guide](terraform-state-management.md).

---

## �🛠️ Environment Configuration

### Azure Authentication

Commands requiring Azure access need authentication:

```bash
# Service Principal
export ARM_CLIENT_ID="your-client-id"
export ARM_CLIENT_SECRET="your-client-secret" 
export ARM_SUBSCRIPTION_ID="your-subscription-id"
export ARM_TENANT_ID="your-tenant-id"

# Or Azure CLI
az login
```

### Backend Configuration

For remote state management:

```hcl
terraform {
  backend "azurerm" {
    resource_group_name  = "terraform-state-rg"
    storage_account_name = "terraformstate"
    container_name       = "tfstate"
    key                  = "terraform.tfstate"
  }
}
```

---

## 📊 Performance Tips

### Parallel Operations
- Use `parallelism` parameter in Terraform configuration
- Consider resource dependencies when planning parallel execution

### State Management  
- Use remote state for team collaboration
- Enable state locking to prevent conflicts
- Regular state file backups

### Output Management
- Use output filters for large plan outputs
- Structured output formats for automation
- Log management for audit trails

---

## 🔗 Related Tools

- **[State Management Guide](terraform-state-management.md)**: Detailed state operations and code cleanup workflow
- **[Static Analysis](tflint-integration.md)**: TFLint integration for code quality
- **[Security Validation](conftest-avm-validation.md)**: Policy-based security checks
- **[Azure Export](aztfexport-integration.md)**: Export existing Azure resources
- **[Best Practices](azure-best-practices-tool.md)**: Get Terraform best practices and code cleanup guidance