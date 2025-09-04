"""
Context-Aware Conversation Engine
Uses LLM to understand context semantically, not pattern matching
Industry-standard approach for conversational AI
"""

import logging
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import asyncpg

logger = logging.getLogger(__name__)

@dataclass
class ConversationState:
    """Represents the full conversation state"""
    session_id: str
    customer_id: Optional[str] = None
    messages: List[Dict] = field(default_factory=list)  # Full conversation history
    last_products_shown: List[Dict] = field(default_factory=list)
    last_intent: Optional[str] = None
    current_topic: Optional[str] = None  # What we're discussing
    cart_items: List[Dict] = field(default_factory=list)
    user_preferences: Dict = field(default_factory=dict)
    
    def to_context_string(self) -> str:
        """Convert state to a context string for LLM"""
        context = "Conversation Context:\n"
        
        # Recent messages
        if self.messages:
            context += "\nRecent Messages:\n"
            for msg in self.messages[-5:]:  # Last 5 exchanges
                context += f"Customer: {msg.get('user', '')}\n"
                context += f"Assistant: {msg.get('assistant', '')}\n"
        
        # Products shown
        if self.last_products_shown:
            context += f"\nProducts Currently Displayed ({len(self.last_products_shown)} items):\n"
            for i, product in enumerate(self.last_products_shown[:10], 1):
                context += f"{i}. {product.get('product_name', 'Unknown')} - ${product.get('price', 0):.2f}"
                if product.get('size'):
                    context += f" ({product['size']})"
                if product.get('brand'):
                    context += f" by {product['brand']}"
                context += "\n"
        
        # Current cart
        if self.cart_items:
            context += f"\nItems in Cart: {len(self.cart_items)}\n"
            
        return context


class ContextAwareEngine:
    """
    Modern context-aware conversation engine using LLM for understanding
    No pattern matching - pure semantic understanding
    """
    
    def __init__(self, db_pool: asyncpg.Pool, llm_function, prompt_manager):
        self.db_pool = db_pool
        self.llm = llm_function
        self.prompt_manager = prompt_manager
        self.conversation_states = {}  # In-memory cache
        
    async primitive.get_conversation_state(self, session_id: str, customer_id: str = None) -> ConversationState:
        """Get or create conversation state"""
        
        # Check cache first
        if session_id in self.conversation_states:
            return self.conversation_states[session_id]
            
        # Load from database
        state = await self._load_state_from_db(session_id, customer_id)
        self.conversation_states[session_id] = state
        return state
    
    async def understand_message(self, 
                                message: str, 
                                session_id: str,
                                customer_id: str = None) -> Dict:
        """
        Use LLM to understand message in context
        This is the core of modern conversational AI
        """
        
        # Get conversation state
        state = await self.get_conversation_state(session_id, customer_id)
        
        # Build context for LLM
        context_string = state.to_context_string()
        
        # Use LLM to understand the message WITH context
        understanding_prompt = f"""
You are analyzing a customer message in a cannabis dispensary conversation.

{context_string}

Current Customer Message: "{message}"

Analyze and determine:
1. Intent: What does the customer want? (search/purchase/question/greeting/reference)
2. Reference: Are they referring to previously shown products? If yes, which one?
3. Action: What action should be taken?

IMPORTANT: If the customer is referring to products shown above (using numbers, "that", "this", "it", etc.), 
identify WHICH product they mean based on context, not patterns.

Output as JSON:
{{"intent": "", "reference_type": "", "referenced_product_index": null, "action": "", "details": {{}}}}

Examples:
- "I want number 1" -> {{"intent": "purchase", "reference_type": "product", "referenced_product_index": 0, "action": "add_to_cart"}}
- "tell me more about the second one" -> {{"intent": "question", "reference_type": "product", "referenced_product_index": 1, "action": "show_details"}}
- "what's the THC?" (after showing products) -> {{"intent": "question", "reference_type": "attribute", "action": "show_thc_levels"}}
- "I'll stick with that" -> {{"intent": "purchase", "reference_type": "last_discussed", "action": "add_to_cart"}}
"""
        
        # Get LLM understanding
        if self.llm:
            try:
                response = self.llm(understanding_prompt, max_tokens=200, temperature=0.1, echo=False)
                if response and response.get('choices'):
                    understanding_text = response['choices'][0]['text'].strip()
                    
                    # Parse JSON response
                    try:
                        # Extract JSON from response
                        import re
                        json_match = re.search(r'\{.*\}', understanding_text, re.DOTALL)
                        if json_match:
                            understanding = json.loads(json_match.group())
                            logger.info(f"LLM Understanding: {understanding}")
                            
                            # Process based on understanding
                            return await self._process_understanding(understanding, message, state)
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse LLM understanding: {understanding_text}")
            except Exception as e:
                logger.error(f"LLM understanding failed: {e}")
        
        # Fallback to basic intent detection
        return {
            "intent": "unknown",
            "needs_clarification": True,
            "message": "I'm not sure what you're referring to. Could you be more specific?"
        }
    
    async def _process_understanding(self, understanding: Dict, message: str, state: ConversationState) -> Dict:
        """Process the LLM's understanding and generate appropriate response"""
        
        intent = understanding.get('intent', 'unknown')
        ref_type = understanding.get('reference_type')
        ref_index = understanding.get('referenced_product_index')
        action = understanding.get('action')
        
        # Handle product references
        if ref_type == 'product' and ref_index is not None:
            if 0 <= ref_index < len(state.last_products_shown):
                product = state.last_products_shown[ref_index]
                
                if intent == 'purchase' or action == 'add_to_cart':
                    return {
                        "intent": "purchase",
                        "action": "add_to_cart",
                        "product": product,
                        "message": f"Great choice! Adding {product['product_name']} to your cart - ${product.get('price', 0):.2f}",
                        "success": True
                    }
                elif intent == 'question':
                    return {
                        "intent": "question",
                        "action": "show_details",
                        "product": product,
                        "message": self._generate_product_details(product),
                        "success": True
                    }
        
        # Handle other intents
        if intent == 'greeting':
            return {
                "intent": "greeting",
                "message": "Hello! How can I help you find the perfect cannabis product today?",
                "success": True
            }
        
        # Default response
        return {
            "intent": intent,
            "action": action,
            "understanding": understanding,
            "needs_processing": True
        }
    
    def _generate_product_details(self, product: Dict) -> str:
        """Generate detailed product information"""
        details = f"Here are the details for {product.get('product_name', 'this product')}:\n"
        
        if product.get('brand'):
            details += f"Brand: {product['brand']}\n"
        if product.get('price'):
            details += f"Price: ${product['price']:.2f}\n"
        if product.get('size'):
            details += f"Size: {product['size']}\n"
        if product.get('thc'):
            details += f"THC: {product['thc']}%\n"
        if product.get('cbd'):
            details += f"CBD: {product['cbd']}%\n"
        if product.get('description'):
            details += f"\n{product['description']}\n"
            
        details += "\nWould you like to add this to your cart?"
        return details
    
    async def update_state(self, session_id: str, update: Dict):
        """Update conversation state"""
        state = await self.get_conversation_state(session_id)
        
        if 'message' in update:
            state.messages.append(update['message'])
            # Keep last 20 messages
            state.messages = state.messages[-20:]
            
        if 'products_shown' in update:
            state.last_products_shown = update['products_shown']
            
        if 'intent' in update:
            state.last_intent = update['intent']
            
        if 'cart_item' in update:
            state.cart_items.append(update['cart_item'])
            
        # Save to database
        await self._save_state_to_db(session_id, state)
        
        # Update cache
        self.conversation_states[session_id] = state
    
    async def _load_state_from_db(self, session_id: str, customer_id: str = None) -> ConversationState:
        """Load conversation state from database"""
        state = ConversationState(session_id=session_id, customer_id=customer_id)
        
        if not self.db_pool:
            return state
            
        try:
            async with self.db_pool.acquire() as conn:
                # Load from conversation_context table
                row = await conn.fetchrow("""
                    SELECT * FROM conversation_context
                    WHERE session_id = $1
                """, session_id)
                
                if row:
                    if row['last_products_shown']:
                        state.last_products_shown = json.loads(row['last_products_shown'])
                    state.last_intent = row['last_intent']
                    if row['user_preferences']:
                        state.user_preferences = json.loads(row['user_preferences'])
                    
                    logger.info(f"Loaded state for {session_id}: {len(state.last_products_shown)} products")
                
                # Load recent messages
                messages = await conn.fetch("""
                    SELECT user_message, ai_response, created_at
                    FROM conversation_messages
                    WHERE session_id = $1
                    ORDER BY created_at DESC
                    LIMIT 10
                """, session_id)
                
                if messages:
                    for msg in reversed(messages):
                        state.messages.append({
                            'user': msg['user_message'],
                            'assistant': msg['ai_response'],
                            'timestamp': msg['created_at'].isoformat() if msg['created_at'] else None
                        })
                        
        except Exception as e:
            logger.error(f"Error loading state: {e}")
            
        return state
    
    async def _save_state_to_db(self, session_id: str, state: ConversationState):
        """Save conversation state to database"""
        if not self.db_pool:
            return
            
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO conversation_context 
                    (session_id, customer_id, last_products_shown, last_intent, user_preferences)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (session_id) DO UPDATE SET
                        last_products_shown = EXCLUDED.last_products_shown,
                        last_intent = EXCLUDED.last_intent,
                        user_preferences = EXCLUDED.user_preferences,
                        updated_at = CURRENT_TIMESTAMP
                """,
                session_id,
                state.customer_id,
                json.dumps(state.last_products_shown) if state.last_products_shown else None,
                state.last_intent,
                json.dumps(state.user_preferences) if state.user_preferences else None
                )
                
                logger.info(f"Saved state for {session_id}")
                
        except Exception as e:
            logger.error(f"Error saving state: {e}")


# Example of how this would be integrated:
async def process_with_context(engine: ContextAwareEngine, message: str, session_id: str):
    """
    Process a message with full context awareness
    No pattern matching - pure LLM understanding
    """
    
    # Get LLM understanding of the message in context
    understanding = await engine.understand_message(message, session_id)
    
    # Take action based on understanding
    if understanding.get('success'):
        # Update conversation state
        await engine.update_state(session_id, {
            'message': {'user': message, 'assistant': understanding['message']},
            'intent': understanding.get('intent')
        })
        
        return understanding
    else:
        # Need more processing
        return understanding