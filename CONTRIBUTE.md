# Contributing to Azure Terraform MCP Server

Thank you for your interest in contributing to the Azure Terraform MCP Server! This document provides guidelines and information for contributors.

## Table of Contents
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Code Standards](#code-standards)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Issue Guidelines](#issue-guidelines)
- [Development Workflow](#development-workflow)
- [Adding New Features](#adding-new-features)

## Getting Started

### Prerequisites
- Python 3.11 or higher
- Git
- Basic understanding of:
  - Terraform and HCL
  - Azure resources and services
  - Model Context Protocol (MCP)
  - Async Python programming

### Fork and Clone
1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/tf-mcp-server.git
   cd tf-mcp-server
   ```
3. Add the upstream repository:
   ```bash
   git remote add upstream https://github.com/ORIGINAL_OWNER/tf-mcp-server.git
   ```

## Development Setup

### Option 1: Using UV (Recommended)

```bash
# Install UV if not already installed
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies and create virtual environment
uv sync --dev

# Run the server
uv run tf-mcp-server
```

### Option 2: Traditional Python Setup

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows
venv\Scripts\activate
# Unix/macOS
source venv/bin/activate

# Install development dependencies
pip install -r requirements-dev.txt

# Install project in editable mode
pip install -e .
```

### 3. Environment Configuration
Create a `.env.local` file for local development:
```bash
MCP_HOST=localhost
MCP_PORT=6801
MCP_DEBUG=true
```

### 4. Verify Installation
```bash
# Using UV
uv run tf-mcp-server

# Or using Python module
python -m tf_mcp_server

# With debug logging
MCP_DEBUG=true uv run tf-mcp-server

# Run tests
pytest tests/

# Run tests with coverage
pytest --cov=src/tf_mcp_server tests/
```

### Development Server Configuration

The server can be configured using environment variables:

```bash
# Server settings
export MCP_HOST=localhost      # Default: localhost
export MCP_PORT=6801          # Default: 6801
export MCP_DEBUG=true         # Enable debug logging

# Run with custom configuration
uv run tf-mcp-server
```

### Debugging

For debugging issues:

1. **Enable debug logging**: Set `MCP_DEBUG=true`
2. **Check log file**: Look at `tf-mcp-server.log` for detailed logs
3. **Use pytest for testing**: Run individual tests with `-v` for verbose output
4. **Test MCP tools individually**: Use the examples in README.md

## Code Standards

### Python Style
- Follow PEP 8 guidelines
- Use `black` for code formatting
- Use `isort` for import sorting
- Use type hints where appropriate
- Maximum line length: 88 characters (black default)

### Code Formatting
```bash
# Format code with black
black src/tf_mcp_server/ tests/

# Sort imports
isort src/tf_mcp_server/ tests/

# Check formatting
black --check src/tf_mcp_server/ tests/
```

### Documentation
- Use clear, descriptive docstrings for all functions and classes
- Follow Google-style docstrings
- Update README.md for significant changes
- Add inline comments for complex logic

### Example Function Documentation
```python
async def analyze_azure_resources(hcl_content: str) -> Dict[str, Any]:
    """Analyze Azure resources in Terraform configurations.
    
    Args:
        hcl_content: Terraform HCL content to analyze
        
    Returns:
        Analysis results with resource information and recommendations
        
    Raises:
        ValidationError: If HCL content is invalid
        ProcessingError: If analysis fails
    """
```

## Testing

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/test_utils.py

# Run with verbose output
pytest -v
```

### Writing Tests
- Write tests for all new functionality
- Use descriptive test names
- Include both positive and negative test cases
- Test error conditions and edge cases
- Place tests in the `tests/` directory

### Test Structure Example
```python
import pytest
from src.tf_mcp_server.tools.terraform_runner import get_terraform_runner

class TestTerraformRunner:
    """Test cases for Terraform command execution."""
    
    @pytest.mark.asyncio
    async def test_terraform_format(self):
        """Test HCL code formatting."""
        unformatted_hcl = 'resource"azurerm_storage_account""example"{name="test"}'
        
        runner = get_terraform_runner()
        formatted = await runner.format_hcl_code(unformatted_hcl)
        
        assert 'resource "azurerm_storage_account" "example"' in formatted
        assert formatted != unformatted_hcl
    
    @pytest.mark.asyncio
    async def test_terraform_validate_valid_hcl(self):
        """Test validation of valid HCL code."""
        valid_hcl = '''
        resource "azurerm_storage_account" "example" {
          name                     = "mystorageaccount"
          resource_group_name      = "myresourcegroup"
          location                 = "East US"
          account_tier             = "Standard"
          account_replication_type = "LRS"
        }
        '''
        
        runner = get_terraform_runner()
        result = await runner.execute_terraform_command("validate", valid_hcl)
        
        assert result["exit_code"] == 0
```

## Pull Request Process

### Before Submitting
1. **Sync with upstream**:
   ```bash
   git fetch upstream
   git checkout main
   git merge upstream/main
   ```

2. **Create feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make changes and commit**:
   ```bash
   git add .
   git commit -m "feat: add new Azure resource analysis tool"
   ```

4. **Run tests and formatting**:
   ```bash
   pytest
   black src/tf_mcp_server/ tests/
   isort src/tf_mcp_server/ tests/
   ```

### Commit Message Format
Use conventional commits format:
- `feat:` - New features
- `fix:` - Bug fixes
- `docs:` - Documentation changes
- `style:` - Code style changes
- `refactor:` - Code refactoring
- `test:` - Test additions or changes
- `chore:` - Maintenance tasks

Examples:
```
feat: add AzAPI schema validation tool
fix: handle missing resource type in documentation retrieval
docs: update installation instructions for Windows
```

### Pull Request Template
When creating a PR, include:

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Code refactoring

## Testing
- [ ] All existing tests pass
- [ ] New tests added for new functionality
- [ ] Manual testing completed

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Documentation updated if needed
- [ ] No breaking changes (or documented)
```

## Issue Guidelines

### Before Creating an Issue
- Search existing issues to avoid duplicates
- Check if the issue is already fixed in the latest version
- Gather relevant information (OS, Python version, error messages)

### Issue Types

#### Bug Reports
Include:
- Clear description of the bug
- Steps to reproduce
- Expected vs actual behavior
- Environment information
- Error messages and stack traces
- Sample HCL code (if applicable)

#### Feature Requests
Include:
- Clear description of the proposed feature
- Use case and motivation
- Proposed implementation approach
- Examples of how it would be used

#### Documentation Issues
Include:
- What documentation is unclear or missing
- Suggested improvements
- Specific sections that need updates

## Development Workflow

### Adding New MCP Tools

1. **Define the tool** in `src/tf_mcp_server/core/server.py`:
```python
@mcp.tool("your_new_tool")
async def your_new_tool(
    param: str = Field(..., description="Parameter description")
) -> Dict[str, Any]:
    """Tool description for AI assistants."""
    # Implementation
    return await tool_implementation(param)
```

2. **Implement functionality** in appropriate module:
```python
# src/tf_mcp_server/tools/your_module.py
async def tool_implementation(param: str) -> Dict[str, Any]:
    """Implementation details."""
    # Your logic here
    return {"result": "success"}
```

3. **Add tests** in `tests/`:
```python
# tests/test_your_module.py
@pytest.mark.asyncio
async def test_your_new_tool():
    """Test the new tool functionality."""
    # Test implementation
```

4. **Update documentation**:
   - Add tool description to README.md
   - Include usage examples
   - Update API documentation

### Current MCP Tools

The server currently provides these MCP tools:

**Documentation Tools:**
- `azurerm_terraform_documentation_retriever` - Get AzureRM resource/data source docs
- `azapi_terraform_documentation_retriever` - Get AzAPI resource schemas

**Terraform Command Tools:**
- `run_terraform_command` - Execute any Terraform command (init, plan, apply, destroy, validate, fmt)

**Security & Analysis Tools:**
- `analyze_azure_resources` - Analyze resources in Terraform configurations

When adding new tools, follow the established patterns and ensure they integrate well with existing functionality.

### Working with Azure Resources

When adding support for new Azure resources:

1. **Research the resource** in Azure documentation
2. **Check existing patterns** in the codebase
3. **Add schema information** to `src/tf_mcp_server/data/azapi_schemas.json` if needed
4. **Update security scanning rules** if applicable
5. **Add best practices** for the resource type

### Performance Considerations

- Use async/await for I/O operations
- Cache frequently accessed data
- Minimize external API calls
- Use efficient data structures
- Profile code for performance bottlenecks

### Project Structure Notes

The project uses:
- **UV** for dependency management and virtual environments (recommended)
- **FastMCP** framework for the Model Context Protocol server
- **Async/await** pattern throughout for better performance
- **Pydantic** for data validation and serialization
- **pytest** with async support for testing

Key directories:
- `src/tf_mcp_server/core/` - Core server functionality
- `src/tf_mcp_server/tools/` - Individual tool implementations
- `src/tf_mcp_server/data/` - Static data files (schemas, etc.)
- `tests/` - Test files matching the source structure

## Adding New Features

### Planning Phase
1. **Create an issue** discussing the feature
2. **Get feedback** from maintainers
3. **Plan the implementation** approach
4. **Consider breaking changes** and backwards compatibility

### Implementation Phase
1. **Start with tests** (TDD approach recommended)
2. **Implement core functionality**
3. **Add error handling** and validation
4. **Update documentation**
5. **Add usage examples**

### Review Phase
1. **Self-review** your code
2. **Test thoroughly** with various inputs
3. **Check performance** impact
4. **Ensure compatibility** with existing features

## Release Process

### Version Numbering
This project follows [Semantic Versioning](https://semver.org/):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backwards compatible)
- **PATCH**: Bug fixes (backwards compatible)

### Release Checklist
- [ ] All tests pass
- [ ] Documentation updated
- [ ] Version bumped in `pyproject.toml`
- [ ] Changelog updated
- [ ] Release notes prepared

## Questions and Support

### Getting Help
- **Documentation**: Check README.md and code comments
- **Issues**: Search existing issues on GitHub
- **Discussions**: Use GitHub Discussions for questions
- **Code Review**: Request review from maintainers

### Communication Guidelines
- Be respectful and constructive
- Provide clear, detailed information
- Use appropriate channels for different types of communication
- Follow the code of conduct

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](https://www.contributor-covenant.org/). Please read and follow it in all interactions.

## License

By contributing to this project, you agree that your contributions will be licensed under the same license as the project (MIT License).

---

Thank you for contributing to the Azure Terraform MCP Server! Your contributions help make infrastructure as code development better for everyone.
