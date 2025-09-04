# Conversation Context & Intent Detection Design

## Overview
Improve the AI engine to maintain conversation context, detect product references, and handle various intents more intelligently.

## 1. Conversation History System

### Database Schema
```sql
-- Add to existing conversation_messages table
ALTER TABLE conversation_messages ADD COLUMN products_shown JSONB;
ALTER TABLE conversation_messages ADD COLUMN intent_type VARCHAR(50);
ALTER TABLE conversation_messages ADD COLUMN referenced_products JSONB;
```

### Context Structure
```python
class ConversationContext:
    session_id: str
    last_products_shown: List[Dict]  # Last products displayed to user
    last_intent: str  # Previous intent type
    message_history: List[Dict]  # Last 5-10 messages
    current_cart: List[Dict]  # Items in cart
    user_preferences: Dict  # Strain type, price range, etc.
```

## 2. Intent Categories

### Primary Intents
1. **greeting** - Initial contact
2. **search** - Looking for new products
3. **purchase** - Selecting from shown products
4. **reference** - Referring to previous products
5. **question** - Information queries
6. **comparison** - Comparing products
7. **navigation** - Browse/filter commands
8. **cart_action** - Cart operations
9. **clarification** - Refining previous request

### Reference Patterns
```python
REFERENCE_PATTERNS = {
    "number": [r"^\d+$", r"^#\d+$", r"number \d+", r"option \d+"],
    "ordinal": ["first", "second", "third", "last", "first one", "second one"],
    "demonstrative": ["that one", "this one", "those", "these"],
    "definite": ["the [product]", "the cheaper one", "the stronger one"],
    "quantity": [r"^\d+ of (those|them|it)", r"give me \d+", r"i want \d+$"],
}
```

## 3. Common Scenarios & Prompts

### A. Purchase & Selection
- "I'll take the peach ringz" → Extract product name, match to shown
- "Give me 3 of those" → Reference last product + quantity
- "I want the first one" → Reference by position
- "Add 2 to cart" → Cart action with quantity
- "The cheaper one please" → Reference by attribute

### B. Comparison & Questions
- "Which is stronger?" → Compare THC levels of shown products
- "What's the difference?" → Explain variations
- "How much THC in #2?" → Specific product question
- "Tell me about the effects" → Product details

### C. Navigation & Filtering
- "Show me more" → Next page of results
- "Just sativas" → Filter current results
- "Under $20" → Price filter
- "Different brands" → Brand variety
- "Go back" → Return to previous state

### D. Cart Management
- "What's in my cart?" → Show cart
- "Remove the last one" → Cart removal
- "Change quantity to 3" → Update quantity
- "Clear everything" → Empty cart

### E. Availability & Inventory
- "Is that in stock?" → Check availability
- "When will you restock?" → Inventory timeline
- "How many left?" → Stock count
- "Hold that for me" → Reserve product

### F. Recommendations by Need
- "Something for sleep" → Effect-based search
- "Help with anxiety" → Medical intent
- "Party strain" → Social context
- "Beginner friendly" → Experience level
- "Similar to [product]" → Similarity search

### G. Budget & Deals
- "What can I get for $50?" → Budget constraint
- "Cheapest eighth" → Price optimization
- "Any deals today?" → Promotions
- "Bulk discounts?" → Quantity pricing

### H. Product Details
- "More info on this" → Detailed description
- "Lab results?" → Testing information
- "Terpene profile" → Chemical composition
- "Growing method?" → Cultivation details

## 4. Implementation Plan

### Phase 1: Context Passing
```python
# search_first_engine.py
async def process_query(self, message: str, session_id: str = None, context: ConversationContext = None):
    # Fetch conversation history if not provided
    if session_id and not context:
        context = await self._fetch_context(session_id)
    
    # Check for references first
    if self._is_reference(message, context):
        return await self._handle_reference(message, context)
```

### Phase 2: Reference Detection
```python
def _is_reference(self, message: str, context: ConversationContext) -> bool:
    """Check if message references previous products"""
    if not context or not context.last_products_shown:
        return False
    
    # Check patterns
    for pattern_type, patterns in REFERENCE_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, message.lower()):
                return True
    
    # Use LLM for complex references
    if self.llm:
        # Check with prompt
        pass
```

### Phase 3: Intent Router
```python
INTENT_HANDLERS = {
    'greeting': handle_greeting,
    'search': handle_search,
    'purchase': handle_purchase,
    'reference': handle_reference,
    'comparison': handle_comparison,
    'cart_action': handle_cart,
    'question': handle_question,
    'navigation': handle_navigation,
}
```

## 5. Prompt Templates

### Reference Detection Prompt
```
Previous products shown:
1. Pink Kush - $45 (3.5g)
2. Blue Dream - $50 (3.5g)
3. Sour Diesel - $40 (3.5g)

User said: "{message}"

Is the user referring to one of these products? If yes, which one?
Output: YES:[product_number] or NO
```

### Context-Aware Search
```
Conversation context:
- User previously asked about: {previous_searches}
- Products shown: {last_products}
- User preferences: {preferences}

Current message: "{message}"

Extract search intent considering the context.
```

### Purchase Confirmation
```
User wants to purchase: {product_name}
Quantity: {quantity}
Price: ${total_price}

Generate a friendly confirmation message that:
1. Confirms the product and quantity
2. States the total price
3. Asks if they want to add to cart
```

## 6. Error Handling

### Ambiguous References
- "I want that" with no context → Ask "Which product were you interested in?"
- Multiple matches → "Did you mean the Pink Kush or Pink Cookies?"
- Invalid reference → "I don't see that option. Here's what we have..."

### Context Loss
- Session expired → "Let me help you find what you're looking for"
- Missing history → Fall back to standard search

## 7. Testing Scenarios

1. Multi-turn conversation with references
2. Switching between search and purchase
3. Cart operations with context
4. Comparison queries
5. Budget-constrained searches
6. Effect-based recommendations