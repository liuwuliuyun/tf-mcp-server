# Use a minimal base image with Python 3
FROM mcr.microsoft.com/azurelinux/base/python:3

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    MCP_SERVER_HOST=0.0.0.0 \
    MCP_SERVER_PORT=8000 \
    LOG_LEVEL=INFO

# Install system dependencies
RUN tdnf update && tdnf install -y \
    curl \
    unzip \
    wget \
    git \
    ca-certificates \
    jq \
    tar \
    && tdnf clean all

# Install Terraform (latest version)
RUN TERRAFORM_VERSION=$(curl -s "https://api.github.com/repos/hashicorp/terraform/releases/latest" | jq -r '.tag_name' | cut -c 2-) \
    && curl -fsSL https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_amd64.zip -o terraform.zip \
    && unzip terraform.zip \
    && mv terraform /usr/local/bin/ \
    && rm terraform.zip \
    && terraform version

# Install TFLint
RUN curl -s https://raw.githubusercontent.com/terraform-linters/tflint/master/install_linux.sh | bash
RUN tflint --version


# Install Conftest (latest version)
RUN CONFTEST_VERSION=$(curl -s "https://api.github.com/repos/open-policy-agent/conftest/releases/latest" | jq -r '.tag_name' | cut -c 2-) \
    && ARCH=$(arch) \
    && SYSTEM=$(uname) \
    && wget "https://github.com/open-policy-agent/conftest/releases/download/v${CONFTEST_VERSION}/conftest_${CONFTEST_VERSION}_${SYSTEM}_${ARCH}.tar.gz" \
    && tar xzf conftest_${CONFTEST_VERSION}_${SYSTEM}_${ARCH}.tar.gz \
    && mv conftest /usr/local/bin \
    && rm conftest_${CONFTEST_VERSION}_${SYSTEM}_${ARCH}.tar.gz \
    && conftest --version

# Set work directory
WORKDIR /app

# Copy project files
COPY . /app

# Install UV package manager for faster dependency resolution
RUN pip install uv

# Install Python dependencies using uv
RUN uv sync

# Create directories for logs and health checks
RUN mkdir -p /app/logs /app/health

# Expose the default port (can be overridden with environment variables)
EXPOSE 8000

# Start the server
CMD ["uv", "run", "tf-mcp-server"]
