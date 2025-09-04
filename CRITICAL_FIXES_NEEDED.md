# Critical Fixes Needed - AI Engine Service

## Issues Identified from Logs

### 1. Language Detection Problems ❌
- Spanish detected as Welsh (cy), Italian (it)
- "Si ellas me llaman roddy" detected as Welsh instead of Spanish
- "Añadir indica a mi carrito" detected as Italian instead of Spanish

**Root Cause**: Using basic `langdetect` library without context
**Fix**: Implement better language detection with context awareness

### 2. Product Search Returning 0 Results ❌
- All product searches return 0 products
- Database query issues with plant_type column
- SmartAIEngineV3 local search not working

**Root Cause**: Database column mismatch or empty database
**Fix**: Verify database has products and column names match

### 3. Intent Detection Failures ❌
- Constant "Unexpected intent response from LLM" warnings
- All intents defaulting to 'general_fallback'
- LLM not extracting intents properly

**Root Cause**: Prompt format issues or model not understanding intent extraction
**Fix**: Improve intent extraction prompts

### 4. Context Not Preserved ❌
- Bot doesn't remember user's name (Brad/Roddy)
- Doesn't answer direct questions (What's your name?)
- Falls back to generic responses

**Root Cause**: Conversation history not being used effectively
**Fix**: Improve context management

### 5. Multilingual Response Quality ❌
- Mixing languages in responses
- Fallback to English when should stay in Spanish
- Poor quality Spanish responses

**Root Cause**: Model not properly instructed for language consistency
**Fix**: Better multilingual prompts and model selection

## Immediate Actions Required

### Fix 1: Database Verification
```python
# Check if products exist
SELECT COUNT(*) FROM products;
SELECT DISTINCT plant_type FROM products;
SELECT product_name, plant_type FROM products LIMIT 5;
```

### Fix 2: Better Language Detection
```python
# Add context-aware language detection
def detect_language_with_context(message, session_history):
    # Check session language first
    # Then check common patterns
    # Finally use langdetect as fallback
```

### Fix 3: Fix Intent Extraction
```python
# Clearer intent extraction prompt
INTENT_PROMPT = """
Classify this message into ONE intent:
- product_search: Looking for specific products
- greeting: Hello, hi, hola, etc.
- question: Asking a question
- add_to_cart: Want to buy/add to cart

Message: {message}
Intent:
"""
```

### Fix 4: Improve Conversation Memory
```python
# Use last 5 messages for context
context = build_context_from_history(session_history[-5:])
prompt = f"Previous context: {context}\nUser: {message}\nAssistant:"
```

### Fix 5: Fix Product Database Query
```python
# Verify column names
SELECT column_name FROM information_schema.columns 
WHERE table_name = 'products';

# Fix the query
SELECT * FROM products 
WHERE plant_type ILIKE '%sativa%' 
OR product_name ILIKE '%sativa%';
```

## Test Cases to Verify Fixes

1. **Spanish Conversation Flow**:
   - User: "Hola, me llamo Carlos"
   - Bot should: Remember name and respond in Spanish
   - User: "¿Cómo te llamas?"
   - Bot should: Give its name (Zac)

2. **Product Search**:
   - User: "Show me sativa products"
   - Bot should: Return actual products with images

3. **Cart Addition**:
   - User: "Añadir Blue Dream a mi carrito"
   - Bot should: Recognize intent and maintain Spanish

4. **Context Preservation**:
   - Multi-turn conversation should remember previous context
   - Name, preferences, language should persist

## Priority Order
1. Fix database/product search (no products = no functionality)
2. Fix language detection (core multilingual feature)
3. Fix intent extraction (enables proper responses)
4. Fix conversation context (improves UX)
5. Improve response quality (polish)