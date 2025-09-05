#!/usr/bin/env python3
"""
Test script to verify detailed attribute information.
"""

import asyncio
from tf_mcp_server.tools.azurerm_docs_provider import get_azurerm_documentation_provider

async def test_detailed_attributes():
    """Test detailed attribute information."""
    provider = get_azurerm_documentation_provider()
    
    print("Testing virtual_machine data source attributes...")
    result = await provider.search_azurerm_provider_docs(
        resource_type="virtual_machine",
        doc_type="data-source"
    )
    
    print(f"Resource Type: {result.resource_type}")
    print(f"Total attributes: {len(result.attributes)}")
    print("\nAttribute details:")
    for i, attr in enumerate(result.attributes, 1):
        print(f"  {i}. {attr['name']}: {attr['description']}")
    
    # Verify expected attributes
    expected_attrs = [
        'id', 'location', 'size', 'admin_username', 
        'network_interface_ids', 'os_disk', 'storage_data_disk', 'identity'
    ]
    
    found_attrs = [attr['name'] for attr in result.attributes]
    print(f"\nExpected attributes: {expected_attrs}")
    print(f"Found attributes: {found_attrs}")
    
    missing = set(expected_attrs) - set(found_attrs)
    extra = set(found_attrs) - set(expected_attrs)
    
    if missing:
        print(f"Missing attributes: {missing}")
    if extra:
        print(f"Extra attributes: {extra}")
    
    if not missing and not extra:
        print("✅ All expected attributes are present!")

if __name__ == "__main__":
    asyncio.run(test_detailed_attributes())
