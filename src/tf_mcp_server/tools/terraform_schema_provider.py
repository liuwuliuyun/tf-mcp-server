"""
Terraform Schema Provider for querying Terraform schemas and provider information.
"""

import asyncio
import json
import logging
import tempfile
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ProviderRequest:
    """Represents a request for a specific provider."""
    namespace: str
    name: str
    version: Optional[str] = None


class TerraformSchemaProvider:
    """Provider for Terraform schema operations using terraform command."""
    
    def __init__(self):
        self.supported_providers = ["azurerm", "azapi", "aws", "google", "kubernetes"]
    
    async def query_schema(
        self, 
        category: str, 
        resource_type: str, 
        path: Optional[str] = None,
        provider_namespace: str = "hashicorp",
        provider_name: Optional[str] = None,
        provider_version: Optional[str] = None
    ) -> str:
        """
        Query fine-grained Terraform schema information.
        
        Args:
            category: Terraform block type (resource, data, ephemeral, function, provider)
            resource_type: Resource type like azurerm_resource_group
            path: JSON path to query specific schema parts
            provider_namespace: Provider namespace
            provider_name: Provider name
            provider_version: Provider version
            
        Returns:
            JSON string representing the schema
        """
        try:
            # Infer provider name if not provided
            if not provider_name and category != "provider":
                provider_name = self._infer_provider_name(resource_type)
            
            # Validate category
            if category not in ["resource", "data", "ephemeral", "function", "provider"]:
                raise ValueError(f"Invalid category: {category}. Must be one of: resource, data, ephemeral, function, provider")
            
            # Create temporary terraform configuration
            with tempfile.TemporaryDirectory() as temp_dir:
                tf_file = os.path.join(temp_dir, "main.tf")
                
                # Generate terraform configuration based on category
                tf_content = self._generate_terraform_config(category, resource_type, provider_namespace, provider_name, provider_version)
                
                with open(tf_file, 'w') as f:
                    f.write(tf_content)
                
                # Initialize terraform
                init_process = await asyncio.create_subprocess_exec(
                    "terraform", "init",
                    cwd=temp_dir,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await init_process.communicate()
                
                # Get providers schema
                schema_process = await asyncio.create_subprocess_exec(
                    "terraform", "providers", "schema", "-json",
                    cwd=temp_dir,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await schema_process.communicate()
                
                if schema_process.returncode != 0:
                    logger.error(f"Failed to get schema: {stderr.decode()}")
                    return json.dumps({"error": f"Failed to get schema: {stderr.decode()}"})
                
                schema_data = json.loads(stdout.decode())
                
                # Extract the specific schema
                result = self._extract_schema(schema_data, category, resource_type, provider_namespace, provider_name, path)
                
                return json.dumps(result, indent=2)
                
        except Exception as e:
            logger.error(f"Error querying schema: {str(e)}")
            return json.dumps({"error": f"Failed to query schema: {str(e)}"})
    
    async def list_provider_items(
        self,
        category: str,
        provider_namespace: str = "hashicorp",
        provider_name: str = "azurerm",
        provider_version: Optional[str] = None
    ) -> List[str]:
        """
        List available items (resources, data sources, etc.) for a provider.
        
        Args:
            category: Item type (resource, data, ephemeral, function)
            provider_namespace: Provider namespace
            provider_name: Provider name
            provider_version: Provider version
            
        Returns:
            List of available items
        """
        try:
            if category not in ["resource", "data", "ephemeral", "function"]:
                raise ValueError(f"Invalid category: {category}. Must be one of: resource, data, ephemeral, function")
            
            with tempfile.TemporaryDirectory() as temp_dir:
                tf_file = os.path.join(temp_dir, "main.tf")
                
                # Generate terraform configuration
                tf_content = self._generate_terraform_config("provider", "", provider_namespace, provider_name, provider_version)
                
                with open(tf_file, 'w') as f:
                    f.write(tf_content)
                
                # Initialize terraform
                init_process = await asyncio.create_subprocess_exec(
                    "terraform", "init",
                    cwd=temp_dir,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await init_process.communicate()
                
                # Get providers schema
                schema_process = await asyncio.create_subprocess_exec(
                    "terraform", "providers", "schema", "-json",
                    cwd=temp_dir,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await schema_process.communicate()
                
                if schema_process.returncode != 0:
                    logger.error(f"Failed to get schema: {stderr.decode()}")
                    return []
                
                schema_data = json.loads(stdout.decode())
                
                # Extract items list
                items = self._extract_items_list(schema_data, category, provider_namespace, provider_name)
                
                return items
                
        except Exception as e:
            logger.error(f"Error listing provider items: {str(e)}")
            return []
    
    def get_supported_providers(self) -> List[str]:
        """Get list of supported providers."""
        return self.supported_providers.copy()
    
    def _infer_provider_name(self, resource_type: str) -> str:
        """Infer provider name from resource type."""
        if "_" in resource_type:
            return resource_type.split("_")[0]
        return "unknown"
    
    def _generate_terraform_config(
        self, 
        category: str, 
        resource_type: str,
        provider_namespace: str,
        provider_name: str,
        provider_version: Optional[str]
    ) -> str:
        """Generate Terraform configuration for schema query."""
        version_constraint = f'version = "{provider_version}"' if provider_version else ""
        
        if provider_name == "azurerm":
            return f'''
terraform {{
  required_providers {{
    {provider_name} = {{
      source = "{provider_namespace}/{provider_name}"
      {version_constraint}
    }}
  }}
}}

provider "{provider_name}" {{
  features {{}}
}}
'''
        else:
            return f'''
terraform {{
  required_providers {{
    {provider_name} = {{
      source = "{provider_namespace}/{provider_name}"
      {version_constraint}
    }}
  }}
}}

provider "{provider_name}" {{}}
'''
    
    def _extract_schema(
        self, 
        schema_data: Dict, 
        category: str, 
        resource_type: str,
        provider_namespace: str,
        provider_name: str,
        path: Optional[str]
    ) -> Dict:
        """Extract specific schema from the full schema data."""
        try:
            provider_key = f"{provider_namespace}/{provider_name}"
            
            if provider_key not in schema_data.get("provider_schemas", {}):
                return {"error": f"Provider {provider_key} not found in schema"}
            
            provider_schema = schema_data["provider_schemas"][provider_key]
            
            if category == "provider":
                result = provider_schema.get("provider", {})
            elif category == "resource":
                result = provider_schema.get("resource_schemas", {}).get(resource_type, {})
            elif category == "data":
                result = provider_schema.get("data_source_schemas", {}).get(resource_type, {})
            elif category == "function":
                result = provider_schema.get("functions", {}).get(resource_type, {})
            else:
                result = {"error": f"Unsupported category: {category}"}
            
            if not result:
                return {"error": f"Schema for {category} '{resource_type}' not found"}
            
            # Apply path filtering if specified
            if path and category != "function":
                result = self._query_schema_path(result, path)
            
            return result
            
        except Exception as e:
            return {"error": f"Failed to extract schema: {str(e)}"}
    
    def _extract_items_list(
        self, 
        schema_data: Dict, 
        category: str,
        provider_namespace: str,
        provider_name: str
    ) -> List[str]:
        """Extract list of items from schema data."""
        try:
            provider_key = f"{provider_namespace}/{provider_name}"
            
            if provider_key not in schema_data.get("provider_schemas", {}):
                return []
            
            provider_schema = schema_data["provider_schemas"][provider_key]
            
            if category == "resource":
                return list(provider_schema.get("resource_schemas", {}).keys())
            elif category == "data":
                return list(provider_schema.get("data_source_schemas", {}).keys())
            elif category == "function":
                return list(provider_schema.get("functions", {}).keys())
            else:
                return []
                
        except Exception as e:
            logger.error(f"Failed to extract items list: {str(e)}")
            return []
    
    def _query_schema_path(self, schema: Dict, path: str) -> Any:
        """Query specific path in schema."""
        try:
            current = schema
            parts = path.split(".")
            
            for part in parts:
                if isinstance(current, dict):
                    if "block" in current and part in current["block"].get("attributes", {}):
                        current = current["block"]["attributes"][part]
                    elif "block" in current and part in current["block"].get("block_types", {}):
                        current = current["block"]["block_types"][part]
                    elif part in current:
                        current = current[part]
                    else:
                        return {"error": f"Path '{part}' not found in schema"}
                else:
                    return {"error": f"Cannot navigate further at '{part}'"}
            
            return current
            
        except Exception as e:
            return {"error": f"Failed to query path: {str(e)}"}


# Global instance
_terraform_schema_provider = None

def get_terraform_schema_provider() -> TerraformSchemaProvider:
    """Get the global TerraformSchemaProvider instance."""
    global _terraform_schema_provider
    if _terraform_schema_provider is None:
        _terraform_schema_provider = TerraformSchemaProvider()
    return _terraform_schema_provider