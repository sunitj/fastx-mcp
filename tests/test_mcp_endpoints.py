"""
Tests for MCP endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from src.main import app


client = TestClient(app)


class TestMCPEndpoints:
    """Test MCP protocol endpoints"""

    def test_mcp_tools_endpoint(self):
        """Test /mcp/tools endpoint returns correct structure"""
        response = client.get("/mcp/tools")
        assert response.status_code == 200
        
        data = response.json()
        assert "tools" in data
        assert "count" in data
        assert "generated_at" in data
        
        # Verify we have tools
        assert isinstance(data["tools"], list)
        assert data["count"] > 0
        assert len(data["tools"]) == data["count"]
        
        # Check first tool has required fields
        if data["tools"]:
            tool = data["tools"][0]
            required_fields = ["name", "description", "method", "path", "input_schema", "output_schema", "tags"]
            for field in required_fields:
                assert field in tool, f"Tool missing required field: {field}"
            
            # Verify schemas are dictionaries
            assert isinstance(tool["input_schema"], dict)
            assert isinstance(tool["output_schema"], dict)
            assert isinstance(tool["tags"], list)

    def test_mcp_manifest_endpoint(self):
        """Test /mcp/manifest endpoint returns correct structure"""
        response = client.get("/mcp/manifest")
        assert response.status_code == 200
        
        data = response.json()
        required_fields = [
            "protocol_version", "server_version", "server_name", 
            "description", "features", "capabilities", "tools_summary", "generated_at"
        ]
        
        for field in required_fields:
            assert field in data, f"Manifest missing required field: {field}"
        
        # Verify specific values
        assert data["protocol_version"] == "2025-06-18"
        assert data["server_name"] == "FastX-MCP"
        assert isinstance(data["capabilities"], dict)
        assert isinstance(data["tools_summary"], dict)

    def test_mcp_status_endpoint(self):
        """Test /mcp/status endpoint returns correct structure"""
        response = client.get("/mcp/status")
        assert response.status_code == 200
        
        data = response.json()
        required_fields = [
            "status", "timestamp", "uptime_seconds", "services", 
            "tools", "system"
        ]
        
        for field in required_fields:
            assert field in data, f"Status missing required field: {field}"
        
        # Verify status is healthy
        assert data["status"] == "healthy"
        
        # Check services structure
        assert "biopython" in data["services"]
        assert "seqkit" in data["services"]
        assert "fastapi" in data["services"]
        
        # Check tools structure
        assert "total" in data["tools"]
        assert "available" in data["tools"]
        assert "disabled" in data["tools"]

    def test_mcp_info_endpoint(self):
        """Test /mcp/info endpoint returns correct structure"""
        response = client.get("/mcp/info")
        assert response.status_code == 200
        
        data = response.json()
        required_fields = [
            "name", "description", "version", "protocol_version",
            "endpoints", "documentation"
        ]
        
        for field in required_fields:
            assert field in data, f"Info missing required field: {field}"
        
        # Verify endpoints structure
        expected_endpoints = ["tools", "manifest", "status", "info"]
        for endpoint in expected_endpoints:
            assert endpoint in data["endpoints"]

    def test_mcp_tools_content_validation(self):
        """Test that tools contain expected tools from our registry"""
        response = client.get("/mcp/tools")
        assert response.status_code == 200
        
        data = response.json()
        tools = data["tools"]
        
        # Get tool names
        tool_names = [tool["name"] for tool in tools]
        
        # Verify expected tools are present
        expected_tools = [
            "genbank_to_fasta",
            "reverse_complement", 
            "extract_subsequence",
            "seqkit_stats",
            "seqkit_command"
        ]
        
        for expected_tool in expected_tools:
            assert expected_tool in tool_names, f"Expected tool {expected_tool} not found"

    def test_mcp_schema_structure(self):
        """Test that tool schemas have expected structure"""
        response = client.get("/mcp/tools")
        assert response.status_code == 200
        
        data = response.json()
        tools = data["tools"]
        
        for tool in tools:
            input_schema = tool["input_schema"]
            output_schema = tool["output_schema"]
            
            # Verify schemas have properties
            if "properties" in input_schema:
                assert isinstance(input_schema["properties"], dict)
            if "properties" in output_schema:
                assert isinstance(output_schema["properties"], dict)
            
            # Verify schemas have type information
            assert "type" in input_schema or "$defs" in input_schema
            assert "type" in output_schema or "$defs" in output_schema

    def test_mcp_manifest_protocol_version(self):
        """Test that manifest uses correct MCP protocol version"""
        response = client.get("/mcp/manifest")
        assert response.status_code == 200
        
        data = response.json()
        assert data["protocol_version"] == "2025-06-18"

    def test_mcp_endpoints_error_handling(self):
        """Test that MCP endpoints handle errors gracefully"""
        # All endpoints should return JSON even on internal errors
        # This test verifies structure exists and endpoints are accessible
        
        endpoints = ["/mcp/tools", "/mcp/manifest", "/mcp/status", "/mcp/info"]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 200
            assert response.headers["content-type"] == "application/json"
            
            # Should be valid JSON
            data = response.json()
            assert isinstance(data, dict)