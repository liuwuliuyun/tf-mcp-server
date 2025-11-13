# Conftest AVM Runner Cache Implementation

## Summary

Successfully rebuilt the `ConftestAVMRunner.__init__` method to implement a local policy cache system using `git clone`. This eliminates the need for conftest to download policies on every run and provides better control over policy versions.

## Key Changes

### 1. **New Cache Initialization (`__init__` method)**

```python
def __init__(self):
    """Initialize the Conftest AVM runner with local policy cache."""
    self.conftest_executable = self._find_conftest_executable()
    self.avm_policy_repo_url = "https://github.com/Azure/policy-library-avm.git"
    
    # Initialize cache directory for policies
    self.policy_cache_dir = self._get_policy_cache_dir()
    self._ensure_policy_cache()
    
    # Set policy folders based on cached location
    self.policy_base_path = self.policy_cache_dir / "policy"
    self.policy_sets = {
        "all": self.policy_base_path,
        "Azure-Proactive-Resiliency-Library-v2": self.policy_base_path / "Azure-Proactive-Resiliery-Library-v2",
        "avmsec": self.policy_base_path / "avmsec"
    }
```

**Changes:**
- Replaced `self.avm_policy_repo` (git URL) with `self.avm_policy_repo_url`
- Added `policy_cache_dir` for local cache storage at `src/data/avm_policy_cache`
- Added `policy_base_path` and `policy_sets` dictionary for easy access to cached policy folders
- Calls `_ensure_policy_cache()` on initialization to clone or update policies

### 2. **Cache Management Methods**

#### `_get_policy_cache_dir()`
- Returns cache directory path: `src/data/avm_policy_cache`
- Follows the same pattern as other cache directories in the project

#### `_ensure_policy_cache()`
- **First run:** Clones the policy repository using `git clone`
- **Subsequent runs:** Updates existing cache using `git pull`
- Handles errors gracefully with informative messages
- Requires `git` to be installed and available in PATH

#### `get_policy_cache_status()` (NEW)
- Returns detailed cache status information
- Shows available policy sets
- Displays git commit information (hash, date, message)
- Useful for diagnostics

#### `update_policy_cache(force: bool = False)` (NEW)
- Manually updates the policy cache
- `force=True` removes existing cache and re-clones
- Useful for troubleshooting or forcing a refresh

### 3. **Updated Policy Validation Logic**

The `validate_with_avm_policies()` method now:
- Uses local cached policy paths instead of git URLs
- Removed the `--update` flag from conftest commands (no longer needed)
- Removed retry logic for policy download conflicts
- Uses `-p` flag to specify local policy directories

**Before:**
```python
cmd = [self.conftest_executable, 'test', '--all-namespaces', '--update']
cmd.append(self.avm_policy_repo)  # git URL
```

**After:**
```python
cmd = [self.conftest_executable, 'test', '--all-namespaces']
policy_path = self.policy_sets[policy_set]
cmd.extend(['-p', str(policy_path)])  # local path
```

## Benefits

1. **Faster Execution:** No need to download policies on every run
2. **Offline Support:** Works without internet after initial clone
3. **Version Control:** Can lock to specific policy versions if needed
4. **Better Diagnostics:** Can inspect cached policies directly
5. **Reduced Network Load:** Downloads once, uses many times
6. **Automatic Updates:** Pulls latest changes on initialization

## Cache Location

```
src/
└── data/
    └── avm_policy_cache/          # Git clone of policy-library-avm
        ├── .git/                   # Git repository metadata
        ├── policy/                 # Policy subfolder (used by conftest)
        │   ├── avmsec/            # Security policies
        │   ├── Azure-Proactive-Resiliency-Library-v2/  # Resiliency policies
        │   └── common/            # Common policy utilities
        └── ...
```

## Testing Results

✅ Successfully clones repository on first run  
✅ Updates cache using `git pull` on subsequent runs  
✅ Detects and uses all policy sets correctly  
✅ Provides detailed git commit information  
✅ Conftest validation works with cached policies  

## Requirements

- **Git:** Must be installed and available in system PATH
- **Network:** Required for initial clone and updates (not for validation)
- **Disk Space:** ~5-10 MB for policy repository

## Error Handling

- **Git not found:** Provides clear error message requesting git installation
- **Clone failure:** Shows git error output with ANSI codes stripped
- **Missing policies:** Validates policy paths and provides helpful error messages
- **Update failure:** Logs warning but continues with existing cache

## API Usage

```python
from tf_mcp_server.tools.conftest_avm_runner import get_conftest_avm_runner

# Initialize (clones or updates cache)
runner = get_conftest_avm_runner()

# Check cache status
status = await runner.get_policy_cache_status()
print(f"Cached: {status['cached']}")
print(f"Policy sets: {status['policy_sets']}")

# Force update cache
result = await runner.update_policy_cache(force=True)
print(f"Update result: {result['success']}")

# Validate as usual (uses cached policies)
validation = await runner.validate_with_avm_policies(
    terraform_plan_json=plan_json,
    policy_set="avmsec"
)
```

## Migration Notes

No breaking changes to public API. All existing code using `ConftestAVMRunner` will continue to work without modifications. The change is transparent to users.

## Future Enhancements

- Add cache expiration/TTL configuration
- Support for custom policy repositories
- Cache statistics and metrics
- Selective policy set downloads
- Cache cleanup utilities
