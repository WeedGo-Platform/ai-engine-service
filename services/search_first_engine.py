"""
Search-First AI Engine
ALWAYS searches database before making ANY claims about product availability
Industry-standard RAG (Retrieval-Augmented Generation) pattern
"""

import logging
import json
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from services.centralized_prompt_manager import CentralizedPromptManager
from services.semantic_context_manager import ConversationContext, SemanticContextManager
from services.search_interfaces import ISearchEngine, SearchCriteria
from services.fast_extractor_model import get_fast_extractor

logger = logging.getLogger(__name__)

@dataclass
class SearchIntent:
    """Structured search intent"""
    product_name: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    sub_category: Optional[str] = None
    size: Optional[str] = None
    strain_type: Optional[str] = None  # Maps to plant_type column in DB
    effects: Optional[List[str]] = None
    price_range: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    special_type: Optional[str] = None  # For infused, diamond, hash, etc.
    
class SearchFirstEngine(ISearchEngine):
    """
    Engine that ALWAYS searches before responding
    Never makes assumptions about what's in stock
    """
    
    def __init__(self, db_pool=None, llm_function=None):
        """Initialize with optional dependencies for backward compatibility"""
        self.db_pool = db_pool
        self.llm = llm_function
        self.prompt_manager = CentralizedPromptManager() if db_pool else None
        self.context_manager = SemanticContextManager(db_pool, llm_function) if db_pool else None
        
    async def initialize(self, db_pool: Any, llm: Any, prompt_manager: Any) -> None:
        """Initialize the search engine with required dependencies (Interface method)"""
        self.db_pool = db_pool
        self.llm = llm
        self.prompt_manager = prompt_manager or CentralizedPromptManager()
        self.context_manager = SemanticContextManager(db_pool, llm)
        logger.info("SearchFirstEngine initialized via interface")
    
    async def search(self, criteria: SearchCriteria) -> List[Dict[str, Any]]:
        """Search products based on criteria (Interface method)"""
        # Convert SearchCriteria to SearchIntent for backward compatibility
        intent = SearchIntent(
            product_name=criteria.product_name,
            brand=criteria.brand,
            category=criteria.category,
            sub_category=criteria.sub_category,
            size=criteria.size,
            strain_type=criteria.strain_type,
            min_price=criteria.min_price,
            max_price=criteria.max_price,
            effects=criteria.effects
        )
        
        # Use existing comprehensive search
        return await self._comprehensive_search(intent, criteria.product_name or "")
        
    async def process_query(self, message: str, context: Optional[Dict] = None, 
                          session_id: Optional[str] = None, personality: Optional[str] = None) -> Dict:
        """
        Process user query with search-first approach
        
        1. Determine query type using LLM
        2. Execute appropriate database query
        3. Generate response based on results
        """
        
        logger.info(f"Processing query: {message}")
        
        # Get conversation context if session provided
        context = None
        if session_id:
            context = await self.context_manager.get_context(session_id, customer_id)
            logger.info(f"Loaded context with {len(context.last_products_shown)} last products")
            if context.last_products_shown:
                logger.info(f"Last products shown: {[p.get('product_name', 'Unknown') for p in context.last_products_shown[:3]]}")
        
        # Use LLM to determine if this is a greeting/identity question (NO HARDCODING!)
        # But first check for obvious product keywords to bypass greeting check
        product_keywords = ['flower', 'sativa', 'indica', 'hybrid', 'thc', 'cbd', 'edible', 'vape', 
                          'strain', 'cannabis', 'weed', 'bud', 'pre-roll', 'joint', 'gram', 'ounce',
                          'show me', 'i want', 'looking for', 'need', 'price', 'under', 'over',
                          'divvy', 'pink', 'kush', 'roll', 'eighth', 'quarter', 'half', 
                          'gummy', 'chocolate', 'drink', 'oil', 'capsule', 'topical',
                          'find', 'get', 'buy', 'purchase', 'cart', 'add']
        message_lower = message.lower()
        has_product_keywords = any(keyword in message_lower for keyword in product_keywords)
        
        # FAST PATH OPTIMIZATION: Skip all LLM calls except search extraction for obvious product queries
        if has_product_keywords:
            logger.info("FAST PATH: Product keywords detected, skipping greeting/intent/type detection")
            
            # Go straight to search extraction (1 LLM call instead of 5)
            search_intent = self._extract_search_intent(message)
            logger.info(f"Fast path extracted: {search_intent}")
            
            # Search database
            search_results = await self._comprehensive_search(search_intent, message)
            logger.info(f"Fast path found {len(search_results)} products")
            
            # Generate simple response without LLM (save another call!)
            if search_results:
                if len(search_results) <= 5:
                    response = f"I found {len(search_results)} products matching your search:"
                elif len(search_results) <= 20:
                    response = f"I found {len(search_results)} products. Here are the top results:"
                else:
                    response = f"I found {len(search_results)} products. Here are some top matches:"
            else:
                response = f"I couldn't find exact matches for '{message}'. Would you like to see similar products or browse our categories?"
            
            # Generate quick actions
            quick_actions = self._generate_quick_actions(search_results, message)
            
            # Determine how many products to return
            if len(search_results) <= 20:
                products_to_return = search_results
            else:
                products_to_return = search_results[:10]
            
            logger.info(f"Fast path returning {len(products_to_return)} products")
            
            return {
                "message": response,
                "products": products_to_return,
                "intent": "search",
                "search_performed": True,
                "search_intent": {
                    "product_name": search_intent.product_name,
                    "brand": search_intent.brand,
                    "category": search_intent.category,
                    "strain_type": search_intent.strain_type
                },
                "total_found": len(search_results),
                "quick_actions": quick_actions
            }
        
        # SLOW PATH: Original flow with all checks for non-product queries
        if self.llm and not has_product_keywords:
            # Only check for greeting if no product keywords found
            greeting_check_prompt = self.prompt_manager.get_prompt("is_greeting", message=message)
            greeting_response = self.llm(greeting_check_prompt, max_tokens=10, temperature=0, echo=False)
            
            if greeting_response and greeting_response.get('choices'):
                is_greeting_text = greeting_response['choices'][0]['text'].strip().lower()
                logger.info(f"Greeting check response for '{message}': '{is_greeting_text}'")
                
                if 'yes' in is_greeting_text:
                    logger.info(f"LLM detected greeting/identity question: '{message}'")
                    
                    # Get personality from context or use default
                    from services.personality_manager import get_personality_manager
                    personality_manager = get_personality_manager()
                    
                    personality_id = context.personality if context and hasattr(context, 'personality') else 'zac'
                    personality = personality_manager.get_personality(personality_id)
                    
                    if not personality:
                        personality = personality_manager.get_default_personality('budtender')
                    
                    # Use personality-specific greeting prompt
                    if personality:
                        personality_prompt = personality.greeting_prompt
                    else:
                        personality_prompt = "You are a friendly and knowledgeable cannabis consultant"
                    
                    response_prompt = self.prompt_manager.get_prompt("general_conversation",
                                                                    personality=personality_prompt,
                                                                    conversation_text="",
                                                                    message=message)
                    
                    llm_response = self.llm(response_prompt, max_tokens=100, temperature=0.7, echo=False)
                    
                    if llm_response and llm_response.get('choices'):
                        response = {
                            "message": llm_response['choices'][0]['text'].strip(),
                            "products": [],
                            "intent": "greeting",
                            "search_performed": False
                        }
                        
                        # Update context
                        if context:
                            await self.context_manager.update_context(session_id, {
                                'intent': 'greeting',
                                'message': {'user': message, 'ai': response['message']}
                            })
                        return response
        
        # Use LLM to understand if this is a similarity request
        if context:
            similarity_check = await self.context_manager.understand_similarity_request(message, context)
            if similarity_check.get("is_similar"):
                logger.info(f"LLM detected similarity request for: {similarity_check['similar_to'].get('product_name') if similarity_check['similar_to'] else 'unknown'}")
                return await self._handle_similarity_request(similarity_check, session_id)
        
        # Use LLM to understand if this is a reference to previously shown products
        if context and context.last_products_shown:
            reference_result = await self.context_manager.understand_reference_semantically(message, context)
            if reference_result.get('is_reference'):
                logger.info(f"LLM detected reference (confidence: {reference_result.get('confidence', 0):.2f}): '{message}'")
                return await self._handle_reference(message, context, session_id, reference_result)
            else:
                logger.info(f"LLM determined not a reference: '{message}', Has {len(context.last_products_shown)} products in context")
        
        # First check if it's a greeting using intent detection (for more complex greetings)
        if self.llm:
            try:
                # Build conversation context string
                conv_context = "New conversation"
                if context and context.message_history:
                    conv_context = "Recent messages:\n"
                    for msg in context.message_history[-3:]:  # Last 3 messages
                        conv_context += f"User: {msg.get('user', '')}\n"
                        if context.last_products_shown:
                            conv_context += f"(Products were shown)\n"
                
                intent_prompt = self.prompt_manager.get_prompt("intent_detection", 
                                                              conversation_context=conv_context,
                                                              message=message)
                intent_response = self.llm(intent_prompt, max_tokens=20, temperature=0.1, echo=False)
                if intent_response and intent_response.get('choices'):
                    detected_intent = intent_response['choices'][0]['text'].strip().lower()
                    # Clean up the response - get only the first word
                    detected_intent = detected_intent.split()[0] if detected_intent else ""
                    logger.info(f"Detected intent: {detected_intent}")
                    
                    # Check if it's actually a valid intent
                    if detected_intent in ["greeting", "search", "purchase", "question", "recommendation"]:
                        if detected_intent == "greeting":
                            # Handle greeting
                            greeting_prompt = self.prompt_manager.get_prompt("greeting_response",
                                                                            personality="You are a friendly budtender",
                                                                            customer_context="Customer",
                                                                            message=message)
                            greeting_response = self.llm(greeting_prompt, max_tokens=200, temperature=0.7, echo=False)
                            if greeting_response and greeting_response.get('choices'):
                                return {
                                    "message": greeting_response['choices'][0]['text'].strip(),
                                    "products": [],
                                    "intent": "greeting",
                                    "search_performed": False
                                }
            except Exception as e:
                logger.warning(f"Intent detection failed: {e}")
        
        # Use LLM to determine query type
        query_type = "product_search"  # default
        if self.llm:
            try:
                type_prompt = self.prompt_manager.get_prompt("query_type", message=message)
                type_response = self.llm(type_prompt, max_tokens=20, temperature=0.1, echo=False)
                if type_response and type_response.get('choices'):
                    detected_type = type_response['choices'][0]['text'].strip().lower()
                    if detected_type in ['brands_list', 'categories_list', 'analytics_query', 'product_search']:
                        query_type = detected_type
                        logger.info(f"Detected query type: {query_type}")
            except Exception as e:
                logger.warning(f"Query type detection failed: {e}, defaulting to product_search")
        
        # Route to appropriate handler
        if query_type == "brands_list":
            return await self._get_brands_list()
        elif query_type == "categories_list":
            return await self._get_categories_list()
        elif query_type == "analytics_query":
            return await self._handle_analytics_query(message)
        
        # Regular product search
        # Step 1: Extract search intent
        search_intent = self._extract_search_intent(message)
        logger.info(f"Extracted intent: {search_intent}")
        
        # Step 2: ALWAYS search database (multiple strategies)
        logger.info(f"About to search database with intent: product={search_intent.product_name}, category={search_intent.category}, strain={search_intent.strain_type}")
        search_results = await self._comprehensive_search(search_intent, message)
        logger.info(f"Search returned {len(search_results)} products")
        if search_results:
            logger.info(f"Sample results: {[p.get('product_name') for p in search_results[:3]]}")
        else:
            logger.warning(f"No products found for query: {message}")
        
        # Step 3: Generate response based ONLY on actual results
        response = self._generate_factual_response(message, search_results, search_intent)
        
        # Step 4: Generate quick actions based on search results
        quick_actions = self._generate_quick_actions(search_results, message)
        
        # Step 5: Determine how many products to return with images
        # If 20 or less total results, return all with images
        # Otherwise, return top 10 for performance
        products_to_return = []
        if len(search_results) <= 20:
            # Return all products with full details including images
            products_to_return = search_results
            logger.info(f"Returning all {len(search_results)} products with images")
        else:
            # Return only top 10 when there are many results
            products_to_return = search_results[:10]
            logger.info(f"Returning top 10 of {len(search_results)} products")
        
        # Update context with search results
        if context and session_id:
            await self.context_manager.update_context(session_id, {
                'products_shown': products_to_return,
                'intent': 'search',
                'search_criteria': search_intent.__dict__,
                'message': {'user': message, 'ai': response}
            })
        
        return {
            "message": response,
            "products": products_to_return,
            "quick_actions": quick_actions,
            "search_performed": True,
            "search_intent": search_intent.__dict__,
            "total_found": len(search_results),
            "includes_images": len(search_results) <= 20  # Flag to indicate images are included
        }
    
    async def _get_brands_list(self) -> Dict:
        """Get list of all available brands"""
        if not self.db_pool:
            return {"message": "Unable to fetch brands at this time.", "products": []}
        
        async with self.db_pool.acquire() as conn:
            query = """
                SELECT DISTINCT brand, COUNT(*) as product_count
                FROM products
                WHERE brand IS NOT NULL AND brand != ''
                GROUP BY brand
                ORDER BY brand
                LIMIT 50
            """
            results = await conn.fetch(query)
            
            if results:
                brands = [f"{row['brand']} ({row['product_count']} products)" for row in results]
                response = f"We carry {len(results)} brands including:\n\n"
                response += "\n".join(brands[:20])
                if len(results) > 20:
                    response += f"\n\n...and {len(results) - 20} more brands."
                response += "\n\nWhich brand interests you?"
            else:
                response = "Unable to fetch brand list. Please try searching for specific products."
        
        return {
            "message": response,
            "products": [],
            "quick_actions": [
                {"label": "Search products", "value": "show me all products", "type": "search"},
                {"label": "Popular items", "value": "what's popular", "type": "popular"}
            ],
            "search_performed": True,
            "total_found": 0
        }
    
    async def _handle_analytics_query(self, message: str) -> Dict:
        """Handle analytical queries - use LLM to understand and execute"""
        if not self.db_pool:
            return {"message": "Unable to fetch analytics at this time.", "products": []}
        
        # Use LLM to extract what they're looking for
        search_terms = ""
        if self.llm:
            prompt = self.prompt_manager.get_prompt("extract_search_terms", message=message)
            response = self.llm(prompt, max_tokens=300, temperature=0.1, echo=False)
            if response and response.get('choices'):
                search_terms = response['choices'][0]['text'].strip()
        
        # For analytics, just search and sort by THC
        # Let the database and sorting handle finding the highest THC
        async with self.db_pool.acquire() as conn:
            query = """
                SELECT * FROM products 
                WHERE LOWER(product_name) LIKE $1
                OR LOWER(category) LIKE $1
                OR LOWER(sub_category) LIKE $1
                ORDER BY thc_max_percent DESC NULLS LAST
                LIMIT 10
            """
            
            results = await conn.fetch(query, f"%{search_terms.lower()}%")
            
            if results:
                top_products = [self._format_product(dict(r)) for r in results[:5]]
                
                # Generate response using the actual data
                if top_products and top_products[0].get('thc', 0) > 0:
                    max_thc = top_products[0]['thc']
                    response = f"The highest THC in {search_terms} is {max_thc}%.\n\nTop options:\n"
                    for i, p in enumerate(top_products, 1):
                        response += f"{i}. {p['product_name']} - {p['thc']}% THC (${p['price']:.2f})\n"
                else:
                    response = f"Here are {search_terms} products:\n"
                    for i, p in enumerate(top_products, 1):
                        response += f"{i}. {p['product_name']} (${p['price']:.2f})\n"
                
                return {
                    "message": response,
                    "products": top_products,
                    "search_performed": True,
                    "total_found": len(results)
                }
        
        return {
            "message": f"I couldn't find specific information about {message}. Try asking about specific product categories.",
            "products": [],
            "search_performed": True
        }
    
    async def _get_categories_list(self) -> Dict:
        """Get list of all available categories"""
        if not self.db_pool:
            return {"message": "Unable to fetch categories at this time.", "products": []}
        
        async with self.db_pool.acquire() as conn:
            query = """
                SELECT category, sub_category, COUNT(*) as product_count
                FROM products
                WHERE category IS NOT NULL
                GROUP BY category, sub_category
                ORDER BY category, sub_category
            """
            results = await conn.fetch(query)
            
            if results:
                categories = {}
                for row in results:
                    cat = row['category']
                    if cat not in categories:
                        categories[cat] = []
                    if row['sub_category']:
                        categories[cat].append(f"{row['sub_category']} ({row['product_count']})")
                
                response = f"We have {len(categories)} main categories:\n\n"
                for cat, subs in list(categories.items())[:10]:
                    response += f"**{cat}**\n"
                    if subs:
                        response += "  • " + "\n  • ".join(subs[:3])
                        if len(subs) > 3:
                            response += f"\n  • ...and {len(subs) - 3} more"
                    response += "\n\n"
                    
                response += "Which category would you like to explore?"
            else:
                response = "Unable to fetch category list. Please try searching for specific products."
        
        return {
            "message": response,
            "products": [],
            "quick_actions": [
                {"label": "Flower", "value": "show me flower products", "type": "category"},
                {"label": "Edibles", "value": "show me edibles", "type": "category"},
                {"label": "Vapes", "value": "show me vapes", "type": "category"}
            ],
            "search_performed": True,
            "total_found": 0
        }
    
    def _generate_quick_actions(self, products: List[Dict], query: str) -> List[Dict]:
        """Generate contextual quick actions based on search results"""
        quick_actions = []
        
        if not products:
            return [
                {"label": "Browse categories", "value": "show me categories", "type": "browse"},
                {"label": "Search again", "value": "search for something else", "type": "search"}
            ]
        
        # Check for multiple sizes
        sizes = set()
        strain_types = set()
        categories = set()
        
        for p in products[:20]:  # Analyze top 20 results
            if p.get('size'):
                sizes.add(p['size'])
            if p.get('strain_type'):
                strain_types.add(p['strain_type'])
            if p.get('category'):
                categories.add(p['category'])
        
        # If multiple sizes available, add size options
        if len(sizes) > 1:
            sorted_sizes = sorted(sizes)[:5]  # Top 5 sizes
            for size in sorted_sizes:
                quick_actions.append({
                    "label": f"Show {size}",
                    "value": f"show me {size} size",
                    "type": "filter_size",
                    "data": {"size": size}
                })
        
        # If multiple strain types, add strain filters
        if len(strain_types) > 1:
            for strain_type in sorted(strain_types)[:3]:
                quick_actions.append({
                    "label": f"{strain_type} only",
                    "value": f"show only {strain_type} strains",
                    "type": "filter_strain",
                    "data": {"strain_type": strain_type}
                })
        
        # Add "tell me more" for top product
        if products:
            top_product = products[0]
            quick_actions.append({
                "label": f"More about {top_product['product_name'][:20]}",
                "value": f"tell me more about {top_product['product_name']}",
                "type": "product_details",
                "data": {"product_id": top_product['id']}
            })
            
            # Add to cart action
            quick_actions.append({
                "label": f"Add {top_product['size']} to cart",
                "value": f"add {top_product['product_name']} to cart",
                "type": "add_to_cart",
                "data": {"product_id": top_product['id'], "size": top_product['size']}
            })
        
        # If asking about specific product, show size options
        if 'tell me more' in query.lower() and len(products) > 1:
            base_name = products[0]['product_name'].split()[0]
            same_product = [p for p in products if p['product_name'].startswith(base_name)]
            if len(same_product) > 1:
                for p in same_product[:4]:
                    quick_actions.append({
                        "label": f"Select {p['size']}",
                        "value": f"I want the {p['size']} size",
                        "type": "select_size",
                        "data": {
                            "product_id": p['id'],
                            "size": p['size'],
                            "price": p['price'],
                            "image": p.get('image')
                        }
                    })
        
        return quick_actions[:6]  # Limit to 6 quick actions
    
    def _extract_search_intent(self, message: str) -> SearchIntent:
        """
        Use FastExtractor for sub-500ms extraction
        """
        
        intent = SearchIntent()
        
        # Try fast extractor first for speed
        try:
            fast_extractor = get_fast_extractor()
            if fast_extractor and fast_extractor.model:
                # Use search_extraction_enhanced prompt
                prompt = self.prompt_manager.get_prompt("search_extraction_enhanced", query=message)
                
                # Fast extraction with minimal tokens
                json_str = fast_extractor.extract(prompt, max_tokens=150)
                
                if json_str:
                    
                    # Clean up common LLM response prefixes
                    if json_str.startswith("Output:"):
                        json_str = json_str[7:].strip()
                    if json_str.startswith("```json"):
                        json_str = json_str[7:]
                    if json_str.endswith("```"):
                        json_str = json_str[:-3]
                    json_str = json_str.strip()
                    
                    # Try to extract JSON from the response (in case there's extra text)
                    import re
                    json_match = re.search(r'\{.*?\}', json_str, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(0)
                    
                    # Try to parse JSON response
                    try:
                        import json
                        extracted = json.loads(json_str)
                        
                        # Map extracted fields to SearchIntent
                        if extracted.get('product_name'):
                            intent.product_name = extracted['product_name']
                        if extracted.get('brand'):
                            intent.brand = extracted['brand']
                        if extracted.get('category'):
                            intent.category = extracted['category']
                        if extracted.get('sub_category'):
                            intent.sub_category = extracted['sub_category']
                        if extracted.get('size'):
                            # Convert common size formats to grams
                            size = extracted['size'].lower()
                            if '1/2' in size or 'half' in size:
                                if 'oz' in size or 'ounce' in size:
                                    intent.size = '14g'
                                else:
                                    intent.size = extracted['size']
                            elif '1/4' in size or 'quarter' in size:
                                intent.size = '7g'
                            elif '1/8' in size or 'eighth' in size:
                                intent.size = '3.5g'
                            elif 'ounce' in size or 'oz' in size:
                                intent.size = '28g'
                            else:
                                intent.size = extracted['size']
                        if extracted.get('strain_type'):
                            intent.strain_type = extracted['strain_type']
                        if extracted.get('min_price'):
                            intent.min_price = extracted['min_price']
                        if extracted.get('max_price'):
                            intent.max_price = extracted['max_price']
                        if extracted.get('special_type'):
                            intent.special_type = extracted['special_type']
                            
                        logger.info(f"Extracted intent: {intent}")
                        
                    except json.JSONDecodeError as e:
                        # Fallback to simple extraction if JSON parse fails
                        logger.warning(f"Failed to parse JSON: {json_str} - {e}")
                    
        except Exception as e:
            logger.info(f"Fast extractor not available or failed: {e}, falling back to regular LLM")
            
        # Fallback to regular LLM if fast extractor didn't work
        if not intent.product_name and not intent.category and self.llm:
            try:
                # Use search_extraction_enhanced prompt with regular LLM
                prompt = self.prompt_manager.get_prompt("search_extraction_enhanced", query=message)
                
                response = self.llm(prompt, max_tokens=200, temperature=0.1, echo=False)
                if response and response.get('choices'):
                    json_str = response['choices'][0]['text'].strip()
                    
                    # Clean up common LLM response prefixes
                    if json_str.startswith("Output:"):
                        json_str = json_str[7:].strip()
                    if json_str.startswith("```json"):
                        json_str = json_str[7:]
                    if json_str.endswith("```"):
                        json_str = json_str[:-3]
                    json_str = json_str.strip()
                    
                    # Try to extract JSON from the response
                    import re
                    json_match = re.search(r'\{.*?\}', json_str, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(0)
                    
                    # Parse JSON response
                    try:
                        import json
                        extracted = json.loads(json_str)
                        
                        # Map extracted fields to SearchIntent
                        if extracted.get('product_name'):
                            intent.product_name = extracted['product_name']
                        if extracted.get('brand'):
                            intent.brand = extracted['brand']
                        if extracted.get('category'):
                            intent.category = extracted['category']
                        if extracted.get('sub_category'):
                            intent.sub_category = extracted['sub_category']
                        if extracted.get('size'):
                            intent.size = extracted['size']
                        if extracted.get('strain_type'):
                            intent.strain_type = extracted['strain_type']
                        if extracted.get('min_price'):
                            intent.min_price = extracted['min_price']
                        if extracted.get('max_price'):
                            intent.max_price = extracted['max_price']
                        if extracted.get('effects'):
                            intent.effects = extracted['effects']
                        if extracted.get('special_type'):
                            intent.special_type = extracted['special_type']
                            
                    except Exception as e:
                        logger.warning(f"Failed to parse regular LLM JSON: {e}")
                        
            except Exception as e:
                logger.warning(f"Regular LLM extraction failed: {e}")
        
        # Final fallback to pattern matching if nothing extracted
        if not intent.product_name and not intent.category and not intent.brand:
            message_lower = message.lower()
            
            # Check for known brands
            known_brands = ['divvy', 'general admission', 'spot', 'no future', 'versus', 'smokiez', 
                          'homestead', 'snicklefritz', 'emprise', 'station house']
            for brand in known_brands:
                if brand in message_lower:
                    intent.brand = brand.title()
                    # Remove brand from product name search
                    message = message.replace(brand, '').replace(brand.title(), '').replace(brand.upper(), '')
                    break
                    
            # Check for product categories
            if 'pre-roll' in message_lower or 'preroll' in message_lower or 'joint' in message_lower:
                intent.category = 'Flower'
                intent.sub_category = 'Pre-Rolls'
            elif 'flower' in message_lower or 'bud' in message_lower:
                intent.category = 'Flower'
                intent.sub_category = 'Dried Flower'
            
            # Check for strain types
            if 'sativa' in message_lower:
                intent.strain_type = 'Sativa'
            elif 'indica' in message_lower:
                intent.strain_type = 'Indica'
            elif 'hybrid' in message_lower:
                intent.strain_type = 'Hybrid'
            
            # Extract specific product names (remove common words)
            stop_words = ['i', 'want', 'need', 'looking', 'for', 'show', 'me', 'find', 'get', 'by']
            words = message.lower().split()
            product_words = [w for w in words if w not in stop_words and w not in known_brands 
                           and w not in ['sativa', 'indica', 'hybrid', 'pre-roll', 'preroll']]
            
            if product_words and not intent.brand and not intent.category:
                intent.product_name = ' '.join(product_words)
            elif 'roll' in message_lower and 'up' in message_lower:
                intent.product_name = 'roll up'
        
        return intent
    
    async def _comprehensive_search(self, intent: SearchIntent, original_message: str) -> List[Dict]:
        """
        Search database with multiple strategies
        Never give up - try different approaches
        """
        
        logger.info(f"Starting comprehensive search for: {original_message}")
        logger.info(f"DB Pool available: {self.db_pool is not None}")
        
        if not self.db_pool:
            logger.error("No database connection - cannot search products")
            return []
        
        all_results = []
        
        async with self.db_pool.acquire() as conn:
            # Strategy 0: Brand + Special Type search (highest priority)
            if intent.brand or intent.special_type:
                conditions = []
                params = []
                param_count = 0
                
                if intent.brand:
                    param_count += 1
                    conditions.append(f"LOWER(brand) LIKE ${param_count}")
                    params.append(f"%{intent.brand.lower()}%")
                
                if intent.special_type:
                    param_count += 1
                    # For infused products, check product name
                    conditions.append(f"LOWER(product_name) LIKE ${param_count}")
                    params.append(f"%{intent.special_type.lower()}%")
                
                if intent.size:
                    param_count += 1
                    # Handle size variations (1g might be stored as 1x1g)
                    size_str = intent.size
                    if size_str == "1g":
                        conditions.append(f"(size = '1g' OR size = '1x1g')")
                        # No param needed since we hardcoded the values
                        param_count -= 1
                    else:
                        conditions.append(f"(size = ${param_count} OR size LIKE ${param_count})")
                        params.append(size_str)
                
                if conditions:
                    query = f"""
                        SELECT * FROM products 
                        WHERE {' AND '.join(conditions)}
                        ORDER BY unit_price ASC
                        LIMIT 100
                    """
                    results = await conn.fetch(query, *params)
                    if results:
                        all_results.extend([dict(r) for r in results])
                        logger.info(f"Brand/special search found {len(results)} results")
            
            # Strategy 1: Exact product name search
            if intent.product_name and not all_results:
                # Clean up any malformed LLM responses
                product_name = str(intent.product_name).strip()
                # Remove list formatting if present
                if product_name.startswith('[') and product_name.endswith(']'):
                    product_name = product_name[1:-1].strip().strip("'\"")
                intent.product_name = product_name
                
                # First, try to find exact matches with sub_sub_category consideration
                # Split search term to identify potential sub_sub_category terms
                words = product_name.lower().split()
                
                # Try combined search - product name + sub_sub_category
                if len(words) > 1:
                    # Last word might be sub_sub_category indicator
                    potential_product = ' '.join(words[:-1])
                    potential_sub_cat = words[-1]
                    
                    query = """
                        SELECT * FROM products 
                        WHERE (
                            LOWER(product_name) LIKE $1 
                            AND (LOWER(sub_sub_category) LIKE $2 OR LOWER(sub_category) LIKE $2)
                        )
                        OR (
                            LOWER(product_name) LIKE $3
                        )
                        ORDER BY 
                            CASE 
                                WHEN LOWER(product_name) LIKE $1 AND LOWER(sub_sub_category) LIKE $2 THEN 1
                                WHEN LOWER(product_name) LIKE $1 AND LOWER(sub_category) LIKE $2 THEN 2
                                ELSE 3
                            END,
                            unit_price ASC
                        LIMIT 50
                    """
                    
                    results = await conn.fetch(
                        query,
                        f"%{potential_product}%",
                        f"%{potential_sub_cat}%",
                        f"%{product_name}%"
                    )
                    
                    if results:
                        all_results.extend([dict(r) for r in results])
                
                # Check if searching for a brand specifically (e.g., "divvy products")
                if 'products' in product_name.lower():
                    brand_name = product_name.lower().replace('products', '').strip()
                    # Search specifically by brand/supplier
                    query = """
                        SELECT * FROM products 
                        WHERE LOWER(brand) LIKE $1 
                        OR LOWER(supplier_name) LIKE $1
                        ORDER BY unit_price ASC
                        LIMIT 100
                    """
                    results = await conn.fetch(query, f"%{brand_name}%")
                    all_results.extend([dict(r) for r in results])
                
                    
            if intent.product_name and not all_results:
                # Check if search includes both brand/supplier and product (e.g., "pure sunfarms pink kush")
                words = intent.product_name.lower().split()
                if len(words) > 1:
                    # Try searching for combination of brand/supplier + product
                    query = """
                        SELECT * FROM products 
                        WHERE (LOWER(brand) LIKE $1 AND LOWER(product_name) LIKE $2)
                        OR (LOWER(supplier_name) LIKE $1 AND LOWER(product_name) LIKE $2)
                        OR (LOWER(product_name) LIKE $3)
                        ORDER BY 
                            CASE 
                                WHEN LOWER(brand) LIKE $1 AND LOWER(product_name) LIKE $2 THEN 1 
                                WHEN LOWER(supplier_name) LIKE $1 AND LOWER(product_name) LIKE $2 THEN 2
                                ELSE 3 
                            END,
                            unit_price ASC
                        LIMIT 50
                    """
                    # Try first word(s) as brand/supplier, rest as product
                    potential_brand = words[0]
                    if len(words) > 2:
                        # Could be multi-word brand like "Pure Sunfarms"
                        potential_brand = ' '.join(words[:2])
                        potential_product = ' '.join(words[2:])
                    else:
                        potential_product = ' '.join(words[1:])
                    full_search = intent.product_name.lower()
                    
                    results = await conn.fetch(
                        query, 
                        f"%{potential_brand}%",
                        f"%{potential_product}%", 
                        f"%{full_search}%"
                    )
                    all_results.extend([dict(r) for r in results])
                
                # Also do regular search including supplier_name and sub_sub_category
                query = """
                    SELECT * FROM products 
                    WHERE LOWER(product_name) LIKE $1
                    OR LOWER(brand) LIKE $1
                    OR LOWER(supplier_name) LIKE $1
                    OR LOWER(street_name) LIKE $1
                    OR LOWER(sub_sub_category) LIKE $1
                    OR LOWER(sub_category) LIKE $1
                    ORDER BY 
                        CASE 
                            WHEN LOWER(product_name) LIKE $1 THEN 1
                            WHEN LOWER(brand) LIKE $1 THEN 2
                            ELSE 3
                        END,
                        unit_price ASC
                    LIMIT 50
                """
                search_term = f"%{intent.product_name.lower()}%"
                results = await conn.fetch(query, search_term)
                all_results.extend([dict(r) for r in results])
                
                # Strategy 2: Word-by-word search if no results
                if not all_results:
                    words = intent.product_name.split()
                    for word in words:
                        if len(word) > 2:
                            results = await conn.fetch(query, f"%{word.lower()}%")
                            all_results.extend([dict(r) for r in results])
            
            # Strategy 3: Category + subcategory + strain + price search
            if intent.category or intent.sub_category or intent.strain_type or intent.min_price or intent.max_price:
                conditions = []
                params = []
                param_count = 0
                
                if intent.category:
                    param_count += 1
                    conditions.append(f"category = ${param_count}")
                    params.append(intent.category)
                
                if intent.sub_category:
                    param_count += 1
                    conditions.append(f"sub_category = ${param_count}")
                    params.append(intent.sub_category)
                
                if intent.product_name:
                    param_count += 1
                    conditions.append(f"LOWER(product_name) LIKE ${param_count}")
                    params.append(f"%{intent.product_name.lower()}%")
                
                if intent.strain_type:
                    param_count += 1
                    # Check plant_type field for strain type (Sativa, Indica, Hybrid) - DB column is plant_type
                    conditions.append(f"(LOWER(plant_type) LIKE ${param_count} OR LOWER(product_name) LIKE ${param_count})")
                    params.append(f"%{intent.strain_type.lower()}%")
                
                if intent.min_price:
                    param_count += 1
                    conditions.append(f"unit_price >= ${param_count}")
                    params.append(float(intent.min_price))
                
                if intent.max_price:
                    param_count += 1
                    conditions.append(f"unit_price <= ${param_count}")
                    params.append(float(intent.max_price))
                
                if conditions:
                    query = f"""
                        SELECT * FROM products 
                        WHERE {' AND '.join(conditions)}
                        ORDER BY unit_price ASC
                        LIMIT 100
                    """
                    logger.info(f"Strategy 3 query: {query}")
                    logger.info(f"Strategy 3 params: {params}")
                    results = await conn.fetch(query, *params)
                    logger.info(f"Strategy 3 found {len(results)} results")
                    all_results.extend([dict(r) for r in results])
            
            # Strategy 4: Fuzzy search on individual important words
            if not all_results:
                important_words = self._extract_important_words(original_message)
                for word in important_words:
                    query = """
                        SELECT * FROM products 
                        WHERE LOWER(product_name) LIKE $1
                        OR LOWER(brand) LIKE $1
                        LIMIT 20
                    """
                    results = await conn.fetch(query, f"%{word}%")
                    all_results.extend([dict(r) for r in results])
        
        # Deduplicate results
        seen = set()
        unique_results = []
        for r in all_results:
            if r['id'] not in seen:
                seen.add(r['id'])
                unique_results.append(self._format_product(r))
        
        # Sort by relevance (products with exact name matches first)
        if intent.product_name:
            unique_results.sort(
                key=lambda x: (
                    intent.product_name.lower() not in x.get('product_name', '').lower(),
                    x.get('price', 999999)
                )
            )
        
        return unique_results
    
    def _extract_important_words(self, message: str) -> List[str]:
        """Extract important words for search"""
        
        # Remove common words
        stop_words = {'do', 'you', 'have', 'any', 'the', 'a', 'an', 'is', 'are', 
                      'can', 'i', 'get', 'some', 'give', 'me', 'want', 'need',
                      'looking', 'for', 'please', 'pls', 'hey', 'hi', 'hello'}
        
        words = message.lower().split()
        important = []
        
        for word in words:
            # Clean punctuation
            word = re.sub(r'[^\w\s]', '', word)
            
            # Keep if not a stop word and has substance
            if word and word not in stop_words and len(word) > 2:
                important.append(word)
        
        return important
    
    def _format_product(self, product: Dict) -> Dict:
        """Format product for response - using ALL source-of-truth columns"""
        formatted = {
            'id': product.get('id'),
            'product_name': product.get('product_name', 'Unknown'),
            'brand': product.get('brand', ''),
            'supplier_name': product.get('supplier_name', ''),
            'category': product.get('category', ''),
            'sub_category': product.get('sub_category', ''),
            'sub_sub_category': product.get('sub_sub_category', ''),
            'size': product.get('size', ''),
            'price': float(product.get('unit_price', 0)),
            'thc': float(product.get('thc_max_percent', 0)),
            'cbd': float(product.get('cbd_max_percent', 0)),
            'strain_type': product.get('plant_type', ''),  # Map strain_type to plant_type (no strain_type column in DB)
            'image': product.get('image_url', ''),
            'image_url': product.get('image_url', ''),  # Add image_url for API compatibility
            'in_stock': True  # Assume in stock if in database
        }
        
        # Add ALL the source-of-truth columns (only if they have values)
        truth_columns = {
            'short_description': product.get('product_short_description') or product.get('short_description'),
            'long_description': product.get('product_long_description') or product.get('long_description'),
            'thc_min': product.get('minimum_thc_content') or product.get('thc_min'),
            'thc_max': product.get('maximum_thc_content') or product.get('thc_max'),
            'thc_per_unit': product.get('thc_content_per_unit'),
            'thc_per_volume': product.get('thc_content_per_volume'),
            'cbd_min': product.get('minimum_cbd_content') or product.get('cbd_min'),
            'cbd_max': product.get('maximum_cbd_content') or product.get('cbd_max'),
            'cbd_per_unit': product.get('cbd_content_per_unit'),
            'cbd_per_volume': product.get('cbd_content_per_volume'),
            'dried_flower_equivalency': product.get('dried_flower_cannabis_equivalency'),
            'plant_type': product.get('plant_type'),
            'terpenes': product.get('terpenes'),
            'growing_method': product.get('growingmethod') or product.get('growing_method'),
            'items_per_pack': product.get('number_of_items_in_a_retail_pack'),
            'food_allergens': product.get('food_allergens'),
            'ingredients': product.get('ingredients'),
            'street_name': product.get('street_name'),
            'grow_medium': product.get('grow_medium'),
            'grow_method': product.get('grow_method'),
            'grow_region': product.get('grow_region'),
            'drying_method': product.get('drying_method'),
            'trimming_method': product.get('trimming_method'),
            'extraction_process': product.get('extraction_process'),
            'carrier_oil': product.get('carrier_oil'),
            'heating_element_type': product.get('heating_element_type'),
            'battery_type': product.get('battery_type'),
            'rechargeable_battery': product.get('rechargeable_battery'),
            'removable_battery': product.get('removable_battery'),
            'replacement_parts_available': product.get('replacement_parts_available'),
            'temperature_control': product.get('temperature_control'),
            'temperature_display': product.get('temperature_display'),
            'compatibility': product.get('compatibility'),
            'net_weight': product.get('net_weight'),
            'craft': product.get('craft')
        }
        
        # Only include columns that have actual values (not None, not empty, not 0)
        for key, value in truth_columns.items():
            if value and str(value).strip() and str(value).lower() not in ['none', 'null', 'nan', '0', '0.0']:
                # Skip numeric fields that are 0 (likely defaults)
                if isinstance(value, (int, float)) and value == 0:
                    continue
                formatted[key] = value
        
        # Build comprehensive description from available data
        descriptions = []
        if formatted.get('short_description'):
            descriptions.append(formatted['short_description'])
        if formatted.get('long_description'):
            descriptions.append(formatted['long_description'])
        
        # Combine descriptions if both exist, otherwise use what's available
        if descriptions:
            formatted['description'] = ' '.join(descriptions)
        else:
            formatted['description'] = ''
        
        return formatted
    
    def _generate_factual_response(self, query: str, products: List[Dict], intent: SearchIntent) -> str:
        """
        Generate response based ONLY on actual search results
        Use LLM to generate helpful responses with filtering suggestions for large result sets
        """
        
        # If we have an LLM, use it for better responses
        if self.llm and products:
            # Prepare products context
            products_context = ""
            if len(products) <= 10:
                # Show all products
                for i, p in enumerate(products, 1):
                    products_context += f"{i}. {p['product_name']} - ${p['price']:.2f}"
                    if p.get('size'):
                        products_context += f" ({p['size']})"
                    if p.get('brand'):
                        products_context += f" by {p['brand']}"
                    products_context += "\n"
            else:
                # Show top products and indicate there are more
                for i, p in enumerate(products[:5], 1):
                    products_context += f"{i}. {p['product_name']} - ${p['price']:.2f}"
                    if p.get('size'):
                        products_context += f" ({p['size']})"
                    if p.get('brand'):
                        products_context += f" by {p['brand']}"
                    products_context += "\n"
                products_context += f"\n...and {len(products) - 5} more products available"
            
            # Use the product_search_response prompt
            try:
                response_prompt = self.prompt_manager.get_prompt(
                    "product_search_response",
                    personality="You are a helpful budtender",
                    message=query,
                    search_performed="Yes",
                    products_context=products_context,
                    result_count=len(products)
                )
                
                # Increase max_tokens for unlimited response
                llm_response = self.llm(response_prompt, max_tokens=500, temperature=0.7, echo=False)
                if llm_response and llm_response.get('choices'):
                    response_text = llm_response['choices'][0]['text'].strip()
                    # Clean up response - remove any extra sections or recommendations
                    # Look for first quote and extract just that content
                    if '"' in response_text:
                        # Extract content between first set of quotes
                        import re
                        match = re.search(r'"([^"]+)"', response_text)
                        if match:
                            return match.group(1)
                    # If no quotes, look for line breaks that indicate extra content
                    if '\n---' in response_text:
                        response_text = response_text.split('\n---')[0].strip()
                    return response_text
            except Exception as e:
                logger.warning(f"LLM response generation failed: {e}, using fallback")
        
        # Fallback to original logic if LLM fails or no products
        if not products:
            # Use centralized no results prompt if LLM available
            if self.llm:
                try:
                    no_results_prompt = self.prompt_manager.get_prompt(
                        "no_results_response",
                        query=query,
                        criteria=str(intent.__dict__ if hasattr(intent, '__dict__') else intent)
                    )
                    llm_response = self.llm(no_results_prompt, max_tokens=150, temperature=0.7)
                    if llm_response and llm_response.get('choices'):
                        response = llm_response['choices'][0]['text'].strip()
                    else:
                        # Fallback to hardcoded response
                        response = f"I searched our inventory but couldn't find exact matches for '{intent.product_name or query}'. "
                        if intent.category:
                            response += f"Would you like to see other {intent.category} products we have available?"
                        else:
                            response += "Would you like me to show you similar products or browse our categories?"
                except Exception as e:
                    logger.warning(f"No results prompt generation failed: {e}")
                    # Fallback to hardcoded response
                    response = f"I searched our inventory but couldn't find exact matches for '{intent.product_name or query}'. "
                    if intent.category:
                        response += f"Would you like to see other {intent.category} products we have available?"
                    else:
                        response += "Would you like me to show you similar products or browse our categories?"
            else:
                # We searched and found nothing
                response = f"I searched our inventory but couldn't find exact matches for '{intent.product_name or query}'. "
                
                # Suggest alternatives based on what they asked for
                if intent.category:
                    response += f"Would you like to see other {intent.category} products we have available?"
                else:
                    response += "Would you like me to show you similar products or browse our categories?"
        else:
            # Group products by name to find different sizes
            product_groups = {}
            for p in products:
                base_name = p['product_name'].split(' - ')[0].strip()  # Remove size suffix if present
                if base_name not in product_groups:
                    product_groups[base_name] = []
                product_groups[base_name].append(p)
            
            # Check if asking about a specific product
            if 'tell me more about' in query.lower() or 'describe' in query.lower():
                # Provide detailed description
                if products:
                    p = products[0]
                    response = f"{p['product_name']} "
                    if p.get('brand'):
                        response += f"by {p['brand']} "
                    
                    # Add description
                    if p.get('description'):
                        response += f"\n\n{p['description']}\n"
                    
                    # List all available sizes for this product
                    same_product = [prod for prod in products if prod['product_name'].startswith(p['product_name'].split()[0])]
                    if len(same_product) > 1:
                        response += f"\nAvailable in {len(same_product)} sizes:\n"
                        for sp in same_product[:5]:
                            response += f"• {sp['size']} - ${sp['price']:.2f}\n"
                    else:
                        response += f"\nSize: {p['size']} - ${p['price']:.2f}\n"
                    
                    # Add strain and THC/CBD info
                    if p.get('strain_type'):
                        response += f"Strain Type: {p['strain_type']}\n"
                    if p.get('thc') and p['thc'] > 0:
                        response += f"THC: {p['thc']}%\n"
                    if p.get('cbd') and p['cbd'] > 0:
                        response += f"CBD: {p['cbd']}%\n"
                    
                    response += "\nWhich size would you like?"
                return response
            
            # Regular product listing
            if len(products) == 1:
                p = products[0]
                response = f"Yes! We have {p['product_name']}"
                if p['brand']:
                    response += f" by {p['brand']}"
                response += f" - ${p['price']:.2f}"
                if p['size']:
                    response += f" ({p['size']})"
                if p.get('description'):
                    response += f"\n\n{p['description'][:100]}..."
                response += "\n\nWould you like to add it to your cart?"
            else:
                # Check if multiple sizes of same product
                unique_bases = set()
                for p in products[:10]:
                    base_name = ' '.join(p['product_name'].split()[:2])
                    unique_bases.add(base_name)
                
                if len(unique_bases) == 1 and len(products) > 1:
                    # Same product, different sizes
                    response = f"Great! {products[0]['product_name'].split()[0]} is available in {len(products)} sizes:\n\n"
                    for i, p in enumerate(products[:5], 1):
                        response += f"{i}. {p['size']} - ${p['price']:.2f}"
                        if p.get('thc'):
                            response += f" (THC: {p['thc']}%)"
                        response += "\n"
                    
                    if len(products) > 5:
                        response += f"...and {len(products) - 5} more sizes available.\n"
                    response += "\nWhich size would you prefer?"
                else:
                    # Multiple different products
                    response = f"Great news! We have {len(products)} options for you:\n\n"
                    
                    # Group by unique product names
                    shown = set()
                    count = 0
                    for p in products:
                        base_name = p['product_name'].split(' - ')[0].strip()
                        if base_name not in shown and count < 3:
                            shown.add(base_name)
                            count += 1
                            # Find all sizes for this product
                            sizes = [prod for prod in products if prod['product_name'].startswith(base_name.split()[0])]
                            if len(sizes) > 1:
                                response += f"{count}. {base_name} (available in {len(sizes)} sizes: "
                                response += ", ".join([s['size'] for s in sizes[:3]])
                                if len(sizes) > 3:
                                    response += f", +{len(sizes)-3} more"
                                response += f") from ${min(s['price'] for s in sizes):.2f}\n"
                            else:
                                response += f"{count}. {p['product_name']} {p['size']} - ${p['price']:.2f}\n"
                    
                    if len(products) > 3:
                        response += f"\n...and {len(products) - 3} more options available."
                    response += "\n\nWould you like more details on any of these?"
        
        return response
    
    async def _search_products_advanced(self, criteria: Dict) -> List[Dict]:
        """Advanced product search with multiple criteria"""
        
        conditions = []
        params = []
        param_count = 0
        
        # Build WHERE conditions
        if criteria.get("category"):
            param_count += 1
            conditions.append(f"category = ${param_count}")
            params.append(criteria["category"])
            
        if criteria.get("sub_category"):
            param_count += 1
            conditions.append(f"sub_category = ${param_count}")
            params.append(criteria["sub_category"])
            
        # Use plant_type column for strain type
        if criteria.get("strain_type"):
            param_count += 1
            conditions.append(f"plant_type ILIKE ${param_count}")
            params.append(f"%{criteria['strain_type']}%")
            
        if criteria.get("exclude_id"):
            param_count += 1
            conditions.append(f"id != ${param_count}")
            params.append(criteria["exclude_id"])
        
        # Match infused status
        if criteria.get("is_infused"):
            param_count += 1
            conditions.append(f"(LOWER(product_name) LIKE ${param_count} OR LOWER(sub_sub_category) LIKE ${param_count})")
            params.append("%infused%")
        
        # Note: Price filtering will be done in Python after fetching
        # since price might be calculated or from a joined table
        
        # Build query
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        query = f"""
            SELECT * FROM products 
            WHERE {where_clause}
            ORDER BY RANDOM()
            LIMIT 50
        """
        
        try:
            logger.info(f"Advanced search query: {query}")
            logger.info(f"Advanced search params: {params}")
            async with self.db_pool.acquire() as conn:
                products = await conn.fetch(query, *params)
                logger.info(f"Advanced search found {len(products)} products")
                return [dict(p) for p in products]
        except Exception as e:
            logger.error(f"Error in advanced search: {e}")
            return []
    
    async def _handle_similarity_request(self, similarity_check: Dict, session_id: str) -> Dict:
        """Handle requests for similar products"""
        
        similar_to = similarity_check["similar_to"]
        if not similar_to:
            return {
                "message": "I need to know which product you'd like to find similar options for. Could you specify?",
                "products": [],
                "search_performed": False
            }
        
        # Build search criteria based on the product they want similar to
        # For pre-rolls, search in the actual pre-roll category regardless of how it's categorized
        product_name_lower = similar_to.get("product_name", "").lower()
        is_preroll = "pre-roll" in product_name_lower or "pre roll" in product_name_lower
        
        search_criteria = {
            "category": "Flower" if is_preroll else similar_to.get("category"),
            "sub_category": "Pre-Rolls" if is_preroll else similar_to.get("sub_category"),
            "strain_type": similar_to.get("plant_type") or similar_to.get("strain_type"),  # Use plant_type
            "similar_price": similar_to.get("price"),  # Find products in similar price range
            "exclude_id": similar_to.get("id"),  # Don't show the same product
            "is_infused": "infused" in product_name_lower  # Match infused status
        }
        
        # Search for similar products
        products = await self._search_products_advanced(search_criteria)
        
        # Filter to truly similar products
        similar_products = []
        base_price = similar_to.get("price", 0)
        
        for product in products:
            # Skip the exact same product
            if product.get("id") == similar_to.get("id"):
                continue
                
            # Check price similarity (within 50% range)
            if base_price > 0:
                price_ratio = product.get("price", 0) / base_price
                if 0.5 <= price_ratio <= 1.5:
                    similar_products.append(product)
            else:
                similar_products.append(product)
                
            if len(similar_products) >= 10:
                break
        
        # Generate response
        product_name = similar_to.get("product_name", "that product")
        if similar_products:
            response = f"Here are products similar to {product_name}:\n"
            for i, product in enumerate(similar_products[:5], 1):
                response += f"{i}. {product['product_name']}"
                if product.get('brand'):
                    response += f" by {product['brand']}"
                response += f" - ${product.get('price', 0):.2f}"
                if product.get('size'):
                    response += f" ({product['size']})"
                response += "\n"
        else:
            response = f"I couldn't find products similar to {product_name}. Would you like to see other {similar_to.get('category', 'products')}?"
        
        # Update context
        await self.context_manager.update_context(session_id, {
            'products_shown': similar_products[:10],
            'intent': 'similar_search',
            'message': {'user': f"Show similar to {product_name}", 'ai': response}
        })
        
        return {
            "message": response,
            "products": similar_products[:10],
            "intent": "similar_search",
            "original_product": similar_to,
            "search_performed": True,
            "total_found": len(similar_products)
        }
    
    async def _handle_reference(self, message: str, context: ConversationContext, session_id: str, reference_result: Dict) -> Dict:
        """Handle references to previously shown products"""
        
        # Extract which product is being referenced using the semantic result
        referenced_product = self.context_manager.extract_referenced_product(reference_result, context)
        
        if not referenced_product:
            # Couldn't determine which product - ask for clarification
            return {
                "message": "I'm not sure which product you're referring to. Could you please specify by number or name?",
                "products": context.last_products_shown[:5],  # Show last few products again
                "intent": "clarification",
                "search_performed": False
            }
        
        # Use LLM to extract quantity from message
        quantity = 1  # Default to 1
        if self.llm and self.prompt_manager:
            quantity_prompt = self.prompt_manager.get_prompt("quantity_extraction", message=message)
            
            response = self.llm(quantity_prompt, max_tokens=10, temperature=0)
            if response and response.get('choices'):
                try:
                    quantity = int(response['choices'][0]['text'].strip())
                except:
                    quantity = 1
        
        # Use the action from the reference result or determine intent semantically
        action = reference_result.get('action', 'inquire')
        is_purchase = action == 'select' or action == 'purchase'
        
        # If action wasn't clear from reference, use LLM to understand intent
        if action == 'inquire' and self.llm:
            # Use centralized prompt
            intent_prompt = self.prompt_manager.get_prompt(
                'purchase_intent_detection',
                message=message,
                product_name=referenced_product.get('product_name')
            )
            
            response = self.llm(intent_prompt, max_tokens=10, temperature=0)
            if response and response.get('choices'):
                intent = response['choices'][0]['text'].strip().lower()
                is_purchase = 'purchase' in intent
        
        if is_purchase:
            # Generate purchase confirmation
            total_price = referenced_product.get('price', 0) * quantity
            response = f"Great choice! Adding {quantity} x {referenced_product['product_name']}"
            if referenced_product.get('size'):
                response += f" ({referenced_product['size']})"
            response += f" to your cart - ${total_price:.2f} total."
            
            # Track that this product was selected
            context = await self.context_manager.get_context(session_id)
            self.context_manager.track_product_selection(referenced_product, 'add_to_cart', context)
            
            # Update context with cart action
            await self.context_manager.update_context(session_id, {
                'cart_item': {
                    'product': referenced_product,
                    'quantity': quantity
                },
                'intent': 'purchase',
                'message': {'user': message, 'ai': response},
                'last_selected_product': referenced_product  # Track for similarity requests
            })
            
            return {
                "message": response,
                "products": [referenced_product],
                "intent": "purchase",
                "action": "add_to_cart",
                "cart_item": {
                    "product_id": referenced_product.get('id'),
                    "product_name": referenced_product.get('product_name'),
                    "quantity": quantity,
                    "price": referenced_product.get('price', 0)
                },
                "search_performed": False
            }
        else:
            # Just asking about the product - use LLM with ONLY factual data
            if self.llm:
                # Format all available product data for the LLM
                product_data_str = f"Product Name: {referenced_product.get('product_name')}\n"
                
                # Include ALL source-of-truth columns that have values
                truth_fields = [
                    ('Brand', 'brand'),
                    ('Price', 'price', lambda x: f"${x:.2f}"),
                    ('Size', 'size'),
                    ('Category', 'category'),
                    ('Sub-Category', 'sub_category'),
                    ('THC Range', 'thc_min', 'thc_max', lambda min, max: f"{min}% - {max}%"),
                    ('THC Content', 'thc', lambda x: f"{x}%"),
                    ('CBD Range', 'cbd_min', 'cbd_max', lambda min, max: f"{min}% - {max}%"),
                    ('CBD Content', 'cbd', lambda x: f"{x}%"),
                    ('THC per Unit', 'thc_per_unit'),
                    ('CBD per Unit', 'cbd_per_unit'),
                    ('Plant Type', 'plant_type'),
                    ('Strain Type', 'strain_type'),
                    ('Short Description', 'short_description'),
                    ('Long Description', 'long_description'),
                    ('Terpenes', 'terpenes'),
                    ('Growing Method', 'growing_method'),
                    ('Grow Region', 'grow_region'),
                    ('Drying Method', 'drying_method'),
                    ('Trimming Method', 'trimming_method'),
                    ('Extraction Process', 'extraction_process'),
                    ('Ingredients', 'ingredients'),
                    ('Food Allergens', 'food_allergens'),
                    ('Items per Pack', 'items_per_pack'),
                    ('Net Weight', 'net_weight'),
                    ('Craft Product', 'craft', lambda x: "Yes" if x else "No"),
                    ('Temperature Control', 'temperature_control'),
                    ('Battery Type', 'battery_type'),
                    ('Carrier Oil', 'carrier_oil')
                ]
                
                for field_info in truth_fields:
                    if len(field_info) == 2:
                        label, key = field_info
                        value = referenced_product.get(key)
                        # Skip empty, None, or 0 values
                        if value and str(value).strip() and str(value) not in ['0', '0.0', 'None', 'null']:
                            if not (isinstance(value, (int, float)) and value == 0):
                                product_data_str += f"{label}: {value}\n"
                    elif len(field_info) == 3:
                        label, key, formatter = field_info
                        value = referenced_product.get(key)
                        # Skip empty, None, or 0 values
                        if value and str(value).strip() and str(value) not in ['0', '0.0', 'None', 'null']:
                            if not (isinstance(value, (int, float)) and value == 0):
                                product_data_str += f"{label}: {formatter(value)}\n"
                    elif len(field_info) == 4:
                        label, min_key, max_key, formatter = field_info
                        min_val = referenced_product.get(min_key)
                        max_val = referenced_product.get(max_key)
                        # Only include if both values exist and at least one is non-zero
                        if min_val and max_val and (min_val != 0 or max_val != 0):
                            product_data_str += f"{label}: {formatter(min_val, max_val)}\n"
                
                # Use the product_description prompt with ONLY factual data
                description_prompt = self.prompt_manager.get_prompt("product_description",
                                                                   product_data=product_data_str,
                                                                   message=message)
                
                llm_response = self.llm(description_prompt, max_tokens=200, temperature=0.3, echo=False)
                
                if llm_response and llm_response.get('choices'):
                    response = llm_response['choices'][0]['text'].strip()
                else:
                    # Fallback to simple factual response
                    response = f"{referenced_product['product_name']}"
                    if referenced_product.get('brand'):
                        response += f" by {referenced_product['brand']}"
                    response += f" - ${referenced_product.get('price', 0):.2f}"
                    if referenced_product.get('size'):
                        response += f" ({referenced_product['size']})"
                    if referenced_product.get('thc'):
                        response += f", THC: {referenced_product['thc']}%"
                    if referenced_product.get('cbd'):
                        response += f", CBD: {referenced_product['cbd']}%"
            else:
                # No LLM available - just provide basic facts
                response = f"{referenced_product['product_name']}"
                if referenced_product.get('brand'):
                    response += f" by {referenced_product['brand']}"
                response += f" - ${referenced_product.get('price', 0):.2f}"
                if referenced_product.get('size'):
                    response += f" ({referenced_product['size']})"
                if referenced_product.get('thc'):
                    response += f", THC: {referenced_product['thc']}%"
                if referenced_product.get('cbd'):
                    response += f", CBD: {referenced_product['cbd']}%"
            
            return {
                "message": response,
                "products": [referenced_product],
                "intent": "question",
                "search_performed": False
            }

# Usage example:
async def test_search_first():
    """Test the search-first approach"""
    
    import asyncpg
    import os
    
    # Connect to database
    db_pool = await asyncpg.create_pool(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', 5434)),
        database=os.getenv('DB_NAME', 'ai_engine'),
        user=os.getenv('DB_USER', 'weedgo'),
        password=os.getenv('DB_PASSWORD', 'your_password_here')
    )
    
    engine = SearchFirstEngine(db_pool)
    
    # Test queries (using examples, but system works with ANY product in database)
    test_queries = [
        "do you have any pre-rolls?",
        "show me what flowers you have",
        "I want something in 3.5g",
        "what edibles are available"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        result = await engine.process_query(query)
        print(f"Response: {result['message'][:200]}...")
        print(f"Products found: {result['total_found']}")
        if result['products']:
            print("Top products:")
            for p in result['products'][:3]:
                print(f"  - {p['product_name']} ({p['category']}): ${p['price']}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_search_first())