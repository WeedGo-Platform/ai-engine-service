"""
Entity Extraction Service
Extracts structured search parameters from natural language queries using direct LLM access
Supports multilingual queries and context-aware extraction
"""
import json
import logging
from typing import Dict, Any, Optional, List
import aiohttp
from jsonschema import validate, ValidationError

from services.config import PRODUCTS_CATEGORIES_ENDPOINT, CONVERSATION_HISTORY_ENDPOINT

logger = logging.getLogger(__name__)


class EntityExtractor:
    """Extracts entities from natural language queries using LLM"""

    def __init__(self, model_instance, intent_config: Dict[str, Any]):
        """
        Initialize entity extractor

        Args:
            model_instance: Direct reference to LLM model
            intent_config: Loaded intent.json configuration
        """
        self.model = model_instance
        self.config = intent_config.get("entity_extraction", {})
        self.schema = intent_config.get("schemas", {}).get("entity_extraction_output", {})
        self.prompt_template = self.config.get("prompt_template", "")
        self.max_tokens = self.config.get("max_tokens", 300)
        self.temperature = self.config.get("temperature", 0.1)

    async def extract_entities(
        self,
        message: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract structured entities from user message

        Args:
            message: User's natural language query
            session_id: Optional session ID for conversation context
            user_id: Optional user ID for personalization

        Returns:
            Extracted entities matching entity_extraction_output schema
        """
        try:
            # Fetch context data
            available_categories = await self._fetch_categories()
            available_subcategories = await self._fetch_subcategories()
            conversation_history = await self._fetch_conversation_history(session_id) if session_id else []

            # Build prompt with context
            prompt = self._build_prompt(
                message=message,
                available_categories=available_categories,
                available_subcategories=available_subcategories,
                conversation_history=conversation_history
            )

            # Call LLM directly
            logger.info(f"Extracting entities from: {message[:100]}...")
            response = await self._call_llm(prompt)

            # Parse and validate JSON response
            entities = self._parse_and_validate(response)

            logger.info(f"Extracted entities with confidence {entities.get('confidence', 0):.2f}")
            return entities

        except Exception as e:
            logger.error(f"Entity extraction failed: {str(e)}", exc_info=True)
            # Return safe fallback
            return {
                "confidence": 0.0,
                "needs_clarification": True,
                "clarification_reason": "Failed to extract entities from query"
            }

    def _build_prompt(
        self,
        message: str,
        available_categories: List[str],
        available_subcategories: Dict[str, List[str]],
        conversation_history: List[Dict[str, str]]
    ) -> str:
        """Build extraction prompt with dynamic context"""

        # Format categories and subcategories for prompt
        categories_str = ", ".join(available_categories)
        subcategories_str = json.dumps(available_subcategories, indent=2)

        # Add conversation context if available
        context_str = ""
        if conversation_history:
            recent_exchanges = conversation_history[-3:]  # Last 3 exchanges
            context_str = "\n\nRecent conversation context:\n"
            for exchange in recent_exchanges:
                context_str += f"User: {exchange.get('user', '')}\n"
                context_str += f"Assistant: {exchange.get('assistant', '')}\n"

        # Build prompt from template
        prompt = self.prompt_template.format(
            available_categories=categories_str,
            available_subcategories=subcategories_str,
            message=message
        )

        if context_str:
            prompt += context_str

        # Add schema as instruction
        prompt += f"\n\nOutput JSON schema:\n{json.dumps(self.schema, indent=2)}"

        return prompt

    async def _call_llm(self, prompt: str) -> str:
        """
        Call LLM directly with prompt

        Args:
            prompt: Formatted extraction prompt

        Returns:
            Raw LLM response text
        """
        try:
            # Direct model call (adjust based on your model interface)
            # This assumes model has a generate() or complete() method
            if hasattr(self.model, 'generate'):
                response = await self.model.generate(
                    prompt=prompt,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    stop_sequences=["\n\n", "User:", "Assistant:"]
                )
            elif hasattr(self.model, 'complete'):
                response = await self.model.complete(
                    prompt=prompt,
                    max_new_tokens=self.max_tokens,
                    temperature=self.temperature
                )
            else:
                # Fallback: assume callable
                response = await self.model(
                    prompt,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature
                )

            # Extract text from response (adjust based on model output format)
            if isinstance(response, dict):
                return response.get('text', response.get('output', str(response)))
            elif isinstance(response, str):
                return response
            else:
                return str(response)

        except Exception as e:
            logger.error(f"LLM call failed: {str(e)}")
            raise

    def _parse_and_validate(self, response: str) -> Dict[str, Any]:
        """
        Parse JSON response and validate against schema

        Args:
            response: Raw LLM response text

        Returns:
            Validated entity dictionary
        """
        try:
            # Try to extract JSON from response
            # Handle cases where model includes extra text
            response = response.strip()

            # Find JSON block
            start_idx = response.find('{')
            end_idx = response.rfind('}')

            if start_idx == -1 or end_idx == -1:
                raise ValueError("No JSON found in response")

            json_str = response[start_idx:end_idx + 1]
            entities = json.loads(json_str)

            # Validate against schema
            validate(instance=entities, schema=self.schema)

            return entities

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {str(e)}\nResponse: {response[:200]}")
            raise
        except ValidationError as e:
            logger.error(f"Schema validation failed: {str(e)}")
            raise

    async def _fetch_categories(self) -> List[str]:
        """Fetch available product categories from API"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(PRODUCTS_CATEGORIES_ENDPOINT) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        # Adjust based on actual API response format
                        if isinstance(data, dict) and 'categories' in data:
                            return data['categories']
                        elif isinstance(data, list):
                            return data
                        else:
                            return list(data.keys()) if isinstance(data, dict) else []
                    else:
                        logger.error(f"Categories API failed with status {resp.status}")
                        raise Exception(f"Categories API returned status {resp.status}")
        except Exception as e:
            logger.error(f"Failed to fetch categories: {str(e)}")
            raise

    async def _fetch_subcategories(self) -> Dict[str, List[str]]:
        """Fetch available subcategories from API"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(PRODUCTS_CATEGORIES_ENDPOINT) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        # Adjust based on actual API response format
                        if isinstance(data, dict):
                            return {
                                cat: data[cat].get('subcategories', [])
                                for cat in data
                                if isinstance(data[cat], dict)
                            }
                        else:
                            logger.error("Subcategories API returned unexpected format")
                            raise Exception("Unexpected subcategories API response format")
                    else:
                        logger.error(f"Subcategories API failed with status {resp.status}")
                        raise Exception(f"Subcategories API returned status {resp.status}")
        except Exception as e:
            logger.error(f"Failed to fetch subcategories: {str(e)}")
            raise

    async def _fetch_conversation_history(self, session_id: str) -> List[Dict[str, str]]:
        """Fetch conversation history for context"""
        try:
            url = CONVERSATION_HISTORY_ENDPOINT.format(session_id=session_id)
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get('history', [])
                    else:
                        return []
        except Exception as e:
            logger.error(f"Error fetching conversation history: {str(e)}")
            return []
