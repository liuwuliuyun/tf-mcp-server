"""
Test script to verify the conftest AVM runner cache functionality.
"""
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from tf_mcp_server.tools.conftest_avm_runner import get_conftest_avm_runner


async def main():
    """Test the conftest cache initialization."""
    print("=" * 80)
    print("Testing Conftest AVM Runner Cache Initialization")
    print("=" * 80)
    
    try:
        # Initialize the runner (will clone or update cache)
        print("\n1. Initializing Conftest AVM Runner...")
        runner = get_conftest_avm_runner()
        print(f"   ✓ Runner initialized successfully")
        print(f"   Cache location: {runner.policy_cache_dir}")
        
        # Check conftest installation
        print("\n2. Checking Conftest installation...")
        conftest_status = await runner.check_conftest_installation()
        if conftest_status.get("installed"):
            print(f"   ✓ Conftest is installed: {conftest_status.get('version')}")
        else:
            print(f"   ✗ Conftest not found: {conftest_status.get('error')}")
            print(f"   Installation help: {conftest_status.get('installation_help')}")
        
        # Check policy cache status
        print("\n3. Checking policy cache status...")
        cache_status = await runner.get_policy_cache_status()
        if cache_status.get("cached"):
            print(f"   ✓ Policy cache is available")
            print(f"   Cache path: {cache_status.get('cache_path')}")
            print(f"   Policy sets: {', '.join(cache_status.get('policy_sets', []))}")
            if cache_status.get("git_info"):
                git_info = cache_status["git_info"]
                print(f"   Last commit: {git_info.get('last_commit_hash')} - {git_info.get('last_commit_date')}")
                print(f"   Message: {git_info.get('last_commit_message')}")
        else:
            print(f"   ✗ Policy cache not available: {cache_status.get('status')}")
        
        # Verify policy sets
        print("\n4. Verifying policy set paths...")
        for policy_name, policy_path in runner.policy_sets.items():
            exists = policy_path.exists()
            status = "✓" if exists else "✗"
            print(f"   {status} {policy_name}: {policy_path}")
        
        print("\n" + "=" * 80)
        print("Test completed successfully!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n✗ Error during test: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
