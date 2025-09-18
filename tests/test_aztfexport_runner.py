"""
Tests for Azure Export for Terraform (aztfexport) integration.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path
import tempfile
import json

from tf_mcp_server.tools.aztfexport_runner import (
    AztfexportRunner, 
    AztfexportProvider, 
    get_aztfexport_runner
)


class TestAztfexportRunner:
    """Test cases for AztfexportRunner class."""
    
    @pytest.fixture
    def runner(self):
        """Create a runner instance for testing."""
        with patch('tf_mcp_server.tools.aztfexport_runner.shutil.which') as mock_which:
            # Mock that both aztfexport and terraform are available
            def which_side_effect(command):
                if command in ['aztfexport', 'terraform']:
                    return f'/usr/bin/{command}'
                return None
            mock_which.side_effect = which_side_effect
            
            return AztfexportRunner()
    
    def test_initialization_success(self, runner):
        """Test successful initialization when dependencies are available."""
        assert runner is not None
    
    def test_initialization_missing_aztfexport(self):
        """Test initialization failure when aztfexport is missing."""
        with patch('tf_mcp_server.tools.aztfexport_runner.shutil.which') as mock_which:
            mock_which.return_value = None
            
            with pytest.raises(RuntimeError, match="aztfexport is not installed"):
                AztfexportRunner()
    
    def test_initialization_missing_terraform(self):
        """Test initialization failure when terraform is missing."""
        with patch('tf_mcp_server.tools.aztfexport_runner.shutil.which') as mock_which:
            def which_side_effect(command):
                if command == 'aztfexport':
                    return '/usr/bin/aztfexport'
                return None
            mock_which.side_effect = which_side_effect
            
            with pytest.raises(RuntimeError, match="terraform is not installed"):
                AztfexportRunner()
    
    @pytest.mark.asyncio
    async def test_run_command_success(self, runner):
        """Test successful command execution."""
        with patch('asyncio.create_subprocess_exec') as mock_exec:
            # Mock successful process
            mock_process = Mock()
            mock_process.communicate = AsyncMock(return_value=(b'success output', b''))
            mock_process.returncode = 0
            mock_exec.return_value = mock_process
            
            result = await runner._run_command(['echo', 'test'])
            
            assert result['exit_code'] == 0
            assert result['stdout'] == 'success output'
            assert result['stderr'] == ''
            assert result['command'] == 'echo test'
    
    @pytest.mark.asyncio
    async def test_run_command_failure(self, runner):
        """Test command execution failure."""
        with patch('asyncio.create_subprocess_exec') as mock_exec:
            # Mock failed process
            mock_process = Mock()
            mock_process.communicate = AsyncMock(return_value=(b'', b'error output'))
            mock_process.returncode = 1
            mock_exec.return_value = mock_process
            
            result = await runner._run_command(['false'])
            
            assert result['exit_code'] == 1
            assert result['stdout'] == ''
            assert result['stderr'] == 'error output'
    
    @pytest.mark.asyncio
    async def test_run_command_exception(self, runner):
        """Test command execution with exception."""
        with patch('asyncio.create_subprocess_exec') as mock_exec:
            mock_exec.side_effect = Exception('Process creation failed')
            
            result = await runner._run_command(['nonexistent'])
            
            assert result['exit_code'] == -1
            assert 'Process creation failed' in result['stderr']
    
    @pytest.mark.asyncio
    async def test_check_installation_success(self, runner):
        """Test successful installation check."""
        with patch.object(runner, '_run_command') as mock_run:
            mock_run.side_effect = [
                {
                    'exit_code': 0,
                    'stdout': 'aztfexport version 0.18.0',
                    'stderr': ''
                },
                {
                    'exit_code': 0,
                    'stdout': 'Terraform v1.5.0',
                    'stderr': ''
                }
            ]
            
            result = await runner.check_installation()
            
            assert result['installed'] is True
            assert 'aztfexport version 0.18.0' in result['aztfexport_version']
            assert 'Terraform v1.5.0' in result['terraform_version']
            assert result['status'] == 'Ready to use'
    
    @pytest.mark.asyncio
    async def test_check_installation_failure(self, runner):
        """Test installation check failure."""
        with patch.object(runner, '_run_command') as mock_run:
            mock_run.return_value = {
                'exit_code': 1,
                'stdout': '',
                'stderr': 'command not found'
            }
            
            result = await runner.check_installation()
            
            assert result['installed'] is False
            assert 'command not found' in result['error']
            assert result['status'] == 'Installation check failed'
    
    @pytest.mark.asyncio
    async def test_export_resource_success(self, runner):
        """Test successful resource export."""
        resource_id = "/subscriptions/test/resourceGroups/test-rg/providers/Microsoft.Storage/storageAccounts/test"
        
        with patch.object(runner, '_run_command') as mock_run, \
             patch.object(runner, '_read_generated_files') as mock_read:
            
            mock_run.return_value = {
                'exit_code': 0,
                'stdout': 'Export completed successfully',
                'stderr': '',
                'command': 'aztfexport resource ...'
            }
            
            mock_read.return_value = {
                'main.tf': 'resource "azurerm_storage_account" "test" {}',
                'terraform.tfstate': '{"version": 4}'
            }
            
            result = await runner.export_resource(resource_id)
            
            assert result['success'] is True
            assert result['exit_code'] == 0
            assert 'main.tf' in result['generated_files']
            assert 'terraform.tfstate' in result['generated_files']
    
    @pytest.mark.asyncio
    async def test_export_resource_failure(self, runner):
        """Test resource export failure."""
        resource_id = "/subscriptions/test/resourceGroups/test-rg/providers/Microsoft.Storage/storageAccounts/nonexistent"
        
        with patch.object(runner, '_run_command') as mock_run:
            mock_run.return_value = {
                'exit_code': 1,
                'stdout': '',
                'stderr': 'Resource not found',
                'command': 'aztfexport resource ...'
            }
            
            result = await runner.export_resource(resource_id)
            
            assert result['success'] is False
            assert result['exit_code'] == 1
            assert 'Resource not found' in result['stderr']
    
    @pytest.mark.asyncio
    async def test_export_resource_group_success(self, runner):
        """Test successful resource group export."""
        rg_name = "test-resource-group"
        
        with patch.object(runner, '_run_command') as mock_run, \
             patch.object(runner, '_read_generated_files') as mock_read:
            
            mock_run.return_value = {
                'exit_code': 0,
                'stdout': 'Exported 5 resources successfully',
                'stderr': '',
                'command': 'aztfexport resource-group ...'
            }
            
            mock_read.return_value = {
                'main.tf': 'multiple resources...',
                'terraform.tfstate': '{"version": 4, "resources": []}'
            }
            
            result = await runner.export_resource_group(rg_name)
            
            assert result['success'] is True
            assert result['exit_code'] == 0
            assert len(result['generated_files']) == 2
    
    @pytest.mark.asyncio
    async def test_export_query_success(self, runner):
        """Test successful query export."""
        query = "type =~ 'Microsoft.Storage/storageAccounts'"
        
        with patch.object(runner, '_run_command') as mock_run, \
             patch.object(runner, '_read_generated_files') as mock_read:
            
            mock_run.return_value = {
                'exit_code': 0,
                'stdout': 'Query exported 3 resources',
                'stderr': '',
                'command': 'aztfexport query ...'
            }
            
            mock_read.return_value = {
                'main.tf': 'storage accounts...',
                'terraform.tfstate': '{"version": 4}'
            }
            
            result = await runner.export_query(query)
            
            assert result['success'] is True
            assert result['exit_code'] == 0
    
    @pytest.mark.asyncio
    async def test_export_with_azapi_provider(self, runner):
        """Test export using AzAPI provider."""
        resource_id = "/subscriptions/test/resourceGroups/test-rg/providers/Microsoft.Storage/storageAccounts/test"
        
        with patch.object(runner, '_run_command') as mock_run, \
             patch.object(runner, '_read_generated_files') as mock_read:
            
            mock_run.return_value = {
                'exit_code': 0,
                'stdout': 'Export completed with azapi provider',
                'stderr': '',
                'command': 'aztfexport resource --provider-name azapi ...'
            }
            
            mock_read.return_value = {'main.tf': 'azapi resources...'}
            
            result = await runner.export_resource(
                resource_id, 
                provider=AztfexportProvider.AZAPI
            )
            
            assert result['success'] is True
            assert 'azapi' in result['command']
    
    @pytest.mark.asyncio
    async def test_get_config_success(self, runner):
        """Test successful config retrieval."""
        with patch.object(runner, '_run_command') as mock_run:
            mock_run.return_value = {
                'exit_code': 0,
                'stdout': '{"telemetry_enabled": true, "installation_id": "test-id"}',
                'stderr': ''
            }
            
            result = await runner.get_config()
            
            assert result['success'] is True
            assert isinstance(result['config'], dict)
            assert result['config']['telemetry_enabled'] is True
    
    @pytest.mark.asyncio
    async def test_get_config_specific_key(self, runner):
        """Test getting specific config key."""
        with patch.object(runner, '_run_command') as mock_run:
            mock_run.return_value = {
                'exit_code': 0,
                'stdout': 'true',
                'stderr': ''
            }
            
            result = await runner.get_config('telemetry_enabled')
            
            assert result['success'] is True
            assert result['config'] is True  # 'true' gets parsed as JSON boolean
    
    @pytest.mark.asyncio
    async def test_set_config_success(self, runner):
        """Test successful config setting."""
        with patch.object(runner, '_run_command') as mock_run:
            mock_run.return_value = {
                'exit_code': 0,
                'stdout': 'Configuration updated successfully',
                'stderr': ''
            }
            
            result = await runner.set_config('telemetry_enabled', 'false')
            
            assert result['success'] is True
    
    @pytest.mark.asyncio
    async def test_read_generated_files(self, runner):
        """Test reading generated files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test files
            (temp_path / 'main.tf').write_text('resource "test" "example" {}')
            (temp_path / 'terraform.tfstate').write_text('{"version": 4}')
            (temp_path / 'README.md').write_text('# Test')  # Should be ignored
            
            files = await runner._read_generated_files(temp_path)
            
            assert 'main.tf' in files
            assert 'terraform.tfstate' in files
            assert 'README.md' not in files  # Non-terraform files should be excluded
            assert files['main.tf'] == 'resource "test" "example" {}'
    
    def test_get_installation_help(self, runner):
        """Test installation help information."""
        help_info = runner._get_installation_help()
        
        assert 'windows' in help_info
        assert 'macos' in help_info
        assert 'linux_apt' in help_info
        assert 'go' in help_info
        assert 'winget install aztfexport' in help_info['windows']


class TestAztfexportRunnerGlobal:
    """Test the global runner instance function."""
    
    def test_get_aztfexport_runner_singleton(self):
        """Test that get_aztfexport_runner returns the same instance."""
        with patch('tf_mcp_server.tools.aztfexport_runner.shutil.which') as mock_which:
            def which_side_effect(command):
                if command in ['aztfexport', 'terraform']:
                    return f'/usr/bin/{command}'
                return None
            mock_which.side_effect = which_side_effect
            
            runner1 = get_aztfexport_runner()
            runner2 = get_aztfexport_runner()
            
            assert runner1 is runner2


@pytest.mark.integration
class TestAztfexportIntegration:
    """Integration tests that require actual aztfexport installation."""
    
    @pytest.mark.asyncio
    async def test_real_installation_check(self):
        """Test actual installation check (requires aztfexport to be installed)."""
        try:
            runner = get_aztfexport_runner()
            result = await runner.check_installation()
            
            # If aztfexport is installed, verify the result structure
            if result.get('installed'):
                assert 'aztfexport_version' in result
                assert 'terraform_version' in result
                assert result['status'] == 'Ready to use'
            else:
                # If not installed, should have error information
                assert 'error' in result or 'installation_help' in result
                
        except RuntimeError:
            # Expected if aztfexport is not installed
            pytest.skip("aztfexport not installed - skipping integration test")