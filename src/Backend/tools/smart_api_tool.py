"""
Smart API Tool for V5 AI Engine
Dynamic API discovery and intelligent form filling using OpenAPI specifications
Industry-standard approach with LLM-native integration
"""

import json
import yaml
import asyncio
import aiohttp
import os
from typing import Dict, Any, List, Optional, Callable, Tuple
from dataclasses import dataclass
from enum import Enum
import jsonschema
from jsonschema import validate, ValidationError
import logging
from functools import lru_cache

logger = logging.getLogger(__name__)


class SmartAPITool:
    """
    Production-grade API interaction tool that:
    1. Discovers APIs via OpenAPI/Swagger specs
    2. Dynamically understands schemas
    3. Guides conversational data collection
    4. Handles auth, retries, and errors gracefully
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize with configuration
        
        Args:
            config: System configuration dictionary
        """
        self.config = config or self._load_config()
        self.api_config = self.config.get('api', {})
        self.gateway_config = self.api_config.get('gateway', {})
        self.endpoints_config = self.api_config.get('endpoints', {})
        
        # Get gateway URL from config or environment
        self.base_url = os.environ.get(
            'WEEDGO_API_GATEWAY_URL',
            self.gateway_config.get('base_url', 'http://localhost:8000')
        )
        
        # Get OpenAPI spec URL from config
        spec_path = self.gateway_config.get('openapi_spec_path', '/openapi.json')
        self.spec_url = f"{self.base_url}{spec_path}"
        
        self.local_spec_path = self.api_config.get('local_spec_path')
        self.openapi_spec = None
        self.session = None
        self.auth_token = None
        self.conversation_state = {}
        self.collected_params = {}
        self.endpoint_prompts = None
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from system_config.json"""
        config_paths = [
            'config/system_config.json',
            '../config/system_config.json',
            'system_config.json'
        ]
        
        for path in config_paths:
            try:
                with open(path, 'r') as f:
                    return json.load(f)
            except FileNotFoundError:
                continue
        
        logger.warning("Could not find system_config.json, using defaults")
        return {}
    
    async def initialize(self):
        """Load and parse OpenAPI specification and prompts"""
        # Load endpoint prompts
        self._load_endpoint_prompts()
        
        # Load OpenAPI spec
        if self.api_config.get('endpoint_discovery', {}).get('enabled', True):
            await self._load_remote_spec()
        elif self.local_spec_path:
            self._load_local_spec()
        else:
            # Use configuration-based spec
            self._create_spec_from_config()
    
    def _load_endpoint_prompts(self):
        """Load endpoint behavior prompts"""
        try:
            prompts_path = 'prompts/endpoint_prompts.json'
            with open(prompts_path, 'r') as f:
                self.endpoint_prompts = json.load(f)
                logger.info("Loaded endpoint prompts for intelligent form filling")
        except Exception as e:
            logger.warning(f"Could not load endpoint prompts: {e}")
            self.endpoint_prompts = {}
    
    async def _load_remote_spec(self):
        """Load OpenAPI spec from URL"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            async with self.session.get(self.spec_url) as response:
                if response.status == 200:
                    content_type = response.headers.get('content-type', '')
                    if 'yaml' in content_type:
                        text = await response.text()
                        self.openapi_spec = yaml.safe_load(text)
                    else:
                        self.openapi_spec = await response.json()
                    logger.info(f"Loaded OpenAPI spec from {self.spec_url}")
        except Exception as e:
            logger.error(f"Failed to load remote spec: {e}")
            self._create_default_spec()
    
    def _load_local_spec(self):
        """Load OpenAPI spec from local file"""
        try:
            with open(self.local_spec_path, 'r') as f:
                if self.local_spec_path.endswith('.yaml') or self.local_spec_path.endswith('.yml'):
                    self.openapi_spec = yaml.safe_load(f)
                else:
                    self.openapi_spec = json.load(f)
            logger.info(f"Loaded OpenAPI spec from {self.local_spec_path}")
        except Exception as e:
            logger.error(f"Failed to load local spec: {e}")
            self._create_default_spec()
    
    def _create_spec_from_config(self):
        """Create OpenAPI spec from configuration"""
        self.openapi_spec = {
            "openapi": "3.0.0",
            "info": {
                "title": "WeedGo API (Configuration-Based)",
                "version": "1.0.0"
            },
            "servers": [
                {"url": self.base_url}
            ],
            "paths": {
                "/users/register": {
                    "post": {
                        "operationId": "registerUser",
                        "summary": "Register a new user",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/UserRegistration"
                                    }
                                }
                            }
                        },
                        "responses": {
                            "201": {
                                "description": "User created successfully"
                            }
                        }
                    }
                },
                "/orders": {
                    "post": {
                        "operationId": "createOrder",
                        "summary": "Create a new order",
                        "security": [{"bearerAuth": []}],
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/OrderCreation"
                                    }
                                }
                            }
                        }
                    }
                },
                "/products/search": {
                    "get": {
                        "operationId": "searchProducts",
                        "summary": "Search for products",
                        "parameters": [
                            {
                                "name": "query",
                                "in": "query",
                                "schema": {"type": "string"}
                            },
                            {
                                "name": "category",
                                "in": "query",
                                "schema": {
                                    "type": "string",
                                    "enum": ["flower", "edibles", "concentrates", "topicals"]
                                }
                            },
                            {
                                "name": "min_price",
                                "in": "query",
                                "schema": {"type": "number", "minimum": 0}
                            },
                            {
                                "name": "max_price",
                                "in": "query",
                                "schema": {"type": "number", "minimum": 0}
                            }
                        ]
                    }
                }
            },
            "components": {
                "schemas": {
                    "UserRegistration": {
                        "type": "object",
                        "required": ["email", "password", "first_name", "last_name", "date_of_birth"],
                        "properties": {
                            "email": {
                                "type": "string",
                                "format": "email",
                                "description": "User's email address"
                            },
                            "password": {
                                "type": "string",
                                "minLength": 8,
                                "description": "Password (min 8 characters)"
                            },
                            "first_name": {
                                "type": "string",
                                "description": "User's first name"
                            },
                            "last_name": {
                                "type": "string",
                                "description": "User's last name"
                            },
                            "date_of_birth": {
                                "type": "string",
                                "format": "date",
                                "description": "Date of birth (YYYY-MM-DD)"
                            },
                            "phone": {
                                "type": "string",
                                "pattern": "^\\+?[1-9]\\d{1,14}$",
                                "description": "Phone number"
                            },
                            "address": {
                                "type": "object",
                                "properties": {
                                    "street": {"type": "string"},
                                    "city": {"type": "string"},
                                    "province": {"type": "string"},
                                    "postal_code": {"type": "string"}
                                }
                            }
                        }
                    },
                    "OrderCreation": {
                        "type": "object",
                        "required": ["items", "delivery_method"],
                        "properties": {
                            "items": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "product_id": {"type": "string"},
                                        "quantity": {"type": "integer", "minimum": 1}
                                    }
                                }
                            },
                            "delivery_method": {
                                "type": "string",
                                "enum": ["pickup", "delivery"]
                            },
                            "delivery_address": {
                                "type": "string",
                                "description": "Required if delivery_method is 'delivery'"
                            },
                            "notes": {
                                "type": "string"
                            }
                        }
                    }
                },
                "securitySchemes": {
                    "bearerAuth": {
                        "type": "http",
                        "scheme": "bearer"
                    }
                }
            }
        }
    
    @lru_cache(maxsize=128)
    def discover_operations(self) -> List[Dict[str, Any]]:
        """
        Discover all available operations from OpenAPI spec
        Returns list of operations with their details
        """
        if not self.openapi_spec:
            return []
        
        operations = []
        paths = self.openapi_spec.get("paths", {})
        
        for path, methods in paths.items():
            for method, details in methods.items():
                if method in ["get", "post", "put", "delete", "patch"]:
                    operation = {
                        "operationId": details.get("operationId", f"{method}_{path}"),
                        "path": path,
                        "method": method.upper(),
                        "summary": details.get("summary", ""),
                        "description": details.get("description", ""),
                        "requires_auth": bool(details.get("security")),
                        "parameters": self._extract_parameters(details),
                        "requestBody": self._extract_request_body(details)
                    }
                    operations.append(operation)
        
        return operations
    
    def _extract_parameters(self, operation_details: Dict) -> List[Dict]:
        """Extract and process parameters from operation"""
        params = []
        for param in operation_details.get("parameters", []):
            params.append({
                "name": param.get("name"),
                "in": param.get("in"),  # query, path, header, cookie
                "required": param.get("required", False),
                "schema": param.get("schema", {}),
                "description": param.get("description", "")
            })
        return params
    
    def _extract_request_body(self, operation_details: Dict) -> Optional[Dict]:
        """Extract request body schema"""
        request_body = operation_details.get("requestBody")
        if not request_body:
            return None
        
        content = request_body.get("content", {})
        json_content = content.get("application/json", {})
        schema = json_content.get("schema", {})
        
        # Resolve $ref if present
        if "$ref" in schema:
            schema = self._resolve_ref(schema["$ref"])
        
        return {
            "required": request_body.get("required", False),
            "schema": schema
        }
    
    def _resolve_ref(self, ref: str) -> Dict:
        """Resolve $ref references in OpenAPI spec"""
        # ref format: "#/components/schemas/UserRegistration"
        parts = ref.split("/")
        schema = self.openapi_spec
        for part in parts[1:]:  # Skip the '#'
            schema = schema.get(part, {})
        return schema
    
    def get_operation_schema(self, operation_id: str) -> Dict[str, Any]:
        """
        Get detailed schema for a specific operation
        This is what the LLM uses to understand what data to collect
        """
        operations = self.discover_operations()
        for op in operations:
            if op["operationId"] == operation_id:
                return op
        return {}
    
    def validate_data(self, operation_id: str, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate data against operation schema
        Returns (is_valid, error_messages)
        """
        schema = self.get_operation_schema(operation_id)
        if not schema:
            return False, ["Operation not found"]
        
        errors = []
        
        # Validate parameters
        for param in schema.get("parameters", []):
            if param["required"] and param["name"] not in data:
                errors.append(f"Missing required parameter: {param['name']}")
            elif param["name"] in data:
                # Validate against schema
                try:
                    validate(instance=data[param["name"]], schema=param["schema"])
                except ValidationError as e:
                    errors.append(f"{param['name']}: {e.message}")
        
        # Validate request body
        body_spec = schema.get("requestBody")
        if body_spec and body_spec["required"]:
            if "body" not in data:
                errors.append("Missing required request body")
            else:
                try:
                    validate(instance=data["body"], schema=body_spec["schema"])
                except ValidationError as e:
                    errors.append(f"Request body: {e.message}")
        
        return len(errors) == 0, errors
    
    async def execute_operation(
        self,
        operation_id: str,
        data: Dict[str, Any],
        auth_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute an API operation with the provided data
        Handles auth, retries, and error recovery
        """
        schema = self.get_operation_schema(operation_id)
        if not schema:
            return {"error": "Operation not found"}
        
        # Validate data first
        is_valid, errors = self.validate_data(operation_id, data)
        if not is_valid:
            return {"error": "Validation failed", "errors": errors}
        
        # Build request
        servers = self.openapi_spec.get("servers", [])
        base_url = servers[0]["url"] if servers else "http://localhost:8000"
        url = base_url + schema["path"]
        
        # Replace path parameters
        for param in schema.get("parameters", []):
            if param["in"] == "path":
                url = url.replace(f"{{{param['name']}}}", str(data.get(param["name"], "")))
        
        # Prepare headers
        headers = {"Content-Type": "application/json"}
        if schema["requires_auth"]:
            headers["Authorization"] = f"Bearer {auth_token or self.auth_token}"
        
        # Prepare query params and body
        query_params = {}
        for param in schema.get("parameters", []):
            if param["in"] == "query" and param["name"] in data:
                query_params[param["name"]] = data[param["name"]]
        
        body = data.get("body")
        
        # Execute request with retry logic
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        for attempt in range(3):
            try:
                async with self.session.request(
                    method=schema["method"],
                    url=url,
                    params=query_params if query_params else None,
                    json=body if body else None,
                    headers=headers,
                    timeout=30
                ) as response:
                    response_data = await response.json()
                    
                    if response.status in [200, 201]:
                        return {
                            "success": True,
                            "data": response_data,
                            "status": response.status
                        }
                    elif response.status == 400:
                        return {
                            "error": "Bad request",
                            "details": response_data,
                            "status": response.status
                        }
                    elif response.status == 401:
                        return {
                            "error": "Authentication required",
                            "status": response.status
                        }
                    elif response.status == 429:
                        # Rate limited, wait and retry
                        retry_after = int(response.headers.get("Retry-After", 60))
                        if attempt < 2:
                            await asyncio.sleep(retry_after)
                            continue
                        return {
                            "error": "Rate limited",
                            "retry_after": retry_after,
                            "status": response.status
                        }
                    elif response.status >= 500:
                        # Server error, retry with exponential backoff
                        if attempt < 2:
                            await asyncio.sleep(2 ** attempt)
                            continue
                        return {
                            "error": "Server error",
                            "status": response.status
                        }
                    else:
                        return {
                            "error": f"Unexpected status: {response.status}",
                            "data": response_data,
                            "status": response.status
                        }
                        
            except asyncio.TimeoutError:
                if attempt < 2:
                    continue
                return {"error": "Request timeout"}
            except Exception as e:
                return {"error": f"Request failed: {str(e)}"}
        
        return {"error": "All retry attempts failed"}
    
    def get_missing_fields(self, operation_id: str, collected_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Determine what fields are still needed for an operation
        Returns list of missing fields with their schemas
        """
        schema = self.get_operation_schema(operation_id)
        if not schema:
            return []
        
        missing = []
        
        # Check parameters
        for param in schema.get("parameters", []):
            if param["required"] and param["name"] not in collected_data:
                missing.append({
                    "name": param["name"],
                    "type": "parameter",
                    "schema": param["schema"],
                    "description": param["description"]
                })
        
        # Check request body fields
        body_spec = schema.get("requestBody")
        if body_spec and body_spec["required"]:
            body_schema = body_spec["schema"]
            if body_schema.get("type") == "object":
                required_props = body_schema.get("required", [])
                body_data = collected_data.get("body", {})
                
                for prop_name in required_props:
                    if prop_name not in body_data:
                        prop_schema = body_schema["properties"].get(prop_name, {})
                        missing.append({
                            "name": prop_name,
                            "type": "body_field",
                            "schema": prop_schema,
                            "description": prop_schema.get("description", "")
                        })
        
        return missing
    
    def generate_collection_prompt(self, operation_id: str, field_info: Dict[str, Any]) -> str:
        """
        Generate a natural language prompt to collect a specific field
        This is what the AI uses to ask the user for information
        """
        field_name = field_info["name"]
        schema = field_info["schema"]
        description = field_info["description"]
        
        # Build a natural prompt based on the schema
        prompt_parts = []
        
        # Start with field name or description
        if description:
            prompt_parts.append(description)
        else:
            # Convert field_name from snake_case to natural language
            natural_name = field_name.replace("_", " ").title()
            prompt_parts.append(f"Please provide your {natural_name}")
        
        # Add format hints
        if schema.get("format") == "email":
            prompt_parts.append("(email address)")
        elif schema.get("format") == "date":
            prompt_parts.append("(format: YYYY-MM-DD)")
        elif schema.get("pattern"):
            prompt_parts.append(f"(format: {schema['pattern']})")
        elif schema.get("enum"):
            options = ", ".join(schema["enum"])
            prompt_parts.append(f"(options: {options})")
        elif schema.get("minLength"):
            prompt_parts.append(f"(minimum {schema['minLength']} characters)")
        
        return " ".join(prompt_parts)
    
    async def cleanup(self):
        """Clean up resources"""
        if self.session:
            await self.session.close()
            self.session = None


def create_llm_functions_for_api_tool(api_tool: SmartAPITool) -> List[Dict[str, Any]]:
    """
    Create function definitions that modern LLMs can use
    This follows the OpenAI function calling format
    """
    return [
        {
            "name": "discover_api_operations",
            "description": "Discover available API operations",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        },
        {
            "name": "get_operation_requirements",
            "description": "Get required fields for an API operation",
            "parameters": {
                "type": "object",
                "properties": {
                    "operation_id": {
                        "type": "string",
                        "description": "The operation ID to get requirements for"
                    }
                },
                "required": ["operation_id"]
            }
        },
        {
            "name": "validate_field",
            "description": "Validate a single field value",
            "parameters": {
                "type": "object",
                "properties": {
                    "operation_id": {"type": "string"},
                    "field_name": {"type": "string"},
                    "value": {"type": "string"}
                },
                "required": ["operation_id", "field_name", "value"]
            }
        },
        {
            "name": "submit_api_operation",
            "description": "Submit data to an API operation",
            "parameters": {
                "type": "object",
                "properties": {
                    "operation_id": {"type": "string"},
                    "data": {
                        "type": "object",
                        "description": "The data to submit"
                    }
                },
                "required": ["operation_id", "data"]
            }
        }
    ]