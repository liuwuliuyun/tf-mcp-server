# GitHub Authentication for Golang Source Code Provider

The Golang Source Code Provider requires access to GitHub repositories that contain indexed Terraform provider source code. These repositories are maintained by the terraform-mcp-eva project and may require authentication.

## Setting up GitHub Token

1. **Create a GitHub Personal Access Token:**
   - Go to GitHub Settings > Developer settings > Personal access tokens > Tokens (classic)
   - Click "Generate new token (classic)"
   - Select the following scopes:
     - `public_repo` (for accessing public repositories)
     - `repo` (if you need access to private repositories)
   - Set expiration as needed
   - Click "Generate token"

2. **Set Environment Variable:**
   
   **Windows (PowerShell):**
   ```powershell
   $env:GITHUB_TOKEN = "your_github_token_here"
   ```
   
   **Windows (Command Prompt):**
   ```cmd
   set GITHUB_TOKEN=your_github_token_here
   ```
   
   **Linux/macOS:**
   ```bash
   export GITHUB_TOKEN="your_github_token_here"
   ```

3. **Persistent Setup:**
   
   For persistent environment variable setup, add the token to your system environment variables or to your shell profile (`.bashrc`, `.zshrc`, etc.).

## Repositories Used

The provider uses the following indexed repositories:

- **AzureRM Provider:** `lonegunmanb/terraform-provider-azurerm-index`
- **AzAPI Provider:** `lonegunmanb/terraform-provider-azapi-index`

These repositories contain pre-indexed Go source code from:
- https://github.com/hashicorp/terraform-provider-azurerm
- https://github.com/Azure/terraform-provider-azapi

## Troubleshooting

If you encounter authentication errors:

1. **401 Unauthorized:** Set up a GitHub token as described above
2. **403 Rate Limited:** GitHub API has rate limits. A token increases your rate limit
3. **404 Not Found:** The requested source code may not be indexed yet
4. **Network Errors:** Check internet connectivity and GitHub status

## Rate Limits

- **Without token:** 60 requests per hour
- **With token:** 5,000 requests per hour

For production use, always use a GitHub token to avoid rate limiting issues.