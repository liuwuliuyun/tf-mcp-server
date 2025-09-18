"""
Golang Source Code Provider for analyzing Go source code in Terraform providers.
"""

import asyncio
import json
import logging
import os
import httpx
import base64
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RemoteIndex:
    """Represents a remote repository index configuration."""
    github_owner: str
    github_repo: str
    package_path: str


@dataclass
class GolangNamespace:
    """Represents a golang namespace/package."""
    name: str
    description: str
    tags: List[str]


class GolangSourceProvider:
    """Provider for Golang source code analysis operations."""
    
    def __init__(self):
        # Remote index mapping following terraform-mcp-eva pattern
        self.remote_index_map = {
            "github.com/hashicorp/terraform-provider-azurerm/internal": RemoteIndex(
                github_owner="lonegunmanb",
                github_repo="terraform-provider-azurerm-index",
                package_path="github.com/hashicorp/terraform-provider-azurerm"
            ),
            "github.com/Azure/terraform-provider-azapi/internal": RemoteIndex(
                github_owner="lonegunmanb", 
                github_repo="terraform-provider-azapi-index",
                package_path="github.com/Azure/terraform-provider-azapi"
            )
        }
        
        # Provider index mapping - maps provider name to namespace
        self.provider_index_map = {
            "azurerm": "github.com/hashicorp/terraform-provider-azurerm/internal",
            "azapi": "github.com/Azure/terraform-provider-azapi/internal"
        }
        
        self.supported_providers = ["azurerm", "azapi"]
    
    def get_supported_namespaces(self) -> List[str]:
        """Get all supported golang namespaces."""
        return list(self.remote_index_map.keys())
    
    async def get_supported_tags(self, namespace: str) -> List[str]:
        """Get supported tags for a specific namespace by querying GitHub API."""
        if namespace not in self.remote_index_map:
            raise ValueError(f"Unsupported namespace: {namespace}")
        
        remote_index = self.remote_index_map[namespace]
        
        try:
            async with httpx.AsyncClient() as client:
                # Set up GitHub token if available
                headers = {"Accept": "application/vnd.github.v3+json"}
                github_token = os.getenv("GITHUB_TOKEN")
                if github_token:
                    headers["Authorization"] = f"Bearer {github_token}"
                
                # Query GitHub API for tags
                url = f"https://api.github.com/repos/{remote_index.github_owner}/{remote_index.github_repo}/tags"
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                
                tags_data = response.json()
                tags = [tag["name"] for tag in tags_data]
                
                return tags if tags else ["latest"]
                
        except Exception as e:
            logger.error(f"Error fetching tags for {namespace}: {str(e)}")
            return ["latest"]
    
    def get_supported_providers(self) -> List[str]:
        """Get supported Terraform providers for source code analysis."""
        return self.supported_providers.copy()
    
    async def query_golang_source_code(
        self,
        namespace: str,
        symbol: str,
        name: str,
        receiver: Optional[str] = None,
        tag: Optional[str] = None
    ) -> str:
        """
        Query golang source code for a specific symbol.
        
        Args:
            namespace: The golang namespace/package
            symbol: The symbol type (func, method, type, var)
            name: The name of the symbol
            receiver: The receiver type (for methods)
            tag: Version tag
            
        Returns:
            Source code as string
        """
        try:
            # Validate inputs
            if symbol not in ["func", "method", "type", "var"]:
                raise ValueError(f"Invalid symbol type: {symbol}. Must be one of: func, method, type, var")
            
            if symbol == "method" and not receiver:
                raise ValueError("Receiver is required for method symbols")
            
            # Find matching namespace by prefix
            remote_key = None
            for ns in self.remote_index_map.keys():
                if namespace.startswith(ns):
                    remote_key = ns
                    break
            
            if not remote_key:
                return f"Error: Namespace '{namespace}' is not supported. Supported namespaces: {list(self.remote_index_map.keys())}"
            
            # Get real source code from GitHub
            source_code = await self._fetch_golang_source_code(namespace, symbol, name, receiver, tag, remote_key)
            return source_code
            
        except Exception as e:
            logger.error(f"Error querying golang source code: {str(e)}")
            return f"Error: Failed to query golang source code: {str(e)}"
    
    async def query_terraform_source_code(
        self,
        block_type: str,
        terraform_type: str,
        entrypoint_name: str,
        tag: Optional[str] = None
    ) -> str:
        """
        Query Terraform provider source code for a specific block.
        
        Args:
            block_type: The terraform block type (resource, data, ephemeral)
            terraform_type: The terraform type (e.g., azurerm_resource_group)
            entrypoint_name: The function/method name
            tag: Version tag
            
        Returns:
            Source code as string
        """
        try:
            # Validate inputs
            if block_type not in ["resource", "data", "ephemeral"]:
                raise ValueError(f"Invalid block type: {block_type}. Must be one of: resource, data, ephemeral")
            
            # Validate entrypoint names based on block type
            valid_entrypoints = {
                "resource": ["create", "read", "update", "delete", "schema", "attribute"],
                "data": ["read", "schema", "attribute"],
                "ephemeral": ["open", "close", "renew", "schema"]
            }
            
            if entrypoint_name not in valid_entrypoints.get(block_type, []):
                raise ValueError(f"Invalid entrypoint '{entrypoint_name}' for block type '{block_type}'. Valid entrypoints: {valid_entrypoints.get(block_type, [])}")
            
            # Extract provider from terraform type
            segments = terraform_type.split("_")
            if len(segments) < 2:
                raise ValueError(f"Invalid terraform type: {terraform_type}, valid terraform type should be like 'azurerm_resource_group'")
            
            provider_type = segments[0]
            
            if provider_type not in self.provider_index_map:
                return f"Error: Provider '{provider_type}' is not supported. Supported providers: {list(self.provider_index_map.keys())}"
            
            # Get real Terraform source code from GitHub
            source_code = await self._fetch_terraform_source_code(block_type, terraform_type, entrypoint_name, tag)
            return source_code
            
        except Exception as e:
            logger.error(f"Error querying terraform source code: {str(e)}")
            return f"Error: Failed to query terraform source code: {str(e)}"
    
    async def _fetch_golang_source_code(
        self,
        namespace: str,
        symbol: str,
        name: str,
        receiver: Optional[str],
        tag: Optional[str],
        remote_key: str
    ) -> str:
        """Fetch real Go source code from GitHub using the index repository."""
        try:
            remote_index = self.remote_index_map[remote_key]
            
            # Trim namespace prefix to get relative path
            namespace_relative = namespace.replace(remote_index.package_path, "").lstrip("/")
            
            # Build path following terraform-mcp-eva pattern
            if symbol == "method" and receiver:
                path = f"index{namespace_relative}/{symbol}.{receiver}.{name}.goindex"
            else:
                path = f"index{namespace_relative}/{symbol}.{name}.goindex"
            
            # Fetch content from GitHub
            source_code = await self._read_github_content(
                remote_index.github_owner,
                remote_index.github_repo,
                path,
                tag
            )
            
            return source_code
            
        except Exception as e:
            logger.error(f"Error fetching golang source code: {str(e)}")
            if "404" in str(e):
                return f"Source code not found (404): {symbol} {name} in {namespace}"
            return f"Error: Failed to fetch golang source code: {str(e)}"
    
    async def _fetch_terraform_source_code(
        self,
        block_type: str,
        terraform_type: str,
        entrypoint_name: str,
        tag: Optional[str]
    ) -> str:
        """Fetch real Terraform source code from GitHub using the index repository."""
        try:
            # Extract provider type and get index key
            provider_type = terraform_type.split("_")[0]
            index_key = self.provider_index_map[provider_type]
            remote_index = self.remote_index_map[index_key]
            
            # Build path for terraform block index following terraform-mcp-eva pattern
            if block_type != "ephemeral":
                block_type_plural = block_type + "s"
            else:
                block_type_plural = block_type
            
            index_path = f"index/{block_type_plural}/{terraform_type}.json"
            
            # First, fetch the index to get the entrypoint path
            index_content = await self._read_github_content(
                remote_index.github_owner,
                remote_index.github_repo,
                index_path,
                tag
            )
            
            # Parse the index JSON
            index_data = json.loads(index_content)
            entrypoint_key = f"{entrypoint_name}_index"
            
            if entrypoint_key not in index_data:
                return f"Error: Entrypoint '{entrypoint_name}' not found for {terraform_type}"
            
            entrypoint_path = index_data[entrypoint_key] 
            namespace_path = index_data.get("namespace", "")
            
            # Trim namespace prefix to get relative path
            namespace_relative = namespace_path.replace(remote_index.package_path, "").lstrip("/")
            
            # Build final source code path
            source_path = f"index{namespace_relative}/{entrypoint_path}"
            
            # Fetch the actual source code
            source_code = await self._read_github_content(
                remote_index.github_owner,
                remote_index.github_repo,
                source_path,
                ""  # Use empty tag for source code fetch as per terraform-mcp-eva
            )
            
            return source_code
            
        except Exception as e:
            logger.error(f"Error fetching terraform source code: {str(e)}")
            if "404" in str(e):
                return f"Source code not found (404): {block_type} {terraform_type}.{entrypoint_name}"
            return f"Error: Failed to fetch terraform source code: {str(e)}"
    
    async def _read_github_content(
        self,
        owner: str,
        repo: str,
        path: str,
        tag: Optional[str]
    ) -> str:
        """Read content from GitHub repository using the GitHub API."""
        github_token = os.getenv("GITHUB_TOKEN")
        
        try:
            async with httpx.AsyncClient() as client:
                # Set up GitHub token if available
                headers = {"Accept": "application/vnd.github.v3+json"}
                if github_token:
                    headers["Authorization"] = f"Bearer {github_token}"
                
                # Build GitHub API URL
                url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
                params = {}
                if tag:
                    params["ref"] = tag
                
                response = await client.get(url, headers=headers, params=params)
                
                if response.status_code == 404:
                    raise Exception("source code not found (404)")
                
                if response.status_code == 401:
                    if not github_token:
                        raise Exception(f"GitHub API access denied. The repository {owner}/{repo} requires authentication. Please set GITHUB_TOKEN environment variable with a valid GitHub personal access token.")
                    else:
                        raise Exception(f"GitHub API authentication failed. Please check your GITHUB_TOKEN environment variable.")
                
                response.raise_for_status()
                
                content_data = response.json()
                
                # Decode base64 content
                if content_data.get("encoding") == "base64":
                    content = base64.b64decode(content_data["content"]).decode("utf-8")
                else:
                    content = content_data.get("content", "")
                
                return content
                
        except Exception as e:
            logger.error(f"Error reading GitHub content: {str(e)}")
            raise


# Global instance
_golang_source_provider = None

def get_golang_source_provider() -> GolangSourceProvider:
    """Get the global GolangSourceProvider instance."""
    global _golang_source_provider
    if _golang_source_provider is None:
        _golang_source_provider = GolangSourceProvider()
    return _golang_source_provider