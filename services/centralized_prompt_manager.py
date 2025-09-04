"""
Centralized Prompt Management System
Loads prompts from organized JSON files for easy maintenance
"""
from typing import Dict, Any, Optional
import logging
import json
import os
from pathlib import Path

logger = logging.getLogger(__name__)

class CentralizedPromptManager:
    """Manages all prompts for the AI system - loads from JSON files"""
    
    def __init__(self, prompts_dir: str = "prompts"):
        """Initialize by loading all prompt files from directory"""
        self.prompts_dir = Path(prompts_dir)
        self.prompts = {}
        self.prompt_metadata = {}
        self._load_all_prompts()
    
    def _load_all_prompts(self):
        """Load all prompt JSON files from the prompts directory"""
        if not self.prompts_dir.exists():
            logger.warning(f"Prompts directory {self.prompts_dir} does not exist")
            self._initialize_default_prompts()
            return
        
        # Load each JSON file in the prompts directory
        for json_file in self.prompts_dir.glob("*.json"):
            try:
                category = json_file.stem  # filename without extension
                with open(json_file, 'r') as f:
                    category_prompts = json.load(f)
                
                # Process each prompt in the category
                for prompt_name, prompt_data in category_prompts.items():
                    if isinstance(prompt_data, dict):
                        # Store the template
                        self.prompts[prompt_name] = prompt_data.get('template', '')
                        
                        # Store metadata for validation and documentation
                        self.prompt_metadata[prompt_name] = {
                            'category': category,
                            'variables': prompt_data.get('variables', []),
                            'output_format': prompt_data.get('output_format', 'text'),
                            'valid_outputs': prompt_data.get('valid_outputs', []),
                            'max_length': prompt_data.get('max_length'),
                            'required_fields': prompt_data.get('required_fields', []),
                            'optional_fields': prompt_data.get('optional_fields', []),
                            'allow_empty': prompt_data.get('allow_empty', False)
                        }
                    else:
                        # Legacy format - just a string template
                        self.prompts[prompt_name] = prompt_data
                        self.prompt_metadata[prompt_name] = {'category': category}
                
                logger.info(f"Loaded {len(category_prompts)} prompts from {category}.json")
                
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing {json_file}: {e}")
            except Exception as e:
                logger.error(f"Error loading {json_file}: {e}")
        
        logger.info(f"Total prompts loaded: {len(self.prompts)}")
    
    def _initialize_default_prompts(self) -> Dict[str, str]:
        """Initialize default prompts if JSON files don't exist"""
        logger.warning("Loading default prompts as fallback")
        return {
            "error_recovery": "You are a knowledgeable budtender. Please help the customer with: {message}",
            "greeting_response": "Welcome! How can I help you today?",
            "product_search_response": "Let me search for {message} in our inventory.",
            "general_conversation": "I'm here to help you find cannabis products. What are you looking for?"
        }
    
    def get_prompt(self, 
                   prompt_type: str, 
                   **kwargs) -> str:
        """
        Get a formatted prompt by type
        
        Args:
            prompt_type: The type of prompt to retrieve
            **kwargs: Variables to format into the prompt
            
        Returns:
            Formatted prompt string
        """
        if prompt_type not in self.prompts:
            logger.warning(f"Unknown prompt type: {prompt_type}, using error recovery")
            return self.prompts.get("error_recovery", "I need clarification.").format(
                message=kwargs.get("message", "")
            )
        
        try:
            # Get metadata for validation
            metadata = self.prompt_metadata.get(prompt_type, {})
            
            # Add common defaults based on metadata
            defaults = self._get_default_values(metadata)
            
            # Merge with provided kwargs
            format_args = {**defaults, **kwargs}
            
            # Validate required variables if metadata exists
            required_vars = metadata.get('variables', [])
            for var in required_vars:
                if var not in format_args or format_args[var] is None:
                    logger.warning(f"Missing required variable '{var}' for {prompt_type}")
            
            # Format and return
            return self.prompts[prompt_type].format(**format_args)
            
        except KeyError as e:
            logger.error(f"Missing parameter for {prompt_type}: {e}")
            return f"I need help understanding your request about: {kwargs.get('message', 'that')}"
        except Exception as e:
            logger.error(f"Error formatting {prompt_type}: {e}")
            return "Could you please rephrase that?"
    
    def _get_default_values(self, metadata: Dict) -> Dict:
        """Get default values based on prompt metadata"""
        defaults = {
            "personality": "You are a knowledgeable and friendly budtender",
            "conversation_context": "This is a new conversation",
            "customer_context": "New customer",
            "conversation_text": "",
            "message": "",
            "query": "",
            "categories_str": "Flower, Edibles, Vapes, Extracts, Topicals, Accessories",
            "products_hint": "",
            "search_performed": "No search performed",
            "products_context": "No products found",
            "customer_profile": "Unknown preferences",
            "available_products": "Various products available",
            "brands_list": "Various brands",
            "categories_list": "Multiple categories",
            "analytics_result": "No data available",
            "stats_data": "No statistics available"
        }
        
        # Add empty defaults for optional fields
        for field in metadata.get('optional_fields', []):
            if field not in defaults:
                defaults[field] = ""
        
        return defaults
    
    def reload_prompts(self):
        """Reload all prompts from JSON files"""
        logger.info("Reloading all prompts from JSON files")
        self.prompts.clear()
        self.prompt_metadata.clear()
        self._load_all_prompts()
    
    def get_prompt_info(self, prompt_type: str) -> Dict:
        """Get metadata information about a specific prompt"""
        if prompt_type not in self.prompt_metadata:
            return {"error": f"Unknown prompt type: {prompt_type}"}
        
        return {
            "name": prompt_type,
            "category": self.prompt_metadata[prompt_type].get('category'),
            "variables": self.prompt_metadata[prompt_type].get('variables', []),
            "output_format": self.prompt_metadata[prompt_type].get('output_format'),
            "template_preview": self.prompts[prompt_type][:100] + "..." if len(self.prompts[prompt_type]) > 100 else self.prompts[prompt_type]
        }
    
    def get_prompts_by_category(self, category: str) -> Dict[str, str]:
        """Get all prompts from a specific category"""
        result = {}
        for prompt_name, metadata in self.prompt_metadata.items():
            if metadata.get('category') == category:
                result[prompt_name] = self.prompts[prompt_name]
        return result
    
    def get_all_categories(self) -> list:
        """Get list of all prompt categories"""
        categories = set()
        for metadata in self.prompt_metadata.values():
            if 'category' in metadata:
                categories.add(metadata['category'])
        return sorted(list(categories))
    
    def get_all_prompt_types(self) -> list:
        """Get list of all available prompt types"""
        return sorted(list(self.prompts.keys()))
    
    def validate_prompt_response(self, prompt_type: str, response: str) -> Dict:
        """Validate a response against prompt metadata"""
        if prompt_type not in self.prompt_metadata:
            return {"valid": True, "reason": "No validation rules"}
        
        metadata = self.prompt_metadata[prompt_type]
        
        # Check output format
        output_format = metadata.get('output_format')
        
        if output_format == 'json':
            try:
                parsed = json.loads(response)
                # Check required fields
                for field in metadata.get('required_fields', []):
                    if field not in parsed:
                        return {"valid": False, "reason": f"Missing required field: {field}"}
                return {"valid": True}
            except json.JSONDecodeError:
                return {"valid": False, "reason": "Invalid JSON format"}
        
        elif output_format == 'single_word':
            if ' ' in response.strip():
                return {"valid": False, "reason": "Expected single word response"}
            valid_outputs = metadata.get('valid_outputs', [])
            if valid_outputs and response.strip().lower() not in valid_outputs:
                return {"valid": False, "reason": f"Invalid output. Expected one of: {valid_outputs}"}
        
        elif output_format == 'yes_no':
            if response.strip().lower() not in ['yes', 'no']:
                return {"valid": False, "reason": "Expected 'yes' or 'no'"}
        
        # Check max length
        max_length = metadata.get('max_length')
        if max_length and len(response.split()) > max_length:
            return {"valid": False, "reason": f"Response exceeds max length of {max_length} words"}
        
        return {"valid": True}
    
    def export_prompts(self, filename: str):
        """Export all loaded prompts to a single JSON file for backup"""
        export_data = {}
        for category in self.get_all_categories():
            export_data[category] = {}
            for prompt_name, metadata in self.prompt_metadata.items():
                if metadata.get('category') == category:
                    export_data[category][prompt_name] = {
                        'template': self.prompts[prompt_name],
                        **metadata
                    }
        
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2)
        logger.info(f"Exported all prompts to {filename}")
    
    def add_custom_prompt(self, name: str, template: str, category: str = "custom", **metadata):
        """Add a custom prompt at runtime"""
        self.prompts[name] = template
        self.prompt_metadata[name] = {
            'category': category,
            **metadata
        }
        logger.info(f"Added custom prompt: {name} in category: {category}")
    
    def save_prompt_to_file(self, prompt_name: str, category: str = None):
        """Save a specific prompt back to its JSON file"""
        if prompt_name not in self.prompts:
            logger.error(f"Prompt {prompt_name} not found")
            return False
        
        # Determine category
        if not category:
            category = self.prompt_metadata.get(prompt_name, {}).get('category', 'custom')
        
        # Load existing file or create new structure
        json_file = self.prompts_dir / f"{category}.json"
        if json_file.exists():
            with open(json_file, 'r') as f:
                category_prompts = json.load(f)
        else:
            category_prompts = {}
        
        # Update the prompt
        category_prompts[prompt_name] = {
            'template': self.prompts[prompt_name],
            **self.prompt_metadata.get(prompt_name, {})
        }
        
        # Save back to file
        with open(json_file, 'w') as f:
            json.dump(category_prompts, f, indent=2)
        
        logger.info(f"Saved prompt {prompt_name} to {json_file}")
        return True