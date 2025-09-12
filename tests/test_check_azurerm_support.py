"""
Test cases for the server module, focusing on the check_azurerm_resource_support function.
"""

import json
import os
import tempfile
from unittest.mock import mock_open, patch

import pytest

from tf_mcp_server.core.config import Config
from tf_mcp_server.core.server import create_server


@pytest.fixture
def sample_tf_json_data():
    """Sample tf.json data for testing."""
    return [
        {
            "api_version": "2017-04-01",
            "api_path": "/PROVIDERS/MICROSOFT.AADIAM/DIAGNOSTICSETTINGS/{}",
            "operation": "PUT",
            "properties": [
                {
                    "addr": "properties/eventHubAuthorizationRuleId",
                    "app_property_maps": [
                        {
                            "name": "azurerm_monitor_aad_diagnostic_setting",
                            "addr": "/eventhub_authorization_rule_id",
                        }
                    ],
                },
                {
                    "addr": "properties/storageAccountId",
                    "app_property_maps": [
                        {
                            "name": "azurerm_monitor_aad_diagnostic_setting",
                            "addr": "/storage_account_id",
                        }
                    ],
                },
                {
                    "addr": "properties/workspaceId",
                    "app_property_maps": [
                        {
                            "name": "azurerm_monitor_aad_diagnostic_setting",
                            "addr": "/log_analytics_workspace_id",
                        }
                    ],
                },
            ],
        },
        {
            "api_version": "2021-01-01",
            "api_path": "/PROVIDERS/MICROSOFT.COMPUTE/VIRTUALMACHINES/{}",
            "operation": "PUT",
            "properties": [
                {
                    "addr": "properties/storageProfile/osDisk/caching",
                    "app_property_maps": [
                        {"name": "azurerm_virtual_machine", "addr": "/storage_os_disk/caching"}
                    ],
                },
                {
                    "addr": "properties/hardwareProfile/vmSize"
                    # Note: No app_property_maps for this property
                },
            ],
        },
        {
            "api_version": "2020-06-01",
            "api_path": "/PROVIDERS/MICROSOFT.NETWORK/VIRTUALNETWORKS/{}/SUBNETS/{}",
            "operation": "PUT",
            "properties": [
                {
                    "addr": "properties/addressPrefix",
                    "app_property_maps": [{"name": "azurerm_subnet", "addr": "/address_prefix"}],
                },
                {
                    "addr": "properties/networkSecurityGroup/id",
                    "app_property_maps": [
                        {"name": "azurerm_subnet", "addr": "/network_security_group_id"}
                    ],
                },
                {
                    "addr": "properties/serviceEndpoints",
                    "app_property_maps": [{"name": "azurerm_subnet", "addr": "/service_endpoints"}],
                },
                {
                    "addr": "properties/delegations"
                    # Note: No app_property_maps for this property
                },
            ],
        },
        {
            "api_version": "2021-01-01",
            "api_path": "/PROVIDERS/MICROSOFT.STORAGE/STORAGEACCOUNTS/{}",
            "operation": "PUT",
            "properties": [
                {
                    "addr": "properties/encryption/services/blob/enabled",
                    "app_property_maps": [
                        {"name": "azurerm_storage_account", "addr": "/blob_encryption_enabled"},
                        {"name": "azurerm_storage_account_v2", "addr": "/encryption/blob/enabled"},
                    ],
                }
            ],
        },
    ]


@pytest.fixture
def mock_tf_json_file(sample_tf_json_data):
    """Mock the tf.json file reading throughout test execution."""
    tf_json_content = json.dumps(sample_tf_json_data)

    with patch("builtins.open", mock_open(read_data=tf_json_content)) as mock_file:
        with patch("os.path.exists", return_value=True):
            yield mock_file


@pytest.fixture
def server_with_mock_tf_json(test_config, mock_tf_json_file):
    """Create a server with mocked tf.json data."""
    server = create_server(test_config)
    return server


class TestCheckAzurermResourceSupport:
    """Test cases for the check_azurerm_resource_support function."""

    @pytest.mark.asyncio
    async def test_supported_resource_and_property(self, server_with_mock_tf_json):
        """Test a supported resource type and property path."""
        # Get the tool function
        check_tool = await server_with_mock_tf_json.get_tool("check_azurerm_resource_support")

        assert check_tool is not None, "check_azurerm_resource_support tool not found"

        # Test the function
        result = await check_tool.fn(
            resource_type="Microsoft.AADiam/diagnosticSettings",
            property_path="properties.storageAccountId",
        )

        assert result["is_supported"] is True
        assert result["resource_type"] == "Microsoft.AADiam/diagnosticSettings"
        assert result["property_path"] == "properties.storageAccountId"
        assert result["provider"] == "azurerm"
        assert result["status"] == "success"
        assert len(result["azurerm_mappings"]) == 1  # Only one entry in test data
        assert (
            result["azurerm_mappings"][0]["azurerm_resource"]
            == "azurerm_monitor_aad_diagnostic_setting"
        )
        assert result["azurerm_mappings"][0]["azurerm_property"] == "storage_account_id"

    @pytest.mark.asyncio
    async def test_property_without_azurerm_mapping(self, server_with_mock_tf_json):
        """Test a property that exists in API but has no azurerm mapping."""
        check_tool = await server_with_mock_tf_json.get_tool("check_azurerm_resource_support")

        result = await check_tool.fn(
            resource_type="Microsoft.Compute/virtualMachines",
            property_path="properties.hardwareProfile.vmSize",
        )

        assert result["is_supported"] is False
        assert result["property_path"] == "properties.hardwareProfile.vmSize"
        assert "azurerm_mappings" not in result or len(result.get("azurerm_mappings", [])) == 0
        assert "but no azurerm mappings available" in result["message"]

    @pytest.mark.asyncio
    async def test_unsupported_resource_type(self, server_with_mock_tf_json):
        """Test an unsupported resource type."""
        check_tool = await server_with_mock_tf_json.get_tool("check_azurerm_resource_support")

        result = await check_tool.fn(
            resource_type="Microsoft.NonExistent/resources", property_path="properties.someProperty"
        )

        assert result["is_supported"] is False
        assert result["status"] == "resource_not_found"
        assert "No Terraform AzureRM provider support found" in result["message"]

    @pytest.mark.asyncio
    async def test_unsupported_property_path(self, server_with_mock_tf_json):
        """Test a supported resource type with unsupported property path."""
        check_tool = await server_with_mock_tf_json.get_tool("check_azurerm_resource_support")

        result = await check_tool.fn(
            resource_type="Microsoft.AADiam/diagnosticSettings",
            property_path="properties.nonExistentProperty",
        )

        assert result["is_supported"] is False
        assert "not found in" in result["message"]
        assert result["api_entries_found"] > 0  # Resource was found, but not the property

    @pytest.mark.asyncio
    async def test_case_insensitive_matching(self, server_with_mock_tf_json):
        """Test that matching is case-insensitive."""
        check_tool = await server_with_mock_tf_json.get_tool("check_azurerm_resource_support")

        # Test with different case variations
        result = await check_tool.fn(
            resource_type="microsoft.aadiam/diagnosticsettings",
            property_path="PROPERTIES.STORAGEACCOUNTID",
        )

        assert result["is_supported"] is True
        assert len(result["azurerm_mappings"]) == 1

    @pytest.mark.asyncio
    async def test_subnet_nested_resource_support(self, server_with_mock_tf_json):
        """Test support for subnet nested resource with various properties."""
        check_tool = await server_with_mock_tf_json.get_tool("check_azurerm_resource_support")

        # Test subnet address prefix property
        result = await check_tool.fn(
            resource_type="Microsoft.Network/virtualNetworks/subnets",
            property_path="properties.addressPrefix",
        )

        assert result["is_supported"] is True
        assert result["resource_type"] == "Microsoft.Network/virtualNetworks/subnets"
        assert result["property_path"] == "properties.addressPrefix"
        assert result["provider"] == "azurerm"
        assert len(result["azurerm_mappings"]) == 1
        assert result["azurerm_mappings"][0]["azurerm_resource"] == "azurerm_subnet"
        assert result["azurerm_mappings"][0]["azurerm_property"] == "address_prefix"

        # Test subnet network security group property
        result = await check_tool.fn(
            resource_type="Microsoft.Network/virtualNetworks/subnets",
            property_path="properties.networkSecurityGroup.id",
        )

        assert result["is_supported"] is True
        assert result["azurerm_mappings"][0]["azurerm_resource"] == "azurerm_subnet"
        assert result["azurerm_mappings"][0]["azurerm_property"] == "network_security_group_id"

        # Test subnet service endpoints property
        result = await check_tool.fn(
            resource_type="Microsoft.Network/virtualNetworks/subnets",
            property_path="properties.serviceEndpoints",
        )

        assert result["is_supported"] is True
        assert result["azurerm_mappings"][0]["azurerm_resource"] == "azurerm_subnet"
        assert result["azurerm_mappings"][0]["azurerm_property"] == "service_endpoints"

        # Test subnet property without azurerm mapping
        result = await check_tool.fn(
            resource_type="Microsoft.Network/virtualNetworks/subnets",
            property_path="properties.delegations",
        )

        assert result["is_supported"] is False
        assert "but no azurerm mappings available" in result["message"]

    @pytest.mark.asyncio
    async def test_tf_json_file_not_found(self, test_config):
        """Test behavior when tf.json file is not found."""
        with patch("os.path.exists", return_value=False):
            server = create_server(test_config)

            check_tool = await server.get_tool("check_azurerm_resource_support")

            result = await check_tool.fn(
                resource_type="Microsoft.AADiam/diagnosticSettings",
                property_path="properties.storageAccountId",
            )

            assert result["is_supported"] is False
            assert result["status"] == "error"
            assert "tf.json support data file not found" in result["error"]

    @pytest.mark.asyncio
    async def test_invalid_json_file(self, test_config):
        """Test behavior when tf.json file contains invalid JSON."""
        with patch("builtins.open", mock_open(read_data="invalid json")):
            with patch("os.path.exists", return_value=True):
                server = create_server(test_config)

                check_tool = await server.get_tool("check_azurerm_resource_support")

                result = await check_tool.fn(
                    resource_type="Microsoft.AADiam/diagnosticSettings",
                    property_path="properties.storageAccountId",
                )

                assert result["is_supported"] is False
                assert result["status"] == "error"
                assert "Failed to check resource support" in result["error"]

    @pytest.mark.asyncio
    async def test_multiple_azurerm_mappings(self, server_with_mock_tf_json):
        """Test a property with multiple azurerm mappings."""
        check_tool = await server_with_mock_tf_json.get_tool("check_azurerm_resource_support")

        result = await check_tool.fn(
            resource_type="Microsoft.Storage/storageAccounts",
            property_path="properties.encryption.services.blob.enabled",
        )

        assert result["is_supported"] is True
        assert len(result["azurerm_mappings"]) == 2
        assert any(
            mapping["azurerm_resource"] == "azurerm_storage_account"
            for mapping in result["azurerm_mappings"]
        )
        assert any(
            mapping["azurerm_resource"] == "azurerm_storage_account_v2"
            for mapping in result["azurerm_mappings"]
        )

    @pytest.mark.asyncio
    async def test_partial_property_path_match(self, server_with_mock_tf_json):
        """Test partial property path matching - should NOT match incomplete paths."""
        check_tool = await server_with_mock_tf_json.get_tool("check_azurerm_resource_support")

        # Test with partial path that should NOT match (missing 'properties.' prefix)
        result = await check_tool.fn(
            resource_type="Microsoft.Compute/virtualMachines",
            property_path="storageProfile.osDisk.caching",
        )

        assert result["is_supported"] is False
        assert "not found in" in result["message"]

    @pytest.mark.asyncio
    async def test_nested_resource_support(self, server_with_mock_tf_json):
        """Test support for nested resources like subnets."""
        check_tool = await server_with_mock_tf_json.get_tool("check_azurerm_resource_support")

        # Test nested resource with supported property
        result = await check_tool.fn(
            resource_type="Microsoft.Network/virtualNetworks/subnets",
            property_path="properties.addressPrefix",
        )

        assert result["is_supported"] is True
        assert result["resource_type"] == "Microsoft.Network/virtualNetworks/subnets"
        assert result["property_path"] == "properties.addressPrefix"
        assert result["provider"] == "azurerm"
        assert len(result["azurerm_mappings"]) == 1
        assert result["azurerm_mappings"][0]["azurerm_resource"] == "azurerm_subnet"
        assert result["azurerm_mappings"][0]["azurerm_property"] == "address_prefix"

    @pytest.mark.asyncio
    async def test_nested_resource_complex_property(self, server_with_mock_tf_json):
        """Test nested resource with complex property path."""
        check_tool = await server_with_mock_tf_json.get_tool("check_azurerm_resource_support")

        # Test nested resource with network security group property
        result = await check_tool.fn(
            resource_type="Microsoft.Network/virtualNetworks/subnets",
            property_path="properties.networkSecurityGroup.id",
        )

        assert result["is_supported"] is True
        assert result["azurerm_mappings"][0]["azurerm_resource"] == "azurerm_subnet"
        assert result["azurerm_mappings"][0]["azurerm_property"] == "network_security_group_id"

    @pytest.mark.asyncio
    async def test_nested_resource_unsupported_property(self, server_with_mock_tf_json):
        """Test nested resource with property that has no azurerm mapping."""
        check_tool = await server_with_mock_tf_json.get_tool("check_azurerm_resource_support")

        # Test property without azurerm mapping
        result = await check_tool.fn(
            resource_type="Microsoft.Network/virtualNetworks/subnets",
            property_path="properties.delegations",
        )

        assert result["is_supported"] is False
        assert "but no azurerm mappings available" in result["message"]
