"""
Domain-Agnostic AI Engine
Main engine that uses domain plugins for specialized behavior
"""
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
import sys

# Add parent paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.domain_manager import DomainManager
from core.interfaces.domain_plugin import DomainContext, TaskType
from services.unified_model_interface import UnifiedModelManager
from services.multi_model_orchestrator import MultiModelOrchestrator

logger = logging.getLogger(__name__)

class DomainAgnosticAIEngine:
    """
    Main AI Engine that can operate in any domain
    Uses plugins for domain-specific behavior
    """
    
    def __init__(self, config: Dict = None):
        """Initialize the AI engine"""
        self.config = config or {}
        self.domain_manager = DomainManager()
        self.model_manager = None
        self.orchestrator = None
        self.current_context: Dict[str, DomainContext] = {}  # Session contexts
        
    async def initialize(self):
        """Initialize all components"""
        logger.info("Initializing Domain-Agnostic AI Engine...")
        
        # Initialize domain manager
        await self.domain_manager.initialize()
        
        # Initialize model manager
        self.model_manager = UnifiedModelManager()
        await self.model_manager.discover_and_load_models()
        
        # Initialize orchestrator
        self.orchestrator = MultiModelOrchestrator(
            model_manager=self.model_manager
        )
        
        logger.info(f"AI Engine initialized with {len(self.domain_manager.domains)} domains")
        logger.info(f"Available domains: {', '.join(self.domain_manager.domains.keys())}")
        
    async def process(
        self,
        message: str,
        domain: Optional[str] = None,
        session_id: Optional[str] = None,
        task_type: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Process a message using the appropriate domain
        
        Args:
            message: User message
            domain: Domain to use (optional, uses active domain)
            session_id: Session identifier for context
            task_type: Type of task (optional, will be detected)
            metadata: Additional metadata
            
        Returns:
            Processed response with domain-specific formatting
        """
        
        # Select domain
        if domain:
            self.domain_manager.switch_domain(domain)
        
        domain_plugin = self.domain_manager.get_active_domain()
        if not domain_plugin:
            return {
                "error": "No domain selected",
                "message": "Please specify a domain (e.g., 'budtender', 'healthcare', 'legal')"
            }
        
        # Get or create context
        context = self._get_or_create_context(session_id, metadata)
        
        # Detect task type if not provided
        if not task_type:
            task_type = await self._detect_task_type(message, domain_plugin)
        else:
            task_type = TaskType[task_type.upper()]
        
        try:
            # Validate input
            is_valid, error = domain_plugin.validate_input(message, task_type)
            if not is_valid:
                return {
                    "error": "Invalid input",
                    "message": error,
                    "domain": domain_plugin.get_config().name
                }
            
            # Check if should escalate
            if domain_plugin.should_escalate(message, context):
                return {
                    "escalate": True,
                    "message": "This request requires human assistance. Connecting you to a specialist...",
                    "domain": domain_plugin.get_config().name
                }
            
            # Pre-process message
            processed_message = domain_plugin.pre_process(message, context)
            
            # Get domain-specific prompt
            system_prompt = domain_plugin.get_system_prompt()
            task_prompt = domain_plugin.get_prompt(
                task_type,
                input=processed_message,
                context=context,
                language=context.language
            )
            
            # Get examples for few-shot learning
            examples = domain_plugin.get_examples(task_type)
            
            # Get constraints
            constraints = domain_plugin.get_constraints(task_type)
            
            # Search knowledge if needed
            knowledge = []
            if task_type in [TaskType.INFORMATION, TaskType.RECOMMENDATION, TaskType.CONSULTATION]:
                knowledge = domain_plugin.search_knowledge(processed_message, limit=5)
            
            # Build complete prompt
            full_prompt = self._build_full_prompt(
                system_prompt,
                task_prompt,
                examples,
                constraints,
                knowledge
            )
            
            # Call AI model through orchestrator
            ai_response = await self.orchestrator.solve_task(
                task=full_prompt,
                task_type="conversation",
                language=context.language,
                context={
                    "domain": domain_plugin.get_config().name,
                    "task": task_type.value,
                    "session": session_id
                }
            )
            
            # Extract response text - handle both string and dict responses
            if isinstance(ai_response, str):
                response_text = ai_response
            elif isinstance(ai_response, dict):
                response_text = ai_response.get("response", "")
            else:
                response_text = str(ai_response)
            
            # Validate response
            is_valid, error = domain_plugin.validate_response(response_text, task_type)
            if not is_valid:
                logger.warning(f"Response validation failed: {error}")
                response_text = domain_plugin.get_fallback_response(task_type, context)
            
            # Post-process response
            final_response = domain_plugin.post_process(response_text, context)
            
            # Format response
            formatted = domain_plugin.format_response(final_response, task_type, context)
            
            # Add metadata
            formatted["session_id"] = session_id
            formatted["domain"] = domain_plugin.get_config().name
            formatted["task_type"] = task_type.value
            # Handle both string and dict ai_response
            if isinstance(ai_response, dict):
                formatted["model_info"] = ai_response.get("metadata", {})
            else:
                formatted["model_info"] = {}
            
            # Log interaction
            domain_plugin.log_interaction(message, final_response, context)
            
            # Update context
            self._update_context(session_id, message, final_response)
            
            return formatted
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            error_message = domain_plugin.handle_error(e, task_type, context)
            return {
                "error": "Processing failed",
                "message": error_message,
                "domain": domain_plugin.get_config().name
            }
    
    def _get_or_create_context(self, session_id: str, metadata: Dict = None) -> DomainContext:
        """Get or create session context"""
        if not session_id:
            session_id = "default"
        
        if session_id not in self.current_context:
            self.current_context[session_id] = DomainContext(
                session_id=session_id,
                language=metadata.get("language", "en") if metadata else "en",
                location=metadata.get("location") if metadata else None,
                preferences=metadata.get("preferences", {}) if metadata else {},
                history=[],
                metadata=metadata or {}
            )
        
        return self.current_context[session_id]
    
    def _update_context(self, session_id: str, user_message: str, ai_response: str):
        """Update session context with interaction"""
        if session_id in self.current_context:
            context = self.current_context[session_id]
            context.history.append({
                "role": "user",
                "content": user_message
            })
            context.history.append({
                "role": "assistant",
                "content": ai_response
            })
            
            # Keep only last 10 interactions
            if len(context.history) > 20:
                context.history = context.history[-20:]
    
    async def _detect_task_type(self, message: str, domain_plugin) -> TaskType:
        """Detect the task type from the message"""
        message_lower = message.lower()
        
        # Simple keyword-based detection (can be enhanced with AI)
        if any(word in message_lower for word in ["hello", "hi", "hey", "greet"]):
            return TaskType.GREETING
        elif any(word in message_lower for word in ["search", "find", "looking for", "show me"]):
            return TaskType.SEARCH
        elif any(word in message_lower for word in ["recommend", "suggest", "what should", "need something"]):
            return TaskType.RECOMMENDATION
        elif any(word in message_lower for word in ["what is", "tell me about", "explain", "how does"]):
            return TaskType.INFORMATION
        elif any(word in message_lower for word in ["help", "assist", "support", "problem"]):
            return TaskType.SUPPORT
        elif any(word in message_lower for word in ["consult", "advice", "guide", "should i"]):
            return TaskType.CONSULTATION
        elif any(word in message_lower for word in ["learn", "teach", "educate", "course"]):
            return TaskType.EDUCATION
        else:
            return TaskType.INFORMATION
    
    def _build_full_prompt(
        self,
        system_prompt: str,
        task_prompt: str,
        examples: List[Dict],
        constraints: List[str],
        knowledge: List[Dict]
    ) -> str:
        """Build complete prompt with all components"""
        parts = []
        
        # System prompt
        parts.append(f"System: {system_prompt}")
        
        # Examples (few-shot)
        if examples:
            parts.append("\nExamples:")
            for ex in examples:
                parts.append(f"User: {ex['input']}")
                parts.append(f"Assistant: {ex['output']}")
        
        # Constraints
        if constraints:
            parts.append("\nConstraints:")
            for constraint in constraints:
                parts.append(f"- {constraint}")
        
        # Knowledge context
        if knowledge:
            parts.append("\nRelevant Knowledge:")
            for item in knowledge[:3]:  # Limit to top 3
                if isinstance(item, dict):
                    parts.append(f"- {item.get('type', 'info')}: {item.get('data', '')}")
        
        # Main task prompt
        parts.append(f"\n{task_prompt}")
        
        return "\n".join(parts)
    
    async def switch_domain(self, domain_name: str) -> Dict[str, Any]:
        """Switch to a different domain"""
        success = self.domain_manager.switch_domain(domain_name)
        
        if success:
            domain_plugin = self.domain_manager.get_active_domain()
            config = domain_plugin.get_config()
            
            return {
                "success": True,
                "domain": domain_name,
                "display_name": config.display_name,
                "description": config.description,
                "capabilities": self.domain_manager.get_domain_capabilities(domain_name)
            }
        else:
            return {
                "success": False,
                "error": f"Domain '{domain_name}' not found or not loaded",
                "available_domains": list(self.domain_manager.domains.keys())
            }
    
    def list_domains(self) -> List[Dict[str, Any]]:
        """List all available domains"""
        domains = []
        for name, plugin in self.domain_manager.domains.items():
            config = plugin.get_config()
            domains.append({
                "name": name,
                "display_name": config.display_name,
                "description": config.description,
                "languages": config.supported_languages,
                "tasks": [task.value for task in config.supported_tasks]
            })
        return domains
    
    def get_current_domain(self) -> Optional[str]:
        """Get the currently active domain"""
        return self.domain_manager.active_domain
    
    async def search_knowledge(
        self,
        query: str,
        domain: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict]:
        """Search knowledge base of a domain"""
        return await self.domain_manager.search_knowledge(query, domain, limit)
    
    async def get_tools(self, domain: Optional[str] = None) -> List[Dict]:
        """Get available tools for a domain"""
        domain_plugin = self.domain_manager.get_domain(domain) if domain else self.domain_manager.get_active_domain()
        
        if domain_plugin:
            return domain_plugin.get_tools()
        return []
    
    async def cleanup(self):
        """Clean up resources"""
        await self.domain_manager.cleanup()
        logger.info("AI Engine cleaned up")