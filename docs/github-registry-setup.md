# GitHub Container Registry Setup

This document explains how to set up your GitHub repository to automatically build and publish Docker images to GitHub Container Registry (GHCR).

## Repository Settings

### 1. Enable GitHub Container Registry

The GitHub Action is already configured to push to GitHub Container Registry. No additional setup is required for the registry itself.

### 2. Repository Permissions

Ensure the repository has the correct permissions:

1. Go to your repository on GitHub
2. Navigate to **Settings** → **Actions** → **General**
3. Under "Workflow permissions", select **Read and write permissions**
4. Check **Allow GitHub Actions to create and approve pull requests**

### 3. Package Visibility (Optional)

After the first successful build, you may want to make the package public:

1. Go to your repository on GitHub
2. Navigate to the **Packages** tab (or visit `https://github.com/users/YOUR_USERNAME/packages`)
3. Find your `tf-mcp-server` package
4. Click on the package
5. Go to **Package settings**
6. Under **Danger Zone**, click **Change visibility**
7. Select **Public** to make it publicly accessible

## Automatic Builds

The GitHub Action will automatically build and push Docker images when:

- **Push to main branch**: Creates `latest` tag
- **Push to any branch**: Creates branch-specific tag
- **Pull requests**: Creates PR-specific tag for testing
- **Tags**: Creates version-specific tags (e.g., `v1.0.0`)
- **Manual trigger**: Can be triggered manually from the Actions tab

## Image Tags

The action creates multiple tags for flexibility:

- `latest` - Latest stable release (main branch)
- `main` - Latest from main branch
- `v1.0.0` - Specific version tags
- `1.0` - Major.minor version
- `1` - Major version only
- `pr-123` - Pull request builds

## Multi-Architecture Support

The Docker images are built for multiple architectures:
- `linux/amd64` (Intel/AMD 64-bit)
- `linux/arm64` (ARM 64-bit, including Apple Silicon)

## Security Features

The setup includes several security features:

1. **Build attestations**: Cryptographic proof of build provenance
2. **SBOM generation**: Software Bill of Materials for security scanning
3. **Multi-stage builds**: Reduced attack surface
4. **Non-root user**: Container runs as non-privileged user
5. **Health checks**: Built-in container health monitoring

## Usage Examples

Once published, users can use your Docker image:

**For VS Code MCP integration:**
```bash
# Latest version  
docker run --rm -i -v $(pwd):/workspace ghcr.io/YOUR_USERNAME/tf-mcp-server:latest

# Specific version
docker run --rm -i -v $(pwd):/workspace ghcr.io/YOUR_USERNAME/tf-mcp-server:v1.0.0

# Development version
docker run --rm -i -v $(pwd):/workspace ghcr.io/YOUR_USERNAME/tf-mcp-server:main
```

**For HTTP server mode (non-MCP):**
```bash
# Use -p 8000:8000 for direct API access
docker run -p 8000:8000 ghcr.io/YOUR_USERNAME/tf-mcp-server:latest
```

## Monitoring Builds

You can monitor the build process:

1. Go to your repository on GitHub
2. Click the **Actions** tab
3. Select **Build and Publish Docker Image** workflow
4. View the progress and logs of current and past builds

## Troubleshooting

### Build Failures

If builds fail, check:

1. **Dockerfile syntax**: Ensure Dockerfile is valid
2. **Dependencies**: Verify all dependencies are available
3. **Permissions**: Check repository and workflow permissions
4. **Secrets**: Ensure GITHUB_TOKEN has necessary permissions

### Common Issues

1. **Permission denied**: Check workflow permissions in repository settings
2. **Package not found**: Verify the package was created successfully
3. **Tag conflicts**: Ensure tag names don't conflict with existing ones

### Getting Help

If you encounter issues:

1. Check the [GitHub Actions documentation](https://docs.github.com/en/actions)
2. Review the [GitHub Container Registry documentation](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
3. Check the workflow logs in the Actions tab
4. Open an issue in the repository

## Best Practices

1. **Use semantic versioning** for releases (e.g., v1.0.0, v1.1.0)
2. **Test builds locally** before pushing
3. **Monitor build logs** for warnings or errors
4. **Keep Dockerfile optimized** for faster builds
5. **Document breaking changes** in release notes
