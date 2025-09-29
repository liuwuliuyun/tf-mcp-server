"""
Test cases for Golang Source Code Analysis Tools.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import json
import base64
import httpx

from tf_mcp_server.tools.golang_source_provider import get_golang_source_provider


class TestGolangSourceProvider:
    """Test cases for Golang Source Provider."""

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
    async def test_get_supported_tags_with_github_token(self, golang_provider, sample_github_tags_response):
        """Test getting supported tags with GitHub token."""
        namespace = "github.com/hashicorp/terraform-provider-azurerm/internal"
        
        with patch.dict('os.environ', {'GITHUB_TOKEN': 'test-token'}):
            with patch('httpx.AsyncClient') as mock_client:
                mock_response = Mock()
                mock_response.raise_for_status.return_value = None
                mock_response.json.return_value = sample_github_tags_response
                mock_client_instance = mock_client.return_value.__aenter__.return_value
                mock_client_instance.get.return_value = mock_response
                
                tags = await golang_provider.get_supported_tags(namespace)
                
                # Verify Authorization header was set
                call_args = mock_client_instance.get.call_args
                headers = call_args[1]['headers']
                assert 'Authorization' in headers
                assert headers['Authorization'] == 'Bearer test-token'
                assert isinstance(tags, list)

    @pytest.mark.asyncio
    async def test_get_supported_tags_unsupported_namespace(self, golang_provider):
        """Test getting supported tags for unsupported namespace."""
        with pytest.raises(ValueError, match="Unsupported namespace"):
            await golang_provider.get_supported_tags("invalid/namespace")

    @pytest.mark.asyncio
    async def test_get_supported_tags_api_error(self, golang_provider):
        """Test getting supported tags when API returns error."""
        namespace = "github.com/hashicorp/terraform-provider-azurerm/internal"
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "401 Unauthorized", request=Mock(), response=Mock()
            )
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            tags = await golang_provider.get_supported_tags(namespace)
            
            # Should return fallback
            assert tags == ["latest"]

    def test_get_supported_providers(self, golang_provider):
        """Test getting supported providers."""
        providers = golang_provider.get_supported_providers()
        
        assert isinstance(providers, list)
        assert "azurerm" in providers
        assert "azapi" in providers

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
    async def test_query_terraform_source_code_data_source(self, golang_provider):
        """Test querying terraform source code for data source."""
        data_index = {
            "read_index": "services/resource/data_source_resource_group.go",
            "schema_index": "services/resource/data_source_resource_group_schema.go",
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
        with pytest.raises(ValueError, match="Invalid entrypoint"):
            await golang_provider.query_terraform_source_code(
                block_type="resource",
                terraform_type="azurerm_resource_group",
                entrypoint_name="invalid"
            )

    @pytest.mark.asyncio
    async def test_query_terraform_source_code_invalid_terraform_type(self, golang_provider):
        """Test querying terraform source code with invalid terraform type."""
        with pytest.raises(ValueError, match="Invalid terraform type"):
            await golang_provider.query_terraform_source_code(
                block_type="resource",
                terraform_type="invalid",  # Only one segment, should trigger validation error
                entrypoint_name="create"
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
    async def test_read_github_content_success(self, golang_provider):
        """Test reading GitHub content successfully."""
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
            
            result = await golang_provider._read_github_content(
                owner="lonegunmanb",
                repo="terraform-provider-azurerm-index",
                path="index/internal/clients/type.Client.goindex",
                tag="v4.25.0"
            )
            
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
        """Test reading GitHub content with 401 error and no token."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 401
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            with pytest.raises(Exception, match="GitHub API authentication failed.*GITHUB_TOKEN"):
                await golang_provider._read_github_content(
                    owner="lonegunmanb",
                    repo="terraform-provider-azurerm-index",
                    path="some/path",
                    tag=None
                )

    @pytest.mark.asyncio 
    async def test_read_github_content_401_with_token(self, golang_provider):
        """Test reading GitHub content with 401 error and token set."""
        with patch.dict('os.environ', {'GITHUB_TOKEN': 'invalid-token'}):
            with patch('httpx.AsyncClient') as mock_client:
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
            # Verify tag was passed to _read_github_content
            call_args = mock_read.call_args
            # The method calls _read_github_content with: owner, repo, path, tag
            # mock_read.call_args[0] contains positional args (self excluded for patch.object)
            # So args are: [owner, repo, path, tag]
            assert len(call_args[0]) >= 4, f"Expected at least 4 args, got {len(call_args[0])}: {call_args[0]}"
            assert call_args[0][3] == "v4.25.0"  # tag is the 4th argument (index 3)

    @pytest.mark.asyncio
    async def test_fetch_terraform_source_code_ephemeral(self, golang_provider):
        """Test fetching terraform source code for ephemeral resource."""
        ephemeral_index = {
            "open_index": "services/keyvault/ephemeral_key_vault_secret.go",
            "close_index": "services/keyvault/ephemeral_key_vault_secret_close.go",
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
            # The method calls _read_github_content with: owner, repo, path, tag
            # index_call[0] contains positional args: [owner, repo, path, tag]
            assert len(index_call[0]) >= 3, f"Expected at least 3 args, got {len(index_call[0])}: {index_call[0]}"
            path_arg = index_call[0][2]  # path is the 3rd argument (index 2)
            assert "index/ephemeral/" in path_arg

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