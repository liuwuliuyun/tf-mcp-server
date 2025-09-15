"""
Azure Resource Manager support checker for Terraform provider compatibility.

This module provides functionality to check if Azure resource types and their properties
are supported by the Terraform AzureRM provider by analyzing tf.json support data.
"""

import json
import logging
import os
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)


class AzureRMSupportChecker:
    """
    Service for checking Azure resource type and property support in Terraform AzureRM provider.
    """

    def __init__(self):
        """Initialize the AzureRM support checker."""
        self._tf_json_path = None

    def _get_tf_json_path(self) -> str:
        """Get the path to the tf.json support data file."""
        if self._tf_json_path is None:
            # Get the path relative to this module
            current_dir = os.path.dirname(__file__)
            core_dir = os.path.join(current_dir, "..", "core")
            self._tf_json_path = os.path.join(core_dir, "tf.json")
        return self._tf_json_path

    def _format_resource_type_from_api_path(self, api_path: str) -> str:
        """
        Format resource type from API path to standard Azure resource type format.

        Args:
            api_path: API path like "/SUBSCRIPTIONS/{}/RESOURCEGROUPS/{}/PROVIDERS/MICROSOFT.NETWORK/VIRTUALNETWORKS/{}/SUBNETS/{}"
                     or "/PROVIDERS/MICROSOFT.NETWORK/VIRTUALNETWORKS/{}/SUBNETS/{}"

        Returns:
            Formatted resource type like "microsoft.network/virtualnetworks/subnets" (all lowercase for case-insensitive matching)
        """
        # Find the last occurrence of "/PROVIDERS/" in the path
        upper_path = api_path.upper()
        providers_index = upper_path.rfind("/PROVIDERS/")

        if providers_index == -1:
            return ""

        # Extract everything after the last /PROVIDERS/
        providers_part = upper_path[providers_index + len("/PROVIDERS/"):]

        # Remove placeholders and clean up
        cleaned_path = providers_part.replace("{}", "").strip("/")

        # Split into parts and remove empty parts
        parts = [part for part in cleaned_path.split("/") if part]

        if not parts:
            return ""

        # Convert all parts to lowercase and join with '/'
        # This creates the resource type like "microsoft.network/virtualnetworks/subnets"
        return "/".join(part.lower() for part in parts)

    def _load_support_data(self) -> List[Dict[str, Any]]:
        """
        Load the tf.json support data and format it for efficient querying.

        This method pre-formats the data by:
        - Converting API paths to lowercase resource types (e.g. "microsoft.network/virtualnetworks/subnets")
        - Converting property addresses to dot notation (e.g. "properties.addressPrefix")

        Returns:
            List of support data entries with pre-formatted fields

        Raises:
            FileNotFoundError: If tf.json file is not found
            json.JSONDecodeError: If tf.json file contains invalid JSON
        """
        tf_json_path = self._get_tf_json_path()

        if not os.path.exists(tf_json_path):
            raise FileNotFoundError(f"tf.json support data file not found at {tf_json_path}")

        with open(tf_json_path, "r") as f:
            raw_data = json.load(f)

        # Format the data for efficient querying by overriding original fields
        for entry in raw_data:
            # Format resource type from API path and override api_path
            if "api_path" in entry:
                entry["api_path"] = self._format_resource_type_from_api_path(entry["api_path"])

            # Format property paths and override addr fields
            if "properties" in entry:
                for prop in entry["properties"]:
                    if "addr" in prop:
                        # Convert slash notation to dot notation for property paths
                        prop["addr"] = prop["addr"].replace("/", ".")

        return raw_data

    def _find_matching_entries(
        self, support_data: List[Dict[str, Any]], resource_type: str
    ) -> List[Dict[str, Any]]:
        """
        Find entries in support data that match the resource type.

        Args:
            support_data: List of support data entries from tf.json (with pre-formatted api_path)
            resource_type: Resource type to match against (e.g., "Microsoft.Network/virtualNetworks/subnets")

        Returns:
            List of matching entries
        """
        matching_entries = []
        resource_type_lower = resource_type.lower()

        for entry in support_data:
            if "api_path" in entry:
                api_path_lower = entry["api_path"].lower()

                # Case-insensitive exact match
                if resource_type_lower == api_path_lower:
                    matching_entries.append(entry)

        return matching_entries

    def _extract_azurerm_mappings(self, prop: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract azurerm mappings from a property definition.

        Args:
            prop: Property definition from tf.json

        Returns:
            List of azurerm mappings
        """
        azurerm_mappings = []

        if "app_property_maps" in prop:
            for mapping in prop["app_property_maps"]:
                if "name" in mapping and mapping["name"].startswith("azurerm_"):
                    # Clean up the azurerm_property path (remove leading slash)
                    azurerm_property = mapping.get("addr", "")
                    if azurerm_property.startswith("/"):
                        azurerm_property = azurerm_property[1:]

                    # Avoid duplicates by checking if this mapping already exists
                    mapping_exists = any(
                        m["azurerm_resource"] == mapping["name"]
                        and m["azurerm_property"] == azurerm_property
                        for m in azurerm_mappings
                    )

                    if not mapping_exists:
                        azurerm_mappings.append(
                            {
                                "azurerm_resource": mapping["name"],
                                "azurerm_property": azurerm_property,
                                "api_property": prop["addr"],
                            }
                        )

        return azurerm_mappings

    def _check_property_support(
        self, matching_entries: List[Dict[str, Any]], property_path: str
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Check if a property path is supported in the matching entries.

        Args:
            matching_entries: List of matching support data entries (with pre-formatted addr fields)
            property_path: Property path to check

        Returns:
            Tuple of (property_found, azurerm_mappings)
        """
        property_found = False
        azurerm_mappings = []

        # Normalize user input to dot notation
        property_path_dot = property_path.replace("/", ".")
        property_path_lower = property_path_dot.lower()

        for entry in matching_entries:
            if "properties" in entry:
                for prop in entry["properties"]:
                    if "addr" in prop:
                        # Case-insensitive exact match using pre-formatted dot notation
                        addr_lower = prop["addr"].lower()

                        if property_path_lower == addr_lower:
                            property_found = True

                            # Extract azurerm mappings
                            mappings = self._extract_azurerm_mappings(prop)
                            azurerm_mappings.extend(mappings)
                            break  # Found the property, no need to continue with this entry

                if property_found:
                    break  # Found the property, no need to continue with other entries

        return property_found, azurerm_mappings

    async def check_azurerm_resource_support(
        self, resource_type: str, property_path: str
    ) -> Dict[str, Any]:
        """
        Check if a specific Azure resource type and property path is supported by the Terraform AzureRM provider.

        Args:
            resource_type: The Azure resource type to check (e.g., 'Microsoft.Compute/virtualMachines')
            property_path: The property path within the resource to verify support for (e.g., 'properties.storageProfile.osDisk.caching')

        Returns:
            JSON object indicating whether the resource type and property path are supported
        """
        try:
            # Load pre-formatted support data
            support_data = self._load_support_data()

            # Find matching entries using pre-formatted resource types
            matching_entries = self._find_matching_entries(support_data, resource_type)

            if not matching_entries:
                return {
                    "resource_type": resource_type,
                    "property_path": property_path,
                    "is_supported": False,
                    "provider": "azurerm",
                    "status": "resource_not_found",
                    "message": f"No Terraform AzureRM provider support found for resource type {resource_type}",
                }

            # Check for property path support using pre-formatted property paths
            property_found, azurerm_mappings = self._check_property_support(
                matching_entries, property_path
            )

            is_supported = property_found and len(azurerm_mappings) > 0

            result = {
                "resource_type": resource_type,
                "property_path": property_path,
                "is_supported": is_supported,
                "provider": "azurerm",
                "status": "success",
            }

            if property_found:
                result["message"] = f"Property path '{property_path}' found in API definition"
                if azurerm_mappings:
                    result["azurerm_mappings"] = azurerm_mappings
                    result["message"] += f" with {len(azurerm_mappings)} azurerm mapping(s)"
                else:
                    result["message"] += " but no azurerm mappings available"
            else:
                result["message"] = (
                    f"Property path '{property_path}' not found in {resource_type} API definition"
                )

            # Add some additional context
            result["api_entries_found"] = len(matching_entries)

            return result

        except FileNotFoundError as e:
            logger.error(f"tf.json support data file not found: {e}")
            return {
                "resource_type": resource_type,
                "property_path": property_path,
                "is_supported": False,
                "provider": "azurerm",
                "error": "tf.json support data file not found",
                "status": "error",
            }
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in tf.json support data file: {e}")
            return {
                "resource_type": resource_type,
                "property_path": property_path,
                "is_supported": False,
                "provider": "azurerm",
                "error": f"Failed to check resource support: Invalid JSON in tf.json support data file",
                "status": "error",
            }
        except Exception as e:
            logger.error(f"Error checking azurerm resource support: {e}")
            return {
                "resource_type": resource_type,
                "property_path": property_path,
                "is_supported": False,
                "provider": "azurerm",
                "error": f"Failed to check resource support: {str(e)}",
                "status": "error",
            }


# Singleton instance
_azurerm_support_checker = None


def get_azurerm_support_checker() -> AzureRMSupportChecker:
    """
    Get the singleton instance of AzureRMSupportChecker.

    Returns:
        AzureRMSupportChecker instance
    """
    global _azurerm_support_checker
    if _azurerm_support_checker is None:
        _azurerm_support_checker = AzureRMSupportChecker()
    return _azurerm_support_checker
