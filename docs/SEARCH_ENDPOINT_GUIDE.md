# Search Endpoint Guide

## Core Philosophy
**Default returns ALL products, filters REDUCE the result set**

## Query Parameter (Primary Search)
The `query` parameter is the most important - it searches across:
- Product names (e.g., "Pink Kush", "Blue Dream")
- Brand names (e.g., "Cookies", "Raw Garden")
- Strain types mentioned in names

### Intelligent Query Interpretation
The AI infers and expands queries:
```
User says: "something strong for sleep"
AI infers: query="high thc indica sleep"

User says: "pink kush half ounce"
AI infers: query="pink kush 14g"

User says: "beginner friendly"
AI infers: query="low thc mild balanced"
```

## Filtering Strategy

### Category Filter
- **Empty/None**: Returns products from ALL categories
- **Set**: Returns ONLY products from that category
- Values: `Flower`, `Edibles`, `Vapes`, `Extracts`, `Topicals`, `Accessories`

### Price Filters
- **min_price**: Inclusive lower bound (products >= this price)
- **max_price**: Inclusive upper bound (products <= this price)
- **Both empty**: No price filtering

### THC Filters
- **min_thc**: Products with THC% >= this value
- **max_thc**: Products with THC% <= this value
- **Both empty**: No THC filtering

### Intent Filter
Maps customer intent to product effects in descriptions:
- `sleep` → Searches for "sleep", "sedative", "nighttime" in descriptions
- `energy` → Searches for "energetic", "uplifting", "daytime"
- `pain` → Searches for "pain relief", "analgesic", "medical"
- `relax` → Searches for "relaxing", "calming", "stress relief"

## Example API Calls

### 1. Get ALL Products (Default)
```json
POST /api/v1/products/search
{}
// Returns: All products in database
```

### 2. Search for Specific Product
```json
POST /api/v1/products/search
{
  "query": "pink kush"
}
// Returns: All Pink Kush products (any category, any price)
```

### 3. Category + Price Range
```json
POST /api/v1/products/search
{
  "category": "Flower",
  "min_price": 10,
  "max_price": 30
}
// Returns: All flower products between $10-30
```

### 4. Intent-Based Search
```json
POST /api/v1/products/search
{
  "intent": "sleep",
  "category": "Flower",
  "min_thc": 15
}
// Returns: Flower products with THC >= 15% that mention sleep effects
```

### 5. Complex Search
```json
POST /api/v1/products/search
{
  "query": "hybrid",
  "category": "Flower",
  "min_price": 10,
  "max_price": 20,
  "min_thc": 10,
  "max_thc": 20
}
// Returns: Hybrid flower products, $10-20, THC 10-20%
```

## SQL Logic (Backend Implementation)
```sql
-- Base query starts with ALL products
SELECT * FROM products
WHERE 1=1  -- Always true, returns all

-- Each filter REDUCES the result set
AND (query IS NULL OR (product_name ILIKE %query% OR brand ILIKE %query%))
AND (category IS NULL OR LOWER(category) = LOWER(:category))
AND (min_price IS NULL OR unit_price >= :min_price)
AND (max_price IS NULL OR unit_price <= :max_price)
AND (min_thc IS NULL OR thc_max_percent >= :min_thc)
AND (max_thc IS NULL OR thc_max_percent <= :max_thc)
AND (intent IS NULL OR long_description ILIKE %intent_keywords%)
```

## AI's Role in Search

1. **Parameter Inference**: AI converts natural language to structured parameters
2. **Query Expansion**: AI expands simple terms to comprehensive searches
3. **Size Conversion**: AI converts colloquial sizes to grams
4. **Intent Mapping**: AI maps customer needs to product effects

## Common Patterns

### Size Conversions
- "eighth" → 3.5g
- "quarter" → 7g
- "half ounce" → 14g
- "ounce" → 28g

### Effect Mappings
- "get high" → high THC products
- "medical" → balanced CBD/THC products
- "party" → sativa, energetic strains
- "couch lock" → heavy indica strains

## Training the AI

The AI improves through:
1. **Feedback Collection**: Recording which products customers click/buy
2. **Correction Learning**: Human operators correct misinterpreted queries
3. **Pattern Recognition**: Learning common request patterns
4. **A/B Testing**: Comparing different inference strategies

## Monitoring Accuracy

Track these metrics:
- **Click-through rate**: Do customers click on recommended products?
- **Purchase rate**: Do recommendations lead to purchases?
- **Parameter accuracy**: How often does AI correctly infer each parameter?
- **Response time**: Speed of inference and search

## Best Practices

1. **Always start broad**: Default to showing all products
2. **Let filters narrow**: Each filter should reduce, not expand results
3. **Handle typos**: Use fuzzy matching in queries
4. **Consider context**: Previous messages influence current inference
5. **Fail gracefully**: If unsure, show popular products