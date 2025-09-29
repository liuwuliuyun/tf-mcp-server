# Azure Best Practices - Practical Terraform Examples

This document provides practical Terraform code examples that implement the best practices recommended by the `get_azure_best_practices` tool.

## Provider Configuration Examples

### Recommended Provider Versions (AzureRM 4.x + AzAPI 2.x)

```hcl
terraform {
  required_version = ">= 1.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"  # Use AzureRM 4.x
    }
    azapi = {
      source  = "Azure/azapi"
      version = "~> 2.0"  # Use AzAPI 2.x
    }
  }
}

provider "azurerm" {
  features {}
}

provider "azapi" {}
```

## AzAPI 2.x Best Practices Examples

### ✅ Correct: Direct HCL Object Usage (AzAPI 2.x)

```hcl
# AzAPI 2.x - Use HCL objects directly
resource "azapi_resource" "example" {
  type      = "Microsoft.Storage/storageAccounts@2021-09-01"
  parent_id = azurerm_resource_group.example.id
  name      = "examplestorageaccount"
  
  # ✅ Use HCL object directly in AzAPI 2.x
  body = {
    location = "East US"
    properties = {
      accessTier = "Hot"
      allowBlobPublicAccess = false
      minimumTlsVersion = "TLS1_2"
      supportsHttpsTrafficOnly = true
    }
    sku = {
      name = "Standard_LRS"
    }
  }
}
```

### ❌ Avoid: Using jsonencode() in AzAPI 2.x

```hcl
# ❌ Don't do this in AzAPI 2.x (this was needed in 1.x)
resource "azapi_resource" "example_old_way" {
  type      = "Microsoft.Storage/storageAccounts@2021-09-01"
  parent_id = azurerm_resource_group.example.id
  name      = "examplestorageaccount"
  
  # ❌ jsonencode() not needed in AzAPI 2.x
  body = jsonencode({
    location = "East US"
    properties = {
      accessTier = "Hot"
      allowBlobPublicAccess = false
    }
    sku = {
      name = "Standard_LRS"
    }
  })
}
```

## Resource Organization Best Practices

### Proper Resource Naming and Tagging

```hcl
locals {
  # Consistent naming convention
  environment = "prod"
  application = "webapp"
  location    = "eastus"
  
  # Common tags
  common_tags = {
    Environment   = local.environment
    Application   = local.application
    ManagedBy     = "Terraform"
    Owner         = "DevOps Team"
    CostCenter    = "Engineering"
    Project       = "MyProject"
  }
  
  # Resource naming convention: {env}-{app}-{resource}-{location}
  resource_prefix = "${local.environment}-${local.application}"
}

resource "azurerm_resource_group" "main" {
  name     = "${local.resource_prefix}-rg-${local.location}"
  location = "East US"
  tags     = local.common_tags
}

resource "azurerm_storage_account" "main" {
  name                = "${replace(local.resource_prefix, "-", "")}st${local.location}"
  resource_group_name = azurerm_resource_group.main.name
  location           = azurerm_resource_group.main.location
  
  account_tier             = "Standard"
  account_replication_type = "LRS"
  
  # Security best practices
  allow_nested_items_to_be_public = false
  min_tls_version                 = "TLS1_2"
  
  tags = local.common_tags
}
```

## State Management Best Practices

### Remote State Configuration

```hcl
terraform {
  backend "azurerm" {
    resource_group_name  = "terraform-state-rg"
    storage_account_name = "terraformstateaccount"
    container_name       = "tfstate"
    key                  = "prod/terraform.tfstate"
    
    # Enable state locking
    use_azuread_auth = true
  }
}
```

## Security Best Practices Examples

### Network Security Groups

```hcl
resource "azurerm_network_security_group" "web_tier" {
  name                = "${local.resource_prefix}-web-nsg-${local.location}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name

  # Allow HTTPS only
  security_rule {
    name                       = "Allow_HTTPS"
    priority                   = 1001
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "443"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  # Deny all other inbound traffic
  security_rule {
    name                       = "Deny_All_Inbound"
    priority                   = 4000
    direction                  = "Inbound"
    access                     = "Deny"
    protocol                   = "*"
    source_port_range          = "*"
    destination_port_range     = "*"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  tags = local.common_tags
}
```

### Key Vault for Secrets Management

```hcl
resource "azurerm_key_vault" "main" {
  name                = "${local.resource_prefix}-kv-${local.location}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  tenant_id           = data.azurerm_client_config.current.tenant_id

  sku_name = "standard"

  # Security best practices
  enabled_for_disk_encryption     = true
  enabled_for_deployment          = false
  enabled_for_template_deployment = false
  purge_protection_enabled        = true
  soft_delete_retention_days      = 7

  network_acls {
    default_action = "Deny"
    bypass         = "AzureServices"
  }

  tags = local.common_tags
}
```

## Compute Best Practices Examples

### Virtual Machine with Managed Disks

```hcl
resource "azurerm_linux_virtual_machine" "main" {
  name                = "${local.resource_prefix}-vm-${local.location}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  size                = "Standard_B2s"  # Right-sized for workload
  
  # Disable password authentication (use SSH keys)
  disable_password_authentication = true

  network_interface_ids = [
    azurerm_network_interface.main.id,
  ]

  admin_username = "adminuser"

  admin_ssh_key {
    username   = "adminuser"
    public_key = file("~/.ssh/id_rsa.pub")
  }

  # Use managed disks (recommended)
  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "Premium_LRS"  # Better performance
  }

  source_image_reference {
    publisher = "Canonical"
    offer     = "0001-com-ubuntu-server-jammy"
    sku       = "22_04-lts-gen2"
    version   = "latest"
  }

  # Enable boot diagnostics
  boot_diagnostics {
    storage_account_uri = azurerm_storage_account.main.primary_blob_endpoint
  }

  tags = local.common_tags
}

# Backup configuration
resource "azurerm_backup_policy_vm" "main" {
  name                = "${local.resource_prefix}-backup-policy"
  resource_group_name = azurerm_resource_group.main.name
  recovery_vault_name = azurerm_recovery_services_vault.main.name

  backup {
    frequency = "Daily"
    time      = "23:00"
  }

  retention_daily {
    count = 30
  }

  tags = local.common_tags
}
```

## Database Best Practices Examples

### Azure SQL Database with Security Features

```hcl
resource "azurerm_mssql_server" "main" {
  name                         = "${local.resource_prefix}-sqlserver-${local.location}"
  resource_group_name          = azurerm_resource_group.main.name
  location                     = azurerm_resource_group.main.location
  version                      = "12.0"
  administrator_login          = "sqladmin"
  administrator_login_password = azurerm_key_vault_secret.sql_admin_password.value

  # Security best practices
  minimum_tls_version               = "1.2"
  public_network_access_enabled     = false  # Private access only

  azuread_administrator {
    login_username = "sqladmin@contoso.com"
    object_id      = data.azuread_user.sql_admin.object_id
  }

  tags = local.common_tags
}

resource "azurerm_mssql_database" "main" {
  name      = "${local.resource_prefix}-sqldb"
  server_id = azurerm_mssql_server.main.id
  
  # Right-size based on workload
  sku_name   = "S2"  # Standard tier
  collation  = "SQL_Latin1_General_CP1_CI_AS"

  # Enable threat detection
  threat_detection_policy {
    state                = "Enabled"
    email_account_admins = "Enabled"
    retention_days       = 30
  }

  # Enable auditing
  extended_auditing_policy {
    storage_endpoint           = azurerm_storage_account.main.primary_blob_endpoint
    storage_account_access_key = azurerm_storage_account.main.primary_access_key
    retention_in_days          = 90
  }

  tags = local.common_tags
}
```

## Monitoring Best Practices Examples

### Application Insights and Log Analytics

```hcl
resource "azurerm_log_analytics_workspace" "main" {
  name                = "${local.resource_prefix}-loganalytics-${local.location}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = "PerGB2018"
  retention_in_days   = 90

  tags = local.common_tags
}

resource "azurerm_application_insights" "main" {
  name                = "${local.resource_prefix}-appinsights-${local.location}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  workspace_id        = azurerm_log_analytics_workspace.main.id
  application_type    = "web"

  tags = local.common_tags
}

# Alert rule for high error rate
resource "azurerm_monitor_metric_alert" "high_error_rate" {
  name                = "High Error Rate Alert"
  resource_group_name = azurerm_resource_group.main.name
  scopes              = [azurerm_application_insights.main.id]

  criteria {
    metric_namespace = "Microsoft.Insights/components"
    metric_name      = "exceptions/count"
    aggregation      = "Count"
    operator         = "GreaterThan"
    threshold        = 10
  }

  action {
    action_group_id = azurerm_monitor_action_group.main.id
  }

  tags = local.common_tags
}
```

## Variable Validation Examples

```hcl
variable "environment" {
  description = "Environment name"
  type        = string
  
  validation {
    condition = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

variable "vm_size" {
  description = "Virtual machine size"
  type        = string
  default     = "Standard_B2s"
  
  validation {
    condition = can(regex("^Standard_[BD][0-9]+[ms]?$", var.vm_size))
    error_message = "VM size must be a valid Azure VM size (e.g., Standard_B2s, Standard_D2s_v3)."
  }
}
```

## Lifecycle Management Examples

```hcl
resource "azurerm_storage_account" "main" {
  name                = "${replace(local.resource_prefix, "-", "")}st${local.location}"
  resource_group_name = azurerm_resource_group.main.name
  location           = azurerm_resource_group.main.location
  
  account_tier             = "Standard"
  account_replication_type = "LRS"

  # Lifecycle management
  lifecycle {
    prevent_destroy = true  # Protect critical resources
    ignore_changes = [
      tags["CreatedDate"],  # Ignore automatically generated tags
    ]
  }

  tags = local.common_tags
}
```

These examples demonstrate the practical application of the best practices provided by the `get_azure_best_practices` tool, showing real-world Terraform configurations that follow Azure and Terraform best practices.