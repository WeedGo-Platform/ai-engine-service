#!/usr/bin/env python3
"""
Sales Conversation Engine
Implements intelligent budtender that guides customers to purchase decisions
Uses SPIN selling methodology adapted for cannabis retail
"""

import json
import logging
import re
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from datetime import datetime
import asyncio
import psycopg2
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

class ConversationStage(Enum):
    """Sales funnel stages"""
    GREETING = "greeting"
    QUALIFICATION = "qualification"  # Understand needs
    RECOMMENDATION = "recommendation"  # Present solutions
    OBJECTION_HANDLING = "objection_handling"  # Address concerns
    CLOSING = "closing"  # Guide to purchase
    POST_SALE = "post_sale"  # Upsell/cross-sell

class CustomerIntent(Enum):
    """Detected customer intents"""
    # Purchase intents (high value)
    SEEKING_RELIEF = "seeking_relief"  # "I need help with..."
    SPECIFIC_EFFECT = "specific_effect"  # "Something for energy"
    REORDER = "reorder"  # "I want the same as last time"
    RECOMMENDATION = "recommendation"  # "What do you recommend?"
    PRODUCT_REQUEST = "product_request"  # "3 joint sativa under $10"
    
    # Information intents (medium value)
    PRODUCT_QUESTION = "product_question"  # "Tell me about..."
    COMPARISON = "comparison"  # "What's the difference..."
    EDUCATION = "education"  # "What is CBD?"
    
    # Browsing intents (low value)
    JUST_LOOKING = "just_looking"  # "Just browsing"
    PRICE_CHECK = "price_check"  # "How much is..."
    
    # Objections (handle carefully)
    PRICE_OBJECTION = "price_objection"  # "Too expensive"
    EFFECT_CONCERN = "effect_concern"  # "Will this make me paranoid?"
    INEXPERIENCED = "inexperienced"  # "I'm new to this"

@dataclass
class CustomerProfile:
    """Customer context for personalization"""
    customer_id: str
    experience_level: str = "unknown"  # beginner, intermediate, experienced
    budget_range: Tuple[float, float] = (20, 100)
    preferred_effects: List[str] = field(default_factory=list)
    avoided_effects: List[str] = field(default_factory=list)
    medical_conditions: List[str] = field(default_factory=list)
    consumption_method: str = "any"  # flower, vape, edible, oil
    strain_preference: str = "any"  # sativa, indica, hybrid, any
    time_of_use: str = "anytime"  # morning, daytime, evening, night
    purchase_history: List[Dict] = field(default_factory=list)
    cart_items: List[Dict] = field(default_factory=list)
    cart_value: float = 0.0
    conversation_stage: ConversationStage = ConversationStage.GREETING
    detected_intents: List[CustomerIntent] = field(default_factory=list)

class SalesConversationEngine:
    """Orchestrates sales-focused conversations"""
    
    # Intent patterns for detection
    INTENT_PATTERNS = {
        CustomerIntent.SEEKING_RELIEF: [
            r"help with (.*)",
            r"suffering from (.*)",
            r"dealing with (.*)",
            r"need relief",
            r"looking for something for (.*)"
        ],
        CustomerIntent.SPECIFIC_EFFECT: [
            r"(energy|sleep|relax|focus|creative|appetite)",
            r"want to feel (.*)",
            r"need to be (.*)",
            r"something (uplifting|calming|energizing)"
        ],
        CustomerIntent.PRODUCT_REQUEST: [
            r"(sativa|indica|hybrid)",
            r"(joint|joints|pre-roll|pre-rolls|flower|bud|vape|edible)",
            r"under \$?\d+",
            r"less than \$?\d+",
            r"\d+ (joint|joints|gram|grams|eighth)",
            r"looking for .*(sativa|indica|hybrid)",
            r"want .*(joint|pre-roll|flower|vape|edible)",
            r"need .*(sativa|indica|hybrid)"
        ],
        CustomerIntent.PRICE_OBJECTION: [
            r"expensive",
            r"cheaper",
            r"budget",
            r"can't afford",
            r"price"
        ],
        CustomerIntent.INEXPERIENCED: [
            r"first time",
            r"never tried",
            r"new to",
            r"beginner",
            r"don't know much"
        ]
    }
    
    # Sales responses by stage
    STAGE_RESPONSES = {
        ConversationStage.GREETING: {
            "opener": "Welcome! I'm here to help you find the perfect cannabis products for your needs. What brings you in today?",
            "returning": "Welcome back! Great to see you again. Looking for something similar to last time, or want to try something new?",
            "medical": "I understand you're looking for relief. I can help you find products that may help with your specific needs. What are you hoping to address?"
        },
        ConversationStage.QUALIFICATION: {
            "experience": "To help me find the best products for you, could you tell me about your experience with cannabis?",
            "effects": "What kind of effects are you looking for? For example, relaxation, energy, pain relief, or better sleep?",
            "consumption": "Do you have a preference for how you consume? We have flower, vapes, edibles, and oils.",
            "budget": "What price range are you comfortable with today?",
            "timeline": "When do you typically use cannabis? Morning, evening, or throughout the day?"
        },
        ConversationStage.RECOMMENDATION: {
            "intro": "Based on what you've told me, I have some perfect recommendations for you:",
            "feature_benefit": "This {product} contains {terpenes}, which are known for {effects}. Many customers use it for {use_case}.",
            "social_proof": "This is one of our most popular products for {intent}. Customers love it because {reason}.",
            "scarcity": "This one is flying off the shelves - we only have {quantity} left in stock.",
            "bundle": "If you get this with {companion_product}, you'll save {discount}% and have everything you need."
        },
        ConversationStage.OBJECTION_HANDLING: {
            "price": "I understand price is important. This product gives you {value_prop}. We also have {alternative} that might fit your budget better.",
            "effect_concern": "That's a valid concern. We can start with a lower THC option or try a CBD-balanced product to minimize any unwanted effects.",
            "inexperience": "No worries! I'll recommend something gentle and beginner-friendly. We'll start low and go slow.",
            "quality": "All our products are lab-tested and regulated by Health Canada. You're getting safe, consistent quality."
        },
        ConversationStage.CLOSING: {
            "assumptive": "Great choice! Should I add the {product} to your order?",
            "alternative": "Would you prefer the {option1} or the {option2}?",
            "urgency": "This promotion ends today - shall we lock in these savings?",
            "trial": "How about we start with a smaller quantity so you can try it first?"
        }
    }
    
    def __init__(self, db_config: Dict):
        self.db_config = db_config
        self.conn = None
        self.customers = {}  # Active customer profiles
        
    def connect_db(self):
        """Connect to database"""
        self.conn = psycopg2.connect(**self.db_config)
        
    async def process_message(self, customer_id: str, message: str) -> Dict:
        """Process customer message and generate sales response"""
        
        # Get or create customer profile
        profile = self._get_customer_profile(customer_id)
        
        # Update profile from message content
        self._update_profile_from_message(profile, message)
        
        # Detect intent from message
        intents = self._detect_intent(message)
        profile.detected_intents.extend(intents)
        
        # Determine conversation stage
        new_stage = self._determine_stage(profile, intents)
        if new_stage != profile.conversation_stage:
            profile.conversation_stage = new_stage
            logger.info(f"Customer {customer_id} moved to stage: {new_stage.value}")
        
        # Generate appropriate response
        response = await self._generate_response(profile, message, intents)
        
        # Track metrics
        self._track_conversation_metrics(profile, intents, response)
        
        return response
    
    def _detect_intent(self, message: str) -> List[CustomerIntent]:
        """Detect customer intent from message"""
        detected = []
        message_lower = message.lower()
        
        for intent, patterns in self.INTENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    detected.append(intent)
                    break
        
        # Default intent if nothing detected
        if not detected and "?" in message:
            detected.append(CustomerIntent.PRODUCT_QUESTION)
        elif not detected:
            detected.append(CustomerIntent.JUST_LOOKING)
            
        return detected
    
    def _update_profile_from_message(self, profile: CustomerProfile, message: str):
        """Update customer profile based on message content"""
        message_lower = message.lower()
        
        # Detect experience level
        if any(word in message_lower for word in ["beginner", "first", "new"]):
            profile.experience_level = "beginner"
        elif any(word in message_lower for word in ["tried", "some experience", "few times"]):
            profile.experience_level = "intermediate"
        elif any(word in message_lower for word in ["regular", "experienced", "often"]):
            profile.experience_level = "experienced"
        
        # Detect consumption method
        if "flower" in message_lower or "smoking" in message_lower:
            profile.consumption_method = "flower"
        elif "joint" in message_lower or "pre-roll" in message_lower or "preroll" in message_lower:
            profile.consumption_method = "flower"  # joints are flower products
        elif "vape" in message_lower:
            profile.consumption_method = "vape"
        elif "edible" in message_lower:
            profile.consumption_method = "edible"
        elif "oil" in message_lower or "tincture" in message_lower:
            profile.consumption_method = "oil"
        
        # Detect strain preference
        if "sativa" in message_lower:
            profile.strain_preference = "sativa"
        elif "indica" in message_lower:
            profile.strain_preference = "indica"
        elif "hybrid" in message_lower:
            profile.strain_preference = "hybrid"
        
        # Detect effects preferences
        effect_keywords = {
            "sleep": ["sleep", "insomnia", "rest"],
            "energy": ["energy", "energizing", "daytime", "sativa"],
            "pain": ["pain", "ache", "inflammation"],
            "anxiety": ["anxiety", "stress", "calm"],
            "focus": ["focus", "concentration", "productive"],
            "relax": ["relax", "chill", "unwind", "indica"]
        }
        
        for effect, keywords in effect_keywords.items():
            if any(word in message_lower for word in keywords):
                if effect not in profile.preferred_effects:
                    profile.preferred_effects.append(effect)
        
        # Detect budget - now handles single values and ranges
        # Try single value patterns first
        single_budget = re.search(r'under \$?(\d+)|less than \$?(\d+)', message_lower)
        if single_budget:
            value = float(single_budget.group(1) or single_budget.group(2))
            profile.budget_range = (0, value)
        else:
            # Try range patterns
            budget_match = re.search(r'\$?(\d+)[-\s](?:to\s)?(\d+)', message_lower)
            if budget_match:
                profile.budget_range = (float(budget_match.group(1)), float(budget_match.group(2)))
    
    def _determine_stage(self, profile: CustomerProfile, intents: List[CustomerIntent]) -> ConversationStage:
        """Determine appropriate conversation stage based on profile and intents"""
        
        # Direct product requests skip straight to recommendations
        if CustomerIntent.PRODUCT_REQUEST in intents:
            return ConversationStage.RECOMMENDATION
        
        # High-value intents move to recommendation quickly
        if any(intent in [CustomerIntent.SEEKING_RELIEF, CustomerIntent.SPECIFIC_EFFECT] 
               for intent in intents):
            if profile.conversation_stage == ConversationStage.GREETING:
                return ConversationStage.QUALIFICATION
            else:
                return ConversationStage.RECOMMENDATION
        
        # Objections need handling
        if any(intent in [CustomerIntent.PRICE_OBJECTION, CustomerIntent.EFFECT_CONCERN]
               for intent in intents):
            return ConversationStage.OBJECTION_HANDLING
        
        # Natural progression
        if profile.conversation_stage == ConversationStage.GREETING:
            return ConversationStage.QUALIFICATION
        elif profile.conversation_stage == ConversationStage.QUALIFICATION:
            if self._has_enough_info(profile):
                return ConversationStage.RECOMMENDATION
        elif profile.conversation_stage == ConversationStage.RECOMMENDATION:
            if profile.cart_value > 0:
                return ConversationStage.CLOSING
                
        return profile.conversation_stage
    
    def _has_enough_info(self, profile: CustomerProfile) -> bool:
        """Check if we have enough info to make recommendations"""
        return (len(profile.preferred_effects) > 0 or 
                len(profile.medical_conditions) > 0 or
                profile.experience_level != "unknown")
    
    async def _generate_response(self, profile: CustomerProfile, message: str, intents: List[CustomerIntent]) -> Dict:
        """Generate sales-optimized response"""
        
        response = {
            "message": "",
            "products": [],
            "quick_replies": [],
            "stage": profile.conversation_stage.value,
            "confidence": 0.0
        }
        
        # Get stage-appropriate base response
        stage_responses = self.STAGE_RESPONSES[profile.conversation_stage]
        
        if profile.conversation_stage == ConversationStage.GREETING:
            if profile.purchase_history:
                response["message"] = stage_responses["returning"]
            elif CustomerIntent.SEEKING_RELIEF in intents:
                response["message"] = stage_responses["medical"]
            else:
                response["message"] = stage_responses["opener"]
                
            response["quick_replies"] = [
                "I need help sleeping",
                "Looking for energy",
                "Pain relief",
                "Just browsing"
            ]
            
        elif profile.conversation_stage == ConversationStage.QUALIFICATION:
            # Ask qualifying questions
            if profile.experience_level == "unknown":
                response["message"] = stage_responses["experience"]
                response["quick_replies"] = ["Beginner", "Some experience", "Regular user"]
            elif not profile.preferred_effects:
                response["message"] = stage_responses["effects"]
                response["quick_replies"] = ["Relaxation", "Energy", "Pain relief", "Creativity", "Sleep"]
            elif profile.consumption_method == "any":
                response["message"] = stage_responses["consumption"]
                response["quick_replies"] = ["Flower", "Vapes", "Edibles", "Oils", "No preference"]
            else:
                # Move to recommendation
                profile.conversation_stage = ConversationStage.RECOMMENDATION
                return await self._generate_response(profile, message, intents)
                
        elif profile.conversation_stage == ConversationStage.RECOMMENDATION:
            # Get personalized recommendations
            products = await self._get_recommendations(profile)
            
            if products:
                response["message"] = stage_responses["intro"]
                response["products"] = products[:3]  # Top 3 recommendations
                
                # Add persuasive product descriptions
                for product in response["products"]:
                    product["pitch"] = self._create_product_pitch(product, profile)
                    
                response["quick_replies"] = [
                    f"Tell me more about {products[0]['name']}",
                    "Show me something cheaper",
                    "Add to cart",
                    "I have concerns"
                ]
            else:
                response["message"] = "Let me find some alternatives for you..."
                
        elif profile.conversation_stage == ConversationStage.OBJECTION_HANDLING:
            # Handle specific objections
            if CustomerIntent.PRICE_OBJECTION in intents:
                response["message"] = stage_responses["price"]
                # Get budget alternatives
                products = await self._get_budget_alternatives(profile)
                response["products"] = products[:2]
            elif CustomerIntent.EFFECT_CONCERN in intents or "groggy" in message.lower():
                response["message"] = stage_responses["effect_concern"]
                # Get gentler options
                products = await self._get_gentle_options(profile)
                response["products"] = products[:2]
            elif CustomerIntent.INEXPERIENCED in intents:
                response["message"] = stage_responses["inexperience"]
                products = await self._get_beginner_products(profile)
                response["products"] = products[:2]
            else:
                # Default objection handling
                response["message"] = "I understand your concern. Let me show you some alternatives that might work better for you."
                products = await self._get_gentle_options(profile)
                response["products"] = products[:2]
                
        elif profile.conversation_stage == ConversationStage.CLOSING:
            # Close the sale
            response["message"] = stage_responses["assumptive"].format(
                product=profile.cart_items[0]["name"] if profile.cart_items else "your selection"
            )
            response["quick_replies"] = [
                "Yes, add to cart",
                "I'll think about it",
                "Show me similar options"
            ]
            
            # Add urgency if applicable
            if self._check_promotion_available():
                response["message"] += " Plus, you'll get 10% off if you order in the next hour!"
        
        response["confidence"] = self._calculate_confidence(profile)
        return response
    
    async def _get_recommendations(self, profile: CustomerProfile) -> List[Dict]:
        """Get personalized product recommendations"""
        cur = self.conn.cursor()
        
        # Map effects to intents
        intent_map = {
            "sleep": ["sleep", "relax", "insomnia"],
            "energy": ["energy", "focus", "motivation"],
            "pain": ["pain", "inflammation", "aches"],
            "anxiety": ["anxiety", "stress", "calm"]
        }
        
        # Find matching intent
        matched_intent = None
        for intent, keywords in intent_map.items():
            if any(effect in keywords for effect in profile.preferred_effects):
                matched_intent = intent
                break
        
        if not matched_intent:
            matched_intent = "anxiety"  # Default safe option
        
        # Build query with optional strain preference
        base_query = """
            SELECT p.id, p.product_name, p.brand, p.unit_price, 
                   p.thc_max_percent, p.cbd_max_percent, p.plant_type,
                   pes.score, pes.reasoning
            FROM products p
            JOIN product_effect_scores pes ON p.id = pes.product_id
            WHERE pes.intent = %s
                AND p.category = %s
                AND p.unit_price BETWEEN %s AND %s
        """
        
        # Add strain filter if specified
        params = [matched_intent]
        
        # Map consumption method to category
        category_map = {
            "flower": "Flower",
            "vape": "Vapes", 
            "edible": "Edibles",
            "oil": "Extracts",
            "any": "Flower"  # Default
        }
        category = category_map.get(profile.consumption_method, "Flower")
        params.append(category)
        params.extend([profile.budget_range[0], profile.budget_range[1]])
        
        # Add strain preference if specified
        if profile.strain_preference and profile.strain_preference != "any":
            base_query += " AND LOWER(p.plant_type) LIKE %s"
            params.append(f"%{profile.strain_preference.lower()}%")
        
        base_query += " ORDER BY pes.score DESC LIMIT 5"
        
        cur.execute(base_query, params)
        
        products = []
        for row in cur.fetchall():
            products.append({
                "id": row[0],
                "name": row[1],
                "brand": row[2],
                "price": float(row[3]) if row[3] else 0,
                "thc": row[4],
                "cbd": row[5],
                "plant_type": row[6],
                "score": row[7],
                "reasoning": row[8]
            })
            
        return products
    
    async def _get_budget_alternatives(self, profile: CustomerProfile) -> List[Dict]:
        """Get budget-friendly alternatives"""
        profile.budget_range = (10, 30)  # Lower budget
        return await self._get_recommendations(profile)
    
    async def _get_gentle_options(self, profile: CustomerProfile) -> List[Dict]:
        """Get gentler, CBD-balanced options"""
        cur = self.conn.cursor()
        
        query = """
            SELECT id, product_name, brand, unit_price,
                   thc_max_percent, cbd_max_percent
            FROM products
            WHERE cbd_max_percent > 5
                OR thc_max_percent < 15
            ORDER BY cbd_max_percent DESC
            LIMIT 3
        """
        
        cur.execute(query)
        products = []
        for row in cur.fetchall():
            products.append({
                "id": row[0],
                "name": row[1],
                "brand": row[2],
                "price": float(row[3]) if row[3] else 0,
                "thc": row[4],
                "cbd": row[5],
                "pitch": "Balanced CBD for a gentle experience"
            })
            
        return products
    
    async def _get_beginner_products(self, profile: CustomerProfile) -> List[Dict]:
        """Get beginner-friendly products"""
        cur = self.conn.cursor()
        
        query = """
            SELECT id, product_name, brand, unit_price,
                   thc_max_percent, cbd_max_percent
            FROM products
            WHERE thc_max_percent BETWEEN 5 AND 15
                AND category IN ('Flower', 'Edibles')
            ORDER BY (thc_max_percent + COALESCE(cbd_max_percent, 0)) ASC
            LIMIT 3
        """
        
        cur.execute(query)
        products = []
        for row in cur.fetchall():
            products.append({
                "id": row[0],
                "name": row[1],
                "brand": row[2],
                "price": float(row[3]) if row[3] else 0,
                "thc": row[4],
                "cbd": row[5],
                "pitch": "Perfect for beginners - start low and go slow"
            })
            
        return products
    
    def _create_product_pitch(self, product: Dict, profile: CustomerProfile) -> str:
        """Create persuasive product pitch"""
        pitches = []
        
        # Experience-based pitch
        if profile.experience_level == "beginner":
            if product["thc"] and product["thc"] < 15:
                pitches.append("Gentle potency perfect for beginners")
        elif profile.experience_level == "experienced":
            if product["thc"] and product["thc"] > 20:
                pitches.append("Premium potency for experienced users")
        
        # Effect-based pitch
        if "sleep" in profile.preferred_effects:
            pitches.append("Customers report excellent sleep quality")
        elif "energy" in profile.preferred_effects:
            pitches.append("Great for daytime productivity")
        elif "pain" in profile.preferred_effects:
            pitches.append("Popular choice for pain management")
        
        # Value pitch
        if product["price"] < 25:
            pitches.append("Excellent value - premium quality at this price")
        
        # Social proof
        if product.get("score", 0) > 80:
            pitches.append("One of our top-rated products for your needs")
        
        return ". ".join(pitches) if pitches else "High-quality product from a trusted brand"
    
    def _calculate_confidence(self, profile: CustomerProfile) -> float:
        """Calculate confidence in making a sale"""
        confidence = 0.3  # Base confidence
        
        # Stage progression adds confidence
        stage_scores = {
            ConversationStage.GREETING: 0.1,
            ConversationStage.QUALIFICATION: 0.2,
            ConversationStage.RECOMMENDATION: 0.3,
            ConversationStage.OBJECTION_HANDLING: 0.2,
            ConversationStage.CLOSING: 0.4
        }
        confidence += stage_scores.get(profile.conversation_stage, 0)
        
        # Customer engagement adds confidence  
        if profile.detected_intents:
            high_value_intents = [CustomerIntent.SEEKING_RELIEF, CustomerIntent.SPECIFIC_EFFECT, CustomerIntent.RECOMMENDATION]
            if any(intent in high_value_intents for intent in profile.detected_intents):
                confidence += 0.2
        
        # Information completeness
        if profile.experience_level != "unknown":
            confidence += 0.05
        if profile.preferred_effects:
            confidence += 0.05
        if profile.cart_value > 0:
            confidence += 0.1
            
        return min(confidence, 0.95)
    
    def _get_customer_profile(self, customer_id: str) -> CustomerProfile:
        """Get or create customer profile"""
        if customer_id not in self.customers:
            self.customers[customer_id] = CustomerProfile(customer_id=customer_id)
        return self.customers[customer_id]
    
    def _check_promotion_available(self) -> bool:
        """Check if any promotions are available"""
        # Could check database for active promotions
        return datetime.now().hour in [16, 17, 18, 19, 20]  # Happy hour
    
    def _track_conversation_metrics(self, profile: CustomerProfile, intents: List[CustomerIntent], response: Dict):
        """Track conversation metrics for optimization"""
        # Log to database for analysis
        if self.conn:
            cur = self.conn.cursor()
            cur.execute("""
                INSERT INTO conversation_metrics 
                (customer_id, stage, intents, products_shown, confidence, timestamp)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                profile.customer_id,
                profile.conversation_stage.value,
                json.dumps([i.value for i in intents]),
                len(response.get("products", [])),
                response.get("confidence", 0),
                datetime.now()
            ))
            self.conn.commit()

# Integration test
async def test_sales_engine():
    """Test the sales conversation engine"""
    import os
    
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 5434)),
        'database': os.getenv('DB_NAME', 'ai_engine'),
        'user': os.getenv('DB_USER', 'weedgo'),
        'password': os.getenv('DB_PASSWORD', 'weedgo123')
    }
    
    engine = SalesConversationEngine(db_config)
    engine.connect_db()
    
    # Create conversation metrics table
    cur = engine.conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS conversation_metrics (
            id SERIAL PRIMARY KEY,
            customer_id VARCHAR(255),
            stage VARCHAR(50),
            intents JSONB,
            products_shown INTEGER,
            confidence FLOAT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    engine.conn.commit()
    
    # Simulate customer conversation
    customer_id = "test_customer_123"
    
    print("\n=== Sales Conversation Simulation ===\n")
    
    # Test conversation flow
    test_messages = [
        "Hi, I'm looking for something to help me sleep",
        "I've tried cannabis a few times before",
        "I prefer smoking flower",
        "My budget is around $40-60",
        "Will this make me groggy in the morning?",
        "Ok, I'll take the first one you recommended"
    ]
    
    for message in test_messages:
        print(f"Customer: {message}")
        response = await engine.process_message(customer_id, message)
        print(f"Budtender: {response['message']}")
        
        if response.get('products'):
            print("\nRecommended products:")
            for product in response['products']:
                print(f"  - {product['name']} ({product['brand']}) - ${product['price']:.2f}")
                if product.get('pitch'):
                    print(f"    '{product['pitch']}'")
        
        if response.get('quick_replies'):
            print(f"Quick replies: {', '.join(response['quick_replies'])}")
        
        print(f"[Stage: {response['stage']}, Confidence: {response['confidence']:.2%}]\n")
        print("-" * 50 + "\n")
    
    print("Conversation complete!")
    engine.conn.close()

if __name__ == "__main__":
    asyncio.run(test_sales_engine())