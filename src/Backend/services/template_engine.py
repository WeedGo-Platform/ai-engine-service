"""
Template Engine for Context and Variable Injection
Handles {{variable}} replacement in prompts and API configurations
"""

import re
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class TemplateEngine:
    """Engine for injecting context variables into templates"""
    
    def __init__(self):
        self.variable_pattern = re.compile(r'\{\{([^}]+)\}\}')
    
    def inject_variables(
        self,
        template: str,
        context: Optional[Dict[str, Any]] = None,
        tool_result: Optional[Dict[str, Any]] = None,
        extracted: Optional[Dict[str, Any]] = None,
        message: Optional[str] = None
    ) -> str:
        """
        Inject variables into template string
        
        Args:
            template: Template string with {{variable}} placeholders
            context: User context (store_id, tenant_id, user_id, role, etc.)
            tool_result: Results from tool execution
            extracted: Extracted parameters from user message
            message: Original user message
            
        Returns:
            Template with all variables replaced
        """
        if not template:
            return template
        
        # Build variable map
        variables = {}
        
        # Add context variables
        if context:
            for key, value in context.items():
                variables[f'context.{key}'] = str(value) if value is not None else ''
        
        # Add tool_result variables
        if tool_result:
            variables['tool_result.count'] = str(tool_result.get('count', 0))
            # Format data concisely to avoid context overflow
            variables['tool_result.data'] = self._format_tool_data(
                tool_result.get('data', []),
                max_items=50  # Limit to 50 items max to avoid context overflow
            )
            
            # Add individual data fields for first item
            if tool_result.get('data') and isinstance(tool_result['data'], list) and len(tool_result['data']) > 0:
                first_item = tool_result['data'][0]
                if isinstance(first_item, dict):
                    for key, value in first_item.items():
                        variables[f'tool_result.{key}'] = str(value) if value is not None else ''
        
        # Add extracted variables
        if extracted:
            for key, value in extracted.items():
                variables[f'extracted.{key}'] = str(value) if value is not None else ''
        
        # Add message
        if message:
            variables['message'] = message
        
        # Replace all variables in template
        result = template
        for match in self.variable_pattern.finditer(template):
            full_match = match.group(0)  # {{variable}}
            var_name = match.group(1).strip()  # variable
            
            if var_name in variables:
                result = result.replace(full_match, variables[var_name])
            else:
                logger.warning(f"Variable {{{{var_name}}}} not found in context")
                result = result.replace(full_match, '')  # Remove undefined variables
        
        return result
    
    def inject_params(
        self,
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        extracted: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Inject variables into API parameters
        
        Args:
            params: Parameter dict with {{variable}} placeholders
            context: User context
            extracted: Extracted parameters
            
        Returns:
            Params with all variables replaced
        """
        result = {}
        
        for key, value in params.items():
            if isinstance(value, str):
                # Inject variables in string values
                injected = self.inject_variables(
                    value,
                    context=context,
                    extracted=extracted
                )
                # Include even if empty (some APIs require empty strings)
                result[key] = injected
            elif isinstance(value, (int, float, bool)):
                result[key] = value
            elif value is None:
                # Skip None values
                continue
            else:
                result[key] = value
        
        return result
    
    def inject_endpoint(
        self,
        endpoint: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Inject variables into API endpoint path
        
        Args:
            endpoint: Endpoint path with {{variable}} placeholders
            context: User context
            
        Returns:
            Endpoint with variables replaced
        """
        return self.inject_variables(endpoint, context=context)
    
    def _format_tool_data(self, data: Any, max_items: int = 20) -> str:
        """
        Format tool result data for template injection
        
        Args:
            data: Tool result data (list, dict, or primitive)
            max_items: Maximum number of items to include
            
        Returns:
            Formatted string representation (concise, not full JSON)
        """
        if not data:
            return "No data"
        
        if isinstance(data, list):
            if len(data) == 0:
                return "No items found"
            
            # Format list of items concisely (NOT full JSON to avoid context overflow)
            formatted = []
            for i, item in enumerate(data[:max_items], 1):
                if isinstance(item, dict):
                    # Extract key fields only
                    summary = self._format_dict_item(item)
                    formatted.append(f"{i}. {summary}")
                else:
                    formatted.append(f"{i}. {item}")
            
            if len(data) > max_items:
                formatted.append(f"... and {len(data) - max_items} more items")
            
            return "\n".join(formatted)
        
        elif isinstance(data, dict):
            # For single dict, format as key summary
            return self._format_dict_item(data)
        
        else:
            return str(data)
    
    def _format_dict_item(self, item: Dict[str, Any]) -> str:
        """Format a single dictionary item for display"""
        # Try to find meaningful fields
        name = (
            item.get('name') or 
            item.get('product_name') or 
            item.get('customer_name') or
            item.get('po_number') or
            item.get('purchase_order_id') or
            item.get('order_id') or
            item.get('order_number') or
            item.get('email') or
            item.get('sku') or
            item.get('id') or
            'Item'
        )
        
        details = []
        
        # Add PO-specific fields
        if 'supplier' in item and item['supplier']:
            details.append(f"Supplier: {item['supplier']}")
        if 'supplier_name' in item and item['supplier_name']:
            details.append(f"Supplier: {item['supplier_name']}")
        
        # Add order date
        if 'order_date' in item and item['order_date']:
            details.append(f"Date: {str(item['order_date'])[:10]}")
        elif 'created_at' in item and item['created_at']:
            details.append(f"Date: {str(item['created_at'])[:10]}")
        
        # Add email if present (for customers) and different from name
        if 'email' in item and item['email'] and item['email'] != name:
            details.append(f"Email: {item['email']}")
        
        # Add phone if present (for customers)
        if 'phone' in item and item['phone']:
            details.append(f"Phone: {item['phone']}")
        
        # Add loyalty points if present (for customers)
        if 'loyalty_points' in item:
            details.append(f"Points: {item['loyalty_points']}")
        
        # Add SKU if present (for products/inventory)
        if 'sku' in item and item['sku'] and item['sku'] != name:
            details.append(f"SKU: {item['sku']}")
        
        # Add quantity if present
        if 'quantity' in item:
            details.append(f"Qty: {item['quantity']}")
        elif 'available_quantity' in item:
            details.append(f"Qty: {item['available_quantity']}")
        elif 'items_count' in item:
            details.append(f"Items: {item['items_count']}")
        
        # Add status if present
        if 'status' in item:
            details.append(f"Status: {item['status']}")
        
        # Add price/total if present
        if 'total_cost' in item:
            details.append(f"Total: ${item['total_cost']}")
        elif 'price' in item:
            details.append(f"${item['price']}")
        elif 'total' in item:
            details.append(f"Total: ${item['total']}")
        elif 'total_amount' in item:
            details.append(f"Total: ${item['total_amount']}")
        elif 'unit_price' in item:
            details.append(f"${item['unit_price']}")
        
        # Add category/type if present
        if 'category' in item:
            details.append(f"Cat: {item['category']}")
        elif 'product_type' in item:
            details.append(f"Type: {item['product_type']}")
        
        if details:
            return f"{name} ({', '.join(details)})"
        else:
            return str(name)
    
    def extract_parameters(
        self,
        message: str,
        intent_config: Dict[str, Any],
        llm_generator: Any = None
    ) -> Dict[str, Any]:
        """
        Extract parameters from user message
        
        Args:
            message: User message
            intent_config: Intent configuration with parameter extraction template
            llm_generator: LLM generator function
            
        Returns:
            Extracted parameters as dict
        """
        # Get intent from config
        intent_description = intent_config.get('description', '')
        
        # For product_search, extract search term from message
        if 'search' in intent_description.lower() or 'product' in intent_description.lower():
            # Extract search term (simple approach - remove common question words)
            search_term = message.lower()
            for word in ['do we have', 'show me', 'find', 'search for', 'looking for', 'any', 'got']:
                search_term = search_term.replace(word, '')
            search_term = search_term.strip()
            
            if search_term:
                return {'search_term': search_term}
        
        return {}


# Global template engine instance
template_engine = TemplateEngine()
