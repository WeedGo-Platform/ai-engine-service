"""
Prompt Management Service
Implements IPromptManager interface following SOLID principles
Handles prompt template loading and application
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

# Import interface
import sys
sys.path.append(str(Path(__file__).parent.parent))
from core.interfaces import IPromptManager

logger = logging.getLogger(__name__)


class PromptManager(IPromptManager):
    """
    Prompt Manager implementation that handles prompt templates
    Single Responsibility: Prompt template management and application
    """
    
    def __init__(self):
        """Initialize the Prompt Manager"""
        self.loaded_prompts = {}
        self.base_prompts = {}
        self.role_prompts = {}
        self.personality_prompts = {}
        self.agent_prompts = {}
        self.personality_traits = {}
        self.prompt_folder = None
        self.role_folder = None
        self.personality_folder = None
        self.current_agent = None
        self.current_personality = None
        self.system_config = {}
        
        logger.info("PromptManager initialized")
    
    def load_prompts(self, prompt_folder: str) -> bool:
        """
        Load prompts from a folder
        
        Args:
            prompt_folder: Path to the prompt folder
            
        Returns:
            True if successfully loaded, False otherwise
        """
        try:
            self.prompt_folder = prompt_folder
            prompt_path = Path(prompt_folder)
            
            if not prompt_path.exists():
                logger.warning(f"Prompt folder does not exist: {prompt_folder}")
                return False
            
            # Clear existing prompts
            self.loaded_prompts = {}
            self.base_prompts = {}
            
            # Special handling for system folder
            if "system" in prompt_folder:
                return self._load_system_config(prompt_path)
            
            # Load all JSON files in the folder
            json_files = list(prompt_path.glob("*.json"))
            
            if not json_files:
                logger.warning(f"No JSON files found in {prompt_folder}")
                return False
            
            for json_file in json_files:
                # Skip config files
                if json_file.stem == "config":
                    continue
                    
                try:
                    with open(json_file, 'r') as f:
                        prompts = json.load(f)
                        file_name = json_file.stem
                        
                        # Store prompts
                        self.base_prompts[file_name] = prompts
                        self.loaded_prompts[file_name] = prompts
                        
                        logger.info(f"Loaded {len(prompts)} prompts from {json_file.name}")
                        
                except Exception as e:
                    logger.error(f"Failed to load prompts from {json_file}: {e}")
            
            # Merge all loaded prompts
            self._merge_prompts()
            
            total_prompts = sum(len(p) if isinstance(p, dict) else 1 for p in self.loaded_prompts.values())
            logger.info(f"Loaded total {total_prompts} prompts from {prompt_folder}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to load prompts from {prompt_folder}: {e}")
            return False
    
    def _load_system_config(self, prompt_path: Path) -> bool:
        """
        Load system configuration from prompts/system folder
        
        Args:
            prompt_path: Path to system folder
            
        Returns:
            True if loaded successfully
        """
        config_file = prompt_path / "config.json"
        
        if not config_file.exists():
            logger.warning(f"System config file not found: {config_file}")
            return False
        
        try:
            with open(config_file, 'r') as f:
                config_data = json.load(f)
                
                # Apply system configuration
                if 'system' in config_data:
                    self.system_config = config_data
                    system_cfg = config_data['system']
                    
                    # Apply default behavior settings if available
                    if 'default_behavior' in system_cfg:
                        defaults = system_cfg['default_behavior']
                        logger.info(f"Applied system configuration: {defaults.get('response_style', 'default')} style")
                    
                    # Apply safety guidelines
                    if 'safety_guidelines' in system_cfg and system_cfg['safety_guidelines'].get('enabled'):
                        logger.info(f"Safety guidelines enabled with {len(system_cfg['safety_guidelines'].get('rules', []))} rules")
                
                logger.info(f"Loaded system configuration from {config_file.name}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to load system config: {e}")
            return False
    
    def load_agent_prompts(self, agent_id: str) -> bool:
        """
        Load prompts for a specific agent
        
        Args:
            agent_id: The agent identifier
            
        Returns:
            True if successfully loaded
        """
        try:
            self.current_agent = agent_id
            
            # Load agent configuration
            config_path = Path(f"prompts/agents/{agent_id}/config.json")
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config_data = json.load(f)
                    
                    # Store the entire config including system_behavior settings
                    if 'system_behavior' in config_data:
                        self.system_config.update(config_data['system_behavior'])
                    if 'default_behavior' in config_data:
                        self.system_config.update(config_data['default_behavior'])
                    if 'safety_guidelines' in config_data:
                        self.system_config['safety_guidelines'] = config_data['safety_guidelines']
                    
                    logger.info(f"Loaded agent config for '{agent_id}'")
            
            # Load agent prompts
            prompts_path = Path(f"prompts/agents/{agent_id}/prompts.json")
            if prompts_path.exists():
                with open(prompts_path, 'r') as f:
                    agent_data = json.load(f)
                    self.agent_prompts = agent_data.get('prompts', {})
                    logger.info(f"Loaded {len(self.agent_prompts)} prompts for agent '{agent_id}'")
            
            # Merge prompts
            self._merge_prompts()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to load agent prompts for {agent_id}: {e}")
            return False
    
    def load_personality(self, personality_id: str, agent_id: Optional[str] = None) -> bool:
        """
        Load personality traits
        
        Args:
            personality_id: The personality identifier
            agent_id: Optional agent ID for agent-specific personalities
            
        Returns:
            True if successfully loaded
        """
        try:
            self.current_personality = personality_id
            
            # First check for agent-specific personality
            if agent_id:
                agent_personality_path = Path(f"prompts/agents/{agent_id}/personalities/{personality_id}.json")
                if agent_personality_path.exists():
                    with open(agent_personality_path, 'r') as f:
                        personality_data = json.load(f)
                        self.personality_traits = personality_data.get('personality', {})
                        self.personality_prompts = personality_data
                        logger.info(f"Loaded agent personality '{personality_id}' for agent '{agent_id}'")
                        self._merge_prompts()
                        return True
            
            # Check global personality folder
            personality_path = Path(f"prompts/personality/{personality_id}/traits.json")
            if personality_path.exists():
                with open(personality_path, 'r') as f:
                    personality_data = json.load(f)
                    self.personality_traits = personality_data.get('personality', {})
                    self.personality_prompts = personality_data
                    logger.info(f"Loaded global personality '{personality_id}'")
                    self._merge_prompts()
                    return True
            
            logger.warning(f"Personality '{personality_id}' not found")
            return False
            
        except Exception as e:
            logger.error(f"Failed to load personality {personality_id}: {e}")
            return False
    
    def get_prompt_template(self, prompt_type: str) -> Optional[Dict]:
        """
        Get a specific prompt template
        
        Args:
            prompt_type: Type of prompt to retrieve
            
        Returns:
            Prompt template dictionary or None
        """
        # First check agent prompts
        if self.agent_prompts and prompt_type in self.agent_prompts:
            return self.agent_prompts[prompt_type]
        
        # Then check merged prompts
        for file_prompts in self.loaded_prompts.values():
            if isinstance(file_prompts, dict) and prompt_type in file_prompts:
                return file_prompts[prompt_type]
        
        # Check base prompts
        for file_prompts in self.base_prompts.values():
            if isinstance(file_prompts, dict) and prompt_type in file_prompts:
                return file_prompts[prompt_type]
        
        return None
    
    def apply_prompt_template(self, user_input: str, prompt_type: str) -> str:
        """
        Apply a prompt template to user input
        
        Args:
            user_input: The user's input message
            prompt_type: Type of prompt template to apply
            
        Returns:
            Formatted prompt string
        """
        # Get the template
        template_data = self.get_prompt_template(prompt_type)
        
        if not template_data:
            logger.debug(f"No template found for prompt type: {prompt_type}")
            return user_input
        
        # Extract template string
        if isinstance(template_data, dict):
            template_str = template_data.get('template', '')
            use_system_format = template_data.get('system_format', False)
            variables = template_data.get('variables', [])
        else:
            template_str = str(template_data)
            use_system_format = False
            variables = []
        
        if not template_str:
            return user_input
        
        # Replace personality variables
        if self.personality_traits:
            personality_name = self.personality_traits.get('name', 'Assistant')
            template_str = template_str.replace('{personality_name}', personality_name)
            
            # Format traits as a descriptive string
            traits_dict = self.personality_traits.get('traits', {})
            if traits_dict and isinstance(traits_dict, dict):
                traits_desc = f"who is {traits_dict.get('communication_style', 'friendly')} and {traits_dict.get('sales_approach', 'helpful')}"
                template_str = template_str.replace('{personality_traits}', traits_desc)
            else:
                template_str = template_str.replace('{personality_traits}', '')
        else:
            # Default replacements
            template_str = template_str.replace('{personality_name}', 'Assistant')
            template_str = template_str.replace('{personality_traits}', '')
        
        # Replace other variables
        for var in variables:
            if var == 'message':
                # Don't replace message in system format
                if not use_system_format:
                    template_str = template_str.replace('{message}', user_input)
            else:
                # Replace with empty string for missing variables
                template_str = template_str.replace(f'{{{var}}}', '')
        
        # Handle system format
        if use_system_format:
            if self.system_config and 'prompt_format' in self.system_config:
                return self.system_config['prompt_format'].format(system=template_str, user=user_input)
            return user_input
        
        # Ensure message is included if not system format
        if '{message}' in template_str:
            template_str = template_str.replace('{message}', user_input)
        elif user_input not in template_str:
            # Append user input if not already included
            template_str = f"{template_str}\n{user_input}" if template_str else user_input
        
        return template_str
    
    def list_loaded_prompts(self) -> Dict[str, List[str]]:
        """
        List all loaded prompts
        
        Returns:
            Dictionary mapping prompt files to their prompt types
        """
        result = {}
        
        # Add agent prompts
        if self.agent_prompts:
            result[f"agent_{self.current_agent}"] = list(self.agent_prompts.keys())
        
        # Add base prompts
        for file_name, prompts in self.base_prompts.items():
            if isinstance(prompts, dict):
                result[f"base_{file_name}"] = list(prompts.keys())
        
        # Add role prompts
        for file_name, prompts in self.role_prompts.items():
            if isinstance(prompts, dict):
                result[f"role_{file_name}"] = list(prompts.keys())
        
        # Add personality prompts
        if self.personality_prompts and isinstance(self.personality_prompts, dict):
            # Extract actual prompts from personality data
            if 'prompts' in self.personality_prompts:
                result[f"personality_{self.current_personality}"] = list(self.personality_prompts['prompts'].keys())
        
        return result
    
    def _merge_prompts(self):
        """Merge all prompts with proper priority"""
        # Priority: personality < role < base < agent
        self.loaded_prompts = {}
        
        # Start with personality prompts (lowest priority)
        if self.personality_prompts:
            self.loaded_prompts.update(self.personality_prompts)
        
        # Add role prompts
        for prompts in self.role_prompts.values():
            if isinstance(prompts, dict):
                self.loaded_prompts.update(prompts)
        
        # Add base prompts
        for prompts in self.base_prompts.values():
            if isinstance(prompts, dict):
                self.loaded_prompts.update(prompts)
        
        # Add agent prompts (highest priority)
        if self.agent_prompts:
            # Agent prompts are already the full prompt dict
            for key, value in self.agent_prompts.items():
                self.loaded_prompts[key] = value
    
    def get_prompt_config(self, prompt_type: str) -> Dict[str, Any]:
        """
        Get configuration for a specific prompt type
        
        Args:
            prompt_type: Type of prompt
            
        Returns:
            Configuration dictionary with max_tokens, temperature, etc.
        """
        template = self.get_prompt_template(prompt_type)
        
        if not template or not isinstance(template, dict):
            return {}
        
        config = {}
        
        # Extract max_tokens
        if 'max_tokens' in template:
            config['max_tokens'] = template['max_tokens']
        elif 'constraints' in template and 'max_words' in template['constraints']:
            # Rough conversion from words to tokens
            config['max_tokens'] = template['constraints']['max_words'] * 2
        
        # Extract temperature
        if 'temperature' in template:
            config['temperature'] = template['temperature']
        
        # Extract stop sequences
        stop_sequences = template.get('stop_sequences', [])
        if not stop_sequences and 'constraints' in template:
            stop_sequences = template['constraints'].get('stop_sequences', [])
        if stop_sequences:
            config['stop_sequences'] = stop_sequences
        
        # Extract other parameters
        for param in ['top_p', 'top_k', 'repeat_penalty']:
            if param in template:
                config[param] = template[param]
        
        return config
    
    def clear_prompts(self):
        """Clear all loaded prompts"""
        self.loaded_prompts = {}
        self.base_prompts = {}
        self.role_prompts = {}
        self.personality_prompts = {}
        self.agent_prompts = {}
        self.personality_traits = {}
        self.current_agent = None
        self.current_personality = None
        logger.info("All prompts cleared")