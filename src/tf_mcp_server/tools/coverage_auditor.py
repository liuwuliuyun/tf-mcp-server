"""
Terraform Coverage Auditor for Azure Terraform MCP Server.

This module analyzes Azure environments and compares them against Terraform state
to identify coverage gaps, orphaned resources, and provide recommendations.
"""

import asyncio
import json
import logging
import os
import re
from typing import Dict, Any, List, Optional, Set, Tuple

from ..core.utils import resolve_workspace_path, get_docker_path_tip

logger = logging.getLogger(__name__)


class ResourceMatcher:
    """Handles matching between Azure resources and Terraform state addresses."""
    
    @staticmethod
    def extract_resource_name_from_id(resource_id: str) -> str:
        """Extract resource name from Azure resource ID."""
        if not resource_id:
            return ""
        parts = resource_id.split('/')
        return parts[-1] if parts else ""
    
    @staticmethod
    def extract_resource_type_from_id(resource_id: str) -> str:
        """Extract resource type from Azure resource ID."""
        if not resource_id:
            return ""
        # Azure resource ID format: /subscriptions/{sub}/resourceGroups/{rg}/providers/{provider}/{type}/{name}
        parts = resource_id.split('/')
        try:
            provider_index = parts.index('providers')
            if provider_index + 2 < len(parts):
                provider = parts[provider_index + 1]
                resource_type = parts[provider_index + 2]
                return f"{provider}/{resource_type}"
        except (ValueError, IndexError) as e:
            logger.debug(f"Failed to extract resource type from id '{resource_id}': {e}")
        return ""
    
    @staticmethod
    def normalize_resource_name(name: str) -> str:
        """Normalize resource name for comparison (lowercase, remove special chars)."""
        return re.sub(r'[^a-z0-9]', '', name.lower())
    
    @staticmethod
    def parse_terraform_address(tf_address: str) -> Tuple[str, str]:
        """
        Parse Terraform resource address into type and name.
        
        Args:
            tf_address: Terraform address (e.g., "azurerm_storage_account.my_storage")
            
        Returns:
            Tuple of (terraform_type, resource_name)
        """
        parts = tf_address.split('.')
        if len(parts) >= 2:
            tf_type = parts[0]
            tf_name = '.'.join(parts[1:])  # Handle names with dots
            return tf_type, tf_name
        return "", ""
    
    @staticmethod
    async def get_state_resource_details(
        terraform_runner,
        workspace_folder: str,
        resource_addresses: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get detailed information about resources from Terraform state file.
        
        Args:
            terraform_runner: TerraformRunner instance
            workspace_folder: Workspace folder path
            resource_addresses: List of Terraform resource addresses
            
        Returns:
            Dictionary mapping resource addresses to their details including Azure resource IDs
        """
        resource_details = {}
        
        try:
            # Read the terraform.tfstate file directly
            workspace_path = resolve_workspace_path(workspace_folder)
            tfstate_path = workspace_path / "terraform.tfstate"
            
            if not tfstate_path.exists():
                logger.warning(
                    f"Terraform state file not found at {tfstate_path}\n\n"
                    f"Tip: When running in Docker, ensure you're using the correct workspace folder.\n"
                    f"     Default mount: -v ${{workspaceFolder}}:/workspace\n"
                    f"     Use relative paths like 'my-folder' which resolves to /workspace/my-folder"
                )
                
                # Check if workspace is initialized
                terraform_dir = workspace_path / ".terraform"
                if not terraform_dir.exists():
                    logger.info("Workspace not initialized. Running terraform init...")
                    init_result = await terraform_runner.execute_terraform_command(
                        command="init",
                        workspace_folder=workspace_folder
                    )
                    
                    if init_result.get('exit_code') != 0:
                        logger.error(f"Terraform init failed: {init_result.get('stderr')}")
                        return resource_details
                    
                    logger.info("Terraform init completed successfully")
                    
                    # Check again for state file after init (in case it's remote)
                    if not tfstate_path.exists():
                        logger.warning(
                            "State file still not found after initialization. "
                            "This workspace may use remote state or has not been applied yet. "
                            "Run 'terraform apply' to create resources and generate state."
                        )
                        return resource_details
                else:
                    logger.warning(
                        "Workspace is initialized but state file not found. "
                        "This may be a remote state configuration or resources haven't been created. "
                        "Run 'terraform apply' to create resources."
                    )
                    return resource_details
            
            # Load the state file
            with open(tfstate_path, 'r', encoding='utf-8') as f:
                state_data = json.load(f)
            
            # Extract resources from state file
            # Terraform state structure: state.resources[] contains all resources
            resources = state_data.get('resources', [])
            
            for resource in resources:
                resource_type = resource.get('type', '')
                resource_name = resource.get('name', '')
                resource_mode = resource.get('mode', 'managed')
                
                # Skip data sources, focus on managed resources
                if resource_mode != 'managed':
                    continue
                
                # Handle both single instances and resource arrays (count/for_each)
                instances = resource.get('instances', [])
                
                for instance in instances:
                    # Build the resource address
                    # For single resources: type.name
                    # For counted/for_each resources: type.name[key]
                    index_key = instance.get('index_key')
                    if index_key is not None:
                        if isinstance(index_key, int):
                            address = f"{resource_type}.{resource_name}[{index_key}]"
                        else:
                            # String key for for_each
                            address = f'{resource_type}.{resource_name}["{index_key}"]'
                    else:
                        address = f"{resource_type}.{resource_name}"
                    
                    # Only process if this address is in our list
                    if address not in resource_addresses:
                        continue
                    
                    # Get the resource attributes
                    attributes = instance.get('attributes', {})
                    
                    # Extract Azure resource ID
                    azure_id = attributes.get('id', '')
                    
                    resource_details[address] = {
                        'terraform_type': resource_type,
                        'terraform_name': resource_name,
                        'azure_resource_id': azure_id,
                        'normalized_name': ResourceMatcher.normalize_resource_name(resource_name),
                        'attributes': attributes  # Store full attributes for potential future use
                    }
            
            logger.info(f"Extracted details for {len(resource_details)} resources from state file")
            
        except FileNotFoundError:
            logger.error(
                f"Terraform state file not found in {workspace_folder}\n\n"
                f"Tip: When running in Docker, ensure you're using the correct workspace folder.\n"
                f"     Default mount: -v ${{workspaceFolder}}:/workspace\n"
                f"     Use relative paths like 'my-folder' which resolves to /workspace/my-folder"
            )
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse terraform.tfstate file: {e}")
        except Exception as e:
            logger.error(f"Failed to read state file: {e}")
        
        return resource_details
    
    @staticmethod
    def _extract_azure_id_from_state_show(state_output: str) -> str:
        """
        Extract Azure resource ID from terraform state show output.
        
        Args:
            state_output: Output from terraform state show command
            
        Returns:
            Azure resource ID or empty string
        """
        # Look for common ID patterns in state output
        # Pattern 1: id = "/subscriptions/..."
        id_match = re.search(r'id\s*=\s*["\']?(/subscriptions/[^"\'\s]+)["\']?', state_output)
        if id_match:
            return id_match.group(1)
        
        # Pattern 2: Look for resource_group_id or similar
        # This helps with child resources
        for pattern in [r'resource_group_id', r'virtual_network_id', r'subnet_id']:
            match = re.search(f'{pattern}\\s*=\\s*["\']?(/subscriptions/[^"\'\\s]+)["\']?', state_output)
            if match:
                # Use this as a hint for the resource group at least
                return match.group(1)
        
        return ""
    
    @staticmethod
    async def match_resources(
        azure_resources: List[Dict[str, Any]],
        terraform_runner,
        workspace_folder: str,
        terraform_resource_addresses: List[str]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Match Azure resources with Terraform state resources using dynamic state lookup.
        
        Args:
            azure_resources: List of Azure resources from ARG query
            terraform_runner: TerraformRunner instance for state queries
            workspace_folder: Workspace folder path
            terraform_resource_addresses: List of Terraform resource addresses from state
            
        Returns:
            Tuple of (matched_resources, missing_in_terraform, orphaned_in_terraform)
        """
        matched = []
        missing = []
        matched_terraform = set()
        
        # Get detailed information about Terraform resources from state
        logger.info(f"Fetching detailed state information for {len(terraform_resource_addresses)} Terraform resources...")
        tf_resource_details = await ResourceMatcher.get_state_resource_details(
            terraform_runner,
            workspace_folder,
            terraform_resource_addresses
        )
        
        # Create lookup dictionaries for efficient matching
        # Map normalized Azure resource IDs to Terraform addresses
        azure_id_to_tf = {}
        normalized_name_to_tf = {}
        
        for tf_address, details in tf_resource_details.items():
            azure_id = details.get('azure_resource_id', '')
            if azure_id:
                # Normalize Azure ID (lowercase, no trailing slashes)
                normalized_id = azure_id.lower().rstrip('/')
                azure_id_to_tf[normalized_id] = tf_address
            
            # Also index by normalized name for fuzzy matching
            normalized_name = details.get('normalized_name', '')
            if normalized_name:
                if normalized_name not in normalized_name_to_tf:
                    normalized_name_to_tf[normalized_name] = []
                normalized_name_to_tf[normalized_name].append(tf_address)
        
        logger.info(f"Built lookup index with {len(azure_id_to_tf)} Azure ID mappings")
        
        # Match Azure resources
        for azure_resource in azure_resources:
            resource_id = azure_resource.get('id', '')
            resource_type = azure_resource.get('type', '')
            resource_name = ResourceMatcher.extract_resource_name_from_id(resource_id)
            normalized_azure_id = resource_id.lower().rstrip('/')
            normalized_azure_name = ResourceMatcher.normalize_resource_name(resource_name)
            
            matched_tf_address = None
            match_method = None
            
            # Strategy 1: Match by exact Azure resource ID (most reliable)
            if normalized_azure_id in azure_id_to_tf:
                matched_tf_address = azure_id_to_tf[normalized_azure_id]
                match_method = 'azure_id'
            
            # Strategy 2: Match by normalized name (fallback for fuzzy matching)
            elif normalized_azure_name in normalized_name_to_tf:
                # If multiple matches, try to pick the best one based on type similarity
                candidates = normalized_name_to_tf[normalized_azure_name]
                if len(candidates) == 1:
                    matched_tf_address = candidates[0]
                    match_method = 'name'
                else:
                    # Multiple candidates - pick one that might match the resource type
                    # This is a best-effort heuristic
                    for candidate in candidates:
                        tf_type = tf_resource_details[candidate]['terraform_type']
                        # Simple heuristic: if azure type contains part of tf type
                        azure_type_simplified = resource_type.lower().replace('microsoft.', '').replace('/', '')
                        if azure_type_simplified in tf_type.lower():
                            matched_tf_address = candidate
                            match_method = 'name_with_type_hint'
                            break
                    
                    # If still no match, just take the first one
                    if not matched_tf_address:
                        matched_tf_address = candidates[0]
                        match_method = 'name_ambiguous'
            
            if matched_tf_address:
                tf_details = tf_resource_details[matched_tf_address]
                matched.append({
                    'azure_resource_id': resource_id,
                    'azure_resource_type': resource_type,
                    'azure_resource_name': resource_name,
                    'terraform_address': matched_tf_address,
                    'terraform_type': tf_details['terraform_type'],
                    'match_confidence': 'high' if match_method == 'azure_id' else 'medium',
                    'match_method': match_method
                })
                matched_terraform.add(matched_tf_address)
            else:
                # No match found - resource missing in Terraform
                missing.append({
                    'resource_id': resource_id,
                    'resource_type': resource_type,
                    'resource_name': resource_name,
                    'location': azure_resource.get('location', 'unknown'),
                    'reason': 'Not found in Terraform state'
                })
        
        # Find orphaned Terraform resources (not matched to Azure)
        orphaned: List[Dict[str, Any]] = []
        for tf_address in terraform_resource_addresses:
            if tf_address not in matched_terraform:
                tf_type, tf_name = ResourceMatcher.parse_terraform_address(tf_address)
                orphaned.append({
                    'terraform_address': tf_address,
                    'terraform_type': tf_type,
                    'terraform_name': tf_name,
                    'reason': 'Resource not found in Azure or could not be matched'
                })
        
        logger.info(f"Matching complete: {len(matched)} matched, {len(missing)} missing, {len(orphaned)} orphaned")
        
        return matched, missing, orphaned


class CoverageAuditor:
    """Audits Terraform coverage of Azure resources."""
    
    def __init__(self, terraform_runner, aztfexport_runner):
        """
        Initialize the coverage auditor.
        
        Args:
            terraform_runner: TerraformRunner instance for state operations
            aztfexport_runner: AztfexportRunner instance for Azure queries
        """
        self.terraform_runner = terraform_runner
        self.aztfexport_runner = aztfexport_runner
        self.resource_matcher = ResourceMatcher()
        self.auth_attempted = False
        self.auth_successful = False
    
    async def _authenticate_azure_cli(self):
        """
        Attempt to authenticate Azure CLI using service principal credentials from environment.
        
        This method checks for ARM environment variables and attempts to login with Azure CLI.
        If authentication fails or credentials are not available, it logs a warning but does not fail.
        """
        if self.auth_attempted:
            return
        
        self.auth_attempted = True
        
        # Check for service principal credentials
        client_id = os.environ.get('ARM_CLIENT_ID')
        client_secret = os.environ.get('ARM_CLIENT_SECRET')
        tenant_id = os.environ.get('ARM_TENANT_ID')
        
        if not all([client_id, client_secret, tenant_id]):
            logger.warning(
                "Azure service principal credentials not found in environment variables. "
                "Coverage auditor will attempt to use existing Azure CLI authentication. "
                "Set ARM_CLIENT_ID, ARM_CLIENT_SECRET, and ARM_TENANT_ID for service principal authentication."
            )
            # Check if user is already logged in with az CLI
            try:
                check_process = await asyncio.create_subprocess_exec(
                    'az', 'account', 'show',
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await check_process.communicate()
                
                if check_process.returncode == 0:
                    logger.info("Using existing Azure CLI authentication session")
                    self.auth_successful = True
                else:
                    logger.warning(
                        "No active Azure CLI session found. Please run 'az login' or set service principal credentials. "
                        "Azure resource queries will fail without authentication."
                    )
            except Exception as e:
                logger.warning(f"Failed to check Azure CLI authentication status: {e}")
            return
        
        # Attempt service principal login
        try:
            logger.info("Attempting Azure CLI authentication with service principal...")
            
            command = [
                'az', 'login',
                '--service-principal',
                '-u', client_id,
                '-p', client_secret,
                '--tenant', tenant_id
            ]
            
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                logger.info("Azure CLI authentication successful")
                self.auth_successful = True
                
                # Set default subscription if ARM_SUBSCRIPTION_ID is provided
                subscription_id = os.environ.get('ARM_SUBSCRIPTION_ID')
                if subscription_id:
                    try:
                        set_sub_process = await asyncio.create_subprocess_exec(
                            'az', 'account', 'set',
                            '--subscription', subscription_id,
                            stdout=asyncio.subprocess.PIPE,
                            stderr=asyncio.subprocess.PIPE
                        )
                        await set_sub_process.communicate()
                        if set_sub_process.returncode == 0:
                            logger.info(f"Set default subscription to: {subscription_id}")
                    except Exception as e:
                        logger.warning(f"Failed to set default subscription: {e}")
            else:
                error_msg = stderr.decode() if stderr else "Unknown error"
                logger.warning(
                    f"Azure CLI authentication failed: {error_msg}. "
                    "Coverage auditor will continue but Azure resource queries may fail."
                )
        
        except Exception as e:
            logger.warning(
                f"Failed to authenticate with Azure CLI: {e}. "
                "Coverage auditor will continue but Azure resource queries may fail."
            )
    
    async def audit_coverage(
        self,
        workspace_folder: str,
        scope: str = "resource-group",
        scope_value: str = "",
        include_non_terraform_resources: bool = True,
        include_orphaned_terraform_resources: bool = True
    ) -> Dict[str, Any]:
        """
        Audit Terraform coverage of Azure resources.
        
        Args:
            workspace_folder: Terraform workspace to audit
            scope: Audit scope ('resource-group', 'subscription', 'query')
            scope_value: Resource group name, subscription ID, or ARG query
            include_non_terraform_resources: Include resources not in Terraform
            include_orphaned_terraform_resources: Include Terraform resources not in Azure
            
        Returns:
            Coverage audit report
        """
        try:
            logger.info(f"Starting coverage audit for workspace: {workspace_folder}")
            
            # Ensure Azure authentication is attempted before querying
            if not self.auth_attempted:
                await self._authenticate_azure_cli()
            
            # Validate workspace
            try:
                workspace_path = resolve_workspace_path(workspace_folder)
            except ValueError as e:
                return {
                    'success': False,
                    'error': f'{str(e)}{get_docker_path_tip(workspace_folder)}'
                }
            
            # Step 1: Get Terraform state
            terraform_resources = await self._get_terraform_state_resources(workspace_folder)
            if terraform_resources is None:
                return {
                    'success': False,
                    'error': 'Failed to retrieve Terraform state. Ensure workspace is initialized and state exists.'
                }
            
            logger.info(f"Found {len(terraform_resources)} resources in Terraform state")
            
            # Step 2: Query Azure resources
            azure_resources = await self._query_azure_resources(scope, scope_value)
            if azure_resources is None:
                error_msg = 'Failed to query Azure resources. '
                if not self.auth_successful:
                    error_msg += 'Azure authentication may not be configured. Please run "az login" or set ARM_CLIENT_ID, ARM_CLIENT_SECRET, and ARM_TENANT_ID environment variables. '
                error_msg += 'Check Azure authentication and scope parameters.'
                return {
                    'success': False,
                    'error': error_msg
                }
            
            logger.info(f"Found {len(azure_resources)} resources in Azure")
            
            # Step 3: Match resources using dynamic state-based matching
            matched, missing, orphaned = await self.resource_matcher.match_resources(
                azure_resources=azure_resources,
                terraform_runner=self.terraform_runner,
                workspace_folder=workspace_folder,
                terraform_resource_addresses=terraform_resources
            )
            
            # Step 4: Generate report
            report = self._generate_report(
                matched=matched,
                missing=missing if include_non_terraform_resources else [],
                orphaned=orphaned if include_orphaned_terraform_resources else [],
                total_azure=len(azure_resources),
                total_terraform=len(terraform_resources)
            )
            
            logger.info(f"Coverage audit completed: {report['summary']['coverage_percentage']:.1f}% coverage")
            
            return report
            
        except Exception as e:
            logger.error(f"Coverage audit failed: {e}", exc_info=True)
            return {
                'success': False,
                'error': f'Coverage audit failed: {str(e)}'
            }
    
    async def _get_terraform_state_resources(self, workspace_folder: str) -> Optional[List[str]]:
        """
        Get list of resources from Terraform state.
        
        Args:
            workspace_folder: Terraform workspace folder
            
        Returns:
            List of Terraform resource addresses or None on error
        """
        try:
            # Use terraform state list to get all resources
            result = await self.terraform_runner.execute_terraform_command(
                command="state list",
                workspace_folder=workspace_folder
            )
            
            if result.get('exit_code') != 0:
                logger.error(f"Terraform state list failed: {result.get('stderr')}")
                return None
            
            # Parse output - one resource per line
            stdout = result.get('stdout', '')
            resources = [line.strip() for line in stdout.split('\n') if line.strip()]
            
            return resources
            
        except Exception as e:
            logger.error(f"Failed to get Terraform state: {e}")
            return None
    
    async def _query_azure_resources(
        self,
        scope: str,
        scope_value: str
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Query Azure resources based on scope.
        
        Args:
            scope: Audit scope ('resource-group', 'subscription', 'query')
            scope_value: Scope-specific value
            
        Returns:
            List of Azure resources or None on error
        """
        try:
            # Build Azure Resource Graph query based on scope
            if scope == "resource-group":
                query = f"resourceGroup =~ '{scope_value}'"
            elif scope == "subscription":
                # Query all resources in subscription (scope_value should be subscription ID)
                query = f"subscriptionId =~ '{scope_value}'"
            elif scope == "query":
                # Use custom ARG query
                query = scope_value
            else:
                logger.error(f"Invalid scope: {scope}")
                return None
            
            # Use Azure CLI to run Resource Graph query
            # Note: aztfexport uses ARG internally, but we'll use az CLI directly for flexibility
            command = [
                'az', 'graph', 'query',
                '-q', f"Resources | where {query} | project id, name, type, location, resourceGroup",
                '--output', 'json'
            ]
            
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                logger.error(f"Azure Resource Graph query failed: {stderr.decode()}")
                return None
            
            # Parse JSON result
            result = json.loads(stdout.decode())
            
            # ARG returns results in 'data' field
            resources = result.get('data', [])
            
            # For resource-group scope, also include the resource group itself
            # The resource group is not returned in the resources query (it only returns resources within the RG)
            if scope == "resource-group" and scope_value:
                rg_command = [
                    'az', 'group', 'show',
                    '--name', scope_value,
                    '--output', 'json'
                ]
                
                rg_process = await asyncio.create_subprocess_exec(
                    *rg_command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                rg_stdout, rg_stderr = await rg_process.communicate()
                
                if rg_process.returncode == 0:
                    rg_data = json.loads(rg_stdout.decode())
                    # Format the resource group to match the ARG query result format
                    rg_resource = {
                        'id': rg_data.get('id', ''),
                        'name': rg_data.get('name', ''),
                        'type': 'microsoft.resources/resourcegroups',
                        'location': rg_data.get('location', ''),
                        'resourceGroup': rg_data.get('name', '')
                    }
                    # Add the resource group to the beginning of the list
                    resources = [rg_resource] + resources
                    logger.info(f"Added resource group '{scope_value}' to the resources list")
                else:
                    logger.warning(f"Failed to query resource group itself: {rg_stderr.decode()}")
            
            return resources
            
        except Exception as e:
            logger.error(f"Failed to query Azure resources: {e}")
            return None
    
    def _generate_report(
        self,
        matched: List[Dict[str, Any]],
        missing: List[Dict[str, Any]],
        orphaned: List[Dict[str, Any]],
        total_azure: int,
        total_terraform: int
    ) -> Dict[str, Any]:
        """
        Generate coverage audit report.
        
        Args:
            matched: List of matched resources
            missing: List of Azure resources not in Terraform
            orphaned: List of Terraform resources not in Azure
            total_azure: Total Azure resources queried
            total_terraform: Total Terraform resources in state
            
        Returns:
            Coverage report dictionary
        """
        coverage_percentage = (len(matched) / total_azure * 100) if total_azure > 0 else 0
        
        # Generate recommendations
        recommendations = []
        if missing:
            recommendations.append(
                f"Export {len(missing)} unmanaged resources using aztfexport tools"
            )
        if orphaned:
            recommendations.append(
                f"Review {len(orphaned)} orphaned resources in Terraform state - "
                "they may have been deleted in Azure or renamed"
            )
        if coverage_percentage < 100 and not missing:
            recommendations.append(
                "Some resources could not be automatically matched. Review Azure and Terraform resources manually."
            )
        if coverage_percentage == 100:
            recommendations.append(
                "Excellent! All Azure resources in scope are managed by Terraform."
            )
        
        # Add export commands for missing resources
        for resource in missing:
            resource['export_command'] = (
                f"Use export_azure_resource with resource_id='{resource['resource_id']}'"
            )
        
        report = {
            'success': True,
            'summary': {
                'total_azure_resources': total_azure,
                'total_terraform_resources': total_terraform,
                'terraform_managed': len(matched),
                'coverage_percentage': round(coverage_percentage, 2),
                'missing_from_terraform': len(missing),
                'orphaned_in_terraform': len(orphaned)
            },
            'managed_resources': matched,
            'missing_resources': missing,
            'orphaned_resources': orphaned,
            'recommendations': recommendations
        }
        
        return report


def get_coverage_auditor(terraform_runner, aztfexport_runner) -> CoverageAuditor:
    """
    Get a CoverageAuditor instance.
    
    Args:
        terraform_runner: TerraformRunner instance
        aztfexport_runner: AztfexportRunner instance
        
    Returns:
        CoverageAuditor instance
    """
    return CoverageAuditor(terraform_runner, aztfexport_runner)
