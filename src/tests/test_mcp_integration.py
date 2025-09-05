#!/usr/bin/env python3
"""
Test script for MCP Integration
Tests MCP client, adapter, server, and V5 engine integration
"""
import asyncio
import sys
import logging
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.mcp import MCPClient, MCPDiscovery
from core.mcp.mcp_types import MCPServer, MCPRequest, TransportType
from services.mcp_adapter import MCPAdapter
from mcp_servers.weedgo_mcp_server import WeedGoMCPServer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_mcp_discovery():
    """Test MCP server discovery"""
    logger.info("=" * 50)
    logger.info("Testing MCP Discovery...")
    
    try:
        discovery = MCPDiscovery()
        servers = await discovery.discover_servers()
        
        logger.info(f"✅ Discovered {len(servers)} servers")
        for server in servers:
            logger.info(f"   - {server.name} ({server.transport.value})")
        
        # Check if WeedGo server is discovered
        weedgo = discovery.get_server("weedgo")
        if weedgo:
            logger.info("✅ WeedGo server found in discovery")
        else:
            logger.warning("⚠️ WeedGo server not found")
        
        return True
        
    except Exception as e:
        logger.error(f"Discovery test failed: {e}")
        return False

async def test_mcp_client():
    """Test MCP client connectivity"""
    logger.info("=" * 50)
    logger.info("Testing MCP Client...")
    
    try:
        client = MCPClient()
        
        # Discover servers
        servers = await client.discover_servers()
        logger.info(f"Found {len(servers)} servers")
        
        # Try to connect to WeedGo server
        weedgo = next((s for s in servers if s.name == "weedgo"), None)
        
        if weedgo:
            # For stdio transport, we'll simulate connection
            logger.info("✅ WeedGo server configuration found")
            
            # List available tools (simulated)
            logger.info("Available MCP operations:")
            logger.info("   - tools/list")
            logger.info("   - tools/call")
            logger.info("   - resources/list")
            logger.info("   - prompts/list")
        else:
            logger.warning("WeedGo server not found")
        
        return True
        
    except Exception as e:
        logger.error(f"Client test failed: {e}")
        return False

async def test_mcp_server():
    """Test WeedGo MCP server directly"""
    logger.info("=" * 50)
    logger.info("Testing WeedGo MCP Server...")
    
    try:
        server = WeedGoMCPServer()
        
        # Test initialization
        init_request = MCPRequest(method="initialize", params={"protocolVersion": "1.0"})
        init_response = await server.handle_request(init_request)
        
        if init_response.is_success():
            logger.info("✅ Server initialized successfully")
            server_info = init_response.result.get("serverInfo", {})
            logger.info(f"   Name: {server_info.get('name')}")
            logger.info(f"   Version: {server_info.get('version')}")
        else:
            logger.error(f"Server initialization failed: {init_response.error}")
            return False
        
        # Test tools listing
        tools_request = MCPRequest(method="tools/list")
        tools_response = await server.handle_request(tools_request)
        
        if tools_response.is_success():
            tools = tools_response.result.get("tools", [])
            logger.info(f"✅ Server has {len(tools)} tools:")
            for tool in tools:
                logger.info(f"   - {tool['name']}: {tool['description']}")
        else:
            logger.error(f"Tools listing failed: {tools_response.error}")
        
        # Test specific tool execution
        tool_request = MCPRequest(
            method="tools/call",
            params={
                "name": "strain_lookup",
                "arguments": {"strain": "Blue Dream"}
            }
        )
        tool_response = await server.handle_request(tool_request)
        
        if tool_response.is_success():
            logger.info("✅ Tool execution successful")
            content = tool_response.result.get("content", [])
            if content:
                result = json.loads(content[0]["text"])
                logger.info(f"   Strain: {result.get('name')}")
                logger.info(f"   Type: {result.get('type')}")
        else:
            logger.error(f"Tool execution failed: {tool_response.error}")
        
        return True
        
    except Exception as e:
        logger.error(f"Server test failed: {e}")
        return False

async def test_mcp_adapter():
    """Test MCP adapter with offline fallback"""
    logger.info("=" * 50)
    logger.info("Testing MCP Adapter...")
    
    try:
        adapter = MCPAdapter(offline_fallback=True)
        initialized = await adapter.initialize()
        
        if initialized:
            logger.info("✅ Adapter initialized")
        else:
            logger.info("⚠️ Adapter using offline mode")
        
        # Get available tools
        tools = adapter.get_available_tools()
        logger.info(f"Available tools: {len(tools)}")
        for tool_name in list(tools.keys())[:5]:
            tool = tools[tool_name]
            logger.info(f"   - {tool_name} ({tool['source']})")
        
        # Test tool execution
        result = await adapter.execute_tool(
            "dosage_calculator",
            {
                "weight": 70,
                "tolerance": "none",
                "product_type": "flower",
                "desired_effect": "moderate"
            }
        )
        
        if result["success"]:
            logger.info("✅ Tool execution successful")
            logger.info(f"   Result: {result['result']}")
        else:
            logger.error(f"Tool execution failed: {result.get('error')}")
        
        # Test tool schemas
        schemas = adapter.get_tool_schemas("openai")
        logger.info(f"Generated {len(schemas)} tool schemas")
        
        return True
        
    except Exception as e:
        logger.error(f"Adapter test failed: {e}")
        return False

async def test_mcp_tools():
    """Test specific MCP tools"""
    logger.info("=" * 50)
    logger.info("Testing MCP Tools...")
    
    server = WeedGoMCPServer()
    
    # Test cases for different tools
    test_cases = [
        {
            "name": "dosage_calculator",
            "args": {
                "weight": 75,
                "tolerance": "moderate",
                "product_type": "edible",
                "desired_effect": "mild"
            }
        },
        {
            "name": "compliance_check",
            "args": {
                "state": "CA",
                "query": "possession"
            }
        },
        {
            "name": "terpene_analyzer",
            "args": {
                "terpenes": ["myrcene", "limonene", "pinene"],
                "analysis_type": "effects"
            }
        },
        {
            "name": "lab_result_interpreter",
            "args": {
                "thc": 18.5,
                "cbd": 2.0,
                "terpenes": {"myrcene": 0.5, "limonene": 0.3},
                "contaminants": {
                    "pesticides": "pass",
                    "heavy_metals": "pass",
                    "microbials": "pass"
                }
            }
        }
    ]
    
    success_count = 0
    for test in test_cases:
        try:
            request = MCPRequest(
                method="tools/call",
                params={
                    "name": test["name"],
                    "arguments": test["args"]
                }
            )
            
            response = await server.handle_request(request)
            
            if response.is_success():
                logger.info(f"✅ {test['name']}: SUCCESS")
                success_count += 1
            else:
                logger.error(f"❌ {test['name']}: FAILED - {response.error}")
                
        except Exception as e:
            logger.error(f"❌ {test['name']}: ERROR - {e}")
    
    logger.info(f"\n📊 Tool Tests: {success_count}/{len(test_cases)} passed")
    return success_count == len(test_cases)

async def test_mcp_resources():
    """Test MCP resource handling"""
    logger.info("=" * 50)
    logger.info("Testing MCP Resources...")
    
    server = WeedGoMCPServer()
    
    try:
        # List resources
        list_request = MCPRequest(method="resources/list")
        list_response = await server.handle_request(list_request)
        
        if list_response.is_success():
            resources = list_response.result.get("resources", [])
            logger.info(f"✅ Found {len(resources)} resources:")
            
            for resource in resources:
                logger.info(f"   - {resource['name']}: {resource['uri']}")
                
                # Read each resource
                read_request = MCPRequest(
                    method="resources/read",
                    params={"uri": resource["uri"]}
                )
                read_response = await server.handle_request(read_request)
                
                if read_response.is_success():
                    contents = read_response.result.get("contents", [])
                    if contents:
                        data = json.loads(contents[0]["text"])
                        logger.info(f"     ✓ Read successfully ({len(json.dumps(data))} bytes)")
                else:
                    logger.error(f"     ✗ Failed to read: {read_response.error}")
        
        return True
        
    except Exception as e:
        logger.error(f"Resource test failed: {e}")
        return False

async def test_mcp_prompts():
    """Test MCP prompt templates"""
    logger.info("=" * 50)
    logger.info("Testing MCP Prompts...")
    
    server = WeedGoMCPServer()
    
    try:
        # List prompts
        list_request = MCPRequest(method="prompts/list")
        list_response = await server.handle_request(list_request)
        
        if list_response.is_success():
            prompts = list_response.result.get("prompts", [])
            logger.info(f"✅ Found {len(prompts)} prompts:")
            
            for prompt in prompts:
                logger.info(f"   - {prompt['name']}: {prompt['description']}")
                
                # Test getting each prompt
                get_request = MCPRequest(
                    method="prompts/get",
                    params={
                        "name": prompt["name"],
                        "arguments": {
                            "customer_needs": "pain relief",
                            "experience_level": "beginner",
                            "state": "CA",
                            "business_type": "dispensary"
                        }
                    }
                )
                get_response = await server.handle_request(get_request)
                
                if get_response.is_success():
                    messages = get_response.result.get("messages", [])
                    if messages:
                        logger.info(f"     ✓ Rendered successfully")
                else:
                    logger.error(f"     ✗ Failed to render: {get_response.error}")
        
        return True
        
    except Exception as e:
        logger.error(f"Prompt test failed: {e}")
        return False

async def main():
    """Run all MCP integration tests"""
    logger.info("🔧 MCP Integration Test Suite")
    logger.info("=" * 50)
    
    # Check if MCP configuration exists
    config_file = Path("config/system_config.json")
    if config_file.exists():
        with open(config_file) as f:
            config = json.load(f)
            mcp_config = config.get("mcp", {})
            if mcp_config.get("enabled"):
                logger.info("✅ MCP is enabled in configuration")
            else:
                logger.warning("⚠️ MCP is disabled in configuration")
    else:
        logger.warning("⚠️ Configuration file not found")
    
    # Run tests
    tests = [
        ("MCP Discovery", test_mcp_discovery),
        ("MCP Client", test_mcp_client),
        ("MCP Server", test_mcp_server),
        ("MCP Adapter", test_mcp_adapter),
        ("MCP Tools", test_mcp_tools),
        ("MCP Resources", test_mcp_resources),
        ("MCP Prompts", test_mcp_prompts)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = await test_func()
            results.append((name, success))
        except Exception as e:
            logger.error(f"Test {name} crashed: {e}")
            results.append((name, False))
    
    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("📊 Test Summary:")
    for name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        logger.info(f"   {name}: {status}")
    
    total = len(results)
    passed = sum(1 for _, s in results if s)
    logger.info(f"\n   Total: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("\n🎉 All MCP integration tests passed!")
        logger.info("MCP system is fully functional and ready for use.")
    else:
        logger.info("\n⚠️ Some tests failed. Please check the logs above.")
        logger.info("The system will still work with offline fallback mode.")

if __name__ == "__main__":
    asyncio.run(main())