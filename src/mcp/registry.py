"""
MCP Tool Registry - Static mapping of available tools and their schemas
"""
from typing import Dict, List, Any

from src.api.convert import GenBankToFastaRequest, GenBankToFastaResponse
from src.api.manipulate import ReverseComplementRequest, ReverseComplementResponse, SubsequenceRequest, SubsequenceResponse
from src.api.seqkit import SeqkitStatsRequest, SeqkitStatsResponse, SeqkitCommandRequest, SeqkitCommandResponse


def get_tool_schema(model_class) -> Dict[str, Any]:
    """Get JSON schema for a Pydantic model"""
    return model_class.model_json_schema()


def get_tools() -> List[Dict[str, Any]]:
    """Return list of all available tools with their MCP-compatible descriptors"""
    tools = [
        {
            "name": "genbank_to_fasta",
            "description": "Convert GenBank format files to FASTA format with optional summary statistics",
            "method": "POST",
            "path": "/convert/genbank-to-fasta",
            "input_schema": get_tool_schema(GenBankToFastaRequest),
            "output_schema": get_tool_schema(GenBankToFastaResponse),
            "tags": ["conversion", "genbank", "fasta"]
        },
        {
            "name": "reverse_complement",
            "description": "Generate reverse complement of all sequences in a FASTA file",
            "method": "POST", 
            "path": "/manipulate/reverse-complement",
            "input_schema": get_tool_schema(ReverseComplementRequest),
            "output_schema": get_tool_schema(ReverseComplementResponse),
            "tags": ["manipulation", "fasta", "reverse-complement"]
        },
        {
            "name": "extract_subsequence",
            "description": "Extract subsequence by coordinates from a specific sequence in FASTA file",
            "method": "POST",
            "path": "/manipulate/extract-subsequence", 
            "input_schema": get_tool_schema(SubsequenceRequest),
            "output_schema": get_tool_schema(SubsequenceResponse),
            "tags": ["manipulation", "fasta", "subsequence"]
        },
        {
            "name": "seqkit_stats",
            "description": "Generate FASTQ statistics using seqkit stats command",
            "method": "POST",
            "path": "/seqkit/stats",
            "input_schema": get_tool_schema(SeqkitStatsRequest),
            "output_schema": get_tool_schema(SeqkitStatsResponse),
            "tags": ["seqkit", "statistics", "fastq"]
        },
        {
            "name": "seqkit_command", 
            "description": "Run custom seqkit commands on FASTQ files",
            "method": "POST",
            "path": "/seqkit/command",
            "input_schema": get_tool_schema(SeqkitCommandRequest),
            "output_schema": get_tool_schema(SeqkitCommandResponse),
            "tags": ["seqkit", "command", "fastq"]
        }
    ]
    
    return tools


def get_tool_by_name(name: str) -> Dict[str, Any]:
    """Get a specific tool by name"""
    tools = get_tools()
    for tool in tools:
        if tool["name"] == name:
            return tool
    raise ValueError(f"Tool '{name}' not found")


def get_tools_summary() -> Dict[str, Any]:
    """Get summary information about available tools"""
    tools = get_tools()
    
    return {
        "total_tools": len(tools),
        "tools_by_category": {
            "conversion": len([t for t in tools if "conversion" in t["tags"]]),
            "manipulation": len([t for t in tools if "manipulation" in t["tags"]]),
            "seqkit": len([t for t in tools if "seqkit" in t["tags"]])
        },
        "supported_formats": {
            "input": ["string", "base64"],
            "sequence_types": ["FASTA", "FASTQ", "GenBank"]
        }
    }