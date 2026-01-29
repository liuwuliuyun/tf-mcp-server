"""Configuration management for Azure Terraform MCP Server."""

import os
import json
import uuid
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from httpx import Client

logger = logging.getLogger(__name__)


class TelemetryConfig(BaseModel):
    """Telemetry configuration settings."""
    
    enabled: bool = Field(default=True, description="Enable telemetry collection")
    connection_string: str = Field(default="", description="Application Insights connection string")
    sample_rate: float = Field(default=1.0, description="Telemetry sampling rate (0.0-1.0)")
    user_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Anonymous user ID")
    
    @classmethod
    def from_env(cls) -> "TelemetryConfig":
        """Create telemetry configuration from environment variables."""
        enabled = os.getenv("TELEMETRY_ENABLED", "true").lower() in ("true", "1", "yes")
        ai_key = os.getenv("AI_KEY", "f20a7f04-a605-4057-a76d-57de0a138abb")
        ai_ingest_endpoint = os.getenv("AI_INGEST_ENDPOINT", "https://westeurope-5.in.applicationinsights.azure.com/")
        ai_live_endpoint = os.getenv("AI_LIVE_ENDPOINT", "https://westeurope.livediagnostics.monitor.azure.com/")
        app_id = os.getenv("APP_ID", "e5481343-dfa6-454c-8f50-2eec2d86be0c")
        connection_string = (
            f"InstrumentationKey={ai_key};"
            f"IngestionEndpoint={ai_ingest_endpoint};"
            f"LiveEndpoint={ai_live_endpoint};"
            f"ApplicationId={app_id}"
        )
        connection_string = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING", connection_string)
        sample_rate = float(os.getenv("TELEMETRY_SAMPLE_RATE", "1.0"))
        
        # Load or generate user ID
        user_id = cls._load_or_generate_user_id()
        
        return cls(
            enabled=enabled,
            connection_string=connection_string,
            sample_rate=sample_rate,
            user_id=user_id
        )
    
    @staticmethod
    def _load_or_generate_user_id() -> str:
        """Load existing user ID or generate a new one.
        
        The config file is stored in the workspace root (MCP_WORKSPACE_ROOT) if available,
        which is typically a mounted volume that persists across container restarts.
        Falls back to home directory if workspace root is not available.
        """
        # Prefer workspace root (mounted volume) for persistence across container restarts
        workspace_root = os.getenv("MCP_WORKSPACE_ROOT")
        if workspace_root and Path(workspace_root).exists():
            config_file = Path(workspace_root) / ".tf_mcp_server" / ".telemetry_config.json"
        else:
            config_file = Path.home() / ".tf_mcp_server" / ".telemetry_config.json"
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    data = json.load(f)
                    return data.get("user_id", str(uuid.uuid4()))
            except Exception:
                pass
        
        # Generate new user ID
        user_id = str(uuid.uuid4())
        
        # Save to file
        try:
            config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(config_file, 'w') as f:
                json.dump({
                    "user_id": user_id,
                    "telemetry_enabled": True,
                    "first_seen": os.environ.get("TZ", "UTC")
                }, f, indent=2)
        except Exception:
            pass  # If we can't save, just use the generated ID
        
        return user_id


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
    telemetry: TelemetryConfig = Field(default_factory=TelemetryConfig)
    
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
            telemetry=TelemetryConfig.from_env()
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
