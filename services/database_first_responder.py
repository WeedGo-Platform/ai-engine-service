"""
Database-First Responder
NEVER makes claims without checking database
Maintains conversation context properly
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class DatabaseFirstResponder:
    """
    Ensures ALL responses are grounded in actual database searches
    Never hallucinates inventory
    """
    
    def __init__(self, db_pool, llm_function=None):
        self.db_pool = db_pool
        self.llm = llm_function
        self.sessions = {}  # Maintain conversation state
        
    async def handle_message(self, message: str, session_id: str, customer_id: str) -> Dict:
        """
        Handle message with strict database-first approach
        """
        
        # Initialize or get session
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                'history': [],
                'last_products': [],
                'context': {},
                'customer_id': customer_id
            }
        
        session = self.sessions[session_id]
        session['history'].append({'role': 'user', 'content': message, 'timestamp': datetime.now()})
        
        # Determine what user is asking about
        message_lower = message.lower()
        
        # Check if referencing previous context
        if any(word in message_lower for word in ['it', 'that', 'those', 'them']):
            # User is referencing something from earlier
            if not session['last_products']:
                return {
                    'message': "I need to know which product you're referring to. What specific item are you interested in?",
                    'products': [],
                    'needs_clarification': True
                }
        
        # CRITICAL: Check for product inquiries
        product_inquiry_keywords = [
            'do you have', 'do you carry', 'is there', 'got any',
            'looking for', 'want', 'need', 'give me', 'show me',
            'what about', 'how about', 'price of', 'cost of'
        ]
        
        is_product_inquiry = any(keyword in message_lower for keyword in product_inquiry_keywords)
        
        if is_product_inquiry:
            # ALWAYS SEARCH - Never assume
            products = await self.search_comprehensive(message)
            
            # Update session with found products
            session['last_products'] = products
            
            # Generate response based on ACTUAL search results
            response = self.generate_factual_response(message, products)
            
            # Add to history
            session['history'].append({
                'role': 'assistant',
                'content': response,
                'products': len(products),
                'timestamp': datetime.now()
            })
            
            return {
                'message': response,
                'products': products[:5],  # Return top 5
                'searched': True,
                'total_found': len(products)
            }
        
        # Handle other types of messages
        return await self.handle_general_message(message, session)
    
    async def search_comprehensive(self, message: str) -> List[Dict]:
        """
        Search database comprehensively
        Try multiple strategies to find products
        """
        
        if not self.db_pool:
            return []
        
        all_results = []
        message_lower = message.lower()
        
        async with self.db_pool.acquire() as conn:
            # Extract potential product names
            search_terms = []
            
            # Look for product names after key phrases
            import re
            patterns = [
                r'(?:have|carry|got|want|need)\s+(?:any\s+)?([a-z\s]+?)(?:\s+pre-?roll|\s+flower|\s+\d|\?|$)',
                r'(?:about|price of)\s+([a-z\s]+?)(?:\s+pre-?roll|\s+flower|\?|$)',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, message_lower)
                search_terms.extend(matches)
            
            # Clean up search terms
            search_terms = [term.strip() for term in search_terms if len(term.strip()) > 2]
            
            # Always search for the full message too
            if not search_terms:
                # Extract meaningful words
                words = message_lower.split()
                search_terms = [w for w in words if len(w) > 3 and w not in 
                              ['have', 'does', 'your', 'what', 'about', 'give', 'show']]
            
            # Search for each term
            for term in search_terms:
                query = """
                    SELECT DISTINCT ON (id) * FROM products 
                    WHERE LOWER(product_name) LIKE $1
                       OR LOWER(brand) LIKE $1
                       OR LOWER(street_name) LIKE $1
                    ORDER BY id, unit_price ASC
                    LIMIT 20
                """
                
                results = await conn.fetch(query, f'%{term}%')
                for row in results:
                    product = {
                        'id': row['id'],
                        'product_name': row['product_name'],
                        'brand': row['brand'],
                        'category': row['category'],
                        'sub_category': row['sub_category'],
                        'size': row['size'],
                        'price': float(row['unit_price']),
                        'thc': float(row['thc_max_percent'] or 0),
                        'cbd': float(row['cbd_max_percent'] or 0),
                        'description': row['short_description'],
                        'image': row['image_url']
                    }
                    
                    # Avoid duplicates
                    if not any(p['id'] == product['id'] for p in all_results):
                        all_results.append(product)
            
            # Special handling for pre-rolls
            if 'pre-roll' in message_lower or 'preroll' in message_lower:
                # Search in both Pre-Rolls subcategory AND Extracts (for infused)
                query = """
                    SELECT * FROM products 
                    WHERE sub_category = 'Pre-Rolls' 
                       OR (LOWER(product_name) LIKE '%pre-roll%' OR LOWER(product_name) LIKE '%preroll%')
                    ORDER BY unit_price ASC
                    LIMIT 50
                """
                
                results = await conn.fetch(query)
                for row in results:
                    # Check if matches our search terms
                    if search_terms and any(term in row['product_name'].lower() for term in search_terms):
                        product = {
                            'id': row['id'],
                            'product_name': row['product_name'],
                            'brand': row['brand'],
                            'category': row['category'],
                            'sub_category': row['sub_category'],
                            'size': row['size'],
                            'price': float(row['unit_price']),
                            'in_stock': True
                        }
                        
                        if not any(p['id'] == product['id'] for p in all_results):
                            all_results.append(product)
        
        return all_results
    
    def generate_factual_response(self, query: str, products: List[Dict]) -> str:
        """
        Generate response based ONLY on search results
        NEVER claim products don't exist without proof
        """
        
        query_lower = query.lower()
        
        if products:
            # We found products - report them
            if len(products) == 1:
                p = products[0]
                return f"Yes! We have {p['product_name']} ({p['category']}/{p['sub_category']}) for ${p['price']:.2f}. Would you like to add it to your cart?"
            else:
                # Multiple products
                response = f"Yes! I found {len(products)} options for you:\n\n"
                for i, p in enumerate(products[:3], 1):
                    response += f"{i}. {p['product_name']} "
                    if p.get('size'):
                        response += f"{p['size']} "
                    response += f"- ${p['price']:.2f}\n"
                
                if len(products) > 3:
                    response += f"\n...and {len(products) - 3} more options available."
                
                response += "\n\nWhich one interests you?"
                return response
        else:
            # No products found after comprehensive search
            # Extract what they asked for
            import re
            asked_for = "that specific item"
            
            patterns = [
                r'(?:have|carry|got)\s+([a-z\s]+?)(?:\s+pre-?roll|\s+flower|\?|$)',
                r'(?:want|need)\s+([a-z\s]+?)(?:\s+pre-?roll|\s+flower|\?|$)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, query_lower)
                if match:
                    asked_for = match.group(1).strip()
                    break
            
            return f"I searched our entire inventory but couldn't find '{asked_for}' specifically. Would you like me to show you similar products or browse our available categories?"
    
    async def handle_general_message(self, message: str, session: Dict) -> Dict:
        """Handle non-product inquiry messages"""
        
        message_lower = message.lower()
        
        # Handle greetings
        if any(greeting in message_lower for greeting in ['hello', 'hi', 'hey', 'good morning', 'good afternoon']):
            return {
                'message': "Hello! Welcome to our dispensary. How can I help you find the perfect cannabis product today?",
                'products': [],
                'greeting': True
            }
        
        # Handle yes/no to previous question
        if message_lower in ['yes', 'yes please', 'yeah', 'yep', 'sure']:
            if session['last_products']:
                product = session['last_products'][0]
                return {
                    'message': f"Great! I'll add {product['product_name']} to your cart. Is there anything else you'd like?",
                    'products': [product],
                    'action': 'add_to_cart'
                }
        
        # Default response
        return {
            'message': "I can help you find specific products. Just ask 'do you have [product name]?' or 'show me [category]' and I'll search our inventory for you.",
            'products': [],
            'help': True
        }

# Test function
async def test_database_first():
    """Test the database-first responder"""
    
    import asyncpg
    import os
    
    db_pool = await asyncpg.create_pool(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', 5434)),
        database=os.getenv('DB_NAME', 'ai_engine'),
        user=os.getenv('DB_USER', 'weedgo'),
        password=os.getenv('DB_PASSWORD', 'weedgo123')
    )
    
    responder = DatabaseFirstResponder(db_pool)
    
    # Simulate the problematic conversation
    test_conversation = [
        "do you have tiger blood preroll?",
        "do you have pink kush 1/2 ounce?",
        "i want to see it",
        "what about tiger blood preroll"
    ]
    
    session_id = "test-session-1"
    
    for message in test_conversation:
        print(f"\n🧑 User: {message}")
        response = await responder.handle_message(message, session_id, "test-customer")
        print(f"🤖 Bot: {response['message'][:200]}")
        if response.get('products'):
            print(f"   📦 Found {len(response['products'])} products")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_database_first())