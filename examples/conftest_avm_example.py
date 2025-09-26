"""
Example demonstrating how to use the Conftest AVM runner for Azure policy validation
with the workspace- and plan-based tooling.
"""

import asyncio
import json
import os
import shutil
import sys
import textwrap
from pathlib import Path
from uuid import uuid4

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tf_mcp_server.core.utils import get_workspace_root
from tf_mcp_server.tools.conftest_avm_runner import get_conftest_avm_runner


SAMPLE_HCL = """
terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~>3.0"
    }
  }
}

provider "azurerm" {
  features {}
}

resource "azurerm_resource_group" "example" {
  name     = "example-rg"
  location = "West Europe"

  tags = {
    Environment = "Test"
  }
}

resource "azurerm_storage_account" "example" {
  name                     = "examplestorageacct"
  resource_group_name      = azurerm_resource_group.example.name
  location                 = azurerm_resource_group.example.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  allow_nested_items_to_be_public = true

  tags = {
    Environment = "Test"
  }
}
"""

SAMPLE_PLAN_JSON = {
    "format_version": "1.1",
    "terraform_version": "1.5.0",
    "planned_values": {
        "root_module": {
            "resources": [
                {
                    "address": "azurerm_storage_account.example",
                    "mode": "managed",
                    "type": "azurerm_storage_account",
                    "values": {
                        "name": "examplestorage",
                        "resource_group_name": "example-rg",
                        "location": "West Europe",
                        "account_tier": "Standard",
                        "account_replication_type": "LRS",
                        "allow_nested_items_to_be_public": True,
                        "min_tls_version": "TLS1_0"
                    }
                }
            ]
        }
    }
}


def _create_workspace() -> tuple[Path, str]:
    """Create a temporary Terraform workspace containing the sample configuration."""
    workspace_root = get_workspace_root()
    workspace_root.mkdir(parents=True, exist_ok=True)

    folder_name = f"conftest-avm-example-{uuid4().hex}"
    workspace_dir = workspace_root / folder_name
    workspace_dir.mkdir(parents=True, exist_ok=True)

    (workspace_dir / "main.tf").write_text(textwrap.dedent(SAMPLE_HCL).strip() + "\n", encoding="utf-8")
    return workspace_dir, folder_name


def _print_result(title: str, result: dict) -> None:
    """Pretty-print Conftest results."""
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)

    success = result.get("success", False)
    print(f"Success: {success}")

    if "policy_set" in result:
        print(f"Policy Set: {result['policy_set']}")
    if "severity_filter" in result and result['severity_filter']:
        print(f"Severity Filter: {result['severity_filter']}")

    summary = result.get("summary", {})
    if summary:
        print(f"Total Violations: {summary.get('total_violations', 'n/a')}")

    if success and result.get("violations"):
        print("\nViolations:")
        for idx, violation in enumerate(result["violations"], start=1):
            policy = violation.get("policy", "unknown-policy")
            level = violation.get("level", "warning").upper()
            message = violation.get("message", "No message provided")
            print(f"  {idx}. [{level}] {policy}\n     {message}")
    elif not success:
        error_msg = result.get("error") or result.get("command_error")
        if error_msg:
            print(f"Error: {error_msg}")
        else:
            print("Validation did not succeed; see logs for details.")


async def main() -> None:
    runner = get_conftest_avm_runner()

    workspace_dir, folder_name = _create_workspace()
    try:
        # 1. Validate the workspace folder with all policies
        workspace_result = await runner.validate_workspace_folder_with_avm_policies(
            workspace_folder=folder_name,
            policy_set="all"
        )
        _print_result("Workspace Validation (All Policies)", workspace_result)

        # 2. Validate the same workspace with avmsec high severity policies
        severity_result = await runner.validate_workspace_folder_with_avm_policies(
            workspace_folder=folder_name,
            policy_set="avmsec",
            severity_filter="high"
        )
        _print_result("Workspace Validation (avmsec High Severity)", severity_result)

        # 3. Validate a pre-generated plan JSON payload
        plan_json = json.dumps(SAMPLE_PLAN_JSON)
        plan_result = await runner.validate_with_avm_policies(
            terraform_plan_json=plan_json,
            policy_set="avmsec",
            severity_filter="medium"
        )
        _print_result("Plan JSON Validation", plan_result)

        # 4. Illustrate workspace plan validation (will run terraform plan/show)
        print("\nNote: Workspace plan validation runs `terraform plan` in the workspace.")
        workspace_plan_result = await runner.validate_workspace_folder_plan_with_avm_policies(
            folder_name=folder_name,
            policy_set="Azure-Proactive-Resiliency-Library-v2"
        )
        _print_result("Workspace Plan Validation", workspace_plan_result)

    finally:
        if workspace_dir.exists():
            shutil.rmtree(workspace_dir, ignore_errors=True)

    print("\nExamples completed. Review the output above for validation results.")


if __name__ == "__main__":
    asyncio.run(main())
