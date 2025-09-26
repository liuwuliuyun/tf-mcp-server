"""
Terraform execution utilities for Azure Terraform MCP Server.
"""

import asyncio
import json
import logging
import re
import shutil
import subprocess
import tempfile
from asyncio.subprocess import Process
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from .models import ValidationResult
from .utils import extract_hcl_from_markdown, extract_error_messages

logger = logging.getLogger(__name__)


class TerraformExecutor:
    """Terraform HCL execution and validation utilities."""
    
    def __init__(self, max_instances: int = 10):
        """
        Initialize the Terraform executor.
        
        Args:
            max_instances: Maximum number of executor instances to maintain
        """
        self.max_instances = max_instances
        self.pool: asyncio.Queue = asyncio.Queue(max_instances)
        self.lock = asyncio.Lock()
        self._initialized = False
    
    async def init_tf(self) -> None:
        """Initialize Terraform in a temporary directory."""
        if self._initialized:
            return
        
        try:
            # Check if Terraform is installed
            result = await asyncio.create_subprocess_exec(
                'terraform', 'version',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            if result.returncode != 0:
                raise RuntimeError(f"Terraform not found or not working: {stderr.decode()}")
            
            logger.info(f"Terraform version: {stdout.decode().strip()}")
            self._initialized = True
            
        except FileNotFoundError:
            raise RuntimeError("Terraform binary not found. Please install Terraform.")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Terraform: {e}")
    
    def clean_up(self) -> None:
        """Clean up temporary resources."""
        while not self.pool.empty():
            try:
                item = self.pool.get_nowait()
                if hasattr(item, 'clean_tmp'):
                    item.clean_tmp()
            except asyncio.QueueEmpty:
                break
    
    @asynccontextmanager
    async def get_instance(self):
        """Get an executor instance with proper resource management."""
        async with self.lock:
            if not self._initialized:
                await self.init_tf()
            yield self
    
    async def validate_hcl(self, hcl_content: str, file_name: str = "main.tf") -> ValidationResult:
        """
        Validate HCL content using Terraform.
        
        Args:
            hcl_content: HCL content to validate
            file_name: Name for the temporary file
            
        Returns:
            ValidationResult with validation details
        """
        if not hcl_content.strip():
            return ValidationResult(
                is_valid=False,
                errors=["Empty HCL content provided"],
                file_path=file_name
            )
        
        # Extract HCL from markdown if needed
        extracted_hcl = extract_hcl_from_markdown(hcl_content)
        if extracted_hcl:
            hcl_content = extracted_hcl
        
        # Create temporary directory for validation
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            tf_file = temp_path / file_name
            
            try:
                # Write HCL content to temporary file
                tf_file.write_text(hcl_content, encoding='utf-8')
                
                # Run terraform validate
                result = await self._run_terraform_command(['validate'], str(temp_path))
                
                if result['exit_code'] == 0:
                    return ValidationResult(
                        is_valid=True,
                        file_path=str(tf_file)
                    )
                else:
                    # Parse validation errors
                    errors = self._parse_terraform_errors(result['stderr'])
                    return ValidationResult(
                        is_valid=False,
                        errors=errors,
                        file_path=str(tf_file)
                    )
                    
            except Exception as e:
                logger.error(f"Error during HCL validation: {e}")
                return ValidationResult(
                    is_valid=False,
                    errors=[f"Validation error: {str(e)}"],
                    file_path=str(tf_file)
                )
    
    async def plan_terraform(self, working_dir: str, var_file: Optional[str] = None, strip_ansi: bool = True) -> Dict[str, Any]:
        """
        Run terraform plan in the specified directory.
        
        Args:
            working_dir: Directory containing Terraform files
            var_file: Optional variables file
            strip_ansi: Whether to clean ANSI codes from output
            
        Returns:
            Plan execution result
        """
        cmd = ['plan', '-no-color', '-detailed-exitcode']
        
        if var_file:
            cmd.extend(['-var-file', var_file])
        
        return await self._run_terraform_command(cmd, working_dir, strip_ansi)
    
    async def init_terraform(self, working_dir: str, upgrade: bool = False, strip_ansi: bool = True) -> Dict[str, Any]:
        """
        Run terraform init in the specified directory.
        
        Args:
            working_dir: Directory to initialize
            upgrade: Whether to upgrade modules and providers
            strip_ansi: Whether to clean ANSI codes from output
            
        Returns:
            Initialization result
        """
        cmd = ['init', '-no-color']
        if upgrade:
            cmd.append('-upgrade')
        return await self._run_terraform_command(cmd, working_dir, strip_ansi)
    
    async def apply_terraform(self, working_dir: str, var_file: Optional[str] = None, auto_approve: bool = False, strip_ansi: bool = True) -> Dict[str, Any]:
        """
        Run terraform apply in the specified directory.
        
        Args:
            working_dir: Directory containing Terraform files
            var_file: Optional variables file
            auto_approve: Whether to automatically approve the apply
            strip_ansi: Whether to clean ANSI codes from output
            
        Returns:
            Apply execution result
        """
        cmd = ['apply', '-no-color']
        
        if auto_approve:
            cmd.append('-auto-approve')
        
        if var_file:
            cmd.extend(['-var-file', var_file])
        
        return await self._run_terraform_command(cmd, working_dir, strip_ansi)
    
    async def destroy_terraform(self, working_dir: str, var_file: Optional[str] = None, auto_approve: bool = False, strip_ansi: bool = True) -> Dict[str, Any]:
        """
        Run terraform destroy in the specified directory.
        
        Args:
            working_dir: Directory containing Terraform files
            var_file: Optional variables file
            auto_approve: Whether to automatically approve the destroy
            strip_ansi: Whether to clean ANSI codes from output
            
        Returns:
            Destroy execution result
        """
        cmd = ['destroy', '-no-color']
        
        if auto_approve:
            cmd.append('-auto-approve')
        
        if var_file:
            cmd.extend(['-var-file', var_file])
        
        return await self._run_terraform_command(cmd, working_dir, strip_ansi)
    
    async def refresh_terraform(self, working_dir: str, var_file: Optional[str] = None, strip_ansi: bool = True) -> Dict[str, Any]:
        """
        Run terraform refresh in the specified directory.
        
        Args:
            working_dir: Directory containing Terraform files
            var_file: Optional variables file
            strip_ansi: Whether to clean ANSI codes from output
            
        Returns:
            Refresh execution result
        """
        cmd = ['refresh', '-no-color']
        
        if var_file:
            cmd.extend(['-var-file', var_file])
        
        return await self._run_terraform_command(cmd, working_dir, strip_ansi)
    
    async def show_terraform(self, working_dir: str, state_file: Optional[str] = None, strip_ansi: bool = True) -> Dict[str, Any]:
        """
        Run terraform show in the specified directory.
        
        Args:
            working_dir: Directory containing Terraform files
            state_file: Optional state file to show
            strip_ansi: Whether to clean ANSI codes from output
            
        Returns:
            Show execution result
        """
        cmd = ['show', '-no-color']
        
        if state_file:
            cmd.append(state_file)
        
        return await self._run_terraform_command(cmd, working_dir, strip_ansi)
    
    async def output_terraform(self, working_dir: str, output_name: Optional[str] = None, json_format: bool = False, strip_ansi: bool = True) -> Dict[str, Any]:
        """
        Run terraform output in the specified directory.
        
        Args:
            working_dir: Directory containing Terraform files
            output_name: Optional specific output to retrieve
            json_format: Whether to return output in JSON format
            strip_ansi: Whether to clean ANSI codes from output
            
        Returns:
            Output execution result with parsed outputs if JSON format
        """
        cmd = ['output', '-no-color']
        
        if json_format:
            cmd.append('-json')
        
        if output_name:
            cmd.append(output_name)
        
        result = await self._run_terraform_command(cmd, working_dir, strip_ansi)
        
        # Parse JSON outputs if requested and successful
        if json_format and result['exit_code'] == 0 and result['stdout']:
            try:
                raw_outputs = json.loads(result['stdout'])
                processed_outputs = {}
                
                for key, value in raw_outputs.items():
                    # Terraform outputs in JSON format have a nested structure
                    # with 'value', 'type', and sometimes 'sensitive'
                    if isinstance(value, dict) and 'value' in value:
                        processed_outputs[key] = value['value']
                    else:
                        processed_outputs[key] = value
                
                result['outputs'] = processed_outputs
                logger.info(f'Extracted {len(processed_outputs)} Terraform outputs')
            except json.JSONDecodeError as e:
                logger.warning(f'Failed to parse Terraform outputs JSON: {e}')
                result['outputs'] = None
        
        return result
    
    async def workspace_list(self, working_dir: str, strip_ansi: bool = True) -> Dict[str, Any]:
        """
        List Terraform workspaces.
        
        Args:
            working_dir: Directory containing Terraform files
            strip_ansi: Whether to clean ANSI codes from output
            
        Returns:
            Workspace list result
        """
        return await self._run_terraform_command(['workspace', 'list'], working_dir, strip_ansi)
    
    async def workspace_select(self, working_dir: str, workspace_name: str, strip_ansi: bool = True) -> Dict[str, Any]:
        """
        Select a Terraform workspace.
        
        Args:
            working_dir: Directory containing Terraform files
            workspace_name: Name of the workspace to select
            strip_ansi: Whether to clean ANSI codes from output
            
        Returns:
            Workspace selection result
        """
        return await self._run_terraform_command(['workspace', 'select', workspace_name], working_dir, strip_ansi)
    
    async def workspace_new(self, working_dir: str, workspace_name: str, strip_ansi: bool = True) -> Dict[str, Any]:
        """
        Create a new Terraform workspace.
        
        Args:
            working_dir: Directory containing Terraform files
            workspace_name: Name of the new workspace
            strip_ansi: Whether to clean ANSI codes from output
            
        Returns:
            Workspace creation result
        """
        return await self._run_terraform_command(['workspace', 'new', workspace_name], working_dir, strip_ansi)

    async def execute_in_workspace(
        self, 
        command: str, 
        workspace_path: str, 
        strip_ansi: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute a generic Terraform command in a workspace directory.
        
        Args:
            command: The Terraform command to execute (e.g., 'validate', 'plan', 'apply')
            workspace_path: Path to the workspace directory containing Terraform files
            strip_ansi: Whether to clean ANSI codes from output
            **kwargs: Additional command-specific arguments
            
        Returns:
            Command execution result with stdout, stderr, exit_code
        """
        # Build the command list
        cmd_parts = [command]
        
        # Handle common command-specific options
        if command == 'plan':
            if kwargs.get('var_file'):
                cmd_parts.extend(['-var-file', kwargs['var_file']])
            if kwargs.get('detailed_exitcode'):
                cmd_parts.append('-detailed-exitcode')
        elif command == 'apply':
            if kwargs.get('var_file'):
                cmd_parts.extend(['-var-file', kwargs['var_file']])
            if kwargs.get('auto_approve'):
                cmd_parts.append('-auto-approve')
        elif command == 'destroy':
            if kwargs.get('var_file'):
                cmd_parts.extend(['-var-file', kwargs['var_file']])
            if kwargs.get('auto_approve'):
                cmd_parts.append('-auto-approve')
        elif command == 'init':
            if kwargs.get('upgrade'):
                cmd_parts.append('-upgrade')
        
        # Add no-color flag for most commands (unless explicitly disabled)
        if not kwargs.get('allow_color', False):
            cmd_parts.append('-no-color')
        
        return await self._run_terraform_command(cmd_parts, workspace_path, strip_ansi)
    
    def _clean_output_text(self, text: str) -> str:
        """
        Clean output text by removing or replacing problematic Unicode characters.
        
        Args:
            text: The text to clean
            
        Returns:
            Cleaned text with ASCII-friendly replacements
        """
        if not text:
            return text

        # First remove ANSI escape sequences (color codes, cursor movement)
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        text = ansi_escape.sub('', text)

        # Remove C0 and C1 control characters (except common whitespace)
        control_chars = re.compile(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F-\x9F]')
        text = control_chars.sub('', text)

        # Replace HTML entities
        html_entities = {
            '-&gt;': '->',  # Replace HTML arrow
            '&lt;': '<',  # Less than
            '&gt;': '>',  # Greater than
            '&amp;': '&',  # Ampersand
        }
        for entity, replacement in html_entities.items():
            text = text.replace(entity, replacement)

        # Replace box-drawing and other special Unicode characters with ASCII equivalents
        unicode_chars = {
            '\u2500': '-',  # Horizontal line
            '\u2502': '|',  # Vertical line
            '\u2514': '+',  # Up and right
            '\u2518': '+',  # Up and left
            '\u2551': '|',  # Double vertical
            '\u2550': '-',  # Double horizontal
            '\u2554': '+',  # Double down and right
            '\u2557': '+',  # Double down and left
            '\u255a': '+',  # Double up and right
            '\u255d': '+',  # Double up and left
            '\u256c': '+',  # Double cross
            '\u2588': '#',  # Full block
            '\u25cf': '*',  # Black circle
            '\u2574': '-',  # Left box drawing
            '\u2576': '-',  # Right box drawing
            '\u2577': '|',  # Down box drawing
            '\u2575': '|',  # Up box drawing
        }
        for char, replacement in unicode_chars.items():
            text = text.replace(char, replacement)

        return text

    async def _run_terraform_command(self, cmd: List[str], working_dir: str, strip_ansi: bool = True) -> Dict[str, Any]:
        """
        Run a Terraform command in the specified directory.
        
        Args:
            cmd: Terraform command and arguments
            working_dir: Working directory for the command
            strip_ansi: Whether to clean ANSI codes and Unicode from output
            
        Returns:
            Command execution result with structured output
        """
        full_cmd = ['terraform'] + cmd
        
        try:
            process = await asyncio.create_subprocess_exec(
                *full_cmd,
                cwd=working_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            # Decode output
            stdout_text = stdout.decode('utf-8')
            stderr_text = stderr.decode('utf-8') if stderr else ''
            
            # Clean output text if requested
            if strip_ansi:
                logger.debug('Cleaning command output text (ANSI codes and control characters)')
                stdout_text = self._clean_output_text(stdout_text)
                stderr_text = self._clean_output_text(stderr_text)
            
            return {
                'exit_code': process.returncode,
                'stdout': stdout_text,
                'stderr': stderr_text,
                'command': ' '.join(full_cmd),
                'status': 'success' if process.returncode == 0 else 'error'
            }
            
        except Exception as e:
            logger.error(f"Error running Terraform command {full_cmd}: {e}")
            return {
                'exit_code': -1,
                'stdout': '',
                'stderr': str(e),
                'command': ' '.join(full_cmd),
                'status': 'error'
            }
    
    def _parse_terraform_errors(self, stderr: str) -> List[str]:
        """
        Parse Terraform error output into structured messages.
        
        Args:
            stderr: Standard error output from Terraform
            
        Returns:
            List of error messages
        """
        errors = []
        
        if not stderr:
            return errors
        
        # Try to parse as JSON first (newer Terraform versions)
        try:
            lines = stderr.strip().split('\n')
            for line in lines:
                if line.startswith('{'):
                    error_data = json.loads(line)
                    if error_data.get('@level') == 'error':
                        message = error_data.get('@message', 'Unknown error')
                        errors.append(message)
        except (json.JSONDecodeError, ValueError):
            # Fall back to text parsing
            lines = stderr.strip().split('\n')
            current_error = []
            
            for line in lines:
                line = line.strip()
                if line.startswith('Error:') or line.startswith('╷'):
                    if current_error:
                        errors.append('\n'.join(current_error))
                        current_error = []
                    if not line.startswith('╷'):
                        current_error.append(line)
                elif line and current_error:
                    current_error.append(line)
                elif line.startswith('╵') and current_error:
                    errors.append('\n'.join(current_error))
                    current_error = []
            
            # Add any remaining error
            if current_error:
                errors.append('\n'.join(current_error))
        
        # If no structured errors found, return the raw stderr
        if not errors and stderr.strip():
            errors.append(stderr.strip())
        
        return errors


# Global executor instance management
_executor_lock = asyncio.Lock()
_executor_instance: Optional[TerraformExecutor] = None


@asynccontextmanager
async def get_terraform_executor():
    """Get the global Terraform executor instance."""
    global _executor_instance
    async with _executor_lock:
        if _executor_instance is None:
            _executor_instance = TerraformExecutor()
            await _executor_instance.init_tf()
        
        async with _executor_instance.get_instance() as executor:
            yield executor
