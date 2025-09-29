# Terraform Command Integration

This guide covers the Terraform command execution capabilities of the MCP server, allowing you to run Terraform CLI commands directly through the MCP interface.

## 🚀 Overview

The `run_terraform_command` tool provides a unified interface to execute all major Terraform CLI commands within workspace directories that contain Terraform configuration files.

## 📋 Supported Commands

| Command | Description | Common Use Cases |
|---------|-------------|------------------|
| `init` | Initialize Terraform workspace | First-time setup, provider updates |
| `plan` | Generate execution plan | Review changes before apply |
| `apply` | Apply configuration changes | Deploy infrastructure |
| `destroy` | Destroy managed infrastructure | Clean up resources |
| `validate` | Validate configuration syntax | CI/CD validation, debugging |
| `fmt` | Format configuration files | Code formatting, pre-commit hooks |

## 🔧 Tool Reference

### `run_terraform_command`

Execute Terraform CLI commands inside a workspace folder.

**Parameters:**
- `command` (required): Terraform command to execute
- `workspace_folder` (required): Path to workspace containing Terraform files
- `auto_approve` (optional): Auto-approve for apply/destroy (default: false) ⚠️
- `upgrade` (optional): Upgrade providers/modules for init (default: false)

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

## 🛠️ Environment Configuration

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

- **[Static Analysis](tflint-integration.md)**: TFLint integration for code quality
- **[Security Validation](conftest-avm-validation.md)**: Policy-based security checks
- **[Azure Export](aztfexport-integration.md)**: Export existing Azure resources
- **[Best Practices](azure-best-practices-tool.md)**: Get Terraform best practices