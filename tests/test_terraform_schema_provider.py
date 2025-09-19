"""
Unit tests for Terraform Schema Provider.
Tests the integration and functionality of terraform schema analysis tools.
"""

import pytest
import json
import subprocess
from unittest.mock import Mock, patch, MagicMock
from src.tf_mcp_server.tools.terraform_schema_provider import (
    TerraformSchemaProvider, 
    get_terraform_schema_provider
)


class TestTerraformSchemaProvider:
    """Test cases for TerraformSchemaProvider."""
    
    @pytest.fixture
    def schema_provider(self):
        """Create TerraformSchemaProvider instance for testing."""
        return get_terraform_schema_provider()
    
    @pytest.fixture
    def sample_schema_response(self):
        """Sample terraform schema response."""
        return {
            "provider_schemas": {
                "registry.terraform.io/hashicorp/azurerm": {
                    "resource_schemas": {
                        "azurerm_storage_account": {
                            "version": 0,
                            "block": {
                                "attributes": {
                                    "name": {
                                        "type": "string",
                                        "description": "Storage account name",
                                        "required": True
                                    },
                                    "resource_group_name": {
                                        "type": "string",
                                        "description": "Resource group name",
                                        "required": True
                                    },
                                    "location": {
                                        "type": "string",
                                        "description": "Azure location",
                                        "required": True
                                    },
                                    "account_tier": {
                                        "type": "string",
                                        "description": "Performance tier",
                                        "required": True
                                    }
                                },
                                "block_types": {
                                    "network_rules": {
                                        "nesting_mode": "list",
                                        "max_items": 1,
                                        "block": {
                                            "attributes": {
                                                "default_action": {
                                                    "type": "string",
                                                    "description": "Default action",
                                                    "required": True
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "data_source_schemas": {
                        "azurerm_storage_account": {
                            "version": 0,
                            "block": {
                                "attributes": {
                                    "name": {
                                        "type": "string",
                                        "description": "Storage account name",
                                        "required": True
                                    }
                                }
                            }
                        }
                    }
                },
                "registry.terraform.io/Azure/azapi": {
                    "functions": {
                        "build_resource_id": {
                            "summary": "Build Azure resource ID",
                            "description": "Builds a properly formatted Azure resource ID"
                        }
                    }
                }
            }
        }

    @pytest.mark.asyncio
    async def test_query_terraform_schema_resource_full(self, schema_provider, sample_schema_response):
        """Test query_terraform_schema for a full resource schema."""
        with patch('subprocess.run') as mock_run:
            # Mock successful subprocess call
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = json.dumps(sample_schema_response)
            
            result = await schema_provider.query_schema(
                category="resource",
                resource_type="azurerm_storage_account",
                provider_namespace="hashicorp",
                provider_name="azurerm",
                provider_version="4.39.0"
            )
            
            # Parse the JSON response
            content = json.loads(result)
            assert "name" in content
            assert "resource_group_name" in content
            assert "location" in content
            assert "account_tier" in content
            assert "network_rules" in content

    @pytest.mark.asyncio
    async def test_query_terraform_schema_resource_with_path(self, schema_provider, sample_schema_response):
        """Test query_terraform_schema for a specific resource attribute."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = json.dumps(sample_schema_response)
            
            result = await schema_provider.query_schema(
                category="resource",
                resource_type="azurerm_storage_account",
                path="name",
                provider_namespace="hashicorp",
                provider_name="azurerm"
            )
            
            content = json.loads(result)
            assert content["type"] == "string"
            assert "Storage account name" in content["description"]

    @pytest.mark.asyncio
    async def test_query_terraform_schema_data_source(self, schema_provider, sample_schema_response):
        """Test query_terraform_schema for a data source."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = json.dumps(sample_schema_response)
            
            result = await schema_provider.query_schema(
                category="data",
                resource_type="azurerm_storage_account",
                provider_namespace="hashicorp",
                provider_name="azurerm"
            )
            
            content = json.loads(result)
            assert "name" in content

    @pytest.mark.asyncio
    async def test_query_terraform_schema_invalid_category(self, schema_provider):
        """Test query_terraform_schema with invalid category."""
        with pytest.raises(ValueError) as exc_info:
            await schema_provider.query_schema(
                category="invalid",
                resource_type="azurerm_storage_account"
            )
        
        assert "Invalid category" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_list_terraform_provider_items_resources(self, schema_provider, sample_schema_response):
        """Test list_terraform_provider_items for resources."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = json.dumps(sample_schema_response)
            
            result = await schema_provider.list_provider_items(
                category="resource",
                provider_namespace="hashicorp",
                provider_name="azurerm",
                provider_version="4.39.0"
            )
            
            assert isinstance(result, list)
            assert "azurerm_storage_account" in result

    @pytest.mark.asyncio
    async def test_list_terraform_provider_items_data_sources(self, schema_provider, sample_schema_response):
        """Test list_terraform_provider_items for data sources."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = json.dumps(sample_schema_response)
            
            result = await schema_provider.list_provider_items(
                category="data",
                provider_namespace="hashicorp",
                provider_name="azurerm"
            )
            
            assert isinstance(result, list)
            assert "azurerm_storage_account" in result

    @pytest.mark.asyncio
    async def test_list_terraform_provider_items_functions(self, schema_provider, sample_schema_response):
        """Test list_terraform_provider_items for functions."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = json.dumps(sample_schema_response)
            
            result = await schema_provider.list_provider_items(
                category="function",
                provider_namespace="Azure",
                provider_name="azapi"
            )
            
            assert isinstance(result, list)
            assert "build_resource_id" in result

    @pytest.mark.asyncio
    async def test_list_terraform_provider_items_invalid_category(self, schema_provider):
        """Test list_terraform_provider_items with invalid category."""
        with pytest.raises(ValueError) as exc_info:
            await schema_provider.list_provider_items(
                category="invalid",
                provider_namespace="hashicorp",
                provider_name="azurerm"
            )
        
        assert "Invalid category" in str(exc_info.value)

    def test_get_supported_providers(self, schema_provider):
        """Test get_supported_providers method."""
        result = schema_provider.get_supported_providers()
        
        assert isinstance(result, list)
        assert "azurerm" in result
        assert "azapi" in result

    @pytest.mark.asyncio
    async def test_terraform_schema_provider_error_handling(self, schema_provider):
        """Test error handling when terraform command fails."""
        with patch('subprocess.run') as mock_run:
            # Mock failed subprocess call
            mock_run.return_value.returncode = 1
            mock_run.return_value.stderr = "Terraform error occurred"
            
            with pytest.raises(Exception) as exc_info:
                await schema_provider.query_schema(
                    category="resource",
                    resource_type="azurerm_storage_account"
                )
            
            assert "Terraform schema query failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_query_terraform_schema_nested_path(self, schema_provider, sample_schema_response):
        """Test query_terraform_schema with nested path."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = json.dumps(sample_schema_response)
            
            result = await schema_provider.query_schema(
                category="resource",
                resource_type="azurerm_storage_account",
                path="network_rules.default_action",
                provider_namespace="hashicorp",
                provider_name="azurerm"
            )
            
            content = json.loads(result)
            assert content["type"] == "string"
            assert "Default action" in content["description"]

    @pytest.mark.asyncio
    async def test_infer_provider_name(self, schema_provider):
        """Test provider name inference from resource type."""
        # Test azurerm inference
        provider_name = schema_provider._infer_provider_name("azurerm_storage_account")
        assert provider_name == "azurerm"
        
        # Test azapi inference  
        provider_name = schema_provider._infer_provider_name("azapi_storage_account")
        assert provider_name == "azapi"

    @pytest.mark.asyncio
    async def test_terraform_config_generation(self, schema_provider):
        """Test terraform configuration generation."""
        # Mock filesystem operations
        with patch('tempfile.mkdtemp', return_value="/tmp/test"):
            with patch('builtins.open', mock_open()) as mock_file:
                config = schema_provider._generate_terraform_config(
                    "/tmp/test",
                    [{"namespace": "hashicorp", "name": "azurerm", "version": "4.39.0"}]
                )
                
                assert "terraform {" in config
                assert "required_providers {" in config
                assert "azurerm" in config
                assert "4.39.0" in config

    @pytest.mark.asyncio
    async def test_schema_path_querying(self, schema_provider):
        """Test schema path querying functionality."""
        test_schema = {
            "attributes": {
                "name": {"type": "string", "description": "Test name"},
                "nested": {
                    "inner": {"type": "number", "description": "Test number"}
                }
            }
        }
        
        # Test simple path
        result = schema_provider._query_schema_path(test_schema, "name")
        assert result["type"] == "string"
        
        # Test nested path
        result = schema_provider._query_schema_path(test_schema, "nested.inner")
        assert result["type"] == "number"
        
        # Test invalid path
        with pytest.raises(KeyError):
            schema_provider._query_schema_path(test_schema, "invalid.path")


def mock_open(read_data=""):
    """Helper function to create mock file objects."""
    mock = MagicMock()
    mock.return_value.__enter__ = mock
    mock.return_value.__exit__ = MagicMock()
    mock.return_value.read.return_value = read_data
    mock.return_value.write = MagicMock()
    return mock