"""
Tests for ANSI escape sequence cleanup in Conftest AVM runner.
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from tf_mcp_server.tools.conftest_avm_runner import ConftestAVMRunner
from tf_mcp_server.core.utils import strip_ansi_escape_sequences


class TestAnsiCleanup:
    """Test ANSI escape sequence cleanup functionality."""
    
    def test_strip_ansi_escape_sequences_basic(self):
        """Test basic ANSI escape sequence removal."""
        # Test string with ANSI escape sequences (like the example from the user)
        text_with_ansi = "\u001b[31m╷\u001b[0m\u001b[0m\n\u001b[31m│\u001b[0m \u001b[0m\u001b[1m\u001b[31mError: \u001b[0m\u001b[0m\u001b[1mReference to undeclared input variable\u001b[0m"
        expected = "╷\n│ Error: Reference to undeclared input variable"
        result = strip_ansi_escape_sequences(text_with_ansi)
        assert result == expected
    
    def test_strip_ansi_escape_sequences_empty_string(self):
        """Test ANSI stripping with empty string."""
        assert strip_ansi_escape_sequences("") == ""
        assert strip_ansi_escape_sequences(None) is None
    
    def test_strip_ansi_escape_sequences_no_ansi(self):
        """Test ANSI stripping with text that has no ANSI sequences."""
        text = "This is a normal text without ANSI sequences"
        result = strip_ansi_escape_sequences(text)
        assert result == text
    
    def test_strip_ansi_escape_sequences_complex(self):
        """Test ANSI stripping with complex escape sequences."""
        text_with_ansi = (
            "\u001b[31m│\u001b[0m \u001b[0m\u001b[0m  on main.tf line 8, in resource \"azurerm_resource_group\" \"batch_rg\":\n"
            "\u001b[31m│\u001b[0m \u001b[0m   8:   name     = \"rg-batch-${\u001b[4mvar.environment\u001b[0m}-${var.location_short}\"\u001b[0m"
        )
        expected = (
            "│   on main.tf line 8, in resource \"azurerm_resource_group\" \"batch_rg\":\n"
            "│    8:   name     = \"rg-batch-${var.environment}-${var.location_short}\""
        )
        result = strip_ansi_escape_sequences(text_with_ansi)
        assert result == expected
    
    @pytest.mark.asyncio
    async def test_conftest_runner_error_cleanup(self):
        """Test that ConftestAVMRunner cleans ANSI sequences from errors."""
        runner = ConftestAVMRunner()
        
        # Mock subprocess to return error with ANSI sequences
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "\u001b[31mError: \u001b[0mTerraform plan failed with ANSI colors"
        mock_result.stdout = ""
        
        with patch('subprocess.run', return_value=mock_result):
            with patch('tempfile.TemporaryDirectory') as mock_temp_dir:
                # Mock the temporary directory context manager
                mock_temp_dir.return_value.__enter__.return_value = "/fake/temp/dir"
                with patch('builtins.open', create=True):
                    result = await runner.validate_terraform_hcl_with_avm_policies(
                        hcl_content='resource "azurerm_resource_group" "test" {}'
                    )
        
        # Check that the error message has ANSI sequences removed
        assert result['success'] is False
        assert 'Terraform plan failed with ANSI colors' in result['error']
        assert '\u001b[31m' not in result['error']
        assert '\u001b[0m' not in result['error']
    
    def test_terraform_error_example_cleanup(self):
        """Test cleanup of the specific Terraform error from the user's example."""
        error_text = (
            "\u001b[31m╷\u001b[0m\u001b[0m\n"
            "\u001b[31m│\u001b[0m \u001b[0m\u001b[1m\u001b[31mError: \u001b[0m\u001b[0m\u001b[1mReference to undeclared input variable\u001b[0m\n"
            "\u001b[31m│\u001b[0m \u001b[0m\n"
            "\u001b[31m│\u001b[0m \u001b[0m\u001b[0m  on main.tf line 8, in resource \"azurerm_resource_group\" \"batch_rg\":\n"
            "\u001b[31m│\u001b[0m \u001b[0m   8:   name     = \"rg-batch-${\u001b[4mvar.environment\u001b[0m}-${var.location_short}\"\u001b[0m\n"
            "\u001b[31m│\u001b[0m \u001b[0m\n"
            "\u001b[31m│\u001b[0m \u001b[0mAn input variable with the name \"environment\" has not been declared. This\n"
            "\u001b[31m│\u001b[0m \u001b[0mvariable can be declared with a variable \"environment\" {} block.\n"
            "\u001b[31m╵\u001b[0m\u001b[0m"
        )
        
        result = strip_ansi_escape_sequences(error_text)
        
        # Check that result is not None and is a string
        assert result is not None
        assert isinstance(result, str)
        
        # Check that ANSI sequences are removed
        assert '\u001b[31m' not in result
        assert '\u001b[0m' not in result
        assert '\u001b[1m' not in result
        assert '\u001b[4m' not in result
        
        # Check that the actual content is preserved
        assert 'Error: Reference to undeclared input variable' in result
        assert 'on main.tf line 8' in result
        assert 'var.environment' in result
        assert 'variable can be declared with a variable "environment" {} block' in result
    
    @pytest.mark.asyncio 
    async def test_conftest_validation_with_ansi_cleanup(self):
        """Test that conftest validation cleans ANSI sequences from command output."""
        runner = ConftestAVMRunner()
        
        # Mock subprocess to return output with ANSI sequences
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = "\u001b[31mFAIL\u001b[0m - Policy violation found"
        mock_result.stderr = "\u001b[33mWarning: \u001b[0mSome warning message"
        
        with patch('subprocess.run', return_value=mock_result):
            with patch('tempfile.NamedTemporaryFile'):
                result = await runner.validate_with_avm_policies(
                    terraform_plan_json='{"planned_values": {}}'
                )
        
        # Check that command output and error have ANSI sequences removed
        if result.get('command_output'):
            assert '\u001b[31m' not in result['command_output']
            assert '\u001b[0m' not in result['command_output']
            assert 'FAIL - Policy violation found' in result['command_output']
        
        if result.get('command_error'):
            assert '\u001b[33m' not in result['command_error']
            assert '\u001b[0m' not in result['command_error']
            assert 'Warning: Some warning message' in result['command_error']


if __name__ == "__main__":
    pytest.main([__file__])
