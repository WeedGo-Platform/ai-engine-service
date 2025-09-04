#!/usr/bin/env python3
"""
Cannabis Domain Prompt Engineering
Specialized prompt templates and optimization for dispensary conversations
"""

import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class PromptStrategy(Enum):
    """Different prompt strategies for various scenarios"""
    PRODUCT_RECOMMENDATION = "product_recommendation"
    MEDICAL_CONSULTATION = "medical_consultation"
    BEGINNER_EDUCATION = "beginner_education"
    STRAIN_COMPARISON = "strain_comparison"
    DOSAGE_GUIDANCE = "dosage_guidance"
    EFFECTS_EXPLANATION = "effects_explanation"

@dataclass
class PromptComponents:
    """Components that make up a complete prompt"""
    system_role: str
    domain_knowledge: str
    few_shot_examples: List[Dict[str, str]]
    context: str
    constraints: List[str]
    output_format: str

class CannabisPromptEngineer:
    """Engineer optimized prompts for cannabis domain"""
    
    # Cannabis domain knowledge base
    CANNABIS_KNOWLEDGE = {
        "cannabinoids": {
            "THC": {
                "full_name": "Tetrahydrocannabinol",
                "effects": ["euphoria", "relaxation", "increased appetite", "altered perception"],
                "medical_uses": ["pain relief", "nausea reduction", "appetite stimulation"],
                "onset": {"smoking": "minutes", "edibles": "30-120 minutes"},
                "duration": {"smoking": "1-3 hours", "edibles": "4-8 hours"}
            },
            "CBD": {
                "full_name": "Cannabidiol",
                "effects": ["relaxation", "anxiety reduction", "anti-inflammatory"],
                "medical_uses": ["anxiety", "inflammation", "seizures", "pain"],
                "onset": {"oil": "15-45 minutes", "topical": "minutes"},
                "non_psychoactive": True
            },
            "CBG": {
                "full_name": "Cannabigerol",
                "effects": ["focus", "alertness", "anti-inflammatory"],
                "medical_uses": ["glaucoma", "inflammatory bowel disease", "huntington's disease"]
            },
            "CBN": {
                "full_name": "Cannabinol",
                "effects": ["sedation", "relaxation"],
                "medical_uses": ["insomnia", "pain relief"]
            }
        },
        "terpenes": {
            "myrcene": {
                "aroma": "earthy, musky, cloves",
                "effects": ["sedating", "muscle relaxant", "anti-inflammatory"],
                "found_in": ["mangoes", "hops", "thyme"]
            },
            "limonene": {
                "aroma": "citrus",
                "effects": ["mood elevation", "stress relief", "anti-anxiety"],
                "found_in": ["lemons", "oranges", "juniper"]
            },
            "pinene": {
                "aroma": "pine",
                "effects": ["alertness", "memory retention", "counteracts THC effects"],
                "found_in": ["pine needles", "rosemary", "basil"]
            },
            "linalool": {
                "aroma": "floral, lavender",
                "effects": ["calming", "anti-anxiety", "sedating"],
                "found_in": ["lavender", "mint", "cinnamon"]
            },
            "caryophyllene": {
                "aroma": "spicy, peppery",
                "effects": ["anti-inflammatory", "pain relief"],
                "unique": "only terpene that binds to CB2 receptors"
            }
        },
        "strain_categories": {
            "sativa": {
                "typical_effects": ["energizing", "uplifting", "creative", "focused"],
                "best_for": ["daytime use", "social activities", "creative work", "exercise"],
                "physical": "tall plants, narrow leaves, longer flowering time",
                "common_terpenes": ["limonene", "pinene"]
            },
            "indica": {
                "typical_effects": ["relaxing", "sedating", "body high", "appetite boost"],
                "best_for": ["evening use", "pain relief", "insomnia", "relaxation"],
                "physical": "short plants, broad leaves, shorter flowering time",
                "common_terpenes": ["myrcene", "linalool"]
            },
            "hybrid": {
                "typical_effects": ["balanced", "versatile", "strain-specific"],
                "best_for": ["anytime use", "specific effect combinations"],
                "types": ["sativa-dominant", "indica-dominant", "balanced"]
            }
        },
        "consumption_methods": {
            "smoking": {
                "onset": "immediate",
                "duration": "1-3 hours",
                "bioavailability": "10-35%",
                "pros": ["fast acting", "easy dosing"],
                "cons": ["lung irritation", "smell"]
            },
            "vaporizing": {
                "onset": "immediate",
                "duration": "1-3 hours",
                "bioavailability": "30-40%",
                "pros": ["less harsh", "better flavor", "discrete"],
                "cons": ["equipment cost"]
            },
            "edibles": {
                "onset": "30-120 minutes",
                "duration": "4-8 hours",
                "bioavailability": "4-20%",
                "pros": ["long lasting", "discrete", "no lung impact"],
                "cons": ["delayed onset", "harder to dose"]
            },
            "tinctures": {
                "onset": "15-45 minutes",
                "duration": "2-4 hours",
                "bioavailability": "20-30%",
                "pros": ["precise dosing", "discrete"],
                "cons": ["taste"]
            },
            "topicals": {
                "onset": "minutes",
                "duration": "1-2 hours",
                "bioavailability": "0% (no psychoactive effects)",
                "pros": ["localized relief", "no high"],
                "cons": ["surface-level only"]
            }
        }
    }
    
    def __init__(self):
        self.strategies = self._initialize_strategies()
        
    def _initialize_strategies(self) -> Dict[PromptStrategy, PromptComponents]:
        """Initialize prompt strategies for different scenarios"""
        
        strategies = {
            PromptStrategy.PRODUCT_RECOMMENDATION: PromptComponents(
                system_role="""You are an expert cannabis budtender with deep knowledge of strains, terpenes, and effects.
                Your goal is to recommend the perfect products based on customer needs, experience level, and desired effects.
                Always prioritize safety and appropriate dosing.""",
                
                domain_knowledge=json.dumps(self.CANNABIS_KNOWLEDGE["strain_categories"]),
                
                few_shot_examples=[
                    {
                        "input": "I need something for energy and focus",
                        "output": "For energy and focus, I recommend sativa strains high in limonene and pinene. 'Green Crack' provides pure energy without anxiety, while 'Jack Herer' offers focused creativity. Both have around 18-20% THC. Start with a small amount to gauge your tolerance."
                    },
                    {
                        "input": "Looking for pain relief without getting too high",
                        "output": "For pain relief with minimal psychoactive effects, try high-CBD strains like 'Harlequin' (2:1 CBD/THC ratio) or 'ACDC' (20:1 CBD/THC). These provide anti-inflammatory benefits without intense highs. Topical CBD creams also offer localized relief with zero psychoactive effects."
                    }
                ],
                
                context="Customer profile: {profile}\nCurrent request: {request}",
                
                constraints=[
                    "Recommend 2-3 specific products",
                    "Include THC/CBD percentages",
                    "Mention appropriate dosing",
                    "Consider experience level",
                    "Stay within budget if specified"
                ],
                
                output_format="Provide recommendations in this format: Product name, strain type, THC/CBD levels, effects, and suggested use."
            ),
            
            PromptStrategy.MEDICAL_CONSULTATION: PromptComponents(
                system_role="""You are a knowledgeable cannabis wellness consultant.
                Provide evidence-based information about cannabis for various conditions.
                Always emphasize that this is not medical advice and customers should consult healthcare providers.""",
                
                domain_knowledge=json.dumps(self.CANNABIS_KNOWLEDGE["cannabinoids"]),
                
                few_shot_examples=[
                    {
                        "input": "I have chronic arthritis pain",
                        "output": "Many customers with arthritis find relief with CBD-rich products for anti-inflammatory effects. Balanced THC/CBD ratios like 1:1 can provide pain relief while minimizing psychoactive effects. Topical creams target specific areas, while tinctures offer systemic relief. Start with low doses and track your response. Always consult your doctor, especially if taking other medications."
                    }
                ],
                
                context="Condition: {condition}\nCurrent medications: {medications}\nExperience: {experience}",
                
                constraints=[
                    "Don't make medical claims",
                    "Suggest consulting healthcare providers",
                    "Focus on general wellness",
                    "Mention potential interactions"
                ],
                
                output_format="Provide educational information about how cannabis may help, always with appropriate disclaimers."
            ),
            
            PromptStrategy.BEGINNER_EDUCATION: PromptComponents(
                system_role="""You are a patient, friendly cannabis educator helping newcomers.
                Explain concepts simply, emphasize safety, and build confidence.
                Use analogies and avoid overwhelming with technical details.""",
                
                domain_knowledge=json.dumps(self.CANNABIS_KNOWLEDGE["consumption_methods"]),
                
                few_shot_examples=[
                    {
                        "input": "I've never tried cannabis, where do I start?",
                        "output": "Welcome! Starting with cannabis is like learning to swim - begin in the shallow end. Try low-THC products (5-10%) or balanced CBD options. If smoking, take one small puff and wait 15 minutes. For edibles, start with 2.5mg and wait 2 hours. Choose indica for relaxation or sativa for energy. Most importantly, be in a comfortable, safe environment your first time."
                    }
                ],
                
                context="Experience level: beginner\nConcerns: {concerns}\nGoals: {goals}",
                
                constraints=[
                    "Use simple language",
                    "Emphasize 'start low, go slow'",
                    "Address common concerns",
                    "Suggest beginner-friendly products"
                ],
                
                output_format="Provide clear, reassuring guidance appropriate for beginners."
            ),
            
            PromptStrategy.DOSAGE_GUIDANCE: PromptComponents(
                system_role="""You are a cannabis dosing expert who helps customers find their optimal dose.
                Provide specific, conservative dosing recommendations based on experience and consumption method.""",
                
                domain_knowledge=json.dumps({
                    "dosing_guidelines": {
                        "beginner": {
                            "smoking": "1 small puff, wait 15 min",
                            "edibles": "2.5mg THC, wait 2 hours",
                            "tinctures": "0.25ml, wait 45 min"
                        },
                        "intermediate": {
                            "smoking": "2-3 puffs",
                            "edibles": "5-10mg THC",
                            "tinctures": "0.5-1ml"
                        },
                        "experienced": {
                            "smoking": "as needed",
                            "edibles": "10-25mg THC",
                            "tinctures": "1-2ml"
                        }
                    }
                }),
                
                few_shot_examples=[
                    {
                        "input": "How much edible should I take?",
                        "output": "For edibles, your dose depends on experience. Beginners: start with 2.5mg THC and wait 2 full hours before taking more - edibles can take up to 2 hours to peak. Regular users: 5-10mg is typical. Remember, you can always take more, but you can't take less once consumed. Keep CBD on hand as it can help if you get too high."
                    }
                ],
                
                context="Experience: {experience}\nMethod: {method}\nTolerance: {tolerance}",
                
                constraints=[
                    "Always err on the conservative side",
                    "Explain onset and duration",
                    "Mention what to do if too high",
                    "Consider individual factors"
                ],
                
                output_format="Provide specific dosing recommendations with timing guidance."
            )
        }
        
        return strategies
    
    def generate_prompt(self, 
                        strategy: PromptStrategy,
                        context: Dict[str, Any],
                        include_examples: bool = True,
                        max_examples: int = 2) -> str:
        """Generate an optimized prompt for the given strategy"""
        
        components = self.strategies.get(strategy)
        if not components:
            raise ValueError(f"Unknown strategy: {strategy}")
        
        # Build the prompt
        prompt_parts = []
        
        # System role
        prompt_parts.append(f"System: {components.system_role}")
        
        # Domain knowledge
        prompt_parts.append(f"\nDomain Knowledge:\n{components.domain_knowledge}")
        
        # Few-shot examples
        if include_examples and components.few_shot_examples:
            prompt_parts.append("\nExamples:")
            for example in components.few_shot_examples[:max_examples]:
                prompt_parts.append(f"User: {example['input']}")
                prompt_parts.append(f"Assistant: {example['output']}\n")
        
        # Constraints
        if components.constraints:
            prompt_parts.append("\nGuidelines:")
            for constraint in components.constraints:
                prompt_parts.append(f"- {constraint}")
        
        # Context
        if components.context:
            formatted_context = components.context.format(**context)
            prompt_parts.append(f"\nContext: {formatted_context}")
        
        # Output format
        if components.output_format:
            prompt_parts.append(f"\n{components.output_format}")
        
        # Current query
        if "query" in context:
            prompt_parts.append(f"\nUser Query: {context['query']}")
            prompt_parts.append("\nAssistant:")
        
        return "\n".join(prompt_parts)
    
    def optimize_for_speed(self, prompt: str) -> str:
        """Optimize prompt for faster inference"""
        
        # Remove excessive whitespace
        prompt = " ".join(prompt.split())
        
        # Shorten if too long
        if len(prompt) > 1500:
            # Keep essential parts
            lines = prompt.split('\n')
            essential_parts = []
            
            # Keep system role
            for line in lines[:3]:
                essential_parts.append(line)
            
            # Keep one example
            example_start = None
            for i, line in enumerate(lines):
                if "Examples:" in line:
                    example_start = i
                    break
            
            if example_start:
                essential_parts.extend(lines[example_start:example_start+4])
            
            # Keep context and query
            for line in lines[-5:]:
                essential_parts.append(line)
            
            prompt = "\n".join(essential_parts)
        
        return prompt
    
    def add_safety_guidelines(self, prompt: str) -> str:
        """Add safety and compliance guidelines to any prompt"""
        
        safety_text = """
        Safety Guidelines:
        - Never recommend driving while impaired
        - Emphasize starting with low doses
        - Mention waiting periods between doses
        - Include age verification reminders (19+ in Ontario)
        - Don't make unverified medical claims
        - Suggest safe consumption environments
        """
        
        return prompt + safety_text
    
    def create_chain_of_thought_prompt(self, task: str, context: Dict) -> str:
        """Create a chain-of-thought prompt for complex reasoning"""
        
        cot_template = """Let's think through this step by step.
        
        Task: {task}
        
        Step 1: Understand the customer's needs
        - What effects are they seeking?
        - What's their experience level?
        - Are there any constraints (budget, time of use, medical conditions)?
        
        Step 2: Consider appropriate options
        - Which strain types match their needs?
        - What THC/CBD ratio is appropriate?
        - Which consumption method suits them?
        
        Step 3: Make specific recommendations
        - Select 2-3 products that best match
        - Explain why each is suitable
        - Provide dosing guidance
        
        Context: {context}
        
        Now, let's apply this thinking:
        """
        
        return cot_template.format(task=task, context=json.dumps(context))
    
    def create_rag_prompt(self, query: str, retrieved_context: List[str]) -> str:
        """Create a Retrieval-Augmented Generation prompt"""
        
        rag_template = """Based on the following information from our knowledge base, answer the customer's question.
        
        Retrieved Information:
        {retrieved_context}
        
        Customer Question: {query}
        
        Provide a helpful, accurate answer based on the retrieved information. If the information doesn't fully answer the question, acknowledge what you can answer and what might need clarification.
        
        Answer:"""
        
        context_text = "\n".join([f"- {ctx}" for ctx in retrieved_context[:5]])
        return rag_template.format(retrieved_context=context_text, query=query)
    
    def get_prompt_metrics(self, prompt: str) -> Dict[str, Any]:
        """Analyze prompt characteristics for optimization"""
        
        tokens_estimate = len(prompt.split()) * 1.3  # Rough token estimate
        
        return {
            "character_count": len(prompt),
            "word_count": len(prompt.split()),
            "estimated_tokens": int(tokens_estimate),
            "line_count": len(prompt.split('\n')),
            "has_examples": "Examples:" in prompt or "example" in prompt.lower(),
            "has_constraints": "Guidelines:" in prompt or "constraints" in prompt.lower(),
            "optimization_suggestions": []
        }
        
        # Add optimization suggestions
        if tokens_estimate > 1000:
            return["optimization_suggestions"].append("Consider reducing prompt length for faster inference")
        if not "Examples:" in prompt:
            return["optimization_suggestions"].append("Adding few-shot examples may improve response quality")
        
        return metrics
    
    @staticmethod
    def create_evaluation_prompt(response: str) -> str:
        """Create a prompt to evaluate the quality of a generated response"""
        
        eval_template = """Evaluate the following budtender response on these criteria:
        
        Response: {response}
        
        Criteria:
        1. Accuracy: Is the cannabis information correct?
        2. Safety: Does it emphasize safe consumption?
        3. Helpfulness: Does it address the customer's needs?
        4. Clarity: Is it easy to understand?
        5. Compliance: Does it follow regulations?
        
        Rate each criterion 1-5 and provide a brief explanation.
        """
        
        return eval_template.format(response=response)

class AdaptivePromptManager:
    """Manages dynamic prompt adaptation based on conversation flow"""
    
    def __init__(self, prompt_engineer: CannabisPromptEngineer):
        self.prompt_engineer = prompt_engineer
        self.conversation_history = {}
        self.performance_metrics = {}
        
    def select_strategy(self, message: str, context: Dict) -> PromptStrategy:
        """Dynamically select the best prompt strategy"""
        
        message_lower = message.lower()
        
        # Keywords to strategy mapping
        if any(word in message_lower for word in ["recommend", "suggest", "looking for", "need", "want"]):
            return PromptStrategy.PRODUCT_RECOMMENDATION
        elif any(word in message_lower for word in ["pain", "sleep", "anxiety", "nausea", "inflammation"]):
            return PromptStrategy.MEDICAL_CONSULTATION
        elif any(word in message_lower for word in ["first time", "never tried", "beginner", "new to"]):
            return PromptStrategy.BEGINNER_EDUCATION
        elif any(word in message_lower for word in ["how much", "dose", "dosage", "amount"]):
            return PromptStrategy.DOSAGE_GUIDANCE
        elif any(word in message_lower for word in ["difference between", "versus", "vs", "compare"]):
            return PromptStrategy.STRAIN_COMPARISON
        else:
            return PromptStrategy.EFFECTS_EXPLANATION
    
    def adapt_prompt(self, base_prompt: str, performance_data: Dict) -> str:
        """Adapt prompt based on performance metrics"""
        
        # If responses are too long, add brevity instruction
        if performance_data.get("avg_response_length", 0) > 150:
            base_prompt += "\nKeep response under 100 words."
        
        # If confidence is low, add more examples
        if performance_data.get("avg_confidence", 1.0) < 0.7:
            base_prompt = base_prompt.replace("Examples:", "Examples (study these carefully):")
        
        # If response time is slow, optimize
        if performance_data.get("avg_response_time_ms", 0) > 1000:
            base_prompt = self.prompt_engineer.optimize_for_speed(base_prompt)
        
        return base_prompt
    
    def track_performance(self, prompt_strategy: PromptStrategy, 
                         response_time_ms: int, 
                         confidence: float,
                         response_length: int):
        """Track performance metrics for adaptive optimization"""
        
        if prompt_strategy not in self.performance_metrics:
            self.performance_metrics[prompt_strategy] = {
                "count": 0,
                "total_time_ms": 0,
                "total_confidence": 0,
                "total_length": 0
            }
        
        metrics = self.performance_metrics[prompt_strategy]
        metrics["count"] += 1
        metrics["total_time_ms"] += response_time_ms
        metrics["total_confidence"] += confidence
        metrics["total_length"] += response_length
        
        # Calculate averages
        metrics["avg_response_time_ms"] = metrics["total_time_ms"] / metrics["count"]
        metrics["avg_confidence"] = metrics["total_confidence"] / metrics["count"]
        metrics["avg_response_length"] = metrics["total_length"] / metrics["count"]
    
    def get_optimization_report(self) -> Dict:
        """Generate optimization report"""
        
        report = {
            "strategy_performance": {},
            "recommendations": []
        }
        
        for strategy, metrics in self.performance_metrics.items():
            report["strategy_performance"][strategy.value] = {
                "uses": metrics["count"],
                "avg_time_ms": metrics.get("avg_response_time_ms", 0),
                "avg_confidence": metrics.get("avg_confidence", 0),
                "avg_length": metrics.get("avg_response_length", 0)
            }
            
            # Add recommendations
            if metrics.get("avg_response_time_ms", 0) > 1000:
                report["recommendations"].append(
                    f"Optimize {strategy.value} prompts for speed"
                )
            if metrics.get("avg_confidence", 0) < 0.7:
                report["recommendations"].append(
                    f"Add more examples to {strategy.value} prompts"
                )
        
        return report