"""
AzAPI provider documentation tools for Azure Terraform MCP Server.
"""

from typing import Dict, Any
from httpx import AsyncClient

from ..core.azapi_schema_generator import AzAPISchemaGenerator


class AzAPIDocumentationProvider:
    """Provider for AzAPI Terraform documentation."""
    
    def __init__(self):
        """Initialize the AzAPI documentation provider."""
        self.azapi_schema = AzAPISchemaGenerator().load_with_version_check()
    
    async def search_azapi_provider_docs(
        self, 
        resource_type: str, 
        api_version: str = ""
    ) -> Dict[str, Any]:
        """
        Search Azure API provider documentation and schemas.
        
        Args:
            resource_type: Azure API resource type
            api_version: Optional specific API version
            
        Returns:
            Dictionary containing AzAPI documentation and schema information
        """
        try:
            # Search in loaded schema
            schema_info = self._search_azapi_schema(resource_type, api_version)
            
            if schema_info:
                return {
                    "resource_type": resource_type,
                    "api_version": api_version or "latest",
                    "schema": schema_info,
                    "source": "azapi_schemas.json"
                }
            
            # If not found in local schema, try to fetch from Azure docs
            return await self._fetch_azapi_docs_online(resource_type, api_version)
            
        except Exception as e:
            return {
                "error": f"Error searching AzAPI documentation: {str(e)}",
                "resource_type": resource_type,
                "api_version": api_version
            }
    
    def _search_azapi_schema(self, resource_type: str, api_version: str = "") -> Dict[str, Any]:
        """Search in the loaded AzAPI schema."""
        if not self.azapi_schema:
            return {}
        
        # Normalize the resource type for searching
        search_type = resource_type.lower()
        
        # Search through the schema
        for key, value in self.azapi_schema.items():
            if search_type in key.lower():
                return {
                    "definition": value,
                    "schema_key": key
                }
        
        return {}
    
    async def _fetch_azapi_docs_online(self, resource_type: str, api_version: str) -> Dict[str, Any]:
        """Fetch AzAPI documentation from online sources."""
        try:
            # Try Azure REST API documentation
            azure_docs_url = f"https://docs.microsoft.com/en-us/rest/api/{resource_type.lower()}"
            
            async with AsyncClient(timeout=30.0) as client:
                response = await client.get(azure_docs_url)
                
                if response.status_code == 200:
                    return {
                        "resource_type": resource_type,
                        "api_version": api_version or "latest",
                        "documentation_url": azure_docs_url,
                        "source": "Azure REST API docs",
                        "summary": f"Azure REST API documentation for {resource_type}"
                    }
        
        except Exception as e:
            pass  # Continue to fallback
        
        # Fallback response
        return {
            "resource_type": resource_type,
            "api_version": api_version or "latest",
            "summary": f"AzAPI resource type: {resource_type}",
            "documentation_url": "https://registry.terraform.io/providers/Azure/azapi/latest/docs",
            "source": "fallback"
        }


# Global instance
_azapi_provider = None


def get_azapi_documentation_provider() -> AzAPIDocumentationProvider:
    """Get the global AzAPI documentation provider instance."""
    global _azapi_provider
    if _azapi_provider is None:
        _azapi_provider = AzAPIDocumentationProvider()
    return _azapi_provider
