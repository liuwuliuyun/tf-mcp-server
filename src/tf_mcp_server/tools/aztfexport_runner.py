import subprocess
import shlex
import os
import shutil
from typing import Dict, Any, List, Optional


class AztfexportRunner:
    """Aztfexport runner for exporting Azure resources to Terraform configurations."""

    # nanxu: investigate how to self trigger az login

    def __init__(self):
        """Initialize the AztfexportRunner."""
        self.aztfexport_executable = self._find_aztfexport_executable()

    def _find_aztfexport_executable(self) -> str:
        """Find the aztfexport executable on the system."""
        
        
        # Try common locations and PATH
        possible_names = ["aztfexport", "aztfexport.exe"]
        
        for name in possible_names:
            path = shutil.which(name)
            if path:
                return path
        
        # If not found in PATH, try common installation locations
        common_paths = [
            "/usr/local/bin/aztfexport",
            "/usr/bin/aztfexport", 
            os.path.expanduser("~/go/bin/aztfexport"),
            "C:\\Program Files\\aztfexport\\aztfexport.exe",
            "C:\\tools\\aztfexport\\aztfexport.exe"
        ]
        
        for path in common_paths:
            if os.path.isfile(path) and os.access(path, os.X_OK):
                return path
            
        return "aztfexport"  # Fallback - let subprocess handle the error
    
    def run_raw_command(self, command_args: str, client_working_directory: str = "") -> Dict[str, Any]:
        """
        Run aztfexport with raw command line arguments.
        
        Args:
            command_args: Raw command arguments as string (e.g., "rg myRG -o ./output -f -n")
            client_working_directory: Client's working directory for resolving relative paths
            
        Returns:
            A dictionary with stderr, returncode, and command_executed.
            In case of timeout or error, returns an error message.
        """
        
        execution_warning = None  # Initialize warning variable
        
        # Define timeout in seconds (90 minutes)
        COMMAND_TIMEOUT_SECONDS = 5400
        
        try:
            # Check if aztfexport executable exists
            if not os.path.isfile(self.aztfexport_executable) and not shutil.which(self.aztfexport_executable):
                error_msg = f"aztfexport executable not found: {self.aztfexport_executable}"

                return {
                    "stderr": error_msg,
                    "returncode": -1,
                    "command_executed": f"{self.aztfexport_executable} {command_args}",
                    "raw_args": command_args
                }
            
            # Parse the command arguments using shlex for proper handling of quotes and spaces
            args = shlex.split(command_args)
            
            # Check if command contains relative paths
            has_relative_paths = self._has_relative_paths(args)
            
            # Process relative paths intelligently
            if has_relative_paths:
                if client_working_directory:
                    # Resolve relative paths using client working directory (even if directory doesn't exist yet)
                    args = self._resolve_relative_paths(args, client_working_directory)
                else:
                    # Add a warning to the result but don't fail
                    execution_warning = "Note: Relative paths were resolved relative to server working directory. Provide client_working_directory for better path control."
            
            # Build the full command
            cmd_args = [self.aztfexport_executable] + args
            
            # Determine working directory for command execution
            # If we resolved relative paths to absolute paths, run from server directory
            # If client provided directory but relative paths weren't resolved, we can try client directory if it exists
            if client_working_directory and not has_relative_paths and os.path.isdir(client_working_directory):
                execution_cwd = client_working_directory
            else:
                execution_cwd = os.getcwd()  # Use server working directory
            
            # Run the command
            result = subprocess.run(
                cmd_args, 
                capture_output=True, 
                text=True, 
                timeout=COMMAND_TIMEOUT_SECONDS,
                cwd=execution_cwd
            )
            
            # Direct return - let aztfexport speak for itself
            response = {
                "stderr": result.stderr,
                "returncode": result.returncode,
                "command_executed": " ".join(cmd_args),
                "raw_args": command_args,
                "working_directory": execution_cwd,
                "executable_path": self.aztfexport_executable,
                "success": result.returncode == 0
            }
            
            # Add warning if relative paths were used without client working directory
            if execution_warning:
                response["warning"] = execution_warning
                
            return response
            
        except subprocess.TimeoutExpired:
            return {"error": error_msg}
        except subprocess.CalledProcessError as e:
            error_msg = f"Error during aztfexport execution: {str(e)}"
            return {"error": error_msg}
        except FileNotFoundError as e:
            error_msg = f"aztfexport executable not found: {e}"
            return {"error": error_msg}
        except Exception as e:
            error_msg = f"Error parsing or executing command: {str(e)}"
            return {"error": error_msg}
    
    def _resolve_relative_paths(self, args: List[str], client_working_directory: str) -> List[str]:
        """
        Resolve relative paths in command arguments to be relative to client working directory.
        
        Args:
            args: List of command arguments
            client_working_directory: Client's working directory
            
        Returns:
            Updated arguments list with resolved paths
        """
        resolved_args = []
        i = 0
        
        # Arguments that expect a path as the next argument
        path_flags = ['-o', '--output-dir']
        
        while i < len(args):
            arg = args[i]
            resolved_args.append(arg)
            
            # Check if this argument expects a path as the next argument
            if i + 1 < len(args) and arg in path_flags:
                next_arg = args[i + 1]
                if next_arg.startswith('./') or next_arg.startswith('.\\'):
                    # Convert relative path to absolute path based on client working directory
                    relative_path = next_arg[2:]  # Remove ./ or .\
                    absolute_path = os.path.join(client_working_directory, relative_path)
                    # Normalize path separators for consistency
                    absolute_path = absolute_path.replace('\\', '/')
                    resolved_args.append(absolute_path)
                    i += 2  # Skip the next argument since we processed it
                    continue
                elif next_arg.startswith('../') or next_arg.startswith('..\\'):
                    # Handle parent directory references
                    absolute_path = os.path.abspath(os.path.join(client_working_directory, next_arg))
                    # Normalize path separators for consistency
                    absolute_path = absolute_path.replace('\\', '/')
                    resolved_args.append(absolute_path)
                    i += 2  # Skip the next argument since we processed it
                    continue
            
            i += 1
        
        return resolved_args
    
    def _has_relative_paths(self, args: List[str]) -> bool:
        """
        Check if command arguments contain relative paths.
        
        Args:
            args: List of command arguments
            
        Returns:
            True if relative paths are found
        """
        path_flags = ['-o', '--output-dir']
        
        for i, arg in enumerate(args):
            # Check if this argument expects a path as the next argument
            if i + 1 < len(args) and arg in path_flags:
                next_arg = args[i + 1]
                if (next_arg.startswith('./') or next_arg.startswith('.\\') or 
                    next_arg.startswith('../') or next_arg.startswith('..\\')):
                    return True
        
        return False

    def _get_mapping_file_format_info(self) -> str:
        """
        Get detailed information about the required mapping file JSON format.
        
        Returns:
            Formatted string with mapping file format specification and examples
        """
        return """
=== MAPPING FILE JSON FORMAT (REQUIRED) ===

The mapping file must be a JSON object where:
- Keys: Azure resource IDs (full ARM resource IDs)  
- Values: Objects with exactly 3 REQUIRED fields:

REQUIRED FIELDS:
- "resource_type": Terraform resource type (e.g., "azurerm_resource_group")
- "resource_name": Terraform resource name
- "resource_id": Azure resource ID (same as the key)

EXAMPLE MAPPING FILE:
{
  "/subscriptions/12345678-1234-1234-1234-123456789abc/resourceGroups/myRG": {
    "resource_type": "azurerm_resource_group",
    "resource_name": "main_rg", 
    "resource_id": "/subscriptions/12345678-1234-1234-1234-123456789abc/resourceGroups/myRG"
  },
  "/subscriptions/12345678-1234-1234-1234-123456789abc/resourceGroups/myRG/providers/Microsoft.Automation/automationAccounts/myautomation": {
    "resource_type": "azurerm_automation_account", 
    "resource_name": "automation_account",
    "resource_id": "/subscriptions/12345678-1234-1234-1234-123456789abc/resourceGroups/myRG/providers/Microsoft.Automation/automationAccounts/myautomation"
  }
}

TIPS:
- Get resource IDs from Azure CLI: az resource list --query "[].id" -o tsv
- Verify resource types match Terraform provider documentation
- Test with small mapping files first before large imports

VALIDATION:
- All 3 fields (resource_type, resource_name, resource_id) are mandatory
- Missing any field will cause aztfexport to fail
- Duplicate resource_name values are not allowed
- Invalid resource_type will be detected during plan phase
"""

    def get_help(self, command: str = "") -> Dict[str, Any]:
        """
        Get help information from aztfexport dynamically.
        
        Args:
            command: Optional command to get help for (e.g., "rg", "res", "query", "map")
                    If empty, gets main help with all available commands
            
        Returns:
            Dictionary with help information, executable status, and any errors
        """
        try:
            # Check if aztfexport executable exists
            if not os.path.isfile(self.aztfexport_executable) and not shutil.which(self.aztfexport_executable):
                return {
                    "success": False,
                    "error": f"aztfexport executable not found: {self.aztfexport_executable}",
                    "executable_path": self.aztfexport_executable,
                    "command": command or "main"
                }
            
            # Build help command
            if command:
                cmd_args = [self.aztfexport_executable, command, "-h"]
                help_type = f"command '{command}'"
            else:
                cmd_args = [self.aztfexport_executable, "-h"]
                help_type = "main"
            
            # Run help command
            result = subprocess.run(
                cmd_args,
                capture_output=True,
                text=True,
                timeout=30  # Help should be fast
            )
            
            # aztfexport help typically goes to stdout, but some help might go to stderr
            help_text = result.stdout or result.stderr
            
            # Enhance help for mapping file commands with required JSON format
            if command in ['map', 'mapping-file'] and help_text:
                mapping_format_info = self._get_mapping_file_format_info()
                help_text = help_text + "\n\n" + mapping_format_info
            
            return {
                "success": True,
                "help_text": help_text,
                "command": command or "main",
                "executable_path": self.aztfexport_executable,
                "returncode": result.returncode
            }
            
        except subprocess.TimeoutExpired:
            error_msg = "Help command timed out"
            return {
                "success": False,
                "error": error_msg,
                "command": command or "main"
            }
        except FileNotFoundError as e:
            error_msg = f"aztfexport executable not found: {e}"
            return {
                "success": False,
                "error": error_msg,
                "command": command or "main"
            }
        except Exception as e:
            error_msg = f"Error getting help: {str(e)}"
            return {
                "success": False,
                "error": error_msg,
                "command": command or "main"
            }

# Global variable to store singleton instance
_aztfexport_runner_instance = None


def get_aztfexport_runner() -> AztfexportRunner:
    """Get a singleton instance of AztfexportRunner."""
    global _aztfexport_runner_instance
    if _aztfexport_runner_instance is None:
        _aztfexport_runner_instance = AztfexportRunner()
    return _aztfexport_runner_instance
