"""
Model Router - Intelligent routing to appropriate AI model
Uses strategy pattern for routing decisions
"""

import re
import logging
from typing import List, Dict, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)

class QueryType(Enum):
    """Types of queries for routing"""
    MEDICAL = "medical"
    TECHNICAL = "technical"
    GENERAL = "general"
    GREETING = "greeting"
    PRODUCT_SEARCH = "product_search"

class ModelRouter:
    """
    Routes queries to appropriate models based on content analysis
    Strategy Pattern: Different routing strategies for different query types
    """
    
    def __init__(self):
        # Medical/health related keywords
        self.medical_keywords = {
            "pain", "anxiety", "stress", "sleep", "insomnia", "medical",
            "chronic", "relief", "symptom", "condition", "treatment",
            "therapy", "ptsd", "depression", "inflammation", "arthritis",
            "migraine", "nausea", "appetite", "seizure", "muscle",
            "spasm", "cancer", "epilepsy", "cbd", "thc ratio",
            "dosage", "medication", "prescription", "doctor", "health"
        }
        
        # Technical cannabis keywords
        self.technical_keywords = {
            "terpene", "cannabinoid", "entourage", "extraction",
            "distillate", "isolate", "spectrum", "bioavailability",
            "decarboxylation", "endocannabinoid", "receptor",
            "pharmacology", "metabolism", "half-life", "potency",
            "certificate", "analysis", "testing", "microdosing"
        }
        
        # Greeting patterns
        self.greeting_patterns = [
            r"^(hi|hello|hey|greetings|good\s+(morning|afternoon|evening))[\s!]*$",
            r"^(bonjour|salut|bonsoir)[\s!]*$",
            r"^(hola|buenos)[\s!]*$",
            r"^(olá|oi)[\s!]*$",
            r"^(مرحبا|السلام)[\s!]*$",
            r"^(你好|您好)[\s!]*$"
        ]
        
        # Product search patterns
        self.product_patterns = [
            r"(show|find|search|looking for|need|want|recommend)",
            r"(strain|product|flower|edible|oil|vape|pre-roll|preroll)",
            r"(indica|sativa|hybrid)",
            r"(price|cost|cheap|expensive|budget)"
        ]
    
    def select_model(
        self,
        message: str,
        language: str = "en",
        available_models: List[Any] = None
    ) -> Any:
        """
        Select the best model for the query
        
        Args:
            message: User message
            language: Language code
            available_models: List of available model types
        
        Returns:
            Selected model type
        """
        from services.model_manager import ModelType
        
        # Analyze query type
        query_type = self._analyze_query_type(message)
        
        # Score models based on query type
        scores = self._score_models(query_type, language, available_models)
        
        # Select highest scoring available model
        if available_models:
            available_scores = {
                model: scores.get(model, 0)
                for model in available_models
            }
            
            if available_scores:
                selected = max(available_scores, key=available_scores.get)
                
                logger.info(
                    f"Routing query to {selected.value} "
                    f"(type: {query_type.value}, score: {available_scores[selected]})"
                )
                
                return selected
        
        # Default fallback
        return ModelType.LLAMA2_7B if ModelType.LLAMA2_7B in available_models else ModelType.FALLBACK
    
    def _analyze_query_type(self, message: str) -> QueryType:
        """Analyze the type of query"""
        message_lower = message.lower()
        
        # Check for greetings first
        for pattern in self.greeting_patterns:
            if re.match(pattern, message_lower, re.IGNORECASE):
                return QueryType.GREETING
        
        # Count keyword matches
        medical_count = sum(
            1 for keyword in self.medical_keywords
            if keyword in message_lower
        )
        
        technical_count = sum(
            1 for keyword in self.technical_keywords
            if keyword in message_lower
        )
        
        product_count = sum(
            1 for pattern in self.product_patterns
            if re.search(pattern, message_lower)
        )
        
        # Determine primary type
        if medical_count >= 2 or "medical" in message_lower:
            return QueryType.MEDICAL
        elif technical_count >= 2:
            return QueryType.TECHNICAL
        elif product_count >= 2:
            return QueryType.PRODUCT_SEARCH
        else:
            return QueryType.GENERAL
    
    def _score_models(
        self,
        query_type: QueryType,
        language: str,
        available_models: List[Any]
    ) -> Dict[Any, float]:
        """Score models based on query characteristics"""
        from services.model_manager import ModelType
        
        scores = {}
        
        # Base scores for each model
        base_scores = {
            ModelType.LLAMA2_7B: {
                QueryType.GENERAL: 10,
                QueryType.GREETING: 8,
                QueryType.PRODUCT_SEARCH: 9,
                QueryType.TECHNICAL: 7,
                QueryType.MEDICAL: 6
            },
            ModelType.MISTRAL_7B: {
                QueryType.MEDICAL: 10,
                QueryType.TECHNICAL: 9,
                QueryType.PRODUCT_SEARCH: 8,
                QueryType.GENERAL: 7,
                QueryType.GREETING: 6
            },
            ModelType.FALLBACK: {
                QueryType.GREETING: 5,
                QueryType.GENERAL: 3,
                QueryType.PRODUCT_SEARCH: 2,
                QueryType.TECHNICAL: 1,
                QueryType.MEDICAL: 1
            }
        }
        
        # Calculate scores
        for model_type in [ModelType.LLAMA2_7B, ModelType.MISTRAL_7B, ModelType.FALLBACK]:
            if model_type in base_scores:
                score = base_scores[model_type].get(query_type, 5)
                
                # Bonus for language support
                if language != "en":
                    # Both LLMs support multiple languages well
                    if model_type in [ModelType.LLAMA2_7B, ModelType.MISTRAL_7B]:
                        score += 2
                
                # Penalty if model not available
                if available_models and model_type not in available_models:
                    score = 0
                
                scores[model_type] = score
        
        return scores
    
    def get_routing_metrics(self) -> Dict[str, Any]:
        """Get routing statistics and metrics"""
        # This would connect to a metrics store in production
        return {
            "total_routes": 0,
            "model_distribution": {},
            "query_type_distribution": {},
            "average_confidence": 0.0
        }