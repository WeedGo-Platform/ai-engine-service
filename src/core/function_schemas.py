"""
Function Schema System (OpenAI Compatible)
Implements OpenAI's function calling standard for tool definitions
"""

import json
from typing import Dict, List, Any, Optional, Callable, Union, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import inspect
import logging
from pydantic import BaseModel, Field, create_model

logger = logging.getLogger(__name__)


class ParameterType(str, Enum):
    """JSON Schema types for parameters"""
    STRING = "string"
    NUMBER = "number"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"
    NULL = "null"


@dataclass
class Parameter:
    """Function parameter definition"""
    name: str
    type: Union[ParameterType, List[ParameterType]]
    description: str
    required: bool = True
    default: Any = None
    enum: Optional[List[Any]] = None
    format: Optional[str] = None  # e.g., "date-time", "email", "uri"
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[str] = None  # regex pattern
    items: Optional['Parameter'] = None  # for arrays
    properties: Optional[Dict[str, 'Parameter']] = None  # for objects
    
    def to_json_schema(self) -> Dict[str, Any]:
        """Convert to JSON Schema format"""
        schema = {}
        
        # Handle type
        if isinstance(self.type, list):
            schema["type"] = [t.value for t in self.type]
        else:
            schema["type"] = self.type.value
        
        # Add description
        if self.description:
            schema["description"] = self.description
        
        # Add constraints
        if self.enum:
            schema["enum"] = self.enum
        
        if self.format:
            schema["format"] = self.format
        
        if self.min_value is not None:
            schema["minimum"] = self.min_value
        
        if self.max_value is not None:
            schema["maximum"] = self.max_value
        
        if self.min_length is not None:
            schema["minLength"] = self.min_length
        
        if self.max_length is not None:
            schema["maxLength"] = self.max_length
        
        if self.pattern:
            schema["pattern"] = self.pattern
        
        # Handle array items
        if self.type == ParameterType.ARRAY and self.items:
            schema["items"] = self.items.to_json_schema()
        
        # Handle object properties
        if self.type == ParameterType.OBJECT and self.properties:
            schema["properties"] = {
                name: param.to_json_schema()
                for name, param in self.properties.items()
            }
            # Add required fields for object
            required = [
                name for name, param in self.properties.items()
                if param.required
            ]
            if required:
                schema["required"] = required
        
        # Add default if not required
        if not self.required and self.default is not None:
            schema["default"] = self.default
        
        return schema


@dataclass
class FunctionSchema:
    """OpenAI-compatible function schema"""
    name: str
    description: str
    parameters: List[Parameter]
    returns: Optional[Parameter] = None
    examples: Optional[List[Dict[str, Any]]] = None
    deprecated: bool = False
    tags: Optional[List[str]] = None
    
    def to_openai_format(self) -> Dict[str, Any]:
        """Convert to OpenAI function calling format"""
        # Build parameters schema
        properties = {}
        required = []
        
        for param in self.parameters:
            properties[param.name] = param.to_json_schema()
            if param.required:
                required.append(param.name)
        
        schema = {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": properties
            }
        }
        
        if required:
            schema["parameters"]["required"] = required
        
        # Add optional fields
        if self.deprecated:
            schema["deprecated"] = True
        
        if self.examples:
            schema["examples"] = self.examples
        
        return schema
    
    def to_anthropic_format(self) -> Dict[str, Any]:
        """Convert to Anthropic tool use format"""
        schema = self.to_openai_format()
        
        # Anthropic uses slightly different format
        return {
            "name": schema["name"],
            "description": schema["description"],
            "input_schema": schema["parameters"]
        }
    
    def validate_arguments(self, arguments: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate function arguments against schema
        
        Returns:
            (valid, error_message) tuple
        """
        # Check required parameters
        for param in self.parameters:
            if param.required and param.name not in arguments:
                return False, f"Missing required parameter: {param.name}"
        
        # Validate each argument
        for param in self.parameters:
            if param.name in arguments:
                value = arguments[param.name]
                valid, error = self._validate_parameter(param, value)
                if not valid:
                    return False, f"Parameter '{param.name}': {error}"
        
        # Check for unknown parameters
        known_params = {p.name for p in self.parameters}
        unknown = set(arguments.keys()) - known_params
        if unknown:
            return False, f"Unknown parameters: {unknown}"
        
        return True, None
    
    def _validate_parameter(self, param: Parameter, value: Any) -> Tuple[bool, Optional[str]]:
        """Validate a single parameter value"""
        # Type validation
        if param.type == ParameterType.STRING:
            if not isinstance(value, str):
                return False, f"Expected string, got {type(value).__name__}"
            
            if param.min_length and len(value) < param.min_length:
                return False, f"String too short (min {param.min_length})"
            
            if param.max_length and len(value) > param.max_length:
                return False, f"String too long (max {param.max_length})"
            
            if param.pattern:
                import re
                if not re.match(param.pattern, value):
                    return False, f"Does not match pattern {param.pattern}"
        
        elif param.type == ParameterType.NUMBER:
            if not isinstance(value, (int, float)):
                return False, f"Expected number, got {type(value).__name__}"
            
            if param.min_value is not None and value < param.min_value:
                return False, f"Value too small (min {param.min_value})"
            
            if param.max_value is not None and value > param.max_value:
                return False, f"Value too large (max {param.max_value})"
        
        elif param.type == ParameterType.INTEGER:
            if not isinstance(value, int):
                return False, f"Expected integer, got {type(value).__name__}"
            
            if param.min_value is not None and value < param.min_value:
                return False, f"Value too small (min {param.min_value})"
            
            if param.max_value is not None and value > param.max_value:
                return False, f"Value too large (max {param.max_value})"
        
        elif param.type == ParameterType.BOOLEAN:
            if not isinstance(value, bool):
                return False, f"Expected boolean, got {type(value).__name__}"
        
        elif param.type == ParameterType.ARRAY:
            if not isinstance(value, list):
                return False, f"Expected array, got {type(value).__name__}"
            
            # Validate array items if schema provided
            if param.items:
                for i, item in enumerate(value):
                    valid, error = self._validate_parameter(param.items, item)
                    if not valid:
                        return False, f"Array item {i}: {error}"
        
        elif param.type == ParameterType.OBJECT:
            if not isinstance(value, dict):
                return False, f"Expected object, got {type(value).__name__}"
            
            # Validate object properties if schema provided
            if param.properties:
                for prop_name, prop_schema in param.properties.items():
                    if prop_schema.required and prop_name not in value:
                        return False, f"Missing required property: {prop_name}"
                    
                    if prop_name in value:
                        valid, error = self._validate_parameter(prop_schema, value[prop_name])
                        if not valid:
                            return False, f"Property '{prop_name}': {error}"
        
        # Enum validation
        if param.enum and value not in param.enum:
            return False, f"Value not in allowed values: {param.enum}"
        
        return True, None


class FunctionRegistry:
    """Registry for function schemas and implementations"""
    
    def __init__(self):
        self.functions: Dict[str, FunctionSchema] = {}
        self.implementations: Dict[str, Callable] = {}
        self.categories: Dict[str, List[str]] = {}
    
    def register(
        self,
        schema: FunctionSchema,
        implementation: Callable,
        category: Optional[str] = None
    ):
        """Register a function with its schema"""
        self.functions[schema.name] = schema
        self.implementations[schema.name] = implementation
        
        if category:
            if category not in self.categories:
                self.categories[category] = []
            self.categories[category].append(schema.name)
        
        logger.info(f"Registered function: {schema.name}")
    
    def get_schema(self, name: str) -> Optional[FunctionSchema]:
        """Get function schema by name"""
        return self.functions.get(name)
    
    def get_implementation(self, name: str) -> Optional[Callable]:
        """Get function implementation by name"""
        return self.implementations.get(name)
    
    def list_functions(self, category: Optional[str] = None) -> List[str]:
        """List all registered functions"""
        if category:
            return self.categories.get(category, [])
        return list(self.functions.keys())
    
    def get_openai_tools(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all functions in OpenAI format"""
        functions = self.list_functions(category)
        return [
            self.functions[name].to_openai_format()
            for name in functions
        ]
    
    def get_anthropic_tools(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all functions in Anthropic format"""
        functions = self.list_functions(category)
        return [
            self.functions[name].to_anthropic_format()
            for name in functions
        ]
    
    async def execute(
        self,
        name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a function with validation"""
        # Get schema and implementation
        schema = self.get_schema(name)
        if not schema:
            return {"error": f"Function '{name}' not found"}
        
        implementation = self.get_implementation(name)
        if not implementation:
            return {"error": f"Implementation for '{name}' not found"}
        
        # Validate arguments
        valid, error = schema.validate_arguments(arguments)
        if not valid:
            return {"error": f"Invalid arguments: {error}"}
        
        try:
            # Execute function
            if inspect.iscoroutinefunction(implementation):
                result = await implementation(**arguments)
            else:
                result = implementation(**arguments)
            
            return {"result": result}
        
        except Exception as e:
            logger.error(f"Function execution failed: {e}")
            return {"error": f"Execution failed: {str(e)}"}


# Decorator for auto-generating schemas
def function_schema(
    description: str,
    examples: Optional[List[Dict]] = None,
    category: Optional[str] = None,
    **param_descriptions: str
):
    """
    Decorator to auto-generate function schema from type hints
    
    Usage:
        @function_schema(
            description="Search for products",
            query="Search query string",
            category="Product category",
            examples=[{"query": "indica", "limit": 10}]
        )
        def search_products(query: str, category: str = None, limit: int = 10) -> List[Dict]:
            ...
    """
    def decorator(func: Callable) -> Callable:
        # Get function signature
        sig = inspect.signature(func)
        
        # Build parameters
        parameters = []
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
            
            # Determine type
            param_type = ParameterType.STRING  # default
            if param.annotation != inspect.Parameter.empty:
                if param.annotation == int:
                    param_type = ParameterType.INTEGER
                elif param.annotation == float:
                    param_type = ParameterType.NUMBER
                elif param.annotation == bool:
                    param_type = ParameterType.BOOLEAN
                elif param.annotation == list:
                    param_type = ParameterType.ARRAY
                elif param.annotation == dict:
                    param_type = ParameterType.OBJECT
            
            # Build parameter
            parameters.append(Parameter(
                name=param_name,
                type=param_type,
                description=param_descriptions.get(param_name, f"Parameter {param_name}"),
                required=param.default == inspect.Parameter.empty,
                default=param.default if param.default != inspect.Parameter.empty else None
            ))
        
        # Create schema
        schema = FunctionSchema(
            name=func.__name__,
            description=description,
            parameters=parameters,
            examples=examples
        )
        
        # Attach schema to function
        func._schema = schema
        func._category = category
        
        return func
    
    return decorator


# Example V5 tool schemas
def create_v5_tool_schemas() -> FunctionRegistry:
    """Create standard V5 tool schemas"""
    registry = FunctionRegistry()
    
    # Product Search Tool
    product_search_schema = FunctionSchema(
        name="search_products",
        description="Search for cannabis products based on various criteria",
        parameters=[
            Parameter(
                name="query",
                type=ParameterType.STRING,
                description="Search query for product names or descriptions",
                required=False,
                max_length=200
            ),
            Parameter(
                name="category",
                type=ParameterType.STRING,
                description="Product category",
                required=False,
                enum=["flower", "edibles", "concentrates", "vapes", "topicals", "accessories"]
            ),
            Parameter(
                name="strain_type",
                type=ParameterType.STRING,
                description="Cannabis strain type",
                required=False,
                enum=["indica", "sativa", "hybrid"]
            ),
            Parameter(
                name="min_thc",
                type=ParameterType.NUMBER,
                description="Minimum THC percentage",
                required=False,
                min_value=0,
                max_value=100
            ),
            Parameter(
                name="max_thc",
                type=ParameterType.NUMBER,
                description="Maximum THC percentage",
                required=False,
                min_value=0,
                max_value=100
            ),
            Parameter(
                name="min_price",
                type=ParameterType.NUMBER,
                description="Minimum price in dollars",
                required=False,
                min_value=0
            ),
            Parameter(
                name="max_price",
                type=ParameterType.NUMBER,
                description="Maximum price in dollars",
                required=False,
                min_value=0
            ),
            Parameter(
                name="limit",
                type=ParameterType.INTEGER,
                description="Maximum number of results to return",
                required=False,
                default=10,
                min_value=1,
                max_value=100
            )
        ],
        examples=[
            {
                "query": "blue dream",
                "category": "flower",
                "limit": 5
            },
            {
                "strain_type": "indica",
                "min_thc": 20,
                "max_price": 50
            }
        ]
    )
    
    # Dosage Calculator Tool
    dosage_calculator_schema = FunctionSchema(
        name="calculate_dosage",
        description="Calculate recommended cannabis dosage based on user factors",
        parameters=[
            Parameter(
                name="weight_kg",
                type=ParameterType.NUMBER,
                description="User's weight in kilograms",
                required=True,
                min_value=20,
                max_value=300
            ),
            Parameter(
                name="tolerance",
                type=ParameterType.STRING,
                description="User's cannabis tolerance level",
                required=True,
                enum=["none", "low", "medium", "high"]
            ),
            Parameter(
                name="condition",
                type=ParameterType.STRING,
                description="Medical condition being treated",
                required=False,
                enum=["pain", "anxiety", "insomnia", "appetite", "nausea", "general"]
            ),
            Parameter(
                name="method",
                type=ParameterType.STRING,
                description="Consumption method",
                required=True,
                enum=["smoke", "vape", "edible", "tincture", "topical"]
            )
        ],
        examples=[
            {
                "weight_kg": 70,
                "tolerance": "low",
                "condition": "anxiety",
                "method": "vape"
            }
        ]
    )
    
    # Order Creation Tool
    order_creation_schema = FunctionSchema(
        name="create_order",
        description="Create a new order for products",
        parameters=[
            Parameter(
                name="items",
                type=ParameterType.ARRAY,
                description="List of items to order",
                required=True,
                items=Parameter(
                    name="item",
                    type=ParameterType.OBJECT,
                    description="Order item",
                    properties={
                        "product_id": Parameter(
                            name="product_id",
                            type=ParameterType.STRING,
                            description="Product identifier",
                            required=True
                        ),
                        "quantity": Parameter(
                            name="quantity",
                            type=ParameterType.INTEGER,
                            description="Quantity to order",
                            required=True,
                            min_value=1,
                            max_value=100
                        )
                    }
                )
            ),
            Parameter(
                name="delivery_method",
                type=ParameterType.STRING,
                description="Delivery or pickup preference",
                required=True,
                enum=["delivery", "pickup"]
            ),
            Parameter(
                name="delivery_address",
                type=ParameterType.STRING,
                description="Delivery address (required if delivery method is 'delivery')",
                required=False,
                max_length=500
            ),
            Parameter(
                name="payment_method",
                type=ParameterType.STRING,
                description="Payment method",
                required=True,
                enum=["cash", "debit", "credit"]
            ),
            Parameter(
                name="notes",
                type=ParameterType.STRING,
                description="Special instructions or notes",
                required=False,
                max_length=500
            )
        ]
    )
    
    # Register schemas with placeholder implementations
    async def search_products_impl(**kwargs):
        return {"products": [], "count": 0}
    
    async def calculate_dosage_impl(**kwargs):
        return {"recommended_dose": 5, "unit": "mg", "notes": "Start low and go slow"}
    
    async def create_order_impl(**kwargs):
        return {"order_id": "123", "status": "pending"}
    
    registry.register(product_search_schema, search_products_impl, "products")
    registry.register(dosage_calculator_schema, calculate_dosage_impl, "medical")
    registry.register(order_creation_schema, create_order_impl, "orders")
    
    return registry


# Global registry instance
_registry_instance = None

def get_function_registry() -> FunctionRegistry:
    """Get or create global function registry"""
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = create_v5_tool_schemas()
    return _registry_instance