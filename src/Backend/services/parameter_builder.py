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

            logger.info(f"[PARAM_BUILDER] Building parameters: confidence={confidence:.2f}, needs_clarification={needs_clarification}")
            logger.info(f"[PARAM_BUILDER] Entities: {entities}")

            # Case 1: High confidence, no clarification needed
            if confidence >= self.confidence_threshold and not needs_clarification:
                logger.info(f"[PARAM_BUILDER] CASE 1: High confidence ({confidence:.2f} >= {self.confidence_threshold}) + no clarification - building direct search parameters")
                return {
                    "type": "search",
                    "params": self._build_search_params(entities)
                }
            else:
                logger.info(f"[PARAM_BUILDER] Skipping CASE 1: confidence={confidence:.2f} < {self.confidence_threshold} OR needs_clarification={needs_clarification}")

            # Case 2: Needs clarification but we have strong user preferences
            if needs_clarification and self.use_user_preferences and user_preferences:
                pref_confidence = user_preferences.get("confidence", 0.0)
                logger.info(f"[PARAM_BUILDER] Checking CASE 2: user_preferences available, pref_confidence={pref_confidence:.2f}, threshold={self.preference_confidence_threshold}")
                if pref_confidence >= self.preference_confidence_threshold:
                    logger.info(f"[PARAM_BUILDER] CASE 2: Using user preferences (confidence={pref_confidence:.2f})")
                    enhanced_entities = self._apply_user_preferences(entities, user_preferences)
                    return {
                        "type": "search",
                        "params": self._build_search_params(enhanced_entities),
                        "applied_preferences": True
                    }
                else:
                    logger.info(f"[PARAM_BUILDER] Skipping CASE 2: pref_confidence={pref_confidence:.2f} < {self.preference_confidence_threshold}")
            else:
                logger.info(f"[PARAM_BUILDER] Skipping CASE 2: needs_clarification={needs_clarification}, use_user_preferences={self.use_user_preferences}, user_preferences={'present' if user_preferences else 'None'}")

            # Case 3: Needs clarification, generate quick actions
            if needs_clarification and self.fallback_to_quick_actions:
                logger.info(f"[PARAM_BUILDER] CASE 3: Needs clarification + fallback enabled - generating quick actions")
                quick_actions = await self._generate_quick_actions(entities)
                logger.info(f"[PARAM_BUILDER] Quick actions generated: {quick_actions}")
                return {
                    "type": "quick_actions",
                    "data": quick_actions
                }
            else:
                logger.info(f"[PARAM_BUILDER] Skipping CASE 3: needs_clarification={needs_clarification}, fallback_to_quick_actions={self.fallback_to_quick_actions}")

            # No fallback: If all cases are skipped, this is an error state
            logger.error("[PARAM_BUILDER] ERROR: All cases skipped - this should never happen")
            raise ValueError("Parameter building failed: all decision cases skipped")

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
            product_subcategory = entities.get("product_subcategory")
            effects = entities.get("effects")
            thc_range = entities.get("thc_range")
            cbd_range = entities.get("cbd_range")

            logger.info(f"[QUICK_ACTIONS] Determining quick action type:")
            logger.info(f"[QUICK_ACTIONS]   - strain_type: {strain_type}")
            logger.info(f"[QUICK_ACTIONS]   - product_subcategory: {product_subcategory}")
            logger.info(f"[QUICK_ACTIONS]   - effects: {effects}")
            logger.info(f"[QUICK_ACTIONS]   - thc_range: {thc_range}")
            logger.info(f"[QUICK_ACTIONS]   - cbd_range: {cbd_range}")
            logger.info(f"[QUICK_ACTIONS]   - clarification_reason: {clarification_reason}")

            # Determine which quick action type to generate
            if not product_subcategory and strain_type:
                # Need subcategory clarification
                logger.info(f"[QUICK_ACTIONS] BRANCH 1: Missing subcategory + has strain_type → _generate_category_quick_actions()")
                return await self._generate_category_quick_actions(strain_type, entities)
            elif not effects:
                # Need effect clarification
                logger.info(f"[QUICK_ACTIONS] BRANCH 2: Missing effects → _generate_effect_quick_actions()")
                return await self._generate_effect_quick_actions(entities)
            elif not thc_range and not cbd_range:
                # Need potency clarification
                logger.info(f"[QUICK_ACTIONS] BRANCH 3: Missing potency → _generate_potency_quick_actions()")
                return await self._generate_potency_quick_actions(entities)
            else:
                # Generic clarification
                logger.info(f"[QUICK_ACTIONS] BRANCH 4: Fallback → _generate_generic_quick_actions()")
                return self._generate_generic_quick_actions(entities)

        except Exception as e:
            logger.error(f"[QUICK_ACTIONS] ERROR: Quick action generation failed: {str(e)}", exc_info=True)
            logger.info(f"[QUICK_ACTIONS] Returning generic fallback due to exception")
            return self._generate_generic_quick_actions(entities)

    async def _generate_category_quick_actions(
        self,
        strain_type: str,
        entities: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate quick actions for subcategory selection"""

        logger.info(f"[CATEGORY_QA] Generating category quick actions for strain_type={strain_type}")

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

        logger.info(f"[CATEGORY_QA] Formatted prompt (first 200 chars): {prompt[:200]}...")
        logger.info(f"[CATEGORY_QA] Calling LLM with max_tokens={config.get('max_tokens', 200)}, temp={config.get('temperature', 0.7)}")

        # Call LLM
        response = await self._call_llm(
            prompt,
            max_tokens=config.get("max_tokens", 200),
            temperature=config.get("temperature", 0.7)
        )

        logger.info(f"[CATEGORY_QA] LLM response (first 200 chars): {str(response)[:200]}...")

        # Parse and validate
        result = self._parse_quick_actions_response(response)
        logger.info(f"[CATEGORY_QA] Parsed quick actions: {result}")
        return result

    async def _generate_effect_quick_actions(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Generate quick actions for effect selection"""

        logger.info(f"[EFFECT_QA] Generating effect quick actions")

        config = self.quick_actions_config.get("effect_clarification", {})
        prompt_template = config.get("prompt_template", "")

        product_category = entities.get("product_category", "cannabis products")
        prompt = prompt_template.format(product_category=product_category)

        logger.info(f"[EFFECT_QA] product_category={product_category}")
        logger.info(f"[EFFECT_QA] Formatted prompt (first 200 chars): {prompt[:200]}...")
        logger.info(f"[EFFECT_QA] Calling LLM with max_tokens={config.get('max_tokens', 200)}, temp={config.get('temperature', 0.7)}")

        response = await self._call_llm(
            prompt,
            max_tokens=config.get("max_tokens", 200),
            temperature=config.get("temperature", 0.7)
        )

        logger.info(f"[EFFECT_QA] LLM response (first 200 chars): {str(response)[:200]}...")

        result = self._parse_quick_actions_response(response)
        logger.info(f"[EFFECT_QA] Parsed quick actions: {result}")
        return result

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
            logger.info(f"[LLM_CALL] Starting LLM call with prompt length={len(prompt)}, max_tokens={max_tokens}, temp={temperature}")

            if hasattr(self.model, 'generate'):
                logger.info(f"[LLM_CALL] Using model.generate() method")
                response = await self.model.generate(
                    prompt=prompt,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
            elif hasattr(self.model, 'complete'):
                logger.info(f"[LLM_CALL] Using model.complete() method")
                response = await self.model.complete(
                    prompt=prompt,
                    max_new_tokens=max_tokens,
                    temperature=temperature
                )
            else:
                logger.info(f"[LLM_CALL] Using model() callable")
                response = await self.model(prompt, max_tokens=max_tokens, temperature=temperature)

            logger.info(f"[LLM_CALL] LLM responded, type={type(response)}")

            if isinstance(response, dict):
                # Check if response contains text/output field
                if 'text' in response or 'output' in response:
                    result = response.get('text', response.get('output', ''))
                    logger.info(f"[LLM_CALL] Extracted text from dict response, length={len(result)}")
                    return result
                else:
                    # If dict doesn't have text/output, convert to JSON string
                    result = json.dumps(response, ensure_ascii=False)
                    logger.info(f"[LLM_CALL] Converted dict to JSON string, length={len(result)}")
                    return result

            result = str(response)
            logger.info(f"[LLM_CALL] Converted response to string, length={len(result)}")
            return result

        except Exception as e:
            logger.error(f"[LLM_CALL] ERROR: LLM call failed: {str(e)}", exc_info=True)
            logger.error(f"[LLM_CALL] Prompt that caused error (first 300 chars): {prompt[:300]}...")
            raise

    def _parse_quick_actions_response(self, response: str) -> Dict[str, Any]:
        """Parse and validate quick actions JSON response"""
        try:
            logger.info(f"[PARSE_QA] Parsing quick actions response, length={len(response)}")
            logger.info(f"[PARSE_QA] Response (first 300 chars): {response[:300]}...")

            response = response.strip()
            start_idx = response.find('{')
            end_idx = response.rfind('}')

            if start_idx == -1 or end_idx == -1:
                logger.error(f"[PARSE_QA] No JSON found in response")
                raise ValueError("No JSON found in response")

            json_str = response[start_idx:end_idx + 1]
            logger.info(f"[PARSE_QA] Extracted JSON string (first 200 chars): {json_str[:200]}...")

            quick_actions = json.loads(json_str)
            logger.info(f"[PARSE_QA] Successfully parsed JSON: {quick_actions}")

            # Validate against schema
            schema = self.schemas.get("quick_actions_output", {})
            validate(instance=quick_actions, schema=schema)
            logger.info(f"[PARSE_QA] Schema validation passed")

            return quick_actions

        except (json.JSONDecodeError, ValidationError) as e:
            logger.error(f"[PARSE_QA] ERROR: Failed to parse quick actions: {str(e)}")
            logger.error(f"[PARSE_QA] Response that failed to parse (first 500 chars): {response[:500]}...")
            # No fallback - let the exception propagate
            raise
