"""Test case to verify the fix for service subdirectory search."""

import pytest
from unittest.mock import AsyncMock, patch
from tf_mcp_server.tools.golang_source_provider import GolangSourceProvider


class TestServiceSubdirectorySearch:
    """Test the service subdirectory search functionality."""
    
    @pytest.mark.asyncio
    async def test_service_subdirectory_search_kusto_function(self):
        """Test that functions in service subdirectories can be found."""
        provider = GolangSourceProvider()
        
        # Mock the GitHub content reading to simulate the actual fix
        def mock_read_github_content(owner, repo, path, tag):
            if path == "index/internal/func.resourceKustoClusterCreate.goindex":
                # Simulate 404 for direct path
                raise Exception("source code not found (404)")
            elif path == "index/internal/services/kusto/func.resourceKustoClusterCreate.goindex":
                # Return mock Go code for the service subdirectory
                return """package github.com/hashicorp/terraform-provider-azurerm/internal/services/kusto

func resourceKustoClusterCreate(d *schema.ResourceData, meta interface{}) error {
    client := meta.(*clients.Client).Kusto.ClustersClient
    ctx, cancel := timeouts.ForCreate(meta.(*clients.Client).StopContext, d)
    defer cancel()
    
    // Implementation...
    return nil
}"""
            else:
                raise Exception(f"Unexpected path: {path}")
        
        def mock_read_github_directory(owner, repo, path, tag):
            if path == "index/internal/services":
                # Return mock directory listing with kusto service
                return [
                    {"name": "kusto", "type": "dir"},
                    {"name": "storage", "type": "dir"},
                    {"name": "compute", "type": "dir"}
                ]
            else:
                raise Exception(f"Unexpected directory path: {path}")
        
        with patch.object(provider, '_read_github_content', side_effect=mock_read_github_content), \
             patch.object(provider, '_read_github_directory', side_effect=mock_read_github_directory):
            
            result = await provider.query_golang_source_code(
                namespace="github.com/hashicorp/terraform-provider-azurerm/internal",
                symbol="func",
                name="resourceKustoClusterCreate",
                tag="v4.46.0"
            )
            
            assert "func resourceKustoClusterCreate" in result
            assert "internal/services/kusto" in result
            assert "Source code not found" not in result  # No error message in the result
    
    @pytest.mark.asyncio
    async def test_should_not_search_services_for_clients_namespace(self):
        """Test that functions in clients namespace don't trigger service search."""
        provider = GolangSourceProvider()
        
        # Mock the GitHub content reading to simulate direct path failure
        def mock_read_github_content(owner, repo, path, tag):
            # Always fail to simulate 404
            raise Exception("source code not found (404)")
        
        with patch.object(provider, '_read_github_content', side_effect=mock_read_github_content):
            
            result = await provider.query_golang_source_code(
                namespace="github.com/hashicorp/terraform-provider-azurerm/internal/clients",
                symbol="func",
                name="NewClient",
                tag="v4.46.0"
            )
            
            # Should return error message without searching in services
            assert "Source code not found (404)" in result
    
    def test_should_search_in_services_logic(self):
        """Test the logic for determining when to search in services."""
        provider = GolangSourceProvider()
        
        # Should search for resource functions
        assert provider._should_search_in_services("resourceKustoClusterCreate", "internal") == True
        assert provider._should_search_in_services("dataSourceKustoCluster", "internal") == True
        assert provider._should_search_in_services("data_sourceKustoCluster", "internal") == True
        
        # Should not search for clients functions
        assert provider._should_search_in_services("NewClient", "internal/clients") == False
        assert provider._should_search_in_services("BuildClient", "internal/utils") == False
        
        # Should not search for non-resource functions in general namespaces
        assert provider._should_search_in_services("helperFunction", "internal") == False