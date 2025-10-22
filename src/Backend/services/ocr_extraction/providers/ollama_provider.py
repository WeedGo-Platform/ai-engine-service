"""
Ollama Vision Provider

Provides OCR extraction using Ollama-hosted vision models.
Supports: MiniCPM-V, Qwen-VL, LLaVA, and any other vision models in Ollama.

Following SRP: Provider only knows how to talk to Ollama.
Following KISS: Simple HTTP API calls, no complex setup.
"""

import base64
import logging
import httpx
import asyncio
from typing import Dict, Any, Optional
from pathlib import Path

from .base_vision_provider import BaseVisionProvider
from ..domain.entities import Document, AvailableModel
from ..domain.value_objects import VisionProviderConfig, ExtractionOptions
from ..domain.exceptions import (
    ProviderError,
    ProviderUnavailableError,
    ProviderTimeoutError
)

logger = logging.getLogger(__name__)


class OllamaVisionProvider(BaseVisionProvider):
    """
    Provider for Ollama-hosted vision models

    Ollama is a local model runtime that makes running LLMs easy.
    This provider works with any vision model in Ollama:
    - minicpm-v (recommended)
    - qwen2.5-vl
    - llava
    - etc.

    Cost: FREE (unlimited, local execution)
    """

    def __init__(
        self,
        config: VisionProviderConfig,
        model: AvailableModel,
        ollama_url: str = "http://localhost:11434"
    ):
        """
        Initialize Ollama provider

        Args:
            config: Provider configuration
            model: Model discovered at runtime
            ollama_url: Ollama API URL
        """
        super().__init__(config, model)
        self.ollama_url = ollama_url
        self.client = None

    async def initialize(self):
        """Initialize Ollama connection"""
        try:
            # Create async HTTP client
            self.client = httpx.AsyncClient(
                base_url=self.ollama_url,
                timeout=httpx.Timeout(60.0)  # 60s timeout
            )

            # Test connection
            is_healthy = await self.check_health()

            if not is_healthy:
                raise ProviderUnavailableError(
                    self.name,
                    "Ollama is not responding"
                )

            self.is_initialized = True
            logger.info(f"✅ Ollama provider initialized: {self.model.name}")

        except Exception as e:
            logger.error(f"Failed to initialize Ollama provider: {e}")
            raise ProviderUnavailableError(self.name, str(e))

    async def extract(
        self,
        document: Document,
        prompt: str,
        options: Optional[ExtractionOptions] = None
    ) -> Dict[str, Any]:
        """
        Extract data using Ollama vision model

        Args:
            document: Document to process
            prompt: Extraction prompt
            options: Extraction options

        Returns:
            Extracted data dictionary

        Raises:
            ProviderError: If extraction fails
        """
        if not self.is_initialized:
            await self.initialize()

        options = options or ExtractionOptions()

        try:
            # Load and encode image
            if document.image_bytes:
                # Document has raw bytes (e.g., from upload)
                image_b64 = base64.b64encode(document.image_bytes).decode('utf-8')
                img_size_kb = len(document.image_bytes) / 1024
                logger.info(f"📸 Processing image from bytes: {img_size_kb:.1f} KB")
            else:
                # Document has file path
                image_b64 = self._load_and_encode_image(document.file_path)
                logger.info(f"📸 Processing image from file: {document.file_path}")

            # Build request
            request_data = {
                "model": self.model.name,
                "prompt": prompt,
                "images": [image_b64],
                "format": "json",  # Request JSON response
                "stream": False,
                "options": {
                    "temperature": 0.0,  # Zero temperature for maximum accuracy, no creativity
                    "top_k": 1,  # Only use most likely token
                    "top_p": 0.1,  # Minimal sampling diversity
                    "num_predict": 500,  # Max tokens
                }
            }
            
            logger.info(f"🤖 Calling Ollama model: {self.model.name} with temp=0.0, top_k=1")

            # Call Ollama API
            response = await self.client.post(
                "/api/generate",
                json=request_data,
                timeout=options.timeout_seconds
            )

            response.raise_for_status()
            result = response.json()

            # Extract response text
            response_text = result.get('response', '{}')

            # Parse JSON
            import json
            try:
                data = json.loads(response_text)
                # DEBUG: Log all extracted fields
                logger.info(f"✅ Ollama extraction complete:")
                logger.info(f"   Product: {data.get('product_name', 'N/A')}")
                logger.info(f"   Brand: {data.get('brand', 'N/A')}")
                logger.info(f"   Barcode: {data.get('barcode', 'N/A')}")
                logger.info(f"   Size: {data.get('size_variant', 'N/A')}")
            except json.JSONDecodeError:
                # Try to extract JSON from response
                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group(0))
                    if 'barcode' in data:
                        img_size = len(document.image_bytes) if document.image_bytes else 0
                        logger.info(f"🔍 DEBUG - Ollama extracted barcode (from regex): '{data.get('barcode')}' from image ({img_size} bytes)")
                else:
                    data = {"raw_text": response_text}

            return data

        except httpx.TimeoutException:
            raise ProviderTimeoutError(self.name, options.timeout_seconds)

        except httpx.HTTPStatusError as e:
            raise ProviderError(f"Ollama API error: {e.response.status_code}")

        except Exception as e:
            logger.error(f"Ollama extraction failed: {e}")
            raise ProviderError(f"Extraction failed: {e}")

    async def check_health(self) -> bool:
        """
        Check if Ollama is healthy

        Returns:
            True if healthy, False otherwise
        """
        try:
            if not self.client:
                self.client = httpx.AsyncClient(base_url=self.ollama_url)

            # Simple health check - list models
            response = await self.client.get("/api/tags", timeout=5.0)
            return response.status_code == 200

        except Exception as e:
            logger.warning(f"Ollama health check failed: {e}")
            return False

    def _load_and_encode_image(self, file_path: str) -> str:
        """
        Load image and encode as base64

        Args:
            file_path: Path to image file

        Returns:
            Base64-encoded image string
        """
        try:
            with open(file_path, 'rb') as f:
                image_data = f.read()

            # Encode to base64
            b64_data = base64.b64encode(image_data).decode('utf-8')

            return b64_data

        except Exception as e:
            raise ProviderError(f"Failed to load image: {e}")

    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.client:
            await self.client.aclose()
