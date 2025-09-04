"""
Semantic Search Engine with Proper Context Understanding
Uses LLM for all understanding - no pattern matching
"""

import logging
import json
from typing import Dict, List, Optional
from services.centralized_prompt_manager import CentralizedPromptManager

logger = logging.getLogger(__name__)

class SemanticSearchEngine:
    """
    Modern semantic search engine that uses LLM for everything
    No regex, no patterns - pure AI understanding
    """
    
    def __init__(self, db_pool, llm_function):
        self.db_pool = db_pool
        self.llm = llm_function
        self.prompt_manager = CentralizedPromptManager()
        
    async def process_query(self, message: str, session_id: str, customer_id: str = None) -> Dict:
        """
        Process query with semantic understanding
        """
        logger.info(f"Semantic processing: {message}")
        
        # Load conversation context from database
        context = await self._load_context(session_id)
        
        # Step 1: Understand message in context using LLM
        understanding = await self._understand_with_llm(message, context)
        
        # Step 2: Take action based on understanding
        result = await self._execute_understanding(understanding, message, context, session_id)
        
        # Step 3: Update context for next turn
        await self._save_context(session_id, result, message)
        
        return result
    
    async def _understand_with_llm(self, message: str, context: Dict) -> Dict:
        """
        Use LLM to understand the message semantically
        This replaces ALL pattern matching
        """
        
        # Build context string for LLM
        context_prompt = self._build_context_prompt(message, context)
        
        # Ask LLM to understand the message
        understanding_prompt = f"""
Analyze this customer message in a cannabis dispensary.

{context_prompt}

Current message: "{message}"

Determine:
1. What is the customer's intent?
2. Are they referring to something shown earlier?
3. What action should be taken?

Critical: Use context to understand references.
- "I want 1" after showing products = select product #1
- "I want 1" when discussing quantity = wants 1 item
- "that one" = last discussed item
- "yes" after showing products = confirmation

Output JSON:
{{
    "intent": "search|purchase|question|greeting|confirmation",
    "refers_to_product": true/false,
    "product_reference": null or product_index,
    "confidence": 0.0-1.0,
    "reasoning": "why you think this"
}}
"""
        
        if self.llm:
            try:
                response = self.llm(understanding_prompt, max_tokens=300, temperature=0.1, echo=False)
                if response and response.get('choices'):
                    text = response['choices'][0]['text'].strip()
                    
                    # Extract JSON from response
                    import re
                    json_match = re.search(r'\{.*\}', text, re.DOTALL)
                    if json_match:
                        understanding = json.loads(json_match.group())
                        logger.info(f"LLM Understanding: {understanding}")
                        return understanding
                        
            except Exception as e:
                logger.error(f"LLM understanding failed: {e}")
        
        # Fallback
        return {"intent": "unknown", "confidence": 0.0}
    
    def _build_context_prompt(self, message: str, context: Dict) -> str:
        """Build context string for LLM"""
        
        prompt = ""
        
        # Add conversation history
        if context.get('messages'):
            prompt += "Recent conversation:\n"
            for msg in context['messages'][-3:]:
                prompt += f"Customer: {msg.get('user', '')}\n"
                prompt += f"Assistant: {msg.get('ai', '')}\n"
            prompt += "\n"
        
        # Add products shown
        if context.get('products_shown'):
            prompt += f"Products currently displayed ({len(context['products_shown'])} items):\n"
            for i, product in enumerate(context['products_shown'][:10], 1):
                prompt += f"{i}. {product.get('product_name', '')} - ${product.get('price', 0):.2f}"
                if product.get('size'):
                    prompt += f" ({product['size']})"
                prompt += "\n"
            prompt += "\n"
        
        # Add cart status
        if context.get('cart_items'):
            prompt += f"Cart has {len(context['cart_items'])} items\n\n"
        
        return prompt
    
    async def _execute_understanding(self, understanding: Dict, message: str, context: Dict, session_id: str) -> Dict:
        """
        Execute action based on LLM understanding
        No patterns - just semantic logic
        """
        
        intent = understanding.get('intent', 'unknown')
        confidence = understanding.get('confidence', 0.0)
        
        # Only act if confident
        if confidence < 0.5:
            return {
                "message": "I'm not sure what you mean. Could you please clarify?",
                "intent": "clarification",
                "success": False
            }
        
        # Handle product reference
        if understanding.get('refers_to_product') and understanding.get('product_reference') is not None:
            idx = understanding['product_reference']
            if 0 <= idx < len(context.get('products_shown', [])):
                product = context['products_shown'][idx]
                
                if intent == 'purchase':
                    return {
                        "message": f"Great! Adding {product['product_name']} to your cart - ${product.get('price', 0):.2f}",
                        "intent": "purchase",
                        "product": product,
                        "action": "add_to_cart",
                        "success": True
                    }
                elif intent == 'question':
                    return {
                        "message": self._describe_product(product),
                        "intent": "question",
                        "product": product,
                        "success": True
                    }
        
        # Handle search intent
        if intent == 'search':
            # Extract what to search for using LLM
            search_results = await self._semantic_search(message)
            return {
                "message": self._format_search_results(search_results),
                "products": search_results,
                "intent": "search",
                "success": True
            }
        
        # Handle greeting
        if intent == 'greeting':
            return {
                "message": "Hello! Welcome to our dispensary. What can I help you find today?",
                "intent": "greeting",
                "success": True
            }
        
        # Handle confirmation
        if intent == 'confirmation':
            # Use context to understand what's being confirmed
            if context.get('last_intent') == 'search':
                return {
                    "message": "Great! Which product would you like?",
                    "intent": "confirmation",
                    "success": True
                }
        
        return {
            "message": f"I understand you want to {intent}. Let me help you with that.",
            "intent": intent,
            "needs_processing": True
        }
    
    async def _semantic_search(self, query: str) -> List[Dict]:
        """
        Use LLM to understand search intent and query database
        """
        
        # Use LLM to extract search parameters
        extract_prompt = f"""
Extract search parameters from this cannabis product query:
"{query}"

Output JSON with any relevant fields:
- product_name: specific product mentioned
- category: Flower/Edibles/Vapes/Extracts/Topicals
- strain_type: Sativa/Indica/Hybrid
- price_range: budget constraints
- size: quantity/weight
- brand: brand name

Only include fields that are mentioned.
"""
        
        search_params = {}
        if self.llm:
            try:
                response = self.llm(extract_prompt, max_tokens=200, temperature=0.1, echo=False)
                if response and response.get('choices'):
                    text = response['choices'][0]['text'].strip()
                    import re
                    json_match = re.search(r'\{.*\}', text, re.DOTALL)
                    if json_match:
                        search_params = json.loads(json_match.group())
            except Exception as e:
                logger.error(f"Search extraction failed: {e}")
        
        # Query database based on extracted parameters
        return await self._query_products(search_params)
    
    async def _query_products(self, params: Dict) -> List[Dict]:
        """Query database for products"""
        
        if not self.db_pool:
            return []
            
        async with self.db_pool.acquire() as conn:
            # Build dynamic query based on parameters
            conditions = []
            values = []
            idx = 1
            
            if params.get('product_name'):
                conditions.append(f"LOWER(product_name) LIKE ${idx}")
                values.append(f"%{params['product_name'].lower()}%")
                idx += 1
                
            if params.get('category'):
                conditions.append(f"category = ${idx}")
                values.append(params['category'])
                idx += 1
                
            if params.get('strain_type'):
                conditions.append(f"plant_type = ${idx}")
                values.append(params['strain_type'])
                idx += 1
            
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            query = f"""
                SELECT * FROM products 
                WHERE {where_clause}
                ORDER BY unit_price ASC
                LIMIT 20
            """
            
            results = await conn.fetch(query, *values)
            return [dict(r) for r in results]
    
    def _describe_product(self, product: Dict) -> str:
        """Generate product description"""
        desc = f"{product.get('product_name', 'Product')} details:\n"
        desc += f"Price: ${product.get('price', 0):.2f}\n"
        if product.get('thc'):
            desc += f"THC: {product['thc']}%\n"
        if product.get('cbd'):
            desc += f"CBD: {product['cbd']}%\n"
        return desc
    
    def _format_search_results(self, products: List[Dict]) -> str:
        """Format search results for display"""
        if not products:
            return "I couldn't find any products matching your search."
            
        response = f"I found {len(products)} products for you:\n\n"
        for i, p in enumerate(products[:10], 1):
            response += f"{i}. {p.get('product_name', 'Unknown')} - ${p.get('unit_price', 0):.2f}\n"
        
        return response
    
    async def _load_context(self, session_id: str) -> Dict:
        """Load conversation context from database"""
        
        context = {
            'messages': [],
            'products_shown': [],
            'cart_items': [],
            'last_intent': None
        }
        
        if not self.db_pool or not session_id:
            return context
            
        try:
            async with self.db_pool.acquire() as conn:
                # Load from conversation_context table
                row = await conn.fetchrow("""
                    SELECT * FROM conversation_context
                    WHERE session_id = $1
                """, session_id)
                
                if row:
                    if row['last_products_shown']:
                        context['products_shown'] = json.loads(row['last_products_shown'])
                    context['last_intent'] = row['last_intent']
                    
                    logger.info(f"Loaded context: {len(context['products_shown'])} products")
                    
        except Exception as e:
            logger.error(f"Failed to load context: {e}")
            
        return context
    
    async def _save_context(self, session_id: str, result: Dict, message: str):
        """Save updated context to database"""
        
        if not self.db_pool or not session_id:
            return
            
        try:
            async with self.db_pool.acquire() as conn:
                products_shown = json.dumps(result.get('products', [])) if result.get('products') else None
                
                await conn.execute("""
                    INSERT INTO conversation_context 
                    (session_id, last_products_shown, last_intent)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (session_id) DO UPDATE SET
                        last_products_shown = EXCLUDED.last_products_shown,
                        last_intent = EXCLUDED.last_intent,
                        updated_at = CURRENT_TIMESTAMP
                """, session_id, products_shown, result.get('intent'))
                
                logger.info(f"Saved context for {session_id}")
                
        except Exception as e:
            logger.error(f"Failed to save context: {e}")