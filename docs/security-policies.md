# Security Policies Guide

This guide covers the security and compliance policies available in the Azure Terraform MCP Server for validating Azure infrastructure configurations.

## 🛡️ Overview

The MCP server includes comprehensive security policy sets for validating Terraform configurations against Azure security best practices and compliance standards.

## 📋 Available Policy Sets

| Policy Set | Description | Focus Area | Rules Count |
|------------|-------------|------------|-------------|
| **avmsec** | Azure Verified Modules Security | Core Azure security | 50+ rules |
| **Azure-Proactive-Resiliency-Library-v2** | Azure resilience and reliability | Business continuity | 30+ rules |
| **common** | Common infrastructure policies | General best practices | 20+ rules |

---

## 🔍 Policy Set Details

### Azure Verified Modules Security (avmsec)

Core security policies for Azure resources based on Microsoft security recommendations.

**Key Areas:**
- **Storage Security**: Encryption, access controls, network restrictions
- **Compute Security**: VM hardening, disk encryption, network security
- **Network Security**: NSG rules, subnet configurations, firewall settings
- **Identity & Access**: RBAC, managed identities, authentication
- **Database Security**: Encryption, access controls, audit logging

**Sample Rules:**
- `ACRAdminAccountDisabled` - Ensures Container Registry admin account is disabled
- `ACRAnonymousPullDisabled` - Prevents anonymous pull access to ACR
- `ACRPublicNetworkAccessDisabled` - Restricts public network access to ACR
- `StorageAccountMinTLSVersion` - Enforces minimum TLS version for storage
- `KeyVaultSoftDeleteEnabled` - Ensures Key Vault soft delete is enabled

### Azure Proactive Resiliency Library v2

Focuses on business continuity, disaster recovery, and service resilience.

**Key Areas:**
- **High Availability**: Multi-zone deployments, redundancy configurations
- **Backup & Recovery**: Backup policies, recovery configurations
- **Monitoring & Alerting**: Health checks, metric collection, alert setup
- **Scaling & Performance**: Auto-scaling, performance optimization
- **Geographic Distribution**: Multi-region deployments, traffic distribution

**Sample Rules:**
- `VirtualMachineAvailabilitySet` - Ensures VMs are in availability sets
- `StorageAccountReplication` - Validates storage replication settings
- `DatabaseBackupRetention` - Checks backup retention policies
- `LoadBalancerProbes` - Validates health probe configurations

### Common Policies

General infrastructure best practices applicable across cloud providers.

**Key Areas:**
- **Resource Tagging**: Mandatory tags, tag formats, governance
- **Naming Conventions**: Resource naming standards
- **Cost Management**: Resource sizing, lifecycle policies
- **Documentation**: Resource descriptions, metadata
- **Security Baselines**: Common security configurations

---

## 🔧 Using Security Policies

### Workspace Validation

Validate Terraform files in a workspace directory:

```json
{
  "tool": "run_conftest_workspace_validation",
  "arguments": {
    "workspace_folder": "workspace/my-project",
    "policy_set": "avmsec",
    "severity_filter": "high"
  }
}
```

### Plan Validation

Validate Terraform plan files:

```json
{
  "tool": "run_conftest_workspace_plan_validation",
  "arguments": {
    "folder_name": "workspace/my-project",
    "policy_set": "all"
  }
}
```

### Severity Filtering

Filter validation results by severity:

```json
{
  "tool": "run_conftest_workspace_validation",
  "arguments": {
    "workspace_folder": "workspace/production",
    "policy_set": "avmsec", 
    "severity_filter": "high"
  }
}
```

**Available severity levels:**
- `high` - Critical security issues
- `medium` - Important security recommendations  
- `low` - Best practice suggestions
- `all` - All findings (default)

---

## 🎯 Common Validation Scenarios

### 1. Pre-Deployment Security Check

```json
# Step 1: Validate workspace configuration
{
  "tool": "run_conftest_workspace_validation",
  "arguments": {
    "workspace_folder": "workspace/production",
    "policy_set": "avmsec",
    "severity_filter": "high"
  }
}

# Step 2: Generate and validate plan
{
  "tool": "run_terraform_command",
  "arguments": {
    "command": "plan",
    "workspace_folder": "workspace/production"
  }
}

# Step 3: Validate plan file
{
  "tool": "run_conftest_workspace_plan_validation",
  "arguments": {
    "folder_name": "workspace/production",
    "policy_set": "avmsec"
  }
}
```

### 2. Azure Export Security Validation

```json
# Step 1: Export existing Azure resource
{
  "tool": "export_azure_resource",
  "arguments": {
    "resource_id": "/subscriptions/xxx/resourceGroups/rg/providers/Microsoft.Storage/storageAccounts/mystorageaccount",
    "output_folder_name": "exported-storage"
  }
}

# Step 2: Validate exported configuration
{
  "tool": "run_conftest_workspace_validation",
  "arguments": {
    "workspace_folder": "exported-storage",
    "policy_set": "avmsec"
  }
}
```

### 3. Multi-Policy Validation

```json
# Security-focused validation
{
  "tool": "run_conftest_workspace_validation",
  "arguments": {
    "workspace_folder": "workspace/secure-app",
    "policy_set": "avmsec",
    "severity_filter": "high"
  }
}

# Resiliency-focused validation
{
  "tool": "run_conftest_workspace_validation", 
  "arguments": {
    "workspace_folder": "workspace/secure-app",
    "policy_set": "Azure-Proactive-Resiliency-Library-v2"
  }
}
```

---

## 📊 Understanding Validation Results

### Success Result

```json
{
  "success": true,
  "total_files": 3,
  "total_violations": 0,
  "policy_set": "avmsec",
  "message": "All files passed policy validation"
}
```

### Violation Result

```json
{
  "success": false,
  "total_files": 3,
  "total_violations": 2,
  "policy_set": "avmsec",
  "violations": [
    {
      "file": "main.tf",
      "policy": "StorageAccountMinTLSVersion",
      "severity": "high",
      "message": "Storage account must enforce minimum TLS version 1.2",
      "line": 15,
      "suggestion": "Add min_tls_version = '1.2' to storage account configuration"
    }
  ]
}
```

### Result Fields

- `success`: Whether all validations passed
- `total_files`: Number of files validated
- `total_violations`: Number of policy violations found
- `policy_set`: Policy set used for validation
- `violations`: Array of violation details
  - `file`: File containing the violation
  - `policy`: Policy rule that was violated
  - `severity`: Violation severity (high/medium/low)
  - `message`: Description of the violation
  - `line`: Line number (if available)
  - `suggestion`: Remediation suggestion

---

## 🔒 Resource-Specific Security Rules

### Storage Account Security

**Key Policies:**
- Minimum TLS version enforcement
- HTTPS-only traffic requirement
- Public access restrictions
- Encryption at rest configuration
- Network access controls

**Example Violation:**
```hcl
resource "azurerm_storage_account" "example" {
  name                = "mystorageaccount"
  # ❌ Missing: min_tls_version = "TLS1_2"
  # ❌ Missing: https_traffic_only_enabled = true
}
```

**Compliant Configuration:**
```hcl
resource "azurerm_storage_account" "example" {
  name                     = "mystorageaccount"
  min_tls_version         = "TLS1_2"          # ✅ Required
  https_traffic_only_enabled = true           # ✅ Required
  public_network_access_enabled = false       # ✅ Recommended
  
  blob_properties {
    delete_retention_policy {
      days = 7                                # ✅ Required
    }
  }
}
```

### Virtual Machine Security

**Key Policies:**
- OS disk encryption requirement
- Managed disk usage enforcement
- Network security group association
- SSH key authentication (Linux)
- Boot diagnostics enablement

**Example Violation:**
```hcl
resource "azurerm_linux_virtual_machine" "example" {
  name = "vm-example"
  # ❌ Missing: encryption at host
  # ❌ Missing: managed disk configuration
}
```

**Compliant Configuration:**
```hcl
resource "azurerm_linux_virtual_machine" "example" {
  name                = "vm-example"
  encryption_at_host_enabled = true          # ✅ Required
  
  os_disk {
    storage_account_type = "Premium_LRS"     # ✅ Required
    caching             = "ReadWrite"
  }
  
  identity {
    type = "SystemAssigned"                  # ✅ Recommended
  }
}
```

### Key Vault Security

**Key Policies:**
- Soft delete enablement
- Purge protection activation
- Network access restrictions
- Audit logging configuration
- RBAC usage enforcement

**Compliant Configuration:**
```hcl
resource "azurerm_key_vault" "example" {
  name                = "kv-example"
  soft_delete_retention_days = 7             # ✅ Required
  purge_protection_enabled   = true          # ✅ Required
  
  network_acls {
    default_action = "Deny"                  # ✅ Required
    bypass         = "AzureServices"
  }
}
```

---

## ⚡ Performance and Best Practices

### Validation Performance

**Optimize validation speed:**
```json
# Validate only high-severity issues for quick checks
{
  "tool": "run_conftest_workspace_validation",
  "arguments": {
    "workspace_folder": "workspace/large-project",
    "policy_set": "avmsec",
    "severity_filter": "high"
  }
}

# Use specific policy sets for targeted validation
{
  "tool": "run_conftest_workspace_validation", 
  "arguments": {
    "workspace_folder": "workspace/storage-only",
    "policy_set": "avmsec"  # More efficient than "all"
  }
}
```

### CI/CD Integration

**Pipeline validation example:**
```yaml
# GitHub Actions example
- name: Validate Security Policies
  run: |
    # Use MCP tool via API or CLI wrapper
    validate_terraform_security \
      --workspace ./terraform \
      --policy-set avmsec \
      --severity high \
      --fail-on-violations
```

### Policy Customization

While the MCP server comes with pre-configured policies, you can extend them:

1. **Custom Policy Directory:**
   ```bash
   # Set environment variable for additional policies
   export CONFTEST_CUSTOM_POLICY_PATH="/path/to/custom/policies"
   ```

2. **Policy Overrides:**
   Create local `.rego` files to override specific rules

3. **Severity Configuration:**
   Adjust severity levels for specific organizational requirements

---

## 🔍 Policy Development and Maintenance

### Policy Updates

The MCP server includes the latest versions of policy sets:
- **avmsec**: Updated with Azure security recommendations
- **Azure-Proactive-Resiliency-Library-v2**: Updated with Azure reliability patterns
- **common**: Updated with general best practices

### Custom Policy Development

For custom organizational policies:

1. **Rego Syntax:** Use Open Policy Agent (OPA) Rego language
2. **Testing:** Include test cases for policy rules
3. **Documentation:** Document policy intent and usage
4. **Versioning:** Maintain policy versions for consistency

### Policy Governance

**Establish governance processes:**
- Regular policy reviews and updates
- Exception handling procedures
- Policy compliance reporting
- Training and education programs

---

## 🚨 Compliance Frameworks

### Azure Security Benchmark

The `avmsec` policy set aligns with Azure Security Benchmark controls:
- **NS (Network Security)**: Network isolation and segmentation
- **IM (Identity Management)**: Identity and access controls  
- **PA (Privileged Access)**: Privileged access management
- **DP (Data Protection)**: Data encryption and privacy
- **AM (Asset Management)**: Resource inventory and control

### Industry Standards

**Supported compliance frameworks:**
- **ISO 27001**: Information security management
- **SOC 2**: Service organization controls
- **NIST Cybersecurity Framework**: Risk-based security approach
- **GDPR**: Data protection and privacy (where applicable)

---

## 🔗 Related Tools Integration

### With TFLint

```json
# Step 1: Static analysis with TFLint
{
  "tool": "run_tflint_workspace_analysis",
  "arguments": {
    "workspace_folder": "workspace/project"
  }
}

# Step 2: Security policy validation
{
  "tool": "run_conftest_workspace_validation",
  "arguments": {
    "workspace_folder": "workspace/project",
    "policy_set": "avmsec"
  }
}
```

### With Azure Export

```json
# Export and immediately validate
{
  "tool": "export_azure_resource_group",
  "arguments": {
    "resource_group_name": "production-rg",
    "output_folder_name": "exported-prod"
  }
}

{
  "tool": "run_conftest_workspace_validation",
  "arguments": {
    "workspace_folder": "exported-prod",
    "policy_set": "all"
  }
}
```

### With Best Practices

```json
# Get security best practices
{
  "tool": "get_azure_best_practices",
  "arguments": {
    "resource": "security",
    "action": "security"
  }
}

# Then validate against policies
{
  "tool": "run_conftest_workspace_validation",
  "arguments": {
    "workspace_folder": "workspace/project",
    "policy_set": "avmsec",
    "severity_filter": "high"
  }
}
```

---

## 📚 Additional Resources

- **[Conftest Documentation](https://www.conftest.dev/)**: Open Policy Agent testing framework
- **[OPA Rego Language](https://www.openpolicyagent.org/docs/latest/policy-language/)**: Policy language reference
- **[Azure Security Benchmark](https://docs.microsoft.com/en-us/security/benchmark/azure/)**: Microsoft security recommendations
- **[Azure Architecture Center](https://docs.microsoft.com/en-us/azure/architecture/)**: Security architecture patterns

---

## 🔗 Related Documentation

- **[Conftest Integration Guide](conftest-avm-validation.md)**: Detailed Conftest usage
- **[Azure Best Practices](azure-best-practices-tool.md)**: Best practices recommendations
- **[TFLint Integration](tflint-integration.md)**: Static analysis capabilities
- **[API Reference](api-reference.md)**: Complete tool reference