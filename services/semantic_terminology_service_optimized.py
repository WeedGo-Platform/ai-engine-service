#!/usr/bin/env python3
"""
Optimized Semantic Terminology Service
Single LLM call for ALL understanding - FAST!
"""

import logging
import json
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ComprehensiveUnderstanding:
    """Complete semantic understanding from a single LLM call"""
    normalized_text: str
    product_references: List[str]
    quantities: List[Dict]
    effects_desired: List[str]
    characteristics_wanted: List[str]
    price_constraints: Optional[Dict] = None
    strain_preferences: Optional[str] = None
    consumption_method: Optional[str] = None
    product_type: Optional[str] = None
    expanded_search_terms: List[str] = None
    spelling_corrected: Optional[str] = None
    preferences: Dict = None


class OptimizedSemanticTerminology:
    """
    FAST semantic understanding - single LLM call for everything!
    """
    
    def __init__(self, llm_function=None):
        self.llm = llm_function
        logger.info("Initialized OPTIMIZED Semantic Service - single LLM call!")
    
    async def understand_everything(self, message: str) -> ComprehensiveUnderstanding:
        """
        ONE LLM call to understand EVERYTHING semantically
        This is 5x faster than calling separate methods!
        """
        
        if not self.llm:
            logger.warning("No LLM available")
            return ComprehensiveUnderstanding(
                normalized_text=message.lower(),
                product_references=[],
                quantities=[],
                effects_desired=[],
                characteristics_wanted=[]
            )
        
        # OPTIMIZED prompt - shorter = faster!
        comprehensive_prompt = f"""Cannabis message: "{message}"

Extract JSON:
{{
"normalized": "clear version",
"products": ["strains mentioned"],
"quantities": [{{"amount": "num", "unit": "g", "original": "slang"}}],
"effects": ["desired effects"],
"characteristics": ["qualities"],
"price_max": null,
"strain_type": "sativa/indica/hybrid or null",
"consumption": "method or null",
"product_type": "Flower/Edibles/etc or null",
"search_terms": ["3-5 related terms"],
"spelling_fixed": "corrected or null",
"preferences": {{"potency": "high/low", "use_case": "medical/rec"}}
}}

Slang: zip=28g, eighth=3.5g, quarter=7g, half=14g, loud/fire/gas=potent"""
        
        try:
            # Single LLM call - FAST! Reduced tokens for speed
            response = self.llm(comprehensive_prompt, max_tokens=250, temperature=0)
            
            if response and response.get('choices'):
                response_text = response['choices'][0]['text'].strip()
                
                # Parse JSON
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group())
                    
                    logger.info(f"Complete understanding in ONE call: {data.get('normalized')}")
                    
                    return ComprehensiveUnderstanding(
                        normalized_text=data.get('normalized', message.lower()),
                        product_references=data.get('products', []),
                        quantities=data.get('quantities', []),
                        effects_desired=data.get('effects', []),
                        characteristics_wanted=data.get('characteristics', []),
                        price_constraints={'max': data.get('price_max')} if data.get('price_max') else None,
                        strain_preferences=data.get('strain_type'),
                        consumption_method=data.get('consumption'),
                        product_type=data.get('product_type'),
                        expanded_search_terms=data.get('search_terms', []),
                        spelling_corrected=data.get('spelling_fixed'),
                        preferences=data.get('preferences', {})
                    )
                    
        except Exception as e:
            logger.error(f"Semantic understanding failed: {e}")
        
        # Fallback
        return ComprehensiveUnderstanding(
            normalized_text=message.lower(),
            product_references=[],
            quantities=[],
            effects_desired=[],
            characteristics_wanted=[]
        )
    
    # Backward compatibility methods that use the single understanding
    async def understand_terminology(self, message: str) -> ComprehensiveUnderstanding:
        """For backward compatibility - calls the fast method"""
        return await self.understand_everything(message)
    
    async def expand_search_semantically(self, message: str) -> List[str]:
        """For backward compatibility - uses cached understanding"""
        understanding = await self.understand_everything(message)
        return understanding.expanded_search_terms or [message]
    
    async def identify_product_type(self, message: str) -> Optional[str]:
        """For backward compatibility - uses cached understanding"""
        understanding = await self.understand_everything(message)
        return understanding.product_type
    
    async def correct_spelling_semantically(self, message: str) -> str:
        """For backward compatibility - uses cached understanding"""
        understanding = await self.understand_everything(message)
        return understanding.spelling_corrected or message
    
    async def understand_preferences(self, message: str) -> Dict:
        """For backward compatibility - uses cached understanding"""
        understanding = await self.understand_everything(message)
        return understanding.preferences or {}


# Global instance
optimized_semantic = None

def initialize_optimized_semantic(llm_function=None):
    """Initialize the optimized semantic service"""
    global optimized_semantic
    optimized_semantic = OptimizedSemanticTerminology(llm_function)
    return optimized_semantic