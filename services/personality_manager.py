"""
Personality Manager Service
Loads and manages AI personalities from JSON files in role-based folders
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class PersonalityTraits:
    """Personality traits configuration"""
    age: str
    gender: str
    communication_style: str
    knowledge_level: str
    humor_style: str
    humor_level: str
    empathy_level: str
    response_length: str
    jargon_level: str
    sales_approach: str
    formality: str

@dataclass
class ConversationStyle:
    """Conversation style templates"""
    opening_phrases: List[str]
    product_transitions: List[str]
    closing_phrases: List[str]

@dataclass
class Personality:
    """Complete personality definition"""
    id: str
    name: str
    role: str
    description: str
    traits: PersonalityTraits
    greeting_prompt: str
    product_search_prompt: str
    recommendation_prompt: str
    conversation_style: ConversationStyle
    emoji: str
    active: bool = True

class PersonalityManager:
    """
    Manages AI personalities loaded from JSON files
    """
    
    def __init__(self, prompts_dir: str = None):
        """
        Initialize personality manager
        
        Args:
            prompts_dir: Base directory for prompts (default: prompts folder)
        """
        if prompts_dir is None:
            prompts_dir = Path(__file__).parent.parent / "prompts"
        
        self.prompts_dir = Path(prompts_dir)
        self.roles_dir = self.prompts_dir / "roles"
        self.personalities: Dict[str, Personality] = {}
        self.personalities_by_role: Dict[str, List[str]] = {}
        
        # Load all personalities on initialization
        self.load_all_personalities()
    
    def load_all_personalities(self):
        """Load all personalities from role folders"""
        if not self.roles_dir.exists():
            logger.warning(f"Roles directory not found: {self.roles_dir}")
            return
        
        # Iterate through each role folder
        for role_dir in self.roles_dir.iterdir():
            if role_dir.is_dir():
                role_name = role_dir.name
                self.personalities_by_role[role_name] = []
                
                # Load all personality JSON files in this role folder
                for json_file in role_dir.glob("*.json"):
                    try:
                        personality = self.load_personality_from_file(json_file, role_name)
                        if personality:
                            self.personalities[personality.id] = personality
                            self.personalities_by_role[role_name].append(personality.id)
                            logger.info(f"Loaded personality: {personality.name} ({personality.id}) for role: {role_name}")
                    except Exception as e:
                        logger.error(f"Failed to load personality from {json_file}: {e}")
        
        logger.info(f"Loaded {len(self.personalities)} personalities across {len(self.personalities_by_role)} roles")
    
    def load_personality_from_file(self, file_path: Path, role: str) -> Optional[Personality]:
        """
        Load a single personality from a JSON file
        
        Args:
            file_path: Path to the JSON file
            role: Role name (from folder name)
        
        Returns:
            Personality object or None if loading fails
        """
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Extract personality data
            personality_data = data.get('personality', data)
            
            # Ensure role matches folder
            personality_data['role'] = role
            
            # Create PersonalityTraits
            traits_data = personality_data.get('traits', {})
            traits = PersonalityTraits(**traits_data)
            
            # Create ConversationStyle
            style_data = personality_data.get('conversation_style', {})
            conversation_style = ConversationStyle(
                opening_phrases=style_data.get('opening_phrases', []),
                product_transitions=style_data.get('product_transitions', []),
                closing_phrases=style_data.get('closing_phrases', [])
            )
            
            # Create Personality
            personality = Personality(
                id=personality_data.get('id'),
                name=personality_data.get('name'),
                role=role,
                description=personality_data.get('description'),
                traits=traits,
                greeting_prompt=personality_data.get('greeting_prompt', ''),
                product_search_prompt=personality_data.get('product_search_prompt', ''),
                recommendation_prompt=personality_data.get('recommendation_prompt', ''),
                conversation_style=conversation_style,
                emoji=personality_data.get('emoji', '🌿'),
                active=personality_data.get('active', True)
            )
            
            return personality
            
        except Exception as e:
            logger.error(f"Error loading personality from {file_path}: {e}")
            return None
    
    def get_personality(self, personality_id: str) -> Optional[Personality]:
        """
        Get a specific personality by ID
        
        Args:
            personality_id: Personality ID
        
        Returns:
            Personality object or None if not found
        """
        return self.personalities.get(personality_id)
    
    def get_personalities_by_role(self, role: str) -> List[Personality]:
        """
        Get all personalities for a specific role
        
        Args:
            role: Role name
        
        Returns:
            List of Personality objects
        """
        personality_ids = self.personalities_by_role.get(role, [])
        return [self.personalities[pid] for pid in personality_ids if pid in self.personalities]
    
    def get_default_personality(self, role: str = "budtender") -> Optional[Personality]:
        """
        Get the default personality for a role
        
        Args:
            role: Role name
        
        Returns:
            First active personality for the role or None
        """
        personalities = self.get_personalities_by_role(role)
        
        # Return first active personality
        for personality in personalities:
            if personality.active:
                return personality
        
        # If no active personality, return first one
        return personalities[0] if personalities else None
    
    def get_all_personalities(self) -> List[Dict[str, Any]]:
        """
        Get all personalities as dictionaries
        
        Returns:
            List of personality dictionaries
        """
        result = []
        for personality in self.personalities.values():
            result.append({
                'id': personality.id,
                'name': personality.name,
                'role': personality.role,
                'description': personality.description,
                'active': personality.active,
                'emoji': personality.emoji,
                'traits': asdict(personality.traits),
                'conversation_style': asdict(personality.conversation_style)
            })
        return result
    
    def get_personality_prompt(self, personality_id: str, prompt_type: str, **kwargs) -> str:
        """
        Get a formatted prompt for a personality
        
        Args:
            personality_id: Personality ID
            prompt_type: Type of prompt (greeting, product_search, recommendation)
            **kwargs: Additional variables for prompt formatting
        
        Returns:
            Formatted prompt string
        """
        personality = self.get_personality(personality_id)
        if not personality:
            logger.warning(f"Personality {personality_id} not found, using default")
            personality = self.get_default_personality()
        
        if not personality:
            return "You are a helpful assistant."
        
        # Get the base prompt
        if prompt_type == "greeting":
            base_prompt = personality.greeting_prompt
        elif prompt_type == "product_search":
            base_prompt = personality.product_search_prompt
        elif prompt_type == "recommendation":
            base_prompt = personality.recommendation_prompt
        else:
            # Build a general prompt from personality traits
            base_prompt = f"""You are {personality.name}, a {personality.description}.
Your communication style is {personality.traits.communication_style}.
You have {personality.traits.empathy_level} empathy and use {personality.traits.humor_level} humor.
Your responses are {personality.traits.response_length} and {personality.traits.formality}."""
        
        # Add any additional context
        if kwargs:
            context = "\n".join([f"{k}: {v}" for k, v in kwargs.items()])
            base_prompt = f"{base_prompt}\n\nContext:\n{context}"
        
        return base_prompt
    
    def reload_personalities(self):
        """Reload all personalities from disk"""
        self.personalities.clear()
        self.personalities_by_role.clear()
        self.load_all_personalities()

# Singleton instance
_personality_manager = None

def get_personality_manager() -> PersonalityManager:
    """Get or create personality manager singleton"""
    global _personality_manager
    if _personality_manager is None:
        _personality_manager = PersonalityManager()
    return _personality_manager