"""
Model-Driven Intent Detection Service
NO hardcoded patterns - everything through the model
"""
import logging
import json
from typing import Optional, Dict, List, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

class ModelDrivenIntentService:
    """
    Pure model-driven intent detection
    NO hardcoded patterns or rules
    """
    
    def __init__(self, llm_instance=None, prompt_path: str = "prompts"):
        self.llm = llm_instance
        self.prompt_path = Path(prompt_path)
        self.intent_prompt = self._load_prompt("intent_detection.json")
        
    def _load_prompt(self, filename: str) -> Dict:
        """Load prompt from JSON file"""
        prompt_file = self.prompt_path / filename
        if prompt_file.exists():
            with open(prompt_file, 'r') as f:
                return json.load(f)
        return {}
    
    async def detect_intent(
        self, 
        text: str, 
        session_context: Optional[List[Dict]] = None,
        product_context: Optional[Dict] = None
    ) -> Dict:
        """
        Detect intent using ONLY the model - no patterns
        
        Args:
            text: Input text to analyze
            session_context: Previous conversation history
            product_context: Current product being discussed
            
        Returns:
            Dict with intent type, confidence, and entities
        """
        if not self.llm:
            logger.warning("No LLM configured, cannot detect intent")
            return {"type": "general", "confidence": 0.5, "entities": {}}
        
        # Build prompt from template
        detection_prompt = self.intent_prompt.get("intent_detection_prompt", {})
        prompt_template = detection_prompt.get("template", "")
        
        if not prompt_template:
            # Fallback prompt if file not loaded
            prompt_template = """Analyze this message and identify the user's intent.

Message: {text}

{context}

Respond with ONLY a JSON object containing:
- type: greeting|product_search|product_info|recommendation|purchase|checkout|help|general
- confidence: 0.0-1.0
- entities: extracted entities (products, effects, preferences, etc.)

JSON response:"""
        
        # Add context if available
        context_str = ""
        if session_context:
            recent = session_context[-3:] if len(session_context) > 3 else session_context
            context_lines = []
            for msg in recent:
                role = "Customer" if msg.get("role") == "user" else "Budtender"
                context_lines.append(f"{role}: {msg.get('content', '')}")
            context_str = "Recent conversation:\n" + "\n".join(context_lines)
        
        if product_context:
            context_str += f"\nCurrently discussing: {product_context.get('name', 'a product')}"
        
        prompt = prompt_template.format(text=text, context=context_str)
        
        try:
            # Get intent detection from model
            response = self.llm(
                prompt,
                max_tokens=150,
                temperature=0.3,  # Low temperature for consistent detection
                echo=False
            )
            
            # Extract JSON from response
            response_text = response.get('choices', [{}])[0].get('text', '').strip()
            
            # Try to parse JSON response
            try:
                # Clean up response to get JSON
                if '{' in response_text:
                    json_start = response_text.find('{')
                    json_end = response_text.rfind('}') + 1
                    json_str = response_text[json_start:json_end]
                    intent_data = json.loads(json_str)
                    
                    logger.info(f"Model detected intent: {intent_data.get('type')} for text: '{text[:50]}...'")
                    return intent_data
                else:
                    # Fallback if no JSON in response
                    logger.warning(f"No JSON in intent response: {response_text}")
                    return {"type": "general", "confidence": 0.5, "entities": {}}
                    
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse intent JSON: {e}, response: {response_text}")
                return {"type": "general", "confidence": 0.5, "entities": {}}
                
        except Exception as e:
            logger.error(f"Intent detection failed: {e}")
            return {"type": "general", "confidence": 0.5, "entities": {}}
    
    async def classify_query_complexity(self, text: str, intent: Dict) -> str:
        """
        Classify query complexity for routing
        Pure model-driven, no hardcoded rules
        """
        if not self.llm:
            return "simple"
        
        complexity_prompt = self.intent_prompt.get("complexity_prompt", {})
        prompt_template = complexity_prompt.get("template", "")
        
        if not prompt_template:
            prompt_template = """Classify the complexity of this query:

Query: {text}
Intent: {intent_type}

Respond with ONLY one word: simple, moderate, or complex

Complexity:"""
        
        prompt = prompt_template.format(text=text, intent_type=intent.get('type', 'general'))
        
        try:
            response = self.llm(
                prompt,
                max_tokens=10,
                temperature=0.1,
                echo=False
            )
            
            complexity = response.get('choices', [{}])[0].get('text', '').strip().lower()
            
            if complexity in ["simple", "moderate", "complex"]:
                return complexity
            else:
                return "moderate"
                
        except Exception as e:
            logger.error(f"Complexity classification failed: {e}")
            return "moderate"
    
    async def extract_entities(self, text: str, intent_type: str) -> Dict:
        """
        Extract entities from text based on intent
        Model-driven entity extraction
        """
        if not self.llm:
            return {}
        
        entity_prompt = self.intent_prompt.get("entity_extraction_prompt", {})
        prompt_template = entity_prompt.get("template", "")
        
        if not prompt_template:
            prompt_template = """Extract relevant entities from this {intent_type} query:

Query: {text}

Extract and return as JSON:
- products: mentioned product names
- effects: desired effects (relaxation, energy, pain relief, etc.)
- preferences: user preferences (price, strength, type, etc.)
- quantities: amounts mentioned
- actions: specific actions requested

JSON entities:"""
        
        prompt = prompt_template.format(text=text, intent_type=intent_type)
        
        try:
            response = self.llm(
                prompt,
                max_tokens=200,
                temperature=0.3,
                echo=False
            )
            
            response_text = response.get('choices', [{}])[0].get('text', '').strip()
            
            # Parse JSON response
            if '{' in response_text:
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                json_str = response_text[json_start:json_end]
                entities = json.loads(json_str)
                return entities
            
            return {}
            
        except Exception as e:
            logger.error(f"Entity extraction failed: {e}")
            return {}