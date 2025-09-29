"""
Comprehensive test cases for AVM documentation provider.
"""

import pytest
import json
import re
import os

from src.tf_mcp_server.tools.avm_docs_provider import AzureVerifiedModuleDocumentationProvider, Constants

class TestAzureVerifiedModuleDocumentationProviderIntegration:
    def setup_method(self):
        """Set up test fixtures."""
        self.provider = AzureVerifiedModuleDocumentationProvider()
    
    def test_get_available_modules(self):
        """Test that available_modules returns valid JSON with expected structure."""
        # Call the actual method
        result = self.provider.available_modules()
        
        # Verify it returns a valid JSON string
        assert isinstance(result, str)
        modules_data = json.loads(result)
        
        # Verify the result is a list
        assert isinstance(modules_data, list)
        
        # If there are modules, verify the structure
        if modules_data:
            # Check the first module has the expected fields
            first_module = modules_data[0]
            expected_fields = ["module_name", "description", "source"]
            
            for field in expected_fields:
                assert field in first_module, f"Expected field '{field}' not found in module data"
                assert isinstance(first_module[field], str), f"Field '{field}' should be a string"
            
            # Verify module_name is not empty
            assert first_module["module_name"].strip() != "", "Module name should not be empty"
            
            # Verify source follows expected pattern (Azure/terraform-azurerm-*)
            assert first_module["source"].startswith("Azure/"), f"Source should start with 'Azure/', got: {first_module['source']}"
            
        print(f"Successfully retrieved {len(modules_data)} available modules")

    def test_get_latest_module_version(self):
        """Test that latest_module_version returns a valid version for an existing module."""
        # Skip test if no GitHub token is available
        if not os.getenv("GITHUB_TOKEN"):
            pytest.skip("GITHUB_TOKEN not available, skipping GitHub API test")
            
        try:
            # First get available modules to use a real module name
            available_modules_result = self.provider.available_modules()
            modules_data = json.loads(available_modules_result)
            
            # Skip test if no modules are available
            if not modules_data:
                pytest.skip("No modules available to test")
            
            # Use the first available module
            test_module_name = modules_data[0]["module_name"]
            
            # Call the latest_module_version method
            result = self.provider.latest_module_version(test_module_name)
            
            # Verify the result is a string
            assert isinstance(result, str)
            
            # Verify it's not an error message
            assert not result.startswith("No version found for module:")
            
            print(f"Latest version for module '{test_module_name}': {result}")
            
        except Exception as e:
            if "401" in str(e) or "Unauthorized" in str(e):
                pytest.skip(f"GitHub API authentication failed: {e}")
            else:
                raise

    def test_get_module_versions(self):
        """Test that module_versions returns valid JSON with version information for an existing module."""
        # Skip test if no GitHub token is available
        if not os.getenv("GITHUB_TOKEN"):
            pytest.skip("GITHUB_TOKEN not available, skipping GitHub API test")
            
        try:
            # First get available modules to use a real module name
            available_modules_result = self.provider.available_modules()
            modules_data = json.loads(available_modules_result)
            
            # Skip test if no modules are available
            if not modules_data:
                pytest.skip("No modules available to test")
            
            # Use the first available module
            test_module_name = modules_data[0]["module_name"]
            
            # Call the module_versions method
            result = self.provider.module_versions(test_module_name)
            
        except Exception as e:
            if "401" in str(e) or "Unauthorized" in str(e):
                pytest.skip(f"GitHub API authentication failed: {e}")
            else:
                raise
        
        # Verify the result is a string
        assert isinstance(result, str)
        
        # Verify it's not an error message
        assert not result.startswith("No versions found for module:")
        
        # Verify it's valid JSON
        versions_data = json.loads(result)
        
        # Verify the result is a list
        assert isinstance(versions_data, list)
        
        # If there are versions, verify they are valid version strings
        if versions_data:
            for version in versions_data:
                assert isinstance(version, str), "Each version should be a string"
                assert version.strip() != "", "Version should not be empty"
        
        print(f"Successfully retrieved {len(versions_data)} versions for module '{test_module_name}'")
        if versions_data:
            print(f"Latest version: {versions_data[0]}")

    def test_get_module_variables(self):
        """Test that module_variables returns valid Terraform variable content for an existing module."""
        # Skip test if no GitHub token is available
        if not os.getenv("GITHUB_TOKEN"):
            pytest.skip("GITHUB_TOKEN not available, skipping GitHub API test")
            
        try:
            # First get available modules to use a real module name
            available_modules_result = self.provider.available_modules()
            modules_data = json.loads(available_modules_result)
            
            # Skip test if no modules are available
            if not modules_data:
                pytest.skip("No modules available to test")
            
            # Use the first available module
            test_module_name = modules_data[0]["module_name"]
            
            # Get the latest version for this module
            latest_version = self.provider.latest_module_version(test_module_name)
            
            # Skip test if no version is available
            if latest_version.startswith("No version found for module:"):
                pytest.skip(f"No version available for module: {test_module_name}")
            
            # Call the module_variables method
            result = self.provider.module_variables(test_module_name, latest_version)
            
            # Verify the result is a string
            assert isinstance(result, str)
            
            # If there are variables, verify it contains Terraform variable syntax
            if result.strip():
                # Check for common Terraform variable patterns
                variable_patterns = [
                    r'variable\s+"[^"]+"\s*\{',  # variable "name" {
                    r'description\s*=',          # description =
                    r'type\s*=',                 # type =
                    r'default\s*='               # default =
                ]
                
                found_pattern = False
                for pattern in variable_patterns:
                    if re.search(pattern, result, re.IGNORECASE):
                        found_pattern = True
                        break
                
                if found_pattern:
                    print(f"Successfully retrieved variables for module '{test_module_name}' version '{latest_version}'")
                    print(f"Variables content length: {len(result)} characters")
                else:
                    print(f"Warning: Variables content for module '{test_module_name}' doesn't match expected Terraform syntax")
                    print(f"Content preview: {result[:200]}...")
            else:
                print(f"No variables found for module '{test_module_name}' version '{latest_version}'")
            
        except Exception as e:
            if "401" in str(e) or "Unauthorized" in str(e):
                pytest.skip(f"GitHub API authentication failed: {e}")
            else:
                raise
        
        # Skip test if no modules are available
        if not modules_data:
            pytest.skip("No modules available to test")
        
        # Use the first available module
        test_module_name = modules_data[0]["module_name"]
        
        # Get the latest version for this module
        latest_version = self.provider.latest_module_version(test_module_name)
        
        # Skip test if no version is available
        if latest_version.startswith("No version found for module:"):
            pytest.skip(f"No version available for module: {test_module_name}")
        
        # Call the module_variables method
        result = self.provider.module_variables(test_module_name, latest_version)
        
        # Verify the result is a string
        assert isinstance(result, str)
        
        # If there are variables, verify it contains Terraform variable syntax
        if result.strip():
            # Check for common Terraform variable patterns
            terraform_patterns = [
                r'variable\s+"[\w-]+"',  # variable "name"
                r'description\s*=',       # description =
                r'type\s*=',             # type =
                r'default\s*='           # default =
            ]
            
            # At least one pattern should match if there are variables
            pattern_matches = sum(1 for pattern in terraform_patterns if re.search(pattern, result))
            
            if pattern_matches > 0:
                print(f"Successfully retrieved Terraform variables for module '{test_module_name}' version '{latest_version}'")
                print(f"Variables content length: {len(result)} characters")
                
                # Show first few lines as a sample
                lines = result.split('\n')[:5]
                print(f"Sample content: {lines}")
            else:
                # If no patterns match but result is not empty, it might be an error message or no variables
                print(f"No Terraform variable patterns found in result for module '{test_module_name}'")
                print(f"Result preview: {result[:200]}...")
        else:
            print(f"No variables found for module '{test_module_name}' version '{latest_version}'")

    def test_get_module_outputs(self):
        """Test that module_outputs returns valid Terraform output content for an existing module."""
        # Skip test if no GitHub token is available
        if not os.getenv("GITHUB_TOKEN"):
            pytest.skip("GITHUB_TOKEN not available, skipping GitHub API test")
            
        try:
            # First get available modules to use a real module name
            available_modules_result = self.provider.available_modules()
            modules_data = json.loads(available_modules_result)
            
            # Skip test if no modules are available
            if not modules_data:
                pytest.skip("No modules available to test")
            
            # Use the first available module
            test_module_name = modules_data[0]["module_name"]
            
            # Get the latest version for this module
            latest_version = self.provider.latest_module_version(test_module_name)
            
            # Skip test if no version is available
            if latest_version.startswith("No version found for module:"):
                pytest.skip(f"No version available for module: {test_module_name}")
            
            # Call the module_outputs method
            result = self.provider.module_outputs(test_module_name, latest_version)
            
            # Verify the result is a string
            assert isinstance(result, str)
            
            # If there are outputs, verify it contains Terraform output syntax
            if result.strip():
                # Check for common Terraform output patterns
                terraform_patterns = [
                    r'output\s+"[\w-]+"',     # output "name"
                    r'description\s*=',       # description =
                    r'value\s*=',            # value =
                    r'sensitive\s*='         # sensitive =
                ]
                
                # At least one pattern should match if there are outputs
                pattern_matches = sum(1 for pattern in terraform_patterns if re.search(pattern, result))
                
                if pattern_matches > 0:
                    print(f"Successfully retrieved Terraform outputs for module '{test_module_name}' version '{latest_version}'")
                    print(f"Outputs content length: {len(result)} characters")
                    
                    # Show first few lines as a sample
                    lines = result.split('\n')[:5]
                    print(f"Sample content: {lines}")
                else:
                    # If no patterns match but result is not empty, it might be an error message or no outputs
                    print(f"No Terraform output patterns found in result for module '{test_module_name}'")
                    print(f"Result preview: {result[:200]}...")
            else:
                print(f"No outputs found for module '{test_module_name}' version '{latest_version}'")
                
        except Exception as e:
            if "401" in str(e) or "Unauthorized" in str(e):
                pytest.skip(f"GitHub API authentication failed: {e}")
            else:
                raise