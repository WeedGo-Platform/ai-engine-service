"""
Integration of Smart API Tool with V5 AI Engine
Provides seamless API interaction capabilities to the dispensary agent
"""

import asyncio
from typing import Dict, Any, Optional
from tools.smart_api_tool import SmartAPITool
import logging

logger = logging.getLogger(__name__)


class APIToolIntegration:
    """
    Integrates Smart API Tool with V5's tool management system
    Provides conversational API interaction capabilities
    """
    
    def __init__(self):
        self.api_tool = None
        self.current_operation = None
        self.collected_data = {}
        self.conversation_context = {}
        
    async def initialize(self, config: Dict[str, Any] = None):
        """Initialize the API tool with configuration"""
        self.api_tool = SmartAPITool(config=config)
        await self.api_tool.initialize()
        logger.info("API Tool initialized with configuration-driven endpoints")
    
    async def handle_tool_call(self, action: str, **params) -> Dict[str, Any]:
        """
        Main handler for tool calls from V5 engine
        Maps tool actions to API operations
        """
        
        if not self.api_tool:
            return {"error": "API tool not initialized"}
        
        # Route to appropriate handler
        handlers = {
            "discover": self._handle_discover,
            "start_operation": self._handle_start_operation,
            "collect_field": self._handle_collect_field,
            "validate": self._handle_validate,
            "submit": self._handle_submit,
            "get_next_prompt": self._handle_get_next_prompt,
            "cancel": self._handle_cancel,
            "status": self._handle_status
        }
        
        handler = handlers.get(action)
        if not handler:
            return {"error": f"Unknown action: {action}"}
        
        try:
            return await handler(**params)
        except Exception as e:
            logger.error(f"Error handling tool call: {e}")
            return {"error": str(e)}
    
    async def _handle_discover(self, **params) -> Dict[str, Any]:
        """Discover available API operations"""
        operations = self.api_tool.discover_operations()
        
        # Format for easy consumption by LLM
        formatted_ops = []
        for op in operations:
            formatted_ops.append({
                "id": op["operationId"],
                "description": op["summary"] or op["description"],
                "requires_auth": op["requires_auth"],
                "method": op["method"],
                "path": op["path"]
            })
        
        return {
            "operations": formatted_ops,
            "count": len(formatted_ops)
        }
    
    async def _handle_start_operation(self, operation_id: str, **params) -> Dict[str, Any]:
        """Start collecting data for an operation"""
        self.current_operation = operation_id
        self.collected_data = {}
        
        # Get operation schema
        schema = self.api_tool.get_operation_schema(operation_id)
        if not schema:
            return {"error": f"Operation {operation_id} not found"}
        
        # Get required fields
        missing_fields = self.api_tool.get_missing_fields(operation_id, self.collected_data)
        
        return {
            "operation": operation_id,
            "description": schema.get("summary", ""),
            "requires_auth": schema.get("requires_auth", False),
            "fields_needed": len(missing_fields),
            "next_field": missing_fields[0] if missing_fields else None
        }
    
    async def _handle_collect_field(self, field_name: str, value: Any, **params) -> Dict[str, Any]:
        """Collect a field value"""
        if not self.current_operation:
            return {"error": "No operation in progress"}
        
        # Determine if this is a body field or parameter
        schema = self.api_tool.get_operation_schema(self.current_operation)
        is_body_field = False
        
        # Check if it's a body field
        body_spec = schema.get("requestBody", {})
        if body_spec:
            body_schema = body_spec.get("schema", {})
            if body_schema.get("type") == "object":
                props = body_schema.get("properties", {})
                if field_name in props:
                    is_body_field = True
        
        # Store the collected value
        if is_body_field:
            if "body" not in self.collected_data:
                self.collected_data["body"] = {}
            self.collected_data["body"][field_name] = value
        else:
            self.collected_data[field_name] = value
        
        # Check what's still missing
        missing_fields = self.api_tool.get_missing_fields(
            self.current_operation, 
            self.collected_data
        )
        
        return {
            "field": field_name,
            "value": value,
            "accepted": True,
            "fields_remaining": len(missing_fields),
            "next_field": missing_fields[0] if missing_fields else None,
            "ready_to_submit": len(missing_fields) == 0
        }
    
    async def _handle_validate(self, field_name: str = None, value: Any = None, **params) -> Dict[str, Any]:
        """Validate field value or entire collected data"""
        if not self.current_operation:
            return {"error": "No operation in progress"}
        
        if field_name and value is not None:
            # Validate single field
            # Create temporary data with just this field
            temp_data = {field_name: value}
            is_valid, errors = self.api_tool.validate_data(
                self.current_operation,
                temp_data
            )
            return {
                "field": field_name,
                "valid": is_valid,
                "errors": errors
            }
        else:
            # Validate all collected data
            is_valid, errors = self.api_tool.validate_data(
                self.current_operation,
                self.collected_data
            )
            return {
                "valid": is_valid,
                "errors": errors,
                "data": self.collected_data
            }
    
    async def _handle_submit(self, auth_token: str = None, **params) -> Dict[str, Any]:
        """Submit the collected data"""
        if not self.current_operation:
            return {"error": "No operation in progress"}
        
        # Validate before submission
        is_valid, errors = self.api_tool.validate_data(
            self.current_operation,
            self.collected_data
        )
        
        if not is_valid:
            return {
                "error": "Validation failed",
                "validation_errors": errors
            }
        
        # Execute the operation
        result = await self.api_tool.execute_operation(
            self.current_operation,
            self.collected_data,
            auth_token
        )
        
        # Clear state after submission
        if result.get("success"):
            self.current_operation = None
            self.collected_data = {}
        
        return result
    
    async def _handle_get_next_prompt(self, **params) -> Dict[str, Any]:
        """Get a conversational prompt for the next field"""
        if not self.current_operation:
            return {"error": "No operation in progress"}
        
        missing_fields = self.api_tool.get_missing_fields(
            self.current_operation,
            self.collected_data
        )
        
        if not missing_fields:
            return {
                "prompt": "All required information has been collected. Ready to submit!",
                "ready_to_submit": True
            }
        
        next_field = missing_fields[0]
        prompt = self.api_tool.generate_collection_prompt(
            self.current_operation,
            next_field
        )
        
        return {
            "prompt": prompt,
            "field_name": next_field["name"],
            "field_type": next_field["type"],
            "schema": next_field["schema"],
            "fields_remaining": len(missing_fields)
        }
    
    async def _handle_cancel(self, **params) -> Dict[str, Any]:
        """Cancel current operation"""
        self.current_operation = None
        self.collected_data = {}
        return {"status": "cancelled"}
    
    async def _handle_status(self, **params) -> Dict[str, Any]:
        """Get current status"""
        if not self.current_operation:
            return {
                "status": "idle",
                "operation": None,
                "collected_fields": []
            }
        
        missing_fields = self.api_tool.get_missing_fields(
            self.current_operation,
            self.collected_data
        )
        
        return {
            "status": "collecting",
            "operation": self.current_operation,
            "collected_fields": list(self.collected_data.keys()),
            "fields_remaining": len(missing_fields),
            "ready_to_submit": len(missing_fields) == 0
        }
    
    async def cleanup(self):
        """Clean up resources"""
        if self.api_tool:
            await self.api_tool.cleanup()


def register_api_tool_with_v5(tool_manager, config: Dict[str, Any] = None):
    """
    Register the Smart API Tool with V5's tool manager
    
    Args:
        tool_manager: V5's tool manager instance
        config: System configuration dictionary
    """
    integration = APIToolIntegration()
    
    # Initialize asynchronously
    async def init_wrapper():
        await integration.initialize(config=config)
    
    # Run initialization
    asyncio.create_task(init_wrapper())
    
    # Register the tool handler
    async def tool_wrapper(action: str, **kwargs) -> Dict[str, Any]:
        return await integration.handle_tool_call(action, **kwargs)
    
    # Register with tool manager
    tool_manager.register_tool(
        name="api_orchestrator",
        handler=tool_wrapper,
        description="Smart API orchestration for form filling, user registration, orders, etc."
    )
    
    # Also register as individual functions for LLM function calling
    tool_manager.register_tool(
        name="discover_apis",
        handler=lambda **kwargs: integration.handle_tool_call("discover", **kwargs),
        description="Discover available API operations"
    )
    
    tool_manager.register_tool(
        name="start_api_operation",
        handler=lambda **kwargs: integration.handle_tool_call("start_operation", **kwargs),
        description="Start collecting data for an API operation"
    )
    
    tool_manager.register_tool(
        name="collect_api_field",
        handler=lambda **kwargs: integration.handle_tool_call("collect_field", **kwargs),
        description="Collect a field value for the current API operation"
    )
    
    tool_manager.register_tool(
        name="submit_api_operation",
        handler=lambda **kwargs: integration.handle_tool_call("submit", **kwargs),
        description="Submit the collected data to the API"
    )
    
    logger.info("Smart API Tool registered with V5 engine")
    return integration


# Example usage in conversation flow
"""
User: "I want to create an account"

AI: [Calls discover_apis to find registerUser operation]
AI: [Calls start_api_operation with operation_id="registerUser"]
AI: "I'll help you create an account. What's your email address?"

User: "john.doe@example.com"

AI: [Calls collect_api_field with field_name="email", value="john.doe@example.com"]
AI: "Great! Now I need your first name."

User: "John"

AI: [Calls collect_api_field with field_name="first_name", value="John"]
AI: "Thanks John! What's your last name?"

... (continues collecting required fields)

AI: [Calls submit_api_operation when all fields are collected]
AI: "Perfect! Your account has been created successfully."
"""