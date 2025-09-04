"""
Budtender Domain Plugin
Cannabis industry specific implementation
"""
import os
import yaml
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

# Add parent paths for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.interfaces.domain_plugin import DomainPlugin, DomainConfig, DomainContext, TaskType

logger = logging.getLogger(__name__)

class BudtenderPlugin(DomainPlugin):
    """
    Cannabis budtender domain implementation
    Provides cannabis product recommendations, education, and consultation
    """
    
    def __init__(self, config_path: str):
        """Initialize the budtender plugin"""
        self.config_path = Path(config_path)
        self.domain_path = self.config_path.parent
        
        # Load configuration
        with open(self.config_path) as f:
            self.config_data = yaml.safe_load(f)
        
        # Load prompts
        self.prompts = self._load_prompts()
        
        # Load knowledge base
        self.knowledge = self._load_knowledge()
        
        # Initialize domain config
        self.domain_config = DomainConfig(
            name=self.config_data['name'],
            display_name=self.config_data['display_name'],
            description=self.config_data['description'],
            version=self.config_data['version'],
            author=self.config_data['author'],
            supported_languages=self.config_data['supported_languages'],
            supported_tasks=[TaskType[task.upper()] for task in self.config_data['supported_tasks']],
            requires_auth=self.config_data['requires_auth'],
            data_sources=self.config_data.get('data_sources', []),
            knowledge_bases=self.config_data.get('knowledge_bases', [])
        )
    
    def _load_prompts(self) -> Dict:
        """Load all prompts from the prompts directory"""
        prompts = {}
        prompts_dir = self.domain_path / "prompts"
        
        if prompts_dir.exists():
            # Load JSON prompts (primary format)
            for prompt_file in prompts_dir.glob("*.json"):
                with open(prompt_file) as f:
                    prompt_data = json.load(f)
                    prompts[prompt_file.stem] = prompt_data
            
            # Load YAML prompts (legacy support)
            for prompt_file in prompts_dir.glob("*.yaml"):
                with open(prompt_file) as f:
                    prompt_data = yaml.safe_load(f)
                    prompts[prompt_file.stem] = prompt_data
        
        return prompts
    
    def _load_knowledge(self) -> Dict:
        """Load knowledge base"""
        knowledge = {}
        knowledge_dir = self.domain_path / "knowledge"
        
        if knowledge_dir.exists():
            for knowledge_file in knowledge_dir.glob("*.json"):
                with open(knowledge_file) as f:
                    knowledge_data = json.load(f)
                    knowledge[knowledge_file.stem] = knowledge_data
        
        return knowledge
    
    def get_config(self) -> DomainConfig:
        """Get domain configuration"""
        return self.domain_config
    
    def get_prompt(self, task: TaskType, **kwargs) -> str:
        """Get a prompt template for a specific task"""
        task_key = task.value
        
        if task_key not in self.prompts:
            # Fallback to a generic prompt
            return self._get_generic_prompt(task, **kwargs)
        
        prompt_template = self.prompts[task_key].get('template', '')
        
        # Replace variables in template
        for key, value in kwargs.items():
            prompt_template = prompt_template.replace(f"{{{key}}}", str(value))
        
        return prompt_template
    
    def _get_generic_prompt(self, task: TaskType, **kwargs) -> str:
        """Get a generic prompt when specific one isn't available"""
        input_text = kwargs.get('input', '')
        
        if task == TaskType.GREETING:
            return f"Greet the customer warmly as a knowledgeable cannabis budtender. Input: {input_text}"
        elif task == TaskType.SEARCH:
            return f"Search for cannabis products matching: {input_text}"
        elif task == TaskType.RECOMMENDATION:
            return f"Recommend cannabis products for: {input_text}"
        elif task == TaskType.INFORMATION:
            return f"Provide detailed information about: {input_text}"
        else:
            return f"Help the customer with: {input_text}"
    
    def get_system_prompt(self) -> str:
        """Get the system prompt from loaded configuration files"""
        # Use intelligent_budtender.json system prompt
        if 'intelligent_budtender' in self.prompts:
            system_config = self.prompts['intelligent_budtender'].get('system_prompt', {})
            base_prompt = system_config.get('base', '')
            
            # Add personality traits
            if 'personality_traits' in system_config:
                traits = system_config['personality_traits']
                traits_text = '. '.join([f"{k}: {v}" for k, v in traits.items()])
                base_prompt += f"\n\n{traits_text}"
            
            # Add conversation principles
            if 'conversation_principles' in system_config:
                principles = system_config['conversation_principles']
                base_prompt += "\n\nConversation Principles:\n" + "\n".join([f"- {p}" for p in principles])
            
            return base_prompt
        
        # Fallback to prompts from configuration
        return self.prompts.get('conversation', {}).get('system_prompt', 'You are a helpful budtender assistant.')
    
    def search_knowledge(self, query: str, limit: int = 10) -> List[Dict]:
        """Search cannabis knowledge base"""
        results = []
        query_lower = query.lower()
        
        # Search strains
        if 'strains' in self.knowledge:
            for strain in self.knowledge['strains']:
                if query_lower in strain.get('name', '').lower() or \
                   query_lower in strain.get('description', '').lower():
                    results.append({
                        'type': 'strain',
                        'data': strain
                    })
        
        # Search effects
        if 'effects' in self.knowledge:
            for effect in self.knowledge['effects']:
                if query_lower in effect.get('name', '').lower() or \
                   query_lower in effect.get('description', '').lower():
                    results.append({
                        'type': 'effect',
                        'data': effect
                    })
        
        # Search terpenes
        if 'terpenes' in self.knowledge:
            for terpene in self.knowledge['terpenes']:
                if query_lower in terpene.get('name', '').lower() or \
                   query_lower in terpene.get('effects', '').lower():
                    results.append({
                        'type': 'terpene',
                        'data': terpene
                    })
        
        return results[:limit]
    
    def validate_input(self, input_text: str, task: TaskType) -> Tuple[bool, Optional[str]]:
        """Validate user input for cannabis-specific rules"""
        
        # Check for illegal requests
        illegal_keywords = ['sell', 'dealer', 'illegal', 'smuggle', 'underage', 'minor']
        input_lower = input_text.lower()
        
        for keyword in illegal_keywords:
            if keyword in input_lower:
                return False, "I cannot assist with illegal activities. Please ask about legal cannabis products and information."
        
        # Check for medical claims we can't make
        if task == TaskType.INFORMATION:
            medical_claims = ['cure', 'treat disease', 'replace medication']
            for claim in medical_claims:
                if claim in input_lower:
                    return False, "I cannot make medical claims. Please consult a healthcare provider for medical advice."
        
        return True, None
    
    def validate_response(self, response: str, task: TaskType) -> Tuple[bool, Optional[str]]:
        """Validate AI response for compliance"""
        response_lower = response.lower()
        
        # Check for unsubstantiated medical claims
        forbidden_claims = ['cure', 'treat', 'diagnose', 'prescribe']
        for claim in forbidden_claims:
            if claim in response_lower and 'cannot' not in response_lower:
                return False, "Response contains medical claims"
        
        # Ensure disclaimer is present for recommendations
        if task == TaskType.RECOMMENDATION:
            if 'consult' not in response_lower and 'professional' not in response_lower:
                return False, "Missing disclaimer"
        
        return True, None
    
    def format_response(self, raw_response: str, task: TaskType, context: DomainContext) -> Dict:
        """Format response for cannabis domain"""
        formatted = {
            'message': raw_response,
            'type': task.value,
            'timestamp': datetime.now().isoformat(),
            'domain': 'budtender'
        }
        
        # Add disclaimer if needed
        if self.config_data['response_format']['include_disclaimer']:
            formatted['disclaimer'] = "This information is for educational purposes only. Please consume responsibly and in accordance with local laws."
        
        # Add dosage warning for recommendations
        if task == TaskType.RECOMMENDATION and self.config_data['response_format']['include_dosage_warning']:
            formatted['warning'] = "Start with a low dose and go slow, especially if you're new to cannabis."
        
        # Add metadata
        formatted['metadata'] = {
            'language': context.language if context else 'en',
            'compliance_mode': self.config_data['settings']['compliance_mode']
        }
        
        return formatted
    
    def get_tools(self) -> List[Dict]:
        """Get cannabis-specific tools"""
        return [
            {
                'name': 'search_strains',
                'description': 'Search cannabis strains database',
                'parameters': {
                    'query': 'string',
                    'filters': {
                        'type': ['sativa', 'indica', 'hybrid'],
                        'thc_range': 'string',
                        'cbd_range': 'string'
                    }
                }
            },
            {
                'name': 'calculate_dosage',
                'description': 'Calculate recommended dosage',
                'parameters': {
                    'product_type': 'string',
                    'experience_level': ['beginner', 'intermediate', 'experienced'],
                    'desired_effect': 'string'
                }
            },
            {
                'name': 'check_drug_interactions',
                'description': 'Check for potential interactions',
                'parameters': {
                    'medications': 'list',
                    'conditions': 'list'
                }
            },
            {
                'name': 'find_alternatives',
                'description': 'Find alternative products',
                'parameters': {
                    'current_product': 'string',
                    'reason_for_change': 'string'
                }
            }
        ]
    
    def get_data_schema(self) -> Dict:
        """Get cannabis data schema mapping"""
        return {
            'products': {
                'entity': 'products',
                'fields': {
                    'id': 'product_id',
                    'name': 'product_name',
                    'type': 'product_type',
                    'strain': 'strain_name',
                    'thc': 'thc_percentage',
                    'cbd': 'cbd_percentage',
                    'price': 'price',
                    'description': 'description',
                    'effects': 'effects',
                    'terpenes': 'terpene_profile'
                }
            },
            'strains': {
                'entity': 'strains',
                'fields': {
                    'id': 'strain_id',
                    'name': 'strain_name',
                    'type': 'strain_type',
                    'genetics': 'genetics',
                    'thc_avg': 'avg_thc',
                    'cbd_avg': 'avg_cbd',
                    'effects': 'common_effects',
                    'medical': 'medical_uses',
                    'negatives': 'negative_effects'
                }
            },
            'inventory': {
                'entity': 'inventory',
                'fields': {
                    'product_id': 'product_id',
                    'quantity': 'quantity_available',
                    'location': 'store_location'
                }
            }
        }
    
    def handle_error(self, error: Exception, task: TaskType, context: DomainContext) -> str:
        """Handle cannabis domain errors"""
        error_type = type(error).__name__
        
        if 'Database' in error_type:
            return "I'm having trouble accessing the product database. Please try again in a moment."
        elif 'Network' in error_type:
            return "I'm having connection issues. Please check your internet and try again."
        elif 'Auth' in error_type:
            return "You need to verify your age to access this information."
        else:
            return "I encountered an issue processing your request. Please try rephrasing or contact support."
    
    def get_fallback_response(self, task: TaskType, context: DomainContext) -> str:
        """Get fallback response for cannabis domain"""
        if task == TaskType.GREETING:
            return "Welcome! I'm your cannabis consultant. How can I help you find the perfect product today?"
        elif task == TaskType.SEARCH:
            return "I'm having trouble searching right now. Try browsing our categories or ask me for recommendations!"
        elif task == TaskType.RECOMMENDATION:
            return "I'd love to help you find the right product. Can you tell me more about what effects you're looking for?"
        elif task == TaskType.INFORMATION:
            return "I can provide information about strains, effects, terpenes, and consumption methods. What would you like to know?"
        else:
            return "I'm here to help with all your cannabis questions. What would you like to know?"
    
    def pre_process(self, input_text: str, context: DomainContext) -> str:
        """Pre-process cannabis queries"""
        # Expand common abbreviations
        abbreviations = {
            'thc': 'THC',
            'cbd': 'CBD',
            'cbg': 'CBG',
            'cbn': 'CBN'
        }
        
        processed = input_text
        for abbr, full in abbreviations.items():
            processed = processed.replace(abbr, full)
        
        return processed
    
    def post_process(self, response: str, context: DomainContext) -> str:
        """Post-process cannabis responses"""
        # Add units to measurements
        response = response.replace('mg ', 'mg ')
        response = response.replace('% ', '% ')
        
        # Ensure proper capitalization
        response = response.replace('thc', 'THC')
        response = response.replace('cbd', 'CBD')
        
        return response
    
    def get_examples(self, task: TaskType) -> List[Dict[str, str]]:
        """Get few-shot examples for cannabis tasks"""
        if task == TaskType.RECOMMENDATION:
            return [
                {
                    'input': 'I need something for sleep',
                    'output': 'For sleep, I recommend indica-dominant strains with higher CBD content...'
                },
                {
                    'input': 'Looking for pain relief',
                    'output': 'For pain management, consider products with balanced THC/CBD ratios...'
                }
            ]
        return []
    
    def should_escalate(self, input_text: str, context: DomainContext) -> bool:
        """Determine if query needs human budtender"""
        escalation_triggers = [
            'speak to human',
            'real person',
            'medical emergency',
            'allergic reaction',
            'overdose',
            'pregnant',
            'nursing',
            'legal advice'
        ]
        
        input_lower = input_text.lower()
        return any(trigger in input_lower for trigger in escalation_triggers)
    
    def log_interaction(self, input_text: str, response: str, context: DomainContext) -> None:
        """Log cannabis consultation for compliance and training"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'user_id': context.user_id if context else None,
            'input': input_text,
            'response': response[:500],  # Truncate for storage
            'language': context.language if context else 'en',
            'escalated': self.should_escalate(input_text, context)
        }
        
        logger.info(f"Cannabis consultation logged: {log_entry['timestamp']}")