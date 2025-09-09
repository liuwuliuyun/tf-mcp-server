"""
AzAPI Schema Generator

This module downloads the latest AzAPI provider source code from GitHub,
parses the bicep types, and generates comprehensive schema documentation
with examples and parent information.
"""

import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional
import asyncio

from .config import get_data_dir


logger = logging.getLogger(__name__)


class GitHubLoader:
    """Download and extract GitHub repositories."""
    
    def __init__(self, owner: str, repo: str, tag: str = "latest"):
        self.owner = owner
        self.repo = repo
        self.tag = tag
        self.download_dir = Path(tempfile.gettempdir()) / "azapi_downloads"
        try:
            self.download_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"Failed to create download directory {self.download_dir}: {e}")
            raise
    async def download_latest_release(self) -> Path:
        """Download and extract the latest release."""
        import tarfile
        from httpx import AsyncClient
        
        # Get release info
        api_url = f"https://api.github.com/repos/{self.owner}/{self.repo}/releases/{self.tag}"
        
        async with AsyncClient(timeout=60.0, follow_redirects=True) as client:
            response = await client.get(api_url)
            response.raise_for_status()
            release_info = response.json()
                
            tarball_url = release_info["tarball_url"]
            tarball_name = f"{release_info['name']}.tar.gz"
            dest_path = self.download_dir / tarball_name
            
            # Download if not exists
            if not dest_path.exists():
                logger.info(f"Downloading {tarball_name} from {tarball_url}")
                download_response = await client.get(tarball_url)
                download_response.raise_for_status()
                with open(dest_path, 'wb') as f:
                    f.write(download_response.content)
                logger.info(f"Downloaded {dest_path}")
            
            # Extract
            extract_dir = self.download_dir / f"extracted_{release_info['name']}"
            if not extract_dir.exists():
                logger.info(f"Extracting {dest_path}")
                with tarfile.open(dest_path, "r:gz") as tar:
                    tar.extractall(path=self.download_dir)
                    # Find the extracted directory (first member's top-level directory)
                    first_member = tar.getmembers()[0]
                    extracted_name = first_member.path.split('/')[0]
                    actual_extract_dir = self.download_dir / extracted_name
                    if actual_extract_dir != extract_dir:
                        actual_extract_dir.rename(extract_dir)
                logger.info(f"Extracted to {extract_dir}")
            
            return extract_dir


class ResourceSchema:
    """Represents an AzAPI resource schema."""
    
    def __init__(self, name: str, scope: str, properties: Dict[str, Any]):
        self.name = name
        self.scope = scope
        self.properties = properties
        
    @property
    def resource_type(self) -> str:
        return self.name.split("@")[0]
        
    @property
    def api_version(self) -> str:
        return self.name.split("@")[1] if "@" in self.name else ""
        
    def parent_id(self) -> str:
        """Get the parent resource type."""
        parts = self.resource_type.split("/")
        if len(parts) > 2:
            return "/".join(parts[:-1])
        
        # Default to resource group for top-level resources
        if self.scope in ["ResourceGroup", "Subscription"]:
            return "Microsoft.Resources/resourceGroups"
        return ""
        
    def as_documentation(self) -> str:
        """Generate HCL documentation format."""
        label = self.resource_type.split("/")[-1].removesuffix("s")
        doc = f"# Resource Type: {self.name}\n"
        doc += f"API Version: {self.api_version}\n"
        doc += f"Parent resource type: {self.parent_id()}\n"
        doc += "A json-like Resource Schema reference:\n\n"
        
        # Generate HCL format
        doc += f'```hcl\nresource "azapi_resource" "{label}" {{\n'
        doc += self._format_properties_as_hcl(self.properties, indent=2)
        doc += "}\n```\n"
        
        return doc
        
    def _format_properties_as_hcl(self, data: Any, indent: int = 0) -> str:
        """Format properties as HCL using the original key ordering logic."""
        if isinstance(data, dict):
            lines = []
            
            # Sort keys using the original key_fn logic
            def key_fn(k: str) -> tuple:
                if k.startswith("__"):
                    return (0, k)
                if k in ["name", "type", "parent_id", "location", "sku"]:
                    return (30, k)
                if k in ["identity"]:
                    return (50, k)
                if k == "tags":
                    return (9999, k)
                return (100, k)
            
            keys = sorted(data.keys(), key=key_fn)
            
            for key in keys:
                if key.startswith("__"):
                    continue
                value = data[key]
                formatted_value = self._format_properties_as_hcl(value, indent + 2)
                lines.append(" " * indent + f"{key} = {formatted_value}")
                
            return "{\n" + "\n".join(lines) + "\n" + " " * (indent - 2) + "}"
        elif isinstance(data, str):
            return f'"{data}"'
        elif isinstance(data, bool):
            return str(data).lower()
        elif isinstance(data, (int, float)):
            return str(data)
        elif isinstance(data, list):
            # Format arrays
            if not data:
                return "[]"
            items = [self._format_properties_as_hcl(item, indent) for item in data]
            return "[" + ", ".join(items) + "]"
        else:
            return json.dumps(data)
            
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "scope": self.scope,
            "properties": self.properties,
            "resource_type": self.resource_type,
            "api_version": self.api_version,
            "parent_id": self.parent_id()
        }


class SimpleBicepParser:
    """Enhanced bicep parser for resource schemas based on the original azapi_parser."""
    
    def __init__(self, bicep_dir: Path):
        self.bicep_dir = bicep_dir
        
    def parse_resource_schemas(self) -> Dict[str, ResourceSchema]:
        """Parse all resource schemas from bicep types."""
        schemas = {}
        
        # Walk through all JSON files in the bicep directory
        for json_file in self.bicep_dir.rglob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    types_data = json.load(f)
                    
                if not isinstance(types_data, list):
                    continue
                    
                # Process this types file
                parser = BicepTypesParser(types_data)
                resource_types = parser.get_resource_types()
                
                # Parse each resource type and keep only the latest API version
                rt_versions = {}
                for rt in resource_types:
                    resource_type = rt.resource_type.lower()
                    if resource_type not in rt_versions or rt.api_version > rt_versions[resource_type].api_version:
                        rt_versions[resource_type] = rt
                        
                # Parse the latest versions
                for rt in rt_versions.values():
                    try:
                        schema = parser.parse_resource_type(rt.index)
                        if schema:
                            schemas[schema.resource_type] = schema
                    except Exception as e:
                        logger.warning(f"Failed to parse resource type {rt.name}: {e}")
                        continue
                            
            except Exception as e:
                logger.warning(f"Failed to parse {json_file}: {e}")
                continue
                
        logger.info(f"Parsed {len(schemas)} resource schemas")
        return schemas


class BicepTypesParser:
    """Parser for bicep types data."""
    
    def __init__(self, types_data: list):
        self.types = types_data
        self.parsed = {}
        self.parsing_stack = []
        
    def get_resource_types(self) -> list:
        """Get all resource types from the types data."""
        resource_types = []
        for idx, data in enumerate(self.types):
            if isinstance(data, dict) and data.get("$type") == "ResourceType":
                resource_types.append(BicepResourceType(idx, data, self))
        return resource_types
        
    def parse_resource_type(self, index: int) -> Optional[ResourceSchema]:
        """Parse a resource type at the given index."""
        try:
            data = self.types[index]
            name = data.get("name", "")
            scope_type = data.get("scopeType", 0)
            
            # Map scope type to string
            scope_map = {
                1: "Tenant",
                2: "ManagementGroup", 
                4: "Subscription",
                8: "ResourceGroup",
                16: "Extension"
            }
            scope = scope_map.get(scope_type, "Unknown")
            
            # Parse body properties
            body_ref = data.get("body", {}).get("$ref")
            properties = {}
            
            if body_ref:
                body_index = int(body_ref.replace("#/", ""))
                properties = self._parse_object_properties(body_index)
                    
            # Create schema structure matching the original format
            parent_id_doc = self._get_parent_id_doc(name, scope_type)
            
            schema_properties = {
                "type": name,
                "parent_id": parent_id_doc,
                "body": properties
            }
            
            # Add common properties
            if scope_type & 8:  # ResourceGroup scope
                schema_properties["location"] = "(Required) String Type. The geo-location where the resource lives"
                
            return ResourceSchema(name, scope, schema_properties)
            
        except Exception as e:
            logger.warning(f"Failed to parse resource type at index {index}: {e}")
            return None
            
    def _parse_object_properties(self, index: int) -> Dict[str, Any]:
        """Parse object properties."""
        if index < 0 or index >= len(self.types) or index in self.parsing_stack:
            return {}
            
        self.parsing_stack.append(index)
        
        try:
            data = self.types[index]
            properties = {}
            
            if isinstance(data, dict) and "properties" in data:
                for prop_name, prop_data in data["properties"].items():
                    if isinstance(prop_data, dict):
                        prop_value = self._parse_property(prop_name, prop_data)
                        if prop_value:
                            properties[prop_name] = prop_value
                            
            return properties
            
        finally:
            self.parsing_stack.pop()
            
    def _parse_property(self, name: str, prop_data: Dict) -> Optional[str]:
        """Parse a single property."""
        try:
            description = prop_data.get("description", "")
            flags = prop_data.get("flags", 0)
            
            # Check if readonly (skip readonly properties)
            if flags & 2:  # readOnly flag
                return None
                
            # Determine if required
            required = "(Required)" if flags & 1 else "(Optional)"
            
            # Simple type description
            prop_type = prop_data.get("type", {})
            type_desc = "Property"
            
            if isinstance(prop_type, dict):
                ref = prop_type.get("$ref", "")
                if ref:
                    ref_index = int(ref.replace("#/", ""))
                    if ref_index < len(self.types):
                        ref_data = self.types[ref_index]
                        ref_type = ref_data.get("$type", "")
                        
                        if ref_type == "StringType":
                            type_desc = "String Type"
                        elif ref_type == "IntegerType":
                            type_desc = "Integer Type"
                        elif ref_type == "BooleanType":
                            type_desc = "Boolean"
                        elif ref_type == "ArrayType":
                            type_desc = "Array Type"
                        elif ref_type == "ObjectType":
                            type_desc = "Object Type"
                        elif ref_type == "UnionType":
                            type_desc = "Union Type"
                        else:
                            type_desc = "Complex Type"
                            
            return f"{required} {type_desc}. {description}".strip()
            
        except Exception:
            return f"(Optional) Property. {prop_data.get('description', '')}"
            
    def _get_parent_id_doc(self, resource_name: str, scope_type: int) -> str:
        """Generate parent ID documentation."""
        parts = resource_name.split("@")[0].split("/")
        
        if len(parts) > 2:
            parent_type = "/".join(parts[:-1])
            parent_name = parts[-2].lower().removesuffix("s") + "Name"
            return f"Reference to the `id` property of resource of type: `{parent_type}`, or a string in the format like: /subscriptions/{{subscriptionId}}/resourceGroups/{{resourceGroupName}}/providers/{parent_type}"
        
        # Handle scope types
        if scope_type & 1:  # Tenant
            return "A tenant id in format /tenants/{tenantId}"
        elif scope_type & 2:  # ManagementGroup
            return "A management group id in format /providers/Microsoft.Management/managementGroups/{managementGroupId}"
        elif scope_type & 4:  # Subscription
            return "A subscription id in format /subscriptions/{subscriptionId}"
        elif scope_type & 8:  # ResourceGroup
            return "Reference to the `id` property of a `Microsoft.Resources/resourceGroups`, or a string value in format /subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}"
        elif scope_type & 16:  # Extension
            return "A resource id reference to a extension."
        else:
            return "Unknown scope"


class BicepResourceType:
    """Represents a bicep resource type."""
    
    def __init__(self, index: int, data: Dict, parser: BicepTypesParser):
        self.index = index
        self.data = data
        self.parser = parser
        self.name = data.get("name", "")
        
    @property
    def resource_type(self) -> str:
        return self.name.split("@")[0]
        
    @property
    def api_version(self) -> str:
        return self.name.split("@")[1] if "@" in self.name else ""


class AzAPISchemaGenerator:
    """Main class for generating AzAPI schemas."""
    
    def __init__(self):
        self.data_dir = get_data_dir()
        self.current_version = None
        
    def _get_schema_file(self, version: str) -> Path:
        """Get the schema file path for a specific version."""
        return self.data_dir / f"azapi_schemas_{version}.json"
    
    def _get_latest_local_version(self) -> Optional[str]:
        """Find the latest version from local schema files."""
        import re
        
        if not self.data_dir.exists():
            return None
            
        version_pattern = re.compile(r'azapi_schemas_v(\d+\.\d+\.\d+)\.json')
        versions = []
        
        for file in self.data_dir.glob("azapi_schemas_v*.json"):
            match = version_pattern.match(file.name)
            if match:
                versions.append(match.group(1))
        
        if not versions:
            return None
            
        # Sort versions semantically
        def version_key(v):
            return tuple(map(int, v.split('.')))
        
        return sorted(versions, key=version_key, reverse=True)[0]
    
    async def _check_latest_github_version(self) -> str:
        """Check the latest version available on GitHub."""
        from httpx import AsyncClient
        
        api_url = "https://api.github.com/repos/Azure/terraform-provider-azapi/releases/latest"
        
        async with AsyncClient(timeout=60.0, follow_redirects=True) as client:
            response = await client.get(api_url)
            response.raise_for_status()
            release_info = response.json()
            return release_info["name"]  # This will be something like "v2.6.1"
            
    async def generate_schemas(self, tag: str = "latest") -> Dict[str, str]:
        """Generate AzAPI schemas from GitHub repository."""
        logger.info(f"Generating AzAPI schemas for tag: {tag}")
        
        try:
            # Download AzAPI provider repository
            loader = GitHubLoader("Azure", "terraform-provider-azapi", tag)
            repo_dir = await loader.download_latest_release()
            
            # Get the actual version from the release info
            if tag == "latest":
                self.current_version = await self._check_latest_github_version()
            else:
                self.current_version = tag
            
            # Find bicep types directory
            bicep_dir = repo_dir / "internal" / "azure" / "generated"
            if not bicep_dir.exists():
                raise ValueError(f"Bicep directory not found: {bicep_dir}")
                
            # Parse schemas
            parser = SimpleBicepParser(bicep_dir)
            schemas = parser.parse_resource_schemas()
            
            # Convert to documentation format
            schema_docs = {}
            for resource_type, schema in schemas.items():
                schema_docs[resource_type] = schema.as_documentation()
                
            # Save to file with version
            await self._save_schemas(schema_docs)
            
            logger.info(f"Generated {len(schema_docs)} AzAPI schemas")
            return schema_docs
            
        except Exception as e:
            logger.error(f"Failed to generate AzAPI schemas: {e}")
            raise
            
    async def _save_schemas(self, schemas: Dict[str, str]) -> None:
        """Save schemas to JSON file with version."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        if not self.current_version:
            raise ValueError("No version set - call generate_schemas first")
            
        schema_file = self._get_schema_file(self.current_version)
        
        with open(schema_file, 'w', encoding='utf-8') as f:
            json.dump(schemas, f, indent=2, ensure_ascii=False)
            
        logger.info(f"Saved schemas to {schema_file}")
        
    async def load_or_generate_schemas(self, force_regenerate: bool = False) -> Dict[str, str]:
        """Load existing schemas or generate new ones based on version checking."""
        
        # Check latest GitHub version
        latest_github_version = await self._check_latest_github_version()
        latest_local_version = self._get_latest_local_version()
        
        # If we have a local version and it matches the latest GitHub version, load it
        if (not force_regenerate and 
            latest_local_version and 
            latest_local_version == latest_github_version.lstrip('v')):
            
            schema_file = self._get_schema_file(f"v{latest_local_version}")
            try:
                with open(schema_file, 'r', encoding='utf-8') as f:
                    schemas = json.load(f)
                logger.info(f"Loaded {len(schemas)} existing AzAPI schemas from {schema_file}")
                self.current_version = f"v{latest_local_version}"
                return schemas
            except Exception as e:
                logger.warning(f"Failed to load existing schemas: {e}")
                
        # Generate new schemas (either forced or new version available)
        if latest_local_version != latest_github_version.lstrip('v'):
            logger.info(f"New version available: {latest_github_version} (local: {latest_local_version or 'none'})")
            
        return await self.generate_schemas("latest")
    
    def get_latest_schema_file(self) -> Optional[Path]:
        """Get the path to the latest versioned schema file."""
        latest_version = self._get_latest_local_version()
        if latest_version:
            return self._get_schema_file(f"v{latest_version}")
        return None


# Main functions for integration
async def initialize_azapi_schemas(force_regenerate: bool = False) -> Dict[str, str]:
    """Initialize AzAPI schemas on server startup."""
    generator = AzAPISchemaGenerator()
    return await generator.load_or_generate_schemas(force_regenerate)


def get_azapi_schema(resource_type: str, schemas: Dict[str, str]) -> str:
    """Get schema for a specific resource type."""
    # Direct match
    if resource_type in schemas:
        return schemas[resource_type]
        
    # Case-insensitive match
    resource_type_lower = resource_type.lower()
    for key, value in schemas.items():
        if key.lower() == resource_type_lower:
            return value
            
    return ""


def get_azapi_parent(resource_type: str) -> str:
    """Get parent resource type for a given resource type."""
    parts = resource_type.split("/")
    if len(parts) > 2:
        return "/".join(parts[:-1])
    return "Microsoft.Resources/resourceGroups"  # Default parent


if __name__ == "__main__":
    # For testing
    import asyncio
    
    async def test():
        generator = AzAPISchemaGenerator()
        schemas = await generator.generate_schemas()
        print(f"Generated {len(schemas)} schemas")
        
    asyncio.run(test())
