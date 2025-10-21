"""
Gemini Vision Provider (FREE Tier Only)

Provides OCR extraction using Google Gemini vision API.
STRICTLY enforces free tier limits - never makes paid calls!

Following SRP: Provider only knows how to talk to Gemini API.
Following KISS: Simple API calls with rate limiting.
"""

import logging
import asyncio
from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional, List
from PIL import Image

from .base_vision_provider import BaseVisionProvider
from ..domain.entities import Document, AvailableModel
from ..domain.value_objects import VisionProviderConfig, ExtractionOptions
from ..domain.exceptions import (
    ProviderError,
    ProviderUnavailableError,
    RateLimitError
)

logger = logging.getLogger(__name__)


class GeminiVisionProvider(BaseVisionProvider):
    """
    Provider for Google Gemini Vision API - FREE TIER ONLY

    Free Tier Limits (strictly enforced):
    - 15 requests per minute (RPM)
    - 1,500 requests per day (RPD)
    - Total: ~45,000 requests per month

    Model: gemini-2.0-flash-exp (best free model)
    Cost: $0.00 (completely free!)
    """

    # Free tier limits (conservative)
    MAX_RPM = 15
    MAX_RPD = 1500

    def __init__(
        self,
        config: VisionProviderConfig,
        model: AvailableModel,
        api_key: str
    ):
        """
        Initialize Gemini provider

        Args:
            config: Provider configuration
            model: Model info (virtual model for Gemini)
            api_key: Gemini API key
        """
        super().__init__(config, model)
        self.api_key = api_key
        self.genai_model = None

        # Rate limiting state
        self.request_timestamps: List[datetime] = []
        self.daily_count: Dict[date, int] = {}

    async def initialize(self):
        """Initialize Gemini API"""
        try:
            # Import Gemini SDK
            import google.generativeai as genai

            # Configure API key
            genai.configure(api_key=self.api_key)

            # Create model
            self.genai_model = genai.GenerativeModel('gemini-2.0-flash-exp')

            self.is_initialized = True
            logger.info("✅ Gemini provider initialized (FREE tier)")

        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")
            raise ProviderUnavailableError(self.name, str(e))

    async def extract(
        self,
        document: Document,
        prompt: str,
        options: Optional[ExtractionOptions] = None
    ) -> Dict[str, Any]:
        """
        Extract data using Gemini vision API

        Args:
            document: Document to process
            prompt: Extraction prompt
            options: Extraction options

        Returns:
            Extracted data dictionary

        Raises:
            RateLimitError: If free tier limits exceeded
            ProviderError: If extraction fails
        """
        if not self.is_initialized:
            await self.initialize()

        # Check rate limits BEFORE making request
        self._check_rate_limits()

        try:
            # Load image
            image = Image.open(document.file_path)

            # Generate content
            response = await self.genai_model.generate_content_async([
                prompt,
                image
            ])

            # Record successful request
            self._record_request()

            # Parse response
            response_text = response.text

            # Parse JSON
            data = self._parse_json_response(response_text)

            return data

        except Exception as e:
            logger.error(f"Gemini extraction failed: {e}")
            raise ProviderError(f"Extraction failed: {e}")

    async def check_health(self) -> bool:
        """
        Check if Gemini API is accessible

        Returns:
            True if healthy, False otherwise
        """
        return self.is_initialized and self.genai_model is not None

    def _check_rate_limits(self):
        """
        Check if we can make a request within free tier limits

        Raises:
            RateLimitError: If limits would be exceeded
        """
        now = datetime.now()
        today = now.date()

        # Clean old timestamps (older than 1 minute)
        minute_ago = now - timedelta(minutes=1)
        self.request_timestamps = [
            ts for ts in self.request_timestamps
            if ts > minute_ago
        ]

        # Check RPM limit
        rpm_count = len(self.request_timestamps)
        if rpm_count >= self.MAX_RPM:
            wait_seconds = 60 - (now - self.request_timestamps[0]).seconds
            raise RateLimitError(
                self.name,
                f"RPM limit ({self.MAX_RPM})",
                retry_after=wait_seconds
            )

        # Check daily limit
        daily_count = self.daily_count.get(today, 0)
        if daily_count >= self.MAX_RPD:
            raise RateLimitError(
                self.name,
                f"Daily limit ({self.MAX_RPD})",
                retry_after=None  # Wait until midnight
            )

        logger.debug(
            f"Gemini rate limits OK: "
            f"RPM={rpm_count}/{self.MAX_RPM}, "
            f"Daily={daily_count}/{self.MAX_RPD}"
        )

    def _record_request(self):
        """Record a successful request for rate limiting"""
        now = datetime.now()
        today = now.date()

        # Record timestamp
        self.request_timestamps.append(now)

        # Increment daily counter
        self.daily_count[today] = self.daily_count.get(today, 0) + 1

        # Clean old daily counters (keep last 7 days)
        week_ago = today - timedelta(days=7)
        self.daily_count = {
            d: count
            for d, count in self.daily_count.items()
            if d > week_ago
        }

    def _parse_json_response(self, response: str) -> dict:
        """
        Parse JSON response from Gemini

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
        except json.JSONDecodeError:
            # Try to extract JSON object
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(0))
                except:
                    pass

            # Return raw text if parsing fails
            return {"raw_text": response}

    def get_stats(self) -> Dict[str, Any]:
        """
        Get provider statistics including rate limit info

        Returns:
            Dictionary with stats
        """
        base_stats = super().get_stats()

        # Add rate limit info
        today = datetime.now().date()
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)

        recent_requests = [
            ts for ts in self.request_timestamps
            if ts > minute_ago
        ]

        base_stats.update({
            'rate_limits': {
                'current_rpm': len(recent_requests),
                'max_rpm': self.MAX_RPM,
                'rpm_remaining': self.MAX_RPM - len(recent_requests),
                'daily_count': self.daily_count.get(today, 0),
                'max_rpd': self.MAX_RPD,
                'daily_remaining': self.MAX_RPD - self.daily_count.get(today, 0),
            }
        })

        return base_stats
