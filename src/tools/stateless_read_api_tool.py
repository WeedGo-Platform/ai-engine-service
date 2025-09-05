"""
Stateless Read API Tool for V5 AI Engine
Clean architecture for reading API data with proper separation of concerns
"""

import asyncio
import aiohttp
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import logging
import json
import os

logger = logging.getLogger(__name__)


@dataclass
class ReadRequest:
    """Encapsulates a read request with all necessary context"""
    endpoint: str
    method: str = "GET"
    params: Dict[str, Any] = None
    headers: Dict[str, str] = None
    user_context: Dict[str, Any] = None  # Contains user_id, session_id, etc.


class StatelessReadAPITool:
    """
    Stateless tool for reading API data
    - No token management (handled by auth service)
    - No user session management (provided by context)
    - Configuration-driven endpoints (from system_config.json)
    - Pure data fetching with proper error handling
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._load_config()
        self.api_config = self.config.get('api', {})
        self.gateway_config = self.api_config.get('gateway', {})
        self.endpoints_config = self.api_config.get('endpoints', {})
        
        # Use configuration with environment variable override
        self.api_gateway_url = os.environ.get(
            'WEEDGO_API_GATEWAY_URL',
            self.gateway_config.get('base_url', 'http://localhost:8000')
        )
        
        self.session = None
        self._openapi_spec = None
        self._endpoint_prompts = None
    
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
        """Initialize HTTP session and load configurations"""
        if not self.session:
            timeout = aiohttp.ClientTimeout(
                total=self.gateway_config.get('timeout_seconds', 30)
            )
            self.session = aiohttp.ClientSession(timeout=timeout)
        
        # Load OpenAPI spec if discovery is enabled
        if self.api_config.get('endpoint_discovery', {}).get('enabled', True):
            await self._load_openapi_spec()
        
        # Load endpoint prompts
        await self._load_endpoint_prompts()
    
    async def _load_openapi_spec(self):
        """Load OpenAPI specification from configured endpoint"""
        try:
            spec_path = self.gateway_config.get('openapi_spec_path', '/openapi.json')
            spec_url = f"{self.api_gateway_url}{spec_path}"
            
            async with self.session.get(spec_url) as response:
                if response.status == 200:
                    self._openapi_spec = await response.json()
                    logger.info(f"Loaded OpenAPI spec from {spec_url}")
                    
                    # Merge with configured endpoints
                    self._merge_configured_endpoints()
                else:
                    logger.warning(f"Could not load OpenAPI spec from {spec_url}, using config")
                    self._use_configured_endpoints()
        except Exception as e:
            logger.error(f"Failed to load OpenAPI spec: {e}")
            
            # Fallback to configuration if enabled
            if self.api_config.get('endpoint_discovery', {}).get('fallback_to_config', True):
                self._use_configured_endpoints()
            else:
                self._openapi_spec = {}
    
    async def _load_endpoint_prompts(self):
        """Load endpoint behavior prompts"""
        try:
            prompts_path = 'prompts/endpoint_prompts.json'
            with open(prompts_path, 'r') as f:
                self._endpoint_prompts = json.load(f)
                logger.info("Loaded endpoint prompts")
        except Exception as e:
            logger.warning(f"Could not load endpoint prompts: {e}")
            self._endpoint_prompts = {}
    
    def _merge_configured_endpoints(self):
        """Merge configured endpoints with discovered OpenAPI spec"""
        if not self._openapi_spec:
            self._openapi_spec = {"paths": {}}
        
        # Add configured endpoints to the spec
        for category, endpoints in self.endpoints_config.items():
            for endpoint_name, endpoint_config in endpoints.items():
                if isinstance(endpoint_config, dict) and 'path' in endpoint_config:
                    path = endpoint_config['path']
                    method = endpoint_config.get('method', 'GET').lower()
                    
                    if path not in self._openapi_spec['paths']:
                        self._openapi_spec['paths'][path] = {}
                    
                    self._openapi_spec['paths'][path][method] = {
                        'operationId': f"{category}_{endpoint_name}",
                        'summary': endpoint_config.get('description', ''),
                        'x-prompts': endpoint_config.get('prompts', {}),
                        'x-requires-auth': endpoint_config.get('requires_auth', False),
                        'x-requires-scope': endpoint_config.get('requires_scope', None)
                    }
    
    def _use_configured_endpoints(self):
        """Build OpenAPI spec entirely from configuration"""
        self._openapi_spec = {
            "openapi": "3.0.0",
            "info": {
                "title": "WeedGo API (from config)",
                "version": "1.0.0"
            },
            "servers": [
                {"url": self.api_gateway_url}
            ],
            "paths": {}
        }
        
        # Build paths from configuration
        for category, endpoints in self.endpoints_config.items():
            for endpoint_name, endpoint_config in endpoints.items():
                if isinstance(endpoint_config, dict) and 'path' in endpoint_config:
                    path = endpoint_config['path']
                    method = endpoint_config.get('method', 'GET').lower()
                    
                    if path not in self._openapi_spec['paths']:
                        self._openapi_spec['paths'][path] = {}
                    
                    # Extract parameters from path
                    parameters = []
                    import re
                    for param in re.findall(r'\{(\w+)\}', path):
                        parameters.append({
                            "name": param,
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"}
                        })
                    
                    # Add query parameters if specified
                    if 'parameters' in endpoint_config:
                        for param_name in endpoint_config['parameters']:
                            parameters.append({
                                "name": param_name,
                                "in": "query",
                                "required": False,
                                "schema": {"type": "string"}
                            })
                    
                    self._openapi_spec['paths'][path][method] = {
                        'operationId': f"{category}_{endpoint_name}",
                        'summary': endpoint_config.get('description', ''),
                        'parameters': parameters if parameters else None,
                        'x-prompts': endpoint_config.get('prompts', {}),
                        'x-requires-auth': endpoint_config.get('requires_auth', False),
                        'x-requires-scope': endpoint_config.get('requires_scope', None)
                    }
        
        logger.info(f"Built OpenAPI spec from configuration with {len(self._openapi_spec['paths'])} endpoints")
    
    async def discover_readable_endpoints(self) -> List[Dict[str, str]]:
        """
        Discover all GET endpoints from OpenAPI spec
        Returns list of readable endpoints with descriptions
        """
        if not self._openapi_spec:
            await self._load_openapi_spec()
        
        endpoints = []
        for path, methods in self._openapi_spec.get("paths", {}).items():
            if "get" in methods:
                endpoint_info = methods["get"]
                endpoints.append({
                    "path": path,
                    "operation_id": endpoint_info.get("operationId", ""),
                    "description": endpoint_info.get("summary", ""),
                    "parameters": endpoint_info.get("parameters", [])
                })
        
        return endpoints
    
    async def read(
        self,
        endpoint_path: str,
        parameters: Dict[str, Any] = None,
        auth_token: str = None,
        user_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Core read method - stateless and pure
        
        Args:
            endpoint_path: API endpoint path (e.g., "/api/v1/orders/{order_id}")
            parameters: Path and query parameters
            auth_token: Bearer token for authentication
            user_context: User context (user_id, session_id, etc.)
        
        Returns:
            API response or error
        """
        try:
            await self.initialize()
            
            # Substitute path parameters
            formatted_path = endpoint_path
            if parameters:
                for key, value in parameters.items():
                    placeholder = f"{{{key}}}"
                    if placeholder in formatted_path:
                        formatted_path = formatted_path.replace(placeholder, str(value))
            
            # Handle user context substitution
            if user_context and "{customer_id}" in formatted_path:
                formatted_path = formatted_path.replace(
                    "{customer_id}", 
                    str(user_context.get("user_id", ""))
                )
            
            # Build full URL
            full_url = f"{self.api_gateway_url}{formatted_path}"
            
            # Prepare headers
            headers = {"Accept": "application/json"}
            if auth_token:
                headers["Authorization"] = f"Bearer {auth_token}"
            
            # Extract query parameters
            query_params = {
                k: v for k, v in (parameters or {}).items() 
                if f"{{{k}}}" not in endpoint_path
            }
            
            # Make the request
            async with self.session.get(
                full_url,
                headers=headers,
                params=query_params if query_params else None
            ) as response:
                
                response_data = await response.json()
                
                return {
                    "status": response.status,
                    "success": 200 <= response.status < 300,
                    "data": response_data,
                    "endpoint": endpoint_path,
                    "url": str(response.url)
                }
                
        except aiohttp.ClientError as e:
            return {
                "status": 0,
                "success": False,
                "error": f"Network error: {str(e)}",
                "endpoint": endpoint_path
            }
        except Exception as e:
            logger.error(f"Read error: {e}")
            return {
                "status": 0,
                "success": False,
                "error": f"Read failed: {str(e)}",
                "endpoint": endpoint_path
            }
    
    def interpret_response(self, response: Dict[str, Any], query_intent: str) -> str:
        """
        Interpret API response based on user's query intent
        This is where the AI adds value by understanding the data
        
        Args:
            response: Raw API response
            query_intent: What the user asked for
        
        Returns:
            Natural language interpretation
        """
        if not response.get("success"):
            status = response.get("status", 0)
            if status == 401:
                return "I need you to log in first to access this information."
            elif status == 403:
                return "You don't have permission to access this information."
            elif status == 404:
                return "I couldn't find that information."
            else:
                return "I'm having trouble accessing that information right now."
        
        data = response.get("data", {})
        endpoint = response.get("endpoint", "")
        
        # Interpret based on endpoint pattern and intent
        if "orders/latest" in endpoint or "last order" in query_intent.lower():
            return self._interpret_order_data(data)
        elif "inventory" in endpoint or "stock" in query_intent.lower():
            return self._interpret_inventory_data(data)
        elif "profile" in endpoint:
            return self._interpret_profile_data(data)
        elif "prescriptions" in endpoint:
            return self._interpret_prescription_data(data)
        elif "recommendations" in endpoint:
            return self._interpret_recommendations_data(data)
        else:
            # Generic interpretation
            return self._generic_interpretation(data, query_intent)
    
    def _interpret_order_data(self, data: Dict) -> str:
        """Interpret order data into natural language"""
        if not data or "error" in data:
            return "You don't have any recent orders."
        
        order_id = data.get("id", data.get("order_id", "unknown"))
        created = data.get("created_at", "recently")
        status = data.get("status", "processing")
        total = data.get("total", 0)
        items = data.get("items", [])
        
        response = f"Your last order (#{order_id}) was placed {created}. "
        response += f"It's currently {status}"
        
        if total > 0:
            response += f" with a total of ${total:.2f}"
        
        if items:
            item_count = len(items)
            response += f". You ordered {item_count} item{'s' if item_count != 1 else ''}"
            
            # Mention first few items
            if item_count <= 3:
                item_names = [item.get("name", "item") for item in items]
                response += f": {', '.join(item_names)}"
            else:
                first_items = [items[0].get("name", "item"), items[1].get("name", "item")]
                response += f" including {', '.join(first_items)} and {item_count - 2} more"
        
        response += "."
        return response
    
    def _interpret_inventory_data(self, data: Dict) -> str:
        """Interpret inventory data"""
        if not data:
            return "I couldn't find inventory information for that product."
        
        product_name = data.get("product_name", data.get("name", "That product"))
        quantity = data.get("quantity_available", data.get("stock", 0))
        
        if quantity > 20:
            return f"{product_name} is well stocked with {quantity} units available."
        elif quantity > 0:
            return f"{product_name} has limited availability with only {quantity} units left."
        else:
            return f"{product_name} is currently out of stock."
    
    def _interpret_profile_data(self, data: Dict) -> str:
        """Interpret profile data"""
        if not data:
            return "I couldn't retrieve your profile information."
        
        name = data.get("name", data.get("first_name", "there"))
        member_since = data.get("created_at", data.get("member_since", ""))
        
        response = f"Hi {name}!"
        if member_since:
            response += f" You've been a member since {member_since}."
        
        preferences = data.get("preferences", {})
        if preferences:
            fav_category = preferences.get("favorite_category")
            if fav_category:
                response += f" I see you prefer {fav_category} products."
        
        return response
    
    def _interpret_prescription_data(self, data: Dict) -> str:
        """Interpret prescription data"""
        if not data or not data.get("prescriptions"):
            return "You don't have any active prescriptions on file."
        
        prescriptions = data.get("prescriptions", [])
        active = [p for p in prescriptions if p.get("status") == "active"]
        
        if not active:
            return "Your prescriptions have expired. You'll need to renew them."
        
        if len(active) == 1:
            exp = active[0].get("expiry_date", "soon")
            return f"You have an active prescription valid until {exp}."
        else:
            return f"You have {len(active)} active prescriptions on file."
    
    def _interpret_recommendations_data(self, data: Dict) -> str:
        """Interpret product recommendations"""
        if not data or not data.get("recommendations"):
            return "I don't have any personalized recommendations for you right now."
        
        recs = data.get("recommendations", [])[:3]  # Top 3
        
        response = "Based on your preferences, I recommend "
        rec_names = [r.get("name", "a product") for r in recs]
        
        if len(rec_names) == 1:
            response += rec_names[0]
        elif len(rec_names) == 2:
            response += f"{rec_names[0]} and {rec_names[1]}"
        else:
            response += f"{', '.join(rec_names[:-1])}, and {rec_names[-1]}"
        
        response += ". Would you like more details about any of these?"
        return response
    
    def _generic_interpretation(self, data: Dict, query_intent: str) -> str:
        """Generic interpretation for unknown data types"""
        if not data:
            return "I couldn't find the information you requested."
        
        # Try to extract key information
        if isinstance(data, list):
            return f"I found {len(data)} results for your query."
        elif isinstance(data, dict):
            # Look for common fields
            if "name" in data:
                return f"Here's information about {data['name']}."
            elif "message" in data:
                return data["message"]
            else:
                # Return a summary of available fields
                fields = list(data.keys())[:5]
                return f"I found information with details about: {', '.join(fields)}"
        else:
            return "I found the information you requested."
    
    async def cleanup(self):
        """Clean up resources"""
        if self.session:
            await self.session.close()
            self.session = None


class ConversationAwareReadTool:
    """
    Wrapper that adds conversation context awareness to the stateless read tool
    This is what actually gets registered with V5
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.read_tool = StatelessReadAPITool(config)
        self.conversation_context = {}
        self.endpoint_prompts = None
    
    async def handle_query(
        self,
        user_query: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Main entry point for handling user queries
        
        Args:
            user_query: Natural language query from user
            context: Conversation context with auth token, user info, etc.
        
        Returns:
            Natural language response
        """
        # Update context
        self.conversation_context.update(context)
        
        # Determine what endpoint to call based on query
        endpoint, params = await self._determine_endpoint(user_query)
        
        if not endpoint:
            return "I'm not sure what information you're looking for. Could you be more specific?"
        
        # Get auth token from context
        auth_token = self.conversation_context.get("auth_token")
        user_context = {
            "user_id": self.conversation_context.get("user_id"),
            "session_id": self.conversation_context.get("session_id")
        }
        
        # Make the API call
        response = await self.read_tool.read(
            endpoint_path=endpoint,
            parameters=params,
            auth_token=auth_token,
            user_context=user_context
        )
        
        # Interpret the response
        interpretation = self.read_tool.interpret_response(response, user_query)
        
        return interpretation
    
    async def _determine_endpoint(self, query: str) -> tuple[str, Dict]:
        """
        Determine which endpoint to call based on user query
        This is where LLM understanding shines
        
        Returns:
            (endpoint_path, parameters)
        """
        query_lower = query.lower()
        
        # Product search patterns - PRIMARY business logic
        if any(word in query_lower for word in ["product", "strain", "flower", "edible", "vape", "cannabis", "thc", "cbd", "indica", "sativa", "hybrid"]):
            # Build search parameters based on query
            params = {"limit": 10}
            
            # Extract category if mentioned
            if "flower" in query_lower:
                params["category"] = "flower"
            elif "edible" in query_lower:
                params["category"] = "edibles"
            elif "vape" in query_lower:
                params["category"] = "vapes"
            
            # Extract strain type if mentioned
            if "indica" in query_lower:
                params["strain_type"] = "indica"
            elif "sativa" in query_lower:
                params["strain_type"] = "sativa"
            elif "hybrid" in query_lower:
                params["strain_type"] = "hybrid"
            
            # Extract THC/CBD preferences
            if "high thc" in query_lower:
                params["min_thc"] = 20
            elif "low thc" in query_lower:
                params["max_thc"] = 10
            
            if "high cbd" in query_lower:
                params["min_cbd"] = 10
            elif "cbd" in query_lower:
                params["min_cbd"] = 1
            
            # Price range extraction (simple pattern matching)
            import re
            price_match = re.search(r'under \$?(\d+)', query_lower)
            if price_match:
                params["max_price"] = int(price_match.group(1))
            
            # General search query
            if not any(k in params for k in ["category", "strain_type", "min_thc", "max_thc"]):
                params["query"] = query  # Use full query for text search
            
            return "/api/v1/products/search", params
        
        # Inventory/stock check
        elif "inventory" in query_lower or "in stock" in query_lower:
            # Need to extract product name/ID (would use NER in production)
            return "/api/v1/inventory/{product_id}", {"product_id": "extracted_id"}
        
        # Trending/popular products
        elif "trending" in query_lower or "popular" in query_lower or "best seller" in query_lower:
            return "/api/v1/analytics/products/trending", {}
        
        # Product statistics
        elif "statistics" in query_lower or "analytics" in query_lower:
            return "/api/v1/analytics/products/stats", {}
        
        # Order patterns
        elif "last order" in query_lower or "recent order" in query_lower:
            return "/api/v1/customers/{customer_id}/orders/latest", {}
        
        elif "order history" in query_lower:
            return "/api/v1/customers/{customer_id}/orders", {"limit": 10}
        
        # Profile patterns
        elif "profile" in query_lower or "my account" in query_lower:
            return "/api/v1/customers/{customer_id}/profile", {}
        
        # Prescription patterns
        elif "prescription" in query_lower:
            return "/api/v1/customers/{customer_id}/prescriptions", {}
        
        # Recommendations
        elif "recommend" in query_lower:
            return "/api/v1/customers/{customer_id}/recommendations", {}
        
        else:
            # Default to product search for unknown queries
            return "/api/v1/products/search", {"query": query, "limit": 10}
    
    async def cleanup(self):
        """Clean up resources"""
        await self.read_tool.cleanup()


def register_conversation_read_tool_with_v5(tool_manager, config: Dict[str, Any] = None):
    """
    Register the conversation-aware read tool with V5
    """
    tool = ConversationAwareReadTool(config)
    
    async def tool_wrapper(action: str, **kwargs) -> Any:
        """Tool wrapper for V5 integration"""
        
        if action == "query":
            user_query = kwargs.get("query", "")
            context = kwargs.get("context", {})
            return await tool.handle_query(user_query, context)
        
        elif action == "discover":
            return await tool.read_tool.discover_readable_endpoints()
        
        elif action == "read_raw":
            # For direct endpoint access
            endpoint = kwargs.get("endpoint")
            params = kwargs.get("params", {})
            auth_token = kwargs.get("auth_token")
            user_context = kwargs.get("user_context", {})
            
            return await tool.read_tool.read(
                endpoint_path=endpoint,
                parameters=params,
                auth_token=auth_token,
                user_context=user_context
            )
        
        else:
            return {"error": f"Unknown action: {action}"}
    
    # Register with tool manager
    tool_manager.register_tool(
        name="conversation_read_api",
        handler=tool_wrapper,
        description="Read API data based on natural language queries with conversation context"
    )
    
    logger.info("Conversation-aware Read API Tool registered with V5")
    return tool