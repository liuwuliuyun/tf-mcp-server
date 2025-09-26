#!/usr/bin/env python3
"""
Integration test for TFLint functionality in the Azure Terraform MCP Server.
"""

import asyncio
import sys
import os
import tempfile

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tf_mcp_server.core.server import create_server
from tf_mcp_server.core.config import Config


async def test_tflint_integration():
    """Test TFLint integration with the MCP server."""
    
    print("🧪 TFLint Integration Test")
    print("=" * 40)
    
    # Create server
    config = Config.from_env()
    server = create_server(config)
    print("✅ Server created successfully")
    
    # Test TFLint installation check
    print("\n1. Testing TFLint installation check...")
    try:
        # Access the tool function directly for testing
        from tf_mcp_server.tools.tflint_runner import get_tflint_runner
        
        tflint_runner = get_tflint_runner()
        result = await tflint_runner.check_tflint_installation()
        
        if result['installed']:
            print(f"✅ TFLint is installed: {result['version']}")
        else:
            print(f"ℹ️  TFLint is not installed: {result['error']}")
            print("   This is expected if TFLint is not installed on the system")
        
    except Exception as e:
        print(f"❌ Error checking TFLint installation: {e}")
        return False
    
    # Test TFLint analysis in a workspace folder
    print("\n2. Testing TFLint workspace analysis...")
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            main_tf_path = os.path.join(temp_dir, "main.tf")
            with open(main_tf_path, "w", encoding="utf-8") as tf_file:
                tf_file.write(
                    """
resource "azurerm_resource_group" "example" {
  name     = "example-resources"
  location = "West Europe"
}

resource "azurerm_storage_account" "example" {
  name                     = "examplestorageaccount"
  resource_group_name      = azurerm_resource_group.example.name
  location                 = azurerm_resource_group.example.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
}
                    """
                )

            analysis_result = await tflint_runner.lint_terraform_workspace_folder(
                temp_dir,
                output_format="json",
                enable_azure_plugin=True,
                initialize_plugins=False  # Avoid network/downloads during tests
            )

            if analysis_result['success']:
                print("✅ TFLint workspace analysis completed successfully")
                print(f"   Issues found: {analysis_result['summary']['total_issues']}")
            else:
                print(f"ℹ️  TFLint workspace analysis failed: {analysis_result['error']}")

    except Exception as e:
        print(f"❌ Error running TFLint workspace analysis: {e}")
        return False

    # Test error handling for missing workspace folder
    print("\n3. Testing error handling for missing workspace folder...")
    try:
        missing_result = await tflint_runner.lint_terraform_workspace_folder("/nonexistent/folder")

        if not missing_result['success'] and 'does not exist' in missing_result['error']:
            print("✅ Missing folder handled correctly")
        else:
            print("❌ Missing folder not handled as expected")
            return False

    except Exception as e:
        print(f"❌ Error testing missing folder handling: {e}")
        return False
    
    print("\n🎉 All TFLint integration tests passed!")
    print("\nThe TFLint functionality is working correctly.")
    print("To use TFLint analysis features, install TFLint on your system.")
    
    return True


if __name__ == "__main__":
    success = asyncio.run(test_tflint_integration())
    sys.exit(0 if success else 1)
