"""
Abstract Vision Strategy

Base class for all extraction strategies.
Following Strategy Pattern: Different algorithms for extraction.
Following SRP: Strategy only knows HOW to extract, not WHAT to extract.
"""

import logging
from abc import ABC, abstractmethod
from typing import List, Optional

from ..domain.entities import Document, ExtractionResult
from ..domain.value_objects import Template, ExtractionOptions
from ..providers.base_vision_provider import BaseVisionProvider

logger = logging.getLogger(__name__)


class AbstractVisionStrategy(ABC):
    """
    Base class for all vision extraction strategies

    Strategies determine HOW to extract:
    - LocalVisionStrategy: Use local models only
    - CloudVisionStrategy: Use cloud APIs only
    - HybridVisionStrategy: Smart combination

    Following Strategy Pattern: Client code doesn't know which
    strategy is used - they all have the same interface.
    """

    @abstractmethod
    def get_name(self) -> str:
        """
        Get strategy name

        Returns:
            Strategy name (e.g., 'local', 'cloud', 'hybrid')
        """
        pass

    @abstractmethod
    async def extract(
        self,
        document: Document,
        template: Template,
        options: Optional[ExtractionOptions] = None
    ) -> ExtractionResult:
        """
        Extract data from document using this strategy

        Args:
            document: Document to process
            template: Template defining what to extract
            options: Extraction options

        Returns:
            ExtractionResult with extracted data

        Raises:
            ExtractionError: If extraction fails
        """
        pass

    @abstractmethod
    def supports_template(self, template: Template) -> bool:
        """
        Check if strategy supports this template type

        Args:
            template: Template to check

        Returns:
            True if supported, False otherwise
        """
        pass

    @abstractmethod
    def estimate_cost(self, document: Document) -> float:
        """
        Estimate cost for processing this document

        Args:
            document: Document to estimate cost for

        Returns:
            Estimated cost in USD
        """
        pass

    @abstractmethod
    def estimate_latency(self, document: Document) -> float:
        """
        Estimate latency for processing this document

        Args:
            document: Document to estimate latency for

        Returns:
            Estimated latency in seconds
        """
        pass

    def _build_extraction_prompt(
        self,
        template: Template,
        document: Document
    ) -> str:
        """
        Build prompt for LLM/vision model

        Args:
            template: Template with prompt template
            document: Document being processed

        Returns:
            Formatted prompt string
        """
        # Use template's prompt template
        prompt = template.prompt_template

        # Add document context if needed
        context = f"\n\nDocument type: {document.content_type}"
        if document.width and document.height:
            context += f"\nImage size: {document.width}x{document.height}"

        return prompt + context

    def _parse_json_response(self, response: str) -> dict:
        """
        Parse JSON response from model

        Handles common JSON parsing issues:
        - Markdown code blocks
        - Extra whitespace
        - Incomplete JSON

        Args:
            response: Raw response text

        Returns:
            Parsed dictionary
        """
        import json
        import re

        # Remove markdown code blocks
        response = re.sub(r'```json\s*', '', response)
        response = re.sub(r'```\s*', '', response)

        # Strip whitespace
        response = response.strip()

        # Try to parse
        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            logger.error(f"Response: {response[:500]}")

            # Try to extract JSON object
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(0))
                except:
                    pass

            # Return empty dict if parsing fails
            return {}

    def __repr__(self):
        return f"{self.__class__.__name__}(name='{self.get_name()}')"


class StrategySelector:
    """
    Selects optimal strategy based on requirements

    Following DDD: This is a Domain Service that knows business rules
    for strategy selection.
    """

    def __init__(self, strategies: Optional[List[AbstractVisionStrategy]] = None):
        """
        Initialize strategy selector

        Args:
            strategies: List of available strategies
        """
        self.strategies = strategies or []
        logger.info(f"Strategy selector initialized with {len(self.strategies)} strategies")

    def add_strategy(self, strategy: AbstractVisionStrategy):
        """Add a strategy to available strategies"""
        self.strategies.append(strategy)
        logger.info(f"Added strategy: {strategy.get_name()}")

    def select(
        self,
        template: Template,
        options: ExtractionOptions
    ) -> AbstractVisionStrategy:
        """
        Select optimal strategy based on requirements

        Selection algorithm:
        1. If strategy specified in options → use that
        2. If template requires specific features → filter
        3. Score remaining strategies (cost, latency, accuracy)
        4. Return highest scoring strategy

        Args:
            template: Template being used
            options: Extraction options

        Returns:
            Selected strategy

        Raises:
            ValueError: If no suitable strategy found
        """
        if not self.strategies:
            raise ValueError("No strategies available")

        # If strategy explicitly specified
        if options.strategy and options.strategy != 'auto':
            for strategy in self.strategies:
                if strategy.get_name() == options.strategy:
                    logger.info(f"Using specified strategy: {options.strategy}")
                    return strategy

        # Filter by template support
        suitable = [s for s in self.strategies if s.supports_template(template)]

        if not suitable:
            raise ValueError(
                f"No strategy supports template type: {template.template_type}"
            )

        # If preferred provider specified
        if options.preferred_provider:
            # Try to find strategy using that provider
            for strategy in suitable:
                if hasattr(strategy, 'provider'):
                    if strategy.provider.name == options.preferred_provider:
                        logger.info(f"Using preferred provider: {options.preferred_provider}")
                        return strategy

        # Score strategies
        scored = []
        dummy_doc = Document(file_path="dummy.jpg")  # For estimation

        for strategy in suitable:
            score = 0.0

            # Factor 1: Cost (lower is better)
            cost = strategy.estimate_cost(dummy_doc)
            if cost == 0.0:
                score += 50  # Free providers prioritized
            else:
                score -= cost * 100  # Penalize paid providers

            # Factor 2: Latency (lower is better)
            latency = strategy.estimate_latency(dummy_doc)
            if latency < 3.0:
                score += 20  # Fast providers preferred
            elif latency > 10.0:
                score -= 20  # Slow providers penalized

            # Factor 3: Strategy type preference
            if strategy.get_name() == 'hybrid':
                score += 10  # Hybrid preferred (best of both worlds)

            scored.append((score, strategy))

        # Sort by score (highest first)
        scored.sort(reverse=True, key=lambda x: x[0])

        selected = scored[0][1]
        logger.info(
            f"Selected strategy: {selected.get_name()} "
            f"(score: {scored[0][0]:.1f})"
        )

        return selected

    def get_available_strategies(self) -> List[str]:
        """Get list of available strategy names"""
        return [s.get_name() for s in self.strategies]

    def __repr__(self):
        return f"StrategySelector(strategies={len(self.strategies)})"
