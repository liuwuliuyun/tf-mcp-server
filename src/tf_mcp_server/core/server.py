"""
Main server implementation for Azure Terraform MCP Server.
"""

import json
import logging
from typing import Dict, Any
from pydantic import Field
from fastmcp import FastMCP

from .config import Config
from ..tools.avm_docs_provider import get_avm_documentation_provider, ExpectedException
from ..tools.azurerm_docs_provider import get_azurerm_documentation_provider
from ..tools.azapi_docs_provider import get_azapi_documentation_provider
from ..tools.terraform_runner import get_terraform_runner
from ..tools.tflint_runner import get_tflint_runner
from ..tools.conftest_avm_runner import get_conftest_avm_runner
from ..tools.aztfexport_runner import get_aztfexport_runner

from ..tools.golang_source_provider import get_golang_source_provider

logger = logging.getLogger(__name__)


def create_server(config: Config) -> FastMCP:
    """
    Create and configure the FastMCP server.

    Args:
        config: Server configuration

    Returns:
        Configured FastMCP server instance
    """
    mcp = FastMCP("Azure Terraform MCP Server", version="0.1.0")

    # Get service instances
    avm_doc_provider = get_avm_documentation_provider()
    azurerm_doc_provider = get_azurerm_documentation_provider()
    azapi_doc_provider = get_azapi_documentation_provider()
    terraform_runner = get_terraform_runner()
    tflint_runner = get_tflint_runner()
    conftest_avm_runner = get_conftest_avm_runner()
    aztfexport_runner = get_aztfexport_runner()
    golang_source_provider = get_golang_source_provider()

    # ==========================================
    # DOCUMENTATION TOOLS
    # ==========================================

    @mcp.tool("get_avm_modules")
    def get_avm_modules() -> str:
        """Retrieves all available Azure verified modules.

        Returns:
            A list of Azure verified modules. Each item in the list contains the following fields:
            - module_name: The name of the Azure verified module, which is typically used as the input parameter of other tools.
            - description: A brief description of the module.
            - source: The value of `source` field in the module's definition. (e.g., `source = "Azure/avm-res-apimanagement-service/azurerm"`)
        """

        try:
            return avm_doc_provider.available_modules()
        except ExpectedException as e:
            return f'{str(e)}'
        except Exception as e:
            logger.error(f"Error: get_avm_modules: {str(e)}")
            return "failed to retrieve available modules"

    @mcp.tool("get_avm_latest_version")
    def get_avm_latest_version(module_name: str) -> str:
        """Retrieves the latest version of a specified Azure verified module.

        Args:
            module_name (str): The name of the Azure verified module, which is typically in the format of `avm-res-<provider>-<resource>`. (e.g., avm-res-apimanagement-service, avm-res-app-containerapp.)

        Returns:
            The latest version of the specified module.
        """
        try:
            return avm_doc_provider.latest_module_version(module_name)
        except ExpectedException as e:
            return f'{str(e)}'
        except Exception as e:
            logger.error(
                f"Error: get_avm_latest_version({module_name}): {str(e)}")
            return "failed to retrieve the latest module version"

    @mcp.tool("get_avm_versions")
    def get_avm_versions(module_name: str) -> str:
        """Retrieves all available versions of a specified Azure verified module.

        Args:
            module_name (str): The name of the Azure verified module, which is typically in the format of `avm-res-<provider>-<resource>`. (e.g., avm-res-apimanagement-service, avm-res-app-containerapp.)

        Returns:
            A list of available versions of the specified module.
        """
        try:
            return avm_doc_provider.module_versions(module_name)
        except ExpectedException as e:
            return f'{str(e)}'
        except Exception as e:
            logger.error(f"Error: get_avm_versions({module_name}): {str(e)}")
            return "failed to retrieve available module versions"

    @mcp.tool("get_avm_variables")
    def get_avm_variables(module_name: str, module_version: str) -> str:
        """Retrieves the variables of a specified Azure verified module. The variables describe the schema of the module's configuration.

        Args:
            module_name (str): The name of the Azure verified module, which is typically in the format of `avm-res-<provider>-<resource>`. (e.g., avm-res-apimanagement-service, avm-res-app-containerapp.)
            module_version (str): The version of the Azure verified module, which is the value of `version` field in the module's `.tf` file.

        Returns:
            str: A string containing the variables of the specified module.
        """
        try:
            return avm_doc_provider.module_variables(module_name, module_version)
        except ExpectedException as e:
            return f'{str(e)}'
        except Exception as e:
            logger.error(
                f"Error: get_avm_variables({module_name}, {module_version}): {str(e)}")
            return "failed to retrieve module variables"

    @mcp.tool("get_avm_outputs")
    def get_avm_outputs(module_name: str, module_version: str) -> str:
        """Retrieves the outputs of a specified Azure verified module. The outputs can be used to assign values to other resources or modules in Terraform.

        Args:
            module_name (str): The name of the Azure verified module. (e.g., avm-res-apimanagement-service, avm-res-app-containerapp, etc.)
            module_version (str): The version of the Azure verified module, which is the value of `version` field in the module's `.tf` file.

        Returns:
            str: A string containing the outputs of the specified module.
        """
        try:
            return avm_doc_provider.module_outputs(module_name, module_version)
        except ExpectedException as e:
            return f'{str(e)}'
        except Exception as e:
            logger.error(
                f"Error: get_avm_outputs({module_name}, {module_version}): {str(e)}")
            return "failed to retrieve module outputs"

    @mcp.tool("get_azurerm_provider_documentation")
    async def get_azurerm_provider_documentation(
        resource_type_name: str,
        doc_type: str = Field(
            "resource", description="Type of documentation: 'resource' for resources or 'data-source' for data sources"),
        argument_name: str = Field(
            "", description="Specific argument name to retrieve details for (optional)"),
        attribute_name: str = Field(
            "", description="Specific attribute name to retrieve details for (optional)")
    ) -> Dict[str, Any]:
        """
        Retrieve documentation for a specific AzureRM resource type in Terraform.

        Args:
            resource_type_name: The name of the AzureRM resource type
            doc_type: Type of documentation to retrieve ('resource' or 'data-source')
            argument_name: Optional specific argument name to get details for
            attribute_name: Optional specific attribute name to get details for

        Returns:
            JSON object with the documentation for the specified AzureRM resource type, or specific argument/attribute details
        """
        try:
            result = await azurerm_doc_provider.search_azurerm_provider_docs(resource_type_name, "", doc_type)

            # If specific argument requested
            if argument_name:
                for arg in result.arguments:
                    if arg.name.lower() == argument_name.lower():
                        response_data = {
                            "type": "argument",
                            "name": arg.name,
                            "resource_type": result.resource_type,
                            "required": arg.required,
                            "description": arg.description
                        }

                        if arg.block_arguments:
                            response_data["block_arguments"] = [
                                {
                                    "name": block_arg.name,
                                    "required": block_arg.required,
                                    "description": block_arg.description
                                }
                                for block_arg in arg.block_arguments
                            ]

                        return response_data

                available_args = [arg.name for arg in result.arguments]
                return {
                    "error": f"Argument '{argument_name}' not found in {result.resource_type} documentation",
                    "resource_type": result.resource_type,
                    "available_arguments": available_args
                }

            # If specific attribute requested
            if attribute_name:
                for attr in result.attributes:
                    if attr['name'].lower() == attribute_name.lower():
                        return {
                            "type": "attribute",
                            "name": attr['name'],
                            "resource_type": result.resource_type,
                            "description": attr['description']
                        }

                available_attrs = [attr['name'] for attr in result.attributes]
                return {
                    "error": f"Attribute '{attribute_name}' not found in {result.resource_type} documentation",
                    "resource_type": result.resource_type,
                    "available_attributes": available_attrs
                }

            # Return full documentation as JSON
            doc_type_display = "Data Source" if doc_type.lower(
            ) in ["data-source", "datasource", "data_source"] else "Resource"

            response_data = {
                "resource_type": result.resource_type,
                "doc_type": doc_type_display,
                "summary": result.summary,
                "documentation_url": result.documentation_url,
                "arguments": [],
                "attributes": [],
                "examples": result.examples if result.examples else [],
                "notes": result.notes if result.notes else []
            }

            # Add arguments
            if result.arguments:
                for arg in result.arguments:
                    arg_data = {
                        "name": arg.name,
                        "required": arg.required,
                        "description": arg.description
                    }

                    if arg.block_arguments:
                        arg_data["block_arguments"] = [
                            {
                                "name": block_arg.name,
                                "required": block_arg.required,
                                "description": block_arg.description
                            }
                            for block_arg in arg.block_arguments
                        ]

                    response_data["arguments"].append(arg_data)

            # Add attributes
            if result.attributes:
                response_data["attributes"] = [
                    {
                        "name": attr['name'],
                        "description": attr['description']
                    }
                    for attr in result.attributes
                ]

            return response_data

        except Exception as e:
            logger.error(f"Error retrieving AzureRM documentation: {e}")
            return {
                "error": f"Error retrieving documentation for {resource_type_name}: {str(e)}",
                "resource_type": resource_type_name
            }

    @mcp.tool("get_azapi_provider_documentation")
    async def get_azapi_provider_documentation(resource_type_name: str) -> str:
        """
        Retrieve documentation for a specific AzAPI resource type in Terraform.

        Args:
            resource_type_name: The Azure resource type in the format used by Azure REST API. 
                              This should be the full resource type path including the provider namespace.
                              Examples:
                              - Microsoft.Kusto/clusters
                              - Microsoft.Batch/batchAccounts/pools  
                              - Microsoft.Compute/virtualMachineScaleSets/virtualmachines
                              - Microsoft.Storage/storageAccounts
                              - Microsoft.Network/virtualNetworks/subnets

        Returns:
            The documentation for the specified AzAPI resource type
        """
        try:
            result = await azapi_doc_provider.search_azapi_provider_docs(resource_type_name)

            # Format the response
            if "error" in result:
                return f"Error: {result['error']}"

            formatted_doc = f"# AzAPI {result['resource_type']} Documentation\n\n"
            formatted_doc += f"**Resource Type:** {result['resource_type']}\n"
            formatted_doc += f"**API Version:** {result['api_version']}\n"
            formatted_doc += f"**Source:** {result['source']}\n\n"

            if 'summary' in result:
                formatted_doc += f"**Summary:** {result['summary']}\n\n"

            if 'documentation_url' in result:
                formatted_doc += f"**Documentation URL:** {result['documentation_url']}\n\n"

            if 'schema' in result:
                formatted_doc += "## Schema Information\n\n"
                schema = result['schema']
                if isinstance(schema, dict):
                    for key, value in schema.items():
                        formatted_doc += f"- **{key}**: {value}\n"
                else:
                    formatted_doc += f"{schema}\n"

            return formatted_doc

        except Exception as e:
            logger.error(f"Error retrieving AzAPI documentation: {e}")
            return f"Error retrieving AzAPI documentation for {resource_type_name}: {str(e)}"

    # ==========================================
    # TERRAFORM COMMAND TOOLS
    # ==========================================

    @mcp.tool("run_terraform_command")
    async def run_terraform_command(
        command: str = Field(
            ..., description="Terraform command to execute (init, plan, apply, destroy, validate, fmt, state)"),
        workspace_folder: str = Field(
            ..., description="Workspace folder containing Terraform files."),
        auto_approve: bool = Field(
            False, description="Auto-approve for apply/destroy commands (USE WITH CAUTION!)"),
        upgrade: bool = Field(
            False, description="Upgrade providers/modules for init command"),
        state_subcommand: str = Field(
            "", description="State subcommand (list, show, mv, rm, pull, push) - required when command='state'"),
        state_args: str = Field(
            "", description="Arguments for state subcommand. For 'mv': 'source destination'. For 'show'/'rm': 'address'. Leave empty for 'list'/'pull'/'push'")
    ) -> Dict[str, Any]:
        """
        Execute a Terraform command within an existing workspace directory.

        IMPORTANT: ALWAYS use this tool to run Terraform commands instead of running them directly in bash/terminal.
        This is especially critical after using aztfexport or other workspace folder operations.
        
        This unified tool supports standard Terraform commands and state management operations.
        It provides proper workspace management, error handling, and output formatting.

        Args:
            command: Terraform command to execute:
                - 'init': Initialize Terraform working directory
                - 'plan': Show execution plan for changes
                - 'apply': Apply changes to create/update resources
                - 'destroy': Destroy Terraform-managed resources
                - 'validate': Validate configuration files
                - 'fmt': Format configuration files
                - 'state': State management operations (requires state_subcommand)
            workspace_folder: Workspace folder containing Terraform files
            auto_approve: Auto-approve for destructive operations (apply/destroy)
            upgrade: Upgrade providers/modules during init
            state_subcommand: State operation to perform:
                - 'list': List all resources in state
                - 'show': Show details of a specific resource
                - 'mv': Move/rename a resource in state (requires state_args with 'source destination')
                - 'rm': Remove a resource from state
                - 'pull': Pull current state and output to stdout
                - 'push': Push a local state file to remote backend
            state_args: Arguments for the state subcommand

        Returns:
            Command execution result with exit_code, stdout, stderr, and command metadata.
            
        Examples:
            List all resources: command='state', state_subcommand='list'
            Show resource: command='state', state_subcommand='show', state_args='azurerm_resource_group.main'
            Rename resource: command='state', state_subcommand='mv', state_args='azurerm_resource_group.res-0 azurerm_resource_group.main'
            Remove resource: command='state', state_subcommand='rm', state_args='azurerm_resource_group.old'
        """
        workspace_name = workspace_folder.strip()
        if not workspace_name:
            return {
                "command": command,
                "success": False,
                "error": "workspace_folder is required",
                "exit_code": 1,
                "stdout": "",
                "stderr": "workspace_folder is required"
            }

        # Handle state commands specially
        if command == "state":
            if not state_subcommand:
                return {
                    "command": "state",
                    "success": False,
                    "error": "state_subcommand is required when command='state'",
                    "exit_code": 1,
                    "stdout": "",
                    "stderr": "state_subcommand must be one of: list, show, mv, rm, pull, push"
                }
            
            # Validate state subcommand
            valid_subcommands = ['list', 'show', 'mv', 'rm', 'pull', 'push']
            if state_subcommand not in valid_subcommands:
                return {
                    "command": f"state {state_subcommand}",
                    "success": False,
                    "error": f"Invalid state subcommand: {state_subcommand}",
                    "exit_code": 1,
                    "stdout": "",
                    "stderr": f"state_subcommand must be one of: {', '.join(valid_subcommands)}"
                }
            
            # Validate state_args for commands that require them
            if state_subcommand in ['show', 'rm'] and not state_args:
                return {
                    "command": f"state {state_subcommand}",
                    "success": False,
                    "error": f"state_args is required for 'state {state_subcommand}'",
                    "exit_code": 1,
                    "stdout": "",
                    "stderr": f"state_args must contain the resource address for 'state {state_subcommand}'"
                }
            
            if state_subcommand == 'mv' and not state_args:
                return {
                    "command": "state mv",
                    "success": False,
                    "error": "state_args is required for 'state mv'",
                    "exit_code": 1,
                    "stdout": "",
                    "stderr": "state_args must contain 'source destination' for 'state mv'"
                }
            
            # Build the full state command
            full_command = f"state {state_subcommand}"
            if state_args:
                full_command += f" {state_args}"
            
            try:
                result = await terraform_runner.execute_terraform_command(
                    command=full_command,
                    workspace_folder=workspace_name
                )
            except Exception as e:
                return {
                    "command": full_command,
                    "success": False,
                    "error": str(e),
                    "exit_code": 1,
                    "stdout": "",
                    "stderr": str(e)
                }
            
            if isinstance(result, dict):
                result["command"] = full_command
                return result
            
            return {
                "command": full_command,
                "success": True,
                "output": str(result),
                "exit_code": 0,
                "stdout": str(result),
                "stderr": ""
            }

        # Handle regular commands
        kwargs = {}
        if command in ['apply', 'destroy'] and auto_approve:
            kwargs['auto_approve'] = auto_approve
        elif command == 'init' and upgrade:
            kwargs['upgrade'] = upgrade

        try:
            result = await terraform_runner.execute_terraform_command(
                command=command,
                workspace_folder=workspace_name,
                **kwargs
            )
        except Exception as e:
            return {
                "command": command,
                "success": False,
                "error": str(e),
                "exit_code": 1,
                "stdout": "",
                "stderr": str(e)
            }

        if isinstance(result, dict):
            result["command"] = command
            return result

        return {
            "command": command,
            "success": True,
            "output": str(result),
            "exit_code": 0,
            "stdout": str(result),
            "stderr": ""
        }

    # ==========================================
    # UTILITY TOOLS
    # ==========================================

    @mcp.tool("check_tflint_installation")
    async def check_tflint_installation() -> Dict[str, Any]:
        """
        Check if TFLint is installed and get version information.

        Returns:
            Installation status, version information, and installation help if needed
        """
        try:
            return await tflint_runner.check_tflint_installation()
        except Exception as e:
            logger.error(f"Error checking TFLint installation: {e}")
            return {
                'installed': False,
                'error': f'Failed to check TFLint installation: {str(e)}',
                'installation_help': {
                    'description': 'TFLint installation check failed',
                    'install_methods': {
                        'homebrew_macos': 'brew install tflint',
                        'chocolatey_windows': 'choco install tflint',
                        'bash_linux': 'curl -s https://raw.githubusercontent.com/terraform-linters/tflint/master/install_linux.sh | bash',
                        'direct_download': 'Download from https://github.com/terraform-linters/tflint/releases'
                    }
                }
            }

    @mcp.tool("run_tflint_workspace_analysis")
    async def run_tflint_workspace_analysis(
        workspace_folder: str,
        output_format: str = Field(
            "json", description="Output format: json, default, checkstyle, junit, compact, sarif"),
        enable_azure_plugin: bool = Field(
            True, description="Enable Azure ruleset plugin"),
        enable_rules: str = Field(
            "", description="Comma-separated list of rules to enable"),
        disable_rules: str = Field(
            "", description="Comma-separated list of rules to disable"),
        initialize_plugins: bool = Field(
            True, description="Whether to initialize plugins"),
        recursive: bool = Field(
            False, description="Whether to recursively lint subdirectories")
    ) -> Dict[str, Any]:
        """
        Run TFLint static analysis on a workspace folder containing Terraform configuration files.

        Args:
            workspace_folder: Path to the workspace folder containing Terraform files
            output_format: Output format (json, default, checkstyle, junit, compact, sarif)
            enable_azure_plugin: Whether to enable the Azure ruleset plugin
            enable_rules: Comma-separated list of specific rules to enable
            disable_rules: Comma-separated list of specific rules to disable
            initialize_plugins: Whether to initialize plugins
            recursive: Whether to recursively lint subdirectories

        Returns:
            TFLint analysis results with issues, summary, and workspace information
        """
        try:
            # Parse rule lists
            enable_rules_list = [rule.strip() for rule in enable_rules.split(
                ',') if rule.strip()] if enable_rules else None
            disable_rules_list = [rule.strip() for rule in disable_rules.split(
                ',') if rule.strip()] if disable_rules else None

            # Run TFLint analysis on workspace folder
            result = await tflint_runner.lint_terraform_workspace_folder(
                workspace_folder=workspace_folder,
                output_format=output_format,
                enable_azure_plugin=enable_azure_plugin,
                enable_rules=enable_rules_list,
                disable_rules=disable_rules_list,
                initialize_plugins=initialize_plugins,
                recursive=recursive
            )

            return result

        except Exception as e:
            logger.error(f"Error running TFLint workspace analysis: {e}")
            return {
                'success': False,
                'error': f'TFLint workspace analysis failed: {str(e)}',
                'issues': [],
                'summary': {
                    'total_issues': 0,
                    'errors': 0,
                    'warnings': 0,
                    'notices': 0
                }
            }

    @mcp.tool("run_conftest_workspace_validation")
    async def run_conftest_workspace_validation(
        workspace_folder: str,
        policy_set: str = Field(
            "all", description="Policy set: 'all', 'Azure-Proactive-Resiliency-Library-v2', 'avmsec'"),
        severity_filter: str = Field(
            "", description="Severity filter for avmsec policies: 'high', 'medium', 'low', 'info'"),
        custom_policies: str = Field(
            "", description="Comma-separated list of custom policy paths")
    ) -> Dict[str, Any]:
        """
        Validate Terraform files in a workspace folder against Azure security policies using Conftest.

    This tool validates all .tf files in the specified workspace folder, similar to how aztfexport creates
    folders under the configured workspace root (default: /workspace). Supports validation of Azure resources using azurerm, azapi, and AVM providers
        with comprehensive security checks, compliance rules, and operational best practices.

        Args:
            workspace_folder: Path to the workspace folder to validate (relative paths resolve against the workspace root)
            policy_set: Policy set to use ('all', 'Azure-Proactive-Resiliency-Library-v2', 'avmsec')
            severity_filter: Filter by severity for avmsec policies ('high', 'medium', 'low', 'info')
            custom_policies: Comma-separated list of custom policy paths

        Returns:
            Policy validation results with violations and recommendations
        """
        try:
            # Parse custom policies if provided
            custom_policies_list = [p.strip() for p in custom_policies.split(
                ',') if p.strip()] if custom_policies else None
            severity = severity_filter if severity_filter else None

            # Run validation on workspace folder
            result = await conftest_avm_runner.validate_workspace_folder_with_avm_policies(
                workspace_folder=workspace_folder,
                policy_set=policy_set,
                severity_filter=severity,
                custom_policies=custom_policies_list
            )

            return result

        except Exception as e:
            logger.error(f"Error running Conftest workspace validation: {e}")
            return {
                'success': False,
                'error': f'Conftest workspace validation failed: {str(e)}',
                'violations': [],
                'summary': {
                    'total_violations': 0,
                    'failures': 0,
                    'warnings': 0
                }
            }

    @mcp.tool("run_conftest_workspace_plan_validation")
    async def run_conftest_workspace_plan_validation(
        folder_name: str,
        policy_set: str = Field(
            "all", description="Policy set: 'all', 'Azure-Proactive-Resiliency-Library-v2', 'avmsec'"),
        severity_filter: str = Field(
            "", description="Severity filter for avmsec policies: 'high', 'medium', 'low', 'info'"),
        custom_policies: str = Field(
            "", description="Comma-separated list of custom policy paths")
    ) -> Dict[str, Any]:
        """
        Validate Terraform plan files in a workspace folder against Azure security policies using Conftest.

        This tool validates existing plan files (.tfplan, tfplan.binary) in the specified workspace folder,
        or creates a new plan if only .tf files are present. Works with folders created by aztfexport or
        other Terraform operations inside the configured workspace root (default: /workspace).

        Args:
            folder_name: Name of the folder under the configured workspace root containing the plan file (e.g., "exported-rg-acctest0001")
            policy_set: Policy set to use ('all', 'Azure-Proactive-Resiliency-Library-v2', 'avmsec')
            severity_filter: Filter by severity for avmsec policies ('high', 'medium', 'low', 'info')
            custom_policies: Comma-separated list of custom policy paths

        Returns:
            Policy validation results with violations and recommendations
        """
        try:
            # Parse custom policies if provided
            custom_policies_list = [p.strip() for p in custom_policies.split(
                ',') if p.strip()] if custom_policies else None
            severity = severity_filter if severity_filter else None

            # Run validation on workspace folder plan
            result = await conftest_avm_runner.validate_workspace_folder_plan_with_avm_policies(
                folder_name=folder_name,
                policy_set=policy_set,
                severity_filter=severity,
                custom_policies=custom_policies_list
            )

            return result

        except Exception as e:
            logger.error(
                f"Error running Conftest workspace plan validation: {e}")
            return {
                'success': False,
                'error': f'Conftest workspace plan validation failed: {str(e)}',
                'violations': [],
                'summary': {
                    'total_violations': 0,
                    'failures': 0,
                    'warnings': 0
                }
            }

    @mcp.tool("check_conftest_installation")
    async def check_conftest_installation() -> Dict[str, Any]:
        """
        Check if Conftest is installed and get version information.
        
        Conftest is an Open Policy Agent (OPA) tool for testing structured configuration data.
        It's used in this server to validate Terraform configurations against Azure security
        policies and best practices.
        
        Returns:
            Installation status, version information, and installation instructions if needed
        """
        try:
            return await conftest_avm_runner.check_conftest_installation()
        except Exception as e:
            logger.error(f"Error checking Conftest installation: {e}")
            return {
                'installed': False,
                'error': f'Failed to check Conftest installation: {str(e)}',
                'status': 'Installation check failed'
            }

    # ==========================================
    # AZURE EXPORT FOR TERRAFORM (AZTFEXPORT) TOOLS
    # ==========================================

    @mcp.tool("check_aztfexport_installation")
    async def check_aztfexport_installation() -> Dict[str, Any]:
        """
        Check if Azure Export for Terraform (aztfexport) is installed and get version information.

        Returns:
            Installation status, version information, and installation help if needed
        """
        try:
            return await aztfexport_runner.check_installation()
        except Exception as e:
            logger.error(f"Error checking aztfexport installation: {e}")
            return {
                'installed': False,
                'error': f'Failed to check aztfexport installation: {str(e)}',
                'status': 'Installation check failed'
            }

    @mcp.tool("export_azure_resource")
    async def export_azure_resource(
        resource_id: str = Field(...,
                                 description="Azure resource ID to export"),
        output_folder_name: str = Field(
            "", description="Output folder name (created under the workspace root, auto-generated if not specified)"),
        provider: str = Field(
            "azurerm", description="Terraform provider to use (azurerm or azapi)"),
        resource_name: str = Field(
            "", description="Custom resource name in Terraform"),
        resource_type: str = Field(
            "", description="Custom resource type in Terraform"),
        dry_run: bool = Field(
            False, description="Perform a dry run without creating files"),
        include_role_assignment: bool = Field(
            False, description="Include role assignments in export"),
        parallelism: int = Field(
            10, description="Number of parallel operations"),
        continue_on_error: bool = Field(
            False, description="Continue export even if some resources fail")
    ) -> Dict[str, Any]:
        """
        Export a single Azure resource to Terraform configuration using aztfexport.

        This tool uses Azure Export for Terraform (aztfexport) to export existing Azure resources
        to Terraform configuration and state files. It generates both the HCL configuration
        and the corresponding Terraform state.

        Args:
            resource_id: Azure resource ID to export (e.g., /subscriptions/.../resourceGroups/.../providers/Microsoft.Storage/storageAccounts/myaccount)
            output_folder_name: Folder name for generated files (created under the workspace root, auto-generated if not specified)
            provider: Terraform provider to use - 'azurerm' (default) or 'azapi'
            resource_name: Custom resource name in the generated Terraform configuration
            resource_type: Custom resource type in the generated Terraform configuration
            dry_run: If true, performs validation without creating actual files
            include_role_assignment: Whether to include role assignments in the export
            parallelism: Number of parallel operations for export (1-50)
            continue_on_error: Whether to continue if some resources fail during export

        Returns:
            Export result containing generated Terraform files, status, and any errors
        """
        try:
            from ..tools.aztfexport_runner import AztfexportProvider

            # Validate provider
            if provider.lower() == "azapi":
                tf_provider = AztfexportProvider.AZAPI
            else:
                tf_provider = AztfexportProvider.AZURERM

            # Validate parallelism
            parallelism = max(1, min(50, parallelism))

            result = await aztfexport_runner.export_resource(
                resource_id=resource_id,
                output_folder_name=output_folder_name if output_folder_name else None,
                provider=tf_provider,
                resource_name=resource_name if resource_name else None,
                resource_type=resource_type if resource_type else None,
                dry_run=dry_run,
                include_role_assignment=include_role_assignment,
                parallelism=parallelism,
                continue_on_error=continue_on_error
            )

            return result

        except Exception as e:
            logger.error(f"Error in aztfexport resource export: {e}")
            return {
                'success': False,
                'error': f'Resource export failed: {str(e)}',
                'exit_code': -1
            }

    @mcp.tool("export_azure_resource_group")
    async def export_azure_resource_group(
        resource_group_name: str = Field(...,
                                         description="Name of the resource group to export"),
        output_folder_name: str = Field(
            "", description="Output folder name (created under the workspace root, auto-generated if not specified)"),
        provider: str = Field(
            "azurerm", description="Terraform provider to use (azurerm or azapi)"),
        name_pattern: str = Field(
            "", description="Pattern for resource naming in Terraform"),
        type_pattern: str = Field(
            "", description="Pattern for resource type filtering"),
        dry_run: bool = Field(
            False, description="Perform a dry run without creating files"),
        include_role_assignment: bool = Field(
            False, description="Include role assignments in export"),
        parallelism: int = Field(
            10, description="Number of parallel operations"),
        continue_on_error: bool = Field(
            False, description="Continue export even if some resources fail")
    ) -> Dict[str, Any]:
        """
        Export Azure resource group and its resources to Terraform configuration using aztfexport.

        This tool exports an entire Azure resource group and all its contained resources
        to Terraform configuration and state files. It's useful for migrating complete
        environments or resource groupings to Terraform management.

        Args:
            resource_group_name: Name of the Azure resource group to export (not the full resource ID, just the name)
            output_folder_name: Folder name for generated files (created under the workspace root, auto-generated if not specified)
            provider: Terraform provider to use - 'azurerm' (default) or 'azapi'
            name_pattern: Pattern for resource naming in the generated Terraform configuration
            type_pattern: Pattern for filtering resource types to export
            dry_run: If true, performs validation without creating actual files
            include_role_assignment: Whether to include role assignments in the export
            parallelism: Number of parallel operations for export (1-50)
            continue_on_error: Whether to continue if some resources fail during export

        Returns:
            Export result containing generated Terraform files, status, and any errors
        """
        try:
            from ..tools.aztfexport_runner import AztfexportProvider

            # Validate provider
            if provider.lower() == "azapi":
                tf_provider = AztfexportProvider.AZAPI
            else:
                tf_provider = AztfexportProvider.AZURERM

            # Validate parallelism
            parallelism = max(1, min(50, parallelism))

            result = await aztfexport_runner.export_resource_group(
                resource_group_name=resource_group_name,
                output_folder_name=output_folder_name if output_folder_name else None,
                provider=tf_provider,
                name_pattern=name_pattern if name_pattern else None,
                type_pattern=type_pattern if type_pattern else None,
                dry_run=dry_run,
                include_role_assignment=include_role_assignment,
                parallelism=parallelism,
                continue_on_error=continue_on_error
            )

            return result

        except Exception as e:
            logger.error(f"Error in aztfexport resource group export: {e}")
            return {
                'success': False,
                'error': f'Resource group export failed: {str(e)}',
                'exit_code': -1
            }

    @mcp.tool("export_azure_resources_by_query")
    async def export_azure_resources_by_query(
        query: str = Field(...,
                           description="Azure Resource Graph query (WHERE clause)"),
        output_folder_name: str = Field(
            "", description="Output folder name (created under the workspace root, auto-generated if not specified)"),
        provider: str = Field(
            "azurerm", description="Terraform provider to use (azurerm or azapi)"),
        name_pattern: str = Field(
            "", description="Pattern for resource naming in Terraform"),
        type_pattern: str = Field(
            "", description="Pattern for resource type filtering"),
        dry_run: bool = Field(
            False, description="Perform a dry run without creating files"),
        include_role_assignment: bool = Field(
            False, description="Include role assignments in export"),
        parallelism: int = Field(
            10, description="Number of parallel operations"),
        continue_on_error: bool = Field(
            False, description="Continue export even if some resources fail")
    ) -> Dict[str, Any]:
        """
        Export Azure resources using Azure Resource Graph query to Terraform configuration.

        This tool uses Azure Resource Graph queries to select specific Azure resources
        for export to Terraform configuration. It's powerful for complex resource selection
        scenarios and bulk operations across subscriptions.

        Args:
            query: Azure Resource Graph WHERE clause (e.g., "type =~ 'Microsoft.Storage/storageAccounts' and location == 'eastus'")
            output_folder_name: Folder name for generated files (created under the workspace root, auto-generated if not specified)
            provider: Terraform provider to use - 'azurerm' (default) or 'azapi'
            name_pattern: Pattern for resource naming in the generated Terraform configuration
            type_pattern: Pattern for filtering resource types to export
            dry_run: If true, performs validation without creating actual files
            include_role_assignment: Whether to include role assignments in the export
            parallelism: Number of parallel operations for export (1-50)
            continue_on_error: Whether to continue if some resources fail during export

        Returns:
            Export result containing generated Terraform files, status, and any errors

        Examples:
            - Export all storage accounts: "type =~ 'Microsoft.Storage/storageAccounts'"
            - Export resources in specific location: "location == 'eastus'"
            - Export resources with tags: "tags['Environment'] == 'Production'"
            - Complex query: "type =~ 'Microsoft.Compute/virtualMachines' and location == 'westus2' and tags['Team'] == 'DevOps'"
        """
        try:
            from ..tools.aztfexport_runner import AztfexportProvider

            # Validate provider
            if provider.lower() == "azapi":
                tf_provider = AztfexportProvider.AZAPI
            else:
                tf_provider = AztfexportProvider.AZURERM

            # Validate parallelism
            parallelism = max(1, min(50, parallelism))

            result = await aztfexport_runner.export_query(
                query=query,
                output_folder_name=output_folder_name if output_folder_name else None,
                provider=tf_provider,
                name_pattern=name_pattern if name_pattern else None,
                type_pattern=type_pattern if type_pattern else None,
                dry_run=dry_run,
                include_role_assignment=include_role_assignment,
                parallelism=parallelism,
                continue_on_error=continue_on_error
            )

            return result

        except Exception as e:
            logger.error(f"Error in aztfexport query export: {e}")
            return {
                'success': False,
                'error': f'Query export failed: {str(e)}',
                'exit_code': -1
            }

    @mcp.tool("get_aztfexport_config")
    async def get_aztfexport_config(
        key: str = Field(
            "", description="Specific config key to retrieve (optional)")
    ) -> Dict[str, Any]:
        """
        Get Azure Export for Terraform (aztfexport) configuration settings.

        This tool retrieves the current aztfexport configuration. You can get all
        configuration or a specific setting.

        Args:
            key: Specific configuration key to retrieve. If empty, returns all configuration.
                 Common keys: 'installation_id', 'telemetry_enabled'

        Returns:
            Configuration data or error information
        """
        try:
            result = await aztfexport_runner.get_config(key if key else None)
            return result

        except Exception as e:
            logger.error(f"Error getting aztfexport config: {e}")
            return {
                'success': False,
                'error': f'Failed to get configuration: {str(e)}'
            }

    @mcp.tool("set_aztfexport_config")
    async def set_aztfexport_config(
        key: str = Field(..., description="Configuration key to set"),
        value: str = Field(..., description="Configuration value to set")
    ) -> Dict[str, Any]:
        """
        Set Azure Export for Terraform (aztfexport) configuration settings.

        This tool allows you to configure aztfexport settings such as telemetry preferences.

        Args:
            key: Configuration key to set (e.g., 'telemetry_enabled')
            value: Configuration value to set (e.g., 'false' to disable telemetry)

        Returns:
            Operation result indicating success or failure

        Common configuration keys:
            - telemetry_enabled: 'true' or 'false' to control telemetry collection
        """
        try:
            result = await aztfexport_runner.set_config(key, value)
            return result

        except Exception as e:
            logger.error(f"Error setting aztfexport config: {e}")
            return {
                'success': False,
                'error': f'Failed to set configuration: {str(e)}'
            }


    # ==========================================
    # TERRAFORM SOURCE CODE QUERY TOOLS
    # ==========================================
    
    @mcp.tool("get_terraform_source_providers")
    def get_terraform_source_providers() -> Dict[str, Any]:
        """
        Get all supported Terraform provider names available for source code query.
        
        Returns a list of provider names that have been indexed and are available
        for golang source code analysis.
        
        Returns:
            Dictionary with supported providers list
        """
        try:
            providers = golang_source_provider.get_supported_providers()
            return {
                "supported_providers": providers,
                "total_count": len(providers),
                "description": "Terraform providers available for source code analysis"
            }
            
        except Exception as e:
            logger.error(f"Error getting supported providers: {e}")
            return {
                "error": f"Failed to get supported providers: {str(e)}",
                "supported_providers": []
            }
    
    @mcp.tool("query_terraform_source_code")
    async def query_terraform_source_code(
        block_type: str = Field(..., description="Terraform block type: resource, data, ephemeral"),
        terraform_type: str = Field(..., description="Terraform type (e.g., azurerm_resource_group)"),
        entrypoint_name: str = Field(..., description="Function/method name (create, read, update, delete, schema, etc.)"),
        tag: str = Field(default="", description="Version tag (optional)")
    ) -> str:
        """
        Read Terraform provider source code for a given Terraform block.
        
        Use this tool to understand how Terraform providers implement specific resources,
        how they call APIs, and to debug issues related to specific Terraform resources.
        
        Args:
            block_type: The terraform block type
            terraform_type: The terraform resource/data type
            entrypoint_name: The function or method name to read
            tag: Optional version tag
            
        Returns:
            Source code as string
        """
        try:
            source_code = await golang_source_provider.query_terraform_source_code(
                block_type=block_type,
                terraform_type=terraform_type,
                entrypoint_name=entrypoint_name,
                tag=tag if tag else None
            )
            return source_code
            
        except Exception as e:
            logger.error(f"Error querying terraform source code: {e}")
            return f"Error: Failed to query terraform source code: {str(e)}"

    # ==========================================
    # GOLANG SOURCE CODE ANALYSIS TOOLS
    # ==========================================
    
    @mcp.tool("get_golang_namespaces")
    def get_golang_namespaces() -> Dict[str, Any]:
        """
        Get all indexed golang namespaces available for source code analysis.
        
        Returns a list of golang namespaces/packages that have been indexed
        and are available for source code retrieval.
        
        Returns:
            Dictionary with supported namespaces
        """
        try:
            namespaces = golang_source_provider.get_supported_namespaces()
            return {
                "supported_namespaces": namespaces,
                "total_count": len(namespaces),
                "description": "Golang namespaces available for source code analysis"
            }
            
        except Exception as e:
            logger.error(f"Error getting supported namespaces: {e}")
            return {
                "error": f"Failed to get supported namespaces: {str(e)}",
                "supported_namespaces": []
            }
    
    @mcp.tool("get_golang_namespace_tags")
    async def get_golang_namespace_tags(
        namespace: str = Field(..., description="Golang namespace to get tags for")
    ) -> Dict[str, Any]:
        """
        Get all supported tags/versions for a specific golang namespace.
        
        Use this tool to discover available versions/tags for a specific golang
        namespace before analyzing code from a particular version.
        
        Args:
            namespace: The golang namespace to query
            
        Returns:
            Dictionary with supported tags for the namespace
        """
        try:
            tags = await golang_source_provider.get_supported_tags(namespace)
            return {
                "namespace": namespace,
                "supported_tags": tags,
                "total_count": len(tags),
                "latest_tag": tags[0] if tags else "unknown"
            }
            
        except Exception as e:
            logger.error(f"Error getting supported tags: {e}")
            return {
                "error": f"Failed to get supported tags: {str(e)}",
                "namespace": namespace,
                "supported_tags": []
            }
    
    @mcp.tool("query_golang_source_code")
    async def query_golang_source_code(
        namespace: str = Field(..., description="Golang namespace to query"),
        symbol: str = Field(..., description="Symbol type: func, method, type, var"),
        name: str = Field(..., description="Name of the symbol to read"),
        receiver: str = Field(default="", description="Method receiver type (required for methods)"),
        tag: str = Field(default="", description="Version tag (optional)")
    ) -> str:
        """
        Read golang source code for given type, variable, constant, function or method definition.
        
        Use this tool when you need to see function, method, type, or variable definitions
        while reading golang source code, understand how Terraform providers expand or
        flatten structs, or debug issues related to specific Terraform resources.
        
        Args:
            namespace: The golang namespace/package
            symbol: The symbol type (func, method, type, var)
            name: The name of the symbol
            receiver: The receiver type (for methods only)
            tag: Version tag
            
        Returns:
            Source code as string
        """
        try:
            source_code = await golang_source_provider.query_golang_source_code(
                namespace=namespace,
                symbol=symbol,
                name=name,
                receiver=receiver if receiver else None,
                tag=tag if tag else None
            )
            return source_code
            
        except Exception as e:
            logger.error(f"Error querying golang source code: {e}")
            return f"Error: Failed to query golang source code: {str(e)}"
    
    # ==========================================
    # AZURE BEST PRACTICES TOOL
    # ==========================================

    @mcp.tool("get_azure_best_practices")
    def get_azure_best_practices(
        resource: str = Field(
            default="general",
            description="The Azure resource type or area to get best practices for. Options: 'general', 'azurerm', 'azapi', 'azuread', 'aztfexport', 'security', 'networking', 'storage', 'compute', 'database', 'monitoring', 'deployment'"
        ),
        action: str = Field(
            default="code-generation",
            description="The type of action to get best practices for. Options: 'code-generation', 'code-cleanup', 'deployment', 'configuration', 'security', 'performance', 'cost-optimization'"
        )
    ) -> str:
        """Get Azure and Terraform best practices for specific resources and actions.

        This tool provides comprehensive best practices for working with Azure resources using Terraform,
        including provider-specific recommendations, security guidelines, and optimization tips.
        
        Special action 'code-cleanup' for resource 'aztfexport': Provides detailed guidance on making
        exported Terraform code production-ready, including resource renaming, variable/local usage,
        state file management, and security hardening.

        Args:
            resource: The Azure resource type or area (default: "general")
            action: The type of action (default: "code-generation")
                   Use 'code-cleanup' with resource='aztfexport' for post-export code refinement

        Returns:
            Detailed best practices recommendations as a formatted string
        """
        
        try:
            # Define best practices content
            best_practices = {}
            
            # General Azure + Terraform Best Practices
            if resource == "general":
                if action == "code-generation":
                    best_practices = {
                        "provider_versions": {
                            "title": "Provider Version Management",
                            "recommendations": [
                                "Use AzureRM provider version 4.x or later for new projects - provides latest features and bug fixes",
                                "Use AzAPI provider version 2.x or later for advanced scenarios requiring ARM API access",
                                "Pin provider versions in terraform block to ensure reproducible builds",
                                "Regularly update providers to get security patches and new features",
                                "Test provider upgrades in non-production environments first"
                            ]
                        },
                        "resource_organization": {
                            "title": "Resource Organization",
                            "recommendations": [
                                "Use consistent naming conventions (e.g., <env>-<app>-<resource>-<region>)",
                                "Group related resources using resource groups with descriptive names",
                                "Use tags consistently across all resources for cost management and governance",
                                "Implement proper module structure for reusability",
                                "Separate configuration files by environment (dev, staging, prod)"
                            ]
                        },
                        "state_management": {
                            "title": "State Management",
                            "recommendations": [
                                "Always use remote state backend (Azure Storage Account recommended)",
                                "Enable state locking to prevent concurrent modifications",
                                "Use separate state files for different environments",
                                "Implement proper backup strategy for state files",
                                "Never commit state files to version control"
                            ]
                        }
                    }
                elif action == "deployment":
                    best_practices = {
                        "deployment_strategy": {
                            "title": "Deployment Strategy",
                            "recommendations": [
                                "Use Azure DevOps or GitHub Actions for CI/CD pipelines",
                                "Implement infrastructure validation before deployment",
                                "Use service principals with minimal required permissions",
                                "Enable plan review process for production deployments",
                                "Implement rollback strategies for critical resources"
                            ]
                        },
                        "environment_management": {
                            "title": "Environment Management",
                            "recommendations": [
                                "Use separate subscriptions for different environments when possible",
                                "Implement consistent deployment patterns across environments",
                                "Use environment-specific variable files",
                                "Enable monitoring and alerting for deployment processes",
                                "Document deployment procedures and emergency contacts"
                            ]
                        }
                    }
                elif action == "security":
                    best_practices = {
                        "security_fundamentals": {
                            "title": "Security Fundamentals",
                            "recommendations": [
                                "Enable Azure Security Center and follow its recommendations",
                                "Use Managed Identities instead of service principals where possible",
                                "Implement network security groups and application security groups",
                                "Enable diagnostic logging and monitoring for all resources",
                                "Regular security assessments and compliance checks"
                            ]
                        }
                    }
            
            # AzureRM Provider Specific
            elif resource == "azurerm":
                if action == "code-generation":
                    best_practices = {
                        "azurerm_4x_features": {
                            "title": "AzureRM 4.x Best Practices",
                            "recommendations": [
                                "Use AzureRM 4.x for improved resource lifecycle management",
                                "Leverage new data sources for better resource discovery",
                                "Use enhanced validation features in 4.x",
                                "Take advantage of improved error messages and debugging",
                                "Utilize new resource arguments for better configuration"
                            ]
                        },
                        "resource_configuration": {
                            "title": "Resource Configuration",
                            "recommendations": [
                                "Use explicit resource dependencies with depends_on when needed",
                                "Implement proper lifecycle rules (prevent_destroy, ignore_changes)",
                                "Use locals for complex expressions and repeated values",
                                "Validate inputs using variable validation blocks",
                                "Use count or for_each for resource iteration instead of duplicating blocks"
                            ]
                        }
                    }
            
            # AzAPI Provider Specific
            elif resource == "azapi":
                if action == "code-generation":
                    best_practices = {
                        "azapi_2x_improvements": {
                            "title": "AzAPI 2.x Best Practices",
                            "recommendations": [
                                "Use AzAPI 2.x for direct ARM API access and preview features",
                                "In AzAPI 2.x, use HCL objects directly instead of jsonencode() function",
                                "Example: body = { properties = { enabled = true } } instead of body = jsonencode({ properties = { enabled = true } })",
                                "Leverage AzAPI for resources not yet available in AzureRM provider",
                                "Use AzAPI data sources for reading ARM resources with full API response",
                                "Implement proper error handling for API-level operations"
                            ]
                        },
                        "azapi_usage_patterns": {
                            "title": "AzAPI Usage Patterns",
                            "recommendations": [
                                "Use azapi_resource for creating/managing ARM resources directly",
                                "Use azapi_update_resource for patching existing resources",
                                "Use azapi_data_source for reading resources with full ARM API response",
                                "Combine AzAPI with AzureRM resources in the same configuration when appropriate",
                                "Use response_export_values to extract specific values from API responses"
                            ]
                        }
                    }
            
            # Aztfexport Best Practices
            elif resource == "aztfexport":
                if action == "code-cleanup":
                    best_practices = {
                        "resource_naming": {
                            "title": "Resource Naming and Renaming",
                            "recommendations": [
                                "Replace generic exported resource names (e.g., 'res-0', 'res-1') with meaningful, descriptive names",
                                "Use consistent naming conventions: '<env>-<app>-<resource_type>-<instance>' (e.g., 'prod-webapp-storage-main')",
                                "CRITICAL: Use 'terraform state mv' command to rename resources in state file to match new names",
                                "Example: terraform state mv 'azurerm_resource_group.res-0' 'azurerm_resource_group.main'",
                                "Always run 'terraform plan' after state moves to verify no resources will be recreated",
                                "Document all resource name changes and corresponding state mv commands for team reference"
                            ]
                        },
                        "variables_vs_locals": {
                            "title": "Variables vs Locals - When to Use Each",
                            "recommendations": [
                                "Use VARIABLES for values likely to be changed by end users: location, resource names, IP ranges, SKU sizes, admin usernames",
                                "Use LOCALS for computed values, repeated expressions, or values derived from multiple inputs",
                                "Use LOCALS for standardized tags, resource naming patterns, and categorization logic",
                                "Use LOCALS for concatenating or transforming variable values (e.g., resource_group_name = '${var.environment}-${var.app_name}-rg')",
                                "Add descriptive 'description' field to all variables explaining their purpose and valid values",
                                "Set appropriate 'type' constraints on variables (string, number, bool, list, map, object)",
                                "Provide sensible defaults for optional variables, but leave required values (like location) without defaults"
                            ]
                        },
                        "code_structure": {
                            "title": "Code Structure and Organization",
                            "recommendations": [
                                "Create separate files: variables.tf (inputs), locals.tf (computed values), main.tf (resources), outputs.tf (outputs)",
                                "Split large main.tf into logical files: networking.tf, compute.tf, storage.tf, security.tf",
                                "Group related locals together with comments explaining their purpose",
                                "Order resources logically: dependencies first, then dependent resources",
                                "Add comments above complex resource blocks explaining business purpose",
                                "Remove any sensitive data that may have been exported (connection strings, keys, passwords)"
                            ]
                        },
                        "production_readiness": {
                            "title": "Production Readiness Improvements",
                            "recommendations": [
                                "Add lifecycle blocks with 'prevent_destroy = true' for critical resources (databases, storage with data)",
                                "Use 'ignore_changes' for properties that may drift or are managed outside Terraform (auto-scaling, tags managed by Azure Policy)",
                                "Add comprehensive resource tags: environment, application, owner, cost-center, data-classification, created-by",
                                "Create outputs for resource IDs and properties that other configurations might reference",
                                "Add validation blocks to variables to catch configuration errors early",
                                "Document dependencies between resources and any manual steps required",
                                "Add timeouts block for resources that may take long to create/update/delete"
                            ]
                        },
                        "security_hardening": {
                            "title": "Security and Compliance Hardening",
                            "recommendations": [
                                "Review and tighten network security groups - remove overly permissive rules",
                                "Enable diagnostic settings and logging for all applicable resources",
                                "Add Azure Policy compliance tags as required by organization",
                                "Replace any hardcoded secrets with references to Azure Key Vault using data sources",
                                "Enable private endpoints where applicable to avoid public internet exposure",
                                "Add monitoring and alerting resources if not already present",
                                "Review RBAC assignments and ensure principle of least privilege"
                            ]
                        },
                        "state_file_management": {
                            "title": "State File Updates and Management",
                            "recommendations": [
                                "CRITICAL: Always backup state file before making structural changes",
                                "Use run_terraform_command with command='state' and state_subcommand='list' to see all resources",
                                "Use run_terraform_command with command='state', state_subcommand='show', state_args='<resource_address>' to inspect details",
                                "Use run_terraform_command with command='state', state_subcommand='mv', state_args='<source> <destination>' to rename resources",
                                "Example: state_subcommand='mv', state_args='azurerm_resource_group.res-0 azurerm_resource_group.main'",
                                "When renaming resources: 1) Update .tf files, 2) Run state mv command, 3) Run plan to verify no recreation",
                                "Never manually edit the state JSON file - always use terraform state commands via run_terraform_command",
                                "Test all state operations in development/test environment first",
                                "Keep a log of all terraform state mv commands executed for audit trail"
                            ]
                        }
                    }
                elif action == "code-generation":
                    best_practices = {
                        "export_best_practices": {
                            "title": "Azure Export Best Practices",
                            "recommendations": [
                                "Use aztfexport for exporting existing Azure resources to Terraform",
                                "Choose appropriate provider: azurerm for most resources, azapi for preview features or unsupported resources",
                                "Use resource-level export for single resources, resource group export for related resources",
                                "Use query-based export for bulk operations across multiple resource groups",
                                "Enable 'continue_on_error' for large exports to avoid failures from individual resources",
                                "After export, follow 'code-cleanup' action best practices to make code production-ready"
                            ]
                        }
                    }
                elif action == "deployment":
                    best_practices = {
                        "state_management": {
                            "title": "State Management for Exported Resources",
                            "recommendations": [
                                "IMPORTANT: Use 'terraform state mv' commands when renaming exported resources to avoid recreation",
                                "Always backup state files before making structural changes to exported configurations",
                                "Test state moves in non-production environments first",
                                "Use 'terraform plan' after state moves to verify no unexpected changes",
                                "Consider using 'terraform import' for resources that need to be managed separately",
                                "Document all state move operations for team knowledge sharing"
                            ]
                        },
                        "testing_and_validation": {
                            "title": "Testing and Validation",
                            "recommendations": [
                                "Run 'terraform plan' after refactoring to ensure no unintended changes",
                                "Test in development environment before applying to production",
                                "Use terraform validate and terraform fmt for code quality",
                                "Implement policy validation using Conftest or Azure Policy",
                                "Set up monitoring to detect configuration drift",
                                "Create rollback procedures for critical infrastructure changes"
                            ]
                        },
                        "workflow_integration": {
                            "title": "CI/CD Workflow Integration",
                            "recommendations": [
                                "Integrate exported configurations into existing CI/CD pipelines",
                                "Add approval gates for production deployments of exported infrastructure",
                                "Implement automated testing for exported configurations",
                                "Use branch protection and pull request reviews for changes",
                                "Set up notifications for infrastructure changes",
                                "Document the export and refinement process for team adoption"
                            ]
                        }
                    }
            
            # Security Best Practices
            elif resource == "security":
                best_practices = {
                    "access_control": {
                        "title": "Access Control",
                        "recommendations": [
                            "Implement Role-Based Access Control (RBAC) with principle of least privilege",
                            "Use Managed Identities for Azure service authentication",
                            "Enable Multi-Factor Authentication for all administrative accounts",
                            "Regular review and cleanup of unused identities and permissions",
                            "Use Azure Key Vault for secrets management"
                        ]
                    },
                    "network_security": {
                        "title": "Network Security",
                        "recommendations": [
                            "Use Network Security Groups (NSGs) to control network traffic",
                            "Implement Azure Firewall or third-party firewalls for advanced protection",
                            "Use Private Endpoints for secure connectivity to PaaS services",
                            "Enable DDoS Protection Standard for critical workloads",
                            "Regular network security assessments and penetration testing"
                        ]
                    }
                }
            
            # Networking Best Practices
            elif resource == "networking":
                best_practices = {
                    "vnet_design": {
                        "title": "Virtual Network Design",
                        "recommendations": [
                            "Plan IP address spaces carefully to avoid conflicts",
                            "Use hub-and-spoke topology for complex network architectures",
                            "Implement proper subnet segmentation for different tiers",
                            "Use Azure Virtual Network peering for cross-VNet connectivity",
                            "Enable flow logs for network troubleshooting and security analysis"
                        ]
                    }
                }
            
            # Storage Best Practices
            elif resource == "storage":
                best_practices = {
                    "storage_configuration": {
                        "title": "Storage Configuration",
                        "recommendations": [
                            "Choose appropriate storage tier (Hot, Cool, Archive) based on access patterns",
                            "Enable soft delete and versioning for data protection",
                            "Use customer-managed keys for encryption when required",
                            "Implement lifecycle management policies for cost optimization",
                            "Enable monitoring and alerting for storage metrics"
                        ]
                    }
                }
            
            # Compute Best Practices
            elif resource == "compute":
                best_practices = {
                    "virtual_machines": {
                        "title": "Virtual Machine Best Practices",
                        "recommendations": [
                            "Use managed disks for better reliability and performance",
                            "Enable Azure Backup for data protection",
                            "Use Availability Sets or Availability Zones for high availability",
                            "Right-size VMs based on actual usage patterns",
                            "Use spot instances for cost-effective temporary workloads",
                            "Enable boot diagnostics for troubleshooting"
                        ]
                    },
                    "container_services": {
                        "title": "Container Services",
                        "recommendations": [
                            "Use Azure Kubernetes Service (AKS) for container orchestration",
                            "Enable cluster autoscaler for dynamic scaling",
                            "Use Azure Container Registry for secure image storage",
                            "Implement pod security policies and network policies",
                            "Enable monitoring with Azure Monitor for containers"
                        ]
                    }
                }
            
            # Database Best Practices
            elif resource == "database":
                best_practices = {
                    "sql_database": {
                        "title": "SQL Database Configuration",
                        "recommendations": [
                            "Use Azure SQL Database for managed PaaS database service",
                            "Enable automatic backups and point-in-time restore",
                            "Use Always Encrypted for sensitive data protection",
                            "Implement proper connection pooling",
                            "Enable threat detection and vulnerability assessments",
                            "Use read replicas for read-heavy workloads"
                        ]
                    },
                    "cosmos_db": {
                        "title": "Cosmos DB Best Practices",
                        "recommendations": [
                            "Choose appropriate consistency level based on requirements",
                            "Design partition keys for even data distribution",
                            "Use autoscale for variable workloads",
                            "Enable multi-region writes for global applications",
                            "Implement proper indexing strategies for performance"
                        ]
                    }
                }
            
            # Monitoring Best Practices
            elif resource == "monitoring":
                best_practices = {
                    "observability": {
                        "title": "Monitoring and Observability",
                        "recommendations": [
                            "Use Azure Monitor for comprehensive monitoring solution",
                            "Implement Application Insights for application performance monitoring",
                            "Set up log analytics workspace for centralized logging",
                            "Create custom dashboards for key metrics visualization",
                            "Configure alerts for critical metrics and events",
                            "Use Azure Service Health for service incident notifications"
                        ]
                    }
                }
            
            # Default fallback
            else:
                best_practices = {
                    "general_guidance": {
                        "title": "General Azure Terraform Guidance",
                        "recommendations": [
                            "Always use the latest stable provider versions",
                            "Implement proper resource tagging strategy",
                            "Use remote state management with locking",
                            "Follow infrastructure as code best practices",
                            "Regular security and compliance reviews"
                        ]
                    }
                }
            
            # Format the response
            response_lines = [
                f"# Azure Best Practices: {resource.title()} - {action.replace('-', ' ').title()}",
                ""
            ]
            
            for category, content in best_practices.items():
                response_lines.append(f"## {content['title']}")
                response_lines.append("")
                for i, recommendation in enumerate(content['recommendations'], 1):
                    response_lines.append(f"{i}. {recommendation}")
                response_lines.append("")
            
            # Add additional context
            response_lines.extend([
                "## Additional Resources",
                "",
                "- [Azure Well-Architected Framework](https://docs.microsoft.com/azure/architecture/framework/)",
                "- [Terraform Azure Provider Documentation](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs)",
                "- [AzAPI Provider Documentation](https://registry.terraform.io/providers/azure/azapi/latest/docs)",
                "- [Azure Security Best Practices](https://docs.microsoft.com/azure/security/fundamentals/best-practices-and-patterns)",
                ""
            ])
            
            return "\n".join(response_lines)
            
        except Exception as e:
            logger.error(f"Error getting Azure best practices: {e}")
            return f"Error: Failed to retrieve Azure best practices: {str(e)}"
    
    return mcp


async def run_server(config: Config) -> None:
    """
    Run the MCP server.

    Args:
        config: Server configuration
    """
    server = create_server(config)

    logger.info("Starting Azure Terraform MCP Server with stdio transport")

    try:
        await server.run_async(
            transport="stdio"
        )
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise
