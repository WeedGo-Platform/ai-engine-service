"""
Voice Model Router - Multi-Provider Voice Synthesis Orchestration

Routes voice synthesis requests to the best available provider based on:
- Manual provider selection (like LLM router)
- Fallback chain configuration
- Provider health and availability
- Task requirements (quality vs speed vs language)
- Cost optimization (local vs cloud)

Supports:
- Local voice cloning: XTTS v2, StyleTTS2, Piper
- Cloud TTS: Google TTS, Azure TTS, IBM Watson
- Zero-shot voice cloning with personality voice samples
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from enum import Enum

from .xtts_v2_handler import XTTSv2Handler
from .styletts2_handler import StyleTTS2Handler
from .piper_tts import PiperTTSHandler
from .google_tts_handler import GoogleTTSHandler
from .base_handler import SynthesisResult, TTSHandler

logger = logging.getLogger(__name__)


class VoiceProvider(Enum):
    """Available voice providers"""
    XTTS_V2 = "xtts_v2"
    STYLETTS2 = "styletts2"
    PIPER = "piper"
    GOOGLE_TTS = "google_tts"
    AZURE_TTS = "azure_tts"
    IBM_WATSON = "ibm_watson"


class VoiceQuality(Enum):
    """Voice quality levels"""
    HIGHEST = "highest"  # StyleTTS2 (human-level)
    HIGH = "high"  # XTTS v2, Cloud providers
    MEDIUM = "medium"  # Piper (neural)
    FAST = "fast"  # Fastest available


class SynthesisContext:
    """Context for voice synthesis requests"""

    def __init__(
        self,
        personality_id: Optional[str] = None,
        language: str = "en",
        speed: float = 1.0,
        pitch: float = 0.0,
        quality: VoiceQuality = VoiceQuality.HIGH,
        prefer_local: bool = True,
        voice_sample_path: Optional[str] = None,
        # StyleTTS2 advanced controls
        alpha: Optional[float] = None,
        beta: Optional[float] = None,
        diffusion_steps: Optional[int] = None,
        embedding_scale: Optional[float] = None
    ):
        self.personality_id = personality_id
        self.language = language
        self.speed = speed
        self.pitch = pitch
        self.quality = quality
        self.prefer_local = prefer_local
        self.voice_sample_path = voice_sample_path
        # StyleTTS2 params
        self.alpha = alpha
        self.beta = beta
        self.diffusion_steps = diffusion_steps
        self.embedding_scale = embedding_scale
        self.timestamp = datetime.now()


class VoiceModelRouter:
    """
    Intelligent voice provider router with automatic failover

    Features:
    - Manual provider selection (configurable per personality)
    - Automatic fallback chain
    - Local-first optimization (XTTS v2/StyleTTS2/Piper)
    - Cloud fallback (Google/Azure/IBM)
    - Voice sample caching
    - Performance tracking

    Usage:
        router = VoiceModelRouter()
        await router.initialize()

        result = await router.synthesize(
            text="Hello, welcome to WeedGo!",
            context=SynthesisContext(
                personality_id="marcel_custom",
                language="en",
                quality=VoiceQuality.HIGHEST
            )
        )
    """

    def __init__(self, device: str = "cpu"):
        """Initialize the voice router

        Args:
            device: Device for local models ('cpu' or 'cuda')
        """
        self.device = device
        self.providers: Dict[str, TTSHandler] = {}

        # Statistics
        self.total_requests = 0
        self.total_cost = 0.0  # Cloud providers cost
        self.request_history: List[Dict] = []

        # Fallback chains per quality level
        # NOTE: Piper moved higher in chains to ensure fallback works even if voice cloning providers fail
        self.fallback_chains = {
            VoiceQuality.HIGHEST: [
                VoiceProvider.STYLETTS2,
                VoiceProvider.XTTS_V2,
                VoiceProvider.PIPER,  # Fallback to Piper if cloning fails
                VoiceProvider.GOOGLE_TTS
            ],
            VoiceQuality.HIGH: [
                VoiceProvider.XTTS_V2,
                VoiceProvider.STYLETTS2,
                VoiceProvider.PIPER,  # Fallback to Piper if cloning fails
                VoiceProvider.GOOGLE_TTS,
                VoiceProvider.AZURE_TTS
            ],
            VoiceQuality.MEDIUM: [
                VoiceProvider.PIPER,
                VoiceProvider.XTTS_V2,
                VoiceProvider.GOOGLE_TTS
            ],
            VoiceQuality.FAST: [
                VoiceProvider.PIPER,
                VoiceProvider.GOOGLE_TTS,
                VoiceProvider.AZURE_TTS
            ]
        }

        logger.info(f"VoiceModelRouter initialized (device: {device})")

    async def initialize(self) -> bool:
        """Initialize all local voice providers

        Returns:
            True if at least one provider initialized successfully
        """
        try:
            logger.info("Initializing voice providers...")

            # Initialize local providers in parallel
            init_tasks = []

            # XTTS v2 (multilingual voice cloning)
            logger.info("Loading XTTS v2...")
            xtts_handler = XTTSv2Handler(device=self.device)
            init_tasks.append(self._init_provider("xtts_v2", xtts_handler))

            # StyleTTS2 (highest quality voice cloning)
            logger.info("Loading StyleTTS2...")
            styletts2_handler = StyleTTS2Handler()
            init_tasks.append(self._init_provider("styletts2", styletts2_handler))

            # Piper (fast neural TTS)
            logger.info("Loading Piper...")
            piper_handler = PiperTTSHandler()
            init_tasks.append(self._init_provider("piper", piper_handler))

            # Google Cloud TTS (conditional - requires credentials)
            import os
            if os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'):
                logger.info("Loading Google Cloud TTS...")
                google_handler = GoogleTTSHandler()
                init_tasks.append(self._init_provider("google_tts", google_handler))
            else:
                logger.info("Skipping Google TTS (no GOOGLE_APPLICATION_CREDENTIALS)")

            # Wait for all initializations
            results = await asyncio.gather(*init_tasks, return_exceptions=True)

            # Check results
            success_count = sum(1 for r in results if r is True)
            total_providers = len(init_tasks)
            logger.info(f"✅ {success_count}/{total_providers} providers initialized")

            if success_count == 0:
                logger.error("No voice providers initialized successfully")
                return False

            # Cloud providers (Azure/IBM) initialized on-demand
            logger.info("Additional cloud providers (Azure/IBM) available for future implementation")

            return True

        except Exception as e:
            logger.error(f"Voice router initialization failed: {e}")
            return False

    async def _init_provider(self, name: str, handler: TTSHandler) -> bool:
        """Initialize a provider and register it

        Args:
            name: Provider name
            handler: Handler instance

        Returns:
            True if initialized successfully
        """
        try:
            success = await handler.initialize()
            if success:
                self.providers[name] = handler
                logger.info(f"✅ Registered provider: {name}")
                return True
            else:
                logger.warning(f"⚠️  Provider failed to initialize: {name}")
                return False
        except Exception as e:
            logger.error(f"❌ Provider initialization error ({name}): {e}")
            return False

    async def synthesize(
        self,
        text: str,
        context: SynthesisContext,
        provider: Optional[VoiceProvider] = None,
        max_retries: int = 3
    ) -> SynthesisResult:
        """Generate speech using best available provider

        Args:
            text: Text to synthesize
            context: Synthesis context with requirements
            provider: Force specific provider (None = use fallback chain)
            max_retries: Maximum number of providers to try

        Returns:
            SynthesisResult with audio and metadata

        Raises:
            RuntimeError: If all providers fail
        """
        if not self.providers:
            raise RuntimeError("No providers initialized")

        self.total_requests += 1
        attempted_providers = []

        # Determine provider chain
        if provider:
            # Force specific provider
            provider_chain = [provider]
        else:
            # Use quality-based fallback chain
            provider_chain = self.fallback_chains[context.quality]

        for attempt, provider_enum in enumerate(provider_chain[:max_retries]):
            try:
                provider_name = provider_enum.value

                # Skip if provider not available
                if provider_name not in self.providers:
                    logger.warning(f"Provider not available: {provider_name}")
                    continue

                attempted_providers.append(provider_name)

                logger.info(
                    f"Attempt {attempt + 1}/{max_retries}: "
                    f"Using {provider_name} for synthesis"
                )

                # Get handler
                handler = self.providers[provider_name]

                # Prepare parameters
                kwargs = {
                    "text": text,
                    "language": context.language,
                    "speed": context.speed,
                    "pitch": context.pitch
                }

                # Add voice reference
                if context.personality_id:
                    kwargs["voice"] = context.personality_id
                elif context.voice_sample_path:
                    kwargs["speaker_wav"] = context.voice_sample_path

                # Add StyleTTS2 advanced parameters
                if provider_name == "styletts2":
                    if context.alpha is not None:
                        kwargs["alpha"] = context.alpha
                    if context.beta is not None:
                        kwargs["beta"] = context.beta
                    if context.diffusion_steps is not None:
                        kwargs["diffusion_steps"] = context.diffusion_steps
                    if context.embedding_scale is not None:
                        kwargs["embedding_scale"] = context.embedding_scale

                # Generate audio
                result = await handler.synthesize(**kwargs)

                # Record success
                self._record_request(provider_name, result, text, context)

                logger.info(
                    f"✓ Success: {provider_name} - "
                    f"{result.duration_ms:.0f}ms audio, "
                    f"{result.sample_rate}Hz"
                )

                return result

            except Exception as e:
                logger.error(
                    f"❌ Provider {provider_name} failed: {e}"
                )
                continue

        # All providers exhausted
        raise RuntimeError(
            f"All voice providers failed. Tried: {', '.join(attempted_providers)}"
        )

    async def load_personality_voice(
        self,
        personality_id: str,
        voice_sample_path: str,
        providers: Optional[List[VoiceProvider]] = None
    ) -> Dict[str, bool]:
        """Load voice sample for a personality across providers

        Args:
            personality_id: Unique personality ID
            voice_sample_path: Path to voice sample audio
            providers: List of providers to load (None = all voice cloning providers)

        Returns:
            Dict mapping provider name to success status
        """
        if providers is None:
            # Load for all voice cloning providers
            providers = [
                VoiceProvider.XTTS_V2,
                VoiceProvider.STYLETTS2
            ]

        results = {}

        for provider_enum in providers:
            provider_name = provider_enum.value

            if provider_name not in self.providers:
                logger.warning(f"Provider not available: {provider_name}")
                results[provider_name] = False
                continue

            try:
                handler = self.providers[provider_name]

                # Only load for handlers that support voice caching
                if hasattr(handler, 'load_voice_sample'):
                    success = await handler.load_voice_sample(
                        personality_id,
                        voice_sample_path
                    )
                    results[provider_name] = success
                else:
                    logger.warning(
                        f"Provider {provider_name} doesn't support voice caching"
                    )
                    results[provider_name] = False

            except Exception as e:
                logger.error(
                    f"Failed to load voice for {provider_name}: {e}"
                )
                results[provider_name] = False

        success_count = sum(1 for r in results.values() if r)
        logger.info(
            f"Loaded personality '{personality_id}' voice sample: "
            f"{success_count}/{len(results)} providers"
        )

        return results

    async def remove_personality_voice(
        self,
        personality_id: str,
        providers: Optional[List[VoiceProvider]] = None
    ) -> Dict[str, bool]:
        """Remove voice sample for a personality

        Args:
            personality_id: Personality ID to remove
            providers: List of providers (None = all)

        Returns:
            Dict mapping provider name to success status
        """
        if providers is None:
            providers = [VoiceProvider.XTTS_V2, VoiceProvider.STYLETTS2]

        results = {}

        for provider_enum in providers:
            provider_name = provider_enum.value

            if provider_name not in self.providers:
                results[provider_name] = False
                continue

            try:
                handler = self.providers[provider_name]

                if hasattr(handler, 'remove_voice_sample'):
                    success = await handler.remove_voice_sample(personality_id)
                    results[provider_name] = success
                else:
                    results[provider_name] = False

            except Exception as e:
                logger.error(f"Failed to remove voice from {provider_name}: {e}")
                results[provider_name] = False

        return results

    def _record_request(
        self,
        provider_name: str,
        result: SynthesisResult,
        text: str,
        context: SynthesisContext
    ):
        """Record request in history for analytics

        Args:
            provider_name: Provider used
            result: Synthesis result
            text: Input text
            context: Synthesis context
        """
        self.request_history.append({
            "timestamp": datetime.now().isoformat(),
            "provider": provider_name,
            "text_length": len(text),
            "audio_duration_ms": result.duration_ms,
            "sample_rate": result.sample_rate,
            "personality_id": context.personality_id,
            "language": context.language,
            "quality": context.quality.value
        })

        # Keep only last 1000 requests
        if len(self.request_history) > 1000:
            self.request_history = self.request_history[-1000:]

    def get_statistics(self) -> Dict:
        """Get router statistics

        Returns:
            Statistics dictionary
        """
        provider_counts = {}
        for request in self.request_history:
            provider = request["provider"]
            provider_counts[provider] = provider_counts.get(provider, 0) + 1

        return {
            "total_requests": self.total_requests,
            "total_cost": self.total_cost,
            "providers_available": list(self.providers.keys()),
            "provider_usage": provider_counts,
            "request_history_size": len(self.request_history)
        }

    async def cleanup(self):
        """Clean up all providers"""
        try:
            cleanup_tasks = []

            for provider_name, handler in self.providers.items():
                logger.info(f"Cleaning up {provider_name}...")
                cleanup_tasks.append(handler.cleanup())

            await asyncio.gather(*cleanup_tasks, return_exceptions=True)

            self.providers.clear()
            logger.info("Voice router cleaned up")

        except Exception as e:
            logger.error(f"Cleanup error: {e}")
