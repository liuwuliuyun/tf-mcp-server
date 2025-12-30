"""
Main server implementation for Azure Terraform MCP Server.
"""

import logging
import atexit
from typing import Dict, Any
from pydantic import Field
from fastmcp import FastMCP

from .config import Config
from .telemetry import get_telemetry_manager, track_tool_call
from ..tools.azurerm_docs_provider import get_azurerm_documentation_provider
from ..tools.azapi_docs_provider import get_azapi_documentation_provider
from ..tools.terraform_runner import get_terraform_runner
from ..tools.aztfexport_runner import get_aztfexport_runner
from ..tools.coverage_auditor import get_coverage_auditor

logger = logging.getLogger(__name__)


def create_server(config: Config) -> FastMCP:
    """
    Create and configure the FastMCP server.

    Args:
        config: Server configuration

    Returns:
        Configured FastMCP server instance
    """
    mcp = FastMCP("Azure Terraform MCP Server", version="0.6.0")

    # Initialize telemetry
    telemetry_manager = get_telemetry_manager()
    telemetry_manager.configure(
        connection_string=config.telemetry.connection_string,
        user_id=config.telemetry.user_id,
        enabled=config.telemetry.enabled,
        sample_rate=config.telemetry.sample_rate
    )
    
    # Register shutdown handler
    atexit.register(telemetry_manager.shutdown)

    # Get service instances
    azurerm_doc_provider = get_azurerm_documentation_provider()
    azapi_doc_provider = get_azapi_documentation_provider()
    terraform_runner = get_terraform_runner()
    aztfexport_runner = get_aztfexport_runner()
    coverage_auditor = get_coverage_auditor(terraform_runner, aztfexport_runner)

    # ==========================================
    # DOCUMENTATION TOOLS
    # ==========================================

    @mcp.tool("get_azurerm_provider_documentation")
    @track_tool_call("get_azurerm_provider_documentation")
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
    @track_tool_call("get_azapi_provider_documentation")
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
    # AZURE EXPORT FOR TERRAFORM (AZTFEXPORT) TOOLS
    # ==========================================

    @mcp.tool("check_aztfexport_installation")
    @track_tool_call("check_aztfexport_installation")
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
    @track_tool_call("export_azure_resource")
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
    @track_tool_call("export_azure_resource_group")
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
    @track_tool_call("export_azure_resources_by_query")
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


    # ==========================================
    # TERRAFORM COVERAGE AUDIT TOOLS
    # ==========================================

    @mcp.tool("audit_terraform_coverage")
    @track_tool_call("audit_terraform_coverage")
    async def audit_terraform_coverage(
        workspace_folder: str = Field(..., description="Terraform workspace to audit"),
        scope: str = Field(..., description="Audit scope: 'resource-group', 'subscription', 'query'"),
        scope_value: str = Field(..., description="Resource group name, subscription ID, or ARG query"),
        include_non_terraform_resources: bool = Field(default=True, description="Include resources not in Terraform"),
        include_orphaned_terraform_resources: bool = Field(default=True, description="Include Terraform resources not in Azure")
    ) -> Dict[str, Any]:
        """
        Audit Terraform coverage of Azure resources.

        This tool analyzes your Azure environment and compares it against your Terraform state
        to identify coverage gaps, orphaned resources, and provide recommendations for
        infrastructure management.

        **Use Cases:**
        - Identify Azure resources not yet under Terraform management
        - Find orphaned Terraform resources (deleted in Azure but still in state)
        - Measure Terraform coverage percentage
        - Get actionable recommendations for closing gaps

        **Audit Scopes:**
        - 'resource-group': Audit a specific resource group (provide RG name in scope_value)
        - 'subscription': Audit entire subscription (provide subscription ID in scope_value)
        - 'query': Custom Azure Resource Graph query (provide ARG WHERE clause in scope_value)

        Args:
            workspace_folder: Terraform workspace folder to audit (must be initialized with state)
            scope: Scope of the audit (resource-group, subscription, or query)
            scope_value: Scope-specific value (RG name, subscription ID, or ARG query)
            include_non_terraform_resources: Include Azure resources not in Terraform state
            include_orphaned_terraform_resources: Include Terraform resources not found in Azure

        Returns:
            Coverage audit report with summary, matched resources, missing resources, orphaned
            resources, and recommendations

        **Prerequisites:**
        - Terraform workspace must be initialized with `terraform init`
        - State file must exist (not empty)
        - Azure CLI must be authenticated (`az login`)
        - Azure Resource Graph access required

        **Example Usage:**
        ```
        # Audit a resource group
        audit_terraform_coverage(
            workspace_folder="workspace/my-terraform",
            scope="resource-group",
            scope_value="my-resource-group"
        )

        # Audit entire subscription
        audit_terraform_coverage(
            workspace_folder="workspace/my-terraform",
            scope="subscription",
            scope_value="12345678-1234-1234-1234-123456789012"
        )

        # Custom query for specific resources
        audit_terraform_coverage(
            workspace_folder="workspace/my-terraform",
            scope="query",
            scope_value="type =~ 'Microsoft.Storage/storageAccounts'"
        )
        ```

        **Report Structure:**
        - **summary**: Coverage statistics (percentage, counts)
        - **managed_resources**: Resources properly managed by Terraform
        - **missing_resources**: Azure resources not in Terraform (with export commands)
        - **orphaned_resources**: Terraform resources not found in Azure
        - **recommendations**: Actionable steps to improve coverage
        """
        try:
            result = await coverage_auditor.audit_coverage(
                workspace_folder=workspace_folder,
                scope=scope,
                scope_value=scope_value,
                include_non_terraform_resources=include_non_terraform_resources,
                include_orphaned_terraform_resources=include_orphaned_terraform_resources
            )
            return result

        except Exception as e:
            logger.error(f"Error auditing Terraform coverage: {e}")
            return {
                'success': False,
                'error': f'Failed to audit coverage: {str(e)}'
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

