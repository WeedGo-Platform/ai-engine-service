#!/usr/bin/env python3
"""
Semantic Context Manager - NO PATTERN MATCHING!
Uses LLM to understand references and context semantically
Industry-standard approach
"""

import logging
import json
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import asyncpg

logger = logging.getLogger(__name__)

@dataclass
class ConversationContext:
    """Represents the current conversation state"""
    session_id: str
    customer_id: str = None
    last_products_shown: List[Dict] = field(default_factory=list)
    last_intent: str = None
    message_history: List[Dict] = field(default_factory=list)
    current_cart: List[Dict] = field(default_factory=list)
    user_preferences: Dict = field(default_factory=dict)
    last_search_criteria: Dict = field(default_factory=dict)
    last_selected_product: Dict = None
    last_action_product: Dict = None
    timestamp: datetime = field(default_factory=datetime.now)


class SemanticContextManager:
    """
    Manages conversation context using SEMANTIC UNDERSTANDING
    NO PATTERNS - Pure LLM understanding
    """
    
    def __init__(self, db_pool: asyncpg.Pool = None, llm_function=None):
        self.db_pool = db_pool
        self.llm = llm_function
        self.contexts = {}  # In-memory cache
        logger.info("Initialized Semantic Context Manager - NO PATTERNS!")
    
    async def get_context(self, session_id: str, customer_id: str = None) -> ConversationContext:
        """Get or create conversation context"""
        # ALWAYS load from database to ensure we have the latest data
        # The in-memory cache was causing stale data issues
        context = await self._load_context_from_db(session_id, customer_id)
        
        # Update the cache with fresh data
        self.contexts[session_id] = context
        
        return context
    
    async def understand_reference_semantically(self, message: str, context: ConversationContext) -> Dict:
        """
        Use LLM to understand if message references previous products
        NO PATTERN MATCHING - Pure semantic understanding
        """
        
        logger.info(f"Semantic reference check: '{message}' with {len(context.last_products_shown) if context else 0} products in context")
        
        if not self.llm or not context or not context.last_products_shown:
            logger.info(f"Skipping reference check - LLM: {bool(self.llm)}, Context: {bool(context)}, Products: {len(context.last_products_shown) if context and context.last_products_shown else 0}")
            return {"is_reference": False, "referenced_item": None, "confidence": 0}
        
        # Build product list for LLM
        products_text = ""
        for i, product in enumerate(context.last_products_shown[:10], 1):
            products_text += f"{i}. {product.get('product_name', 'Unknown')}"
            if product.get('price'):
                products_text += f" - ${product['price']:.2f}"
            if product.get('size'):
                products_text += f" ({product['size']})"
            products_text += "\n"
        
        logger.info(f"Checking reference with {len(context.last_products_shown[:10])} products")
        
        # Let LLM understand the reference
        prompt = f"""You are analyzing a cannabis dispensary conversation.

Products currently shown to customer:
{products_text}

Customer now says: "{message}"

Determine if they are referring to any of the shown products.

Common references:
- Numbers: "1", "number 1", "the first one" → Product #1
- Ordinals: "first", "second", "last" → Corresponding product
- Questions: "tell me about 1", "what about #2" → Asking about that product
- Actions: "I'll take 1", "add number 2" → Selecting that product
- Descriptions: "the cheaper one", "the indica" → Product matching description

Output JSON:
{{"is_reference": true/false, "product_index": 0-based-index or null, "action": "select/inquire/similar", "confidence": 0.0-1.0}}

If NOT a reference, return is_reference: false.
"""
        
        try:
            logger.info("Calling LLM for reference understanding...")
            response = self.llm(prompt, max_tokens=100, temperature=0)
            if response and response.get('choices'):
                result_text = response['choices'][0]['text'].strip()
                logger.info(f"LLM response: {result_text[:200]}")
                
                # Parse JSON response
                json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                    
                    logger.info(f"Parsed result: {result}")
                    
                    if result.get('is_reference'):
                        logger.info(f"✓ Semantically detected reference: {message} → Product #{result.get('product_index', -1) + 1}")
                    else:
                        logger.info(f"✗ Not a reference according to LLM: {message}")
                    
                    return result
        except Exception as e:
            logger.error(f"Semantic reference understanding failed: {e}", exc_info=True)
        
        logger.info("Returning default non-reference result")
        return {"is_reference": False, "referenced_item": None, "confidence": 0}
    
    async def understand_similarity_request(self, message: str, context: ConversationContext) -> Dict:
        """
        Use LLM to understand if user wants similar products
        NO KEYWORDS - Semantic understanding
        """
        
        if not self.llm:
            return {"is_similar": False, "similar_to": None}
        
        # CRITICAL: Only check for similarity if we have products in context
        # Without context, user is likely searching for new products, not asking for similar
        if not context or (not context.last_selected_product and not context.last_products_shown):
            logger.info(f"No products in context - not a similarity request: '{message}'")
            return {"is_similar": False, "similar_to": None}
        
        # Build context
        last_product = "None"
        if context.last_selected_product:
            last_product = context.last_selected_product.get('product_name', 'Unknown product')
        elif context.last_products_shown:
            last_product = f"Products shown: {len(context.last_products_shown)} items"
        
        prompt = f"""Understand if the customer wants similar products to what they previously viewed.

Last interaction: Customer selected/viewed: {last_product}
Customer now says: "{message}"

IMPORTANT: Distinguish between:
1. Similarity request - wants products SIMILAR to what was shown
   Examples: "show me similar", "what else like this", "alternatives to that", "more like that one"
   
2. New product search - looking for a SPECIFIC product by name
   Examples: "forbidden apple preroll", "pink kush", "1g pre-roll", "show me indicas"

If they mention a specific product name or category, it's likely a NEW SEARCH, not similarity.

Output JSON:
{{"is_similar": true/false, "similar_to_what": "product name or null"}}
"""
        
        try:
            response = self.llm(prompt, max_tokens=100, temperature=0)
            if response and response.get('choices'):
                result_text = response['choices'][0]['text'].strip()
                
                json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                    
                    # Handle both "wants_similar" and "is_similar" for compatibility
                    if result.get('is_similar') or result.get('wants_similar'):
                        logger.info(f"Semantically detected similarity request: {message}")
                        
                        # Return the product they want similar to
                        return {
                            "is_similar": True,
                            "similar_to": context.last_selected_product or (
                                context.last_products_shown[0] if context.last_products_shown else None
                            ),
                            "attributes": ["category", "strain_type", "price_range", "effects"]
                        }
                    
        except Exception as e:
            logger.error(f"Semantic similarity understanding failed: {e}")
        
        return {"is_similar": False, "similar_to": None}
    
    def track_product_selection(self, product: Dict, action: str, context: ConversationContext):
        """Track when a product is selected or acted upon"""
        context.last_selected_product = product
        context.last_action_product = product
        logger.info(f"Tracked {action} for product: {product.get('product_name', 'Unknown')}")
    
    def extract_referenced_product(self, reference_result: Dict, context: ConversationContext) -> Optional[Dict]:
        """Extract the actual product from reference result"""
        
        if not reference_result.get('is_reference'):
            return None
        
        index = reference_result.get('product_index')
        if index is not None and 0 <= index < len(context.last_products_shown):
            return context.last_products_shown[index]
        
        return None
    
    async def update_context(self, session_id: str, update_data: Dict) -> ConversationContext:
        """Update conversation context"""
        
        context = await self.get_context(session_id)
        
        # Update various aspects
        if 'products_shown' in update_data:
            context.last_products_shown = update_data['products_shown']
            logger.info(f"Updated context with {len(update_data['products_shown'])} products")
        
        if 'message' in update_data:
            context.message_history.append(update_data['message'])
            context.message_history = context.message_history[-20:]  # Keep last 20
        
        if 'intent' in update_data:
            context.last_intent = update_data['intent']
        
        if 'last_selected_product' in update_data:
            context.last_selected_product = update_data['last_selected_product']
            logger.info(f"Tracked selected product: {context.last_selected_product.get('product_name')}")
        
        if 'cart_item' in update_data:
            context.current_cart.append(update_data['cart_item'])
        
        # Save to database
        await self._save_context_to_db(session_id, context)
        
        # Update cache
        self.contexts[session_id] = context
        
        return context
    
    async def _load_context_from_db(self, session_id: str, customer_id: str = None) -> ConversationContext:
        """Load context from database"""
        
        logger.info(f"Loading context from DB for session: {session_id}")
        
        context = ConversationContext(session_id=session_id, customer_id=customer_id)
        
        if not self.db_pool:
            logger.warning("No DB pool available for context loading")
            return context
        
        try:
            async with self.db_pool.acquire() as conn:
                # Load from conversation_context table
                row = await conn.fetchrow("""
                    SELECT * FROM conversation_context
                    WHERE session_id = $1
                """, session_id)
                
                if row:
                    logger.info(f"Found row for {session_id}, has products: {row['last_products_shown'] is not None}")
                    if row['last_products_shown']:
                        products_json = row['last_products_shown']
                        context.last_products_shown = json.loads(products_json)
                        logger.info(f"Loaded {len(context.last_products_shown)} products from DB")
                    else:
                        logger.info("No products in DB row")
                    
                    context.last_intent = row['last_intent']
                    if row.get('last_selected_product'):
                        context.last_selected_product = json.loads(row['last_selected_product'])
                    
                    logger.info(f"✓ Loaded context for {session_id}: {len(context.last_products_shown)} products")
                else:
                    logger.info(f"No context found in DB for {session_id}")
                
                # Load message history if table exists
                try:
                    messages = await conn.fetch("""
                        SELECT user_message, ai_response, created_at
                        FROM conversation_messages
                        WHERE session_id = $1
                        ORDER BY created_at DESC
                        LIMIT 10
                    """, session_id)
                    
                    for msg in reversed(messages):
                        context.message_history.append({
                            'user': msg['user_message'],
                            'assistant': msg['ai_response'],
                            'timestamp': msg['created_at'].isoformat()
                        })
                except:
                    pass  # Table might not exist yet
                
        except Exception as e:
            logger.error(f"Error loading context: {e}")
        
        return context
    
    async def _save_context_to_db(self, session_id: str, context: ConversationContext):
        """Save context to database"""
        
        if not self.db_pool:
            return
        
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO conversation_context 
                    (session_id, customer_id, last_products_shown, last_intent, 
                     last_selected_product, user_preferences)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (session_id) DO UPDATE SET
                        last_products_shown = EXCLUDED.last_products_shown,
                        last_intent = EXCLUDED.last_intent,
                        last_selected_product = EXCLUDED.last_selected_product,
                        user_preferences = EXCLUDED.user_preferences,
                        updated_at = CURRENT_TIMESTAMP
                """,
                session_id,
                context.customer_id,
                json.dumps(context.last_products_shown) if context.last_products_shown else None,
                context.last_intent,
                json.dumps(context.last_selected_product) if context.last_selected_product else None,
                json.dumps(context.user_preferences) if context.user_preferences else None
                )
                
                logger.info(f"Saved context for {session_id}")
                
                # Save last message to history if table exists
                if context.message_history:
                    last_msg = context.message_history[-1]
                    try:
                        await conn.execute("""
                            INSERT INTO conversation_messages
                            (session_id, customer_id, user_message, ai_response, intent)
                            VALUES ($1, $2, $3, $4, $5)
                        """,
                        session_id,
                        context.customer_id,
                        last_msg.get('user'),
                        last_msg.get('assistant'),
                        context.last_intent
                        )
                    except:
                        pass  # Table might not exist
                
        except Exception as e:
            logger.error(f"Error saving context: {e}")