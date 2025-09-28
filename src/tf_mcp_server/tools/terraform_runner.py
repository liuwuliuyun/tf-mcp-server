"""
Terraform command execution utilities for Azure Terraform MCP Server.
"""

from pathlib import Path
from typing import Any, Dict
from ..core.terraform_executor import get_terraform_executor
from ..core.utils import resolve_workspace_path


class TerraformRunner:
    """Terraform command execution utilities with simplified interface."""
    
    async def execute_terraform_command(
        self,
        command: str,
        workspace_folder: str,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Execute a Terraform command within an existing workspace directory.
        
        Args:
            command: Terraform command to execute ('init', 'plan', 'apply', 'validate', etc.)
            workspace_folder: Workspace folder containing Terraform files
            **kwargs: Additional command-specific arguments passed to the executor
            
        Returns:
            Execution result with stdout, stderr, exit_code
        """
        workspace_name = workspace_folder.strip()
        if not workspace_name:
            return {
                'exit_code': -1,
                'stdout': '',
                'stderr': 'workspace_folder is required',
                'command': command
            }

        try:
            async with get_terraform_executor() as executor:
                exec_kwargs = dict(kwargs)
                strip_ansi = exec_kwargs.pop('strip_ansi', True)

                try:
                    workspace_path = resolve_workspace_path(workspace_name)
                except ValueError as exc:
                    return {
                        'exit_code': -1,
                        'stdout': '',
                        'stderr': str(exc),
                        'command': command
                    }

                workspace_path = workspace_path.resolve(strict=False)

                if not workspace_path.exists():
                    return {
                        'exit_code': -1,
                        'stdout': '',
                        'stderr': f"Workspace folder does not exist: {workspace_path}",
                        'command': command
                    }

                if not workspace_path.is_dir():
                    return {
                        'exit_code': -1,
                        'stdout': '',
                        'stderr': f"Workspace path is not a directory: {workspace_path}",
                        'command': command
                    }

                if not self._contains_terraform_files(workspace_path):
                    return {
                        'exit_code': -1,
                        'stdout': '',
                        'stderr': f"No Terraform files (.tf or .tf.json) found in workspace folder: {workspace_path}",
                        'command': command
                    }

                return await executor.execute_in_workspace(
                    command=command,
                    workspace_path=str(workspace_path),
                    strip_ansi=strip_ansi,
                    **exec_kwargs
                )

        except Exception as e:
            return {
                'exit_code': -1,
                'stdout': '',
                'stderr': f'Command execution error: {str(e)}',
                'command': command
            }
    @staticmethod
    def _contains_terraform_files(workspace_path: Path) -> bool:
        """Check whether the workspace contains Terraform files."""
        try:
            for pattern in ("*.tf", "*.tf.json"):
                if next(workspace_path.rglob(pattern), None) is not None:
                    return True
        except (OSError, PermissionError):
            return False
        return False


# Global instance
_terraform_runner = None


def get_terraform_runner() -> TerraformRunner:
    """Get the global Terraform runner instance."""
    global _terraform_runner
    if _terraform_runner is None:
        _terraform_runner = TerraformRunner()
    return _terraform_runner
