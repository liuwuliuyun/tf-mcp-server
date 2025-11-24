"""Configuration management for Azure Terraform MCP Server."""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from httpx import Client

logger = logging.getLogger(__name__)


class ServerConfig(BaseModel):
    """Server configuration settings."""
    
    github_token: str = Field(default="", description="GitHub token for accessing repositories")
    host: str = Field(default="localhost", description="Server host")
    port: int = Field(default=8000, description="Server port")
    debug: bool = Field(default=False, description="Enable debug mode")


class AzureConfig(BaseModel):
    """Azure-specific configuration settings."""
    
    subscription_id: Optional[str] = Field(default=None, description="Azure subscription ID")
    tenant_id: Optional[str] = Field(default=None, description="Azure tenant ID")
    client_id: Optional[str] = Field(default=None, description="Azure client ID")
    client_secret: Optional[str] = Field(default=None, description="Azure client secret")


class Config(BaseModel):
    """Main configuration class."""
    
    server: ServerConfig = Field(default_factory=ServerConfig)
    azure: AzureConfig = Field(default_factory=AzureConfig)
    
    @classmethod
    def from_env(cls) -> "Config":
        """Create configuration from environment variables."""
        return cls(
            server=ServerConfig(
                github_token=os.getenv("GITHUB_TOKEN", ""),
                host=os.getenv("MCP_SERVER_HOST", "localhost"),
                port=int(os.getenv("MCP_SERVER_PORT", "8000")),
                debug=os.getenv("MCP_DEBUG", "false").lower() in ("true", "1", "yes")
            ),
            azure=AzureConfig(
                subscription_id=os.getenv("ARM_SUBSCRIPTION_ID"),
                tenant_id=os.getenv("ARM_TENANT_ID"),
                client_id=os.getenv("ARM_CLIENT_ID"),
                client_secret=os.getenv("ARM_CLIENT_SECRET")
            ),
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
