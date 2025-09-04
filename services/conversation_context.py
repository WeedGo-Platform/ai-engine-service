"""
Conversation Context Manager
Maintains conversation state and handles references to previous interactions
"""

import re
import json
import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
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
    last_selected_product: Dict = None  # Track the last product user selected/added to cart
    last_action_product: Dict = None    # Track product from last action (view, add to cart, etc)
    timestamp: datetime = field(default_factory=datetime.now)

class ConversationContextManager:
    """Manages conversation context and product references"""
    
    # Reference patterns for detecting when users refer to previous products
    REFERENCE_PATTERNS = {
        "number": [
            r"^\d+$",  # Just a number: "1", "2", "3"
            r"^#\d+$",  # Hash number: "#1", "#2"
            r"\bnumber\s+\d+\b",  # "number 1", "give me number 2"
            r"\boption\s+\d+\b",  # "option 1", "option 2"
            r"\bitem\s+\d+\b",  # "item 1", "item 2"
            r"(?:i\s+want|give\s+me|i'll\s+take)\s+\d+$",  # "I want 1", "give me 2"
            r"(?:tell\s+me\s+(?:more\s+)?about|what\s+about|details\s+on)\s+\d+",  # "tell me about 1", "tell me more about 1"
            r"(?:tell\s+me\s+(?:more\s+)?about|what\s+about|details\s+on)\s+#?\d+\.?$",  # "tell me about 1.", "what about #1"
        ],
        "ordinal": [
            r"\bfirst\s*(?:one)?\b",  # "first", "first one"
            r"\bsecond\s*(?:one)?\b",  # "second", "second one"
            r"\bthird\s*(?:one)?\b",  # "third", "third one"
            r"\blast\s*(?:one)?\b",  # "last", "last one"
            r"\btop\s*(?:one)?\b",  # "top", "top one"
        ],
        "demonstrative": [
            r"\bthat\s*(?:one)?\b",  # "that", "that one"
            r"\bthis\s*(?:one)?\b",  # "this", "this one"
            r"\bthose\b",  # "those"
            r"\bthese\b",  # "these"
            r"stick\s+with\s+(?:this|that|it)",  # "stick with this", "stick with it"
        ],
        "attribute": [
            r"\bthe\s+cheaper\s*(?:one)?\b",  # "the cheaper one"
            r"\bthe\s+expensive\s*(?:one)?\b",  # "the expensive one"
            r"\bthe\s+strongest?\s*(?:one)?\b",  # "the strong one", "the strongest"
            r"\bthe\s+sativa\s*(?:one)?\b",  # "the sativa", "the sativa one"
            r"\bthe\s+indica\s*(?:one)?\b",  # "the indica", "the indica one"
            r"\bthe\s+hybrid\s*(?:one)?\b",  # "the hybrid"
            r"\bthe\s+\d+g\b",  # "the 3.5g", "the 14g"
        ],
        "quantity": [
            r"^(?:give\s+me|i\s+want|i\'ll\s+take)\s+(\d+)(?:\s+of\s+(?:those|them|it))?$",  # "give me 3", "I want 2 of those"
            r"^(\d+)\s+(?:of\s+)?(?:those|them|it|that)$",  # "2 of those", "3 of them"
            r"^(?:a\s+)?couple(?:\s+of\s+(?:those|them))?$",  # "a couple", "couple of those"
            r"^(?:a\s+)?few(?:\s+of\s+(?:those|them))?$",  # "a few", "few of them"
        ],
        "partial_name": [
            r"\bpeach\b",  # Partial product name
            r"\bpink\b",
            r"\bblue\b",
            r"\bkush\b",
            r"\bdream\b",
        ]
    }
    
    def __init__(self, db_pool: asyncpg.Pool = None):
        self.db_pool = db_pool
        self.contexts = {}  # In-memory cache of contexts
        
    async def get_context(self, session_id: str, customer_id: str = None) -> ConversationContext:
        """Get or create conversation context for a session"""
        
        # Check memory cache first
        if session_id in self.contexts:
            context = self.contexts[session_id]
            # Update if older than 30 minutes
            if datetime.now() - context.timestamp > timedelta(minutes=30):
                context = await self._load_context_from_db(session_id, customer_id)
                self.contexts[session_id] = context
            return context
        
        # Load from database
        context = await self._load_context_from_db(session_id, customer_id)
        self.contexts[session_id] = context
        return context
    
    async def _load_context_from_db(self, session_id: str, customer_id: str = None) -> ConversationContext:
        """Load conversation context from database"""
        
        context = ConversationContext(session_id=session_id, customer_id=customer_id)
        
        if not self.db_pool:
            return context
            
        try:
            async with self.db_pool.acquire() as conn:
                # First try to load from conversation_context table
                context_row = await conn.fetchrow("""
                    SELECT * FROM conversation_context
                    WHERE session_id = $1
                """, session_id)
                
                if context_row:
                    context.customer_id = context_row['customer_id'] or customer_id
                    if context_row['last_products_shown']:
                        context.last_products_shown = json.loads(context_row['last_products_shown'])
                    context.last_intent = context_row['last_intent']
                    if context_row['user_preferences']:
                        context.user_preferences = json.loads(context_row['user_preferences'])
                    if context_row['last_search_criteria']:
                        context.last_search_criteria = json.loads(context_row['last_search_criteria'])
                    if context_row['current_cart']:
                        context.current_cart = json.loads(context_row['current_cart'])
                    
                    logger.info(f"Loaded context from DB for session {session_id} with {len(context.last_products_shown)} products")
                
                # Also get recent message history
                messages = await conn.fetch("""
                    SELECT user_message, ai_response, intent, created_at
                    FROM conversation_messages
                    WHERE session_id = $1
                    ORDER BY created_at DESC
                    LIMIT 10
                """, session_id)
                
                if messages:
                    # Reverse to get chronological order
                    messages = list(reversed(messages))
                    
                    for msg in messages:
                        context.message_history.append({
                            'user': msg['user_message'],
                            'ai': msg['ai_response'],
                            'intent': msg['intent'],
                            'timestamp': msg['created_at'].isoformat() if msg['created_at'] else None
                        })
                
                # Get cart items if customer_id provided and not already loaded
                if customer_id and not context.current_cart:
                    cart_items = await conn.fetch("""
                        SELECT product_id, product_name, quantity, price
                        FROM cart_items
                        WHERE customer_id = $1
                    """, customer_id)
                    
                    if cart_items:
                        context.current_cart = [dict(item) for item in cart_items]
                    
        except Exception as e:
            logger.error(f"Error loading context from DB: {e}")
            
        return context
    
    def is_reference(self, message: str, context: ConversationContext) -> bool:
        """Check if message references previously shown products"""
        
        if not context or not context.last_products_shown:
            return False
            
        message_lower = message.lower().strip()
        
        # Check all reference patterns
        for pattern_type, patterns in self.REFERENCE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    logger.info(f"Detected {pattern_type} reference: {message}")
                    return True
        
        # Check if message contains part of a recently shown product name
        for product in context.last_products_shown[:10]:  # Check last 10 products
            product_name = product.get('product_name', '').lower()
            # Check if significant part of product name is in message
            name_parts = product_name.split()
            for part in name_parts:
                if len(part) > 3 and part in message_lower:
                    # Additional context check - make sure it's likely a reference
                    if any(phrase in message_lower for phrase in ['i want', "i'll take", 'give me', 'add']):
                        logger.info(f"Detected product name reference: {message}")
                        return True
                        
        return False
    
    def extract_reference(self, message: str, context: ConversationContext) -> Optional[Dict]:
        """Extract which product is being referenced"""
        
        if not context or not context.last_products_shown:
            return None
            
        message_lower = message.lower().strip()
        products = context.last_products_shown
        
        # Check for number references (1, 2, #1, etc.)
        number_match = re.search(r'(?:^|#|number\s+|option\s+|item\s+)(\d+)', message_lower)
        if number_match:
            index = int(number_match.group(1)) - 1  # Convert to 0-based index
            if 0 <= index < len(products):
                return products[index]
        
        # Check for ordinal references (first, second, last)
        if re.search(r'\bfirst\b', message_lower) and len(products) > 0:
            return products[0]
        elif re.search(r'\bsecond\b', message_lower) and len(products) > 1:
            return products[1]
        elif re.search(r'\bthird\b', message_lower) and len(products) > 2:
            return products[2]
        elif re.search(r'\blast\b', message_lower) and len(products) > 0:
            return products[-1]
        
        # Check for attribute references (cheaper, stronger, sativa, etc.)
        if 'cheaper' in message_lower or 'cheapest' in message_lower:
            return min(products, key=lambda p: p.get('price', float('inf')))
        elif 'expensive' in message_lower or 'priciest' in message_lower:
            return max(products, key=lambda p: p.get('price', 0))
        elif 'strong' in message_lower or 'potent' in message_lower:
            return max(products, key=lambda p: p.get('thc', 0))
        elif 'sativa' in message_lower:
            sativas = [p for p in products if 'sativa' in p.get('strain_type', '').lower()]
            return sativas[0] if sativas else None
        elif 'indica' in message_lower:
            indicas = [p for p in products if 'indica' in p.get('strain_type', '').lower()]
            return indicas[0] if indicas else None
        
        # Check for partial product name matches
        best_match = None
        best_score = 0
        for product in products:
            product_name = product.get('product_name', '').lower()
            # Calculate match score based on common words
            product_words = set(product_name.split())
            message_words = set(message_lower.split())
            common_words = product_words.intersection(message_words)
            
            # Filter out common words that aren't meaningful
            meaningful_words = {w for w in common_words if len(w) > 3}
            score = len(meaningful_words)
            
            if score > best_score:
                best_score = score
                best_match = product
                
        if best_score > 0:
            return best_match
            
        return None
    
    def extract_quantity(self, message: str) -> int:
        """Extract quantity from message"""
        
        message_lower = message.lower()
        
        # Direct number patterns
        quantity_match = re.search(r'(\d+)(?:\s+of)?(?:\s+(?:those|them|it|that))?', message_lower)
        if quantity_match:
            return int(quantity_match.group(1))
        
        # Word patterns
        word_quantities = {
            'one': 1, 'a': 1, 'an': 1,
            'two': 2, 'couple': 2, 'pair': 2,
            'three': 3, 'few': 3,
            'four': 4,
            'five': 5,
            'six': 6, 'half dozen': 6,
            'dozen': 12,
        }
        
        for word, qty in word_quantities.items():
            if word in message_lower:
                return qty
                
        # Default to 1 if no quantity specified
        return 1
    
    async def update_context(self, session_id: str, update_data: Dict) -> ConversationContext:
        """Update conversation context with new information"""
        
        context = await self.get_context(session_id)
        
        if 'products_shown' in update_data:
            context.last_products_shown = update_data['products_shown']
        
        if 'intent' in update_data:
            context.last_intent = update_data['intent']
            
        if 'message' in update_data:
            context.message_history.append(update_data['message'])
            # Keep only last 10 messages
            context.message_history = context.message_history[-10:]
            
        if 'cart_item' in update_data:
            context.current_cart.append(update_data['cart_item'])
            
        if 'preferences' in update_data:
            context.user_preferences.update(update_data['preferences'])
            
        if 'search_criteria' in update_data:
            context.last_search_criteria = update_data['search_criteria']
            
        context.timestamp = datetime.now()
        self.contexts[session_id] = context
        
        # Save to database
        await self._save_context_to_db(session_id, context)
        
        return context
    
    async def _save_context_to_db(self, session_id: str, context: ConversationContext):
        """Save conversation context to database"""
        
        if not self.db_pool:
            return
            
        try:
            async with self.db_pool.acquire() as conn:
                # Try to create table if it doesn't exist
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS conversation_context (
                        session_id VARCHAR(255) PRIMARY KEY,
                        customer_id VARCHAR(255),
                        last_products_shown JSONB,
                        last_intent VARCHAR(50),
                        user_preferences JSONB,
                        last_search_criteria JSONB,
                        current_cart JSONB,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Upsert context
                await conn.execute("""
                    INSERT INTO conversation_context 
                    (session_id, customer_id, last_products_shown, last_intent, 
                     user_preferences, last_search_criteria, current_cart)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    ON CONFLICT (session_id) 
                    DO UPDATE SET
                        last_products_shown = EXCLUDED.last_products_shown,
                        last_intent = EXCLUDED.last_intent,
                        user_preferences = EXCLUDED.user_preferences,
                        last_search_criteria = EXCLUDED.last_search_criteria,
                        current_cart = EXCLUDED.current_cart,
                        updated_at = CURRENT_TIMESTAMP
                """, 
                session_id,
                context.customer_id,
                json.dumps(context.last_products_shown) if context.last_products_shown else None,
                context.last_intent,
                json.dumps(context.user_preferences) if context.user_preferences else None,
                json.dumps(context.last_search_criteria) if context.last_search_criteria else None,
                json.dumps(context.current_cart) if context.current_cart else None
                )
                
                logger.info(f"Saved context for session {session_id} with {len(context.last_products_shown)} products")
                
        except Exception as e:
            logger.error(f"Error saving context to DB: {e}")
    
    def clear_context(self, session_id: str):
        """Clear conversation context"""
        if session_id in self.contexts:
            del self.contexts[session_id]
    
    def detect_similarity_request(self, message: str, context: ConversationContext) -> Dict:
        """
        Detect if user is asking for similar products
        Returns: {"is_similar": bool, "similar_to": product or None, "attributes": []}
        """
        message_lower = message.lower().strip()
        
        # Keywords that indicate similarity request
        similarity_keywords = [
            'similar', 'like', 'same', 'alternative', 'other option',
            'more like', 'something like', 'comparable', 'equivalent',
            'show me more', 'what else', 'other choices'
        ]
        
        # Check if message contains similarity keywords
        is_similar_request = any(keyword in message_lower for keyword in similarity_keywords)
        
        # If "similar" appears after selecting a product, they want similar to that product
        if is_similar_request:
            # Check if they just selected/added a product
            if context.last_selected_product:
                return {
                    "is_similar": True,
                    "similar_to": context.last_selected_product,
                    "attributes": ["strain_type", "price_range", "category", "effects"]
                }
            
            # Check if they're referring to a shown product
            referenced = self.extract_reference(message, context)
            if referenced:
                return {
                    "is_similar": True,
                    "similar_to": referenced,
                    "attributes": ["strain_type", "price_range", "category", "effects"]
                }
            
            # Check if they mention a specific product name
            if context.last_products_shown:
                for product in context.last_products_shown:
                    product_name = product.get('product_name', '').lower()
                    # Check if part of product name is in message
                    if any(word in message_lower for word in product_name.split()[:2]):
                        return {
                            "is_similar": True,
                            "similar_to": product,
                            "attributes": ["strain_type", "price_range", "category"]
                        }
        
        return {"is_similar": False, "similar_to": None, "attributes": []}
    
    def track_product_selection(self, product: Dict, action: str, context: ConversationContext):
        """
        Track when a user selects or interacts with a product
        action: 'view', 'add_to_cart', 'purchase', 'inquire'
        """
        context.last_action_product = product
        
        if action in ['add_to_cart', 'purchase']:
            context.last_selected_product = product
            
        # Add to message history for context
        context.message_history.append({
            'action': action,
            'product': product.get('product_name'),
            'timestamp': datetime.now().isoformat()
        })
        
        logger.info(f"Tracked {action} for product: {product.get('product_name')}")