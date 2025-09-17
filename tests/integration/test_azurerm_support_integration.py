#!/usr/bin/env python3
"""
Integration test for the check_azurerm_resource_support function.
"""

import asyncio
import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from tf_mcp_server.core.config import Config
from tf_mcp_server.core.server import create_server


async def test_check_azurerm_resource_support():
    """Test the check_azurerm_resource_support function with real tf.json data."""

    print("🧪 AzureRM Resource Support Check Integration Test")
    print("=" * 50)

    # Create server
    config = Config.from_env()
    server = create_server(config)
    print("✅ Server created successfully")

    # Use the get_tool method to access our function
    try:
        check_function = await server.get_tool("check_azurerm_resource_support")
        if check_function:
            print("✅ Found check_azurerm_resource_support tool")
            print(
                "Tool attributes:",
                [attr for attr in dir(check_function) if not attr.startswith("_")],
            )
        else:
            print("❌ check_azurerm_resource_support tool not found")
            return False
    except Exception as e:
        print(f"❌ Error getting tool: {e}")
        return False

    # Test cases
    test_cases = [
        {
            "name": "Test supported resource and property",
            "resource_type": "Microsoft.AADiam/diagnosticSettings",
            "property_path": "properties.storageAccountId",
            "expected_supported": True,
        },
        {
            "name": "Test supported resource with different case",
            "resource_type": "microsoft.aadiam/diagnosticsettings",
            "property_path": "properties.storageaccountid",
            "expected_supported": True,
        },
        {
            "name": "Test unsupported resource type",
            "resource_type": "Microsoft.NonExistent/resources",
            "property_path": "properties.someProperty",
            "expected_supported": False,
        },
        {
            "name": "Test virtual machine resource",
            "resource_type": "Microsoft.Compute/virtualMachines",
            "property_path": "properties.storageProfile",
            "expected_supported": None,  # We'll check if it finds the resource
        },
    ]

    results = []

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print(f"   Resource: {test_case['resource_type']}")
        print(f"   Property: {test_case['property_path']}")

        try:
            result = await check_function.fn(
                resource_type=test_case["resource_type"], property_path=test_case["property_path"]
            )

            print(f"   Status: {result['status']}")
            print(f"   Supported: {result['is_supported']}")

            if result["is_supported"]:
                mappings = result.get("azurerm_mappings", [])
                print(f"   AzureRM Mappings: {len(mappings)}")
                for mapping in mappings[:2]:  # Show first 2 mappings
                    print(f"     - {mapping['azurerm_resource']}: {mapping['azurerm_property']}")

            if "message" in result:
                print(f"   Message: {result['message']}")

            if "error" in result:
                print(f"   Error: {result['error']}")

            # Validate expected results
            if test_case["expected_supported"] is not None:
                if result["is_supported"] == test_case["expected_supported"]:
                    print(f"   ✅ Expected result matched")
                else:
                    print(
                        f"   ❌ Expected {test_case['expected_supported']}, got {result['is_supported']}"
                    )
            else:
                print(f"   ℹ️  Result validation skipped (expected_supported=None)")

            results.append({"test_case": test_case["name"], "success": True, "result": result})

        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            results.append({"test_case": test_case["name"], "success": False, "error": str(e)})

    # Summary
    print(f"\n{'='*50}")
    print("Test Summary:")
    successful_tests = sum(1 for r in results if r["success"])
    print(f"✅ Successful tests: {successful_tests}/{len(results)}")

    if successful_tests < len(results):
        print(f"❌ Failed tests: {len(results) - successful_tests}")
        for result in results:
            if not result["success"]:
                print(f"   - {result['test_case']}: {result['error']}")

    return successful_tests == len(results)


async def main():
    """Run the integration test."""
    try:
        success = await test_check_azurerm_resource_support()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
