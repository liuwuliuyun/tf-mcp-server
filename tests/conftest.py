"""
Test configuration and fixtures.
"""

import pytest
import asyncio
from pathlib import Path
import sys

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.config import Config


@pytest.fixture
def test_config():
    """Create a test configuration."""
    return Config(
        server=Config.ServerConfig(
            host="localhost",
            port=6802,  # Different port for testing
            debug=True
        )
    )


@pytest.fixture
def sample_hcl():
    """Sample HCL content for testing."""
    return '''
resource "azurerm_storage_account" "example" {
  name                     = "examplestorageaccount"
  resource_group_name      = azurerm_resource_group.example.name
  location                 = azurerm_resource_group.example.location
  account_tier             = "Standard"
  account_replication_type = "LRS"

  tags = {
    Environment = "Test"
  }
}
'''


@pytest.fixture
def invalid_hcl():
    """Invalid HCL content for testing."""
    return '''
resource "azurerm_storage_account" "example" {
  name = "invalid-name"
  # Missing required attributes
  invalid_attribute = true
'''


@pytest.fixture
async def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
