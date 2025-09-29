"""
Integration tests for Golang Source Code Analysis Tools.
These tests validate the end-to-end functionality of the integrated tools by testing provider methods directly.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
import json

from src.tf_mcp_server.tools.golang_source_provider import get_golang_source_provider


class TestGolangSourceToolsIntegration:
    """Integration tests for Golang Source Code Analysis Tools."""

    @pytest.fixture
    def provider(self):
        """Create golang source provider instance for testing."""
        return get_golang_source_provider()

    @pytest.fixture
    def mock_github_tags(self):
        """Mock GitHub tags response."""
        return [
            {"name": "v4.25.0"},
            {"name": "v4.24.0"},
            {"name": "v4.23.0"}
        ]

    @pytest.fixture
    def mock_golang_source(self):
        """Mock golang source code."""
        return """package clients

import (
    "context"
    "github.com/hashicorp/terraform-provider-azurerm/internal/common"
)

// Client represents the Azure client configuration
type Client struct {
    Account     *ResourceManagerAccount
    StopContext context.Context
    Features    *common.ClientFeatures
}

// NewClient creates a new client instance
func NewClient(ctx context.Context) (*Client, error) {
    return &Client{
        StopContext: ctx,
    }, nil
}"""

    @pytest.fixture
    def mock_terraform_index(self):
        """Mock terraform resource index."""
        return {
            "create_index": "services/resource/resource_group_create.go",
            "read_index": "services/resource/resource_group_read.go",
            "schema_index": "services/resource/resource_group_schema.go",
            "namespace": "github.com/hashicorp/terraform-provider-azurerm/internal/services/resource"
        }

    @pytest.fixture
    def mock_terraform_source(self):
        """Mock terraform source code."""
        return """func resourceResourceGroupCreateUpdate(d *pluginsdk.ResourceData, meta interface{}) error {
    client := meta.(*clients.Client).Resource.GroupsClient
    subscriptionId := meta.(*clients.Client).Account.SubscriptionId
    ctx, cancel := timeouts.ForCreateUpdate(meta.(*clients.Client).StopContext, d)
    defer cancel()

    name := d.Get("name").(string)
    location := azure.NormalizeLocation(d.Get("location").(string))
    
    properties := resources.ResourceGroup{
        Name:     &name,
        Location: &location,
    }

    if _, err := client.CreateOrUpdate(ctx, name, properties); err != nil {
        return fmt.Errorf("creating Resource Group %q: %+v", name, err)
    }

    return resourceResourceGroupRead(d, meta)
}"""

    def test_golang_source_code_server_get_supported_golang_namespaces_integration(self, provider):
        """Test golang_source_code_server_get_supported_golang_namespaces provider method."""
        result = provider.get_supported_namespaces()
        
        assert result is not None
        assert isinstance(result, list)
        assert "github.com/hashicorp/terraform-provider-azurerm/internal" in result
        assert "github.com/Azure/terraform-provider-azapi/internal" in result

    @pytest.mark.asyncio
    async def test_golang_source_code_server_get_supported_tags_integration(self, provider, mock_github_tags):
        """Test golang_source_code_server_get_supported_tags provider method."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = mock_github_tags
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            result = await provider.get_supported_tags(
                namespace="github.com/hashicorp/terraform-provider-azurerm/internal"
            )
            
            assert result is not None
            assert isinstance(result, list)
            assert "v4.25.0" in result
            assert "v4.24.0" in result

    @pytest.mark.asyncio
    async def test_query_golang_source_code_type_integration(self, provider, mock_golang_source):
        """Test query_golang_source_code provider method for type."""
        with patch('src.tf_mcp_server.tools.golang_source_provider.GolangSourceProvider._read_github_content',
                   return_value=mock_golang_source):
            
            result = await provider.query_golang_source_code(
                namespace="github.com/hashicorp/terraform-provider-azurerm/internal/clients",
                symbol="type",
                name="Client"
            )
            
            assert result is not None
            assert "type Client struct" in result
            assert "ResourceManagerAccount" in result
            assert "StopContext" in result

    @pytest.mark.asyncio
    async def test_query_terraform_block_implementation_source_code_integration(self, provider, mock_terraform_index, mock_terraform_source):
        """Test query_terraform_block_implementation_source_code provider method."""
        with patch('src.tf_mcp_server.tools.golang_source_provider.GolangSourceProvider._read_github_content') as mock_read:
            # First call returns index JSON, second call returns source code
            mock_read.side_effect = [
                json.dumps(mock_terraform_index),
                mock_terraform_source
            ]
            
            result = await provider.query_terraform_source_code(
                block_type="resource",
                terraform_type="azurerm_resource_group",
                entrypoint_name="create"
            )
            
            assert result is not None
            assert "resourceResourceGroupCreateUpdate" in result
            assert "GroupsClient" in result
            assert "CreateOrUpdate" in result

    @pytest.mark.asyncio
    async def test_provider_error_handling_integration(self, provider):
        """Test error handling in provider methods."""
        # Test invalid symbol type
        try:
            result = await provider.query_golang_source_code(
                namespace="github.com/hashicorp/terraform-provider-azurerm/internal/clients",
                symbol="invalid",
                name="Test"
            )
            assert False, "Should have raised an exception"
        except Exception as e:
            assert "Invalid symbol type" in str(e)

        # Test invalid terraform block type  
        try:
            result = await provider.query_terraform_source_code(
                block_type="invalid",
                terraform_type="azurerm_resource_group",
                entrypoint_name="create"
            )
            assert False, "Should have raised an exception"
        except Exception as e:
            assert "Invalid block type" in str(e)

    @pytest.mark.asyncio
    async def test_provider_authentication_error_handling_integration(self, provider):
        """Test authentication error handling in provider methods."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 401
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            # Test GitHub authentication error 
            result = await provider.get_supported_tags(
                namespace="github.com/hashicorp/terraform-provider-azurerm/internal"
            )
            
            assert result is not None
            # Should fallback to ["latest"] on auth error
            assert result == ["latest"]