"""
Golang Source Code Provider for analyzing Go source code in Terraform providers.
"""

import asyncio
import json
import logging
import os
import httpx
import base64
import hashlib
from pathlib import Path
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
        
        # Initialize cache directory
        self.cache_dir = self._get_cache_dir()
        self._ensure_cache_dir()
    
    def get_supported_namespaces(self) -> List[str]:
        """Get all supported golang namespaces."""
        return list(self.remote_index_map.keys())
    
    async def get_supported_tags(self, namespace: str) -> List[str]:
        """Get supported tags for a specific namespace by querying GitHub API."""
        if namespace not in self.remote_index_map:
            raise ValueError(f"Unsupported namespace: {namespace}")
        
        remote_index = self.remote_index_map[namespace]
        
        # Check cache first
        tags_cache_path = self._get_tags_cache_path(namespace)
        cached_tags = self._read_tags_from_cache(tags_cache_path)
        
        if cached_tags:
            logger.debug(f"Using cached tags for {namespace}")
            return cached_tags
        
        try:
            async with httpx.AsyncClient() as client:
                # Query GitHub API for tags
                url = f"https://api.github.com/repos/{remote_index.github_owner}/{remote_index.github_repo}/tags"
                
                # First try: attempt download without auth header
                headers = {"Accept": "application/vnd.github.v3+json"}
                response = await client.get(url, headers=headers)
                
                # If first attempt fails and we have a token, try with auth
                github_token = os.getenv("GITHUB_TOKEN")
                if response.status_code in [401, 403] and github_token:
                    logger.info(f"First attempt failed with status {response.status_code}, retrying with authentication")
                    headers["Authorization"] = f"Bearer {github_token}"
                    response = await client.get(url, headers=headers)
                
                response.raise_for_status()
                
                tags_data = response.json()
                tags = [tag["name"] for tag in tags_data]
                
                result_tags = tags if tags else ["latest"]
                
                # Cache the tags
                self._write_tags_to_cache(tags_cache_path, result_tags)
                
                return result_tags
                
        except Exception as e:
            logger.error(f"Error fetching tags for {namespace}: {str(e)}")
            return ["latest"]
    
    def get_supported_providers(self) -> List[str]:
        """Get supported Terraform providers for source code analysis."""
        return self.supported_providers.copy()
    
    def _get_cache_dir(self) -> Path:
        """Get the cache directory path."""
        # Get the path to src/data relative to this file
        current_file = Path(__file__)
        # Navigate to src/data from src/tf_mcp_server/tools/
        data_dir = current_file.parent.parent.parent / "data" / "golang_cache"
        return data_dir
    
    def _ensure_cache_dir(self) -> None:
        """Ensure the cache directory exists."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_cache_key(self, owner: str, repo: str, path: str, tag: Optional[str]) -> str:
        """Generate a cache key for the given parameters."""
        # Create a hash of the parameters for a unique cache key
        cache_input = f"{owner}/{repo}/{path}/{tag or 'latest'}"
        return hashlib.md5(cache_input.encode()).hexdigest()
    
    def _get_cache_path(self, owner: str, repo: str, path: str, tag: Optional[str]) -> Path:
        """Get the cache file path for the given parameters."""
        cache_key = self._get_cache_key(owner, repo, path, tag)
        # Create subdirectories based on owner/repo for better organization
        cache_subdir = self.cache_dir / owner / repo / (tag or "latest")
        cache_subdir.mkdir(parents=True, exist_ok=True)
        return cache_subdir / f"{cache_key}.cache"
    
    def _is_cache_valid(self, cache_path: Path) -> bool:
        """Check if the cache file exists and is valid."""
        return cache_path.exists() and cache_path.is_file()
    
    def _read_from_cache(self, cache_path: Path) -> Optional[str]:
        """Read content from cache file."""
        try:
            if self._is_cache_valid(cache_path):
                with open(cache_path, 'r', encoding='utf-8') as f:
                    return f.read()
        except Exception as e:
            logger.warning(f"Failed to read from cache {cache_path}: {str(e)}")
        return None
    
    def _write_to_cache(self, cache_path: Path, content: str) -> None:
        """Write content to cache file."""
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.debug(f"Cached content to {cache_path}")
        except Exception as e:
            logger.warning(f"Failed to write to cache {cache_path}: {str(e)}")
    
    def _get_tags_cache_path(self, namespace: str) -> Path:
        """Get the cache path for tags of a namespace."""
        remote_index = self.remote_index_map[namespace]
        cache_subdir = self.cache_dir / remote_index.github_owner / remote_index.github_repo
        cache_subdir.mkdir(parents=True, exist_ok=True)
        return cache_subdir / "tags.json"
    
    def _read_tags_from_cache(self, cache_path: Path) -> Optional[List[str]]:
        """Read tags from cache file."""
        try:
            if self._is_cache_valid(cache_path):
                with open(cache_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('tags', [])
        except Exception as e:
            logger.warning(f"Failed to read tags from cache {cache_path}: {str(e)}")
        return None
    
    def _write_tags_to_cache(self, cache_path: Path, tags: List[str]) -> None:
        """Write tags to cache file."""
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump({'tags': tags}, f, indent=2)
            logger.debug(f"Cached tags to {cache_path}")
        except Exception as e:
            logger.warning(f"Failed to write tags to cache {cache_path}: {str(e)}")
    
    def clear_cache(self, owner: Optional[str] = None, repo: Optional[str] = None, tag: Optional[str] = None) -> None:
        """
        Clear cache entries. If no parameters are provided, clears all cache.
        
        Args:
            owner: Clear cache for specific GitHub owner
            repo: Clear cache for specific repository (requires owner)
            tag: Clear cache for specific tag (requires owner and repo)
        """
        try:
            if owner is None:
                # Clear all cache
                if self.cache_dir.exists():
                    import shutil
                    shutil.rmtree(self.cache_dir)
                    self._ensure_cache_dir()
                    logger.info("Cleared all cache")
            elif repo is None:
                # Clear cache for specific owner
                owner_dir = self.cache_dir / owner
                if owner_dir.exists():
                    import shutil
                    shutil.rmtree(owner_dir)
                    logger.info(f"Cleared cache for owner: {owner}")
            elif tag is None:
                # Clear cache for specific repo
                repo_dir = self.cache_dir / owner / repo
                if repo_dir.exists():
                    import shutil
                    shutil.rmtree(repo_dir)
                    logger.info(f"Cleared cache for repo: {owner}/{repo}")
            else:
                # Clear cache for specific tag
                tag_dir = self.cache_dir / owner / repo / tag
                if tag_dir.exists():
                    import shutil
                    shutil.rmtree(tag_dir)
                    logger.info(f"Cleared cache for tag: {owner}/{repo}:{tag}")
        except Exception as e:
            logger.error(f"Failed to clear cache: {str(e)}")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get information about the current cache."""
        try:
            cache_info = {
                "cache_dir": str(self.cache_dir),
                "exists": self.cache_dir.exists(),
                "size_mb": 0,
                "entries": 0,
                "repositories": []
            }
            
            if self.cache_dir.exists():
                # Calculate cache size and count entries
                total_size = 0
                total_entries = 0
                repositories = []
                
                for owner_dir in self.cache_dir.iterdir():
                    if owner_dir.is_dir():
                        for repo_dir in owner_dir.iterdir():
                            if repo_dir.is_dir():
                                repo_info = {
                                    "owner": owner_dir.name,
                                    "repo": repo_dir.name,
                                    "tags": []
                                }
                                
                                for tag_dir in repo_dir.iterdir():
                                    if tag_dir.is_dir():
                                        tag_entries = 0
                                        tag_size = 0
                                        for cache_file in tag_dir.iterdir():
                                            if cache_file.is_file():
                                                file_size = cache_file.stat().st_size
                                                total_size += file_size
                                                tag_size += file_size
                                                total_entries += 1
                                                tag_entries += 1
                                        
                                        repo_info["tags"].append({
                                            "tag": tag_dir.name,
                                            "entries": tag_entries,
                                            "size_mb": round(tag_size / (1024 * 1024), 2)
                                        })
                                
                                repositories.append(repo_info)
                
                cache_info["size_mb"] = round(total_size / (1024 * 1024), 2)
                cache_info["entries"] = total_entries
                cache_info["repositories"] = repositories
            
            return cache_info
        except Exception as e:
            logger.error(f"Failed to get cache info: {str(e)}")
            return {"error": str(e)}
    
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
            
        except ValueError:
            # Re-raise validation errors as-is for proper test handling
            raise
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
            
        except ValueError:
            # Re-raise validation errors as-is for proper test handling
            raise
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
            
            # Build filename
            if symbol == "method" and receiver:
                filename = f"{symbol}.{receiver}.{name}.goindex"
            else:
                filename = f"{symbol}.{name}.goindex"
            
            # Try direct path first
            path_components = ["index"]
            if namespace_relative:
                path_components.append(namespace_relative)
            path_components.append(filename)
            path = "/".join(path_components)
            
            try:
                # Fetch content from GitHub
                source_code = await self._read_github_content(
                    remote_index.github_owner,
                    remote_index.github_repo,
                    path,
                    tag
                )
                return source_code
            except Exception as direct_error:
                if "404" not in str(direct_error):
                    raise direct_error
                
                # If direct path fails with 404, try searching in service subdirectories
                logger.debug(f"Direct path failed: {path}, searching in service subdirectories")
                
                # For azurerm provider, try searching in services subdirectories
                # But only for function names that look like they belong to services
                if ("terraform-provider-azurerm" in remote_index.package_path and 
                    self._should_search_in_services(name, namespace_relative)):
                    return await self._search_in_service_subdirectories(
                        remote_index, namespace_relative, filename, tag, name
                    )
                else:
                    # For other cases, just return the original error
                    raise direct_error
            
        except Exception as e:
            logger.error(f"Error fetching golang source code: {str(e)}")
            if "404" in str(e):
                return f"Source code not found (404): {symbol} {name} in {namespace}"
            return f"Error: Failed to fetch golang source code: {str(e)}"
    
    def _should_search_in_services(self, name: str, namespace_relative: str) -> bool:
        """Determine if we should search in service subdirectories for this function."""
        # Don't search in services for functions that are clearly in other namespaces
        if "clients" in namespace_relative or "utils" in namespace_relative:
            return False
        
        # Search for functions that look like they belong to services
        lower_name = name.lower()
        return (lower_name.startswith("resource") or 
                lower_name.startswith("datasource") or
                lower_name.startswith("data_source"))
    
    async def _search_in_service_subdirectories(
        self,
        remote_index: RemoteIndex,
        namespace_relative: str,
        filename: str,
        tag: Optional[str],
        name: str
    ) -> str:
        """Search for the function in service subdirectories."""
        try:
            # Build base path for services
            base_path = "index"
            if namespace_relative:
                base_path += f"/{namespace_relative}"
            
            # List services directory
            services_path = f"{base_path}/services"
            try:
                services_response = await self._read_github_directory(
                    remote_index.github_owner,
                    remote_index.github_repo,
                    services_path,
                    tag
                )
                
                # Try to infer service name from function name
                service_candidates = []
                
                # Extract service name from function name patterns
                lower_name = name.lower()
                if lower_name.startswith("resource"):
                    # Extract service from resource name (e.g., resourceKustoCluster -> kusto)
                    remaining = lower_name[8:]  # Remove "resource"
                    for service_dir in services_response:
                        service_name = service_dir['name'].lower()
                        if remaining.startswith(service_name):
                            service_candidates.append(service_dir['name'])
                elif lower_name.startswith("datasource"):
                    # Extract service from datasource name (e.g., dataSourceKustoCluster -> kusto)
                    remaining = lower_name[10:]  # Remove "datasource"
                    for service_dir in services_response:
                        service_name = service_dir['name'].lower()
                        if remaining.startswith(service_name):
                            service_candidates.append(service_dir['name'])
                
                # If no candidates found, try all service directories
                if not service_candidates:
                    service_candidates = [item['name'] for item in services_response if item['type'] == 'dir']
                
                # Try each candidate service directory
                for service_dir in service_candidates:
                    try:
                        service_path = f"{services_path}/{service_dir}/{filename}"
                        source_code = await self._read_github_content(
                            remote_index.github_owner,
                            remote_index.github_repo,
                            service_path,
                            tag
                        )
                        logger.info(f"Found function {name} in service directory: {service_dir}")
                        return source_code
                    except Exception as service_error:
                        if "404" not in str(service_error):
                            logger.warning(f"Error checking service {service_dir}: {service_error}")
                        continue
                
                # If not found in any service directory
                raise Exception(f"Function {name} not found in any service subdirectory")
                
            except Exception as services_error:
                if "404" in str(services_error):
                    raise Exception(f"Services directory not found: {services_path}")
                raise services_error
                
        except Exception as e:
            logger.error(f"Error searching in service subdirectories: {str(e)}")
            raise e
    
    async def _read_github_directory(
        self,
        owner: str,
        repo: str,
        path: str,
        tag: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Read directory contents from GitHub repository."""
        github_token = os.getenv("GITHUB_TOKEN")
        
        try:
            async with httpx.AsyncClient() as client:
                # Build GitHub API URL
                url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
                params = {}
                if tag:
                    params["ref"] = tag
                
                # First try: attempt download without auth header
                headers = {"Accept": "application/vnd.github.v3+json"}
                response = await client.get(url, headers=headers, params=params)
                
                # If first attempt fails and we have a token, try with auth
                if response.status_code in [401, 403] and github_token:
                    logger.info(f"First attempt failed with status {response.status_code}, retrying with authentication")
                    headers["Authorization"] = f"Bearer {github_token}"
                    response = await client.get(url, headers=headers, params=params)
                
                if response.status_code == 404:
                    raise Exception(f"directory not found (404): {path}")
                
                if response.status_code == 401:
                    if not github_token:
                        raise Exception(f"GitHub API access denied. The repository {owner}/{repo} requires authentication. Please set GITHUB_TOKEN environment variable with a valid GitHub personal access token.")
                    else:
                        raise Exception(f"GitHub API authentication failed. Please check your GITHUB_TOKEN environment variable.")
                
                response.raise_for_status()
                
                directory_data = response.json()
                return directory_data
                
        except Exception as e:
            logger.error(f"Error reading GitHub directory: {str(e)}")
            raise
    
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
            path_components = ["index"]
            if namespace_relative:
                path_components.append(namespace_relative)

            path_components.append(entrypoint_path)
            source_path = "/".join(path_components)
            
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
        """Read content from GitHub repository using the GitHub API with caching."""
        # Check cache first
        cache_path = self._get_cache_path(owner, repo, path, tag)
        cached_content = self._read_from_cache(cache_path)
        
        if cached_content is not None:
            logger.debug(f"Using cached content for {owner}/{repo}/{path} (tag: {tag or 'latest'})")
            return cached_content
        
        github_token = os.getenv("GITHUB_TOKEN")
        
        try:
            async with httpx.AsyncClient() as client:
                # Build GitHub API URL
                url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
                params = {}
                if tag:
                    params["ref"] = tag
                
                # First try: attempt download without auth header
                headers = {"Accept": "application/vnd.github.v3+json"}
                response = await client.get(url, headers=headers, params=params)
                
                # If first attempt fails and we have a token, try with auth
                if response.status_code in [401, 403] and github_token:
                    logger.info(f"First attempt failed with status {response.status_code}, retrying with authentication")
                    headers["Authorization"] = f"Bearer {github_token}"
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
                
                # Cache the content
                self._write_to_cache(cache_path, content)
                logger.debug(f"Downloaded and cached content for {owner}/{repo}/{path} (tag: {tag or 'latest'})")
                
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