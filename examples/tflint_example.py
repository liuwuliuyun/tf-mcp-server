#!/usr/bin/env python3
"""
Example script demonstrating TFLint integration with the Azure Terraform MCP Server.
"""

import asyncio
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tf_mcp_server.tools.tflint_runner import get_tflint_runner


async def main():
    """Main example function."""
    
    # Sample Terraform configuration with potential issues
    sample_hcl = '''
# Example Azure resources with some best practice violations
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
  
  # Missing: min_tls_version, enable_https_traffic_only, etc.
}

resource "azurerm_virtual_network" "example" {
  name                = "example-network"
  address_space       = ["10.0.0.0/16"]
  location            = azurerm_resource_group.example.location
  resource_group_name = azurerm_resource_group.example.name
}

resource "azurerm_subnet" "example" {
  name                 = "internal"
  resource_group_name  = azurerm_resource_group.example.name
  virtual_network_name = azurerm_virtual_network.example.name
  address_prefixes     = ["10.0.2.0/24"]
}
'''
    
    print("🔍 TFLint Integration Example")
    print("=" * 50)
    
    # Get TFLint runner instance
    tflint_runner = get_tflint_runner()
    
    # Check if TFLint is installed
    print("\n1. Checking TFLint installation...")
    installation_status = await tflint_runner.check_tflint_installation()
    
    if installation_status['installed']:
        print(f"✅ TFLint is installed: {installation_status['version']}")
        print(f"   Executable path: {installation_status['executable_path']}")
    else:
        print(f"❌ TFLint is not installed: {installation_status['error']}")
        print("\n📥 Installation methods:")
        for method, command in installation_status.get('installation_help', {}).get('install_methods', {}).items():
            print(f"   {method}: {command}")
        print("\nPlease install TFLint to continue with the analysis.")
        return
    
    # Run TFLint analysis with Azure plugin
    print("\n2. Running TFLint analysis with Azure plugin...")
    result = await tflint_runner.lint_terraform_configuration(
        hcl_content=sample_hcl,
        output_format="json",
        enable_azure_plugin=True,
        initialize_plugins=True
    )
    
    if result['success']:
        print("✅ TFLint analysis completed successfully")
        
        # Display summary
        summary = result['summary']
        print(f"\n📊 Analysis Summary:")
        print(f"   Total issues: {summary['total_issues']}")
        print(f"   Errors: {summary['errors']}")
        print(f"   Warnings: {summary['warnings']}")
        print(f"   Notices: {summary['notices']}")
        
        # Display issues if any
        if result['issues']:
            print(f"\n🔍 Issues Found ({len(result['issues'])}):")
            for i, issue in enumerate(result['issues'], 1):
                rule = issue.get('rule', {})
                severity = rule.get('severity', 'unknown').upper()
                rule_name = rule.get('name', 'unknown')
                message = issue.get('message', 'No message')
                
                print(f"\n   {i}. [{severity}] {rule_name}")
                print(f"      Message: {message}")
                
                # Location information
                range_info = issue.get('range', {})
                if range_info:
                    filename = range_info.get('filename', 'unknown')
                    start = range_info.get('start', {})
                    line = start.get('line', 'unknown')
                    column = start.get('column', 'unknown')
                    print(f"      Location: {filename}:{line}:{column}")
        else:
            print("\n✅ No issues found in the configuration!")
    
    else:
        print(f"❌ TFLint analysis failed: {result['error']}")
        if "Failed to initialize TFLint plugins" in result['error']:
            print("   Note: Azure plugin initialization failed (likely due to GitHub API limits)")
            print("   Continuing with basic Terraform rules only...")
    
    # Run analysis without Azure plugin if it failed above
    azure_plugin_failed = not result['success'] and "Failed to initialize TFLint plugins" in result['error']
    
    # Run analysis with different output format
    print("\n3. Running analysis with compact output format...")
    compact_result = await tflint_runner.lint_terraform_configuration(
        hcl_content=sample_hcl,
        output_format="compact",
        enable_azure_plugin=not azure_plugin_failed,  # Disable Azure plugin if it failed
        initialize_plugins=False  # Don't reinitialize plugins
    )
    
    if compact_result['success']:
        print("✅ Compact format analysis completed")
        if compact_result.get('raw_output'):
            print("Raw output:")
            print(compact_result['raw_output'])
    else:
        print(f"❌ Compact format analysis failed: {compact_result['error']}")
        
    print("\n4. Running analysis with workspace folder...")
    
    # Create a temporary workspace folder for demonstration
    import tempfile
    import shutil
    import time
    
    temp_dir = None
    try:
        temp_dir = tempfile.mkdtemp()
        
        # Create main.tf file
        main_tf_path = os.path.join(temp_dir, 'main.tf')
        with open(main_tf_path, 'w', encoding='utf-8') as f:
            f.write(sample_hcl)
        
        # Create variables.tf file
        variables_tf_path = os.path.join(temp_dir, 'variables.tf')
        with open(variables_tf_path, 'w', encoding='utf-8') as f:
            f.write('''
variable "resource_group_name" {
  description = "The name of the resource group"
  type        = string
  default     = "example-resources"
}

variable "location" {
  description = "The Azure location"
  type        = string
  default     = "West Europe"
}
''')
        
        # Create subdirectory with another terraform file for recursive test
        sub_dir = os.path.join(temp_dir, 'modules', 'network')
        os.makedirs(sub_dir, exist_ok=True)
        
        network_tf_path = os.path.join(sub_dir, 'network.tf')
        with open(network_tf_path, 'w', encoding='utf-8') as f:
            f.write('''
resource "azurerm_network_security_group" "example" {
  name                = "example-nsg"
  location            = var.location
  resource_group_name = var.resource_group_name
  
  # Missing some best practice rules
}
''')
        
        print(f"   Created workspace at: {temp_dir}")
        print("   Files created:")
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                if file.endswith('.tf'):
                    relative_path = os.path.relpath(os.path.join(root, file), temp_dir)
                    print(f"     - {relative_path}")
        
        # Run workspace analysis (non-recursive)
        workspace_result = await tflint_runner.lint_terraform_workspace_folder(
            workspace_folder=temp_dir,
            output_format="json",
            enable_azure_plugin=not azure_plugin_failed,  # Disable Azure plugin if it failed
            initialize_plugins=False,  # Don't reinitialize plugins
            recursive=False
        )
        
        if workspace_result['success']:
            print("✅ Workspace analysis (non-recursive) completed")
            print(f"   Terraform files found: {workspace_result['terraform_files_found']}")
            print(f"   Issues found: {workspace_result['summary']['total_issues']}")
            
            if workspace_result.get('terraform_files'):
                print("   Analyzed files:")
                for tf_file in workspace_result['terraform_files']:
                    relative_path = os.path.relpath(tf_file, temp_dir)
                    print(f"     - {relative_path}")
        else:
            print(f"❌ Workspace analysis failed: {workspace_result['error']}")
        
        # Run workspace analysis (recursive)
        print("\n5. Running recursive workspace analysis...")
        recursive_result = await tflint_runner.lint_terraform_workspace_folder(
            workspace_folder=temp_dir,
            output_format="json",
            enable_azure_plugin=not azure_plugin_failed,  # Disable Azure plugin if it failed
            initialize_plugins=False,
            recursive=True
        )
        
        if recursive_result['success']:
            print("✅ Recursive workspace analysis completed")
            print(f"   Terraform files found: {recursive_result['terraform_files_found']}")
            print(f"   Issues found: {recursive_result['summary']['total_issues']}")
            
            if recursive_result.get('terraform_files'):
                print("   Analyzed files:")
                for tf_file in recursive_result['terraform_files']:
                    relative_path = os.path.relpath(tf_file, temp_dir)
                    print(f"     - {relative_path}")
        else:
            print(f"❌ Recursive workspace analysis failed: {recursive_result['error']}")
            
    except Exception as e:
        print(f"❌ Error during workspace testing: {e}")
    finally:
        # Clean up temporary directory with retry on Windows
        if temp_dir and os.path.exists(temp_dir):
            try:
                # Small delay to ensure file handles are closed
                time.sleep(0.1)
                shutil.rmtree(temp_dir)
            except Exception as cleanup_error:
                print(f"⚠️  Warning: Could not clean up temporary directory: {cleanup_error}")

    # Example with specific rules
    print("\n6. Running analysis with specific rule configuration...")
    specific_rules_result = await tflint_runner.lint_terraform_configuration(
        hcl_content=sample_hcl,
        output_format="json",
        enable_azure_plugin=not azure_plugin_failed,  # Disable Azure plugin if it failed
        disable_rules=["terraform_unused_declarations"],
        initialize_plugins=False
    )
    
    if specific_rules_result['success']:
        print(f"✅ Analysis with rule configuration completed")
        print(f"   Issues found: {specific_rules_result['summary']['total_issues']}")
    else:
        print(f"❌ Analysis with rule configuration failed: {specific_rules_result['error']}")
    
    print("\n🎉 TFLint integration example completed!")
    print("\nNext steps:")
    print("- Use run_tflint_analysis for analyzing raw HCL content")
    print("- Use run_tflint_workspace_analysis for analyzing workspace folders")
    print("- Integrate TFLint analysis into your CI/CD pipeline")
    print("- Configure custom rules based on your organization's standards")
    print("- Use different output formats for different use cases")
    print("- Combine with other tools like terraform validate and security scanning")
    
    if azure_plugin_failed:
        print("\n🔧 Azure Plugin Note:")
        print("   The Azure ruleset plugin failed to initialize (likely GitHub API limits)")
        print("   In production, consider:")
        print("   - Using a GitHub token for API access")
        print("   - Pre-installing plugins in your environment")
        print("   - Running initialization separately before analysis")


if __name__ == "__main__":
    asyncio.run(main())
