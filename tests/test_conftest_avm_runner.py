"""
Tests for Conftest AVM runner.
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch, AsyncMock
from tf_mcp_server.tools.conftest_avm_runner import ConftestAVMRunner, get_conftest_avm_runner


class TestConftestAVMRunner:
    """Test cases for ConftestAVMRunner."""
    
    @pytest.fixture
    def runner(self):
        """Get a ConftestAVMRunner instance."""
        return ConftestAVMRunner()
    
    def test_find_conftest_executable(self, runner):
        """Test finding conftest executable."""
        executable = runner._find_conftest_executable()
        assert executable in ['conftest', 'conftest.exe']
    
    def test_get_installation_help(self, runner):
        """Test getting installation help."""
        help_info = runner._get_installation_help()
        assert isinstance(help_info, dict)
        assert 'windows' in help_info
        assert 'macos' in help_info
        assert 'linux' in help_info
        assert 'go_install' in help_info
    
    def test_create_severity_exception_high(self, runner):
        """Test creating severity exception for high severity."""
        exception = runner._create_severity_exception('high')
        assert 'package avmsec' in exception
        assert 'rules_below_high' in exception
    
    def test_create_severity_exception_medium(self, runner):
        """Test creating severity exception for medium severity."""
        exception = runner._create_severity_exception('medium')
        assert 'package avmsec' in exception
        assert 'rules_below_medium' in exception
    
    def test_create_severity_exception_low(self, runner):
        """Test creating severity exception for low severity."""
        exception = runner._create_severity_exception('low')
        assert 'package avmsec' in exception
        assert 'rules_below_low' in exception
    
    def test_create_severity_exception_info(self, runner):
        """Test creating severity exception for info severity."""
        exception = runner._create_severity_exception('info')
        assert exception == ""
    
    def test_parse_conftest_output(self, runner):
        """Test parsing conftest JSON output."""
        output_data = [
            {
                'filename': 'test.json',
                'failures': [
                    {
                        'rule': 'test_rule',
                        'msg': 'Test failure',
                        'metadata': {'severity': 'high'}
                    }
                ],
                'warnings': [
                    {
                        'rule': 'warning_rule',
                        'msg': 'Test warning',
                        'metadata': {'severity': 'medium'}
                    }
                ]
            }
        ]
        
        violations = runner._parse_conftest_output(output_data)
        assert len(violations) == 2
        assert violations[0]['level'] == 'failure'
        assert violations[1]['level'] == 'warning'
        assert violations[0]['policy'] == 'test_rule'
        assert violations[1]['policy'] == 'warning_rule'
    
    def test_parse_conftest_text_output(self, runner):
        """Test parsing conftest text output."""
        output_text = """
        FAIL - test.json - policy violation
        WARN - test.json - policy warning
        Some other output
        """
        
        violations = runner._parse_conftest_text_output(output_text)
        assert len(violations) == 2
        assert violations[0]['level'] == 'failure'
        assert violations[1]['level'] == 'warning'
    
    @pytest.mark.asyncio
    async def test_check_conftest_installation_success(self, runner):
        """Test successful conftest installation check."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = 'conftest v0.46.0'
            
            result = await runner.check_conftest_installation()
            
            assert result['installed'] is True
            assert 'conftest v0.46.0' in result['version']
    
    @pytest.mark.asyncio
    async def test_check_conftest_installation_not_found(self, runner):
        """Test conftest installation check when not found."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = FileNotFoundError()
            
            result = await runner.check_conftest_installation()
            
            assert result['installed'] is False
            assert 'installation_help' in result
    
    @pytest.mark.asyncio
    async def test_validate_with_avm_policies_empty_input(self, runner):
        """Test validation with empty terraform plan JSON."""
        result = await runner.validate_with_avm_policies("")
        
        assert result['success'] is False
        assert 'No Terraform plan JSON provided' in result['error']
        assert result['violations'] == []
    
    @pytest.mark.asyncio
    async def test_validate_terraform_hcl_with_avm_policies_empty_input(self, runner):
        """Test HCL validation with empty input."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 1
            mock_run.return_value.stderr = 'No configuration files'
            
            result = await runner.validate_terraform_hcl_with_avm_policies("")
            
            # Should fail because empty HCL content
            assert result['success'] is False
    
    @pytest.mark.asyncio
    async def test_validate_with_avm_policies_success(self, runner):
        """Test successful validation with AVM policies."""
        terraform_plan = '{"planned_values": {"root_module": {"resources": []}}}'
        
        with patch('subprocess.run') as mock_run:
            # Mock successful conftest execution
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = '[]'  # Empty violations
            mock_run.return_value.stderr = ''
            
            result = await runner.validate_with_avm_policies(terraform_plan)
            
            assert result['success'] is True
            assert result['total_violations'] == 0
            assert result['policy_set'] == 'all'
    
    @pytest.mark.asyncio
    async def test_validate_with_avm_policies_with_violations(self, runner):
        """Test validation with AVM policies that has violations."""
        terraform_plan = '{"planned_values": {"root_module": {"resources": []}}}'
        
        with patch('subprocess.run') as mock_run:
            # Mock conftest execution with violations
            mock_run.return_value.returncode = 1
            mock_run.return_value.stdout = '''[
                {
                    "filename": "test.json",
                    "failures": [
                        {
                            "rule": "test_violation",
                            "msg": "Policy violation detected",
                            "metadata": {"severity": "high"}
                        }
                    ],
                    "warnings": []
                }
            ]'''
            mock_run.return_value.stderr = ''
            
            result = await runner.validate_with_avm_policies(terraform_plan)
            
            assert result['success'] is False
            assert result['total_violations'] == 1
            assert len(result['violations']) == 1
            assert result['violations'][0]['policy'] == 'test_violation'
    
    @pytest.mark.asyncio
    async def test_validate_with_custom_policy_set(self, runner):
        """Test validation with custom policy set."""
        terraform_plan = '{"planned_values": {"root_module": {"resources": []}}}'
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = '[]'
            mock_run.return_value.stderr = ''
            
            result = await runner.validate_with_avm_policies(
                terraform_plan, 
                policy_set="avmsec"
            )
            
            assert result['success'] is True
            assert result['policy_set'] == 'avmsec'
    
    @pytest.mark.asyncio
    async def test_validate_with_severity_filter(self, runner):
        """Test validation with severity filter."""
        terraform_plan = '{"planned_values": {"root_module": {"resources": []}}}'
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = '[]'
            mock_run.return_value.stderr = ''
            
            result = await runner.validate_with_avm_policies(
                terraform_plan, 
                policy_set="avmsec",
                severity_filter="high"
            )
            
            assert result['success'] is True
            assert result['severity_filter'] == 'high'
    
    def test_get_conftest_avm_runner_singleton(self):
        """Test that get_conftest_avm_runner returns singleton instance."""
        runner1 = get_conftest_avm_runner()
        runner2 = get_conftest_avm_runner()
        assert runner1 is runner2


class TestConftestAVMIntegration:
    """Integration tests for Conftest AVM runner."""
    
    @pytest.mark.asyncio
    async def test_full_hcl_validation_flow(self):
        """Test full HCL validation flow if terraform and conftest are available."""
        runner = ConftestAVMRunner()
        
        # Simple HCL content for testing
        hcl_content = '''
        resource "azurerm_resource_group" "test" {
          name     = "test-rg"
          location = "West Europe"
        }
        '''
        
        # This test will only run if both terraform and conftest are installed
        # Otherwise it will fail gracefully
        result = await runner.validate_terraform_hcl_with_avm_policies(hcl_content)
        
        # We expect either success or a meaningful error message
        assert 'success' in result
        assert 'violations' in result
        assert 'summary' in result
        
        if not result['success']:
            # If it fails, it should be due to missing tools or configuration issues
            assert 'error' in result
            assert isinstance(result['error'], str)
