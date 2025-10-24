"""
Clean Intent-Driven Flow Processor
Declarative, JSON-driven message processing
"""

import logging
import httpx
from typing import Dict, Any, Optional
from services.template_engine import template_engine

logger = logging.getLogger(__name__)


class IntentFlowProcessor:
    """
    Process messages using clean declarative flow:
    1. LLM detects intent
    2. Load intent config from JSON
    3. Inject context into API params
    4. Call API endpoint
    5. Inject tool results into response template
    6. Generate final response
    """
    
    def __init__(self, llm_generator: Any, base_api_url: str = "http://localhost:5024"):
        """
        Initialize flow processor
        
        Args:
            llm_generator: LLM generation function
            base_api_url: Base URL for API calls
        """
        self.llm_generator = llm_generator
        self.base_api_url = base_api_url
        self.http_client = httpx.AsyncClient(timeout=30.0)
    
    async def process_message(
        self,
        message: str,
        detected_intent: str,
        intent_config: Dict[str, Any],
        user_context: Dict[str, Any],
        session_id: str
    ) -> Dict[str, Any]:
        """
        Process message through complete intent flow
        
        Args:
            message: User message
            detected_intent: Intent name from LLM detection
            intent_config: Intent configuration from prompts.json
            user_context: User context (store_id, tenant_id, user_id, role)
            session_id: Session ID
            
        Returns:
            Dict with response text and metadata
        """
        logger.info(f"🔄 Processing intent flow: {detected_intent}")
        
        # Step 1: Extract parameters from message if needed
        extracted_params = template_engine.extract_parameters(
            message, intent_config, self.llm_generator
        )
        
        # Step 2: Execute tool if configured
        tool_result = None
        if intent_config.get('tool'):
            tool_result = await self._execute_tool(
                intent_config, user_context, extracted_params
            )
        
        # Step 3: Build and execute response template
        response_template = intent_config.get('response_template', {})
        response_text = await self._generate_response(
            message, response_template, user_context, tool_result, extracted_params
        )
        
        return {
            'text': response_text,
            'intent': detected_intent,
            'tool_executed': intent_config.get('tool') is not None,
            'tool_result_count': tool_result.get('count', 0) if tool_result else 0
        }
    
    async def _execute_tool(
        self,
        intent_config: Dict[str, Any],
        user_context: Dict[str, Any],
        extracted_params: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Execute tool configured for intent
        
        Args:
            intent_config: Intent configuration
            user_context: User context
            extracted_params: Extracted parameters from message
            
        Returns:
            Tool execution result
        """
        tool_name = intent_config.get('tool')
        tool_config = intent_config.get('tool_config', {})
        
        if tool_name == 'api_query':
            return await self._execute_api_query(
                tool_config, user_context, extracted_params
            )
        else:
            logger.warning(f"Unknown tool type: {tool_name}")
            return None
    
    async def _execute_api_query(
        self,
        tool_config: Dict[str, Any],
        user_context: Dict[str, Any],
        extracted_params: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Execute API query tool
        
        Args:
            tool_config: Tool configuration with endpoint, method, params
            user_context: User context
            extracted_params: Extracted parameters
            
        Returns:
            API response data
        """
        # Get endpoint and inject context variables
        endpoint = tool_config.get('endpoint', '')
        endpoint = template_engine.inject_endpoint(endpoint, context=user_context)
        
        # Get method
        method = tool_config.get('method', 'GET').upper()
        
        # Get params and inject variables
        params = tool_config.get('params', {})
        params = template_engine.inject_params(
            params, context=user_context, extracted=extracted_params
        )
        
        # Get headers and inject variables
        headers = tool_config.get('headers', {})
        if headers:
            headers = template_engine.inject_params(
                headers, context=user_context, extracted=extracted_params
            )
        
        # Build full URL
        url = f"{self.base_api_url}{endpoint}"
        
        logger.info(f"🔧 API Query: {method} {url}")
        logger.info(f"📋 Params: {params}")
        if headers:
            logger.info(f"📋 Headers: {headers}")
        
        try:
            # Make API call
            if method == 'GET':
                response = await self.http_client.get(url, params=params, headers=headers)
            elif method == 'POST':
                response = await self.http_client.post(url, json=params, headers=headers)
            else:
                logger.error(f"Unsupported HTTP method: {method}")
                return None
            
            # Check response
            if response.status_code == 200:
                data = response.json()
                
                # Normalize response format
                if isinstance(data, list):
                    result = {
                        'success': True,
                        'data': data,
                        'count': len(data)
                    }
                elif isinstance(data, dict):
                    # Check common data field names (data, customers, items, results, orders, etc.)
                    data_field = None
                    for field in ['data', 'customers', 'items', 'results', 'orders', 'products']:
                        if field in data:
                            data_field = field
                            break
                    
                    if data_field:
                        result = {
                            'success': True,
                            'data': data[data_field],
                            'count': len(data[data_field]) if isinstance(data[data_field], list) else 1
                        }
                    else:
                        result = {
                            'success': True,
                            'data': [data],
                            'count': 1
                        }
                else:
                    result = {
                        'success': True,
                        'data': [data],
                        'count': 1
                    }
                
                logger.info(f"✅ API Success: {result['count']} items returned")
                return result
            else:
                logger.error(f"❌ API Error: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'data': [],
                    'count': 0,
                    'error': f"API error: {response.status_code}"
                }
        
        except Exception as e:
            logger.error(f"❌ API Exception: {e}", exc_info=True)
            return {
                'success': False,
                'data': [],
                'count': 0,
                'error': str(e)
            }
    
    async def _generate_response(
        self,
        message: str,
        response_template: Dict[str, Any],
        user_context: Dict[str, Any],
        tool_result: Optional[Dict[str, Any]],
        extracted_params: Dict[str, Any]
    ) -> str:
        """
        Generate response using template and LLM
        
        Args:
            message: User message
            response_template: Response template config
            user_context: User context
            tool_result: Tool execution result
            extracted_params: Extracted parameters
            
        Returns:
            Generated response text
        """
        # Get template parts
        system_prompt = response_template.get('system', '')
        template = response_template.get('template', '')
        max_tokens = response_template.get('max_tokens', 75)
        temperature = response_template.get('temperature', 0.7)
        
        # Inject variables into template
        prompt = template_engine.inject_variables(
            template,
            context=user_context,
            tool_result=tool_result,
            extracted=extracted_params,
            message=message
        )
        
        # Build final prompt for LLM
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}\n\nAssistant:"
        else:
            full_prompt = f"{prompt}\n\nAssistant:"
        
        logger.info(f"🎨 Generating response with LLM (max_tokens={max_tokens}, temp={temperature})")
        
        # Generate response using LLM
        try:
            result = await self.llm_generator(
                prompt=full_prompt,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            if isinstance(result, dict):
                response_text = result.get('text', '').strip()
            else:
                response_text = str(result).strip()
            
            logger.info(f"✅ Response generated: {len(response_text)} characters")
            return response_text
        
        except Exception as e:
            logger.error(f"❌ LLM generation failed: {e}", exc_info=True)
            return "I apologize, but I encountered an error generating a response. Please try again."
    
    async def close(self):
        """Close HTTP client"""
        await self.http_client.aclose()
