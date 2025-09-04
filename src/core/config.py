"""
Configuration utilities for FastX-MCP Server
"""
import os
import yaml
from pathlib import Path


def get_mcp_config_path() -> str:
    """
    Get the path to the MCP configuration file.
    
    Checks environment variable MCP_CONFIG_PATH first,
    falls back to default location relative to project root.
    
    Returns:
        str: Path to the MCP configuration file
    """
    config_path = os.environ.get("MCP_CONFIG_PATH")
    if config_path:
        return config_path
    
    # Default to project root
    project_root = Path(__file__).parent.parent.parent
    return str(project_root / "mcp_config.yaml")


def load_mcp_config() -> dict:
    """
    Load MCP configuration from file.
    
    Returns:
        dict: MCP configuration
    """
    config_path = get_mcp_config_path()
    with open(config_path, "r") as f:
        return yaml.safe_load(f)