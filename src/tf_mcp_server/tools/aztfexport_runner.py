"""
Azure Export for Terraform (aztfexport) utilities for Azure Terraform MCP Server.
"""

import asyncio
import json
import logging
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from enum import Enum

from ..core.utils import get_workspace_root, resolve_workspace_path

logger = logging.getLogger(__name__)


class AztfexportProvider(Enum):
    """Supported Terraform providers for aztfexport."""
    AZURERM = "azurerm"
    AZAPI = "azapi"


class AztfexportCommand(Enum):
    """Supported aztfexport commands."""
    RESOURCE = "resource"
    RESOURCE_GROUP = "resource-group"
    QUERY = "query"


class AztfexportRunner:
    """Azure Export for Terraform command execution utilities."""
    
    def __init__(self):
        """Initialize the aztfexport runner."""
        self._check_dependencies()
    
    def _check_dependencies(self) -> None:
        """Check if required dependencies are installed."""
        # Check if aztfexport is available
        if not shutil.which("aztfexport"):
            raise RuntimeError("aztfexport is not installed or not available in PATH. "
                             "Please install it from: https://github.com/Azure/aztfexport/releases")
        
        # Check if terraform is available
        if not shutil.which("terraform"):
            raise RuntimeError("terraform is not installed or not available in PATH. "
                             "aztfexport requires terraform >= v0.12")
    
    async def _run_command(self, command: List[str], cwd: Optional[str] = None) -> Dict[str, Any]:
        """
        Run a command asynchronously and return the result.
        
        Args:
            command: Command and arguments to execute
            cwd: Working directory for the command
            
        Returns:
            Dictionary with exit_code, stdout, stderr
        """
        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd
            )
            
            stdout, stderr = await process.communicate()
            
            return {
                'exit_code': process.returncode,
                'stdout': stdout.decode('utf-8', errors='ignore'),
                'stderr': stderr.decode('utf-8', errors='ignore'),
                'command': ' '.join(command)
            }
            
        except Exception as e:
            return {
                'exit_code': -1,
                'stdout': '',
                'stderr': f'Failed to execute command: {str(e)}',
                'command': ' '.join(command)
            }
    
    async def check_installation(self) -> Dict[str, Any]:
        """
        Check aztfexport installation and get version information.
        
        Returns:
            Installation status and version information
        """
        try:
            # Check aztfexport version
            result = await self._run_command(['aztfexport', '--version'])
            
            if result['exit_code'] == 0:
                version = result['stdout'].strip()
                
                # Check terraform version
                tf_result = await self._run_command(['terraform', '--version'])
                tf_version = tf_result['stdout'].strip() if tf_result['exit_code'] == 0 else "Unknown"
                
                return {
                    'installed': True,
                    'aztfexport_version': version,
                    'terraform_version': tf_version,
                    'status': 'Ready to use'
                }
            else:
                return {
                    'installed': False,
                    'error': result['stderr'],
                    'status': 'Installation check failed'
                }
                
        except Exception as e:
            return {
                'installed': False,
                'error': str(e),
                'status': 'Failed to check installation',
                'installation_help': self._get_installation_help()
            }
    
    def _get_installation_help(self) -> Dict[str, str]:
        """Get installation help for different platforms."""
        return {
            'windows': 'winget install aztfexport',
            'macos': 'brew install aztfexport',
            'linux_apt': 'apt-get install aztfexport (after adding Microsoft repository)',
            'linux_dnf': 'dnf install aztfexport (after adding Microsoft repository)',
            'go': 'go install github.com/Azure/aztfexport@latest',
            'releases': 'Download from https://github.com/Azure/aztfexport/releases'
        }
    
    def _generate_output_folder_name(self, prefix: str = "aztfexport") -> str:
        """
        Generate a unique, non-repeatable output folder name.
        
        Args:
            prefix: Prefix for the folder name
            
        Returns:
            Unique folder name with timestamp and random component
        """
        import time
        import random
        import string
        
        timestamp = int(time.time())
        random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        return f"{prefix}_{timestamp}_{random_suffix}"
    
    def _get_output_directory(self, output_folder_name: Optional[str] = None) -> Path:
        """
        Get the output directory path, creating it if necessary.
        
        Args:
            output_folder_name: Custom folder name to create under the workspace root, or None for auto-generated
            
        Returns:
            Path object for the output directory
        """
        workspace_root = get_workspace_root()

        if output_folder_name:
            # Use provided folder name relative to the workspace root
            work_dir = resolve_workspace_path(output_folder_name)
        else:
            # Generate unique folder name within the workspace root
            folder_name = self._generate_output_folder_name()
            work_dir = workspace_root / folder_name
        
        # Create directory if it doesn't exist
        work_dir.mkdir(parents=True, exist_ok=True)
        return work_dir

    async def export_resource(
        self,
        resource_id: str,
        output_folder_name: Optional[str] = None,
        provider: AztfexportProvider = AztfexportProvider.AZURERM,
        resource_name: Optional[str] = None,
        resource_type: Optional[str] = None,
        dry_run: bool = False,
        include_role_assignment: bool = False,
        parallelism: int = 10,
        continue_on_error: bool = False
    ) -> Dict[str, Any]:
        """
        Export a single Azure resource to Terraform configuration.
        
        Args:
            resource_id: Azure resource ID to export
            output_folder_name: Folder name for generated files (created under /workspace)
            provider: Terraform provider to use (azurerm or azapi)
            resource_name: Custom resource name in Terraform
            resource_type: Custom resource type in Terraform
            dry_run: Perform a dry run without creating files
            include_role_assignment: Include role assignments in export
            parallelism: Number of parallel operations
            continue_on_error: Continue export even if some resources fail
            
        Returns:
            Export result with generated files and status
        """
        try:
            # Get output directory
            work_dir = self._get_output_directory(output_folder_name)
            
            # Build command
            command = ['aztfexport', 'resource']
            
            # Add non-interactive flags for containerized environments
            command.extend(['--non-interactive', '--plain-ui'])
            
            # Add provider flag
            if provider == AztfexportProvider.AZAPI:
                command.extend(['--provider-name', 'azapi'])
            
            # Add options
            if resource_name:
                command.extend(['--name', resource_name])
            
            if resource_type:
                command.extend(['--type', resource_type])
            
            if dry_run:
                command.append('--dry-run')
            
            if include_role_assignment:
                command.append('--include-role-assignment')
            
            command.extend(['--parallelism', str(parallelism)])
            
            if continue_on_error:
                command.append('--continue')
            
            # Add resource ID
            command.append(resource_id)
            
            # Execute command
            result = await self._run_command(command, str(work_dir))
            
            # Process results
            export_result = {
                'exit_code': result['exit_code'],
                'command': result['command'],
                'stdout': result['stdout'],
                'stderr': result['stderr'],
                'success': result['exit_code'] == 0,
                'output_directory': str(work_dir),
                'generated_files': {}
            }
            
            # If successful, read generated files
            if result['exit_code'] == 0:
                export_result['generated_files'] = await self._read_generated_files(work_dir)
            
            return export_result
            
        except Exception as e:
            return {
                'exit_code': -1,
                'success': False,
                'error': str(e)
            }
    
    async def export_resource_group(
        self,
        resource_group_name: str,
        output_folder_name: Optional[str] = None,
        provider: AztfexportProvider = AztfexportProvider.AZURERM,
        name_pattern: Optional[str] = None,
        type_pattern: Optional[str] = None,
        dry_run: bool = False,
        include_role_assignment: bool = False,
        parallelism: int = 10,
        continue_on_error: bool = False
    ) -> Dict[str, Any]:
        """
        Export Azure resource group and its resources to Terraform configuration.
        
        Args:
            resource_group_name: Name of the resource group to export
            output_folder_name: Folder name for generated files (created under /workspace)
            provider: Terraform provider to use (azurerm or azapi)
            name_pattern: Pattern for resource naming in Terraform
            type_pattern: Pattern for resource type filtering
            dry_run: Perform a dry run without creating files
            include_role_assignment: Include role assignments in export
            parallelism: Number of parallel operations
            continue_on_error: Continue export even if some resources fail
            
        Returns:
            Export result with generated files and status
        """
        try:
            # Get output directory
            work_dir = self._get_output_directory(output_folder_name)
            
            # Build command
            command = ['aztfexport', 'resource-group']
            
            # Add non-interactive flags for containerized environments
            command.extend(['--non-interactive', '--plain-ui'])
            
            # Add provider flag
            if provider == AztfexportProvider.AZAPI:
                command.extend(['--provider-name', 'azapi'])
            
            # Add options
            if name_pattern:
                command.extend(['--name-pattern', name_pattern])
            
            if type_pattern:
                command.extend(['--type-pattern', type_pattern])
            
            if dry_run:
                command.append('--dry-run')
            
            if include_role_assignment:
                command.append('--include-role-assignment')
            
            command.extend(['--parallelism', str(parallelism)])
            
            if continue_on_error:
                command.append('--continue')
            
            # Add resource group name
            command.append(resource_group_name)
            
            # Execute command
            result = await self._run_command(command, str(work_dir))
            
            # Process results
            export_result = {
                'exit_code': result['exit_code'],
                'command': result['command'],
                'stdout': result['stdout'],
                'stderr': result['stderr'],
                'success': result['exit_code'] == 0,
                'output_directory': str(work_dir),
                'generated_files': {}
            }
            
            # If successful, read generated files
            if result['exit_code'] == 0:
                export_result['generated_files'] = await self._read_generated_files(work_dir)
            
            return export_result
            
        except Exception as e:
            return {
                'exit_code': -1,
                'success': False,
                'error': str(e)
            }
    
    async def export_query(
        self,
        query: str,
        output_folder_name: Optional[str] = None,
        provider: AztfexportProvider = AztfexportProvider.AZURERM,
        name_pattern: Optional[str] = None,
        type_pattern: Optional[str] = None,
        dry_run: bool = False,
        include_role_assignment: bool = False,
        parallelism: int = 10,
        continue_on_error: bool = False
    ) -> Dict[str, Any]:
        """
        Export Azure resources using Azure Resource Graph query to Terraform configuration.
        
        Args:
            query: Azure Resource Graph query (WHERE clause)
            output_folder_name: Folder name for generated files (created under /workspace)
            provider: Terraform provider to use (azurerm or azapi)
            name_pattern: Pattern for resource naming in Terraform
            type_pattern: Pattern for resource type filtering
            dry_run: Perform a dry run without creating files
            include_role_assignment: Include role assignments in export
            parallelism: Number of parallel operations
            continue_on_error: Continue export even if some resources fail
            
        Returns:
            Export result with generated files and status
        """
        try:
            # Get output directory
            work_dir = self._get_output_directory(output_folder_name)
            
            # Build command
            command = ['aztfexport', 'query']
            
            # Add non-interactive flags for containerized environments
            command.extend(['--non-interactive', '--plain-ui'])
            
            # Add provider flag
            if provider == AztfexportProvider.AZAPI:
                command.extend(['--provider-name', 'azapi'])
            
            # Add options
            if name_pattern:
                command.extend(['--name-pattern', name_pattern])
            
            if type_pattern:
                command.extend(['--type-pattern', type_pattern])
            
            if dry_run:
                command.append('--dry-run')
            
            if include_role_assignment:
                command.append('--include-role-assignment')
            
            command.extend(['--parallelism', str(parallelism)])
            
            if continue_on_error:
                command.append('--continue')
            
            # Add query
            command.append(query)
            
            # Execute command
            result = await self._run_command(command, str(work_dir))
            
            # Process results
            export_result = {
                'exit_code': result['exit_code'],
                'command': result['command'],
                'stdout': result['stdout'],
                'stderr': result['stderr'],
                'success': result['exit_code'] == 0,
                'output_directory': str(work_dir),
                'generated_files': {}
            }
            
            # If successful, read generated files
            if result['exit_code'] == 0:
                export_result['generated_files'] = await self._read_generated_files(work_dir)
            
            return export_result
            
        except Exception as e:
            return {
                'exit_code': -1,
                'success': False,
                'error': str(e)
            }
    
    async def _read_generated_files(self, directory: Path) -> Dict[str, str]:
        """
        Read generated Terraform files from the output directory.
        
        Args:
            directory: Output directory path
            
        Returns:
            Dictionary mapping filename to content
        """
        files = {}
        try:
            # Common Terraform files generated by aztfexport
            terraform_files = [
                'main.tf',
                'terraform.tf',
                'provider.tf',
                'variables.tf',
                'outputs.tf',
                'terraform.tfstate',
                'import.tf'
            ]
            
            for file_path in directory.iterdir():
                if file_path.is_file():
                    try:
                        # Read text files
                        if file_path.suffix in ['.tf', '.tfvars', '.json'] or file_path.name in terraform_files:
                            content = file_path.read_text(encoding='utf-8', errors='ignore')
                            files[file_path.name] = content
                    except Exception as e:
                        logger.warning(f"Failed to read file {file_path}: {e}")
                        files[file_path.name] = f"Error reading file: {e}"
            
            return files
            
        except Exception as e:
            logger.error(f"Failed to read generated files: {e}")
            return {}
    
    async def get_config(self, key: Optional[str] = None) -> Dict[str, Any]:
        """
        Get aztfexport configuration.
        
        Args:
            key: Specific config key to retrieve (optional)
            
        Returns:
            Configuration data
        """
        try:
            if key:
                result = await self._run_command(['aztfexport', 'config', 'get', key])
            else:
                result = await self._run_command(['aztfexport', 'config', 'show'])
            
            if result['exit_code'] == 0:
                try:
                    # Try to parse as JSON if it looks like JSON
                    config_data = json.loads(result['stdout'])
                    return {
                        'success': True,
                        'config': config_data
                    }
                except json.JSONDecodeError:
                    # Return as plain text if not JSON
                    return {
                        'success': True,
                        'config': result['stdout'].strip()
                    }
            else:
                return {
                    'success': False,
                    'error': result['stderr'],
                    'stdout': result['stdout']
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def set_config(self, key: str, value: str) -> Dict[str, Any]:
        """
        Set aztfexport configuration.
        
        Args:
            key: Configuration key to set
            value: Configuration value to set
            
        Returns:
            Operation result
        """
        try:
            result = await self._run_command(['aztfexport', 'config', 'set', key, value])
            
            return {
                'success': result['exit_code'] == 0,
                'exit_code': result['exit_code'],
                'stdout': result['stdout'],
                'stderr': result['stderr']
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }


# Global instance
_aztfexport_runner = None


def get_aztfexport_runner() -> AztfexportRunner:
    """Get the global aztfexport runner instance."""
    global _aztfexport_runner
    if _aztfexport_runner is None:
        _aztfexport_runner = AztfexportRunner()
    return _aztfexport_runner