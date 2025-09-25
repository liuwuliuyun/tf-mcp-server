"""
Example demonstrating how to use the Conftest AVM runner for Azure policy validation.
"""

import asyncio
import json
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tf_mcp_server.tools.conftest_avm_runner import get_conftest_avm_runner


async def main():
    """Main example function."""
    
    # Get the Conftest AVM runner
    runner = get_conftest_avm_runner()
    
    # Example Terraform HCL content
    example_hcl = '''
    # Configure the Azure Provider
    terraform {
      required_providers {
        azurerm = {
          source  = "hashicorp/azurerm"
          version = "~>3.0"
        }
      }
    }
    
    # Configure the Microsoft Azure Provider
    provider "azurerm" {
      features {}
    }
    
    # Create a resource group
    resource "azurerm_resource_group" "example" {
      name     = "example-rg"
      location = "West Europe"
      
      tags = {
        Environment = "Test"
      }
    }
    
    # Create a storage account (potentially insecure for demonstration)
    resource "azurerm_storage_account" "example" {
      name                     = "examplestorageacct"
      resource_group_name      = azurerm_resource_group.example.name
      location                 = azurerm_resource_group.example.location
      account_tier             = "Standard"
      account_replication_type = "LRS"
      
      # Potentially insecure configuration for demo
      allow_nested_items_to_be_public = true
      
      tags = {
        Environment = "Test"
      }
    }
    
    # Create a virtual network
    resource "azurerm_virtual_network" "example" {
      name                = "example-vnet"
      address_space       = ["10.0.0.0/16"]
      location            = azurerm_resource_group.example.location
      resource_group_name = azurerm_resource_group.example.name
      
      tags = {
        Environment = "Test"
      }
    }
    '''
    
    print("\n" + "="*60)
    print("Example 1: Validate with all AVM policies")
    print("="*60)
    
    try:
        result = await runner.validate_terraform_hcl_with_avm_policies(
            hcl_content=example_hcl,
            policy_set="all"
        )
        
        print(f"Validation Success: {result['success']}")
        print(f"Total Violations: {result['summary']['total_violations']}")
        print(f"Policy Set: {result['policy_set']}")
        
        if result['violations']:
            print("\nViolations found:")
            for i, violation in enumerate(result['violations'][:5], 1):  # Show first 5
                print(f"  {i}. [{violation['level'].upper()}] {violation['policy']}")
                print(f"     Message: {violation['message']}")
                if violation.get('metadata'):
                    print(f"     Metadata: {violation['metadata']}")
                print()
        else:
            print("✅ No violations found!")
            
    except Exception as e:
        print(f"❌ Error during validation: {e}")
    
    print("\n" + "="*60)
    print("Example 2: Validate with avmsec high severity policies only")
    print("="*60)
    
    try:
        result = await runner.validate_terraform_hcl_with_avm_policies(
            hcl_content=example_hcl,
            policy_set="avmsec",
            severity_filter="high"
        )
        
        print(f"Validation Success: {result['success']}")
        print(f"Total Violations: {result['summary']['total_violations']}")
        print(f"Policy Set: {result['policy_set']}")
        print(f"Severity Filter: {result['severity_filter']}")
        
        if result['violations']:
            print("\nHigh severity violations:")
            for i, violation in enumerate(result['violations'], 1):
                print(f"  {i}. [{violation['level'].upper()}] {violation['policy']}")
                print(f"     Message: {violation['message']}")
                print()
        else:
            print("✅ No high severity violations found!")
            
    except Exception as e:
        print(f"❌ Error during validation: {e}")
    
    # Example 4: Demonstrate workspace folder validation (simulated)
    print("\n" + "="*60)
    print("Example 4: Workspace Folder Validation (Simulated)")
    print("="*60)
    
    # Note: This would work if you have a real workspace folder with .tf files
    # In a real scenario, you might use this after running aztfexport
    workspace_folder_example = """
    # Example usage for workspace folder validation:
    
    # 1. After exporting resources with aztfexport:
    result = await runner.validate_workspace_folder_with_avm_policies(
        folder_name="exported-rg-myresources",  # Folder created by aztfexport
        policy_set="avmsec",
        severity_filter="high"
    )
    
    # 2. Validate existing workspace folder:
    result = await runner.validate_workspace_folder_with_avm_policies(
        folder_name="my-terraform-project",
        policy_set="all"
    )
    
    # 3. Validate plan files in workspace folder:
    result = await runner.validate_workspace_folder_plan_with_avm_policies(
        folder_name="exported-rg-myresources", 
        policy_set="Azure-Proactive-Resiliency-Library-v2"
    )
    """
    
    print("Workspace folder validation allows you to validate:")
    print("• Terraform files in folders created by aztfexport")
    print("• Existing workspace folders with .tf files")
    print("• Plan files in workspace directories")
    print()
    print("Example code:")
    print(workspace_folder_example)
    
    # Example 5: Demonstrate plan validation
    print("\n" + "="*60)
    print("Example 5: Plan JSON Validation")
    print("="*60)
    
    # Example plan JSON (minimal for demonstration)
    example_plan_json = '''
    {
      "format_version": "1.1",
      "terraform_version": "1.5.0",
      "planned_values": {
        "root_module": {
          "resources": [
            {
              "address": "azurerm_storage_account.example",
              "mode": "managed",
              "type": "azurerm_storage_account",
              "values": {
                "name": "examplestorage",
                "resource_group_name": "example-rg",
                "location": "West Europe",
                "account_tier": "Standard",
                "account_replication_type": "LRS",
                "allow_nested_items_to_be_public": true,
                "min_tls_version": "TLS1_0"
              }
            }
          ]
        }
      }
    }
    '''
    
    try:
        result = await runner.validate_with_avm_policies(
            terraform_plan_json=example_plan_json,
            policy_set="avmsec",
            severity_filter="medium"
        )
        
        print(f"Plan Validation Success: {result['success']}")
        print(f"Total Violations: {result['summary']['total_violations']}")
        print(f"Policy Set: {result['policy_set']}")
        
        if result['violations']:
            print("\nPlan validation violations:")
            for i, violation in enumerate(result['violations'], 1):
                print(f"  {i}. [{violation['level'].upper()}] {violation['policy']}")
                print(f"     Message: {violation['message']}")
                print()
        else:
            print("✅ No violations found in plan!")
            
    except Exception as e:
        print(f"❌ Error during plan validation: {e}")

    print("\n" + "="*60)
    print("Example 3: Validate with Azure Proactive Resiliency Library v2 only")
    print("="*60)
    
    try:
        result = await runner.validate_terraform_hcl_with_avm_policies(
            hcl_content=example_hcl,
            policy_set="Azure-Proactive-Resiliency-Library-v2"
        )
        
        print(f"Validation Success: {result['success']}")
        print(f"Total Violations: {result['summary']['total_violations']}")
        print(f"Policy Set: {result['policy_set']}")
        
        if result['violations']:
            print("\nResiliency violations:")
            for i, violation in enumerate(result['violations'], 1):
                print(f"  {i}. [{violation['level'].upper()}] {violation['policy']}")
                print(f"     Message: {violation['message']}")
                print()
        else:
            print("✅ No resiliency violations found!")
            
    except Exception as e:
        print(f"❌ Error during validation: {e}")
    
    # Example with a Terraform plan JSON (if you have one)
    print("\n" + "="*60)
    print("Example 4: Direct plan validation")
    print("="*60)
    
    example_plan_json = '''
    {
      "format_version": "1.1",
      "terraform_version": "1.0.0",
      "planned_values": {
        "root_module": {
          "resources": [
            {
              "address": "azurerm_storage_account.example",
              "mode": "managed",
              "type": "azurerm_storage_account",
              "name": "example",
              "values": {
                "account_tier": "Standard",
                "account_replication_type": "LRS",
                "allow_nested_items_to_be_public": true,
                "location": "West Europe",
                "name": "examplestorageacct"
              }
            }
          ]
        }
      }
    }
    '''
    
    try:
        result = await runner.validate_with_avm_policies(
            terraform_plan_json=example_plan_json,
            policy_set="avmsec"
        )
        
        print(f"Plan Validation Success: {result['success']}")
        print(f"Total Violations: {result['summary']['total_violations']}")
        
        if result['violations']:
            print("\nPlan violations:")
            for i, violation in enumerate(result['violations'], 1):
                print(f"  {i}. [{violation['level'].upper()}] {violation['policy']}")
                print(f"     Message: {violation['message']}")
                print()
        else:
            print("✅ No plan violations found!")
            
    except Exception as e:
        print(f"❌ Error during plan validation: {e}")
    
    print("\n" + "="*60)
    print("Examples completed!")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
