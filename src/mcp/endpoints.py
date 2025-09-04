"""
MCP Endpoints - FastAPI router for MCP protocol endpoints
"""
import time
from datetime import datetime
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from .registry import get_tools, get_tools_summary
from src.core.seqkit_wrapper import validate_seqkit_installation


router = APIRouter()


@router.get("/tools")
async def get_mcp_tools() -> Dict[str, Any]:
    """
    Get all available tools in MCP-compatible format
    """
    try:
        tools = get_tools()
        return {
            "tools": tools,
            "count": len(tools),
            "generated_at": datetime.utcnow().isoformat() + "Z"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve tools: {str(e)}"
        )


@router.get("/manifest")
async def get_mcp_manifest() -> Dict[str, Any]:
    """
    Get MCP server manifest with protocol version and capabilities
    """
    try:
        # Load config here to avoid circular imports
        import yaml
        import os
        config_path = os.path.join(os.path.dirname(__file__), "../../mcp_config.yaml")
        with open(config_path, "r") as f:
            mcp_config = yaml.safe_load(f)
        
        tools_summary = get_tools_summary()
        
        return {
            "protocol_version": mcp_config["mcp_protocol_version"],
            "server_version": "1.0.0",
            "server_name": "FastX-MCP",
            "description": "MCP Server for FASTA/FASTQ manipulation and file conversion",
            "features": mcp_config.get("features", []),
            "capabilities": {
                "tools": True,
                "logging": True,
                "seqkit_integration": validate_seqkit_installation()
            },
            "tools_summary": tools_summary,
            "generated_at": datetime.utcnow().isoformat() + "Z"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate manifest: {str(e)}"
        )


@router.get("/status")
async def get_mcp_status() -> Dict[str, Any]:
    """
    Get MCP server status and health information
    """
    try:
        seqkit_available = validate_seqkit_installation()
        tools = get_tools()
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "uptime_seconds": time.time(),  # Simplified uptime
            "services": {
                "biopython": True,
                "seqkit": seqkit_available,
                "fastapi": True
            },
            "tools": {
                "total": len(tools),
                "available": len(tools),  # All tools are always available
                "disabled": 0
            },
            "system": {
                "protocol_version": "2025-06-18",
                "server_version": "1.0.0"
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve status: {str(e)}"
        )


@router.get("/info")
async def get_mcp_info() -> Dict[str, Any]:
    """
    Get general information about the MCP server
    """
    try:
        return {
            "name": "FastX-MCP Server",
            "description": "MCP Server for FASTA/FASTQ manipulation and file conversion",
            "version": "1.0.0",
            "protocol_version": "2025-06-18",
            "endpoints": {
                "tools": "/mcp/tools",
                "manifest": "/mcp/manifest", 
                "status": "/mcp/status",
                "info": "/mcp/info"
            },
            "documentation": {
                "openapi": "/docs",
                "redoc": "/redoc"
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve server info: {str(e)}"
        )