"""
Hugging Face Vision Provider

Provides OCR extraction using Hugging Face transformers models.
Supports: PaddleOCR-VL, Qwen-VL, and other vision-language models.

Following SRP: Provider only knows how to load and run HF models.
Following KISS: Direct model loading, no complex pipeline.
"""

import logging
import torch
from typing import Dict, Any, Optional
from pathlib import Path
from PIL import Image

from .base_vision_provider import BaseVisionProvider
from ..domain.entities import Document, AvailableModel
from ..domain.value_objects import VisionProviderConfig, ExtractionOptions
from ..domain.exceptions import (
    ProviderError,
    ProviderUnavailableError,
)

logger = logging.getLogger(__name__)


class HuggingFaceVisionProvider(BaseVisionProvider):
    """
    Provider for Hugging Face vision models

    Loads models directly from local directory.
    Works with:
    - PaddleOCR-VL (recommended for documents)
    - Qwen-VL
    - Any other vision-language model

    Cost: FREE (unlimited, local execution)
    """

    def __init__(
        self,
        config: VisionProviderConfig,
        model: AvailableModel
    ):
        """
        Initialize Hugging Face provider

        Args:
            config: Provider configuration
            model: Model discovered at runtime
        """
        super().__init__(config, model)
        self.hf_model = None
        self.processor = None
        self.device = None

    async def initialize(self):
        """
        Initialize Hugging Face model

        Loads model from disk into memory.
        Uses GPU if available, falls back to CPU.
        """
        try:
            # Determine device
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Using device: {self.device}")

            # Import required libraries
            from transformers import AutoModel, AutoProcessor

            model_path = self.model.model_path

            logger.info(f"Loading model from: {model_path}")

            # Load processor (tokenizer + image processor)
            self.processor = AutoProcessor.from_pretrained(
                model_path,
                trust_remote_code=True  # Required for some models
            )

            # Load model
            self.hf_model = AutoModel.from_pretrained(
                model_path,
                trust_remote_code=True,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
            )

            # Move to device
            self.hf_model.to(self.device)

            # Set to eval mode
            self.hf_model.eval()

            self.is_initialized = True
            logger.info(f"✅ Hugging Face model loaded: {self.model.name}")

        except Exception as e:
            logger.error(f"Failed to load Hugging Face model: {e}")
            raise ProviderUnavailableError(self.name, str(e))

    async def extract(
        self,
        document: Document,
        prompt: str,
        options: Optional[ExtractionOptions] = None
    ) -> Dict[str, Any]:
        """
        Extract data using Hugging Face vision model

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
            # Load image
            image = Image.open(document.file_path).convert('RGB')

            # Preprocess
            inputs = self.processor(
                text=prompt,
                images=image,
                return_tensors="pt"
            )

            # Move to device
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            # Generate
            with torch.no_grad():
                outputs = self.hf_model.generate(
                    **inputs,
                    max_new_tokens=500,
                    temperature=0.1,
                    do_sample=False
                )

            # Decode
            response_text = self.processor.decode(
                outputs[0],
                skip_special_tokens=True
            )

            # Parse JSON response
            data = self._parse_json_response(response_text)

            return data

        except Exception as e:
            logger.error(f"Hugging Face extraction failed: {e}")
            raise ProviderError(f"Extraction failed: {e}")

    async def check_health(self) -> bool:
        """
        Check if model is loaded and healthy

        Returns:
            True if healthy, False otherwise
        """
        return self.is_initialized and self.hf_model is not None

    def _parse_json_response(self, response: str) -> dict:
        """
        Parse JSON response from model

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

    def __del__(self):
        """Cleanup when provider is deleted"""
        if self.hf_model is not None:
            del self.hf_model
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
