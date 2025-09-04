"""
Configuration management for Azure Terraform MCP Server.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
import asyncio
from pydantic import BaseModel, Field
from httpx import AsyncClient


class ServerConfig(BaseModel):
    """Server configuration settings."""
    
    github_token: str = Field(default="", description="GitHub token for accessing repositories")
    host: str = Field(default="localhost", description="Server host")
    port: int = Field(default=6801, description="Server port")
    debug: bool = Field(default=False, description="Enable debug mode")


class AzureConfig(BaseModel):
    """Azure-specific configuration settings."""
    
    subscription_id: Optional[str] = Field(default=None, description="Azure subscription ID")
    tenant_id: Optional[str] = Field(default=None, description="Azure tenant ID")
    client_id: Optional[str] = Field(default=None, description="Azure client ID")
    client_secret: Optional[str] = Field(default=None, description="Azure client secret")


class TerraformConfig(BaseModel):
    """Terraform-specific configuration settings."""
    
    working_directory: str = Field(default=".", description="Default working directory")
    auto_init: bool = Field(default=True, description="Auto-initialize Terraform")
    timeout: int = Field(default=300, description="Command timeout in seconds")


class Config(BaseModel):
    """Main configuration class."""
    
    server: ServerConfig = Field(default_factory=ServerConfig)
    azure: AzureConfig = Field(default_factory=AzureConfig)
    terraform: TerraformConfig = Field(default_factory=TerraformConfig)
    
    @classmethod
    def from_env(cls) -> "Config":
        """Create configuration from environment variables."""
        return cls(
            server=ServerConfig(
                github_token=os.getenv("GITHUB_TOKEN", ""),
                host=os.getenv("MCP_SERVER_HOST", "localhost"),
                port=int(os.getenv("MCP_SERVER_PORT", "6801")),
                debug=os.getenv("MCP_DEBUG", "false").lower() in ("true", "1", "yes")
            ),
            azure=AzureConfig(
                subscription_id=os.getenv("ARM_SUBSCRIPTION_ID"),
                tenant_id=os.getenv("ARM_TENANT_ID"),
                client_id=os.getenv("ARM_CLIENT_ID"),
                client_secret=os.getenv("ARM_CLIENT_SECRET")
            ),
            terraform=TerraformConfig(
                working_directory=os.getenv("TF_WORKING_DIR", "."),
                auto_init=os.getenv("TF_AUTO_INIT", "true").lower() in ("true", "1", "yes"),
                timeout=int(os.getenv("TF_TIMEOUT", "300"))
            )
        )
    
    @classmethod
    def from_file(cls, file_path: Path) -> "Config":
        """Load configuration from JSON file."""
        with open(file_path, 'r') as f:
            data = json.load(f)
        return cls(**data)
    
    def to_file(self, file_path: Path) -> None:
        """Save configuration to JSON file."""
        with open(file_path, 'w') as f:
            json.dump(self.model_dump(), f, indent=2)


def get_data_dir() -> Path:
    """Get the data directory path."""
    return Path(__file__).parent.parent.parent / "data"


def load_azapi_schema() -> Dict[str, Any]:
    """Load AzAPI schema from data file or download from GitHub if not found."""
    schema_file = get_data_dir() / "azapi_schemas.json"
    
    # First try to load from local file
    if schema_file.exists():
        try:
            with open(schema_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            print(f"Warning: Invalid JSON in {schema_file}: {e}")
        except UnicodeDecodeError as e:
            print(f"Warning: Encoding error in {schema_file}: {e}")
    
    # If local file doesn't exist or is invalid, try to download from GitHub
    try:
        print(f"Local schema file not found at {schema_file}. Downloading from GitHub...")
        schema_data = asyncio.run(_download_azapi_schema())
        
        # Save the downloaded schema to local file for future use
        if schema_data:
            _save_schema_to_file(schema_file, schema_data)
            print(f"Successfully downloaded and saved schema to {schema_file}")
            return schema_data
    except Exception as e:
        print(f"Warning: Failed to download schema from GitHub: {e}")
    
    print("Warning: AzAPI schema not available. AzAPI functionality will be limited.")
    return {}


async def _download_azapi_schema() -> Dict[str, Any]:
    """Download AzAPI schema from GitHub."""
    github_url = "https://raw.githubusercontent.com/liuwuliuyun/azapi_schema/refs/heads/main/azapi_schemas.json"
    
    async with AsyncClient(timeout=30.0) as client:
        response = await client.get(github_url)
        response.raise_for_status()
        return response.json()


def _save_schema_to_file(schema_file: Path, schema_data: Dict[str, Any]) -> None:
    """Save schema data to local file."""
    # Ensure the data directory exists
    schema_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(schema_file, 'w', encoding='utf-8') as f:
        json.dump(schema_data, f, indent=2, ensure_ascii=False)
