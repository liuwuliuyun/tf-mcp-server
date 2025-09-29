"""
TFLint runner utilities for Azure Terraform MCP Server.
"""

import os
import json
import subprocess
import tempfile
from typing import Dict, Any, Optional, List
from ..core.utils import resolve_workspace_path


class TFLintRunner:
    """TFLint static analysis tool for Terraform configurations."""
    
    def __init__(self):
        """Initialize the TFLint runner."""
        self.tflint_executable = self._find_tflint_executable()
    
    def _find_tflint_executable(self) -> str:
        """Find the tflint executable in the system PATH."""
        # Try common locations for tflint
        possible_paths = ['tflint', 'tflint.exe']
        
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
        
        return 'tflint'  # Default fallback
    
    def _create_tflint_config(self, enable_azure_plugin: bool = True) -> str:
        """
        Create a basic tflint configuration.
        
        Args:
            enable_azure_plugin: Whether to enable the Azure ruleset plugin
            
        Returns:
            TFLint configuration content
        """
        config = """plugin "terraform" {
  enabled = true
  preset  = "recommended"
}
"""
        
        if enable_azure_plugin:
            config += """
plugin "azurerm" {
  enabled = true
  version = "0.26.0"
  source  = "github.com/terraform-linters/tflint-ruleset-azurerm"
}
"""
        
        return config
    
    async def _run_tflint_init(self, working_dir: str) -> Dict[str, Any]:
        """
        Run tflint --init to install plugins.
        
        Args:
            working_dir: Directory containing the .tflint.hcl config file
            
        Returns:
            Initialization result
        """
        try:
            result = subprocess.run(
                [self.tflint_executable, '--init'],
                cwd=working_dir,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'error': result.stderr if result.returncode != 0 else None
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'TFLint initialization timed out (60 seconds)'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'TFLint initialization error: {str(e)}'
            }
    
    def _parse_tflint_output(self, result: subprocess.CompletedProcess, output_format: str) -> Dict[str, Any]:
        """
        Parse TFLint command output.
        
        Args:
            result: Subprocess result from TFLint execution
            output_format: The output format used
            
        Returns:
            Parsed TFLint result
        """
        # TFLint returns exit code 2 for issues found, 0 for no issues, other codes for errors
        success = result.returncode in [0, 2]
        
        if not success:
            return {
                'success': False,
                'error': result.stderr or 'TFLint execution failed',
                'issues': [],
                'summary': {
                    'total_issues': 0,
                    'errors': 0,
                    'warnings': 0,
                    'notices': 0
                }
            }
        
        issues = []
        summary = {
            'total_issues': 0,
            'errors': 0,
            'warnings': 0,
            'notices': 0
        }
        
        if output_format == 'json' and result.stdout:
            try:
                json_output = json.loads(result.stdout)
                if isinstance(json_output, dict) and 'issues' in json_output:
                    issues = json_output['issues']
                elif isinstance(json_output, list):
                    issues = json_output
                
                # Calculate summary
                for issue in issues:
                    summary['total_issues'] += 1
                    severity = issue.get('rule', {}).get('severity', 'notice').lower()
                    if severity == 'error':
                        summary['errors'] += 1
                    elif severity == 'warning':
                        summary['warnings'] += 1
                    else:
                        summary['notices'] += 1
                        
            except json.JSONDecodeError:
                # If JSON parsing fails, treat as raw output
                pass
        
        return {
            'success': True,
            'issues': issues,
            'raw_output': result.stdout,
            'stderr': result.stderr,
            'exit_code': result.returncode,
            'summary': summary,
            'format': output_format
        }
    
    async def lint_terraform_workspace_folder(self,
                                             workspace_folder: str,
                                             output_format: str = "json",
                                             enable_azure_plugin: bool = True,
                                             enable_rules: Optional[List[str]] = None,
                                             disable_rules: Optional[List[str]] = None,
                                             initialize_plugins: bool = True,
                                             recursive: bool = False) -> Dict[str, Any]:
        """
        Run TFLint on a workspace folder containing Terraform configuration files.
        
        Args:
            workspace_folder: Path to the workspace folder containing Terraform files (relative
                paths are resolved against the configured workspace root)
            output_format: Output format (json, default, checkstyle, junit, compact, sarif)
            enable_azure_plugin: Whether to enable the Azure ruleset plugin
            enable_rules: List of specific rules to enable
            disable_rules: List of specific rules to disable
            initialize_plugins: Whether to run tflint --init to install plugins
            recursive: Whether to recursively lint subdirectories
            
        Returns:
            TFLint analysis result
        """
        if not workspace_folder or not workspace_folder.strip():
            return {
                'success': False,
                'error': 'No workspace folder provided',
                'issues': [],
                'summary': {
                    'total_issues': 0,
                    'errors': 0,
                    'warnings': 0,
                    'notices': 0
                }
            }
        
        # Resolve workspace folder path
        try:
            folder_path = str(resolve_workspace_path(workspace_folder.strip(), allow_external_absolute=True))
        except ValueError as exc:
            return {
                'success': False,
                'error': str(exc),
                'issues': [],
                'summary': {
                    'total_issues': 0,
                    'errors': 0,
                    'warnings': 0,
                    'notices': 0
                }
            }
        
        # Check if folder exists
        if not os.path.exists(folder_path):
            return {
                'success': False,
                'error': f'Workspace folder does not exist: {folder_path}',
                'issues': [],
                'summary': {
                    'total_issues': 0,
                    'errors': 0,
                    'warnings': 0,
                    'notices': 0
                }
            }
        
        if not os.path.isdir(folder_path):
            return {
                'success': False,
                'error': f'Workspace path is not a directory: {folder_path}',
                'issues': [],
                'summary': {
                    'total_issues': 0,
                    'errors': 0,
                    'warnings': 0,
                    'notices': 0
                }
            }
        
        # Check if folder contains Terraform files
        tf_files = []
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.endswith('.tf') or file.endswith('.tf.json'):
                    tf_files.append(os.path.join(root, file))
            if not recursive:
                break
        
        if not tf_files:
            return {
                'success': False,
                'error': f'No Terraform files (.tf or .tf.json) found in workspace folder: {folder_path}',
                'issues': [],
                'summary': {
                    'total_issues': 0,
                    'errors': 0,
                    'warnings': 0,
                    'notices': 0
                }
            }
        
        try:
            # Check if .tflint.hcl exists, if not create one
            tflint_config_path = os.path.join(folder_path, '.tflint.hcl')
            config_created = False
            
            if not os.path.exists(tflint_config_path):
                with open(tflint_config_path, 'w', encoding='utf-8') as f:
                    f.write(self._create_tflint_config(enable_azure_plugin))
                config_created = True
            
            # Initialize plugins if requested
            if initialize_plugins:
                init_result = await self._run_tflint_init(folder_path)
                if not init_result['success']:
                    # Clean up created config if initialization failed
                    if config_created:
                        try:
                            os.remove(tflint_config_path)
                        except:
                            pass
                    
                    return {
                        'success': False,
                        'error': f'Failed to initialize TFLint plugins: {init_result["error"]}',
                        'issues': [],
                        'summary': {
                            'total_issues': 0,
                            'errors': 0,
                            'warnings': 0,
                            'notices': 0
                        }
                    }
            
            # Build tflint command
            cmd = [self.tflint_executable, '--format', output_format]
            
            # Add rule flags
            if enable_rules:
                for rule in enable_rules:
                    cmd.extend(['--enable-rule', rule])
            
            if disable_rules:
                for rule in disable_rules:
                    cmd.extend(['--disable-rule', rule])
            
            # Add recursive flag if requested
            if recursive:
                cmd.append('--recursive')
            
            # Run TFLint
            result = subprocess.run(
                cmd,
                cwd=folder_path,
                capture_output=True,
                text=True,
                timeout=180  # Longer timeout for workspace analysis
            )
            
            # Clean up created config file if we created it
            if config_created:
                try:
                    os.remove(tflint_config_path)
                except:
                    pass
            
            analysis_result = self._parse_tflint_output(result, output_format)
            analysis_result['workspace_folder'] = folder_path
            analysis_result['terraform_files_found'] = len(tf_files)
            analysis_result['terraform_files'] = tf_files
            analysis_result['config_created'] = config_created
            
            return analysis_result
                
        except subprocess.TimeoutExpired:
            # Clean up created config if timeout occurred
            tflint_config_path = os.path.join(folder_path, '.tflint.hcl')
            config_created = False
            try:
                if os.path.exists(tflint_config_path):
                    # Only remove if we created it - simple heuristic
                    os.remove(tflint_config_path)
            except:
                pass
            
            return {
                'success': False,
                'error': 'TFLint execution timed out (180 seconds)',
                'issues': [],
                'summary': {
                    'total_issues': 0,
                    'errors': 0,
                    'warnings': 0,
                    'notices': 0
                }
            }
        except Exception as e:
            # Clean up created config if error occurred
            tflint_config_path = os.path.join(folder_path, '.tflint.hcl')
            try:
                if os.path.exists(tflint_config_path):
                    # Only remove if we created it - simple heuristic
                    os.remove(tflint_config_path)
            except:
                pass
            
            return {
                'success': False,
                'error': f'TFLint execution error: {str(e)}',
                'issues': [],
                'summary': {
                    'total_issues': 0,
                    'errors': 0,
                    'warnings': 0,
                    'notices': 0
                }
            }

    async def check_tflint_installation(self) -> Dict[str, Any]:
        """
        Check if TFLint is installed and get version information.
        
        Returns:
            Installation status and version information
        """
        try:
            result = subprocess.run(
                [self.tflint_executable, '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return {
                    'installed': True,
                    'version': result.stdout.strip(),
                    'executable_path': self.tflint_executable
                }
            else:
                return {
                    'installed': False,
                    'error': result.stderr or 'Failed to get version',
                    'executable_path': self.tflint_executable
                }
                
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            return {
                'installed': False,
                'error': f'TFLint not found or not accessible: {str(e)}',
                'executable_path': self.tflint_executable,
                'installation_help': {
                    'description': 'TFLint is not installed or not in PATH',
                    'install_methods': {
                        'homebrew_macos': 'brew install tflint',
                        'chocolatey_windows': 'choco install tflint',
                        'bash_linux': 'curl -s https://raw.githubusercontent.com/terraform-linters/tflint/master/install_linux.sh | bash',
                        'direct_download': 'Download from https://github.com/terraform-linters/tflint/releases'
                    }
                }
            }


# Singleton instance
_tflint_runner = None


def get_tflint_runner() -> TFLintRunner:
    """
    Get the singleton TFLint runner instance.
    
    Returns:
        TFLint runner instance
    """
    global _tflint_runner
    if _tflint_runner is None:
        _tflint_runner = TFLintRunner()
    return _tflint_runner
