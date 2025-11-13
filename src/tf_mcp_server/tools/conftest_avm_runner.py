"""
Conftest runner for Azure Verified Modules (AVM) policy validation.
"""

import os
import json
import logging
import subprocess
import tempfile
from typing import Dict, Any, Optional, List
from pathlib import Path
from ..core.utils import (
    strip_ansi_escape_sequences,
    resolve_workspace_path,
    get_docker_path_tip,
)

# Set up logger
logger = logging.getLogger(__name__)

class ConftestAVMRunner:
    """Conftest runner for Azure Verified Modules policy validation."""
    
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
            "Azure-Proactive-Resiliency-Library-v2": self.policy_base_path / "Azure-Proactive-Resiliency-Library-v2",
            "avmsec": self.policy_base_path / "avmsec"
        }
    
    def _get_policy_cache_dir(self) -> Path:
        """Get the cache directory path for AVM policies."""
        # Get the path to src/data relative to this file
        current_file = Path(__file__)
        # Navigate to src/data from src/tf_mcp_server/tools/
        data_dir = current_file.parent.parent.parent / "data" / "avm_policy_cache"
        return data_dir
    
    def _ensure_policy_cache(self) -> None:
        """Ensure the policy cache is initialized by cloning the repository if needed."""
        try:
            # Check if the policy cache directory exists and has content
            if self.policy_cache_dir.exists() and (self.policy_cache_dir / "policy").exists():
                logger.info(f"AVM policy cache found at {self.policy_cache_dir}")
                # Check if it's a git repo and try to update it
                if (self.policy_cache_dir / ".git").exists():
                    try:
                        logger.info("Updating cached AVM policies...")
                        result = subprocess.run(['git', 'pull'], 
                                              cwd=str(self.policy_cache_dir),
                                              capture_output=True, 
                                              text=True, 
                                              timeout=60)
                        if result.returncode == 0:
                            logger.info("AVM policy cache updated successfully")
                        else:
                            logger.warning(f"Failed to update policy cache: {result.stderr}")
                    except Exception as e:
                        logger.warning(f"Could not update policy cache: {str(e)}")
            else:
                # Clone the repository
                logger.info(f"Cloning AVM policy repository to {self.policy_cache_dir}...")
                self.policy_cache_dir.mkdir(parents=True, exist_ok=True)
                
                result = subprocess.run(['git', 'clone', self.avm_policy_repo_url, str(self.policy_cache_dir)], 
                                      capture_output=True, 
                                      text=True, 
                                      timeout=120)
                
                if result.returncode == 0:
                    logger.info("AVM policy repository cloned successfully")
                else:
                    error_msg = strip_ansi_escape_sequences(result.stderr)
                    logger.error(f"Failed to clone AVM policy repository: {error_msg}")
                    raise RuntimeError(f"Failed to clone AVM policy repository: {error_msg}")
                    
        except FileNotFoundError:
            logger.error("Git executable not found. Please ensure git is installed and in PATH.")
            raise RuntimeError("Git is required to download AVM policies. Please install git.")
        except Exception as e:
            logger.error(f"Error initializing policy cache: {str(e)}")
            raise
    
    def _find_conftest_executable(self) -> str:
        """Find the conftest executable in the system PATH."""
        # Try common locations for conftest
        possible_paths = ['conftest', 'conftest.exe']
        
        for path in possible_paths:
            try:
                result = subprocess.run([path, '--version'], 
                                      capture_output=True, 
                                      text=True, 
                                      timeout=10)
                if result.returncode == 0:
                    return path
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue
        
        return 'conftest'  # Default fallback
    
    async def check_conftest_installation(self) -> Dict[str, Any]:
        """
        Check if Conftest is installed and get version information.
        
        Returns:
            Installation status, version information, and installation help if needed
        """
        try:
            result = subprocess.run([self.conftest_executable, '--version'], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=10)
            
            if result.returncode == 0:
                version_output = result.stdout.strip()
                return {
                    "installed": True,
                    "version": version_output,
                    "executable_path": self.conftest_executable,
                    "status": "Conftest is installed and ready to use"
                }
            else:
                return {
                    "installed": False,
                    "error": result.stderr,
                    "installation_help": self._get_installation_help()
                }
                
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            return {
                "installed": False,
                "error": f"Conftest not found: {str(e)}",
                "installation_help": self._get_installation_help()
            }
    
    async def get_policy_cache_status(self) -> Dict[str, Any]:
        """
        Get the status of the local AVM policy cache.
        
        Returns:
            Cache status information including path, size, and last update time
        """
        try:
            if not self.policy_cache_dir.exists():
                return {
                    "cached": False,
                    "cache_path": str(self.policy_cache_dir),
                    "status": "Policy cache not initialized. It will be created on first use."
                }
            
            policy_path = self.policy_cache_dir / "policy"
            if not policy_path.exists():
                return {
                    "cached": False,
                    "cache_path": str(self.policy_cache_dir),
                    "status": "Policy cache directory exists but policy folder is missing."
                }
            
            # Get information about the cached policies
            available_policy_sets = [p.name for p in policy_path.iterdir() if p.is_dir()]
            
            # Get git info if available
            git_info = {}
            if (self.policy_cache_dir / ".git").exists():
                try:
                    # Get last commit info
                    result = subprocess.run(['git', 'log', '-1', '--format=%H|%aI|%s'], 
                                          cwd=str(self.policy_cache_dir),
                                          capture_output=True, 
                                          text=True, 
                                          timeout=10)
                    if result.returncode == 0:
                        commit_hash, commit_date, commit_msg = result.stdout.strip().split('|', 2)
                        git_info = {
                            "last_commit_hash": commit_hash[:8],
                            "last_commit_date": commit_date,
                            "last_commit_message": commit_msg
                        }
                except Exception as e:
                    logger.debug(f"Could not get git info: {str(e)}")
            
            return {
                "cached": True,
                "cache_path": str(self.policy_cache_dir),
                "policy_sets": available_policy_sets,
                "git_info": git_info,
                "status": f"Policy cache is available with {len(available_policy_sets)} policy sets"
            }
            
        except Exception as e:
            return {
                "cached": False,
                "error": f"Error checking policy cache status: {str(e)}",
                "cache_path": str(self.policy_cache_dir)
            }
    
    async def update_policy_cache(self, force: bool = False) -> Dict[str, Any]:
        """
        Update the local AVM policy cache by pulling the latest changes from GitHub.
        
        Args:
            force: If True, removes existing cache and re-clones the repository
            
        Returns:
            Update status and information
        """
        try:
            if force and self.policy_cache_dir.exists():
                logger.info(f"Force update requested, removing existing cache at {self.policy_cache_dir}")
                import shutil
                shutil.rmtree(self.policy_cache_dir)
            
            # Re-initialize the cache (will clone or update)
            self._ensure_policy_cache()
            
            return {
                "success": True,
                "message": "Policy cache updated successfully",
                "cache_path": str(self.policy_cache_dir)
            }
            
        except Exception as e:
            error_msg = strip_ansi_escape_sequences(str(e))
            return {
                "success": False,
                "error": f"Failed to update policy cache: {error_msg}",
                "cache_path": str(self.policy_cache_dir)
            }

    
    def _get_installation_help(self) -> Dict[str, str]:
        """Get installation instructions for Conftest."""
        return {
            "description": "Conftest is required to run Azure AVM policy validation",
            "windows": "Download from https://github.com/open-policy-agent/conftest/releases or use: scoop install conftest",
            "macos": "brew install conftest",
            "linux": "Download from https://github.com/open-policy-agent/conftest/releases or use package manager",
            "go_install": "go install github.com/open-policy-agent/conftest@latest"
        }
    
    async def validate_with_avm_policies(self, 
                                       terraform_plan_json: str,
                                       policy_set: str = "all",
                                       severity_filter: Optional[str] = None,
                                       custom_policies: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Validate Terraform plan against Azure Verified Modules policies.
        
        Args:
            terraform_plan_json: Terraform plan in JSON format
            policy_set: Policy set to use ('all', 'Azure-Proactive-Resiliency-Library-v2', 'avmsec')
            severity_filter: Filter by severity for avmsec policies ('high', 'medium', 'low', 'info')
            custom_policies: List of custom policy paths to include
            
        Returns:
            Policy validation results
        """
        if not terraform_plan_json or not terraform_plan_json.strip():
            return {
                'success': False,
                'error': 'No Terraform plan JSON provided',
                'violations': [],
                'summary': {
                    'total_violations': 0,
                    'failures': 0,
                    'warnings': 0
                }
            }
        
        # Initialize variables for cleanup
        plan_file_path = None
        exception_file_path = None
        
        try:
            # Create temporary file for the plan
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as plan_file:
                plan_file.write(terraform_plan_json)
                plan_file_path = plan_file.name
            
            # Build conftest command - no --update flag since we use local cached policies
            cmd = [self.conftest_executable, 'test', '--all-namespaces']
            
            # Add policy source based on policy_set using cached local paths
            if policy_set in self.policy_sets:
                policy_path = self.policy_sets[policy_set]
                if not policy_path.exists():
                    return {
                        'success': False,
                        'error': f'Policy set "{policy_set}" not found at {policy_path}. Try reinitializing the policy cache.',
                        'violations': [],
                        'summary': {'total_violations': 0, 'failures': 0, 'warnings': 0}
                    }
                cmd.extend(['-p', str(policy_path)])
            else:
                # Try custom policy set path
                custom_policy_path = self.policy_base_path / policy_set
                if custom_policy_path.exists():
                    cmd.extend(['-p', str(custom_policy_path)])
                else:
                    return {
                        'success': False,
                        'error': f'Unknown policy set "{policy_set}". Available: {", ".join(self.policy_sets.keys())}',
                        'violations': [],
                        'summary': {'total_violations': 0, 'failures': 0, 'warnings': 0}
                    }
            
            # Handle severity filtering for avmsec
            exception_content = None
            if policy_set == "avmsec" and severity_filter:
                exception_content = self._create_severity_exception(severity_filter)
            
            # Add custom policies if provided
            if custom_policies:
                for policy in custom_policies:
                    cmd.extend(['-p', policy])
            
            # Add exception file if needed
            exception_file_path = None
            if exception_content:
                with tempfile.NamedTemporaryFile(mode='w', suffix='.rego', delete=False) as exception_file:
                    exception_file.write(exception_content)
                    exception_file_path = exception_file.name
                cmd.extend(['-p', exception_file_path])
            
            # Add output format
            cmd.extend(['--output', 'json'])
            
            # Add the plan file
            cmd.append(plan_file_path)
            
            # Run conftest with local cached policies
            result = subprocess.run(cmd, 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=300)  # 5 minute timeout
            
            # Parse results
            violations = []
            if result.stdout:
                try:
                    output_data = json.loads(result.stdout)
                    violations = self._parse_conftest_output(output_data)
                except json.JSONDecodeError:
                    # Fallback to text parsing if JSON parsing fails
                    violations = self._parse_conftest_text_output(result.stdout)
            
            # Calculate summary
            total_violations = len(violations)
            failures = len([v for v in violations if v.get('level') == 'failure'])
            warnings = len([v for v in violations if v.get('level') == 'warning'])
            
            success = result.returncode == 0
            
            # Clean ANSI escape sequences from outputs
            clean_stdout = strip_ansi_escape_sequences(result.stdout) if result.stdout else None
            clean_stderr = strip_ansi_escape_sequences(result.stderr) if result.stderr else None
            
            return {
                'success': success,
                'policy_set': policy_set,
                'severity_filter': severity_filter,
                'total_violations': total_violations,
                'violations': violations,
                'summary': {
                    'total_violations': total_violations,
                    'failures': failures,
                    'warnings': warnings,
                    'policy_set_used': policy_set
                },
                'command_output': clean_stdout if not success else None,
                'command_error': clean_stderr if clean_stderr else None
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Conftest execution timed out (5 minutes)',
                'violations': [],
                'summary': {'total_violations': 0, 'failures': 0, 'warnings': 0}
            }
        except Exception as e:
            error_message = strip_ansi_escape_sequences(str(e))
            return {
                'success': False,
                'error': f'Error running conftest: {error_message}',
                'violations': [],
                'summary': {'total_violations': 0, 'failures': 0, 'warnings': 0}
            }
        finally:
            # Clean up temporary files
            try:
                if plan_file_path is not None:
                    os.unlink(plan_file_path)
                if exception_file_path is not None:
                    os.unlink(exception_file_path)
            except:
                pass  # Ignore cleanup errors
    
    def _create_severity_exception(self, severity_filter: str) -> str:
        """
        Create exception content for severity filtering in avmsec policies.
        
        Args:
            severity_filter: Severity level to filter by
            
        Returns:
            Rego exception content
        """
        if severity_filter == "high":
            return """package avmsec

import rego.v1

# Skip all policies except high severity
exception contains rules if {
  rules = rules_below_high
}"""
        elif severity_filter == "medium":
            return """package avmsec

import rego.v1

# Skip all policies except high and medium severity
exception contains rules if {
  rules = rules_below_medium
}"""
        elif severity_filter == "low":
            return """package avmsec

import rego.v1

# Skip all policies except high, medium, and low severity
exception contains rules if {
  rules = rules_below_low
}"""
        else:
            return ""  # No exception for 'info' or invalid severity
    
    def _parse_conftest_output(self, output_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Parse Conftest JSON output into standardized violation format.
        
        Args:
            output_data: Conftest JSON output
            
        Returns:
            List of violations in standardized format
        """
        violations = []
        
        for result in output_data:
            filename = result.get('filename', 'unknown')
            
            # Parse failures
            for failure in result.get('failures', []):
                violations.append({
                    'filename': filename,
                    'level': 'failure',
                    'policy': failure.get('rule', 'unknown'),
                    'message': failure.get('msg', 'Policy violation'),
                    'metadata': failure.get('metadata', {})
                })
            
            # Parse warnings
            for warning in result.get('warnings', []):
                violations.append({
                    'filename': filename,
                    'level': 'warning',
                    'policy': warning.get('rule', 'unknown'),
                    'message': warning.get('msg', 'Policy warning'),
                    'metadata': warning.get('metadata', {})
                })
        
        return violations
    
    def _parse_conftest_text_output(self, output_text: str) -> List[Dict[str, Any]]:
        """
        Parse Conftest text output as fallback.
        
        Args:
            output_text: Conftest text output
            
        Returns:
            List of violations in standardized format
        """
        violations = []
        lines = output_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if line and ('FAIL' in line or 'WARN' in line):
                violations.append({
                    'filename': 'unknown',
                    'level': 'failure' if 'FAIL' in line else 'warning',
                    'policy': 'unknown',
                    'message': line,
                    'metadata': {}
                })
        
        return violations

    async def validate_terraform_hcl_with_avm_policies(self,
                                                      terraform_hcl: str,
                                                      policy_set: str = "all",
                                                      severity_filter: Optional[str] = None,
                                                      custom_policies: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Validate raw Terraform HCL content against Azure Verified Modules policies.

        This helper writes the HCL to a temporary workspace, runs ``terraform init`` and
        ``terraform plan``, converts the plan to JSON, and then delegates to
        :meth:`validate_with_avm_policies` for policy enforcement.

        Args:
            terraform_hcl: Terraform configuration content in HCL format
            policy_set: Policy set to use ('all', 'Azure-Proactive-Resiliency-Library-v2', 'avmsec')
            severity_filter: Optional severity filter for avmsec policies
            custom_policies: Optional list of custom policy paths to include

        Returns:
            Policy validation results with success status and violation details
        """
        if not terraform_hcl or not terraform_hcl.strip():
            return {
                'success': False,
                'error': 'No Terraform HCL content provided',
                'violations': [],
                'summary': {
                    'total_violations': 0,
                    'failures': 0,
                    'warnings': 0
                }
            }

        try:
            with tempfile.TemporaryDirectory(prefix="conftest-avm-hcl-") as temp_dir:
                temp_path = Path(temp_dir)
                main_tf_path = temp_path / "main.tf"
                main_tf_path.write_text(terraform_hcl, encoding='utf-8')

                init_result = subprocess.run(['terraform', 'init'],
                                             cwd=str(temp_path),
                                             capture_output=True,
                                             text=True,
                                             timeout=120)

                if init_result.returncode != 0:
                    return {
                        'success': False,
                        'error': f'Terraform init failed: {strip_ansi_escape_sequences(init_result.stderr)}',
                        'violations': [],
                        'summary': {
                            'total_violations': 0,
                            'failures': 0,
                            'warnings': 0
                        }
                    }

                plan_file = temp_path / 'tfplan.binary'
                plan_result = subprocess.run(['terraform', 'plan', f'-out={plan_file.name}'],
                                              cwd=str(temp_path),
                                              capture_output=True,
                                              text=True,
                                              timeout=120)

                if plan_result.returncode != 0:
                    return {
                        'success': False,
                        'error': f'Terraform plan failed: {strip_ansi_escape_sequences(plan_result.stderr)}',
                        'violations': [],
                        'summary': {
                            'total_violations': 0,
                            'failures': 0,
                            'warnings': 0
                        }
                    }

                show_result = subprocess.run(['terraform', 'show', '-json', plan_file.name],
                                              cwd=str(temp_path),
                                              capture_output=True,
                                              text=True,
                                              timeout=60)

                if show_result.returncode != 0 or not show_result.stdout:
                    return {
                        'success': False,
                        'error': f'Terraform show failed: {strip_ansi_escape_sequences(show_result.stderr)}',
                        'violations': [],
                        'summary': {
                            'total_violations': 0,
                            'failures': 0,
                            'warnings': 0
                        }
                    }

                # Delegate to plan JSON validation
                try:
                    result = await self.validate_with_avm_policies(
                        terraform_plan_json=show_result.stdout,
                        policy_set=policy_set,
                        severity_filter=severity_filter,
                        custom_policies=custom_policies
                    )
                except Exception as exc:
                    return {
                        'success': False,
                        'error': f'Error during AVM policy validation: {exc}',
                        'violations': [],
                        'summary': {
                            'total_violations': 0,
                            'failures': 0,
                            'warnings': 0
                        }
                    }

                # Provide context about the temporary workspace used
                result.setdefault('workspace_path', str(temp_path))
                result.setdefault('terraform_files', ['main.tf'])
                result.setdefault('plan_file', str(plan_file))
                return result

        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Terraform operation timed out while processing HCL content',
                'violations': [],
                'summary': {
                    'total_violations': 0,
                    'failures': 0,
                    'warnings': 0
                }
            }
        except FileNotFoundError as exc:
            return {
                'success': False,
                'error': f'Terraform executable not found: {exc}',
                'violations': [],
                'summary': {
                    'total_violations': 0,
                    'failures': 0,
                    'warnings': 0
                }
            }
        except Exception as exc:
            return {
                'success': False,
                'error': f'Error validating Terraform HCL: {strip_ansi_escape_sequences(str(exc))}',
                'violations': [],
                'summary': {
                    'total_violations': 0,
                    'failures': 0,
                    'warnings': 0
                }
            }

    async def validate_workspace_folder_with_avm_policies(self,
                                                         workspace_folder: str,
                                                         policy_set: str = "all",
                                                         severity_filter: Optional[str] = None,
                                                         custom_policies: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Validate Terraform files in a workspace folder against Azure Verified Modules policies.
        
        Args:
            workspace_folder: Path to the workspace folder to validate (relative paths
                are resolved against the configured workspace root)
            policy_set: Policy set to use ('all', 'Azure-Proactive-Resiliency-Library-v2', 'avmsec')
            severity_filter: Filter by severity for avmsec policies ('high', 'medium', 'low', 'info')
            custom_policies: List of custom policy paths to include
            
        Returns:
            Policy validation results
        """
        if not workspace_folder or not workspace_folder.strip():
            return {
                'success': False,
                'error': 'No workspace folder provided',
                'violations': [],
                'summary': {
                    'total_violations': 0,
                    'failures': 0,
                    'warnings': 0
                }
            }
        
        try:
            # Build workspace folder path
            workspace_path = resolve_workspace_path(workspace_folder.strip())
            
            # Check if folder exists
            if not workspace_path.exists():
                return {
                    'success': False,
                    'error': f'Workspace folder "{workspace_folder}" does not exist at {workspace_path}{get_docker_path_tip(workspace_folder)}',
                    'violations': [],
                    'summary': {'total_violations': 0, 'failures': 0, 'warnings': 0}
                }
            
            if not workspace_path.is_dir():
                return {
                    'success': False,
                    'error': (
                        f'"{workspace_folder}" is not a directory: {workspace_path}\n\n'
                        f'Tip: Ensure the path points to a directory, not a file.\n'
                        f'     When running in Docker, use relative paths from /workspace'
                    ),
                    'violations': [],
                    'summary': {'total_violations': 0, 'failures': 0, 'warnings': 0}
                }
            
            # Check if folder contains Terraform files
            tf_files = list(workspace_path.glob('*.tf'))
            if not tf_files:
                return {
                    'success': False,
                    'error': (
                        f'No .tf files found in workspace folder "{workspace_folder}"\n\n'
                        f'Tip: Ensure your Terraform files are in the workspace folder.\n'
                        f'     Default Docker mount: -v ${{workspaceFolder}}:/workspace\n'
                        f'     Your files should be accessible at /workspace/your-folder'
                    ),
                    'violations': [],
                    'summary': {'total_violations': 0, 'failures': 0, 'warnings': 0}
                }
            
            # Initialize Terraform in the workspace folder
            init_result = subprocess.run(['terraform', 'init'], 
                                       cwd=str(workspace_path),
                                       capture_output=True, 
                                       text=True, 
                                       timeout=120)
            
            if init_result.returncode != 0:
                error_message = strip_ansi_escape_sequences(init_result.stderr)
                return {
                    'success': False,
                    'error': f'Terraform init failed in workspace folder: {error_message}',
                    'violations': [],
                    'summary': {'total_violations': 0, 'failures': 0, 'warnings': 0}
                }
            
            # Create Terraform plan
            plan_result = subprocess.run(['terraform', 'plan', '-out=tfplan.binary'], 
                                       cwd=str(workspace_path),
                                       capture_output=True, 
                                       text=True, 
                                       timeout=120)
            
            if plan_result.returncode != 0:
                error_message = strip_ansi_escape_sequences(plan_result.stderr)
                return {
                    'success': False,
                    'error': f'Terraform plan failed in workspace folder: {error_message}',
                    'violations': [],
                    'summary': {'total_violations': 0, 'failures': 0, 'warnings': 0}
                }
            
            # Convert plan to JSON
            show_result = subprocess.run(['terraform', 'show', '-json', 'tfplan.binary'], 
                                       cwd=str(workspace_path),
                                       capture_output=True, 
                                       text=True, 
                                       timeout=60)
            
            if show_result.returncode != 0:
                error_message = strip_ansi_escape_sequences(show_result.stderr)
                return {
                    'success': False,
                    'error': f'Terraform show failed in workspace folder: {error_message}',
                    'violations': [],
                    'summary': {'total_violations': 0, 'failures': 0, 'warnings': 0}
                }
            
            # Now validate the plan JSON with AVM policies
            result = await self.validate_with_avm_policies(
                terraform_plan_json=show_result.stdout,
                policy_set=policy_set,
                severity_filter=severity_filter,
                custom_policies=custom_policies
            )
            
            # Add workspace folder information to the result
            if 'workspace_folder' not in result:
                result['workspace_folder'] = workspace_folder
                result['workspace_path'] = str(workspace_path)
                result['terraform_files'] = [tf_file.name for tf_file in tf_files]
            
            return result
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Terraform operation timed out in workspace folder',
                'violations': [],
                'summary': {'total_violations': 0, 'failures': 0, 'warnings': 0}
            }
        except Exception as e:
            error_message = strip_ansi_escape_sequences(str(e))
            return {
                'success': False,
                'error': f'Error validating workspace folder with AVM policies: {error_message}',
                'violations': [],
                'summary': {'total_violations': 0, 'failures': 0, 'warnings': 0}
            }

    async def validate_workspace_folder_plan_with_avm_policies(self,
                                                              folder_name: str,
                                                              policy_set: str = "all",
                                                              severity_filter: Optional[str] = None,
                                                              custom_policies: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Validate an existing Terraform plan file in a workspace folder against Azure Verified Modules policies.
        This method looks for existing tfplan.binary or plan files in the workspace folder.
        
        Args:
            folder_name: Name of the folder in the workspace containing the plan file
                (relative paths are resolved against the configured workspace root)
            policy_set: Policy set to use ('all', 'Azure-Proactive-Resiliency-Library-v2', 'avmsec')
            severity_filter: Filter by severity for avmsec policies ('high', 'medium', 'low', 'info')
            custom_policies: List of custom policy paths to include
            
        Returns:
            Policy validation results
        """
        if not folder_name or not folder_name.strip():
            return {
                'success': False,
                'error': 'No folder name provided',
                'violations': [],
                'summary': {
                    'total_violations': 0,
                    'failures': 0,
                    'warnings': 0
                }
            }
        
        try:
            # Build workspace folder path
            workspace_path = resolve_workspace_path(folder_name.strip())
            
            # Check if folder exists
            if not workspace_path.exists():
                return {
                    'success': False,
                    'error': f'Workspace folder "{folder_name}" does not exist at {workspace_path}{get_docker_path_tip(folder_name)}',
                    'violations': [],
                    'summary': {'total_violations': 0, 'failures': 0, 'warnings': 0}
                }
            
            if not workspace_path.is_dir():
                return {
                    'success': False,
                    'error': (
                        f'"{folder_name}" is not a directory: {workspace_path}\n\n'
                        f'Tip: Ensure the path points to a directory, not a file.\n'
                        f'     When running in Docker, use relative paths from /workspace'
                    ),
                    'violations': [],
                    'summary': {'total_violations': 0, 'failures': 0, 'warnings': 0}
                }
            
            # Look for existing plan files
            plan_files = list(workspace_path.glob('tfplan.binary')) + list(workspace_path.glob('*.tfplan'))
            if not plan_files:
                # Try to create a plan if .tf files exist
                tf_files = list(workspace_path.glob('*.tf'))
                if not tf_files:
                    return {
                        'success': False,
                        'error': (
                            f'No .tf files or plan files found in workspace folder "{folder_name}"\n\n'
                            f'Tip: Ensure your Terraform files are in the workspace folder.\n'
                            f'     Default Docker mount: -v ${{workspaceFolder}}:/workspace\n'
                            f'     Your files should be accessible at /workspace/your-folder'
                        ),
                        'violations': [],
                        'summary': {'total_violations': 0, 'failures': 0, 'warnings': 0}
                    }
                
                # Initialize Terraform if not already initialized
                if not (workspace_path / '.terraform').exists():
                    init_result = subprocess.run(['terraform', 'init'], 
                                               cwd=str(workspace_path),
                                               capture_output=True, 
                                               text=True, 
                                               timeout=120)
                    
                    if init_result.returncode != 0:
                        error_message = strip_ansi_escape_sequences(init_result.stderr)
                        return {
                            'success': False,
                            'error': f'Terraform init failed in workspace folder: {error_message}',
                            'violations': [],
                            'summary': {'total_violations': 0, 'failures': 0, 'warnings': 0}
                        }
                
                # Create Terraform plan
                plan_result = subprocess.run(['terraform', 'plan', '-out=tfplan.binary'], 
                                           cwd=str(workspace_path),
                                           capture_output=True, 
                                           text=True, 
                                           timeout=120)
                
                if plan_result.returncode != 0:
                    error_message = strip_ansi_escape_sequences(plan_result.stderr)
                    return {
                        'success': False,
                        'error': f'Terraform plan failed in workspace folder: {error_message}',
                        'violations': [],
                        'summary': {'total_violations': 0, 'failures': 0, 'warnings': 0}
                    }
                
                plan_files = list(workspace_path.glob('tfplan.binary'))
            
            if not plan_files:
                return {
                    'success': False,
                    'error': f'No plan file found in workspace folder "{folder_name}" after attempting to create one',
                    'violations': [],
                    'summary': {'total_violations': 0, 'failures': 0, 'warnings': 0}
                }
            
            # Use the first plan file found
            plan_file = plan_files[0]
            
            # Convert plan to JSON
            show_result = subprocess.run(['terraform', 'show', '-json', str(plan_file)], 
                                       cwd=str(workspace_path),
                                       capture_output=True, 
                                       text=True, 
                                       timeout=60)
            
            if show_result.returncode != 0:
                error_message = strip_ansi_escape_sequences(show_result.stderr)
                return {
                    'success': False,
                    'error': f'Terraform show failed in workspace folder: {error_message}',
                    'violations': [],
                    'summary': {'total_violations': 0, 'failures': 0, 'warnings': 0}
                }
            
            # Now validate the plan JSON with AVM policies
            result = await self.validate_with_avm_policies(
                terraform_plan_json=show_result.stdout,
                policy_set=policy_set,
                severity_filter=severity_filter,
                custom_policies=custom_policies
            )
            
            # Add workspace folder information to the result
            if 'workspace_folder' not in result:
                result['workspace_folder'] = folder_name
                result['workspace_path'] = str(workspace_path)
                result['plan_file'] = str(plan_file)
            
            return result
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Terraform operation timed out in workspace folder',
                'violations': [],
                'summary': {'total_violations': 0, 'failures': 0, 'warnings': 0}
            }
        except Exception as e:
            error_message = strip_ansi_escape_sequences(str(e))
            return {
                'success': False,
                'error': f'Error validating workspace folder plan with AVM policies: {error_message}',
                'violations': [],
                'summary': {'total_violations': 0, 'failures': 0, 'warnings': 0}
            }


# Global variable to store singleton instance
_conftest_avm_runner_instance = None


def get_conftest_avm_runner() -> ConftestAVMRunner:
    """Get a singleton instance of ConftestAVMRunner."""
    global _conftest_avm_runner_instance
    if _conftest_avm_runner_instance is None:
        _conftest_avm_runner_instance = ConftestAVMRunner()
    return _conftest_avm_runner_instance
