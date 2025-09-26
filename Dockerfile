# Use a minimal base image with Python 3
FROM mcr.microsoft.com/azurelinux/base/python:3

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    MCP_SERVER_HOST=0.0.0.0 \
    MCP_SERVER_PORT=8000 \
    LOG_LEVEL=INFO \
    MCP_WORKSPACE_ROOT=/workspace

# Install system dependencies
RUN tdnf update -y && tdnf install -y \
    curl \
    unzip \
    wget \
    git \
    ca-certificates \
    jq \
    tar \
    net-tools \
    shadow-utils \
    && tdnf clean all

# Install Terraform (latest version)
RUN TERRAFORM_VERSION=$(curl -s "https://api.github.com/repos/hashicorp/terraform/releases/latest" | jq -r '.tag_name' | cut -c 2-) \
    && ARCH=$(uname -m) \
    && if [ "$ARCH" = "x86_64" ]; then ARCH="amd64"; elif [ "$ARCH" = "aarch64" ]; then ARCH="arm64"; fi \
    && curl -fsSL https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_${ARCH}.zip -o terraform.zip \
    && unzip terraform.zip \
    && mv terraform /usr/local/bin/ \
    && rm terraform.zip \
    && terraform version

# Install Azure Export for Terraform (aztfexport) from GitHub releases (latest version)
RUN AZTFEXPORT_VERSION=$(curl -s "https://api.github.com/repos/Azure/aztfexport/releases/latest" | jq -r '.tag_name' | cut -c 2-) \
    && ARCH=$(uname -m) \
    && if [ "$ARCH" = "x86_64" ]; then ARCH="amd64"; elif [ "$ARCH" = "aarch64" ]; then ARCH="arm64"; fi \
    && curl -fsSL "https://github.com/Azure/aztfexport/releases/download/v${AZTFEXPORT_VERSION}/aztfexport_v${AZTFEXPORT_VERSION}_linux_${ARCH}.zip" -o aztfexport.zip \
    && unzip aztfexport.zip \
    && mv aztfexport /usr/local/bin/ \
    && rm aztfexport.zip \
    && aztfexport --version

# Install TFLint
RUN curl -s https://raw.githubusercontent.com/terraform-linters/tflint/master/install_linux.sh | bash
RUN tflint --version


# Install Conftest (latest version)
RUN CONFTEST_VERSION=$(curl -s "https://api.github.com/repos/open-policy-agent/conftest/releases/latest" | jq -r '.tag_name' | cut -c 2-) \
    && ARCH=$(uname -m) \
    && if [ "$ARCH" = "x86_64" ]; then ARCH="x86_64"; elif [ "$ARCH" = "aarch64" ]; then ARCH="arm64"; fi \
    && SYSTEM=$(uname) \
    && wget "https://github.com/open-policy-agent/conftest/releases/download/v${CONFTEST_VERSION}/conftest_${CONFTEST_VERSION}_${SYSTEM}_${ARCH}.tar.gz" \
    && tar xzf conftest_${CONFTEST_VERSION}_${SYSTEM}_${ARCH}.tar.gz \
    && mv conftest /usr/local/bin \
    && rm conftest_${CONFTEST_VERSION}_${SYSTEM}_${ARCH}.tar.gz \
    && conftest --version

# Create non-root user for security
RUN groupadd -r mcpuser && useradd -r -g mcpuser mcpuser

# Set work directory
WORKDIR /app

# Copy project files
COPY . /app

# Create workspace directory
RUN mkdir -p "$MCP_WORKSPACE_ROOT"

# Mark the workspace as a mount point so users can bind their host directories easily
VOLUME ["$MCP_WORKSPACE_ROOT"]

# Install UV package manager for faster dependency resolution
RUN pip install uv

# Create directories for logs and health checks
RUN mkdir -p /app/logs /app/health /home/mcpuser/

# Set proper ownership and permissions for the app directory first
RUN chown -R mcpuser:mcpuser /app /home/mcpuser "$MCP_WORKSPACE_ROOT" \
    && chmod 755 /app/logs /app/health "$MCP_WORKSPACE_ROOT"

# Switch to non-root user before installing dependencies
USER mcpuser

# Install Python dependencies using uv as the mcpuser
RUN uv sync

# Expose the default port (can be overridden with environment variables)
EXPOSE $MCP_SERVER_PORT

# Add health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD netstat -an | grep :${MCP_SERVER_PORT:-8000} | grep LISTEN || exit 1

# Start the server
CMD ["uv", "run", "tf-mcp-server"]
