"""
Conftest runner for Azure Verified Modules (AVM) policy validation.
"""

import os
import json
import subprocess
import tempfile
from typing import Dict, Any, Optional, List
from ..core.utils import extract_hcl_from_markdown, strip_ansi_escape_sequences


class ConftestAVMRunner:
    """Conftest runner for Azure Verified Modules policy validation."""
    
    def __init__(self):
        """Initialize the Conftest AVM runner."""
        self.conftest_executable = self._find_conftest_executable()
        self.avm_policy_repo = "git::https://github.com/Azure/policy-library-avm.git//policy"
    
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
            
            # Build conftest command
            cmd = [self.conftest_executable, 'test', '--all-namespaces', '--update']
            
            # Add policy source based on policy_set
            if policy_set == "all":
                cmd.append(self.avm_policy_repo)
            elif policy_set == "Azure-Proactive-Resiliency-Library-v2":
                cmd.append(f"{self.avm_policy_repo}/Azure-Proactive-Resiliency-Library-v2")
            elif policy_set == "avmsec":
                cmd.append(f"{self.avm_policy_repo}/avmsec")
            else:
                cmd.append(f"{self.avm_policy_repo}/{policy_set}")
            
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
            
            # Run conftest
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
                                                      hcl_content: str,
                                                      policy_set: str = "all",
                                                      severity_filter: Optional[str] = None,
                                                      custom_policies: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Validate Terraform HCL content against Azure Verified Modules policies.
        This method will first convert HCL to a plan, then validate it.
        
        Args:
            hcl_content: Terraform HCL content
            policy_set: Policy set to use ('all', 'Azure-Proactive-Resiliency-Library-v2', 'avmsec')
            severity_filter: Filter by severity for avmsec policies ('high', 'medium', 'low', 'info')
            custom_policies: List of custom policy paths to include
            
        Returns:
            Policy validation results
        """
        # Extract HCL if needed
        extracted_hcl = extract_hcl_from_markdown(hcl_content)
        if extracted_hcl:
            hcl_content = extracted_hcl
        
        try:
            # Create temporary directory for Terraform operations
            with tempfile.TemporaryDirectory() as temp_dir:
                # Write HCL content to main.tf
                main_tf_path = os.path.join(temp_dir, 'main.tf')
                with open(main_tf_path, 'w') as f:
                    f.write(hcl_content)
                
                # Initialize Terraform
                init_result = subprocess.run(['terraform', 'init'], 
                                           cwd=temp_dir,
                                           capture_output=True, 
                                           text=True, 
                                           timeout=120)
                
                if init_result.returncode != 0:
                    error_message = strip_ansi_escape_sequences(init_result.stderr)
                    return {
                        'success': False,
                        'error': f'Terraform init failed: {error_message}',
                        'violations': [],
                        'summary': {'total_violations': 0, 'failures': 0, 'warnings': 0}
                    }
                
                # Create Terraform plan
                plan_result = subprocess.run(['terraform', 'plan', '-out=tfplan.binary'], 
                                           cwd=temp_dir,
                                           capture_output=True, 
                                           text=True, 
                                           timeout=120)
                
                if plan_result.returncode != 0:
                    error_message = strip_ansi_escape_sequences(plan_result.stderr)
                    return {
                        'success': False,
                        'error': f'Terraform plan failed: {error_message}',
                        'violations': [],
                        'summary': {'total_violations': 0, 'failures': 0, 'warnings': 0}
                    }
                
                # Convert plan to JSON
                show_result = subprocess.run(['terraform', 'show', '-json', 'tfplan.binary'], 
                                           cwd=temp_dir,
                                           capture_output=True, 
                                           text=True, 
                                           timeout=60)
                
                if show_result.returncode != 0:
                    error_message = strip_ansi_escape_sequences(show_result.stderr)
                    return {
                        'success': False,
                        'error': f'Terraform show failed: {error_message}',
                        'violations': [],
                        'summary': {'total_violations': 0, 'failures': 0, 'warnings': 0}
                    }
                
                # Now validate the plan JSON with AVM policies
                return await self.validate_with_avm_policies(
                    terraform_plan_json=show_result.stdout,
                    policy_set=policy_set,
                    severity_filter=severity_filter,
                    custom_policies=custom_policies
                )
                
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Terraform operation timed out',
                'violations': [],
                'summary': {'total_violations': 0, 'failures': 0, 'warnings': 0}
            }
        except Exception as e:
            error_message = strip_ansi_escape_sequences(str(e))
            return {
                'success': False,
                'error': f'Error validating HCL with AVM policies: {error_message}',
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
