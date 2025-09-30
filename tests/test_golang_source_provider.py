"""
Test cases for Golang Source Code Analysis Tools.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import json
import base64
import httpx
import os
import tempfile
import shutil
from pathlib import Path

from tf_mcp_server.tools.golang_source_provider import get_golang_source_provider, GolangSourceProvider


class TestGolangSourceProvider:
    """Test cases for Golang Source Provider."""

    @pytest.fixture
    def temp_cache_dir(self):
        """Create a temporary cache directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def golang_provider_with_temp_cache(self, temp_cache_dir):
        """Get golang source provider instance with temporary cache."""
        provider = GolangSourceProvider()
        provider.cache_dir = temp_cache_dir
        provider._ensure_cache_dir()
        return provider

    @pytest.fixture
    def golang_provider(self):
        """Get golang source provider instance."""
        return get_golang_source_provider()

    @pytest.fixture
    def sample_github_tags_response(self):
        """Sample GitHub tags API response."""
        return [
            {"name": "v4.25.0", "commit": {"sha": "abc123"}},
            {"name": "v4.24.0", "commit": {"sha": "def456"}},
            {"name": "v4.23.0", "commit": {"sha": "ghi789"}}
        ]

    @pytest.fixture
    def sample_golang_source_code(self):
        """Sample golang source code."""
        return """// Package clients provides Azure client configurations
package clients

import (
    "context"
    "fmt"
)

// Client represents the Azure client configuration
type Client struct {
    // Account contains the subscription and tenant information
    Account *ResourceManagerAccount
    
    // StopContext is used for graceful shutdown
    StopContext context.Context
    
    // Features contains feature flags
    Features *Features
}

// NewClient creates a new Azure client configuration
func NewClient(ctx context.Context, options *ClientOptions) (*Client, error) {
    client := &Client{
        StopContext: ctx,
    }
    
    // Initialize account information
    account, err := buildAccount(options)
    if err != nil {
        return nil, fmt.Errorf("building account: %w", err)
    }
    
    client.Account = account
    
    return client, nil
}"""

    @pytest.fixture
    def sample_terraform_index_json(self):
        """Sample terraform resource index JSON."""
        return {
            "create_index": "services/resource/resource_group_create.go",
            "read_index": "services/resource/resource_group_read.go", 
            "update_index": "services/resource/resource_group_update.go",
            "delete_index": "services/resource/resource_group_delete.go",
            "schema_index": "services/resource/resource_group_schema.go",
            "attribute_index": "services/resource/resource_group_attribute.go",
            "namespace": "github.com/hashicorp/terraform-provider-azurerm/internal/services/resource"
        }

    @pytest.fixture
    def sample_terraform_source_code(self):
        """Sample terraform resource source code."""
        return """package resource

import (
    "context"
    "fmt"
    "time"

    "github.com/hashicorp/terraform-plugin-sdk/v2/diag"
    "github.com/hashicorp/terraform-plugin-sdk/v2/helper/schema"
    "github.com/hashicorp/terraform-provider-azurerm/internal/clients"
    "github.com/hashicorp/terraform-provider-azurerm/internal/tf/pluginsdk"
)

func resourceResourceGroupCreateUpdate(d *pluginsdk.ResourceData, meta interface{}) error {
    client := meta.(*clients.Client).Resource.GroupsClient
    subscriptionId := meta.(*clients.Client).Account.SubscriptionId
    ctx, cancel := timeouts.ForCreateUpdate(meta.(*clients.Client).StopContext, d)
    defer cancel()

    name := d.Get("name").(string)
    location := azure.NormalizeLocation(d.Get("location").(string))
    
    log.Printf("[INFO] preparing arguments for Azure ARM Resource Group creation")

    properties := resources.ResourceGroup{
        Name:     &name,
        Location: &location,
    }

    if v, ok := d.GetOk("tags"); ok {
        properties.Tags = tags.Expand(v.(map[string]interface{}))
    }

    if _, err := client.CreateOrUpdate(ctx, name, properties); err != nil {
        return fmt.Errorf("creating Resource Group %q: %+v", name, err)
    }

    d.SetId(subscriptionId + "/resourceGroups/" + name)

    return resourceResourceGroupRead(d, meta)
}"""

    def test_get_supported_namespaces(self, golang_provider):
        """Test getting supported golang namespaces."""
        namespaces = golang_provider.get_supported_namespaces()
        
        assert isinstance(namespaces, list)
        assert len(namespaces) > 0
        assert "github.com/hashicorp/terraform-provider-azurerm/internal" in namespaces
        assert "github.com/Azure/terraform-provider-azapi/internal" in namespaces

    def test_get_supported_providers(self, golang_provider):
        """Test getting supported providers."""
        providers = golang_provider.get_supported_providers()
        
        assert isinstance(providers, list)
        assert "azurerm" in providers
        assert "azapi" in providers

    def test_cache_methods(self, golang_provider_with_temp_cache):
        """Test cache-related methods."""
        provider = golang_provider_with_temp_cache
        
        # Test cache info for empty cache
        cache_info = provider.get_cache_info()
        assert cache_info["exists"]
        assert cache_info["entries"] == 0
        assert cache_info["size_mb"] == 0
        
        # Test clear cache
        provider.clear_cache()
        assert provider.cache_dir.exists()
        
        # Test specific cache clearing
        provider.clear_cache(owner="test-owner")
        provider.clear_cache(owner="test-owner", repo="test-repo")
        provider.clear_cache(owner="test-owner", repo="test-repo", tag="v1.0.0")

    @pytest.mark.asyncio
    async def test_get_supported_tags_success(self, golang_provider, sample_github_tags_response):
        """Test getting supported tags successfully."""
        namespace = "github.com/hashicorp/terraform-provider-azurerm/internal"
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = sample_github_tags_response
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            tags = await golang_provider.get_supported_tags(namespace)
            
            assert isinstance(tags, list)
            assert "v4.25.0" in tags
            assert "v4.24.0" in tags
            assert "v4.23.0" in tags

    @pytest.mark.asyncio
    async def test_get_supported_tags_with_auth_fallback(self, golang_provider_with_temp_cache):
        """Test getting supported tags with auth fallback mechanism."""
        provider = golang_provider_with_temp_cache
        namespace = "github.com/hashicorp/terraform-provider-azurerm/internal"
        
        with patch.dict('os.environ', {'GITHUB_TOKEN': 'test-token'}):
            with patch('httpx.AsyncClient') as mock_client:
                # Mock first response (no auth) as 401, second response (with auth) as success
                mock_response_401 = Mock()
                mock_response_401.status_code = 401
                
                mock_response_success = Mock()
                mock_response_success.status_code = 200
                mock_response_success.raise_for_status.return_value = None
                mock_response_success.json.return_value = [
                    {"name": "v4.25.0", "commit": {"sha": "abc123"}},
                    {"name": "v4.24.0", "commit": {"sha": "def456"}}
                ]
                
                mock_client_instance = mock_client.return_value.__aenter__.return_value
                mock_client_instance.get.side_effect = [mock_response_401, mock_response_success]
                
                tags = await provider.get_supported_tags(namespace)
                
                # Verify two calls were made (retry mechanism worked)
                assert mock_client_instance.get.call_count == 2
                
                # Verify successful result
                assert isinstance(tags, list)
                assert "v4.25.0" in tags

    @pytest.mark.asyncio
    async def test_get_supported_tags_unsupported_namespace(self, golang_provider):
        """Test getting supported tags for unsupported namespace."""
        with pytest.raises(ValueError, match="Unsupported namespace"):
            await golang_provider.get_supported_tags("invalid/namespace")

    @pytest.mark.asyncio
    async def test_get_supported_tags_api_error(self, golang_provider_with_temp_cache):
        """Test getting supported tags when API returns error."""
        provider = golang_provider_with_temp_cache
        namespace = "github.com/hashicorp/terraform-provider-azurerm/internal"
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "401 Unauthorized", request=Mock(), response=Mock()
            )
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            tags = await provider.get_supported_tags(namespace)
            
            # Should return fallback
            assert tags == ["latest"]

    @pytest.mark.asyncio
    async def test_query_golang_source_code_type(self, golang_provider, sample_golang_source_code):
        """Test querying golang source code for type."""
        namespace = "github.com/hashicorp/terraform-provider-azurerm/internal/clients"
        
        with patch.object(golang_provider, '_read_github_content', return_value=sample_golang_source_code):
            result = await golang_provider.query_golang_source_code(
                namespace=namespace,
                symbol="type",
                name="Client"
            )
            
            assert "type Client struct" in result
            assert "Account *ResourceManagerAccount" in result
            assert "StopContext context.Context" in result

    @pytest.mark.asyncio
    async def test_query_golang_source_code_function(self, golang_provider, sample_golang_source_code):
        """Test querying golang source code for function."""
        namespace = "github.com/hashicorp/terraform-provider-azurerm/internal/clients"
        
        with patch.object(golang_provider, '_read_github_content', return_value=sample_golang_source_code):
            result = await golang_provider.query_golang_source_code(
                namespace=namespace,
                symbol="func",
                name="NewClient"
            )
            
            assert "func NewClient" in result
            assert "ClientOptions" in result
            assert "buildAccount" in result

    @pytest.mark.asyncio
    async def test_query_golang_source_code_method(self, golang_provider):
        """Test querying golang source code for method."""
        namespace = "github.com/hashicorp/terraform-provider-azurerm/internal/services/resource"
        method_code = """func (r ResourceGroupResource) Create(ctx context.Context, req resource.CreateRequest, resp *resource.CreateResponse) {
    var data ResourceGroupResourceModel
    resp.Diagnostics.Append(req.Plan.Get(ctx, &data)...)
    
    client := r.client.Resource.GroupsClient
    
    // Implementation details...
}"""
        
        with patch.object(golang_provider, '_read_github_content', return_value=method_code):
            result = await golang_provider.query_golang_source_code(
                namespace=namespace,
                symbol="method",
                name="Create",
                receiver="ResourceGroupResource"
            )
            
            assert "func (r ResourceGroupResource) Create" in result
            assert "CreateRequest" in result
            assert "CreateResponse" in result

    @pytest.mark.asyncio
    async def test_query_golang_source_code_invalid_symbol(self, golang_provider):
        """Test querying golang source code with invalid symbol."""
        namespace = "github.com/hashicorp/terraform-provider-azurerm/internal/clients"
        
        with pytest.raises(ValueError, match="Invalid symbol type"):
            await golang_provider.query_golang_source_code(
                namespace=namespace,
                symbol="invalid",
                name="Test"
            )

    @pytest.mark.asyncio
    async def test_query_golang_source_code_method_without_receiver(self, golang_provider):
        """Test querying golang source code for method without receiver."""
        namespace = "github.com/hashicorp/terraform-provider-azurerm/internal/clients"
        
        with pytest.raises(ValueError, match="Receiver is required for method symbols"):
            await golang_provider.query_golang_source_code(
                namespace=namespace,
                symbol="method",
                name="Create"
            )

    @pytest.mark.asyncio
    async def test_query_golang_source_code_unsupported_namespace(self, golang_provider):
        """Test querying golang source code with unsupported namespace."""
        result = await golang_provider.query_golang_source_code(
            namespace="unsupported/namespace",
            symbol="type",
            name="Test"
        )
        
        assert "Error: Namespace 'unsupported/namespace' is not supported" in result

    @pytest.mark.asyncio
    async def test_query_terraform_source_code_resource_create(self, golang_provider, sample_terraform_index_json, sample_terraform_source_code):
        """Test querying terraform source code for resource create."""
        with patch.object(golang_provider, '_read_github_content') as mock_read:
            # First call returns index JSON, second call returns source code
            mock_read.side_effect = [
                json.dumps(sample_terraform_index_json),
                sample_terraform_source_code
            ]
            
            result = await golang_provider.query_terraform_source_code(
                block_type="resource",
                terraform_type="azurerm_resource_group",
                entrypoint_name="create"
            )
            
            assert "resourceResourceGroupCreateUpdate" in result
            assert "GroupsClient" in result
            assert "CreateOrUpdate" in result
            assert len(mock_read.call_args_list) == 2

    @pytest.mark.asyncio
    async def test_query_terraform_source_code_resource_attribute(self, golang_provider):
        """Test querying terraform source code for resource attribute."""
        attribute_index = {
            "create_index": "services/resource/resource_group_create.go",
            "read_index": "services/resource/resource_group_read.go",
            "update_index": "services/resource/resource_group_update.go", 
            "delete_index": "services/resource/resource_group_delete.go",
            "schema_index": "services/resource/resource_group_schema.go",
            "attribute_index": "services/resource/resource_group_attribute.go",
            "namespace": "github.com/hashicorp/terraform-provider-azurerm/internal/services/resource"
        }
        
        attribute_code = """func resourceGroupAttributeSchema() map[string]*schema.Schema {
    return map[string]*schema.Schema{
        "name": {
            Type:     schema.TypeString,
            Required: true,
            ForceNew: true,
        },
        "location": {
            Type:     schema.TypeString,
            Required: true,
            ForceNew: true,
        },
    }
}"""
        
        with patch.object(golang_provider, '_read_github_content') as mock_read:
            mock_read.side_effect = [
                json.dumps(attribute_index),
                attribute_code
            ]
            
            result = await golang_provider.query_terraform_source_code(
                block_type="resource",
                terraform_type="azurerm_resource_group",
                entrypoint_name="attribute"
            )
            
            assert "resourceGroupAttributeSchema" in result
            assert "schema.Schema" in result

    @pytest.mark.asyncio
    async def test_query_terraform_source_code_data_source(self, golang_provider):
        """Test querying terraform source code for data source."""
        data_index = {
            "read_index": "services/resource/data_source_resource_group.go",
            "schema_index": "services/resource/data_source_resource_group_schema.go",
            "attribute_index": "services/resource/data_source_resource_group_attribute.go",
            "namespace": "github.com/hashicorp/terraform-provider-azurerm/internal/services/resource"
        }
        
        data_source_code = """func dataSourceResourceGroupRead(d *schema.ResourceData, meta interface{}) error {
    client := meta.(*clients.Client).Resource.GroupsClient
    ctx, cancel := timeouts.ForRead(meta.(*clients.Client).StopContext, d)
    defer cancel()

    name := d.Get("name").(string)
    
    resp, err := client.Get(ctx, name)
    if err != nil {
        return fmt.Errorf("retrieving Resource Group %q: %+v", name, err)
    }
    
    return nil
}"""
        
        with patch.object(golang_provider, '_read_github_content') as mock_read:
            mock_read.side_effect = [
                json.dumps(data_index),
                data_source_code
            ]
            
            result = await golang_provider.query_terraform_source_code(
                block_type="data",
                terraform_type="azurerm_resource_group",
                entrypoint_name="read"
            )
            
            assert "dataSourceResourceGroupRead" in result
            assert "GroupsClient" in result

    @pytest.mark.asyncio
    async def test_query_terraform_source_code_invalid_block_type(self, golang_provider):
        """Test querying terraform source code with invalid block type."""
        with pytest.raises(ValueError, match="Invalid block type"):
            await golang_provider.query_terraform_source_code(
                block_type="invalid",
                terraform_type="azurerm_resource_group",
                entrypoint_name="create"
            )

    @pytest.mark.asyncio
    async def test_query_terraform_source_code_invalid_entrypoint(self, golang_provider):
        """Test querying terraform source code with invalid entrypoint."""
        with pytest.raises(ValueError, match="Invalid entrypoint 'invalid' for block type 'resource'"):
            await golang_provider.query_terraform_source_code(
                block_type="resource",
                terraform_type="azurerm_resource_group",
                entrypoint_name="invalid"
            )

    @pytest.mark.asyncio
    async def test_query_terraform_source_code_invalid_terraform_type(self, golang_provider):
        """Test querying terraform source code with invalid terraform type."""
        with pytest.raises(ValueError, match="Invalid terraform type: invalid, valid terraform type should be like 'azurerm_resource_group'"):
            await golang_provider.query_terraform_source_code(
                block_type="resource",
                terraform_type="invalid",  # Only one segment, should trigger validation error
                entrypoint_name="create"
            )

    @pytest.mark.asyncio
    async def test_query_terraform_source_code_data_invalid_entrypoint(self, golang_provider):
        """Test querying terraform source code for data source with invalid entrypoint."""
        with pytest.raises(ValueError, match="Invalid entrypoint 'create' for block type 'data'"):
            await golang_provider.query_terraform_source_code(
                block_type="data",
                terraform_type="azurerm_resource_group",
                entrypoint_name="create"  # create is not valid for data sources
            )

    @pytest.mark.asyncio
    async def test_query_terraform_source_code_ephemeral_valid_entrypoints(self, golang_provider):
        """Test querying terraform source code for ephemeral resource with valid entrypoints."""
        # Test all valid ephemeral entrypoints
        valid_entrypoints = ["open", "close", "renew", "schema"]
        
        for entrypoint in valid_entrypoints:
            # This should not raise a ValueError for validation
            # It may fail later with a "not supported" error which is fine
            result = await golang_provider.query_terraform_source_code(
                block_type="ephemeral",
                terraform_type="azurerm_key_vault_secret",
                entrypoint_name=entrypoint
            )
            assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_query_terraform_source_code_ephemeral_invalid_entrypoint(self, golang_provider):
        """Test querying terraform source code for ephemeral resource with invalid entrypoint."""
        with pytest.raises(ValueError, match="Invalid entrypoint 'create' for block type 'ephemeral'"):
            await golang_provider.query_terraform_source_code(
                block_type="ephemeral",
                terraform_type="azurerm_key_vault_secret",
                entrypoint_name="create"  # create is not valid for ephemeral
            )

    @pytest.mark.asyncio
    async def test_query_terraform_source_code_unsupported_provider(self, golang_provider):
        """Test querying terraform source code with unsupported provider."""
        result = await golang_provider.query_terraform_source_code(
            block_type="resource",
            terraform_type="aws_instance",
            entrypoint_name="create"
        )
        
        assert "Error: Provider 'aws' is not supported" in result

    @pytest.mark.asyncio
    async def test_read_github_content_success_no_auth(self, golang_provider_with_temp_cache):
        """Test reading GitHub content successfully without authentication."""
        provider = golang_provider_with_temp_cache
        sample_content = "package main\n\nfunc main() {}\n"
        encoded_content = base64.b64encode(sample_content.encode()).decode()
        
        github_response = {
            "content": encoded_content,
            "encoding": "base64"
        }
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = github_response
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            result = await provider._read_github_content(
                owner="lonegunmanb",
                repo="terraform-provider-azurerm-index",
                path="index/internal/clients/type.Client.goindex",
                tag="v4.25.0"
            )
            
            # Verify the call was made and result is correct
            assert mock_client.return_value.__aenter__.return_value.get.called
            assert result == sample_content

    @pytest.mark.asyncio
    async def test_read_github_content_auth_fallback(self, golang_provider_with_temp_cache):
        """Test reading GitHub content with auth fallback mechanism."""
        provider = golang_provider_with_temp_cache
        sample_content = "package main\n\nfunc main() {}\n"
        encoded_content = base64.b64encode(sample_content.encode()).decode()
        
        github_response = {
            "content": encoded_content,
            "encoding": "base64"
        }
        
        with patch.dict('os.environ', {'GITHUB_TOKEN': 'test-token'}):
            with patch('httpx.AsyncClient') as mock_client:
                # First response: 401 unauthorized
                mock_response_401 = Mock()
                mock_response_401.status_code = 401
                
                # Second response: 200 success with auth
                mock_response_success = Mock()
                mock_response_success.status_code = 200
                mock_response_success.raise_for_status.return_value = None
                mock_response_success.json.return_value = github_response
                
                mock_client_instance = mock_client.return_value.__aenter__.return_value
                mock_client_instance.get.side_effect = [mock_response_401, mock_response_success]
                
                result = await provider._read_github_content(
                    owner="lonegunmanb",
                    repo="terraform-provider-azurerm-index",
                    path="index/internal/clients/type.Client.goindex",
                    tag="v4.25.0"
                )
                
                # Verify two calls were made (retry mechanism worked)
                assert mock_client_instance.get.call_count == 2
                
                # Verify successful result
                assert result == sample_content

    @pytest.mark.asyncio
    async def test_read_github_content_404_error(self, golang_provider):
        """Test reading GitHub content with 404 error."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            with pytest.raises(Exception, match="source code not found \\(404\\)"):
                await golang_provider._read_github_content(
                    owner="lonegunmanb",
                    repo="terraform-provider-azurerm-index",
                    path="nonexistent/path",
                    tag=None
                )

    @pytest.mark.asyncio
    async def test_read_github_content_401_without_token(self, golang_provider):
        """Test reading GitHub content with 401 error and no token available."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 401
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            with pytest.raises(Exception, match="GitHub API access denied.*requires authentication.*GITHUB_TOKEN"):
                await golang_provider._read_github_content(
                    owner="lonegunmanb",
                    repo="terraform-provider-azurerm-index",
                    path="some/path",
                    tag=None
                )

    @pytest.mark.asyncio 
    async def test_read_github_content_401_persistent_with_token(self, golang_provider):
        """Test reading GitHub content with persistent 401 error even with token."""
        with patch.dict('os.environ', {'GITHUB_TOKEN': 'invalid-token'}):
            with patch('httpx.AsyncClient') as mock_client:
                # Both calls return 401
                mock_response = Mock()
                mock_response.status_code = 401
                mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
                
                with pytest.raises(Exception, match="GitHub API authentication failed"):
                    await golang_provider._read_github_content(
                        owner="lonegunmanb",
                        repo="terraform-provider-azurerm-index",
                        path="some/path",
                        tag=None
                    )
                
                # Verify retry occurred
                assert mock_client.return_value.__aenter__.return_value.get.call_count == 2

    @pytest.mark.asyncio
    async def test_fetch_golang_source_code_with_tag(self, golang_provider, sample_golang_source_code):
        """Test fetching golang source code with specific tag."""
        namespace = "github.com/hashicorp/terraform-provider-azurerm/internal/clients"
        
        with patch.object(golang_provider, '_read_github_content', return_value=sample_golang_source_code) as mock_read:
            result = await golang_provider.query_golang_source_code(
                namespace=namespace,
                symbol="type",
                name="Client",
                tag="v4.25.0"
            )
            
            assert "type Client struct" in result
            # Verify the path construction is correct
            call_args = mock_read.call_args
            assert call_args[0][0] == "lonegunmanb"  # owner
            assert call_args[0][1] == "terraform-provider-azurerm-index"  # repo
            assert call_args[0][2] == "index/internal/clients/type.Client.goindex"  # path
            assert call_args[0][3] == "v4.25.0"  # tag

    @pytest.mark.asyncio
    async def test_fetch_golang_source_code_method_with_receiver(self, golang_provider):
        """Test fetching golang source code for method with receiver."""
        namespace = "github.com/hashicorp/terraform-provider-azurerm/internal/services/resource"
        method_code = """func (r ResourceGroupResource) Create(ctx context.Context, req resource.CreateRequest, resp *resource.CreateResponse) {
    var data ResourceGroupResourceModel
    resp.Diagnostics.Append(req.Plan.Get(ctx, &data)...)
    
    client := r.client.Resource.GroupsClient
    
    // Implementation details...
}"""
        
        with patch.object(golang_provider, '_read_github_content', return_value=method_code) as mock_read:
            result = await golang_provider.query_golang_source_code(
                namespace=namespace,
                symbol="method",
                name="Create",
                receiver="ResourceGroupResource"
            )
            
            assert "func (r ResourceGroupResource) Create" in result
            # Verify the path construction for method with receiver
            call_args = mock_read.call_args
            assert call_args[0][0] == "lonegunmanb"  # owner
            assert call_args[0][1] == "terraform-provider-azurerm-index"  # repo
            assert call_args[0][2] == "index/internal/services/resource/method.ResourceGroupResource.Create.goindex"  # path

    @pytest.mark.asyncio
    async def test_fetch_terraform_source_code_ephemeral(self, golang_provider):
        """Test fetching terraform source code for ephemeral resource."""
        ephemeral_index = {
            "open_index": "services/keyvault/ephemeral_key_vault_secret.go",
            "close_index": "services/keyvault/ephemeral_key_vault_secret_close.go",
            "renew_index": "services/keyvault/ephemeral_key_vault_secret_renew.go", 
            "schema_index": "services/keyvault/ephemeral_key_vault_secret_schema.go",
            "namespace": "github.com/hashicorp/terraform-provider-azurerm/internal/services/keyvault"
        }
        
        ephemeral_code = """func (e *KeyVaultSecretEphemeralResource) Open(ctx context.Context, req ephemeral.OpenRequest, resp *ephemeral.OpenResponse) {
    var data KeyVaultSecretEphemeralResourceModel
    resp.Diagnostics.Append(req.Config.Get(ctx, &data)...)
    
    // Implementation for opening ephemeral resource
}"""
        
        with patch.object(golang_provider, '_read_github_content') as mock_read:
            mock_read.side_effect = [
                json.dumps(ephemeral_index),
                ephemeral_code
            ]
            
            result = await golang_provider.query_terraform_source_code(
                block_type="ephemeral",
                terraform_type="azurerm_key_vault_secret",
                entrypoint_name="open"
            )
            
            assert "KeyVaultSecretEphemeralResource" in result
            assert "OpenRequest" in result
            # Verify ephemeral path is used (not "ephemerals")
            index_call = mock_read.call_args_list[0]
            path_arg = index_call[0][2]  # path is the 3rd argument (index 2)
            assert "index/ephemeral/" in path_arg
            assert "azurerm_key_vault_secret.json" in path_arg

    @pytest.mark.asyncio
    async def test_query_golang_source_code_with_var_symbol(self, golang_provider):
        """Test querying golang source code for variable."""
        namespace = "github.com/hashicorp/terraform-provider-azurerm/internal/services/resource"
        var_code = """package resource

import "github.com/hashicorp/terraform-plugin-sdk/v2/helper/schema"

var resourceGroupSchema = map[string]*schema.Schema{
    "name": {
        Type:     schema.TypeString,
        Required: true,
        ForceNew: true,
    },
    "location": {
        Type:     schema.TypeString,
        Required: true,
        ForceNew: true,
    },
}"""
        
        with patch.object(golang_provider, '_read_github_content', return_value=var_code):
            result = await golang_provider.query_golang_source_code(
                namespace=namespace,
                symbol="var",
                name="resourceGroupSchema"
            )
            
            assert "var resourceGroupSchema" in result
            assert "schema.Schema" in result
            assert "TypeString" in result

    @pytest.mark.asyncio
    async def test_caching_functionality(self, golang_provider_with_temp_cache):
        """Test caching functionality with real file operations."""
        provider = golang_provider_with_temp_cache
        sample_content = "package main\n\nfunc main() {}\n"
        encoded_content = base64.b64encode(sample_content.encode()).decode()
        
        github_response = {
            "content": encoded_content,
            "encoding": "base64"
        }
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = github_response
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            # First call should hit the API
            result1 = await provider._read_github_content(
                owner="test-owner",
                repo="test-repo",
                path="test/path.go",
                tag="v1.0.0"
            )
            
            # Second call should use cache
            result2 = await provider._read_github_content(
                owner="test-owner",
                repo="test-repo",
                path="test/path.go",
                tag="v1.0.0"
            )
            
            # Verify both calls returned same content
            assert result1 == sample_content
            assert result2 == sample_content
            
            # Verify API was only called once (second call used cache)
            assert mock_client.return_value.__aenter__.return_value.get.call_count == 1
            
            # Verify cache info shows the cached entry
            cache_info = provider.get_cache_info()
            assert cache_info["entries"] > 0
            assert cache_info["size_mb"] >= 0  # Changed from > 0 since small files might round to 0

    @pytest.mark.asyncio
    async def test_error_handling_404(self, golang_provider):
        """Test error handling for 404 responses."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            result = await golang_provider.query_golang_source_code(
                namespace="github.com/hashicorp/terraform-provider-azurerm/internal/clients",
                symbol="type",
                name="NonExistentType"
            )
            
            assert "Source code not found (404)" in result

    @pytest.mark.asyncio
    async def test_error_handling_401_no_token(self, golang_provider):
        """Test error handling for 401 without token."""
        # Ensure no token is set
        original_token = os.environ.get('GITHUB_TOKEN')
        if 'GITHUB_TOKEN' in os.environ:
            del os.environ['GITHUB_TOKEN']
        
        try:
            with patch('httpx.AsyncClient') as mock_client:
                mock_response = Mock()
                mock_response.status_code = 401
                mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
                
                result = await golang_provider.query_golang_source_code(
                    namespace="github.com/hashicorp/terraform-provider-azurerm/internal/clients",
                    symbol="type",
                    name="Client"
                )
                
                assert "requires authentication" in result
                assert "GITHUB_TOKEN" in result
        finally:
            # Restore original token
            if original_token:
                os.environ['GITHUB_TOKEN'] = original_token

    @pytest.mark.asyncio
    async def test_error_handling_401_with_invalid_token(self, golang_provider):
        """Test error handling for 401 with invalid token."""
        with patch.dict('os.environ', {'GITHUB_TOKEN': 'invalid-token'}):
            with patch('httpx.AsyncClient') as mock_client:
                mock_response = Mock()
                mock_response.status_code = 401
                mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
                
                result = await golang_provider.query_golang_source_code(
                    namespace="github.com/hashicorp/terraform-provider-azurerm/internal/clients",
                    symbol="type",
                    name="Client"
                )
                
                assert "GitHub API authentication failed" in result


class TestGolangSourceProviderIntegration:
    """Integration test cases for Golang Source Provider using real GitHub API."""

    @pytest.fixture
    def golang_provider(self):
        """Get golang source provider instance."""
        return get_golang_source_provider()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_supported_tags_real_api(self, golang_provider):
        """Test getting supported tags from real GitHub API."""
        namespace = "github.com/hashicorp/terraform-provider-azurerm/internal"
        
        tags = await golang_provider.get_supported_tags(namespace)
        
        assert isinstance(tags, list)
        assert len(tags) > 0
        # Should contain version tags or fallback to ["latest"]
        assert any(tag.startswith("v") for tag in tags) or tags == ["latest"]

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_query_golang_source_code_real_type(self, golang_provider):
        """Test querying real golang source code for a type."""
        namespace = "github.com/hashicorp/terraform-provider-azurerm/internal/clients"
        
        result = await golang_provider.query_golang_source_code(
            namespace=namespace,
            symbol="type",
            name="Client"
        )
        
        # Should either return source code or a specific error message
        assert isinstance(result, str)
        assert len(result) > 0
        # Should not be a generic error
        assert not result.startswith("Error: Failed to query golang source code")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_query_golang_source_code_real_function(self, golang_provider):
        """Test querying real golang source code for a function."""
        namespace = "github.com/hashicorp/terraform-provider-azurerm/internal/clients"
        
        result = await golang_provider.query_golang_source_code(
            namespace=namespace,
            symbol="func",
            name="NewClient"
        )
        
        assert isinstance(result, str)
        assert len(result) > 0
        # Should either contain source code or a 404 not found message
        if not result.startswith("Source code not found"):
            assert "func" in result or "NewClient" in result

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_query_terraform_source_code_real_resource(self, golang_provider):
        """Test querying real terraform source code for a resource."""
        result = await golang_provider.query_terraform_source_code(
            block_type="resource",
            terraform_type="azurerm_resource_group",
            entrypoint_name="create"
        )
        
        assert isinstance(result, str)
        assert len(result) > 0
        # Should either return source code or a specific error message
        assert not result.startswith("Error: Failed to query terraform source code")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_query_terraform_source_code_real_data_source(self, golang_provider):
        """Test querying real terraform source code for a data source."""
        result = await golang_provider.query_terraform_source_code(
            block_type="data",
            terraform_type="azurerm_resource_group",
            entrypoint_name="read"
        )
        
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_auth_fallback_real_api(self, golang_provider):
        """Test auth fallback mechanism with real API."""
        # This test verifies the new auth logic works with real API
        namespace = "github.com/hashicorp/terraform-provider-azurerm/internal"
        
        # First, test without token
        original_token = os.environ.get('GITHUB_TOKEN')
        if 'GITHUB_TOKEN' in os.environ:
            del os.environ['GITHUB_TOKEN']
        
        try:
            tags_without_token = await golang_provider.get_supported_tags(namespace)
            assert isinstance(tags_without_token, list)
            
            # Then test with token if available
            if original_token:
                os.environ['GITHUB_TOKEN'] = original_token
                tags_with_token = await golang_provider.get_supported_tags(namespace)
                assert isinstance(tags_with_token, list)
                # Both should work, possibly returning same or different results
                # depending on rate limits and repository access
                
        finally:
            # Restore original token state
            if original_token:
                os.environ['GITHUB_TOKEN'] = original_token
            elif 'GITHUB_TOKEN' in os.environ:
                del os.environ['GITHUB_TOKEN']

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_azapi_provider_real(self, golang_provider):
        """Test querying real azapi provider source code."""
        namespace = "github.com/Azure/terraform-provider-azapi/internal"
        
        # Test getting tags for azapi provider
        tags = await golang_provider.get_supported_tags(namespace)
        assert isinstance(tags, list)
        assert len(tags) > 0

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_real_api_error_handling(self, golang_provider):
        """Test error handling with real API for non-existent resources."""
        # Test with non-existent namespace that should trigger fallback
        namespace = "github.com/hashicorp/terraform-provider-azurerm/internal/nonexistent"
        
        result = await golang_provider.query_golang_source_code(
            namespace=namespace,
            symbol="type",
            name="NonExistentType"
        )
        
        # Should return a 404 error or specific not found message
        assert isinstance(result, str)
        assert "404" in result or "not found" in result.lower()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_real_terraform_type_validation(self, golang_provider):
        """Test terraform type validation with real provider."""
        # Test with valid provider but non-existent resource type
        result = await golang_provider.query_terraform_source_code(
            block_type="resource",
            terraform_type="azurerm_nonexistent_resource",
            entrypoint_name="create"
        )
        
        assert isinstance(result, str)
        # Should either find the resource or return a 404
        assert not result.startswith("Error: Failed to query terraform source code")