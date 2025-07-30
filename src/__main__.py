#!/usr/bin/env python3
"""
Main entry point for the tf_mcp_server package.
"""

import asyncio
import logging
import sys
from .core.config import Config
from .core.server import run_server


def main():
    """Main entry point for the package."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('tf-mcp-server.log')
        ]
    )
    
    logger = logging.getLogger(__name__)
    
    try:
        # Load configuration from environment
        config = Config.from_env()
        
        logger.info("Starting Azure Terraform MCP Server")
        logger.info(f"Configuration: Host={config.server.host}, Port={config.server.port}")
        
        # Run the server
        asyncio.run(run_server(config))
        
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server failed to start: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
