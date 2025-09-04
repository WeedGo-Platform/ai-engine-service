"""
Automatic Language Router
Routes conversations to appropriate models based on detected language
Maintains language continuity throughout the session
"""
import logging
from typing import Dict, Optional, Any, List
from dataclasses import dataclass
import time

logger = logging.getLogger(__name__)

@dataclass
class LanguageSession:
    """Tracks language state for a session"""
    session_id: str
    primary_language: str
    detected_languages: List[str]
    language_switches: int
    last_language: str
    created_at: float
    updated_at: float
    message_count: int
    
class AutomaticLanguageRouter:
    """
    Automatically routes messages to appropriate models based on language
    No configuration needed - fully dynamic
    """
    
    def __init__(self, universal_language_system, model_orchestrator, model_manager):
        self.language_system = universal_language_system
        self.orchestrator = model_orchestrator
        self.model_manager = model_manager
        self.sessions: Dict[str, LanguageSession] = {}
        
    async def process_message(
        self,
        message: str,
        session_id: str,
        context: Optional[Dict] = None,
        force_language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a message in any language automatically
        
        Args:
            message: User message in any language
            session_id: Session identifier
            context: Optional context
            force_language: Optional language override
        """
        
        start_time = time.time()
        
        # Get or create session
        session = self._get_or_create_session(session_id)
        
        # Detect language
        if force_language:
            language_profile = self.language_system.language_profiles.get(force_language)
            if not language_profile:
                # Create basic profile for forced language
                from services.universal_language_system import LanguageProfile
                language_profile = LanguageProfile(
                    code=force_language,
                    name=force_language,
                    native_name=force_language,
                    script="unknown",
                    direction="ltr",
                    confidence=1.0,
                    detected_by="forced",
                    sample_text=message[:100]
                )
        else:
            language_profile = await self.language_system.detect_language(
                message, 
                session_id,
                use_context=True
            )
        
        detected_language = language_profile.code
        logger.info(f"Processing message in {detected_language} ({language_profile.name})")
        
        # Update session
        self._update_session(session, detected_language)
        
        # Check if language is supported
        capable_models = await self._get_capable_models(detected_language)
        
        if not capable_models:
            # No direct support - try translation pipeline
            logger.warning(f"No models for {detected_language}, using translation pipeline")
            response = await self._process_with_translation(
                message, detected_language, context
            )
        else:
            # Process in native language
            response = await self._process_native(
                message, detected_language, capable_models, context
            )
        
        # Ensure response maintains language continuity
        if response and "text" in response:
            response["text"] = await self.language_system.maintain_language_continuity(
                session_id,
                detected_language,
                response["text"]
            )
        
        # Add language metadata
        response["language_info"] = {
            "detected": detected_language,
            "name": language_profile.name,
            "native_name": language_profile.native_name,
            "confidence": language_profile.confidence,
            "script": language_profile.script,
            "direction": language_profile.direction,
            "processing_time_ms": (time.time() - start_time) * 1000
        }
        
        return response
    
    def _get_or_create_session(self, session_id: str) -> LanguageSession:
        """Get existing session or create new one"""
        
        if session_id not in self.sessions:
            self.sessions[session_id] = LanguageSession(
                session_id=session_id,
                primary_language="en",
                detected_languages=[],
                language_switches=0,
                last_language="en",
                created_at=time.time(),
                updated_at=time.time(),
                message_count=0
            )
        
        return self.sessions[session_id]
    
    def _update_session(self, session: LanguageSession, language: str):
        """Update session with new language detection"""
        
        session.message_count += 1
        session.updated_at = time.time()
        
        if language != session.last_language:
            session.language_switches += 1
        
        session.last_language = language
        
        if language not in session.detected_languages:
            session.detected_languages.append(language)
        
        # Update primary language (most used)
        if session.message_count > 3:
            # After a few messages, determine primary language
            lang_counts = {}
            for lang in session.detected_languages:
                lang_counts[lang] = lang_counts.get(lang, 0) + 1
            session.primary_language = max(lang_counts.items(), key=lambda x: x[1])[0]
    
    async def _get_capable_models(self, language: str) -> List[str]:
        """Get models capable of handling the language"""
        
        capable = []
        
        for model_id, model in self.model_manager.models.items():
            profile = model.get_profile()
            if language in profile.supported_languages:
                capable.append(model_id)
        
        # If no specific support, check for multilingual models
        if not capable:
            for model_id, model in self.model_manager.models.items():
                profile = model.get_profile()
                from services.unified_model_interface import ModelCapability
                if ModelCapability.MULTILINGUAL in profile.capabilities:
                    capable.append(model_id)
        
        return capable
    
    async def _process_native(
        self,
        message: str,
        language: str,
        capable_models: List[str],
        context: Optional[Dict]
    ) -> Dict[str, Any]:
        """Process message in its native language"""
        
        # Enhance context with language info
        enhanced_context = context or {}
        enhanced_context["language"] = language
        enhanced_context["capable_models"] = capable_models
        
        # Use orchestrator to process with best strategy
        result = await self.orchestrator.solve_task(
            task=message,
            task_type="conversation",
            language=language,
            context=enhanced_context,
            constraints={
                "max_time_ms": 3000,
                "min_quality": 0.7,
                "preferred_models": capable_models
            }
        )
        
        return {
            "text": result.get("response", ""),
            "metadata": result.get("metadata", {}),
            "strategy": result.get("metadata", {}).get("strategy", "native"),
            "models_used": result.get("metadata", {}).get("models_used", [])
        }
    
    async def _process_with_translation(
        self,
        message: str,
        source_language: str,
        context: Optional[Dict]
    ) -> Dict[str, Any]:
        """Process using translation pipeline"""
        
        # Translate to English
        translated_message = await self.language_system.translate_if_needed(
            message,
            source_language,
            "en"
        )
        
        # Process in English
        result = await self.orchestrator.solve_task(
            task=translated_message,
            task_type="conversation",
            language="en",
            context=context
        )
        
        # Translate response back
        if result and "response" in result:
            translated_response = await self.language_system.translate_if_needed(
                result["response"],
                "en",
                source_language
            )
        else:
            translated_response = ""
        
        return {
            "text": translated_response,
            "metadata": result.get("metadata", {}),
            "strategy": "translation_pipeline",
            "original_message": message,
            "translated_message": translated_message,
            "english_response": result.get("response", ""),
            "models_used": result.get("metadata", {}).get("models_used", [])
        }
    
    async def handle_multilingual_conversation(
        self,
        messages: List[Dict[str, str]],
        session_id: str
    ) -> List[Dict[str, Any]]:
        """
        Handle a conversation that may include multiple languages
        
        Args:
            messages: List of {"text": str, "language": optional str}
            session_id: Session identifier
        """
        
        responses = []
        context = {"conversation_history": []}
        
        for msg in messages:
            text = msg.get("text", "")
            force_lang = msg.get("language")
            
            # Process message
            response = await self.process_message(
                text,
                session_id,
                context,
                force_lang
            )
            
            responses.append(response)
            
            # Update context
            context["conversation_history"].append({
                "user": text,
                "assistant": response.get("text", ""),
                "language": response.get("language_info", {}).get("detected", "en")
            })
        
        return responses
    
    async def detect_and_switch_language(
        self,
        message: str,
        session_id: str,
        current_language: str
    ) -> Optional[str]:
        """
        Detect if user has switched languages mid-conversation
        
        Returns new language if switched, None otherwise
        """
        
        # Detect language of new message
        new_language = await self.language_system.detect_language(
            message,
            session_id,
            use_context=False  # Don't use context to detect switch
        )
        
        if new_language.code != current_language and new_language.confidence > 0.7:
            logger.info(f"Language switch detected: {current_language} -> {new_language.code}")
            return new_language.code
        
        return None
    
    def get_session_languages(self, session_id: str) -> Dict[str, Any]:
        """Get language statistics for a session"""
        
        if session_id not in self.sessions:
            return {"error": "Session not found"}
        
        session = self.sessions[session_id]
        
        return {
            "session_id": session_id,
            "primary_language": session.primary_language,
            "current_language": session.last_language,
            "all_languages": session.detected_languages,
            "language_switches": session.language_switches,
            "message_count": session.message_count,
            "session_duration_seconds": time.time() - session.created_at
        }
    
    def get_global_language_stats(self) -> Dict[str, Any]:
        """Get global language statistics across all sessions"""
        
        stats = {
            "total_sessions": len(self.sessions),
            "languages_used": {},
            "avg_switches_per_session": 0,
            "multilingual_sessions": 0
        }
        
        total_switches = 0
        
        for session in self.sessions.values():
            # Count language usage
            for lang in session.detected_languages:
                stats["languages_used"][lang] = stats["languages_used"].get(lang, 0) + 1
            
            # Count multilingual sessions
            if len(session.detected_languages) > 1:
                stats["multilingual_sessions"] += 1
            
            total_switches += session.language_switches
        
        if self.sessions:
            stats["avg_switches_per_session"] = total_switches / len(self.sessions)
        
        # Sort languages by usage
        stats["top_languages"] = sorted(
            stats["languages_used"].items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        return stats
    
    async def suggest_language(
        self,
        session_id: str,
        user_location: Optional[str] = None,
        user_preference: Optional[str] = None
    ) -> str:
        """
        Suggest the best language for a user
        
        Args:
            session_id: Session identifier
            user_location: Optional location info
            user_preference: Optional stated preference
        """
        
        # Check user preference first
        if user_preference:
            # Verify we can support it
            capable = await self._get_capable_models(user_preference)
            if capable:
                return user_preference
        
        # Check session history
        if session_id in self.sessions:
            session = self.sessions[session_id]
            if session.primary_language:
                return session.primary_language
        
        # Check location-based suggestion
        if user_location:
            # Map locations to languages (simplified)
            location_languages = {
                "US": "en", "UK": "en", "CA": "en",
                "MX": "es", "ES": "es", "AR": "es",
                "FR": "fr", "BE": "fr",
                "DE": "de", "AT": "de",
                "IT": "it",
                "BR": "pt", "PT": "pt",
                "CN": "zh", "TW": "zh",
                "JP": "ja",
                "KR": "ko",
                "IN": "hi",
                "SA": "ar", "AE": "ar",
                "RU": "ru",
                "NL": "nl",
                "SE": "sv",
                "NO": "no",
                "DK": "da",
                "FI": "fi",
                "PL": "pl",
                "TR": "tr",
                "ID": "id",
                "TH": "th",
                "VN": "vi"
            }
            
            if user_location in location_languages:
                suggested = location_languages[user_location]
                capable = await self._get_capable_models(suggested)
                if capable:
                    return suggested
        
        # Default to English
        return "en"