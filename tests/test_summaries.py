#!/usr/bin/env python3
"""
Test both resource and data source summaries.
"""

import asyncio
from tf_mcp_server.tools.azurerm_docs_provider import get_azurerm_documentation_provider

async def test_summaries():
    """Test both resource and data source summary generation."""
    provider = get_azurerm_documentation_provider()
    
    print("Testing storage_account RESOURCE...")
    result1 = await provider.search_azurerm_provider_docs(
        resource_type="storage_account",
        doc_type="resource"
    )
    print(f"Resource Summary: {result1.summary}")
    
    print("\nTesting storage_account DATA SOURCE...")
    result2 = await provider.search_azurerm_provider_docs(
        resource_type="storage_account",
        doc_type="data-source"
    )
    print(f"Data Source Summary: {result2.summary}")

if __name__ == "__main__":
    asyncio.run(test_summaries())
