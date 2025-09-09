"""
Tests for the core utilities module.
"""
import sys
from pathlib import Path

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tf_mcp_server.core.utils import (
    extract_hcl_from_markdown,
    normalize_resource_type,
    validate_azure_name,
    format_terraform_block
)


def test_extract_hcl_from_markdown():
    """Test HCL extraction from markdown."""
    markdown_content = """
# Some documentation

```hcl
resource "azurerm_storage_account" "example" {
  name = "test"
}
```

Some more text

```terraform
resource "azurerm_key_vault" "example" {
  name = "test-kv"
}
```
"""
    
    extracted = extract_hcl_from_markdown(markdown_content)
    assert 'resource "azurerm_storage_account"' in extracted
    assert 'resource "azurerm_key_vault"' in extracted
    assert "# Some documentation" not in extracted


def test_normalize_resource_type():
    """Test resource type normalization."""
    assert normalize_resource_type("azurerm_storage_account") == "storage-account"
    assert normalize_resource_type("storage_account") == "storage-account"
    assert normalize_resource_type("STORAGE_ACCOUNT") == "storage-account"


def test_validate_azure_name():
    """Test Azure resource name validation."""
    # Valid names
    assert validate_azure_name("valid-name", "resource_group") == []
    assert validate_azure_name("valid123", "resource_group") == []
    
    # Invalid names
    errors = validate_azure_name("", "resource_group")
    assert len(errors) > 0
    assert "cannot be empty" in errors[0]
    
    errors = validate_azure_name("invalid@name", "resource_group")
    assert len(errors) > 0
    assert "can only contain" in errors[0]
    
    # Storage account specific validation
    errors = validate_azure_name("UPPERCASE", "storage_account")
    assert len(errors) > 0
    assert "lowercase" in errors[0]


def test_format_terraform_block():
    """Test Terraform block formatting."""
    attributes = {
        "name": "test-resource",
        "location": "East US",
        "enabled": True,
        "count": 3,
        "tags": {"Environment": "Test"}
    }
    
    result = format_terraform_block("azurerm_test", "example", attributes)
    
    assert 'resource "azurerm_test" "example"' in result
    assert 'name = "test-resource"' in result
    assert 'enabled = true' in result
    assert 'count = 3' in result
    assert 'Environment = "Test"' in result
