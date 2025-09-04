"""
Cannabis Domain Prompt Manager
Manages specialized prompts for cannabis industry knowledge and recommendations
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path

from langchain.prompts import (
    PromptTemplate,
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    FewShotPromptTemplate
)
from langchain.prompts.example_selector import SemanticSimilarityExampleSelector
from langchain.embeddings import HuggingFaceEmbeddings

logger = logging.getLogger(__name__)

class PromptCategory(Enum):
    """Categories of cannabis-related prompts"""
    PRODUCT_RECOMMENDATION = "product_recommendation"
    STRAIN_INFORMATION = "strain_information"
    MEDICAL_CONSULTATION = "medical_consultation"
    EFFECTS_DESCRIPTION = "effects_description"
    TERPENE_EDUCATION = "terpene_education"
    DOSAGE_GUIDANCE = "dosage_guidance"
    LEGAL_COMPLIANCE = "legal_compliance"
    CONSUMPTION_METHODS = "consumption_methods"
    GROWING_ADVICE = "growing_advice"
    GENERAL_EDUCATION = "general_education"

@dataclass
class PromptConfig:
    """Configuration for prompt templates"""
    category: PromptCategory
    template: str
    input_variables: List[str]
    output_parser: Optional[Any] = None
    examples: List[Dict[str, str]] = None
    metadata: Dict[str, Any] = None

class CannabisPromptManager:
    """
    Manages cannabis-specific prompt templates and few-shot examples
    """
    
    def __init__(self):
        self.templates: Dict[PromptCategory, PromptTemplate] = {}
        self.few_shot_templates: Dict[PromptCategory, FewShotPromptTemplate] = {}
        self.system_prompts: Dict[str, str] = {}
        self._load_templates()
        self._load_system_prompts()
        
    def _load_templates(self):
        """Load all prompt templates"""
        
        # Product Recommendation Template
        self.templates[PromptCategory.PRODUCT_RECOMMENDATION] = PromptTemplate(
            input_variables=["customer_profile", "preferences", "medical_conditions", "context", "available_products"],
            template="""You are an expert cannabis budtender helping a customer find the perfect product.

Customer Profile:
{customer_profile}

Preferences:
{preferences}

Medical Conditions/Symptoms:
{medical_conditions}

Context:
{context}

Available Products:
{available_products}

Based on this information, recommend the most suitable cannabis products. Consider:
1. The customer's experience level and tolerance
2. Desired effects and medical benefits
3. THC/CBD ratios appropriate for their needs
4. Terpene profiles that match their preferences
5. Consumption method preferences
6. Time of day and usage context
7. Any potential interactions or contraindications

Provide detailed recommendations with explanations for each product, including:
- Why this product suits their needs
- Expected effects and onset time
- Recommended dosage for their experience level
- Any precautions or considerations

Recommendations:"""
        )
        
        # Strain Information Template
        self.templates[PromptCategory.STRAIN_INFORMATION] = PromptTemplate(
            input_variables=["strain_name", "category", "genetics", "thc_content", "cbd_content", "terpenes"],
            template="""Provide comprehensive information about the following cannabis strain:

Strain: {strain_name}
Category: {category}
Genetics: {genetics}
THC Content: {thc_content}%
CBD Content: {cbd_content}%
Dominant Terpenes: {terpenes}

Please provide:
1. Detailed effects profile (mental and physical)
2. Medical benefits and recommended uses
3. Potential side effects or considerations
4. Best time of day for consumption
5. Ideal for which type of users (beginner, intermediate, experienced)
6. Flavor and aroma profile
7. Growing characteristics (if relevant)
8. Historical background or interesting facts

Strain Information:"""
        )
        
        # Medical Consultation Template
        self.templates[PromptCategory.MEDICAL_CONSULTATION] = PromptTemplate(
            input_variables=["symptoms", "current_medications", "medical_history", "previous_cannabis_use"],
            template="""As a cannabis wellness consultant, provide guidance for medical cannabis use.

DISCLAIMER: This is educational information only. Always consult with a healthcare provider before using cannabis for medical purposes.

Symptoms/Conditions:
{symptoms}

Current Medications:
{current_medications}

Relevant Medical History:
{medical_history}

Previous Cannabis Experience:
{previous_cannabis_use}

Based on this information, provide:
1. Potentially beneficial cannabinoid profiles (THC:CBD ratios)
2. Recommended delivery methods for these symptoms
3. Starting dosage suggestions (start low, go slow)
4. Potential drug interactions to be aware of
5. Terpenes that may provide additional therapeutic benefits
6. Timing and frequency recommendations
7. What to monitor and when to adjust
8. When to seek medical advice

Medical Cannabis Guidance:"""
        )
        
        # Effects Description Template
        self.templates[PromptCategory.EFFECTS_DESCRIPTION] = PromptTemplate(
            input_variables=["product_name", "cannabinoid_profile", "terpene_profile", "consumption_method"],
            template="""Describe the expected effects of this cannabis product:

Product: {product_name}
Cannabinoid Profile: {cannabinoid_profile}
Terpene Profile: {terpene_profile}
Consumption Method: {consumption_method}

Provide a detailed effects timeline including:
1. Onset time (when effects begin)
2. Peak effects (timing and intensity)
3. Duration of effects
4. Mental effects (mood, cognition, creativity)
5. Physical effects (body sensation, pain relief, appetite)
6. Potential therapeutic benefits
7. Possible adverse effects to watch for
8. Factors that might alter these effects

Effects Description:"""
        )
        
        # Terpene Education Template
        self.templates[PromptCategory.TERPENE_EDUCATION] = PromptTemplate(
            input_variables=["terpene_name", "concentration", "context"],
            template="""Educate about the following cannabis terpene:

Terpene: {terpene_name}
Concentration: {concentration}
Context: {context}

Please explain:
1. What this terpene is and where else it's found in nature
2. Aroma and flavor profile it contributes
3. Potential therapeutic effects and benefits
4. How it may modify the effects of cannabinoids (entourage effect)
5. Optimal temperature for vaporization
6. Strains typically high in this terpene
7. Potential synergies with other terpenes
8. Any precautions or sensitivities to be aware of

Terpene Education:"""
        )
        
        # Dosage Guidance Template
        self.templates[PromptCategory.DOSAGE_GUIDANCE] = PromptTemplate(
            input_variables=["product_type", "potency", "experience_level", "desired_effects", "consumption_method"],
            template="""Provide dosage guidance for cannabis consumption:

Product Type: {product_type}
Potency: {potency}
Experience Level: {experience_level}
Desired Effects: {desired_effects}
Consumption Method: {consumption_method}

Following the "start low and go slow" principle, provide:
1. Recommended starting dose
2. How to titrate up safely
3. Time to wait between doses
4. Maximum recommended dose for this experience level
5. How to recognize optimal dosing
6. Signs of overconsumption and what to do
7. Factors that affect individual response
8. Record-keeping recommendations

Dosage Guidance:"""
        )
        
        # Legal Compliance Template
        self.templates[PromptCategory.LEGAL_COMPLIANCE] = PromptTemplate(
            input_variables=["jurisdiction", "question", "context"],
            template="""Provide legal compliance information for cannabis:

Jurisdiction: {jurisdiction}
Question: {question}
Context: {context}

DISCLAIMER: This is general information only. Laws change frequently. Always verify current regulations with official sources.

Address:
1. Current legal status in this jurisdiction
2. Age requirements and ID verification
3. Purchase limits and possession limits
4. Consumption restrictions (where it's legal/illegal)
5. Driving and impairment laws
6. Employment considerations
7. Travel restrictions
8. Medical vs recreational distinctions

Legal Information:"""
        )
        
        # Consumption Methods Template
        self.templates[PromptCategory.CONSUMPTION_METHODS] = PromptTemplate(
            input_variables=["method", "experience_level", "health_considerations"],
            template="""Explain this cannabis consumption method:

Method: {method}
Experience Level: {experience_level}
Health Considerations: {health_considerations}

Provide comprehensive information about:
1. How this consumption method works
2. Onset time and duration of effects
3. Bioavailability and efficiency
4. Pros and cons compared to other methods
5. Required equipment or preparation
6. Best practices for this method
7. Health considerations and harm reduction
8. Ideal products for this consumption method

Consumption Method Guide:"""
        )
        
        # Growing Advice Template
        self.templates[PromptCategory.GROWING_ADVICE] = PromptTemplate(
            input_variables=["strain", "growing_environment", "experience_level", "specific_question"],
            template="""Provide cannabis cultivation advice:

Strain: {strain}
Growing Environment: {growing_environment}
Experience Level: {experience_level}
Specific Question: {specific_question}

Note: Only provide advice for legal home cultivation in permitted jurisdictions.

Address:
1. Optimal growing conditions for this strain
2. Nutrient requirements and feeding schedule
3. Common issues and how to prevent them
4. Harvest timing and indicators
5. Curing and storage best practices
6. Yield expectations
7. Equipment recommendations for this setup
8. Organic vs synthetic approaches

Growing Advice:"""
        )
        
        # General Education Template
        self.templates[PromptCategory.GENERAL_EDUCATION] = PromptTemplate(
            input_variables=["topic", "audience_level"],
            template="""Provide educational information about cannabis:

Topic: {topic}
Audience Knowledge Level: {audience_level}

Create an informative response that:
1. Explains the topic clearly and accurately
2. Uses appropriate terminology for the audience level
3. Includes relevant scientific information
4. Addresses common misconceptions
5. Provides practical applications
6. Cites general scientific consensus
7. Maintains objectivity and balance
8. Suggests areas for further learning

Educational Content:"""
        )
    
    def _load_system_prompts(self):
        """Load system prompts for different scenarios"""
        
        self.system_prompts["budtender"] = """You are an expert cannabis budtender with deep knowledge of:
- Cannabis strains, cannabinoids, and terpenes
- Medical and recreational use cases
- Product types and consumption methods
- Legal compliance and safety
- Customer service and education

Your approach is:
- Professional yet friendly
- Educational and informative
- Safety-conscious
- Non-judgmental
- Compliant with all regulations

Always prioritize customer safety and legal compliance. Never provide medical advice beyond general education."""
        
        self.system_prompts["medical_consultant"] = """You are a cannabis wellness consultant specializing in therapeutic applications.

Your expertise includes:
- Cannabinoid pharmacology and the endocannabinoid system
- Terpene profiles and entourage effects
- Drug interactions and contraindications
- Dosing strategies and titration
- Various medical conditions and symptom management

Important guidelines:
- Always include disclaimers about consulting healthcare providers
- Never diagnose conditions or replace medical advice
- Focus on education and harm reduction
- Emphasize the importance of start low, go slow
- Consider individual variability in response"""
        
        self.system_prompts["educator"] = """You are a cannabis educator focused on providing accurate, science-based information.

Your role involves:
- Explaining complex concepts in accessible ways
- Addressing myths and misconceptions
- Providing balanced, objective information
- Citing scientific consensus when available
- Promoting responsible use and harm reduction

Maintain a neutral, educational tone while being engaging and informative."""
        
        self.system_prompts["compliance_officer"] = """You are a cannabis compliance expert with comprehensive knowledge of regulations.

Your expertise covers:
- Federal, state, and local cannabis laws
- Licensing and regulatory requirements
- Age verification and ID checking
- Product testing and labeling requirements
- Advertising and marketing restrictions
- Tax compliance
- Security and tracking requirements

Always include disclaimers about law changes and the need to verify current regulations."""
    
    def get_prompt(
        self,
        category: PromptCategory,
        **kwargs
    ) -> str:
        """
        Get a formatted prompt for a specific category
        
        Args:
            category: The prompt category
            **kwargs: Variables to fill in the template
        
        Returns:
            Formatted prompt string
        """
        
        if category not in self.templates:
            raise ValueError(f"Unknown prompt category: {category}")
        
        template = self.templates[category]
        
        # Validate required variables
        missing = set(template.input_variables) - set(kwargs.keys())
        if missing:
            raise ValueError(f"Missing required variables: {missing}")
        
        return template.format(**kwargs)
    
    def get_system_prompt(self, role: str) -> str:
        """
        Get a system prompt for a specific role
        
        Args:
            role: The role (budtender, medical_consultant, educator, compliance_officer)
        
        Returns:
            System prompt string
        """
        
        return self.system_prompts.get(
            role,
            self.system_prompts["budtender"]  # Default to budtender
        )
    
    def create_few_shot_prompt(
        self,
        category: PromptCategory,
        examples: List[Dict[str, str]],
        example_selector: Optional[Any] = None
    ) -> FewShotPromptTemplate:
        """
        Create a few-shot prompt template with examples
        
        Args:
            category: The prompt category
            examples: List of example input-output pairs
            example_selector: Optional semantic similarity selector
        
        Returns:
            FewShotPromptTemplate
        """
        
        if category not in self.templates:
            raise ValueError(f"Unknown prompt category: {category}")
        
        base_template = self.templates[category]
        
        # Create example template
        example_template = PromptTemplate(
            input_variables=base_template.input_variables + ["output"],
            template=base_template.template + "\n{output}"
        )
        
        # Create few-shot template
        if example_selector:
            few_shot_template = FewShotPromptTemplate(
                example_selector=example_selector,
                example_prompt=example_template,
                suffix=base_template.template,
                input_variables=base_template.input_variables
            )
        else:
            few_shot_template = FewShotPromptTemplate(
                examples=examples,
                example_prompt=example_template,
                suffix=base_template.template,
                input_variables=base_template.input_variables
            )
        
        self.few_shot_templates[category] = few_shot_template
        return few_shot_template
    
    def create_chat_prompt(
        self,
        system_role: str,
        user_message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ChatPromptTemplate:
        """
        Create a chat prompt with system and user messages
        
        Args:
            system_role: The system role to use
            user_message: The user's message
            context: Optional context to include
        
        Returns:
            ChatPromptTemplate
        """
        
        system_prompt = self.get_system_prompt(system_role)
        
        if context:
            context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])
            system_prompt += f"\n\nContext:\n{context_str}"
        
        chat_template = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(system_prompt),
            HumanMessagePromptTemplate.from_template("{user_message}")
        ])
        
        return chat_template
    
    def get_cannabis_examples(self) -> Dict[PromptCategory, List[Dict[str, str]]]:
        """
        Get example inputs and outputs for different categories
        
        Returns:
            Dictionary of examples by category
        """
        
        examples = {
            PromptCategory.PRODUCT_RECOMMENDATION: [
                {
                    "customer_profile": "New user, 35 years old, anxious about trying cannabis",
                    "preferences": "Wants relaxation without feeling 'high'",
                    "medical_conditions": "Mild anxiety, occasional insomnia",
                    "context": "Evening use at home",
                    "available_products": "Various CBD dominant strains, 1:1 ratios, CBD oils",
                    "output": "I recommend starting with a high-CBD, low-THC product like a 20:1 CBD:THC ratio tincture. Begin with 5-10mg CBD in the evening. This will provide relaxation and potential anxiety relief without intoxicating effects. The oil format allows precise dosing and gradual onset, perfect for beginners. After a week, you might try a 4:1 CBD:THC strain for enhanced relaxation and sleep support."
                },
                {
                    "customer_profile": "Experienced user, medical patient",
                    "preferences": "Pain relief, maintains functionality",
                    "medical_conditions": "Chronic back pain, arthritis",
                    "context": "Daytime use, needs to work",
                    "available_products": "Sativa strains, balanced hybrids, topicals",
                    "output": "For daytime pain management while maintaining functionality, I suggest a balanced hybrid with moderate THC (12-15%) and presence of CBD (2-3%). Look for strains high in limonene and pinene terpenes for focus and anti-inflammatory effects. Supplement with a CBD:THC topical cream for localized relief. Start with 2.5-5mg THC and adjust based on your tolerance and pain levels."
                }
            ],
            
            PromptCategory.STRAIN_INFORMATION: [
                {
                    "strain_name": "Blue Dream",
                    "category": "Sativa-dominant hybrid",
                    "genetics": "Blueberry x Haze",
                    "thc_content": "17-24",
                    "cbd_content": "0.1-0.2",
                    "terpenes": "Myrcene, Pinene, Caryophyllene",
                    "output": "Blue Dream is a legendary sativa-dominant hybrid offering balanced full-body relaxation with gentle cerebral invigoration. Effects include uplifted mood, creativity, and mild euphoria without heavy sedation. Medical users appreciate its effectiveness for depression, chronic pain, and nausea. The high myrcene content provides relaxation while pinene maintains alertness. Best for daytime use or creative activities. Beginners should start with small doses due to potentially high THC. Flavor profile features sweet berry notes from its Blueberry parent with earthy undertones."
                }
            ],
            
            PromptCategory.DOSAGE_GUIDANCE: [
                {
                    "product_type": "Cannabis edibles (gummies)",
                    "potency": "10mg THC per gummy",
                    "experience_level": "Beginner",
                    "desired_effects": "Mild relaxation, social comfort",
                    "consumption_method": "Oral ingestion",
                    "output": "For beginners with edibles, start with 2.5mg THC (1/4 of a gummy). Effects begin in 30-120 minutes and last 4-8 hours. Wait at least 2 hours before considering another dose. The delayed onset is due to liver metabolism. For your goals, 2.5-5mg should provide mild relaxation without overwhelming effects. Keep a journal noting dose, time, and effects. Never drive or operate machinery. Have CBD on hand to counteract if you feel too high. Stay hydrated and have snacks available."
                }
            ]
        }
        
        return examples
    
    def enhance_prompt_with_context(
        self,
        base_prompt: str,
        conversation_history: List[Dict[str, str]],
        user_preferences: Dict[str, Any],
        regulatory_context: Dict[str, str]
    ) -> str:
        """
        Enhance a prompt with additional context
        
        Args:
            base_prompt: The base prompt to enhance
            conversation_history: Previous conversation turns
            user_preferences: User's stated preferences
            regulatory_context: Legal/regulatory information
        
        Returns:
            Enhanced prompt string
        """
        
        enhanced = base_prompt
        
        # Add conversation history if available
        if conversation_history:
            history_str = "\n".join([
                f"User: {turn['user']}\nAssistant: {turn['assistant']}"
                for turn in conversation_history[-3:]  # Last 3 turns
            ])
            enhanced = f"Previous conversation:\n{history_str}\n\n{enhanced}"
        
        # Add user preferences
        if user_preferences:
            pref_str = "\n".join([
                f"- {key}: {value}"
                for key, value in user_preferences.items()
            ])
            enhanced = f"User preferences:\n{pref_str}\n\n{enhanced}"
        
        # Add regulatory context
        if regulatory_context:
            reg_str = "\n".join([
                f"- {key}: {value}"
                for key, value in regulatory_context.items()
            ])
            enhanced = f"Legal context:\n{reg_str}\n\nEnsure all recommendations comply with these regulations.\n\n{enhanced}"
        
        return enhanced
    
    def get_prompt_metadata(self, category: PromptCategory) -> Dict[str, Any]:
        """
        Get metadata about a prompt category
        
        Args:
            category: The prompt category
        
        Returns:
            Metadata dictionary
        """
        
        if category not in self.templates:
            return {}
        
        template = self.templates[category]
        
        return {
            "category": category.value,
            "input_variables": template.input_variables,
            "description": self._get_category_description(category),
            "compliance_level": self._get_compliance_level(category),
            "expertise_required": self._get_expertise_level(category)
        }
    
    def _get_category_description(self, category: PromptCategory) -> str:
        """Get description for a prompt category"""
        
        descriptions = {
            PromptCategory.PRODUCT_RECOMMENDATION: "Personalized product recommendations based on user needs",
            PromptCategory.STRAIN_INFORMATION: "Detailed information about specific cannabis strains",
            PromptCategory.MEDICAL_CONSULTATION: "Medical cannabis guidance and therapeutic applications",
            PromptCategory.EFFECTS_DESCRIPTION: "Expected effects and timeline for cannabis products",
            PromptCategory.TERPENE_EDUCATION: "Educational content about terpenes and their effects",
            PromptCategory.DOSAGE_GUIDANCE: "Safe dosing recommendations and titration strategies",
            PromptCategory.LEGAL_COMPLIANCE: "Legal and regulatory compliance information",
            PromptCategory.CONSUMPTION_METHODS: "Information about different consumption methods",
            PromptCategory.GROWING_ADVICE: "Cannabis cultivation tips and troubleshooting",
            PromptCategory.GENERAL_EDUCATION: "General cannabis education and information"
        }
        
        return descriptions.get(category, "Cannabis-related prompt")
    
    def _get_compliance_level(self, category: PromptCategory) -> str:
        """Get compliance level for a category"""
        
        high_compliance = [
            PromptCategory.MEDICAL_CONSULTATION,
            PromptCategory.LEGAL_COMPLIANCE,
            PromptCategory.DOSAGE_GUIDANCE
        ]
        
        if category in high_compliance:
            return "high"
        return "standard"
    
    def _get_expertise_level(self, category: PromptCategory) -> str:
        """Get required expertise level for a category"""
        
        expert_categories = [
            PromptCategory.MEDICAL_CONSULTATION,
            PromptCategory.GROWING_ADVICE,
            PromptCategory.TERPENE_EDUCATION
        ]
        
        if category in expert_categories:
            return "expert"
        return "intermediate"

# Singleton instance
_prompt_manager: Optional[CannabisPromptManager] = None

def get_prompt_manager() -> CannabisPromptManager:
    """Get singleton prompt manager instance"""
    global _prompt_manager
    if _prompt_manager is None:
        _prompt_manager = CannabisPromptManager()
    return _prompt_manager