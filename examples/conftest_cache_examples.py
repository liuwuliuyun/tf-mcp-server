"""
Example demonstrating the new conftest AVM runner cache functionality.
"""
import asyncio
import json
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from tf_mcp_server.tools.conftest_avm_runner import get_conftest_avm_runner


# Example Terraform plan JSON (simplified)
EXAMPLE_PLAN_JSON = json.dumps({
    "format_version": "1.0",
    "terraform_version": "1.0.0",
    "planned_values": {
        "root_module": {
            "resources": [
                {
                    "address": "azurerm_storage_account.example",
                    "mode": "managed",
                    "type": "azurerm_storage_account",
                    "name": "example",
                    "provider_name": "registry.terraform.io/hashicorp/azurerm",
                    "values": {
                        "name": "examplestorageaccount",
                        "resource_group_name": "example-rg",
                        "location": "eastus",
                        "account_tier": "Standard",
                        "account_replication_type": "LRS",
                        "min_tls_version": "TLS1_0",  # This might trigger a policy violation
                        "enable_https_traffic_only": True
                    }
                }
            ]
        }
    },
    "resource_changes": []
})


async def example_basic_usage():
    """Example 1: Basic usage with automatic cache initialization."""
    print("\n" + "="*80)
    print("Example 1: Basic Usage")
    print("="*80)
    
    # Initialize runner - automatically clones or updates cache
    runner = get_conftest_avm_runner()
    print(f"✓ Runner initialized")
    print(f"  Cache location: {runner.policy_cache_dir}")
    
    # Check conftest installation
    status = await runner.check_conftest_installation()
    print(f"✓ Conftest installed: {status.get('version', 'Unknown')}")


async def example_cache_status():
    """Example 2: Check cache status."""
    print("\n" + "="*80)
    print("Example 2: Cache Status Check")
    print("="*80)
    
    runner = get_conftest_avm_runner()
    
    # Get detailed cache status
    cache_status = await runner.get_policy_cache_status()
    
    if cache_status.get("cached"):
        print("✓ Policy cache is available")
        print(f"  Path: {cache_status['cache_path']}")
        print(f"  Policy sets: {', '.join(cache_status['policy_sets'])}")
        
        if git_info := cache_status.get("git_info"):
            print(f"  Last commit: {git_info['last_commit_hash']}")
            print(f"  Date: {git_info['last_commit_date']}")
            print(f"  Message: {git_info['last_commit_message']}")
    else:
        print(f"✗ Cache not available: {cache_status.get('status')}")


async def example_validate_with_cache():
    """Example 3: Validate Terraform plan using cached policies."""
    print("\n" + "="*80)
    print("Example 3: Validate with Cached Policies")
    print("="*80)
    
    runner = get_conftest_avm_runner()
    
    # Validate using different policy sets
    policy_sets = ["avmsec", "Azure-Proactive-Resiliency-Library-v2"]
    
    for policy_set in policy_sets:
        print(f"\nValidating with '{policy_set}' policy set...")
        
        result = await runner.validate_with_avm_policies(
            terraform_plan_json=EXAMPLE_PLAN_JSON,
            policy_set=policy_set
        )
        
        if result['success']:
            print(f"  ✓ Validation passed - no violations")
        else:
            print(f"  ⚠ Validation found issues:")
            summary = result['summary']
            print(f"    - Total violations: {summary['total_violations']}")
            print(f"    - Failures: {summary['failures']}")
            print(f"    - Warnings: {summary['warnings']}")
            
            # Show first few violations
            for i, violation in enumerate(result.get('violations', [])[:3], 1):
                print(f"    {i}. [{violation['level']}] {violation['policy']}: {violation['message']}")


async def example_manual_update():
    """Example 4: Manually update policy cache."""
    print("\n" + "="*80)
    print("Example 4: Manual Cache Update")
    print("="*80)
    
    runner = get_conftest_avm_runner()
    
    # Regular update (git pull)
    print("Updating policy cache...")
    result = await runner.update_policy_cache()
    
    if result['success']:
        print(f"✓ {result['message']}")
    else:
        print(f"✗ Update failed: {result['error']}")
    
    # Force update (remove and re-clone) - commented out to avoid unnecessary downloads
    # print("\nForce updating policy cache...")
    # result = await runner.update_policy_cache(force=True)
    # if result['success']:
    #     print(f"✓ {result['message']}")


async def example_policy_sets():
    """Example 5: Working with different policy sets."""
    print("\n" + "="*80)
    print("Example 5: Available Policy Sets")
    print("="*80)
    
    runner = get_conftest_avm_runner()
    
    print("Configured policy sets:")
    for name, path in runner.policy_sets.items():
        exists = "✓" if path.exists() else "✗"
        print(f"  {exists} {name}: {path}")
    
    # Check what's actually in the cache
    print("\nActual policy directories in cache:")
    policy_path = runner.policy_cache_dir / "policy"
    if policy_path.exists():
        for item in policy_path.iterdir():
            if item.is_dir():
                rego_files = list(item.glob("**/*.rego"))
                print(f"  - {item.name}: {len(rego_files)} .rego files")


async def example_workspace_validation():
    """Example 6: Validate workspace folder (if exists)."""
    print("\n" + "="*80)
    print("Example 6: Workspace Folder Validation")
    print("="*80)
    
    runner = get_conftest_avm_runner()
    
    # Check if workspace folder exists
    workspace_folder = "workspace"
    
    result = await runner.validate_workspace_folder_with_avm_policies(
        workspace_folder=workspace_folder,
        policy_set="avmsec"
    )
    
    if result['success']:
        print(f"✓ Workspace '{workspace_folder}' validation passed")
        summary = result['summary']
        print(f"  Total violations: {summary['total_violations']}")
    else:
        print(f"⚠ Validation completed with issues:")
        if 'error' in result:
            print(f"  Error: {result['error']}")
        else:
            summary = result['summary']
            print(f"  Total violations: {summary['total_violations']}")


async def main():
    """Run all examples."""
    print("\n" + "="*80)
    print("Conftest AVM Runner Cache - Examples")
    print("="*80)
    
    try:
        await example_basic_usage()
        await example_cache_status()
        await example_policy_sets()
        await example_validate_with_cache()
        await example_manual_update()
        await example_workspace_validation()
        
        print("\n" + "="*80)
        print("All examples completed successfully!")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n✗ Error running examples: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
