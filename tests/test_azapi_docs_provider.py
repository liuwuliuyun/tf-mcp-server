"""
Comprehensive test cases for AzAPI documentation provider.
Tests schema loading, searching, and online documentation retrieval.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from httpx import Response

from tf_mcp_server.tools.azapi_docs_provider import AzAPIDocumentationProvider, get_azapi_documentation_provider


class TestAzAPIDocumentationProvider:
    """Test class for AzAPI documentation provider."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Mock the schema loading to avoid actual file I/O
        with patch('tf_mcp_server.tools.azapi_docs_provider.load_azapi_schema') as mock_load:
            mock_load.return_value = {
                "Microsoft.Storage/storageAccounts@2021-04-01": {
                    "properties": {
                        "location": {"type": "string", "required": True},
                        "sku": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string", "required": True}
                            }
                        },
                        "kind": {"type": "string", "required": True}
                    }
                },
                "Microsoft.Compute/virtualMachines@2021-03-01": {
                    "properties": {
                        "location": {"type": "string", "required": True},
                        "hardwareProfile": {
                            "type": "object",
                            "properties": {
                                "vmSize": {"type": "string", "required": True}
                            }
                        }
                    }
                }
            }
            self.provider = AzAPIDocumentationProvider()
    
    def test_initialization(self):
        """Test that the provider initializes correctly."""
        assert self.provider.azapi_schema is not None
        assert len(self.provider.azapi_schema) == 2
    
    def test_search_azapi_schema_exact_match(self):
        """Test searching for an exact schema match."""
        result = self.provider._search_azapi_schema(
            "Microsoft.Storage/storageAccounts@2021-04-01"
        )
        
        assert result != {}
        assert "definition" in result
        assert "schema_key" in result
        assert result["schema_key"] == "Microsoft.Storage/storageAccounts@2021-04-01"
        assert "properties" in result["definition"]
    
    def test_search_azapi_schema_partial_match(self):
        """Test searching with partial resource type."""
        result = self.provider._search_azapi_schema("storageAccounts")
        
        assert result != {}
        assert "definition" in result
        assert "schema_key" in result
        assert "storageaccounts" in result["schema_key"].lower()
    
    def test_search_azapi_schema_case_insensitive(self):
        """Test that search is case-insensitive."""
        result = self.provider._search_azapi_schema("STORAGEACCOUNTS")
        
        assert result != {}
        assert "definition" in result
    
    def test_search_azapi_schema_not_found(self):
        """Test searching for a non-existent resource type."""
        result = self.provider._search_azapi_schema("NonExistentResource")
        
        assert result == {}
    
    def test_search_azapi_schema_empty_schema(self):
        """Test searching when schema is empty."""
        with patch('tf_mcp_server.tools.azapi_docs_provider.load_azapi_schema') as mock_load:
            mock_load.return_value = {}
            provider = AzAPIDocumentationProvider()
            
            result = provider._search_azapi_schema("storageAccounts")
            assert result == {}
    
    @pytest.mark.asyncio
    async def test_search_azapi_provider_docs_schema_found(self):
        """Test searching documentation when schema is found locally."""
        result = await self.provider.search_azapi_provider_docs(
            "Microsoft.Storage/storageAccounts",
            "2021-04-01"
        )
        
        assert "resource_type" in result
        assert result["resource_type"] == "Microsoft.Storage/storageAccounts"
        assert result["api_version"] == "2021-04-01"
        assert "schema" in result
        assert result["source"] == "azapi_schemas.json"
    
    @pytest.mark.asyncio
    async def test_search_azapi_provider_docs_no_api_version(self):
        """Test searching without specifying API version."""
        result = await self.provider.search_azapi_provider_docs(
            "Microsoft.Compute/virtualMachines"
        )
        
        assert "resource_type" in result
        assert result["api_version"] == "latest"
        assert "schema" in result
    
    @pytest.mark.asyncio
    async def test_fetch_azapi_docs_online_success(self):
        """Test fetching documentation from online sources successfully."""
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.text = "Azure REST API documentation content"
        
        # Create a mock async context manager
        mock_get = AsyncMock(return_value=mock_response)
        mock_client_instance = Mock()
        mock_client_instance.get = mock_get
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)
        
        with patch('tf_mcp_server.tools.azapi_docs_provider.AsyncClient', return_value=mock_client_instance):
            result = await self.provider._fetch_azapi_docs_online(
                "Microsoft.Network/virtualNetworks",
                "2021-02-01"
            )
            
            assert "resource_type" in result
            assert result["resource_type"] == "Microsoft.Network/virtualNetworks"
            assert result["api_version"] == "2021-02-01"
            assert "documentation_url" in result
            assert result["source"] == "Azure REST API docs"
    
    @pytest.mark.asyncio
    async def test_fetch_azapi_docs_online_fallback(self):
        """Test fallback when online fetch fails."""
        mock_response = Mock(spec=Response)
        mock_response.status_code = 404
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_async_client = MagicMock()
            mock_async_client.__aenter__.return_value.get.return_value = mock_response
            mock_client.return_value = mock_async_client
            
            result = await self.provider._fetch_azapi_docs_online(
                "Microsoft.Unknown/resource",
                "2021-01-01"
            )
            
            assert "resource_type" in result
            assert result["source"] == "fallback"
            assert "documentation_url" in result
            assert "registry.terraform.io" in result["documentation_url"]
    
    @pytest.mark.asyncio
    async def test_fetch_azapi_docs_online_exception(self):
        """Test handling of exceptions during online fetch."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.side_effect = Exception("Network error")
            
            result = await self.provider._fetch_azapi_docs_online(
                "Microsoft.Test/resource",
                "2021-01-01"
            )
            
            assert result["source"] == "fallback"
    
    @pytest.mark.asyncio
    async def test_search_azapi_provider_docs_online_fallback(self):
        """Test full search flow with online fallback."""
        with patch('tf_mcp_server.tools.azapi_docs_provider.load_azapi_schema') as mock_load:
            # Empty schema to force online lookup
            mock_load.return_value = {}
            provider = AzAPIDocumentationProvider()
            
            mock_response = Mock(spec=Response)
            mock_response.status_code = 404
            
            with patch('httpx.AsyncClient') as mock_client:
                mock_async_client = MagicMock()
                mock_async_client.__aenter__.return_value.get.return_value = mock_response
                mock_client.return_value = mock_async_client
                
                result = await provider.search_azapi_provider_docs(
                    "Microsoft.NewService/newResource",
                    "2021-01-01"
                )
                
                assert result["source"] == "fallback"
                assert result["resource_type"] == "Microsoft.NewService/newResource"
    
    @pytest.mark.asyncio
    async def test_search_azapi_provider_docs_error_handling(self):
        """Test error handling in search method."""
        with patch.object(
            self.provider,
            '_search_azapi_schema',
            side_effect=Exception("Search error")
        ):
            result = await self.provider.search_azapi_provider_docs(
                "Microsoft.Storage/storageAccounts"
            )
            
            assert "error" in result
            assert "Search error" in result["error"]
            assert result["resource_type"] == "Microsoft.Storage/storageAccounts"
    
    def test_get_azapi_documentation_provider_singleton(self):
        """Test that the global provider returns the same instance."""
        provider1 = get_azapi_documentation_provider()
        provider2 = get_azapi_documentation_provider()
        
        assert provider1 is provider2
    
    @pytest.mark.asyncio
    async def test_search_with_compute_resource(self):
        """Test searching for a compute resource."""
        result = await self.provider.search_azapi_provider_docs(
            "Microsoft.Compute/virtualMachines",
            "2021-03-01"
        )
        
        assert result["resource_type"] == "Microsoft.Compute/virtualMachines"
        assert "schema" in result
        assert result["source"] == "azapi_schemas.json"
    
    @pytest.mark.asyncio
    async def test_search_normalizes_resource_type(self):
        """Test that resource type search is normalized."""
        # Test with different casing
        result1 = await self.provider.search_azapi_provider_docs("storageaccounts")
        result2 = await self.provider.search_azapi_provider_docs("STORAGEACCOUNTS")
        result3 = await self.provider.search_azapi_provider_docs("StorageAccounts")
        
        # All should find the schema
        assert "schema" in result1
        assert "schema" in result2
        assert "schema" in result3
    
    @pytest.mark.asyncio
    async def test_api_version_in_response(self):
        """Test that API version is correctly included in response."""
        # With specific version
        result1 = await self.provider.search_azapi_provider_docs(
            "Microsoft.Storage/storageAccounts",
            "2021-04-01"
        )
        assert result1["api_version"] == "2021-04-01"
        
        # Without version (should default to 'latest')
        result2 = await self.provider.search_azapi_provider_docs(
            "Microsoft.Storage/storageAccounts"
        )
        assert result2["api_version"] == "latest"
    
    def test_schema_structure_validation(self):
        """Test that schema has expected structure."""
        result = self.provider._search_azapi_schema("Microsoft.Storage/storageAccounts")
        
        assert "definition" in result
        assert "properties" in result["definition"]
        
        # Check specific properties
        properties = result["definition"]["properties"]
        assert "location" in properties
        assert "sku" in properties
        assert "kind" in properties
    
    @pytest.mark.asyncio
    async def test_online_docs_url_format(self):
        """Test that online documentation URL is correctly formatted."""
        mock_response = Mock(spec=Response)
        mock_response.status_code = 404
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_async_client = MagicMock()
            mock_async_client.__aenter__.return_value.get.return_value = mock_response
            mock_client.return_value = mock_async_client
            
            result = await self.provider._fetch_azapi_docs_online(
                "Microsoft.Storage/storageAccounts",
                "2021-04-01"
            )
            
            assert "documentation_url" in result
            assert result["documentation_url"] == "https://registry.terraform.io/providers/Azure/azapi/latest/docs"
    
    @pytest.mark.asyncio
    async def test_multiple_searches_different_resources(self):
        """Test searching for multiple different resources."""
        resources = [
            ("Microsoft.Storage/storageAccounts", "2021-04-01"),
            ("Microsoft.Compute/virtualMachines", "2021-03-01"),
        ]
        
        for resource_type, api_version in resources:
            result = await self.provider.search_azapi_provider_docs(
                resource_type,
                api_version
            )
            
            assert result["resource_type"] == resource_type
            assert result["api_version"] == api_version
            assert "schema" in result or "error" in result


class TestAzAPIDocumentationProviderEdgeCases:
    """Test edge cases and error conditions."""
    
    @pytest.mark.asyncio
    async def test_empty_resource_type(self):
        """Test with empty resource type."""
        with patch('tf_mcp_server.tools.azapi_docs_provider.load_azapi_schema') as mock_load:
            mock_load.return_value = {}
            provider = AzAPIDocumentationProvider()
            
            mock_response = Mock(spec=Response)
            mock_response.status_code = 404
            
            with patch('httpx.AsyncClient') as mock_client:
                mock_async_client = MagicMock()
                mock_async_client.__aenter__.return_value.get.return_value = mock_response
                mock_client.return_value = mock_async_client
                
                result = await provider.search_azapi_provider_docs("", "")
                
                assert "resource_type" in result
                assert result["resource_type"] == ""
    
    @pytest.mark.asyncio
    async def test_special_characters_in_resource_type(self):
        """Test with special characters in resource type."""
        with patch('tf_mcp_server.tools.azapi_docs_provider.load_azapi_schema') as mock_load:
            mock_load.return_value = {}
            provider = AzAPIDocumentationProvider()
            
            mock_response = Mock(spec=Response)
            mock_response.status_code = 404
            
            with patch('httpx.AsyncClient') as mock_client:
                mock_async_client = MagicMock()
                mock_async_client.__aenter__.return_value.get.return_value = mock_response
                mock_client.return_value = mock_async_client
                
                result = await provider.search_azapi_provider_docs(
                    "Microsoft.Test/resource@#$%",
                    "2021-01-01"
                )
                
                assert "resource_type" in result
    
    def test_none_schema(self):
        """Test when schema is None."""
        with patch('tf_mcp_server.tools.azapi_docs_provider.load_azapi_schema') as mock_load:
            mock_load.return_value = None
            provider = AzAPIDocumentationProvider()
            
            result = provider._search_azapi_schema("Microsoft.Storage/storageAccounts")
            assert result == {}
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """Test handling of timeout exceptions."""
        with patch('tf_mcp_server.tools.azapi_docs_provider.load_azapi_schema') as mock_load:
            mock_load.return_value = {}
            provider = AzAPIDocumentationProvider()
            
            with patch('httpx.AsyncClient') as mock_client:
                mock_async_client = MagicMock()
                mock_async_client.__aenter__.return_value.get.side_effect = TimeoutError("Timeout")
                mock_client.return_value = mock_async_client
                
                result = await provider._fetch_azapi_docs_online(
                    "Microsoft.Storage/storageAccounts",
                    "2021-04-01"
                )
                
                # Should fall back gracefully
                assert result["source"] == "fallback"
