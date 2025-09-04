#!/usr/bin/env python3
"""
Cannabis AI Training Script
Trains the AI with comprehensive cannabis-specific examples
"""

import asyncio
import aiohttp
import json
from typing import List, Dict, Any
from datetime import datetime

# API Configuration
API_BASE_URL = "http://localhost:8080/api/v1"

class CannabisAITrainer:
    """Trains the AI with cannabis-specific knowledge"""
    
    def __init__(self):
        self.training_examples = []
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()
        
    def create_training_examples(self) -> List[Dict[str, Any]]:
        """Create comprehensive training examples for cannabis AI"""
        
        examples = []
        
        # 1. Greeting examples with budtender personality
        examples.extend([
            {
                "query": "hi",
                "context": {"first_visit": True},
                "expected_intent": "greeting",
                "expected_entities": {},
                "expected_products": [],
                "expected_response_qualities": [
                    "friendly_greeting",
                    "introduces_self_as_budtender",
                    "asks_how_to_help",
                    "welcoming_tone"
                ],
                "feedback_score": 0.95
            },
            {
                "query": "hello",
                "context": {"visit_count": 5},
                "expected_intent": "greeting",
                "expected_entities": {},
                "expected_products": [],
                "expected_response_qualities": [
                    "acknowledges_returning_customer",
                    "friendly_tone",
                    "offers_assistance"
                ],
                "feedback_score": 0.95
            }
        ])
        
        # 2. Cannabis slang understanding
        examples.extend([
            {
                "query": "got any fire?",
                "context": {},
                "expected_intent": "product_search",
                "expected_entities": {
                    "quality": "premium",
                    "potency": "high"
                },
                "expected_products": ["high_thc", "premium", "top_shelf"],
                "expected_response_qualities": [
                    "understands_fire_means_premium",
                    "shows_high_quality_products",
                    "mentions_potency"
                ],
                "feedback_score": 0.9
            },
            {
                "query": "show me some gas",
                "context": {},
                "expected_intent": "product_search",
                "expected_entities": {
                    "terpene_profile": "diesel",
                    "category": "flower"
                },
                "expected_products": ["diesel", "gas", "og_kush"],
                "expected_response_qualities": [
                    "understands_gas_terpene",
                    "mentions_diesel_strains",
                    "shows_flower_products"
                ],
                "feedback_score": 0.9
            },
            {
                "query": "need that sticky icky",
                "context": {},
                "expected_intent": "product_search",
                "expected_entities": {
                    "quality": "premium",
                    "texture": "sticky",
                    "category": "flower"
                },
                "expected_products": ["premium_flower", "high_resin"],
                "expected_response_qualities": [
                    "understands_sticky_icky",
                    "shows_resinous_flower",
                    "mentions_quality"
                ],
                "feedback_score": 0.9
            }
        ])
        
        # 3. Medical/effect-based queries
        examples.extend([
            {
                "query": "I need something for sleep",
                "context": {},
                "expected_intent": "product_search",
                "expected_entities": {
                    "effects": "sleep",
                    "strain_type": "indica"
                },
                "expected_products": ["indica", "sleep", "nighttime"],
                "expected_response_qualities": [
                    "recommends_indica",
                    "mentions_sleep_effects",
                    "suggests_relaxing_strains",
                    "educational_tone"
                ],
                "feedback_score": 0.95
            },
            {
                "query": "what helps with anxiety?",
                "context": {},
                "expected_intent": "product_search",
                "expected_entities": {
                    "medical_condition": "anxiety",
                    "cannabinoid_preference": "cbd"
                },
                "expected_products": ["cbd", "balanced", "calming"],
                "expected_response_qualities": [
                    "suggests_cbd_products",
                    "mentions_calming_effects",
                    "educational_about_cannabinoids",
                    "empathetic_tone"
                ],
                "feedback_score": 0.95
            },
            {
                "query": "need energy boost",
                "context": {},
                "expected_intent": "product_search",
                "expected_entities": {
                    "effects": "energy",
                    "strain_type": "sativa"
                },
                "expected_products": ["sativa", "energizing", "daytime"],
                "expected_response_qualities": [
                    "recommends_sativa",
                    "mentions_energizing_effects",
                    "suggests_daytime_strains"
                ],
                "feedback_score": 0.9
            }
        ])
        
        # 4. Specific product searches
        examples.extend([
            {
                "query": "show me pink kush",
                "context": {},
                "expected_intent": "product_search",
                "expected_entities": {
                    "product": "pink kush",
                    "strain_name": "pink kush"
                },
                "expected_products": ["pink_kush"],
                "expected_response_qualities": [
                    "finds_specific_strain",
                    "shows_pink_kush_products",
                    "mentions_strain_characteristics"
                ],
                "feedback_score": 0.95
            },
            {
                "query": "do you have shatter?",
                "context": {},
                "expected_intent": "product_search",
                "expected_entities": {
                    "category": "concentrates",
                    "sub_category": "shatter"
                },
                "expected_products": ["shatter", "concentrates"],
                "expected_response_qualities": [
                    "shows_shatter_products",
                    "mentions_concentrate_potency",
                    "educational_if_needed"
                ],
                "feedback_score": 0.95
            },
            {
                "query": "any edibles?",
                "context": {},
                "expected_intent": "product_search",
                "expected_entities": {
                    "category": "edibles"
                },
                "expected_products": ["edibles", "gummies", "chocolates"],
                "expected_response_qualities": [
                    "shows_edible_products",
                    "mentions_onset_time",
                    "dosage_guidance"
                ],
                "feedback_score": 0.9
            }
        ])
        
        # 5. Quantity understanding
        examples.extend([
            {
                "query": "gimme a half",
                "context": {},
                "expected_intent": "product_search",
                "expected_entities": {
                    "quantity": "14g",
                    "size": "half_ounce"
                },
                "expected_products": ["14g", "half_ounce"],
                "expected_response_qualities": [
                    "understands_half_means_14g",
                    "shows_14g_products"
                ],
                "feedback_score": 0.9
            },
            {
                "query": "need a quarter",
                "context": {},
                "expected_intent": "product_search",
                "expected_entities": {
                    "quantity": "7g",
                    "size": "quarter_ounce"
                },
                "expected_products": ["7g", "quarter"],
                "expected_response_qualities": [
                    "understands_quarter_means_7g",
                    "shows_7g_products"
                ],
                "feedback_score": 0.9
            },
            {
                "query": "got any eighths?",
                "context": {},
                "expected_intent": "product_search",
                "expected_entities": {
                    "quantity": "3.5g",
                    "size": "eighth"
                },
                "expected_products": ["3.5g", "eighth"],
                "expected_response_qualities": [
                    "understands_eighth_means_3.5g",
                    "shows_3.5g_products"
                ],
                "feedback_score": 0.9
            }
        ])
        
        # 6. New customer guidance
        examples.extend([
            {
                "query": "I'm new to this",
                "context": {"visit_count": 1},
                "expected_intent": "information_request",
                "expected_entities": {
                    "customer_type": "beginner"
                },
                "expected_products": ["beginner_friendly", "low_thc", "cbd"],
                "expected_response_qualities": [
                    "educational_tone",
                    "gentle_guidance",
                    "explains_basics",
                    "recommends_starter_products",
                    "no_overwhelming_info"
                ],
                "feedback_score": 0.95
            },
            {
                "query": "first time here",
                "context": {"first_visit": True},
                "expected_intent": "information_request",
                "expected_entities": {
                    "customer_type": "first_timer"
                },
                "expected_products": [],
                "expected_response_qualities": [
                    "welcoming_tone",
                    "asks_about_experience",
                    "offers_guidance",
                    "explains_process"
                ],
                "feedback_score": 0.95
            }
        ])
        
        # 7. Price-conscious queries
        examples.extend([
            {
                "query": "what's on sale?",
                "context": {},
                "expected_intent": "product_search",
                "expected_entities": {
                    "price_preference": "discount",
                    "looking_for": "deals"
                },
                "expected_products": ["sale_items", "discounted"],
                "expected_response_qualities": [
                    "shows_sale_products",
                    "mentions_discounts",
                    "value_focused"
                ],
                "feedback_score": 0.9
            },
            {
                "query": "cheapest ounce?",
                "context": {},
                "expected_intent": "product_search",
                "expected_entities": {
                    "quantity": "28g",
                    "price_preference": "budget"
                },
                "expected_products": ["28g", "ounce", "budget"],
                "expected_response_qualities": [
                    "shows_affordable_ounces",
                    "mentions_value",
                    "no_judgment"
                ],
                "feedback_score": 0.9
            }
        ])
        
        # 8. Terpene and flavor preferences
        examples.extend([
            {
                "query": "something fruity",
                "context": {},
                "expected_intent": "product_search",
                "expected_entities": {
                    "flavor_profile": "fruity",
                    "terpene_preference": "fruity"
                },
                "expected_products": ["berry", "citrus", "tropical"],
                "expected_response_qualities": [
                    "mentions_fruity_strains",
                    "describes_flavors",
                    "mentions_terpenes"
                ],
                "feedback_score": 0.9
            },
            {
                "query": "pine flavor strains",
                "context": {},
                "expected_intent": "product_search",
                "expected_entities": {
                    "flavor_profile": "pine",
                    "terpene": "pinene"
                },
                "expected_products": ["pine", "pinene", "jack_herer"],
                "expected_response_qualities": [
                    "mentions_pinene_terpene",
                    "shows_pine_flavored_strains",
                    "educational_about_terpenes"
                ],
                "feedback_score": 0.9
            }
        ])
        
        # 9. Consumption method preferences
        examples.extend([
            {
                "query": "I don't smoke",
                "context": {},
                "expected_intent": "product_search",
                "expected_entities": {
                    "consumption_method": "non_smoking",
                    "exclude_category": "flower"
                },
                "expected_products": ["edibles", "tinctures", "topicals"],
                "expected_response_qualities": [
                    "suggests_alternatives_to_smoking",
                    "shows_edibles_tinctures",
                    "understanding_tone"
                ],
                "feedback_score": 0.95
            },
            {
                "query": "vape carts?",
                "context": {},
                "expected_intent": "product_search",
                "expected_entities": {
                    "category": "vaporizers",
                    "product_type": "cartridge"
                },
                "expected_products": ["vape_cartridge", "510_thread"],
                "expected_response_qualities": [
                    "shows_vape_cartridges",
                    "mentions_strains_available",
                    "might_mention_battery"
                ],
                "feedback_score": 0.9
            }
        ])
        
        # 10. Complex multi-intent queries
        examples.extend([
            {
                "query": "I want something strong but not too expensive for tonight",
                "context": {},
                "expected_intent": "product_search",
                "expected_entities": {
                    "potency": "high",
                    "price_preference": "mid_range",
                    "time_of_use": "evening",
                    "strain_type": "indica"
                },
                "expected_products": ["indica", "high_thc", "evening", "mid_price"],
                "expected_response_qualities": [
                    "balances_potency_and_price",
                    "suggests_evening_strains",
                    "shows_good_value_options"
                ],
                "feedback_score": 0.9
            },
            {
                "query": "birthday gift for experienced smoker",
                "context": {},
                "expected_intent": "product_search",
                "expected_entities": {
                    "purpose": "gift",
                    "customer_type": "experienced",
                    "quality": "premium"
                },
                "expected_products": ["premium", "gift_worthy", "unique"],
                "expected_response_qualities": [
                    "suggests_premium_products",
                    "mentions_gift_options",
                    "special_occasion_tone"
                ],
                "feedback_score": 0.9
            }
        ])
        
        # 11. Sales conversation progression
        examples.extend([
            {
                "query": "tell me more about that one",
                "context": {
                    "products_shown": ["Pink Kush 3.5g"],
                    "stage": "product_exploration"
                },
                "expected_intent": "information_request",
                "expected_entities": {
                    "referring_to": "previous_product"
                },
                "expected_products": [],
                "expected_response_qualities": [
                    "provides_product_details",
                    "mentions_effects",
                    "describes_characteristics",
                    "builds_interest"
                ],
                "feedback_score": 0.9
            },
            {
                "query": "I'll take it",
                "context": {
                    "products_shown": ["Pink Kush 3.5g"],
                    "stage": "decision"
                },
                "expected_intent": "cart_action",
                "expected_entities": {
                    "action": "add_to_cart"
                },
                "expected_products": [],
                "expected_response_qualities": [
                    "confirms_addition",
                    "positive_reinforcement",
                    "might_suggest_complementary"
                ],
                "feedback_score": 0.95
            }
        ])
        
        return examples
    
    async def train_ai(self, examples: List[Dict[str, Any]]) -> Dict:
        """Send training examples to the AI"""
        
        url = f"{API_BASE_URL}/ai/train"
        
        # API expects just the list of examples
        async with self.session.post(url, json=examples) as response:
            if response.status == 200:
                return await response.json()
            else:
                return {"success": False, "error": f"HTTP {response.status}"}
    
    async def get_stats(self) -> Dict:
        """Get current AI learning statistics"""
        
        url = f"{API_BASE_URL}/ai/stats"
        
        async with self.session.get(url) as response:
            return await response.json()
    
    async def test_query(self, query: str, context: Dict = None) -> Dict:
        """Test a query against the trained AI"""
        
        url = f"{API_BASE_URL}/chat"
        
        payload = {
            "message": query,
            "customer_id": "test_customer",
            "session_id": "test_session",
            "context": context or {}
        }
        
        async with self.session.post(url, json=payload) as response:
            return await response.json()
    
    async def run_training(self):
        """Execute the training process"""
        
        print("Cannabis AI Training Script")
        print("=" * 50)
        
        # Get initial stats
        print("\n1. Getting initial AI stats...")
        initial_stats = await self.get_stats()
        print(f"   Initial accuracy: {initial_stats.get('current_accuracy', 0):.2%}")
        print(f"   Examples trained: {initial_stats.get('total_examples_trained', 0)}")
        
        # Create training examples
        print("\n2. Creating training examples...")
        examples = self.create_training_examples()
        print(f"   Created {len(examples)} training examples")
        
        # Train in batches
        print("\n3. Training AI with cannabis knowledge...")
        batch_size = 20
        total_trained = 0
        
        for i in range(0, len(examples), batch_size):
            batch = examples[i:i+batch_size]
            print(f"   Training batch {i//batch_size + 1}/{(len(examples)-1)//batch_size + 1}...")
            
            result = await self.train_ai(batch)
            
            if result.get('success'):
                trained = result.get('examples_trained', 0)
                total_trained += trained
                accuracy_after = result.get('accuracy_after', 0)
                print(f"     ✓ Trained {trained} examples")
                print(f"     Accuracy: {accuracy_after:.2%}")
            else:
                print(f"     ✗ Training failed: {result.get('error', 'Unknown error')}")
        
        print(f"\n   Total examples trained: {total_trained}")
        
        # Get final stats
        print("\n4. Getting final AI stats...")
        final_stats = await self.get_stats()
        print(f"   Final accuracy: {final_stats.get('current_accuracy', 0):.2%}")
        print(f"   Total examples: {final_stats.get('total_examples_trained', 0)}")
        print(f"   Unique patterns: {final_stats.get('unique_patterns', 0)}")
        
        # Test some queries
        print("\n5. Testing AI responses...")
        test_queries = [
            ("hi", {}),
            ("got any fire?", {}),
            ("I need something for sleep", {}),
            ("show me pink kush", {}),
            ("I'm new to this", {"visit_count": 1})
        ]
        
        for query, context in test_queries:
            print(f"\n   Query: '{query}'")
            response = await self.test_query(query, context)
            
            if response.get('message'):
                message = response['message'][:100] + "..." if len(response['message']) > 100 else response['message']
                print(f"   Response: {message}")
                print(f"   Confidence: {response.get('confidence', 0):.2%}")
                
                if response.get('products'):
                    print(f"   Products found: {len(response['products'])}")
        
        print("\n" + "=" * 50)
        print("Training complete!")
        
        # Calculate improvement
        initial_accuracy = initial_stats.get('current_accuracy', 0)
        final_accuracy = final_stats.get('current_accuracy', 0)
        
        if initial_accuracy > 0:
            improvement = ((final_accuracy - initial_accuracy) / initial_accuracy) * 100
            print(f"Accuracy improved by {improvement:.1f}%")
        else:
            print(f"Accuracy achieved: {final_accuracy:.2%}")

async def main():
    """Main entry point"""
    
    async with CannabisAITrainer() as trainer:
        await trainer.run_training()

if __name__ == "__main__":
    asyncio.run(main())