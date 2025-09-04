# LLM Search Extractor - How It Works & Deployment Guide

## Architecture Overview

```
User Query → LLM Search Extractor → Database Search → Results
     ↓              ↓                      ↓             ↓
"pink kush      Extract          Search with      Return actual
 flower 14g"    criteria         proper filters    products
                    ↓                      
              {product_name:           
               "Pink Kush",            
               category: "Flower",     
               size: "14g"}            
```

## How It Works

### 1. **Extraction Pipeline**

When a user says "pink kush flower 14g", the extractor:

1. **Sends prompt to LLM** with the query
2. **LLM returns structured JSON** with extracted fields
3. **Validates** the extracted criteria
4. **Converts to database filters**
5. **Executes search** with proper parameters

### 2. **Key Components**

```python
# The extractor uses your existing LLM (Mistral-7B)
extractor = LLMSearchExtractor(smart_ai_engine.llm)

# Step 1: Extract search parameters
criteria = extractor.extract_search_criteria("pink kush flower 14g")
# Returns: {
#   "product_name": "Pink Kush",
#   "category": "Flower", 
#   "sub_category": "Dried Flower",
#   "size": "14g"
# }

# Step 2: Detect intent (optional)
intent = extractor.detect_intent("pink kush flower 14g")
# Returns: "specific_product"

# Step 3: Validate criteria
validated = extractor.validate_criteria(criteria)
# Fixes any inconsistencies

# Step 4: Search database
# Use validated criteria to build SQL query

# Step 5: Generate response
response = extractor.generate_search_response(
    user_query, criteria, search_results
)
```

## Deployment Instructions

### Option 1: Direct Integration in Smart AI Engine V3

**File:** `/services/smart_ai_engine_v3.py`

```python
# Add import at top
from services.llm_search_extractor import LLMSearchExtractor

class SmartAIEngineV3:
    def __init__(self, ...):
        # ... existing init code ...
        
        # Initialize search extractor
        self.search_extractor = LLMSearchExtractor(self.llm)
    
    async def process_message(self, message: str, ...):
        # ... existing code ...
        
        # When intent is "search" or "product_inquiry"
        if intent in ["search", "product_inquiry"]:
            # Use LLM extractor instead of regex
            search_criteria = self.search_extractor.extract_search_criteria(message)
            
            # Build database query from criteria
            products = await self._search_products_with_criteria(search_criteria)
            
            # Generate response
            if products:
                response = self.search_extractor.generate_search_response(
                    message, search_criteria, products
                )
            else:
                # Try refined search
                refinements = self.search_extractor.refine_search(
                    search_criteria, 
                    self._get_available_options()
                )
                # Search with refinements...
    
    async def _search_products_with_criteria(self, criteria: Dict):
        """Search database using extracted criteria"""
        query = "SELECT * FROM products WHERE 1=1"
        params = []
        
        if criteria.get('product_name'):
            query += " AND LOWER(product_name) LIKE %s"
            params.append(f"%{criteria['product_name'].lower()}%")
        
        if criteria.get('category'):
            query += " AND category = %s"
            params.append(criteria['category'])
        
        if criteria.get('sub_category'):
            query += " AND sub_category = %s"
            params.append(criteria['sub_category'])
        
        if criteria.get('size'):
            query += " AND (size = %s OR size LIKE %s)"
            params.append(criteria['size'])
            params.append(f"%{criteria['size']}%")
        
        if criteria.get('strain_type'):
            query += " AND (plant_type = %s OR plant_type LIKE %s)"
            params.append(criteria['strain_type'])
            params.append(f"%{criteria['strain_type']}%")
        
        query += " ORDER BY unit_price ASC LIMIT 20"
        
        # Execute query
        rows = await self.db_conn.fetch(query, *params)
        return rows
```

### Option 2: Integration in API Server

**File:** `/api_server.py`

```python
# In UnifiedAIEngineService class

async def process_chat(self, request: ChatRequest):
    # ... existing code ...
    
    # After getting AI response
    if ai_response.get("intent") == "search":
        # Extract search criteria using LLM
        search_criteria = self.search_extractor.extract_search_criteria(
            request.message
        )
        
        # Search products with proper criteria
        products = await self.search_products_with_criteria(search_criteria)
        
        # Update AI response with actual products
        ai_response["products"] = products
        ai_response["message"] = self.search_extractor.generate_search_response(
            request.message,
            search_criteria,
            products
        )
```

### Option 3: Standalone Search Endpoint

**New endpoint in api_server.py:**

```python
@app.post("/api/v1/products/smart-search")
async def smart_product_search(query: str = Body(...)):
    """Smart search using LLM extraction"""
    
    # Extract search criteria
    criteria = service.search_extractor.extract_search_criteria(query)
    
    # Validate criteria
    validated = service.search_extractor.validate_criteria(criteria)
    
    # Search database
    products = await service.search_products_with_criteria(validated)
    
    # Generate response
    response_text = service.search_extractor.generate_search_response(
        query, validated, products
    )
    
    return {
        "query": query,
        "extracted_criteria": validated,
        "products": products,
        "response": response_text,
        "count": len(products)
    }
```

## Testing the Deployment

### 1. Test Extraction Accuracy

```python
# test_extraction.py
import asyncio
from services.llm_search_extractor import LLMSearchExtractor

test_queries = [
    "pink kush flower",
    "half ounce of blue dream",
    "cheapest sativa edibles",
    "og kush pre-rolls under $20",
    "14g indica flower",
    "show me joints"
]

async def test():
    extractor = LLMSearchExtractor(smart_ai_engine.llm)
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        criteria = extractor.extract_search_criteria(query)
        print(f"Extracted: {criteria}")
        
        intent = extractor.detect_intent(query)
        print(f"Intent: {intent}")

asyncio.run(test())
```

### 2. Verify Database Queries

```sql
-- Test queries that should be generated

-- "pink kush flower"
SELECT * FROM products 
WHERE LOWER(product_name) LIKE '%pink%kush%'
AND category = 'Flower'
ORDER BY unit_price ASC;

-- "half ounce of blue dream"  
SELECT * FROM products
WHERE LOWER(product_name) LIKE '%blue%dream%'
AND (size = '14g' OR size LIKE '%14%g%')
ORDER BY unit_price ASC;

-- "cheapest sativa edibles"
SELECT * FROM products
WHERE category = 'Edibles'
AND (plant_type = 'Sativa' OR plant_type LIKE '%Sativa%')
ORDER BY unit_price ASC;
```

### 3. Monitor Performance

```python
# Add logging to track extraction performance
import time

start = time.time()
criteria = extractor.extract_search_criteria(query)
extraction_time = time.time() - start

logger.info(f"Extraction took {extraction_time:.2f}s for query: {query}")
logger.info(f"Extracted criteria: {criteria}")
```

## Configuration & Tuning

### 1. **Prompt Adjustments**

Edit prompts in `/prompts/enhanced_search_prompts.md` to:
- Add new product names
- Update size conversions
- Modify extraction rules
- Change response format

### 2. **Performance Optimization**

```python
class CachedLLMSearchExtractor(LLMSearchExtractor):
    """Add caching for common queries"""
    
    def __init__(self, llm_function):
        super().__init__(llm_function)
        self.cache = {}
    
    def extract_search_criteria(self, user_query: str):
        # Check cache first
        cache_key = user_query.lower().strip()
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Extract and cache
        criteria = super().extract_search_criteria(user_query)
        self.cache[cache_key] = criteria
        return criteria
```

### 3. **Fallback Strategy**

```python
def extract_with_fallback(self, query: str):
    """Try LLM extraction with regex fallback"""
    try:
        # Try LLM extraction
        criteria = self.extract_search_criteria(query)
        if criteria:
            return criteria
    except Exception as e:
        logger.warning(f"LLM extraction failed: {e}")
    
    # Fallback to regex patterns
    return self._regex_fallback_extraction(query)
```

## Monitoring & Metrics

### Key Metrics to Track:

1. **Extraction Accuracy**
   - % of queries with correct product name extraction
   - % of queries with correct category mapping
   - % of queries with correct size conversion

2. **Search Success Rate**
   - % of searches returning relevant products
   - % of searches requiring refinement
   - Average products returned per search

3. **Performance**
   - LLM extraction latency
   - Database query time
   - End-to-end response time

### Logging Setup:

```python
# Add detailed logging
logger.info("Search extraction metrics", extra={
    "query": user_query,
    "extracted_criteria": criteria,
    "extraction_time_ms": extraction_time * 1000,
    "products_found": len(results),
    "intent": intent
})
```

## Rollback Plan

If issues occur, you can disable LLM extraction:

```python
# In smart_ai_engine_v3.py
USE_LLM_EXTRACTION = False  # Toggle this

if USE_LLM_EXTRACTION:
    criteria = self.search_extractor.extract_search_criteria(message)
else:
    criteria = self._legacy_regex_extraction(message)
```

## Expected Improvements

After deployment, you should see:

1. ✅ "pink kush flower" returns Pink Kush Dried Flower (not edibles)
2. ✅ "half ounce" correctly converts to 14g
3. ✅ "joints" searches Pre-Rolls subcategory
4. ✅ Better product name extraction ("Pink Kush" not just "Kush")
5. ✅ Proper category filtering
6. ✅ Size-aware searches
7. ✅ Natural language responses with actual products