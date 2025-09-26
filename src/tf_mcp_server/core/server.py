"""
Main server implementation for Azure Terraform MCP Server.
"""

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

    @mcp.tool("azurerm_terraform_documentation_retriever")
    async def retrieve_azurerm_docs(
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

    @mcp.tool("azapi_terraform_documentation_retriever")
    async def retrieve_azapi_docs(resource_type_name: str) -> str:
        """
        Retrieve documentation for a specific AzAPI resource type in Terraform.

        Args:
            resource_type_name: The name of the AzAPI resource type

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
            ..., description="Terraform command to execute (init, plan, apply, destroy, validate, fmt)"),
        workspace_folder: str = Field(
            ..., description="Workspace folder containing Terraform files."),
        auto_approve: bool = Field(
            False, description="Auto-approve for apply/destroy commands (USE WITH CAUTION!)"),
        upgrade: bool = Field(
            False, description="Upgrade providers/modules for init command")
    ) -> Dict[str, Any]:
        """
        Execute a Terraform command within an existing workspace directory.

        This unified tool replaces individual terraform_init, terraform_plan, terraform_apply,
        terraform_destroy, terraform_format, and terraform_execute_command tools.

        Args:
            command: Terraform command to execute:
                - 'init': Initialize Terraform working directory
                - 'plan': Show execution plan for changes
                - 'apply': Apply changes to create/update resources
                - 'destroy': Destroy Terraform-managed resources
                - 'validate': Validate configuration files
                - 'fmt': Format configuration files
            workspace_folder: Workspace folder containing Terraform files
            auto_approve: Auto-approve for destructive operations (apply/destroy)
            upgrade: Upgrade providers/modules during init

        Returns:
            Command execution result with exit_code, stdout, stderr, and command metadata.
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

    @mcp.tool("analyze_azure_resources")
    async def analyze_azure_resources(hcl_content: str) -> Dict[str, Any]:
        """
        Analyze Azure resources in Terraform configurations.

        Args:
            hcl_content: Terraform HCL content to analyze

        Returns:
            Analysis results with resource information and recommendations
        """
        try:
            # This is a simplified analysis - in a real implementation,
            # you would parse the HCL and extract detailed resource information

            resources_found = []
            lines = hcl_content.split('\n')

            for line in lines:
                line = line.strip()
                if line.startswith('resource ') and 'azurerm_' in line:
                    # Extract resource type and name
                    parts = line.split('"')
                    if len(parts) >= 4:
                        resource_type = parts[1]
                        resource_name = parts[3]
                        resources_found.append({
                            "type": resource_type,
                            "name": resource_name
                        })

            return {
                "total_resources": len(resources_found),
                "azure_resources": resources_found,
                "analysis_summary": f"Found {len(resources_found)} Azure resources in the configuration",
                "recommendations": [
                    "Review security configurations for all resources",
                    "Ensure proper tagging strategy is implemented",
                    "Validate resource naming conventions",
                    "Check for best practices compliance"
                ]
            }

        except Exception as e:
            logger.error(f"Error analyzing Azure resources: {e}")
            return {
                "error": f"Failed to analyze resources: {str(e)}",
                "total_resources": 0,
                "azure_resources": [],
                "analysis_summary": "Analysis failed",
                "recommendations": []
            }

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
        Validate Terraform files in a workspace folder against Azure security policies and best practices using Conftest.

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

    @mcp.tool("aztfexport_resource")
    async def aztfexport_resource(
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

    @mcp.tool("aztfexport_resource_group")
    async def aztfexport_resource_group(
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

    @mcp.tool("aztfexport_query")
    async def aztfexport_query(
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

    @mcp.tool("aztfexport_get_config")
    async def aztfexport_get_config(
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

    @mcp.tool("aztfexport_set_config")
    async def aztfexport_set_config(
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
