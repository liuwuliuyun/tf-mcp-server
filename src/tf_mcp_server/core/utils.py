"""
Utility functions for Azure Terraform MCP Server.
"""

import os
import re
import logging
from functools import lru_cache
from typing import List, Dict, Any, Optional, Union
from pathlib import Path


def strip_ansi_escape_sequences(text: Optional[str]) -> Optional[str]:
    """
    Remove ANSI escape sequences from text.
    
    Args:
        text: Text that may contain ANSI escape sequences
        
    Returns:
        Text with ANSI escape sequences removed
    """
    if not text:
        return text
    
    # Pattern to match ANSI escape sequences
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def extract_hcl_from_markdown(content: str) -> str:
    """
    Extract HCL code from markdown code blocks.
    
    Args:
        content: Markdown content that may contain HCL code blocks
        
    Returns:
        Extracted HCL content
    """
    if not content:
        return ""
    
    lines = content.split('\n')
    hcl_content = []
    in_hcl_block = False
    
    for line in lines:
        line_stripped = line.strip()
        if line_stripped.startswith('```hcl') or line_stripped.startswith('```terraform'):
            in_hcl_block = True
            continue
        elif line_stripped == '```' and in_hcl_block:
            in_hcl_block = False
            continue
        elif in_hcl_block:
            hcl_content.append(line)
    
    return '\n'.join(hcl_content)


def extract_error_messages(validation_result: Dict[str, Any]) -> List[str]:
    """
    Extract error messages from Terraform validation result.
    
    Args:
        validation_result: Result from Terraform validation
        
    Returns:
        List of formatted error messages
    """
    error_messages = []
    
    if not isinstance(validation_result, dict):
        return error_messages
    
    # Handle diagnostics format
    if 'diagnostics' in validation_result:
        for diagnostic in validation_result['diagnostics']:
            if diagnostic.get('severity') == 'error':
                summary = diagnostic.get('summary', 'Unknown error')
                detail = diagnostic.get('detail', '')
                range_info = diagnostic.get('range', {})
                
                error_msg = f"Error: {summary}"
                if detail:
                    error_msg += f"\nDetail: {detail}"
                if range_info:
                    filename = range_info.get('filename', 'unknown')
                    start = range_info.get('start', {})
                    line = start.get('line', 'unknown')
                    column = start.get('column', 'unknown')
                    error_msg += f"\nLocation: {filename}:{line}:{column}"
                
                error_messages.append(error_msg)
    
    # Handle simple error format
    elif 'error' in validation_result:
        error_messages.append(f"Validation error: {validation_result['error']}")
    
    return error_messages


def normalize_resource_type(resource_type: str) -> str:
    """
    Normalize Azure resource type for documentation lookup.
    
    Args:
        resource_type: Raw resource type string
        
    Returns:
        Normalized resource type
    """
    # Remove azurerm_ prefix if present
    normalized = resource_type.lower().replace('azurerm_', '')
    # Replace underscores with hyphens for URL
    normalized = normalized.replace('_', '-')
    return normalized


def validate_azure_name(name: str, resource_type: str) -> List[str]:
    """
    Validate Azure resource name according to Azure naming conventions.
    
    Args:
        name: Resource name to validate
        resource_type: Type of Azure resource
        
    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    
    # Common validation rules
    if not name:
        errors.append("Resource name cannot be empty")
        return errors
    
    if len(name) < 1:
        errors.append("Resource name must be at least 1 character long")
    
    if len(name) > 80:  # Most Azure resources have this limit
        errors.append("Resource name cannot exceed 80 characters")
    
    # Check for valid characters (alphanumeric, hyphens, underscores)
    if not re.match(r'^[a-zA-Z0-9\-_]+$', name):
        errors.append("Resource name can only contain letters, numbers, hyphens, and underscores")
    
    # Resource-specific rules
    if resource_type in ['storage_account', 'azurerm_storage_account']:
        if len(name) > 24:
            errors.append("Storage account name cannot exceed 24 characters")
        if not re.match(r'^[a-z0-9]+$', name):
            errors.append("Storage account name can only contain lowercase letters and numbers")
    
    elif resource_type in ['key_vault', 'azurerm_key_vault']:
        if len(name) > 24:
            errors.append("Key Vault name cannot exceed 24 characters")
        if not re.match(r'^[a-zA-Z0-9\-]+$', name):
            errors.append("Key Vault name can only contain letters, numbers, and hyphens")
    
    return errors


def format_terraform_block(resource_type: str, resource_name: str, 
                          attributes: Dict[str, Any], indent: int = 0) -> str:
    """
    Format a Terraform resource block.
    
    Args:
        resource_type: Terraform resource type
        resource_name: Resource name
        attributes: Resource attributes
        indent: Indentation level
        
    Returns:
        Formatted Terraform block
    """
    indent_str = "  " * indent
    lines = [f'{indent_str}resource "{resource_type}" "{resource_name}" {{']
    
    for key, value in attributes.items():
        if isinstance(value, str):
            lines.append(f'{indent_str}  {key} = "{value}"')
        elif isinstance(value, bool):
            lines.append(f'{indent_str}  {key} = {str(value).lower()}')
        elif isinstance(value, (int, float)):
            lines.append(f'{indent_str}  {key} = {value}')
        elif isinstance(value, list):
            if all(isinstance(item, str) for item in value):
                formatted_list = ', '.join(f'"{item}"' for item in value)
                lines.append(f'{indent_str}  {key} = [{formatted_list}]')
            else:
                lines.append(f'{indent_str}  {key} = {value}')
        elif isinstance(value, dict):
            lines.append(f'{indent_str}  {key} = {{')
            for sub_key, sub_value in value.items():
                if isinstance(sub_value, str):
                    lines.append(f'{indent_str}    {sub_key} = "{sub_value}"')
                else:
                    lines.append(f'{indent_str}    {sub_key} = {sub_value}')
            lines.append(f'{indent_str}  }}')
        else:
            lines.append(f'{indent_str}  {key} = {value}')
    
    lines.append(f'{indent_str}}}')
    return '\n'.join(lines)


def generate_terraform_variables(variables: Dict[str, Dict[str, Any]]) -> str:
    """
    Generate Terraform variables.tf content.
    
    Args:
        variables: Dictionary of variable definitions
        
    Returns:
        Formatted variables.tf content
    """
    lines = []
    
    for var_name, var_config in variables.items():
        lines.append(f'variable "{var_name}" {{')
        
        if 'description' in var_config:
            lines.append(f'  description = "{var_config["description"]}"')
        
        if 'type' in var_config:
            lines.append(f'  type        = {var_config["type"]}')
        
        if 'default' in var_config:
            default = var_config['default']
            if isinstance(default, str):
                lines.append(f'  default     = "{default}"')
            else:
                lines.append(f'  default     = {default}')
        
        if 'validation' in var_config:
            lines.append('  validation {')
            for rule in var_config['validation']:
                lines.append(f'    condition     = {rule["condition"]}')
                lines.append(f'    error_message = "{rule["error_message"]}"')
            lines.append('  }')
        
        lines.append('}')
        lines.append('')  # Empty line between variables
    
    return '\n'.join(lines)


def generate_terraform_outputs(outputs: Dict[str, Dict[str, Any]]) -> str:
    """
    Generate Terraform outputs.tf content.
    
    Args:
        outputs: Dictionary of output definitions
        
    Returns:
        Formatted outputs.tf content
    """
    lines = []
    
    for output_name, output_config in outputs.items():
        lines.append(f'output "{output_name}" {{')
        
        if 'description' in output_config:
            lines.append(f'  description = "{output_config["description"]}"')
        
        if 'value' in output_config:
            lines.append(f'  value       = {output_config["value"]}')
        
        if 'sensitive' in output_config:
            lines.append(f'  sensitive   = {str(output_config["sensitive"]).lower()}')
        
        lines.append('}')
        lines.append('')  # Empty line between outputs
    
    return '\n'.join(lines)


def safe_filename(filename: str) -> str:
    """
    Create a safe filename by removing/replacing invalid characters.
    
    Args:
        filename: Original filename
        
    Returns:
        Safe filename for filesystem use
    """
    # Replace invalid characters with underscores
    safe_name = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove any trailing dots or spaces
    safe_name = safe_name.rstrip('. ')
    # Ensure it's not empty
    if not safe_name:
        safe_name = "unnamed"
    return safe_name


@lru_cache(maxsize=1)
def get_workspace_root() -> Path:
    """
    Determine the root directory for workspace operations.

    The resolution order is:
    1. Environment variable ``MCP_WORKSPACE_ROOT`` if set
    2. ``/workspace`` when running inside containers that mount this path
    3. Current working directory as a safe fallback

    Returns:
        Path to the workspace root directory (may not exist yet)
    """
    env_path = os.getenv("MCP_WORKSPACE_ROOT")
    candidates = []

    if env_path:
        candidates.append(Path(env_path).expanduser())

    candidates.append(Path("/workspace"))
    candidates.append(Path.cwd())

    for index, candidate in enumerate(candidates):
        try:
            resolved = candidate.resolve(strict=False)
        except (FileNotFoundError, RuntimeError):
            resolved = candidate

        if resolved.exists():
            return resolved

        # Try to create the path when explicitly configured via env var
        if index == 0 and env_path:
            try:
                resolved.mkdir(parents=True, exist_ok=True)
                return resolved.resolve(strict=False)
            except Exception:
                continue

    # Fall back to the last candidate even if it doesn't exist yet
    fallback = candidates[-1]
    try:
        return fallback.resolve(strict=False)
    except (FileNotFoundError, RuntimeError):
        return fallback


def resolve_workspace_path(
    path_like: Optional[Union[str, Path]],
    *,
    allow_external_absolute: bool = False
) -> Path:
    """
    Resolve a workspace-relative path to an absolute location.

    Args:
        path_like: Relative or absolute path provided by the caller
        allow_external_absolute: When False (default), absolute paths must reside
            within the workspace root. Set to True to allow arbitrary absolute paths.

    Returns:
        Absolute path pointing to the requested location

    Raises:
        ValueError: If an absolute path outside the workspace root is provided
                    while ``allow_external_absolute`` is False.
    """
    workspace_root = get_workspace_root().resolve(strict=False)

    if not path_like or (isinstance(path_like, str) and not path_like.strip()):
        return workspace_root

    candidate = Path(path_like).expanduser()

    if candidate.is_absolute():
        resolved = candidate.resolve(strict=False)

        if allow_external_absolute:
            return resolved

        try:
            resolved.relative_to(workspace_root)
            return resolved
        except ValueError as exc:
            raise ValueError(
                f"Path '{resolved}' is outside the configured workspace root '{workspace_root}'"
            ) from exc

    resolved = (workspace_root / candidate).resolve(strict=False)
    return resolved
