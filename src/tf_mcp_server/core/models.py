"""
Data models for Azure Terraform MCP Server.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class ArgumentDetail(BaseModel):
    """Detailed argument information."""
    name: str = Field(..., description="Argument name")
    description: str = Field(..., description="Argument description")
    required: bool = Field(default=False, description="Whether the argument is required")
    type: str = Field(default="string", description="Argument data type")
    block_arguments: Optional[List['ArgumentDetail']] = Field(default=None, description="Nested block arguments")


class TerraformAzureProviderDocsResult(BaseModel):
    """Result structure for Azure provider documentation search."""
    
    resource_type: str = Field(..., description="The Azure resource type")
    documentation_url: str = Field(..., description="URL to the documentation")
    summary: str = Field(..., description="Summary of the resource")
    arguments: List[ArgumentDetail] = Field(default_factory=list, description="Resource arguments")
    attributes: List[Dict[str, str]] = Field(default_factory=list, description="Resource attributes")
    examples: List[str] = Field(default_factory=list, description="Usage examples")
    notes: List[str] = Field(default_factory=list, description="Important notes and warnings from the documentation")


class TerraformExecutionRequest(BaseModel):
    """Request structure for Terraform command execution."""
    
    command: str = Field(..., description="Terraform command to execute")
    working_directory: str = Field(default=".", description="Working directory for execution")
    environment_variables: Optional[Dict[str, str]] = Field(
        default=None, 
        description="Environment variables for the command"
    )
    azure_subscription_id: Optional[str] = Field(
        default=None, 
        description="Azure subscription ID"
    )
    azure_tenant_id: Optional[str] = Field(
        default=None, 
        description="Azure tenant ID"
    )


class TerraformExecutionResult(BaseModel):
    """Result structure for Terraform command execution."""
    
    command: str = Field(..., description="The executed command")
    exit_code: int = Field(..., description="Command exit code")
    stdout: str = Field(..., description="Standard output")
    stderr: str = Field(..., description="Standard error")
    execution_time_seconds: float = Field(..., description="Execution time in seconds")


class ValidationResult(BaseModel):
    """Result structure for HCL validation."""
    
    is_valid: bool = Field(..., description="Whether the HCL is valid")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    file_path: Optional[str] = Field(default=None, description="Path to the validated file")


class AzureResourceAnalysis(BaseModel):
    """Result structure for Azure resource analysis."""
    
    resource_type: str = Field(..., description="Azure resource type")
    resource_name: str = Field(..., description="Resource name")
    configuration: Dict[str, Any] = Field(default_factory=dict, description="Resource configuration")
    dependencies: List[str] = Field(default_factory=list, description="Resource dependencies")
    security_issues: List[str] = Field(default_factory=list, description="Identified security issues")
    recommendations: List[str] = Field(default_factory=list, description="Improvement recommendations")


# Enable forward references for recursive models
ArgumentDetail.model_rebuild()
