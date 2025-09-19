#!/usr/bin/env python3
"""
Example usage of Azure Export for Terraform (aztfexport) integration in the Azure Terraform MCP Server.

This example demonstrates how to use the integrated aztfexport functionality to export
existing Azure resources to Terraform configuration and state.
"""

import asyncio
import json
from tf_mcp_server.tools.aztfexport_runner import get_aztfexport_runner, AztfexportProvider


async def main():
    """Main example function demonstrating aztfexport integration."""
    
    # Get the aztfexport runner instance
    runner = get_aztfexport_runner()
    
    print("=== Azure Export for Terraform (aztfexport) Integration Example ===\n")
    
    # 1. Check if aztfexport is installed
    print("1. Checking aztfexport installation...")
    installation_status = await runner.check_installation()
    print(json.dumps(installation_status, indent=2))
    
    if not installation_status.get('installed', False):
        print("\n❌ aztfexport is not installed. Please install it first.")
        print("Installation options:")
        help_info = installation_status.get('installation_help', {})
        for platform, command in help_info.items():
            print(f"  {platform}: {command}")
        return
    
    print(f"\n✅ aztfexport is installed: {installation_status.get('aztfexport_version', 'Unknown version')}")
    
    # 2. Example: Export a single resource (storage account)
    print("\n2. Example: Export a single Azure resource")
    print("   Note: Replace this with an actual Azure resource ID from your subscription")
    
    example_resource_id = "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/example-rg/providers/Microsoft.Storage/storageAccounts/examplestorageacct"
    
    print(f"   Resource ID: {example_resource_id}")
    print("   Running dry-run export...")
    
    try:
        resource_result = await runner.export_resource(
            resource_id=example_resource_id,
            provider=AztfexportProvider.AZURERM,
            dry_run=True,  # Use dry-run to avoid creating actual files
            continue_on_error=True
        )
        
        print(f"   Exit code: {resource_result.get('exit_code', 'N/A')}")
        print(f"   Success: {resource_result.get('success', False)}")
        
        if resource_result.get('success'):
            print("   ✅ Resource export completed successfully")
            generated_files = resource_result.get('generated_files', {})
            if generated_files:
                print(f"   Generated {len(generated_files)} file(s):")
                for filename in generated_files.keys():
                    print(f"     - {filename}")
        else:
            print(f"   ❌ Resource export failed: {resource_result.get('stderr', 'Unknown error')}")
            
    except Exception as e:
        print(f"   ❌ Error during resource export: {e}")
    
    # 3. Example: Export a resource group
    print("\n3. Example: Export a resource group")
    print("   Note: Replace this with an actual resource group name from your subscription")
    
    example_rg_name = "example-resource-group"
    
    print(f"   Resource Group: {example_rg_name}")
    print("   Running dry-run export...")
    
    try:
        rg_result = await runner.export_resource_group(
            resource_group_name=example_rg_name,
            provider=AztfexportProvider.AZURERM,
            dry_run=True,  # Use dry-run to avoid creating actual files
            parallelism=5,
            continue_on_error=True
        )
        
        print(f"   Exit code: {rg_result.get('exit_code', 'N/A')}")
        print(f"   Success: {rg_result.get('success', False)}")
        
        if rg_result.get('success'):
            print("   ✅ Resource group export completed successfully")
            generated_files = rg_result.get('generated_files', {})
            if generated_files:
                print(f"   Generated {len(generated_files)} file(s):")
                for filename in generated_files.keys():
                    print(f"     - {filename}")
        else:
            print(f"   ❌ Resource group export failed: {rg_result.get('stderr', 'Unknown error')}")
            
    except Exception as e:
        print(f"   ❌ Error during resource group export: {e}")
    
    # 4. Example: Export using Azure Resource Graph query
    print("\n4. Example: Export using Azure Resource Graph query")
    print("   Query: Export all storage accounts in East US region")
    
    example_query = "type =~ 'Microsoft.Storage/storageAccounts' and location == 'eastus'"
    
    print(f"   Query: {example_query}")
    print("   Running dry-run export...")
    
    try:
        query_result = await runner.export_query(
            query=example_query,
            provider=AztfexportProvider.AZURERM,
            dry_run=True,  # Use dry-run to avoid creating actual files
            parallelism=3,
            continue_on_error=True
        )
        
        print(f"   Exit code: {query_result.get('exit_code', 'N/A')}")
        print(f"   Success: {query_result.get('success', False)}")
        
        if query_result.get('success'):
            print("   ✅ Query export completed successfully")
            generated_files = query_result.get('generated_files', {})
            if generated_files:
                print(f"   Generated {len(generated_files)} file(s):")
                for filename in generated_files.keys():
                    print(f"     - {filename}")
        else:
            print(f"   ❌ Query export failed: {query_result.get('stderr', 'Unknown error')}")
            
    except Exception as e:
        print(f"   ❌ Error during query export: {e}")
    
    # 5. Check current configuration
    print("\n5. Checking aztfexport configuration...")
    
    try:
        config_result = await runner.get_config()
        
        if config_result.get('success'):
            print("   ✅ Configuration retrieved successfully:")
            config_data = config_result.get('config', {})
            if isinstance(config_data, dict):
                for key, value in config_data.items():
                    print(f"     {key}: {value}")
            else:
                print(f"     {config_data}")
        else:
            print(f"   ❌ Failed to get configuration: {config_result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"   ❌ Error getting configuration: {e}")
    
    print("\n=== Example completed ===")
    print("\nNext steps:")
    print("1. Install aztfexport if not already installed")
    print("2. Configure Azure Service Principal credentials (ARM_CLIENT_ID, ARM_CLIENT_SECRET, etc.)")
    print("3. Replace example resource IDs/names with actual Azure resources")
    print("4. Remove dry_run=True to generate actual Terraform files")
    print("5. Review and customize the generated Terraform configuration")


if __name__ == "__main__":
    asyncio.run(main())