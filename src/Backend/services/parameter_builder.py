"""
Parameter Builder Service
Builds API search parameters from extracted entities with user context
Handles confidence-based decision making: direct search, preference-based, or quick actions
"""
import json
import logging
from typing import Dict, Any, Optional, Union
from jsonschema import validate, ValidationError

logger = logging.getLogger(__name__)


class ParameterBuilder:
    """Builds search parameters from entities with context-aware decision logic"""

    def __init__(self, model_instance, intent_config: Dict[str, Any]):
        """
        Initialize parameter builder

        Args:
            model_instance: Direct reference to LLM model
            intent_config: Loaded intent.json configuration
        """
        self.model = model_instance
        self.config = intent_config.get("parameter_builder", {})
        self.quick_actions_config = intent_config.get("quick_actions", {})
        self.schemas = intent_config.get("schemas", {})

        # Load thresholds from config
        self.confidence_threshold = self.config.get("confidence_threshold", 0.7)
        self.preference_confidence_threshold = self.config.get("preference_confidence_threshold", 0.6)
        self.use_user_preferences = self.config.get("use_user_preferences", True)
        self.fallback_to_quick_actions = self.config.get("fallback_to_quick_actions", True)

    async def build_parameters(
        self,
        entities: Dict[str, Any],
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Build search parameters or quick actions based on entities and context

        Decision logic:
        1. High confidence + no clarification needed -> Build search params
        2. Needs clarification + strong preferences -> Apply preferences and build params
        3. Needs clarification + weak/no preferences -> Generate quick actions

        Args:
            entities: Extracted entities from entity_extractor
            user_preferences: Optional user preference data

        Returns:
            Either:
            - {"type": "search", "params": {...}} for direct search
            - {"type": "quick_actions", "data": {...}} for disambiguation
        """
        try:
            confidence = entities.get("confidence", 0.0)
            needs_clarification = entities.get("needs_clarification", False)

            logger.info(f"Building parameters: confidence={confidence:.2f}, needs_clarification={needs_clarification}")

            # Case 1: High confidence, no clarification needed
            if confidence >= self.confidence_threshold and not needs_clarification:
                logger.info("High confidence - building direct search parameters")
                return {
                    "type": "search",
                    "params": self._build_search_params(entities)
                }

            # Case 2: Needs clarification but we have strong user preferences
            if needs_clarification and self.use_user_preferences and user_preferences:
                pref_confidence = user_preferences.get("confidence", 0.0)
                if pref_confidence >= self.preference_confidence_threshold:
                    logger.info(f"Using user preferences (confidence={pref_confidence:.2f})")
                    enhanced_entities = self._apply_user_preferences(entities, user_preferences)
                    return {
                        "type": "search",
                        "params": self._build_search_params(enhanced_entities),
                        "applied_preferences": True
                    }

            # Case 3: Needs clarification, generate quick actions
            if needs_clarification and self.fallback_to_quick_actions:
                logger.info("Generating quick actions for disambiguation")
                quick_actions = await self._generate_quick_actions(entities)
                return {
                    "type": "quick_actions",
                    "data": quick_actions
                }

            # Fallback: Build params with what we have
            logger.warning("Fallback to building params with available entities")
            return {
                "type": "search",
                "params": self._build_search_params(entities)
            }

        except Exception as e:
            logger.error(f"Parameter building failed: {str(e)}", exc_info=True)
            # Return safe fallback
            return {
                "type": "error",
                "message": "Failed to build search parameters"
            }

    def _build_search_params(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert entities to API search parameters

        Maps entity_extraction_output schema to search_parameters schema
        """
        params = {}

        # Map strain type
        if entities.get("strain_type"):
            params["strainType"] = entities["strain_type"]

        # Map categories
        if entities.get("product_category"):
            params["category"] = entities["product_category"]

        if entities.get("product_subcategory"):
            params["subCategory"] = entities["product_subcategory"]

        # Map THC range
        thc_range = entities.get("thc_range")
        if thc_range and isinstance(thc_range, dict):
            if thc_range.get("min") is not None:
                params["minThc"] = thc_range["min"]
            if thc_range.get("max") is not None:
                params["maxThc"] = thc_range["max"]

        # Map CBD range
        cbd_range = entities.get("cbd_range")
        if cbd_range and isinstance(cbd_range, dict):
            if cbd_range.get("min") is not None:
                params["minCbd"] = cbd_range["min"]
            if cbd_range.get("max") is not None:
                params["maxCbd"] = cbd_range["max"]

        # Map price range
        price_range = entities.get("price_range")
        if price_range and isinstance(price_range, dict):
            if price_range.get("min") is not None:
                params["minPrice"] = price_range["min"]
            if price_range.get("max") is not None:
                params["maxPrice"] = price_range["max"]

        # Map effects
        if entities.get("effects"):
            params["effects"] = entities["effects"]

        # Default limit
        params["limit"] = 10

        logger.info(f"Built search params: {params}")
        return params

    def _apply_user_preferences(
        self,
        entities: Dict[str, Any],
        preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Enhance entities with user preferences for ambiguous queries

        Only applies preferences for fields not already specified in entities
        """
        enhanced = entities.copy()

        # Apply preferred subcategory if missing
        if not enhanced.get("product_subcategory") and preferences.get("favorite_subcategory"):
            enhanced["product_subcategory"] = preferences["favorite_subcategory"]
            logger.info(f"Applied preferred subcategory: {preferences['favorite_subcategory']}")

        # Apply preferred strain type if missing
        if not enhanced.get("strain_type") and preferences.get("favorite_strain_type"):
            enhanced["strain_type"] = preferences["favorite_strain_type"]
            logger.info(f"Applied preferred strain type: {preferences['favorite_strain_type']}")

        # Apply typical THC range if missing
        if not enhanced.get("thc_range") and preferences.get("typical_thc_range"):
            enhanced["thc_range"] = preferences["typical_thc_range"]
            logger.info(f"Applied typical THC range: {preferences['typical_thc_range']}")

        # Increase confidence after applying preferences
        enhanced["confidence"] = min(1.0, enhanced.get("confidence", 0.0) + 0.2)
        enhanced["needs_clarification"] = False

        return enhanced

    async def _generate_quick_actions(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate quick action buttons for disambiguation using LLM

        Based on clarification_reason, generates appropriate quick actions
        """
        try:
            clarification_reason = entities.get("clarification_reason", "")
            strain_type = entities.get("strain_type")

            # Determine which quick action type to generate
            if not entities.get("product_subcategory") and strain_type:
                # Need subcategory clarification
                return await self._generate_category_quick_actions(strain_type, entities)
            elif not entities.get("effects"):
                # Need effect clarification
                return await self._generate_effect_quick_actions(entities)
            elif not entities.get("thc_range") and not entities.get("cbd_range"):
                # Need potency clarification
                return await self._generate_potency_quick_actions(entities)
            else:
                # Generic clarification
                return self._generate_generic_quick_actions(entities)

        except Exception as e:
            logger.error(f"Quick action generation failed: {str(e)}")
            return self._generate_generic_quick_actions(entities)

    async def _generate_category_quick_actions(
        self,
        strain_type: str,
        entities: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate quick actions for subcategory selection"""

        config = self.quick_actions_config.get("category_clarification", {})
        prompt_template = config.get("prompt_template", "")

        # Build subcategories list
        available_subcategories = [
            "Dried Flower",
            "Pre-Rolls",
            "Infused Pre-Rolls",
            "Vapes",
            "Edibles",
            "Concentrates",
            "Beverages"
        ]

        # Format prompt
        prompt = prompt_template.format(
            strain_type=strain_type,
            available_subcategories=", ".join(available_subcategories)
        )

        # Call LLM
        response = await self._call_llm(
            prompt,
            max_tokens=config.get("max_tokens", 200),
            temperature=config.get("temperature", 0.7)
        )

        # Parse and validate
        return self._parse_quick_actions_response(response)

    async def _generate_effect_quick_actions(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Generate quick actions for effect selection"""

        config = self.quick_actions_config.get("effect_clarification", {})
        prompt_template = config.get("prompt_template", "")

        product_category = entities.get("product_category", "cannabis products")
        prompt = prompt_template.format(product_category=product_category)

        response = await self._call_llm(
            prompt,
            max_tokens=config.get("max_tokens", 200),
            temperature=config.get("temperature", 0.7)
        )

        return self._parse_quick_actions_response(response)

    async def _generate_potency_quick_actions(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Generate quick actions for potency selection"""

        config = self.quick_actions_config.get("potency_clarification", {})
        prompt_template = config.get("prompt_template", "")

        product_category = entities.get("product_category", "cannabis products")
        prompt = prompt_template.format(product_category=product_category)

        response = await self._call_llm(
            prompt,
            max_tokens=config.get("max_tokens", 200),
            temperature=config.get("temperature", 0.7)
        )

        return self._parse_quick_actions_response(response)

    def _generate_generic_quick_actions(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback: Generate generic quick actions without LLM"""

        return {
            "message": "What type of product are you looking for?",
            "quick_actions": [
                {"label": "🌸 Flower", "value": "show me dried flower", "icon": "🌸"},
                {"label": "🚬 Pre-Rolls", "value": "show me pre-rolls", "icon": "🚬"},
                {"label": "🍬 Edibles", "value": "show me edibles", "icon": "🍬"},
                {"label": "💨 Vapes", "value": "show me vapes", "icon": "💨"},
                {"label": "🥤 Beverages", "value": "show me beverages", "icon": "🥤"}
            ]
        }

    async def _call_llm(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Call LLM for quick action generation"""
        try:
            if hasattr(self.model, 'generate'):
                response = await self.model.generate(
                    prompt=prompt,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
            elif hasattr(self.model, 'complete'):
                response = await self.model.complete(
                    prompt=prompt,
                    max_new_tokens=max_tokens,
                    temperature=temperature
                )
            else:
                response = await self.model(prompt, max_tokens=max_tokens, temperature=temperature)

            if isinstance(response, dict):
                return response.get('text', response.get('output', str(response)))
            return str(response)

        except Exception as e:
            logger.error(f"LLM call failed: {str(e)}")
            raise

    def _parse_quick_actions_response(self, response: str) -> Dict[str, Any]:
        """Parse and validate quick actions JSON response"""
        try:
            response = response.strip()
            start_idx = response.find('{')
            end_idx = response.rfind('}')

            if start_idx == -1 or end_idx == -1:
                raise ValueError("No JSON found in response")

            json_str = response[start_idx:end_idx + 1]
            quick_actions = json.loads(json_str)

            # Validate against schema
            schema = self.schemas.get("quick_actions_output", {})
            validate(instance=quick_actions, schema=schema)

            return quick_actions

        except (json.JSONDecodeError, ValidationError) as e:
            logger.error(f"Failed to parse quick actions: {str(e)}")
            # Return generic fallback
            return {
                "message": "Could you please be more specific about what you're looking for?",
                "quick_actions": [
                    {"label": "Flower", "value": "dried flower"},
                    {"label": "Pre-Rolls", "value": "pre-rolls"},
                    {"label": "Edibles", "value": "edibles"}
                ]
            }
