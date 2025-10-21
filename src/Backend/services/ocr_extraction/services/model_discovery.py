"""
Model Discovery Service

Automatically discovers available vision models at runtime.
No hardcoded providers - adapts to what's installed.

Following DDD: This is a Domain Service that orchestrates model discovery.
Following KISS: Simple directory scanning, no complex config needed.
"""

import logging
import os
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from ..domain.entities import AvailableModel
from ..domain.enums import ProviderType

logger = logging.getLogger(__name__)


@dataclass
class DiscoveryResult:
    """Result of model discovery scan"""
    models_found: List[AvailableModel]
    ollama_available: bool
    gemini_api_key: Optional[str]
    huggingface_models: List[str]
    errors: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'models_found': [
                {
                    'name': m.name,
                    'provider_type': m.provider_type.value if hasattr(m.provider_type, 'value') else str(m.provider_type),
                    'size_mb': m.size_mb,
                    'model_path': m.model_path
                }
                for m in self.models_found
            ],
            'ollama_available': self.ollama_available,
            'gemini_api_key_present': self.gemini_api_key is not None,
            'huggingface_models': self.huggingface_models,
            'errors': self.errors
        }


class ModelDiscoveryService:
    """
    Discovers available vision models at runtime

    Scans for:
    1. Ollama models (via ollama list)
    2. Hugging Face models (in ocr/models/ directory)
    3. Cloud API keys (environment variables)

    No hardcoded provider names - completely dynamic!
    """

    def __init__(
        self,
        models_dir: Optional[str] = None,
        check_ollama: bool = True,
        check_env_vars: bool = True
    ):
        """
        Initialize model discovery service

        Args:
            models_dir: Directory to scan for local models (default: Backend/models/LLM/ocr)
            check_ollama: Whether to check for Ollama installation
            check_env_vars: Whether to check environment variables for API keys
        """
        if models_dir:
            self.models_dir = Path(models_dir)
        else:
            # Default to models/LLM/ocr relative to Backend directory
            backend_dir = Path(__file__).parent.parent.parent.parent
            self.models_dir = backend_dir / "models" / "LLM" / "ocr"

        self.check_ollama = check_ollama
        self.check_env_vars = check_env_vars

        # Create models directory if it doesn't exist
        self.models_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Model discovery initialized: {self.models_dir.absolute()}")

    def discover_all(self) -> DiscoveryResult:
        """
        Discover all available models and providers

        Returns:
            DiscoveryResult with all discovered models
        """
        models_found = []
        errors = []

        logger.info("🔍 Starting model discovery...")

        # 1. Check Ollama models
        ollama_available = False
        if self.check_ollama:
            ollama_models, ollama_err = self._discover_ollama_models()
            if ollama_models:
                models_found.extend(ollama_models)
                ollama_available = True
                logger.info(f"✅ Found {len(ollama_models)} Ollama models")
            elif ollama_err:
                errors.append(ollama_err)

        # 2. Check Hugging Face models in directory
        hf_models, hf_err = self._discover_huggingface_models()
        if hf_models:
            models_found.extend(hf_models)
            logger.info(f"✅ Found {len(hf_models)} Hugging Face models")
        elif hf_err:
            errors.append(hf_err)

        # 3. Check for cloud API keys
        gemini_key = None
        if self.check_env_vars:
            gemini_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
            if gemini_key:
                logger.info("✅ Gemini API key found")

        # Build result
        result = DiscoveryResult(
            models_found=models_found,
            ollama_available=ollama_available,
            gemini_api_key=gemini_key,
            huggingface_models=[m.name for m in hf_models],
            errors=errors
        )

        logger.info(
            f"🎯 Discovery complete: {len(models_found)} models, "
            f"{len(errors)} errors"
        )

        return result

    def _discover_ollama_models(self) -> tuple[List[AvailableModel], Optional[str]]:
        """
        Discover Ollama models

        Returns:
            Tuple of (models_list, error_message)
        """
        models = []
        error = None

        try:
            # Check if Ollama is installed
            result = subprocess.run(
                ['ollama', 'list'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode != 0:
                return [], "Ollama not installed or not running"

            # Parse ollama list output
            lines = result.stdout.strip().split('\n')

            if len(lines) <= 1:  # Just header or empty
                return [], None

            # Skip header line
            for line in lines[1:]:
                parts = line.split()
                if not parts:
                    continue

                model_name = parts[0]

                # Filter for vision models
                vision_keywords = [
                    'minicpm-v', 'qwen', 'llava', 'vision',
                    'vl', 'ocr', 'paddle'
                ]

                if any(kw in model_name.lower() for kw in vision_keywords):
                    model = AvailableModel(
                        name=model_name,
                        provider_type='ollama',
                        model_path=f'ollama://{model_name}',
                        size_mb=0.0  # Ollama doesn't expose size easily
                    )
                    models.append(model)

            return models, None

        except FileNotFoundError:
            return [], "Ollama not installed (command not found)"
        except subprocess.TimeoutExpired:
            return [], "Ollama command timed out"
        except Exception as e:
            return [], f"Error discovering Ollama models: {e}"

    def _discover_huggingface_models(self) -> tuple[List[AvailableModel], Optional[str]]:
        """
        Discover Hugging Face models in local directory

        Scans ocr/models/ for subdirectories containing model files.

        Returns:
            Tuple of (models_list, error_message)
        """
        models = []
        error = None

        try:
            if not self.models_dir.exists():
                return [], "Models directory doesn't exist"

            # Scan for model directories
            for item in self.models_dir.iterdir():
                if not item.is_dir():
                    continue

                # Check if directory contains model files
                has_config = (item / 'config.json').exists()
                weight_files = ['pytorch_model.bin', 'model.safetensors', 'paddle_model.pdparams']
                has_weights = any((item / f).exists() for f in weight_files)

                model_dir = item

                # If config found but no weights, check subdirectories (common for Git cloned models)
                if has_config and not has_weights:
                    for subdir in item.iterdir():
                        if not subdir.is_dir() or subdir.name.startswith('.'):
                            continue

                        sub_has_config = (subdir / 'config.json').exists()
                        sub_has_weights = any((subdir / f).exists() for f in weight_files)

                        if sub_has_config and sub_has_weights:
                            # Found actual model in subdirectory
                            model_dir = subdir
                            has_config = True
                            has_weights = True
                            logger.info(f"Found model in subdirectory: {subdir.name}")
                            break

                if has_config and has_weights:
                    # Determine provider type
                    provider_type = 'huggingface'
                    if (model_dir / 'paddle_model.pdparams').exists():
                        provider_type = 'paddleocr'

                    # Calculate directory size
                    total_size = sum(
                        f.stat().st_size
                        for f in model_dir.rglob('*')
                        if f.is_file()
                    )
                    size_mb = total_size / (1024 * 1024)

                    model = AvailableModel(
                        name=model_dir.name,
                        provider_type=provider_type,
                        model_path=str(model_dir),
                        size_mb=size_mb
                    )
                    models.append(model)
                    logger.info(f"Discovered HuggingFace model: {model_dir.name} ({size_mb:.1f}MB)")

            return models, None

        except Exception as e:
            return [], f"Error discovering Hugging Face models: {e}"

    def get_recommended_model(self, models: List[AvailableModel]) -> Optional[AvailableModel]:
        """
        Get recommended model based on priority

        Priority order:
        1. Ollama MiniCPM-V (best performance)
        2. Ollama Qwen-VL (good alternative)
        3. PaddleOCR-VL (best for complex documents)
        4. Any other Ollama vision model
        5. Any Hugging Face model

        Args:
            models: List of available models

        Returns:
            Recommended model or None
        """
        if not models:
            return None

        # Priority 1: Ollama MiniCPM-V
        for model in models:
            if model.is_ollama_model and 'minicpm-v' in model.name.lower():
                logger.info(f"🌟 Recommended: {model.name} (best performance)")
                return model

        # Priority 2: Ollama Qwen
        for model in models:
            if model.is_ollama_model and 'qwen' in model.name.lower():
                logger.info(f"🌟 Recommended: {model.name} (good alternative)")
                return model

        # Priority 3: PaddleOCR-VL
        for model in models:
            if model.is_paddleocr_model:
                logger.info(f"🌟 Recommended: {model.name} (best for documents)")
                return model

        # Priority 4: Any Ollama vision model
        for model in models:
            if model.is_ollama_model:
                logger.info(f"🌟 Recommended: {model.name} (Ollama default)")
                return model

        # Priority 5: Any Hugging Face model
        logger.info(f"🌟 Recommended: {models[0].name} (first available)")
        return models[0]

    def print_discovery_report(self, result: DiscoveryResult):
        """
        Print human-readable discovery report

        Args:
            result: DiscoveryResult to print
        """
        print("\n" + "="*70)
        print(" OCR MODEL DISCOVERY REPORT")
        print("="*70 + "\n")

        if not result.models_found:
            print("❌ NO MODELS FOUND")
            print("\n💡 To use OCR extraction, install at least one model:")
            print("\n  Option 1: Ollama (Recommended)")
            print("    curl -fsSL https://ollama.com/install.sh | sh")
            print("    ollama pull minicpm-v:latest")
            print("\n  Option 2: Hugging Face")
            print(f"    Download model to: {self.models_dir}")
            print()
            return

        print(f"✅ Found {len(result.models_found)} model(s):\n")

        for i, model in enumerate(result.models_found, 1):
            print(f"{i}. {model.name}")
            print(f"   Type: {model.provider_type}")
            print(f"   Path: {model.model_path}")
            if model.size_mb > 0:
                print(f"   Size: {model.size_mb:.1f} MB")
            print()

        # Print recommended
        recommended = self.get_recommended_model(result.models_found)
        if recommended:
            print(f"🌟 Recommended: {recommended.name}")
            print()

        # Print cloud options
        if result.gemini_api_key:
            print("☁️  Cloud fallback available:")
            print("   - Gemini API (FREE tier)")
            print()

        # Print errors
        if result.errors:
            print("⚠️  Warnings:")
            for error in result.errors:
                print(f"   - {error}")
            print()

        print("="*70 + "\n")
