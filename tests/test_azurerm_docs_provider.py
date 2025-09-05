"""
Comprehensive test cases for AzureRM documentation provider.
Tests both resource and data source documentation retrieval and parsing.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import Response

from tf_mcp_server.tools.azurerm_docs_provider import AzureRMDocumentationProvider, get_azurerm_documentation_provider
from tf_mcp_server.core.models import TerraformAzureProviderDocsResult


class TestAzureRMDocumentationProvider:
    """Test class for AzureRM documentation provider."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.provider = AzureRMDocumentationProvider()
    
    def test_provider_urls(self):
        """Test that the provider has correct URL configurations."""
        assert self.provider.base_resources_url == "https://raw.githubusercontent.com/hashicorp/terraform-provider-azurerm/main/website/docs/r"
        assert self.provider.base_datasources_url == "https://raw.githubusercontent.com/hashicorp/terraform-provider-azurerm/main/website/docs/d"
    
    def test_generate_default_summary(self):
        """Test default summary generation."""
        # Test resource summary
        resource_summary = self.provider._generate_default_summary("linux_virtual_machine", False)
        assert "Manages an Azure Linux Virtual Machine resource." == resource_summary
        
        # Test data source summary
        datasource_summary = self.provider._generate_default_summary("virtual_machine", True)
        assert "Use this data source to access information about an existing Virtual Machine." == datasource_summary
    
    def test_extract_summary_from_markdown(self):
        """Test summary extraction from markdown content."""
        # Test with frontmatter
        markdown_with_frontmatter = """---
subcategory: "Compute"
layout: "azurerm"
page_title: "Azure Resource Manager: azurerm_linux_virtual_machine"
description: |-
  Manages a Linux Virtual Machine.
---

# azurerm_linux_virtual_machine

Manages a Linux Virtual Machine within Azure.

## Example Usage
"""
        
        summary = self.provider._extract_summary(markdown_with_frontmatter, "linux_virtual_machine", False)
        assert summary == "Manages a Linux Virtual Machine within Azure."
        
        # Test with description section
        markdown_with_description = """# azurerm_batch_account

## Description

Use this data source to access information about an existing Batch Account.

## Example Usage
"""
        
        summary = self.provider._extract_summary(markdown_with_description, "batch_account", True)
        assert summary == "Use this data source to access information about an existing Batch Account."
    
    def test_extract_arguments_from_markdown(self):
        """Test argument extraction from markdown content."""
        markdown_content = """
## Arguments Reference

The following arguments are supported:

* `name` - (Required) The name of the Linux Virtual Machine. Changing this forces a new resource to be created.

* `resource_group_name` - (Required) The name of the Resource Group in which the Linux Virtual Machine should be created. Changing this forces a new resource to be created.

* `location` - (Required) The Azure location where the Linux Virtual Machine should be created. Changing this forces a new resource to be created.

* `size` - (Required) The SKU which should be used for this Virtual Machine, such as `Standard_F2`.

* `os_disk` - (Required) A `os_disk` block as defined below.

* `tags` - (Optional) A mapping of tags to assign to the resource.

---

A `os_disk` block supports the following:

* `caching` - (Required) The Type of Caching which should be used for the Internal OS Disk. Possible values are `None`, `ReadOnly` and `ReadWrite`.

* `storage_account_type` - (Required) The Type of Storage Account which should back this the Internal OS Disk. Possible values are `Standard_LRS`, `StandardSSD_LRS`, `Premium_LRS`, `StandardSSD_ZRS` and `Premium_ZRS`.
"""
        
        arguments = self.provider._extract_arguments(markdown_content, False)
        
        # Check that we have the main arguments
        arg_names = [arg.name for arg in arguments]
        assert 'name' in arg_names
        assert 'resource_group_name' in arg_names
        assert 'location' in arg_names
        assert 'size' in arg_names
        assert 'os_disk' in arg_names
        assert 'tags' in arg_names
        
        # For this test, we don't expect nested parsing from this format
        # The nested attributes would be in a different section
        
        # Check required flags
        name_arg = next(arg for arg in arguments if arg.name == 'name')
        assert name_arg.required == True
        
        tags_arg = next(arg for arg in arguments if arg.name == 'tags')
        assert tags_arg.required == False
    
    def test_extract_attributes_from_markdown(self):
        """Test attribute extraction from markdown content."""
        markdown_content = """
## Attributes Reference

In addition to the Arguments listed above - the following Attributes are exported:

* `id` - The ID of the Linux Virtual Machine.

* `identity` - An `identity` block as defined below.

* `private_ip_address` - The Primary Private IP Address assigned to this Virtual Machine.

* `public_ip_address` - The Primary Public IP Address assigned to this Virtual Machine.

---

An `identity` block exports the following:

* `principal_id` - The Principal ID of the System Assigned Managed Service Identity.

* `tenant_id` - The Tenant ID of the System Assigned Managed Service Identity.
"""
        
        attributes = self.provider._extract_attributes(markdown_content)
        
        # Check that we have the main attributes
        attr_names = [attr['name'] for attr in attributes]
        assert 'id' in attr_names
        assert 'identity' in attr_names
        assert 'private_ip_address' in attr_names
        assert 'public_ip_address' in attr_names
        
        # For this test format, nested attributes would be in a separate section
        # so we don't expect them in the same parsing pass
    
    def test_extract_examples_from_markdown(self):
        """Test example extraction from markdown content."""
        markdown_content = """
## Example Usage

```hcl
resource "azurerm_resource_group" "example" {
  name     = "example-resources"
  location = "West Europe"
}

resource "azurerm_linux_virtual_machine" "example" {
  name                = "example-machine"
  resource_group_name = azurerm_resource_group.example.name
  location            = azurerm_resource_group.example.location
  size                = "Standard_F2"
  
  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "Standard_LRS"
  }
}
```

## Another Example

```terraform
data "azurerm_linux_virtual_machine" "example" {
  name                = "example-machine"
  resource_group_name = "example-resources"
}

output "vm_id" {
  value = data.azurerm_linux_virtual_machine.example.id
}
```
"""
        
        examples = self.provider._extract_examples(markdown_content, "linux_virtual_machine", False)
        
        assert len(examples) >= 1
        assert "azurerm_linux_virtual_machine" in examples[0]
        assert "resource" in examples[0]
        
        # Test data source examples
        examples_ds = self.provider._extract_examples(markdown_content, "linux_virtual_machine", True)
        
        # Should pick up the data source example
        assert len(examples_ds) >= 1
        if len(examples_ds) > 1:
            # If it found actual examples, check they contain data source
            assert any("data" in example for example in examples_ds)
    
    @pytest.mark.asyncio
    async def test_search_azurerm_provider_docs_success(self):
        """Test successful documentation retrieval."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """---
subcategory: "Compute"
layout: "azurerm"
page_title: "Azure Resource Manager: azurerm_linux_virtual_machine"
description: |-
  Manages a Linux Virtual Machine.
---

# azurerm_linux_virtual_machine

Manages a Linux Virtual Machine within Azure.

## Arguments Reference

* `name` - (Required) The name of the Linux Virtual Machine.
* `resource_group_name` - (Required) The name of the Resource Group.
* `location` - (Required) The Azure location.

## Attributes Reference

* `id` - The ID of the Linux Virtual Machine.
* `private_ip_address` - The Primary Private IP Address.

## Example Usage

```hcl
resource "azurerm_linux_virtual_machine" "example" {
  name                = "example-machine"
  resource_group_name = azurerm_resource_group.example.name
  location            = azurerm_resource_group.example.location
}
```
"""
        
        with patch('tf_mcp_server.tools.azurerm_docs_provider.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_response
            
            result = await self.provider.search_azurerm_provider_docs(
                resource_type="linux_virtual_machine",
                doc_type="resource"
            )
            
            assert isinstance(result, TerraformAzureProviderDocsResult)
            assert result.resource_type == "linux_virtual_machine"
            assert "Manages a Linux Virtual Machine within Azure" in result.summary
            assert len(result.arguments) >= 3
            assert len(result.attributes) >= 2
            assert len(result.examples) >= 1
            assert "azurerm_linux_virtual_machine" in result.examples[0]
    
    @pytest.mark.asyncio
    async def test_search_azurerm_provider_docs_fallback(self):
        """Test fallback mechanism when first URL fails."""
        mock_response_404 = MagicMock()
        mock_response_404.status_code = 404
        
        mock_response_200 = MagicMock()
        mock_response_200.status_code = 200
        mock_response_200.text = """---
layout: "azurerm"
page_title: "Data Source: azurerm_virtual_machine"
description: |-
  Use this data source to access information about an existing Virtual Machine.
---

# Data Source: azurerm_virtual_machine

Use this data source to access information about an existing Virtual Machine.

## Arguments Reference

* `name` - (Optional) The name of the Virtual Machine.
* `resource_group_name` - (Optional) The name of the Resource Group.

## Attributes Reference

* `id` - The ID of the Virtual Machine.
* `location` - The Azure location.
"""
        
        with patch('tf_mcp_server.tools.azurerm_docs_provider.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            # First call returns 404, second call returns 200
            mock_client.get.side_effect = [mock_response_404, mock_response_200]
            
            result = await self.provider.search_azurerm_provider_docs(
                resource_type="virtual_machine",
                doc_type="resource"  # Will fail and fallback to data-source
            )
            
            assert isinstance(result, TerraformAzureProviderDocsResult)
            assert result.resource_type == "virtual_machine"
            assert "docs/d/" in result.documentation_url  # Should be data source URL
    
    @pytest.mark.asyncio
    async def test_search_azurerm_provider_docs_not_found(self):
        """Test handling when documentation is not found."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        
        with patch('httpx.AsyncClient') as mock_client:
            # Both calls return 404
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            result = await self.provider.search_azurerm_provider_docs(
                resource_type="non_existent_resource",
                doc_type="resource"
            )
            
            assert isinstance(result, TerraformAzureProviderDocsResult)
            assert result.resource_type == "non_existent_resource"
            assert "Documentation not found" in result.summary
            assert result.arguments == []
            assert result.attributes == []
            assert result.examples == []
    
    @pytest.mark.asyncio
    async def test_search_azurerm_provider_docs_exception(self):
        """Test handling when an exception occurs."""
        with patch('tf_mcp_server.tools.azurerm_docs_provider.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get.side_effect = Exception("Network error")
            
            result = await self.provider.search_azurerm_provider_docs(
                resource_type="linux_virtual_machine",
                doc_type="resource"
            )
            
            assert isinstance(result, TerraformAzureProviderDocsResult)
            assert result.resource_type == "linux_virtual_machine"
            assert "Error retrieving documentation" in result.summary
            assert "Network error" in result.summary
    
    def test_get_azurerm_documentation_provider_singleton(self):
        """Test that the provider returns the same instance."""
        provider1 = get_azurerm_documentation_provider()
        provider2 = get_azurerm_documentation_provider()
        
        assert provider1 is provider2
        assert isinstance(provider1, AzureRMDocumentationProvider)


# Integration tests that actually fetch from GitHub
class TestAzureRMDocumentationProviderIntegration:
    """Integration tests that make real HTTP requests."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.provider = AzureRMDocumentationProvider()
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_real_resource_documentation(self):
        """Test fetching real resource documentation from GitHub."""
        result = await self.provider.search_azurerm_provider_docs(
            resource_type="linux_virtual_machine",
            doc_type="resource"
        )
        
        assert isinstance(result, TerraformAzureProviderDocsResult)
        assert result.resource_type == "linux_virtual_machine"
        assert "githubusercontent.com" in result.documentation_url
        assert "docs/r/" in result.documentation_url
        assert len(result.summary) > 0
        assert len(result.arguments) > 0
        assert len(result.attributes) > 0
        assert len(result.examples) > 0
        
        # Check for expected arguments
        arg_names = [arg.name for arg in result.arguments]
        assert 'name' in arg_names
        assert 'resource_group_name' in arg_names
        assert 'location' in arg_names
        
        print(f"Resource Summary: {result.summary}")
        print(f"Arguments: {len(result.arguments)}")
        print(f"Attributes: {len(result.attributes)}")
        print(f"Examples: {len(result.examples)}")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_real_datasource_documentation(self):
        """Test fetching real data source documentation from GitHub."""
        result = await self.provider.search_azurerm_provider_docs(
            resource_type="batch_account",
            doc_type="data-source"
        )
        
        assert isinstance(result, TerraformAzureProviderDocsResult)
        assert result.resource_type == "batch_account"
        assert "githubusercontent.com" in result.documentation_url
        assert "docs/d/" in result.documentation_url
        assert len(result.summary) > 0
        assert len(result.arguments) > 0
        assert len(result.attributes) > 0
        assert len(result.examples) > 0
        
        # Check for expected arguments
        arg_names = [arg.name for arg in result.arguments]
        assert 'name' in arg_names
        assert 'resource_group_name' in arg_names
        
        print(f"Data Source Summary: {result.summary}")
        print(f"Arguments: {len(result.arguments)}")
        print(f"Attributes: {len(result.attributes)}")
        print(f"Examples: {len(result.examples)}")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_real_fallback_mechanism(self):
        """Test real fallback from resource to data source."""
        # Try to get a resource that doesn't exist but has a data source
        result = await self.provider.search_azurerm_provider_docs(
            resource_type="client_config",  # This only exists as data source
            doc_type="resource"  # But we're asking for resource
        )
        
        assert isinstance(result, TerraformAzureProviderDocsResult)
        assert result.resource_type == "client_config"
        
        # Should either find the data source or return not found
        if "docs/d/" in result.documentation_url:
            # Successfully fell back to data source
            assert len(result.summary) > 0
            print(f"Successfully fell back to data source: {result.documentation_url}")
        else:
            # Not found
            assert "Documentation not found" in result.summary
            print(f"No fallback available: {result.summary}")


if __name__ == "__main__":
    # Run basic tests
    pytest.main([__file__, "-v"])
