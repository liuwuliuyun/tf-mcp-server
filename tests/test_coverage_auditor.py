"""
Tests for Terraform Coverage Auditor.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.tf_mcp_server.tools.coverage_auditor import (
    CoverageAuditor,
    ResourceMatcher,
    get_coverage_auditor
)


class TestResourceMatcher:
    """Test ResourceMatcher functionality."""
    
    def test_extract_resource_name_from_id(self):
        """Test extracting resource name from Azure resource ID."""
        resource_id = "/subscriptions/12345/resourceGroups/test-rg/providers/Microsoft.Storage/storageAccounts/mystorageaccount"
        result = ResourceMatcher.extract_resource_name_from_id(resource_id)
        assert result == "mystorageaccount"
    
    def test_extract_resource_name_empty(self):
        """Test extracting resource name from empty ID."""
        result = ResourceMatcher.extract_resource_name_from_id("")
        assert result == ""
    
    def test_extract_resource_type_from_id(self):
        """Test extracting resource type from Azure resource ID."""
        resource_id = "/subscriptions/12345/resourceGroups/test-rg/providers/Microsoft.Storage/storageAccounts/mystorageaccount"
        result = ResourceMatcher.extract_resource_type_from_id(resource_id)
        assert result == "Microsoft.Storage/storageAccounts"
    
    def test_extract_resource_type_empty(self):
        """Test extracting resource type from empty ID."""
        result = ResourceMatcher.extract_resource_type_from_id("")
        assert result == ""
    
    def test_normalize_resource_name(self):
        """Test normalizing resource names."""
        assert ResourceMatcher.normalize_resource_name("My-Storage_Account.123") == "mystorageaccount123"
        assert ResourceMatcher.normalize_resource_name("TEST-RG-001") == "testrg001"
        assert ResourceMatcher.normalize_resource_name("simple") == "simple"
    
    def test_parse_terraform_address(self):
        """Test parsing Terraform resource addresses."""
        tf_type, tf_name = ResourceMatcher.parse_terraform_address("azurerm_storage_account.my_storage")
        assert tf_type == "azurerm_storage_account"
        assert tf_name == "my_storage"
        
        # Handle names with dots
        tf_type, tf_name = ResourceMatcher.parse_terraform_address("azurerm_storage_account.my.storage.with.dots")
        assert tf_type == "azurerm_storage_account"
        assert tf_name == "my.storage.with.dots"
    
    def test_extract_azure_id_from_state_show(self):
        """Test extracting Azure resource ID from state show output."""
        state_output = '''
# azurerm_storage_account.test:
resource "azurerm_storage_account" "test" {
    id                       = "/subscriptions/12345/resourceGroups/test-rg/providers/Microsoft.Storage/storageAccounts/testaccount"
    name                     = "testaccount"
    resource_group_name      = "test-rg"
}
'''
        result = ResourceMatcher._extract_azure_id_from_state_show(state_output)
        assert result == "/subscriptions/12345/resourceGroups/test-rg/providers/Microsoft.Storage/storageAccounts/testaccount"
    
    @pytest.mark.asyncio
    async def test_get_state_resource_details(self):
        """Test getting resource details from Terraform state."""
        mock_runner = MagicMock()
        mock_runner.execute_terraform_command = AsyncMock()
        
        # Mock state show response
        mock_runner.execute_terraform_command.return_value = {
            'exit_code': 0,
            'stdout': '''
# azurerm_storage_account.test:
resource "azurerm_storage_account" "test" {
    id = "/subscriptions/12345/resourceGroups/test-rg/providers/Microsoft.Storage/storageAccounts/testaccount"
}
'''
        }
        
        result = await ResourceMatcher.get_state_resource_details(
            mock_runner,
            'test-workspace',
            ['azurerm_storage_account.test']
        )
        
        assert 'azurerm_storage_account.test' in result
        assert result['azurerm_storage_account.test']['terraform_type'] == 'azurerm_storage_account'
        assert result['azurerm_storage_account.test']['terraform_name'] == 'test'
        assert '/subscriptions/12345/' in result['azurerm_storage_account.test']['azure_resource_id']
    
    @pytest.mark.asyncio
    async def test_match_resources_by_azure_id(self):
        """Test matching resources using Azure resource ID from state."""
        mock_runner = MagicMock()
        mock_runner.execute_terraform_command = AsyncMock()
        
        azure_id = "/subscriptions/12345/resourceGroups/test-rg/providers/Microsoft.Storage/storageAccounts/mystorageaccount"
        
        # Mock state show to return resource with Azure ID
        mock_runner.execute_terraform_command.return_value = {
            'exit_code': 0,
            'stdout': f'''
# azurerm_storage_account.mystorageaccount:
resource "azurerm_storage_account" "mystorageaccount" {{
    id = "{azure_id}"
}}
'''
        }
        
        azure_resources = [
            {
                'id': azure_id,
                'type': 'Microsoft.Storage/storageAccounts',
                'name': 'mystorageaccount',
                'location': 'eastus'
            }
        ]
        
        terraform_resources = ['azurerm_storage_account.mystorageaccount']
        
        matched, missing, orphaned = await ResourceMatcher.match_resources(
            azure_resources,
            mock_runner,
            'test-workspace',
            terraform_resources
        )
        
        assert len(matched) == 1
        assert len(missing) == 0
        assert len(orphaned) == 0
        
        assert matched[0]['azure_resource_name'] == 'mystorageaccount'
        assert matched[0]['terraform_address'] == 'azurerm_storage_account.mystorageaccount'
        assert matched[0]['match_confidence'] == 'high'
        assert matched[0]['match_method'] == 'azure_id'
    
    @pytest.mark.asyncio
    async def test_match_resources_by_name_fallback(self):
        """Test matching resources using name fallback when Azure ID not in state."""
        mock_runner = MagicMock()
        mock_runner.execute_terraform_command = AsyncMock()
        
        # Mock state show with no valid Azure ID (edge case)
        mock_runner.execute_terraform_command.return_value = {
            'exit_code': 0,
            'stdout': '''
# azurerm_storage_account.my_storage:
resource "azurerm_storage_account" "my_storage" {
    name = "my-storage"
}
'''
        }
        
        azure_resources = [
            {
                'id': '/subscriptions/12345/resourceGroups/test-rg/providers/Microsoft.Storage/storageAccounts/my-storage',
                'type': 'Microsoft.Storage/storageAccounts',
                'name': 'my-storage',
                'location': 'eastus'
            }
        ]
        
        terraform_resources = ['azurerm_storage_account.my_storage']
        
        matched, missing, orphaned = await ResourceMatcher.match_resources(
            azure_resources,
            mock_runner,
            'test-workspace',
            terraform_resources
        )
        
        # Should still match by normalized name
        assert len(matched) == 1
        assert matched[0]['match_method'] == 'name'
    
    @pytest.mark.asyncio
    async def test_match_resources_missing_in_terraform(self):
        """Test identifying resources missing in Terraform."""
        mock_runner = MagicMock()
        mock_runner.execute_terraform_command = AsyncMock()
        
        azure_resources = [
            {
                'id': '/subscriptions/12345/resourceGroups/test-rg/providers/Microsoft.Storage/storageAccounts/unmanaged',
                'type': 'Microsoft.Storage/storageAccounts',
                'name': 'unmanaged',
                'location': 'eastus'
            }
        ]
        
        terraform_resources = []
        
        matched, missing, orphaned = await ResourceMatcher.match_resources(
            azure_resources,
            mock_runner,
            'test-workspace',
            terraform_resources
        )
        
        assert len(matched) == 0
        assert len(missing) == 1
        assert len(orphaned) == 0
        
        assert missing[0]['resource_name'] == 'unmanaged'
        assert missing[0]['resource_type'] == 'Microsoft.Storage/storageAccounts'
    
    @pytest.mark.asyncio
    async def test_match_resources_orphaned_in_terraform(self):
        """Test identifying orphaned Terraform resources."""
        mock_runner = MagicMock()
        mock_runner.execute_terraform_command = AsyncMock()
        
        # Mock state show for orphaned resource
        mock_runner.execute_terraform_command.return_value = {
            'exit_code': 0,
            'stdout': '''
# azurerm_storage_account.deleted:
resource "azurerm_storage_account" "deleted" {
    id = "/subscriptions/12345/resourceGroups/test-rg/providers/Microsoft.Storage/storageAccounts/deleted"
}
'''
        }
        
        azure_resources = []
        terraform_resources = ['azurerm_storage_account.deleted']
        
        matched, missing, orphaned = await ResourceMatcher.match_resources(
            azure_resources,
            mock_runner,
            'test-workspace',
            terraform_resources
        )
        
        assert len(matched) == 0
        assert len(missing) == 0
        assert len(orphaned) == 1
        
        assert orphaned[0]['terraform_address'] == 'azurerm_storage_account.deleted'
        assert 'not found' in orphaned[0]['reason'].lower()

class TestCoverageAuditor:
    """Test CoverageAuditor functionality."""
    
    @pytest.fixture
    def mock_terraform_runner(self):
        """Create a mock TerraformRunner."""
        runner = MagicMock()
        runner.execute_terraform_command = AsyncMock()
        return runner
    
    @pytest.fixture
    def mock_aztfexport_runner(self):
        """Create a mock AztfexportRunner."""
        return MagicMock()
    
    @pytest.fixture
    def auditor(self, mock_terraform_runner, mock_aztfexport_runner):
        """Create a CoverageAuditor instance."""
        return CoverageAuditor(mock_terraform_runner, mock_aztfexport_runner)
    
    @pytest.mark.asyncio
    async def test_get_terraform_state_resources_success(self, auditor, mock_terraform_runner):
        """Test getting Terraform state resources successfully."""
        mock_terraform_runner.execute_terraform_command.return_value = {
            'exit_code': 0,
            'stdout': 'azurerm_storage_account.test\nazurerm_resource_group.main\n'
        }
        
        result = await auditor._get_terraform_state_resources('test-workspace')
        
        assert result is not None
        assert len(result) == 2
        assert 'azurerm_storage_account.test' in result
        assert 'azurerm_resource_group.main' in result
    
    @pytest.mark.asyncio
    async def test_get_terraform_state_resources_failure(self, auditor, mock_terraform_runner):
        """Test handling Terraform state retrieval failure."""
        mock_terraform_runner.execute_terraform_command.return_value = {
            'exit_code': 1,
            'stderr': 'State file not found'
        }
        
        result = await auditor._get_terraform_state_resources('test-workspace')
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_query_azure_resources_resource_group_scope(self, auditor):
        """Test querying Azure resources with resource group scope."""
        mock_response = {
            'data': [
                {
                    'id': '/subscriptions/12345/resourceGroups/test-rg/providers/Microsoft.Storage/storageAccounts/test',
                    'name': 'test',
                    'type': 'Microsoft.Storage/storageAccounts',
                    'location': 'eastus',
                    'resourceGroup': 'test-rg'
                }
            ]
        }
        
        with patch('asyncio.create_subprocess_exec') as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate.return_value = (
                str.encode(str(mock_response).replace("'", '"')),
                b''
            )
            mock_subprocess.return_value = mock_process
            
            result = await auditor._query_azure_resources('resource-group', 'test-rg')
            
            assert result is not None
            assert len(result) == 1
            assert result[0]['name'] == 'test'
    
    @pytest.mark.asyncio
    async def test_audit_coverage_full_workflow(self, auditor, mock_terraform_runner):
        """Test complete audit coverage workflow with dynamic matching."""
        azure_id = '/subscriptions/12345/resourceGroups/test-rg/providers/Microsoft.Storage/storageAccounts/test'
        
        # Mock Terraform state list
        def state_command_mock(command, workspace_folder, **kwargs):
            if kwargs.get('state_subcommand') == 'list':
                return {
                    'exit_code': 0,
                    'stdout': 'azurerm_storage_account.test\n'
                }
            elif kwargs.get('state_subcommand') == 'show':
                return {
                    'exit_code': 0,
                    'stdout': f'''
# azurerm_storage_account.test:
resource "azurerm_storage_account" "test" {{
    id = "{azure_id}"
}}
'''
                }
            return {'exit_code': 1}
        
        mock_terraform_runner.execute_terraform_command.side_effect = state_command_mock
        
        # Mock Azure query
        azure_response = {
            'data': [
                {
                    'id': azure_id,
                    'name': 'test',
                    'type': 'Microsoft.Storage/storageAccounts',
                    'location': 'eastus',
                    'resourceGroup': 'test-rg'
                }
            ]
        }
        
        with patch('asyncio.create_subprocess_exec') as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate.return_value = (
                str.encode(str(azure_response).replace("'", '"')),
                b''
            )
            mock_subprocess.return_value = mock_process
            
            with patch('src.tf_mcp_server.tools.coverage_auditor.resolve_workspace_path') as mock_resolve:
                from pathlib import Path
                mock_resolve.return_value = Path('/workspace/test')
                
                result = await auditor.audit_coverage(
                    workspace_folder='test-workspace',
                    scope='resource-group',
                    scope_value='test-rg'
                )
                
                assert result['success'] is True
                assert result['summary']['total_azure_resources'] == 1
                assert result['summary']['total_terraform_resources'] == 1
                assert result['summary']['terraform_managed'] == 1
                assert result['summary']['coverage_percentage'] == 100.0
    
    @pytest.mark.asyncio
    async def test_audit_coverage_with_gaps(self, auditor, mock_terraform_runner):
        """Test audit coverage with missing and orphaned resources."""
        # Mock Terraform state with orphaned resource
        def state_command_mock(command, workspace_folder, **kwargs):
            if kwargs.get('state_subcommand') == 'list':
                return {
                    'exit_code': 0,
                    'stdout': 'azurerm_storage_account.orphaned\n'
                }
            elif kwargs.get('state_subcommand') == 'show':
                return {
                    'exit_code': 0,
                    'stdout': '''
# azurerm_storage_account.orphaned:
resource "azurerm_storage_account" "orphaned" {
    id = "/subscriptions/12345/resourceGroups/test-rg/providers/Microsoft.Storage/storageAccounts/orphaned"
}
'''
                }
            return {'exit_code': 1}
        
        mock_terraform_runner.execute_terraform_command.side_effect = state_command_mock
        
        # Mock Azure with different (unmanaged) resource
        azure_response = {
            'data': [
                {
                    'id': '/subscriptions/12345/resourceGroups/test-rg/providers/Microsoft.Storage/storageAccounts/unmanaged',
                    'name': 'unmanaged',
                    'type': 'Microsoft.Storage/storageAccounts',
                    'location': 'eastus',
                    'resourceGroup': 'test-rg'
                }
            ]
        }
        
        with patch('asyncio.create_subprocess_exec') as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate.return_value = (
                str.encode(str(azure_response).replace("'", '"')),
                b''
            )
            mock_subprocess.return_value = mock_process
            
            with patch('src.tf_mcp_server.tools.coverage_auditor.resolve_workspace_path') as mock_resolve:
                from pathlib import Path
                mock_resolve.return_value = Path('/workspace/test')
                
                result = await auditor.audit_coverage(
                    workspace_folder='test-workspace',
                    scope='resource-group',
                    scope_value='test-rg'
                )
                
                assert result['success'] is True
                assert result['summary']['terraform_managed'] == 0
                assert result['summary']['missing_from_terraform'] == 1
                assert result['summary']['orphaned_in_terraform'] == 1
                assert result['summary']['coverage_percentage'] == 0.0
                assert len(result['recommendations']) > 0
    
    def test_generate_report(self, auditor):
        """Test report generation."""
        matched = [{'azure_resource_id': '/test/1', 'terraform_address': 'azurerm_storage_account.test'}]
        missing = [{'resource_id': '/test/2', 'resource_type': 'Microsoft.Storage/storageAccounts'}]
        orphaned = [{'terraform_address': 'azurerm_resource_group.old'}]
        
        report = auditor._generate_report(
            matched=matched,
            missing=missing,
            orphaned=orphaned,
            total_azure=2,
            total_terraform=2
        )
        
        assert report['success'] is True
        assert report['summary']['total_azure_resources'] == 2
        assert report['summary']['total_terraform_resources'] == 2
        assert report['summary']['terraform_managed'] == 1
        assert report['summary']['coverage_percentage'] == 50.0
        assert len(report['recommendations']) > 0


def test_get_coverage_auditor():
    """Test get_coverage_auditor factory function."""
    mock_terraform_runner = MagicMock()
    mock_aztfexport_runner = MagicMock()
    
    auditor = get_coverage_auditor(mock_terraform_runner, mock_aztfexport_runner)
    
    assert isinstance(auditor, CoverageAuditor)
    assert auditor.terraform_runner == mock_terraform_runner
    assert auditor.aztfexport_runner == mock_aztfexport_runner
