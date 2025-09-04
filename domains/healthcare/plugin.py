"""
Healthcare Domain Plugin
Medical information and wellness guidance
"""
import yaml
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.interfaces.domain_plugin import DomainPlugin, DomainConfig, DomainContext, TaskType

logger = logging.getLogger(__name__)

class HealthcarePlugin(DomainPlugin):
    """Healthcare domain implementation"""
    
    def __init__(self, config_path: str):
        """Initialize healthcare plugin"""
        self.config_path = Path(config_path)
        
        with open(self.config_path) as f:
            self.config_data = yaml.safe_load(f)
        
        self.domain_config = DomainConfig(
            name=self.config_data['name'],
            display_name=self.config_data['display_name'],
            description=self.config_data['description'],
            version=self.config_data['version'],
            author=self.config_data['author'],
            supported_languages=self.config_data['supported_languages'],
            supported_tasks=[TaskType[task.upper()] for task in self.config_data['supported_tasks']],
            requires_auth=self.config_data['requires_auth']
        )
    
    def get_config(self) -> DomainConfig:
        return self.domain_config
    
    def get_prompt(self, task: TaskType, **kwargs) -> str:
        """Get healthcare-specific prompts"""
        if task == TaskType.GREETING:
            return "Greet the patient warmly as a healthcare assistant. Ask about their wellness concerns."
        elif task == TaskType.INFORMATION:
            return f"Provide health information about: {kwargs.get('input', '')}. Include disclaimers about seeking professional medical advice."
        elif task == TaskType.RECOMMENDATION:
            return f"Suggest wellness tips for: {kwargs.get('input', '')}. Emphasize consulting healthcare providers."
        else:
            return f"Assist with healthcare question: {kwargs.get('input', '')}"
    
    def get_system_prompt(self) -> str:
        return """You are a caring healthcare information assistant. You provide general health information, 
        wellness tips, and guide users to appropriate medical resources. You never diagnose conditions or 
        prescribe medications. You always encourage users to consult healthcare professionals for medical concerns."""
    
    def search_knowledge(self, query: str, limit: int = 10) -> List[Dict]:
        """Search medical knowledge base"""
        # Simplified for demo
        return [
            {"type": "symptom", "data": "General health information"},
            {"type": "wellness", "data": "Wellness tips"}
        ]
    
    def validate_input(self, input_text: str, task: TaskType) -> Tuple[bool, Optional[str]]:
        """Check for emergency keywords"""
        emergency_keywords = ['emergency', 'urgent', 'severe pain', 'chest pain', 'can\'t breathe']
        
        if any(keyword in input_text.lower() for keyword in emergency_keywords):
            return False, "This seems like an emergency. Please call 911 or your local emergency services immediately."
        
        return True, None
    
    def validate_response(self, response: str, task: TaskType) -> Tuple[bool, Optional[str]]:
        """Ensure no diagnosis or prescription"""
        forbidden = ['diagnose', 'prescribe', 'your condition is', 'you have']
        
        if any(word in response.lower() for word in forbidden):
            return False, "Response contains medical diagnosis/prescription"
        
        return True, None
    
    def format_response(self, raw_response: str, task: TaskType, context: DomainContext) -> Dict:
        return {
            'message': raw_response,
            'type': task.value,
            'domain': 'healthcare',
            'disclaimer': 'This information is for educational purposes only. Please consult a healthcare professional for medical advice.'
        }
    
    def get_tools(self) -> List[Dict]:
        return [
            {
                'name': 'symptom_checker',
                'description': 'Check symptoms against conditions'
            },
            {
                'name': 'find_providers',
                'description': 'Find healthcare providers nearby'
            }
        ]
    
    def get_data_schema(self) -> Dict:
        return {
            'conditions': {
                'entity': 'medical_conditions',
                'fields': {
                    'id': 'condition_id',
                    'name': 'condition_name',
                    'symptoms': 'common_symptoms',
                    'treatments': 'treatment_options'
                }
            }
        }
    
    def handle_error(self, error: Exception, task: TaskType, context: DomainContext) -> str:
        return "I encountered an issue. For medical concerns, please consult a healthcare professional."
    
    def get_fallback_response(self, task: TaskType, context: DomainContext) -> str:
        return "I'm here to provide health information. How can I help you with wellness questions today?"
    
    def should_escalate(self, input_text: str, context: DomainContext) -> bool:
        """Escalate medical emergencies"""
        emergency_terms = ['emergency', 'bleeding', 'unconscious', 'heart attack', 'stroke']
        return any(term in input_text.lower() for term in emergency_terms)
    
    def log_interaction(self, input_text: str, response: str, context: DomainContext) -> None:
        logger.info(f"Healthcare consultation logged for session: {context.session_id}")