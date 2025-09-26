"""
Tests for TFLint runner functionality.
"""

import pytest
import tempfile
import os
import subprocess
from unittest.mock import Mock, patch, AsyncMock
from tf_mcp_server.tools.tflint_runner import TFLintRunner, get_tflint_runner


@pytest.fixture
def tflint_runner():
    """Create a TFLint runner instance for testing."""
    return TFLintRunner()


@pytest.fixture
def sample_terraform_config():
    """Sample Terraform configuration for testing."""
    return '''
resource "azurerm_resource_group" "example" {
  name     = "example-resources"
  location = "West Europe"
}

resource "azurerm_storage_account" "example" {
  name                     = "examplestorageaccount"
  resource_group_name      = azurerm_resource_group.example.name
  location                 = azurerm_resource_group.example.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
}
'''


@pytest.fixture
def sample_terraform_vars():
    """Sample Terraform variables for testing."""
    return '''
location = "West Europe"
environment = "test"
'''


class TestTFLintRunner:
    """Test cases for TFLint runner."""
    
    def test_tflint_runner_initialization(self, tflint_runner):
        """Test TFLint runner initialization."""
        assert isinstance(tflint_runner, TFLintRunner)
        assert hasattr(tflint_runner, 'tflint_executable')
    
    def test_get_tflint_runner_singleton(self):
        """Test that get_tflint_runner returns a singleton."""
        runner1 = get_tflint_runner()
        runner2 = get_tflint_runner()
        assert runner1 is runner2
    
    def test_create_tflint_config_basic(self, tflint_runner):
        """Test creation of basic TFLint configuration."""
        config = tflint_runner._create_tflint_config(enable_azure_plugin=False)
        assert 'plugin "terraform"' in config
        assert 'preset  = "recommended"' in config
        assert 'plugin "azurerm"' not in config
    
    def test_create_tflint_config_with_azure(self, tflint_runner):
        """Test creation of TFLint configuration with Azure plugin."""
        config = tflint_runner._create_tflint_config(enable_azure_plugin=True)
        assert 'plugin "terraform"' in config
        assert 'plugin "azurerm"' in config
        assert 'source  = "github.com/terraform-linters/tflint-ruleset-azurerm"' in config
    
    @patch('subprocess.run')
    def test_check_tflint_installation_success(self, mock_run, tflint_runner):
        """Test successful TFLint installation check."""
        # Mock successful tflint --version command
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "TFLint version 0.50.0"
        mock_run.return_value = mock_result
        
        # Note: This is an async method, so we need to use pytest-asyncio
        import asyncio
        result = asyncio.run(tflint_runner.check_tflint_installation())
        
        assert result['installed'] is True
        assert 'TFLint version 0.50.0' in result['version']
        assert 'executable_path' in result
    
    @patch('subprocess.run')
    def test_check_tflint_installation_not_found(self, mock_run, tflint_runner):
        """Test TFLint installation check when not found."""
        # Mock FileNotFoundError
        mock_run.side_effect = FileNotFoundError("tflint not found")
        
        import asyncio
        result = asyncio.run(tflint_runner.check_tflint_installation())
        
        assert result['installed'] is False
        assert 'not found' in result['error']
        assert 'installation_help' in result
        assert 'install_methods' in result['installation_help']
    
    @patch('subprocess.run')
    async def test_run_tflint_init_success(self, mock_run, tflint_runner):
        """Test successful TFLint plugin initialization."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Installing plugins..."
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        with tempfile.TemporaryDirectory() as temp_dir:
            result = await tflint_runner._run_tflint_init(temp_dir)
            
            assert result['success'] is True
            assert 'Installing plugins' in result['stdout']
    
    @patch('subprocess.run')
    async def test_run_tflint_init_failure(self, mock_run, tflint_runner):
        """Test failed TFLint plugin initialization."""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Failed to install plugins"
        mock_run.return_value = mock_result
        
        with tempfile.TemporaryDirectory() as temp_dir:
            result = await tflint_runner._run_tflint_init(temp_dir)
            
            assert result['success'] is False
            assert 'Failed to install plugins' in result['error']
    
    def test_parse_tflint_output_json_format(self, tflint_runner):
        """Test parsing TFLint JSON output."""
        import subprocess
        
        # Mock successful result with JSON output
        mock_result = Mock(spec=subprocess.CompletedProcess)
        mock_result.returncode = 2  # Issues found
        mock_result.stdout = '''
        {
            "issues": [
                {
                    "rule": {"name": "test_rule", "severity": "error"},
                    "message": "Test error message"
                },
                {
                    "rule": {"name": "test_rule2", "severity": "warning"},
                    "message": "Test warning message"
                }
            ]
        }
        '''
        mock_result.stderr = ""
        
        result = tflint_runner._parse_tflint_output(mock_result, "json")
        
        assert result['success'] is True
        assert len(result['issues']) == 2
        assert result['summary']['total_issues'] == 2
        assert result['summary']['errors'] == 1
        assert result['summary']['warnings'] == 1
    
    def test_parse_tflint_output_execution_error(self, tflint_runner):
        """Test parsing TFLint output with execution error."""
        import subprocess
        
        # Mock failed result
        mock_result = Mock(spec=subprocess.CompletedProcess)
        mock_result.returncode = 1  # Execution error
        mock_result.stdout = ""
        mock_result.stderr = "TFLint execution failed"
        
        result = tflint_runner._parse_tflint_output(mock_result, "json")
        
        assert result['success'] is False
        assert 'TFLint execution failed' in result['error']
        assert result['summary']['total_issues'] == 0

    @pytest.mark.asyncio
    async def test_lint_terraform_workspace_folder_empty_folder(self, tflint_runner):
        """Test workspace folder linting with empty folder path."""
        result = await tflint_runner.lint_terraform_workspace_folder("")
        
        assert result['success'] is False
        assert 'No workspace folder provided' in result['error']

    @pytest.mark.asyncio
    async def test_lint_terraform_workspace_folder_nonexistent(self, tflint_runner):
        """Test workspace folder linting with nonexistent folder."""
        result = await tflint_runner.lint_terraform_workspace_folder("/nonexistent/folder")
        
        assert result['success'] is False
        assert 'does not exist' in result['error']

    @pytest.mark.asyncio
    async def test_lint_terraform_workspace_folder_no_tf_files(self, tflint_runner):
        """Test workspace folder linting with folder containing no Terraform files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a non-Terraform file
            non_tf_file = os.path.join(temp_dir, 'readme.txt')
            with open(non_tf_file, 'w') as f:
                f.write('This is not a Terraform file')
            
            result = await tflint_runner.lint_terraform_workspace_folder(temp_dir)
            
            assert result['success'] is False
            assert 'No Terraform files' in result['error']

    @pytest.mark.asyncio
    async def test_lint_terraform_workspace_folder_with_tf_files(self, tflint_runner, sample_terraform_config):
        """Test workspace folder linting with Terraform files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create main.tf file
            tf_file = os.path.join(temp_dir, 'main.tf')
            with open(tf_file, 'w', encoding='utf-8') as f:
                f.write(sample_terraform_config)
            
            # Mock the subprocess.run call for TFLint execution
            with patch('subprocess.run') as mock_run:
                # Mock successful TFLint execution
                mock_run.return_value.returncode = 0
                mock_run.return_value.stdout = '{"issues": []}'
                mock_run.return_value.stderr = ""
                
                # Mock the initialization call
                with patch.object(tflint_runner, '_run_tflint_init', return_value={'success': True}):
                    result = await tflint_runner.lint_terraform_workspace_folder(
                        temp_dir, 
                        initialize_plugins=True
                    )
                
                assert result['success'] is True
                assert result['workspace_folder'] == os.path.abspath(temp_dir)
                assert result['terraform_files_found'] == 1
                assert len(result['terraform_files']) == 1
                assert result['terraform_files'][0].endswith('main.tf')

    @pytest.mark.asyncio
    async def test_lint_terraform_workspace_folder_recursive(self, tflint_runner, sample_terraform_config):
        """Test recursive workspace folder linting."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create main.tf file in root
            tf_file = os.path.join(temp_dir, 'main.tf')
            with open(tf_file, 'w', encoding='utf-8') as f:
                f.write(sample_terraform_config)
            
            # Create subdirectory with another Terraform file
            sub_dir = os.path.join(temp_dir, 'modules')
            os.makedirs(sub_dir, exist_ok=True)
            
            sub_tf_file = os.path.join(sub_dir, 'network.tf')
            with open(sub_tf_file, 'w', encoding='utf-8') as f:
                f.write('''
resource "azurerm_virtual_network" "example" {
  name = "example-vnet"
}
''')
            
            # Mock the subprocess.run call for TFLint execution
            with patch('subprocess.run') as mock_run:
                mock_run.return_value.returncode = 0
                mock_run.return_value.stdout = '{"issues": []}'
                mock_run.return_value.stderr = ""
                
                # Mock the initialization call
                with patch.object(tflint_runner, '_run_tflint_init', return_value={'success': True}):
                    result = await tflint_runner.lint_terraform_workspace_folder(
                        temp_dir, 
                        recursive=True,
                        initialize_plugins=True
                    )
                
                assert result['success'] is True
                assert result['terraform_files_found'] == 2
                assert len(result['terraform_files']) == 2

    @pytest.mark.asyncio
    async def test_lint_terraform_workspace_folder_init_failure(self, tflint_runner, sample_terraform_config):
        """Test workspace folder linting with initialization failure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create main.tf file
            tf_file = os.path.join(temp_dir, 'main.tf')
            with open(tf_file, 'w', encoding='utf-8') as f:
                f.write(sample_terraform_config)
            
            # Mock failed initialization
            with patch.object(tflint_runner, '_run_tflint_init', return_value={
                'success': False, 
                'error': 'Plugin initialization failed'
            }):
                result = await tflint_runner.lint_terraform_workspace_folder(
                    temp_dir, 
                    initialize_plugins=True
                )
            
            assert result['success'] is False
            assert 'Failed to initialize TFLint plugins' in result['error']

    @pytest.mark.asyncio
    async def test_lint_terraform_workspace_folder_execution_timeout(self, tflint_runner, sample_terraform_config):
        """Test workspace folder linting with execution timeout."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create main.tf file
            tf_file = os.path.join(temp_dir, 'main.tf')
            with open(tf_file, 'w', encoding='utf-8') as f:
                f.write(sample_terraform_config)
            
            # Mock timeout exception
            with patch('subprocess.run', side_effect=subprocess.TimeoutExpired(['tflint'], 180)):
                with patch.object(tflint_runner, '_run_tflint_init', return_value={'success': True}):
                    result = await tflint_runner.lint_terraform_workspace_folder(temp_dir)
                
                assert result['success'] is False
                assert 'timed out' in result['error']

    @pytest.mark.asyncio
    async def test_lint_terraform_workspace_folder_with_rules(self, tflint_runner, sample_terraform_config):
        """Test workspace folder linting with specific rules."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create main.tf file
            tf_file = os.path.join(temp_dir, 'main.tf')
            with open(tf_file, 'w', encoding='utf-8') as f:
                f.write(sample_terraform_config)
            
            # Mock the subprocess.run call for TFLint execution
            with patch('subprocess.run') as mock_run:
                mock_run.return_value.returncode = 0
                mock_run.return_value.stdout = '{"issues": []}'
                mock_run.return_value.stderr = ""
                
                with patch.object(tflint_runner, '_run_tflint_init', return_value={'success': True}):
                    result = await tflint_runner.lint_terraform_workspace_folder(
                        temp_dir,
                        enable_rules=['terraform_required_providers'],
                        disable_rules=['terraform_unused_declarations'],
                        initialize_plugins=True
                    )
                
                # Check that the subprocess was called with the right arguments
                mock_run.assert_called_once()
                call_args = mock_run.call_args[0][0]  # Get the command arguments
                
                assert '--enable-rule' in call_args
                assert 'terraform_required_providers' in call_args
                assert '--disable-rule' in call_args
                assert 'terraform_unused_declarations' in call_args
                
                assert result['success'] is True
