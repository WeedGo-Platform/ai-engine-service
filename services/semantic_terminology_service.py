#!/usr/bin/env python3
"""
Semantic Terminology Service
Industry-standard LLM-based understanding of cannabis terminology
NO hardcoded mappings - pure semantic understanding
"""

import logging
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import re

logger = logging.getLogger(__name__)

@dataclass
class SemanticUnderstanding:
    """Represents the semantic understanding of a message"""
    normalized_text: str
    product_references: List[str]
    quantities: List[Dict]  # [{"amount": "3.5", "unit": "g", "slang": "eighth"}]
    effects_desired: List[str]
    characteristics_wanted: List[str]
    price_constraints: Optional[Dict] = None
    strain_preferences: Optional[str] = None
    consumption_method: Optional[str] = None


class SemanticTerminologyService:
    """
    Modern semantic understanding of cannabis terminology
    Uses LLM for all understanding - NO hardcoded mappings
    """
    
    def __init__(self, llm_function=None):
        self.llm = llm_function
        logger.info("Initialized SemanticTerminologyService - no hardcoded mappings!")
    
    async def understand_terminology(self, message: str) -> SemanticUnderstanding:
        """
        Use LLM to semantically understand cannabis terminology
        No pattern matching, no dictionaries, pure semantic understanding
        """
        
        if not self.llm:
            logger.warning("No LLM available, returning basic understanding")
            return SemanticUnderstanding(
                normalized_text=message.lower(),
                product_references=[],
                quantities=[],
                effects_desired=[],
                characteristics_wanted=[]
            )
        
        # Build semantic understanding prompt
        understanding_prompt = f"""You are a cannabis expert understanding customer language semantically.
Analyze this message and extract semantic meaning without using any patterns or mappings:

Customer Message: "{message}"

Extract and understand:

1. PRODUCT REFERENCES: What products/strains are they talking about?
   - Understand slang: "gas" means diesel/fuel strains, "loud" means potent, "fire" means premium
   - Recognize strain names even with misspellings
   - Identify product types from context

2. QUANTITIES: What amounts do they want?
   - Understand fractions: "1/4" = quarter ounce (7g), "1/8" = eighth (3.5g)
   - Understand slang: "zip" = ounce (28g), "quad" = quarter (7g)
   - Context matters: "half quarter" = half of 7g = 3.5g

3. EFFECTS: What effects are they seeking?
   - Understand intent: "couch-lock" = sedating, "heady" = cerebral
   - Recognize medical needs from description

4. CHARACTERISTICS: What product qualities do they want?
   - Understand descriptors: "frosty" = high trichomes, "sticky" = fresh/resinous
   - Recognize quality indicators

5. PRICE: Any price constraints mentioned?

6. STRAIN TYPE: Do they prefer sativa/indica/hybrid?

7. CONSUMPTION METHOD: How do they want to consume?
   - Understand preferences: "don't smoke" = needs alternative to flower

Output as JSON:
{{
    "normalized": "simplified clear version of request",
    "products": ["product1", "product2"],
    "quantities": [{{"amount": "3.5", "unit": "g", "original": "eighth"}}],
    "effects": ["effect1", "effect2"],
    "characteristics": ["char1", "char2"],
    "price_max": null,
    "strain_type": null,
    "consumption": null
}}

IMPORTANT: Use your semantic understanding of cannabis culture, not pattern matching.
"""
        
        try:
            # Get LLM understanding
            response = self.llm(understanding_prompt, max_tokens=300, temperature=0.1)
            
            if response and response.get('choices'):
                understanding_text = response['choices'][0]['text'].strip()
                
                # Parse JSON response
                json_match = re.search(r'\{.*\}', understanding_text, re.DOTALL)
                if json_match:
                    understanding_data = json.loads(json_match.group())
                    
                    logger.info(f"Semantic understanding: {understanding_data}")
                    
                    return SemanticUnderstanding(
                        normalized_text=understanding_data.get('normalized', message.lower()),
                        product_references=understanding_data.get('products', []),
                        quantities=understanding_data.get('quantities', []),
                        effects_desired=understanding_data.get('effects', []),
                        characteristics_wanted=understanding_data.get('characteristics', []),
                        price_constraints={'max': understanding_data.get('price_max')} if understanding_data.get('price_max') else None,
                        strain_preferences=understanding_data.get('strain_type'),
                        consumption_method=understanding_data.get('consumption')
                    )
                    
        except Exception as e:
            logger.error(f"Semantic understanding failed: {e}")
        
        # Fallback to basic understanding
        return SemanticUnderstanding(
            normalized_text=message.lower(),
            product_references=[],
            quantities=[],
            effects_desired=[],
            characteristics_wanted=[]
        )
    
    async def expand_search_semantically(self, message: str) -> List[str]:
        """
        Use LLM to semantically expand search terms
        No hardcoded mappings - pure semantic expansion
        """
        
        if not self.llm:
            return [message]
        
        expansion_prompt = f"""You are expanding a cannabis search query semantically.
Given this search: "{message}"

Generate semantically related search terms that would find similar products.
Think about:
- Synonyms and related terms
- Common strain families
- Similar effects/characteristics
- Alternative product forms

Output as a JSON array of search terms:
["term1", "term2", "term3", ...]

Maximum 10 terms. Be specific to cannabis domain.
"""
        
        try:
            response = self.llm(expansion_prompt, max_tokens=150, temperature=0.3)
            
            if response and response.get('choices'):
                expansion_text = response['choices'][0]['text'].strip()
                
                # Parse JSON array
                json_match = re.search(r'\[.*\]', expansion_text, re.DOTALL)
                if json_match:
                    expanded_terms = json.loads(json_match.group())
                    logger.info(f"Semantic expansion: {message} -> {expanded_terms}")
                    return expanded_terms[:10]
                    
        except Exception as e:
            logger.error(f"Semantic expansion failed: {e}")
        
        return [message]
    
    async def identify_product_type(self, message: str) -> Optional[str]:
        """
        Use LLM to identify product type from message
        No keyword matching - semantic understanding
        """
        
        if not self.llm:
            return None
        
        type_prompt = f"""Identify the cannabis product type from this message:
"{message}"

Product types:
- Flower (buds, nugs, eighths, quarters)
- Edibles (gummies, chocolates, cookies)
- Vapes (carts, cartridges, pens)
- Concentrates (dabs, wax, shatter, rosin)
- Pre-rolls (joints, blunts)
- Tinctures (drops, oils)
- Topicals (creams, balms)

Output just the product type or null if unclear.
"""
        
        try:
            response = self.llm(type_prompt, max_tokens=20, temperature=0)
            
            if response and response.get('choices'):
                product_type = response['choices'][0]['text'].strip().strip('"').strip("'")
                
                valid_types = ["Flower", "Edibles", "Vapes", "Concentrates", "Pre-rolls", "Tinctures", "Topicals"]
                if product_type in valid_types:
                    logger.info(f"Identified product type: {product_type}")
                    return product_type
                    
        except Exception as e:
            logger.error(f"Product type identification failed: {e}")
        
        return None
    
    async def correct_spelling_semantically(self, message: str) -> str:
        """
        Use LLM to correct cannabis-specific misspellings
        No dictionary lookups - semantic correction
        """
        
        if not self.llm:
            return message
        
        correction_prompt = f"""Correct any cannabis-related misspellings in this message:
"{message}"

Common issues:
- Strain names: "gellato" -> "gelato", "og" -> "OG", "purp" -> "purple"
- Product types: "catridge" -> "cartridge", "edable" -> "edible"
- Quantities: "eigth" -> "eighth"

Output the corrected message. Keep the original if no corrections needed.
"""
        
        try:
            response = self.llm(correction_prompt, max_tokens=100, temperature=0)
            
            if response and response.get('choices'):
                corrected = response['choices'][0]['text'].strip().strip('"')
                
                if corrected != message:
                    logger.info(f"Semantic correction: {message} -> {corrected}")
                    
                return corrected
                
        except Exception as e:
            logger.error(f"Semantic spelling correction failed: {e}")
        
        return message
    
    async def understand_preferences(self, message: str) -> Dict:
        """
        Use LLM to understand customer preferences semantically
        No pattern matching - pure understanding
        """
        
        if not self.llm:
            return {}
        
        preference_prompt = f"""Understand the customer's cannabis preferences from this message:
"{message}"

Extract preferences about:
- Consumption method (smoking, vaping, eating, etc.)
- Desired effects (relaxing, energizing, pain relief, etc.)
- Strain type (sativa, indica, hybrid)
- Potency level (mild, moderate, strong)
- Flavor/aroma preferences
- Medical vs recreational use
- Price sensitivity

Output as JSON with only mentioned preferences:
{{
    "consumption": "method or null",
    "effects": ["effect1", "effect2"],
    "strain_type": "type or null",
    "potency": "level or null",
    "flavors": ["flavor1"],
    "use_case": "medical/recreational or null",
    "price_sensitive": true/false
}}
"""
        
        try:
            response = self.llm(preference_prompt, max_tokens=200, temperature=0.1)
            
            if response and response.get('choices'):
                pref_text = response['choices'][0]['text'].strip()
                
                json_match = re.search(r'\{.*\}', pref_text, re.DOTALL)
                if json_match:
                    preferences = json.loads(json_match.group())
                    logger.info(f"Semantic preferences: {preferences}")
                    return preferences
                    
        except Exception as e:
            logger.error(f"Preference understanding failed: {e}")
        
        return {}


# Global instance for backward compatibility
semantic_terminology = None

def initialize_semantic_terminology(llm_function=None):
    """Initialize the global semantic terminology service"""
    global semantic_terminology
    semantic_terminology = SemanticTerminologyService(llm_function)
    return semantic_terminology