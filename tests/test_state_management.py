"""
Test cases for Terraform state management features.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Dict, Any

import pytest

from tf_mcp_server.tools.terraform_runner import TerraformRunner


@pytest.fixture
def terraform_runner() -> TerraformRunner:
    """Return a TerraformRunner instance."""
    return TerraformRunner()


class TestStateManagement:
    """Test cases for Terraform state management operations."""
    
    @pytest.mark.asyncio
    async def test_state_list_command(
        self, 
        monkeypatch: pytest.MonkeyPatch, 
        tmp_path: Path, 
        terraform_runner: TerraformRunner
    ) -> None:
        """Test state list command execution."""
        workspace_dir = tmp_path / "workspace"
        workspace_dir.mkdir()
        (workspace_dir / "main.tf").write_text("terraform {}", encoding="utf-8")

        class DummyExecutor:
            def __init__(self) -> None:
                self.call_kwargs: Dict[str, Any] | None = None

            async def execute_in_workspace(self, **kwargs: Any) -> Dict[str, Any]:
                self.call_kwargs = kwargs
                return {
                    "exit_code": 0,
                    "stdout": "azurerm_resource_group.main\nazurerm_storage_account.example",
                    "stderr": "",
                    "command": "terraform state list",
                    "status": "success",
                }

        dummy_executor = DummyExecutor()

        @asynccontextmanager
        async def fake_get_executor():
            yield dummy_executor

        def fake_resolve(path_like: str) -> Path:
            return workspace_dir

        monkeypatch.setattr(
            "tf_mcp_server.tools.terraform_runner.get_terraform_executor",
            fake_get_executor,
        )
        monkeypatch.setattr(
            "tf_mcp_server.tools.terraform_runner.resolve_workspace_path",
            fake_resolve,
        )

        result = await terraform_runner.execute_terraform_command(
            command="state list",
            workspace_folder="workspace",
        )

        assert result["exit_code"] == 0
        assert "azurerm_resource_group.main" in result["stdout"]
        assert dummy_executor.call_kwargs is not None
        assert dummy_executor.call_kwargs["command"] == "state list"

    @pytest.mark.asyncio
    async def test_state_show_command(
        self, 
        monkeypatch: pytest.MonkeyPatch, 
        tmp_path: Path, 
        terraform_runner: TerraformRunner
    ) -> None:
        """Test state show command with resource address."""
        workspace_dir = tmp_path / "workspace"
        workspace_dir.mkdir()
        (workspace_dir / "main.tf").write_text("terraform {}", encoding="utf-8")

        class DummyExecutor:
            async def execute_in_workspace(self, **kwargs: Any) -> Dict[str, Any]:
                assert kwargs["command"] == "state show azurerm_resource_group.main"
                return {
                    "exit_code": 0,
                    "stdout": "# azurerm_resource_group.main:\nresource ...",
                    "stderr": "",
                    "command": "terraform state show azurerm_resource_group.main",
                    "status": "success",
                }

        @asynccontextmanager
        async def fake_get_executor():
            yield DummyExecutor()

        def fake_resolve(path_like: str) -> Path:
            return workspace_dir

        monkeypatch.setattr(
            "tf_mcp_server.tools.terraform_runner.get_terraform_executor",
            fake_get_executor,
        )
        monkeypatch.setattr(
            "tf_mcp_server.tools.terraform_runner.resolve_workspace_path",
            fake_resolve,
        )

        result = await terraform_runner.execute_terraform_command(
            command="state show azurerm_resource_group.main",
            workspace_folder="workspace",
        )

        assert result["exit_code"] == 0
        assert "azurerm_resource_group.main" in result["stdout"]

    @pytest.mark.asyncio
    async def test_state_mv_command(
        self, 
        monkeypatch: pytest.MonkeyPatch, 
        tmp_path: Path, 
        terraform_runner: TerraformRunner
    ) -> None:
        """Test state mv command for resource renaming."""
        workspace_dir = tmp_path / "workspace"
        workspace_dir.mkdir()
        (workspace_dir / "main.tf").write_text("terraform {}", encoding="utf-8")

        class DummyExecutor:
            async def execute_in_workspace(self, **kwargs: Any) -> Dict[str, Any]:
                expected_cmd = "state mv azurerm_resource_group.res-0 azurerm_resource_group.main"
                assert kwargs["command"] == expected_cmd
                return {
                    "exit_code": 0,
                    "stdout": "Move \"azurerm_resource_group.res-0\" to \"azurerm_resource_group.main\"",
                    "stderr": "",
                    "command": f"terraform {expected_cmd}",
                    "status": "success",
                }

        @asynccontextmanager
        async def fake_get_executor():
            yield DummyExecutor()

        def fake_resolve(path_like: str) -> Path:
            return workspace_dir

        monkeypatch.setattr(
            "tf_mcp_server.tools.terraform_runner.get_terraform_executor",
            fake_get_executor,
        )
        monkeypatch.setattr(
            "tf_mcp_server.tools.terraform_runner.resolve_workspace_path",
            fake_resolve,
        )

        result = await terraform_runner.execute_terraform_command(
            command="state mv azurerm_resource_group.res-0 azurerm_resource_group.main",
            workspace_folder="workspace",
        )

        assert result["exit_code"] == 0
        assert "Move" in result["stdout"]

    @pytest.mark.asyncio
    async def test_state_rm_command(
        self, 
        monkeypatch: pytest.MonkeyPatch, 
        tmp_path: Path, 
        terraform_runner: TerraformRunner
    ) -> None:
        """Test state rm command for removing resources from state."""
        workspace_dir = tmp_path / "workspace"
        workspace_dir.mkdir()
        (workspace_dir / "main.tf").write_text("terraform {}", encoding="utf-8")

        class DummyExecutor:
            async def execute_in_workspace(self, **kwargs: Any) -> Dict[str, Any]:
                assert kwargs["command"] == "state rm azurerm_resource_group.old"
                return {
                    "exit_code": 0,
                    "stdout": "Removed azurerm_resource_group.old",
                    "stderr": "",
                    "command": "terraform state rm azurerm_resource_group.old",
                    "status": "success",
                }

        @asynccontextmanager
        async def fake_get_executor():
            yield DummyExecutor()

        def fake_resolve(path_like: str) -> Path:
            return workspace_dir

        monkeypatch.setattr(
            "tf_mcp_server.tools.terraform_runner.get_terraform_executor",
            fake_get_executor,
        )
        monkeypatch.setattr(
            "tf_mcp_server.tools.terraform_runner.resolve_workspace_path",
            fake_resolve,
        )

        result = await terraform_runner.execute_terraform_command(
            command="state rm azurerm_resource_group.old",
            workspace_folder="workspace",
        )

        assert result["exit_code"] == 0
        assert "Removed" in result["stdout"]

    @pytest.mark.asyncio
    async def test_state_pull_command(
        self, 
        monkeypatch: pytest.MonkeyPatch, 
        tmp_path: Path, 
        terraform_runner: TerraformRunner
    ) -> None:
        """Test state pull command."""
        workspace_dir = tmp_path / "workspace"
        workspace_dir.mkdir()
        (workspace_dir / "main.tf").write_text("terraform {}", encoding="utf-8")

        class DummyExecutor:
            async def execute_in_workspace(self, **kwargs: Any) -> Dict[str, Any]:
                assert kwargs["command"] == "state pull"
                return {
                    "exit_code": 0,
                    "stdout": '{"version": 4, "terraform_version": "1.0.0"}',
                    "stderr": "",
                    "command": "terraform state pull",
                    "status": "success",
                }

        @asynccontextmanager
        async def fake_get_executor():
            yield DummyExecutor()

        def fake_resolve(path_like: str) -> Path:
            return workspace_dir

        monkeypatch.setattr(
            "tf_mcp_server.tools.terraform_runner.get_terraform_executor",
            fake_get_executor,
        )
        monkeypatch.setattr(
            "tf_mcp_server.tools.terraform_runner.resolve_workspace_path",
            fake_resolve,
        )

        result = await terraform_runner.execute_terraform_command(
            command="state pull",
            workspace_folder="workspace",
        )

        assert result["exit_code"] == 0
        assert "version" in result["stdout"]

    @pytest.mark.asyncio
    async def test_state_command_with_empty_workspace(
        self,
        terraform_runner: TerraformRunner
    ) -> None:
        """Test that state commands require workspace folder."""
        result = await terraform_runner.execute_terraform_command(
            command="state list",
            workspace_folder="   ",
        )

        assert result["exit_code"] == -1
        assert "workspace_folder is required" in result["stderr"]

    @pytest.mark.asyncio
    async def test_state_command_without_tf_files(
        self, 
        monkeypatch: pytest.MonkeyPatch, 
        tmp_path: Path, 
        terraform_runner: TerraformRunner
    ) -> None:
        """Test that state commands require Terraform files."""
        workspace_dir = tmp_path / "workspace"
        workspace_dir.mkdir()

        @asynccontextmanager
        async def fake_get_executor():
            yield None

        def fake_resolve(path_like: str) -> Path:
            return workspace_dir

        monkeypatch.setattr(
            "tf_mcp_server.tools.terraform_runner.get_terraform_executor",
            fake_get_executor,
        )
        monkeypatch.setattr(
            "tf_mcp_server.tools.terraform_runner.resolve_workspace_path",
            fake_resolve,
        )

        result = await terraform_runner.execute_terraform_command(
            command="state list",
            workspace_folder="workspace",
        )

        assert result["exit_code"] == -1
        assert "No Terraform files" in result["stderr"]
