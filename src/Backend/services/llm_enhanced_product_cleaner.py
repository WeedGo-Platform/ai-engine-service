"""
LLM-Enhanced Product Data Cleaner
Uses local LLM router for intelligent data extraction and cleaning
"""

import json
import logging
from typing import Dict, Any, Optional
from services.product_data_cleaner import ProductDataCleaner

logger = logging.getLogger(__name__)


class LLMEnhancedProductCleaner:
    """
    Enhanced product cleaner that uses LLM for intelligent extraction

    Strategy:
    1. Try rule-based cleaning first (fast, free)
    2. If confidence < threshold, use LLM enhancement
    3. Use local LLM router (prioritizes free/local models)
    4. Fallback to rules-only if LLM fails
    """

    def __init__(self, llm_router=None, confidence_threshold: float = 0.6):
        """
        Initialize LLM-enhanced cleaner

        Args:
            llm_router: LLMRouter instance from services/llm_gateway/router.py
            confidence_threshold: Use LLM if confidence below this (0.6 = 60%)
        """
        self.rule_based_cleaner = ProductDataCleaner()
        self.llm_router = llm_router
        self.confidence_threshold = confidence_threshold

        if llm_router:
            logger.info("LLM-enhanced cleaner initialized with router")
        else:
            logger.warning("No LLM router provided - using rules-only mode")

    async def clean_product_data(
        self,
        data: Dict[str, Any],
        force_llm: bool = False
    ) -> Dict[str, Any]:
        """
        Clean product data using hybrid approach

        Args:
            data: Raw scraped product data
            force_llm: Force LLM enhancement even if confidence is high

        Returns:
            Cleaned and enriched product data
        """
        # Step 1: Apply rule-based cleaning (always fast, no cost)
        cleaned = self.rule_based_cleaner.clean_product_data(data.copy())

        # Calculate initial confidence
        initial_confidence = self._calculate_confidence(cleaned)

        # Step 2: Decide if LLM enhancement is needed
        should_use_llm = (
            self.llm_router is not None and  # LLM available
            (force_llm or initial_confidence < self.confidence_threshold)  # Low confidence
        )

        if not should_use_llm:
            logger.info(
                f"Skipping LLM enhancement - confidence {initial_confidence:.2f} "
                f">= {self.confidence_threshold} (threshold)"
            )
            cleaned['enhancement_method'] = 'rules_only'
            return cleaned

        # Step 3: Use LLM for intelligent extraction
        try:
            llm_enhanced = await self._llm_enhance(cleaned)
            llm_enhanced['enhancement_method'] = 'llm_enhanced'

            # Boost confidence for LLM-verified data
            llm_enhanced['confidence'] = min(
                llm_enhanced.get('confidence', 0.5) + 0.15,
                0.95
            )

            logger.info(
                f"LLM enhancement successful - "
                f"confidence: {initial_confidence:.2f} → {llm_enhanced['confidence']:.2f}"
            )

            return llm_enhanced

        except Exception as e:
            logger.warning(f"LLM enhancement failed: {e}. Falling back to rules-only.")
            cleaned['enhancement_method'] = 'rules_only_fallback'
            return cleaned

    async def _llm_enhance(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use LLM to extract structured data and validate

        Args:
            data: Rule-cleaned data

        Returns:
            LLM-enhanced data
        """
        from services.llm_gateway.types import RequestContext, TaskType

        # Build prompt for structured extraction
        prompt = self._build_extraction_prompt(data)

        # Create request context (optimized for speed + cost)
        context = RequestContext(
            task_type=TaskType.EXTRACTION,  # Fast, not reasoning-heavy
            estimated_tokens=300,  # Small prompt
            temperature=0.0,  # Deterministic output
            max_tokens=512,  # Limit response size
            requires_reasoning=False,  # Simple extraction task
            requires_speed=True,  # Prefer fast models
            requires_streaming=False,
            is_production=True  # But still use free tiers if available
        )

        # Call LLM router (automatically selects best provider)
        messages = [
            {
                "role": "system",
                "content": "You are a product data extraction specialist. Extract structured product information from messy text. Return valid JSON only."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

        result = await self.llm_router.complete(messages, context)

        # Parse LLM response
        try:
            llm_data = json.loads(result.content)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks
            content = result.content.strip()
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
                llm_data = json.loads(json_str)
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0].strip()
                llm_data = json.loads(json_str)
            else:
                raise ValueError(f"Could not parse LLM response as JSON: {content}")

        # Merge LLM data with rule-cleaned data (LLM takes precedence)
        enhanced = data.copy()

        # Update main fields if LLM provided better values
        for key in ['name', 'brand', 'category']:
            if llm_data.get(key):
                enhanced[key] = llm_data[key]

        # Merge attributes
        if llm_data.get('attributes'):
            enhanced['attributes'] = enhanced.get('attributes', {})
            enhanced['attributes'].update(llm_data['attributes'])

        # Add LLM metadata
        enhanced['llm_metadata'] = {
            'provider': result.provider,
            'model': result.model,
            'cost': result.cost,
            'latency': result.latency,
            'tokens': f"{result.tokens_input}→{result.tokens_output}"
        }

        logger.info(
            f"LLM extraction: {result.provider}/{result.model} - "
            f"${result.cost:.6f}, {result.latency:.2f}s"
        )

        return enhanced

    def _build_extraction_prompt(self, data: Dict[str, Any]) -> str:
        """
        Build structured prompt for LLM extraction

        Args:
            data: Product data to enhance

        Returns:
            Formatted prompt string
        """
        name = data.get('name', 'Unknown')
        brand = data.get('brand', 'Unknown')
        description = data.get('description', '')

        prompt = f"""Extract structured product information from this accessory product.

PRODUCT DATA:
Name: {name}
Brand: {brand}
Description: {description}

TASK:
Extract and return JSON with these exact fields (use null if not found):

{{
  "name": "cleaned product name (remove junk words like 'new', 'sealed', 'authentic', 'best price')",
  "brand": "manufacturer brand name (not distributor). Examples: RAW (not 'Raw Sports'), Zig-Zag (not 'zig zag')",
  "category": "one of: rolling_papers, filter_tips, grinders, lighters, storage, pipes, cones, trays, vaporizers",
  "attributes": {{
    "quantity": total_count_as_integer_or_null,
    "materials": ["hemp", "cotton", "paper", "metal", "glass"],
    "size": "size descriptor (king_size, 1_1_4, wide, slim, etc)",
    "features": ["perforated", "natural", "unrefined"]
  }}
}}

RULES:
1. Quantity: Extract TOTAL count (e.g., "5 packs of 50" = 250)
2. Brand: Use manufacturer name, normalize to proper case
3. Name: Remove ALL marketing junk words
4. Category: Pick the most specific category that matches
5. Only include attributes you can confidently extract from the text

Return ONLY valid JSON, no explanation."""

        return prompt

    def _calculate_confidence(self, data: Dict[str, Any]) -> float:
        """
        Calculate confidence score for cleaned data

        Args:
            data: Cleaned product data

        Returns:
            Confidence score (0.0-1.0)
        """
        score = 0.0

        # Name present and clean (30 points)
        if data.get('name'):
            score += 0.30
            if len(data['name']) < 100:  # Not too long
                score += 0.05

        # Brand present (20 points)
        if data.get('brand'):
            score += 0.20

        # Category inferred (15 points)
        if data.get('category'):
            score += 0.15

        # Attributes extracted (25 points)
        attributes = data.get('attributes', {})
        if attributes:
            score += 0.10
            if attributes.get('quantity'):
                score += 0.05
            if attributes.get('materials'):
                score += 0.05
            if attributes.get('size') or attributes.get('features'):
                score += 0.05

        # Image URL (10 points)
        if data.get('image_url'):
            score += 0.10

        return min(score, 1.0)

    def set_llm_router(self, llm_router):
        """
        Set or update LLM router

        Args:
            llm_router: LLMRouter instance
        """
        self.llm_router = llm_router
        logger.info("Updated LLM router for enhanced cleaner")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cleaner statistics

        Returns:
            Dictionary with usage stats
        """
        stats = {
            'confidence_threshold': self.confidence_threshold,
            'llm_available': self.llm_router is not None
        }

        if self.llm_router:
            stats['llm_router'] = self.llm_router.get_stats()

        return stats


# Convenience function for easy integration
async def clean_with_llm(
    data: Dict[str, Any],
    llm_router=None,
    force_llm: bool = False
) -> Dict[str, Any]:
    """
    Clean product data using LLM enhancement

    Args:
        data: Raw product data
        llm_router: LLMRouter instance
        force_llm: Force LLM enhancement

    Returns:
        Cleaned product data
    """
    cleaner = LLMEnhancedProductCleaner(llm_router)
    return await cleaner.clean_product_data(data, force_llm=force_llm)
