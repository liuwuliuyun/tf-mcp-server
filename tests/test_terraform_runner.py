"""
Tests for Terraform runner workspace integration.
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


@pytest.mark.asyncio
async def test_execute_command_workspace_success(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, terraform_runner: TerraformRunner) -> None:
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
                "stdout": "ok",
                "stderr": "",
                "command": "terraform plan",
                "status": "success",
            }

    dummy_executor = DummyExecutor()

    @asynccontextmanager
    async def fake_get_executor():
        yield dummy_executor

    def fake_resolve(path_like: str) -> Path:
        assert path_like == "workspace"
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
        command="plan",
        workspace_folder="workspace",
    )

    assert result["exit_code"] == 0
    assert dummy_executor.call_kwargs is not None
    assert dummy_executor.call_kwargs["command"] == "plan"
    assert dummy_executor.call_kwargs["workspace_path"] == str(workspace_dir)


@pytest.mark.asyncio
async def test_execute_command_workspace_resolve_error(monkeypatch: pytest.MonkeyPatch, terraform_runner: TerraformRunner) -> None:
    def fake_resolve(path_like: str) -> Path:
        raise ValueError("outside workspace")

    @asynccontextmanager
    async def fake_get_executor():
        yield None

    monkeypatch.setattr(
        "tf_mcp_server.tools.terraform_runner.resolve_workspace_path",
        fake_resolve,
    )
    monkeypatch.setattr(
        "tf_mcp_server.tools.terraform_runner.get_terraform_executor",
        fake_get_executor,
    )

    result = await terraform_runner.execute_terraform_command(
        command="plan",
        workspace_folder="bad",
    )

    assert result["exit_code"] == -1
    assert "outside workspace" in result["stderr"]


@pytest.mark.asyncio
async def test_execute_command_workspace_requires_tf_files(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, terraform_runner: TerraformRunner) -> None:
    workspace_dir = tmp_path / "workspace"
    workspace_dir.mkdir()

    class DummyExecutor:
        async def execute_in_workspace(self, **kwargs: Any) -> Dict[str, Any]:  # pragma: no cover - should not be called
            return {}

    @asynccontextmanager
    async def fake_get_executor():
        yield DummyExecutor()

    def fake_resolve(path_like: str) -> Path:
        return workspace_dir

    monkeypatch.setattr(
        "tf_mcp_server.tools.terraform_runner.resolve_workspace_path",
        fake_resolve,
    )
    monkeypatch.setattr(
        "tf_mcp_server.tools.terraform_runner.get_terraform_executor",
        fake_get_executor,
    )

    result = await terraform_runner.execute_terraform_command(
        command="plan",
        workspace_folder="workspace",
    )

    assert result["exit_code"] == -1
    assert "No Terraform files" in result["stderr"]


@pytest.mark.asyncio
async def test_execute_command_requires_workspace(terraform_runner: TerraformRunner) -> None:
    result = await terraform_runner.execute_terraform_command(
        command="plan",
        workspace_folder="   ",
    )

    assert result["exit_code"] == -1
    assert "workspace_folder is required" in result["stderr"]
