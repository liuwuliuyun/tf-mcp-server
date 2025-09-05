"""
Main server implementation for Azure Terraform MCP Server.
"""

import logging
from typing import Dict, Any
from pydantic import Field
from fastmcp import FastMCP

from .config import Config
from ..tools.azurerm_docs_provider import get_azurerm_documentation_provider
from ..tools.azapi_docs_provider import get_azapi_documentation_provider
from ..tools.terraform_runner import get_terraform_runner
from ..tools.tflint_runner import get_tflint_runner
from ..tools.conftest_avm_runner import get_conftest_avm_runner

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
    azurerm_doc_provider = get_azurerm_documentation_provider()
    azapi_doc_provider = get_azapi_documentation_provider()
    terraform_runner = get_terraform_runner()
    tflint_runner = get_tflint_runner()
    conftest_avm_runner = get_conftest_avm_runner()
    
    # ==========================================
    # DOCUMENTATION TOOLS
    # ==========================================
    
    @mcp.tool("azurerm_terraform_documentation_retriever")
    async def retrieve_azurerm_docs(
        resource_type_name: str,
        doc_type: str = Field("resource", description="Type of documentation: 'resource' for resources or 'data-source' for data sources"),
        argument_name: str = Field("", description="Specific argument name to retrieve details for (optional)"),
        attribute_name: str = Field("", description="Specific attribute name to retrieve details for (optional)")
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
            doc_type_display = "Data Source" if doc_type.lower() in ["data-source", "datasource", "data_source"] else "Resource"
            
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
        command: str = Field(..., description="Terraform command to execute (init, plan, apply, destroy, validate, fmt)"),
        hcl_content: str = Field(..., description="HCL content to execute the command against"),
        var_file_content: str = Field("", description="Optional Terraform variables content (terraform.tfvars format)"),
        auto_approve: bool = Field(False, description="Auto-approve for apply/destroy commands (USE WITH CAUTION!)"),
        upgrade: bool = Field(False, description="Upgrade providers/modules for init command")
    ) -> Dict[str, Any]:
        """
        Execute any Terraform command with provided HCL content.
        
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
            hcl_content: HCL content to execute the command against
            var_file_content: Optional Terraform variables content
            auto_approve: Auto-approve for destructive operations (apply/destroy)
            upgrade: Upgrade providers/modules during init
            
        Returns:
            Command execution result with details based on command type:
            - For 'fmt': Returns formatted HCL content as string
            - For others: Returns Dict with exit_code, stdout, stderr, and command-specific data
        """
        vars_content = var_file_content if var_file_content.strip() else None
        
        # Handle format command separately as it returns formatted content
        if command == 'fmt':
            formatted_content = await terraform_runner.format_hcl_code(hcl_content)
            return {
                "command": "fmt",
                "success": True,
                "formatted_content": formatted_content,
                "exit_code": 0,
                "stdout": "Successfully formatted HCL content",
                "stderr": ""
            }
        
        # Handle other commands using the unified execution method
        kwargs = {}
        if command in ['apply', 'destroy'] and auto_approve:
            kwargs['auto_approve'] = auto_approve
        elif command == 'init' and upgrade:
            kwargs['upgrade'] = upgrade
        
        try:
            # Use the existing execute_terraform_command method
            result = await terraform_runner.execute_terraform_command(command, hcl_content, vars_content or "", **kwargs)
            
            # Ensure result is a dictionary
            if isinstance(result, str):
                # If the validator returns a string, wrap it in a proper response
                return {
                    "command": command,
                    "success": True,
                    "output": result,
                    "exit_code": 0,
                    "stdout": result,
                    "stderr": ""
                }
            elif isinstance(result, dict):
                # Add command info to the result
                result["command"] = command
                return result
            else:
                # Fallback for unexpected return types
                return {
                    "command": command,
                    "success": False,
                    "output": str(result),
                    "exit_code": 1,
                    "stdout": "",
                    "stderr": f"Unexpected result type: {type(result)}"
                }
                
        except Exception as e:
            return {
                "command": command,
                "success": False,
                "error": str(e),
                "exit_code": 1,
                "stdout": "",
                "stderr": str(e)
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
    
    # ==========================================
    # TFLINT TOOLS
    # ==========================================
    
    @mcp.tool("run_tflint_analysis")
    async def run_tflint_analysis(
        hcl_content: str,
        output_format: str = Field("json", description="Output format: json, default, checkstyle, junit, compact, sarif"),
        enable_azure_plugin: bool = Field(True, description="Enable Azure ruleset plugin"),
        enable_rules: str = Field("", description="Comma-separated list of rules to enable"),
        disable_rules: str = Field("", description="Comma-separated list of rules to disable"),
        var_file_content: str = Field("", description="Optional Terraform variables content"),
        initialize_plugins: bool = Field(True, description="Whether to initialize plugins")
    ) -> Dict[str, Any]:
        """
        Run TFLint static analysis on Terraform configuration.
        
        Args:
            hcl_content: Terraform HCL content to analyze
            output_format: Output format (json, default, checkstyle, junit, compact, sarif)
            enable_azure_plugin: Whether to enable the Azure ruleset plugin
            enable_rules: Comma-separated list of specific rules to enable
            disable_rules: Comma-separated list of specific rules to disable
            var_file_content: Optional Terraform variables content
            initialize_plugins: Whether to run tflint --init to install plugins
            
        Returns:
            TFLint analysis results with issues, summary, and recommendations
        """
        try:
            # Parse rule lists
            enable_rules_list = [rule.strip() for rule in enable_rules.split(',') if rule.strip()] if enable_rules else None
            disable_rules_list = [rule.strip() for rule in disable_rules.split(',') if rule.strip()] if disable_rules else None
            
            # Run TFLint analysis
            result = await tflint_runner.lint_terraform_configuration(
                hcl_content=hcl_content,
                output_format=output_format,
                enable_azure_plugin=enable_azure_plugin,
                enable_rules=enable_rules_list,
                disable_rules=disable_rules_list,
                var_file_content=var_file_content if var_file_content else None,
                initialize_plugins=initialize_plugins
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error running TFLint analysis: {e}")
            return {
                'success': False,
                'error': f'TFLint analysis failed: {str(e)}',
                'issues': [],
                'summary': {
                    'total_issues': 0,
                    'errors': 0,
                    'warnings': 0,
                    'notices': 0
                }
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

    # ==========================================
    # CONFTEST AVM POLICY TOOLS
    # ==========================================
    
    @mcp.tool("run_conftest_validation")
    async def run_conftest_validation(
        hcl_content: str,
        policy_set: str = Field("all", description="Policy set: 'all', 'Azure-Proactive-Resiliency-Library-v2', 'avmsec'"),
        severity_filter: str = Field("", description="Severity filter for avmsec policies: 'high', 'medium', 'low', 'info'"),
        custom_policies: str = Field("", description="Comma-separated list of custom policy paths")
    ) -> Dict[str, Any]:
        """
        Validate Terraform HCL content against Azure security policies and best practices using Conftest.
        
        Supports validation of Azure resources using azurerm, azapi, and AVM (Azure Verified Modules) providers
        with comprehensive security checks, compliance rules, and operational best practices.
        
        Args:
            hcl_content: Terraform HCL content to validate
            policy_set: Policy set to use ('all', 'Azure-Proactive-Resiliency-Library-v2', 'avmsec')
            severity_filter: Filter by severity for avmsec policies ('high', 'medium', 'low', 'info')
            custom_policies: Comma-separated list of custom policy paths
            
        Returns:
            Policy validation results with violations and recommendations
        """
        try:
            # Parse custom policies if provided
            custom_policies_list = [p.strip() for p in custom_policies.split(',') if p.strip()] if custom_policies else None
            severity = severity_filter if severity_filter else None
            
            # Run validation
            result = await conftest_avm_runner.validate_terraform_hcl_with_avm_policies(
                hcl_content=hcl_content,
                policy_set=policy_set,
                severity_filter=severity,
                custom_policies=custom_policies_list
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error running Conftest AVM validation: {e}")
            return {
                'success': False,
                'error': f'Conftest AVM validation failed: {str(e)}',
                'violations': [],
                'summary': {
                    'total_violations': 0,
                    'failures': 0,
                    'warnings': 0
                }
            }
    
    @mcp.tool("run_conftest_plan_validation")
    async def run_conftest_plan_validation(
        terraform_plan_json: str,
        policy_set: str = Field("all", description="Policy set: 'all', 'Azure-Proactive-Resiliency-Library-v2', 'avmsec'"),
        severity_filter: str = Field("", description="Severity filter for avmsec policies: 'high', 'medium', 'low', 'info'"),
        custom_policies: str = Field("", description="Comma-separated list of custom policy paths")
    ) -> Dict[str, Any]:
        """
        Validate Terraform plan JSON against Azure security policies and best practices using Conftest.
        
        Supports validation of Azure resources using azurerm, azapi, and AVM (Azure Verified Modules) providers
        with comprehensive security checks, compliance rules, and operational best practices.
        
        Args:
            terraform_plan_json: Terraform plan in JSON format
            policy_set: Policy set to use ('all', 'Azure-Proactive-Resiliency-Library-v2', 'avmsec')
            severity_filter: Filter by severity for avmsec policies ('high', 'medium', 'low', 'info')
            custom_policies: Comma-separated list of custom policy paths
            
        Returns:
            Policy validation results with violations and recommendations
        """
        try:
            # Parse custom policies if provided
            custom_policies_list = [p.strip() for p in custom_policies.split(',') if p.strip()] if custom_policies else None
            severity = severity_filter if severity_filter else None
            
            # Run validation
            result = await conftest_avm_runner.validate_with_avm_policies(
                terraform_plan_json=terraform_plan_json,
                policy_set=policy_set,
                severity_filter=severity,
                custom_policies=custom_policies_list
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error running Conftest AVM plan validation: {e}")
            return {
                'success': False,
                'error': f'Conftest AVM plan validation failed: {str(e)}',
                'violations': [],
                'summary': {
                    'total_violations': 0,
                    'failures': 0,
                    'warnings': 0
                }
            }
    
    return mcp


async def run_server(config: Config) -> None:
    """
    Run the MCP server.
    
    Args:
        config: Server configuration
    """
    server = create_server(config)
    
    logger.info(f"Starting Azure Terraform MCP Server on {config.server.host}:{config.server.port}")
    
    try:
        await server.run_async(
            transport="http",
            host=config.server.host,
            port=config.server.port
        )
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise
