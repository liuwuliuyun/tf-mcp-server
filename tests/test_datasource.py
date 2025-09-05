#!/usr/bin/env python3
"""
Quick test script to verify data source documentation functionality.
"""

import asyncio
from tf_mcp_server.tools.azurerm_docs_provider import get_azurerm_documentation_provider

async def test_data_source_docs():
    """Test data source documentation retrieval."""
    provider = get_azurerm_documentation_provider()
    
    print("Testing virtual_machine data source...")
    result = await provider.search_azurerm_provider_docs(
        resource_type="virtual_machine",
        doc_type="data-source"
    )
    
    print(f"Resource Type: {result.resource_type}")
    print(f"Documentation URL: {result.documentation_url}")
    print(f"Summary: {result.summary}")
    print(f"Number of arguments: {len(result.arguments)}")
    print(f"Number of attributes: {len(result.attributes)}")
    print(f"Number of examples: {len(result.examples)}")
    
    if result.examples:
        print(f"\nFirst example:\n{result.examples[0]}")
    
    print("\n" + "="*50 + "\n")
    
    print("Testing virtual_machine_scale_set data source...")
    result2 = await provider.search_azurerm_provider_docs(
        resource_type="virtual_machine_scale_set",
        doc_type="data-source"
    )
    
    print(f"Resource Type: {result2.resource_type}")
    print(f"Documentation URL: {result2.documentation_url}")
    print(f"Summary: {result2.summary}")
    print(f"Number of arguments: {len(result2.arguments)}")
    print(f"Number of attributes: {len(result2.attributes)}")
    print(f"Number of examples: {len(result2.examples)}")
    
    if result2.examples:
        print(f"\nFirst example:\n{result2.examples[0]}")

if __name__ == "__main__":
    asyncio.run(test_data_source_docs())
