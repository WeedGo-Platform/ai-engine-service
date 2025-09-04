"""
LLM-based Search Criteria Extractor
Uses language model to extract search parameters from user queries
"""
import json
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class LLMSearchExtractor:
    """Extract search criteria using LLM prompts"""
    
    def __init__(self, llm_function):
        """
        Initialize with LLM function
        
        Args:
            llm_function: Function to call LLM (e.g., smart_ai_engine.llm)
        """
        self.llm = llm_function
        
    def extract_search_criteria(self, user_query: str) -> Dict[str, Any]:
        """
        Extract search criteria from user query using LLM
        
        Args:
            user_query: Natural language query from user
            
        Returns:
            Dictionary with search parameters
        """
        
        prompt = f"""You are a cannabis product search assistant. Extract structured search parameters from the user's query to search the product database.

Output ONLY valid JSON with these fields:
- product_name: The specific product name mentioned (exact string, e.g., "Pink Kush")
- category: Main category (Flower/Edibles/Vapes/Extracts/Topicals/Accessories)
- sub_category: Subcategory if specified (e.g., "Dried Flower", "Pre-Rolls")
- size: Product size/quantity (e.g., "3.5g", "14g", "1x0.5g", "2x1g", "3x0.5g")
- strain_type: Cannabis strain type (Sativa/Indica/Hybrid/Balanced)
- min_price: Minimum price if specified
- max_price: Maximum price if specified

IMPORTANT EXTRACTION RULES:
1. Product names must be extracted exactly as mentioned (e.g., "Pink Kush" not just "Kush")
2. When user says "flower" they usually mean dried flower, not pre-rolls
3. "Joints" or "pre-rolled" means Pre-Rolls subcategory
4. Common size conversions:
   - "eighth" or "1/8 oz" = "3.5g"
   - "quarter" or "1/4 oz" = "7g"  
   - "half ounce" or "1/2 oz" = "14g"
   - "ounce" or "oz" = "28g"
5. QUANTITY FORMATS - Convert various formats to standard:
   - "2 by 1g" or "2x1g" = "2x1g" (2 units of 1 gram each)
   - "3 by 0.5g" or "3x0.5g" = "3x0.5g" (3 units of 0.5 gram each)
   - "10 by 0.35g" = "10x0.35g" (10 units of 0.35 gram each)
   - "5 by .5g" = "5x0.5g" (ensure leading zero for decimals)
   - "paquete de 2" (Spanish) = "2x1g" (2-pack)
   - "1/2 once" or "1/2 ounce" or "half ounce" = "14g"
   - "1/4 once" or "1/4 ounce" or "quarter ounce" = "7g"
6. If both product name AND category are mentioned, include both
7. Don't infer information not explicitly stated

Examples:
User: "pink kush flower"
Output: {{"product_name": "Pink Kush", "category": "Flower"}}

User: "I want half ounce of pink kush"
Output: {{"product_name": "Pink Kush", "size": "14g", "sub_category": "Dried Flower"}}

User: "sativa preroll 2 by 1g under $10"
Output: {{"category": "Flower", "sub_category": "Pre-Rolls", "strain_type": "Sativa", "size": "2x1g", "max_price": 10}}

User: "3 by 0.5g indica joints"
Output: {{"category": "Flower", "sub_category": "Pre-Rolls", "strain_type": "Indica", "size": "3x0.5g"}}

User: "cheapest sativa edibles under $20"
Output: {{"category": "Edibles", "strain_type": "Sativa", "max_price": 20}}

User: "blue dream pre-rolls"
Output: {{"product_name": "Blue Dream", "category": "Flower", "sub_category": "Pre-Rolls"}}

User: "je cherche pink kush 1/2 once" (French)
Output: {{"product_name": "Pink Kush", "size": "14g"}}

User: "quiero paquete de 2 pre-rolls sativa" (Spanish)
Output: {{"category": "Flower", "sub_category": "Pre-Rolls", "strain_type": "Sativa", "size": "2x1g"}}

Current query: {user_query}

CRITICAL: Output ONLY the JSON object. Do not include any explanatory text before or after.
Start with {{ and end with }}. No other text allowed."""

        try:
            response = self.llm(prompt, max_tokens=200, echo=False)
            response_text = response.get('choices', [{}])[0].get('text', '{}')
            
            # Clean and parse JSON - be more aggressive about finding JSON
            response_text = response_text.strip()
            
            # Remove markdown code blocks if present
            if '```json' in response_text:
                start = response_text.find('```json') + 7
                end = response_text.find('```', start)
                if end > start:
                    response_text = response_text[start:end]
            elif '```' in response_text:
                start = response_text.find('```') + 3
                end = response_text.find('```', start)
                if end > start:
                    response_text = response_text[start:end]
            
            # Try to find JSON object in the text
            import re
            json_match = re.search(r'\{[^}]*\}', response_text)
            if json_match:
                response_text = json_match.group(0)
            
            # Remove any "Output:" prefix
            if response_text.startswith('Output:'):
                response_text = response_text[7:].strip()
            
            criteria = json.loads(response_text.strip())
            
            # Remove None values
            criteria = {k: v for k, v in criteria.items() if v is not None}
            
            logger.info(f"LLM extracted criteria: {criteria}")
            return criteria
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {response_text}")
            return {}
        except Exception as e:
            logger.error(f"Error extracting search criteria: {e}")
            return {}
    
    def detect_intent(self, user_query: str) -> str:
        """
        Detect the user's search intent
        
        Args:
            user_query: Natural language query
            
        Returns:
            Intent type string
        """
        
        prompt = f"""Classify the user's intent for their cannabis product query.

Query: {user_query}

INTENT TYPES:
- specific_product: Looking for a named product (e.g., "Pink Kush")
- category_browse: Browsing a category (e.g., "show me edibles")
- effect_based: Seeking specific effects (e.g., "something for sleep")
- price_focused: Primary concern is price (e.g., "cheapest options")
- size_specific: Looking for specific quantity (e.g., "14g products")
- general_browse: No specific criteria (e.g., "what do you have?")

Detection rules:
1. Product names indicate specific_product intent
2. Category without product name is category_browse
3. Medical/effect keywords indicate effect_based
4. Price terms indicate price_focused
5. Size as main criteria is size_specific

Output only the intent type."""

        try:
            response = self.llm(prompt, max_tokens=50, echo=False)
            intent = response.get('choices', [{}])[0].get('text', '').strip().lower()
            
            valid_intents = ['specific_product', 'category_browse', 'effect_based', 
                           'price_focused', 'size_specific', 'general_browse']
            
            if intent in valid_intents:
                return intent
            return 'general_browse'
            
        except Exception as e:
            logger.error(f"Error detecting intent: {e}")
            return 'general_browse'
    
    def normalize_size(self, size_input: str) -> str:
        """
        Normalize size specification using LLM
        
        Args:
            size_input: User's size specification
            
        Returns:
            Normalized size string
        """
        
        prompt = f"""Convert the user's size specification to our standard format.

User specified: {size_input}

Standard formats:
- Dried flower: "1g", "3.5g", "7g", "14g", "28g"
- Pre-rolls: "1x0.5g", "3x0.5g", "5x0.5g", "10x0.35g"
- Edibles: "5mg", "10mg" (per piece), "100mg" (per package)

Common conversions:
- "eighth", "1/8", "1/8 oz" → "3.5g"
- "quarter", "1/4", "1/4 oz" → "7g"
- "half", "half ounce", "1/2 oz" → "14g"
- "zip", "ounce", "oz" → "28g"
- "a joint" → "1x0.5g" or "1x1g"
- "pack of joints" → "3x0.5g" or "5x0.5g"

Output the normalized size string only."""

        try:
            response = self.llm(prompt, max_tokens=20, echo=False)
            return response.get('choices', [{}])[0].get('text', '').strip()
        except Exception as e:
            logger.error(f"Error normalizing size: {e}")
            return size_input
    
    def validate_criteria(self, criteria: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and correct search criteria
        
        Args:
            criteria: Extracted search criteria
            
        Returns:
            Validation result with corrections
        """
        
        prompt = f"""Validate the extracted search criteria and identify potential issues.

Extracted criteria: {json.dumps(criteria)}

VALIDATION CHECKS:
1. Is the category compatible with the subcategory?
2. Is the size format appropriate for the category?
3. Are price constraints reasonable?
4. Is the strain type applicable to the category?
5. Are there conflicting criteria?

Common issues to check:
- Flower category with Edibles subcategory (invalid)
- Strain type specified for Accessories (not applicable)
- Size "14g" for Edibles (should be mg not g)
- Pre-rolls with loose flower sizes (should be NxYg format)

Output JSON:
{{
  "is_valid": boolean,
  "issues": [list of issues found],
  "corrected_criteria": {{corrected criteria}}
}}"""

        try:
            response = self.llm(prompt, max_tokens=300, echo=False)
            response_text = response.get('choices', [{}])[0].get('text', '{}')
            
            # Clean and parse JSON
            response_text = response_text.strip()
            if response_text.startswith('```'):
                response_text = response_text[response_text.index('\n')+1:response_text.rfind('```')]
            
            result = json.loads(response_text.strip())
            
            if result.get('is_valid'):
                return criteria
            else:
                return result.get('corrected_criteria', criteria)
                
        except Exception as e:
            logger.error(f"Error validating criteria: {e}")
            return criteria
    
    def generate_search_response(self, 
                                user_query: str,
                                search_criteria: Dict[str, Any],
                                search_results: List[Dict[str, Any]]) -> str:
        """
        Generate natural language response for search results
        
        Args:
            user_query: Original user query
            search_criteria: Criteria used for search
            search_results: Products found
            
        Returns:
            Natural language response
        """
        
        # Prepare results summary
        if search_results:
            results_summary = f"{len(search_results)} products found"
            products_list = []
            for product in search_results[:3]:  # Show top 3
                products_list.append(
                    f"{product.get('product_name', 'Unknown')} - "
                    f"{product.get('size', '')} - "
                    f"${product.get('unit_price', 0):.2f}"
                )
            results_text = "\n".join(products_list)
        else:
            results_summary = "No products found"
            results_text = "None"
        
        prompt = f"""You are a helpful cannabis budtender. Generate a response based on the search results.

Search query: {user_query}
Search criteria used: {json.dumps(search_criteria)}
Products found: {results_summary}

Top products:
{results_text}

RESPONSE RULES:
1. If products matching the exact criteria were found, list them with details
2. If no exact matches, explain what wasn't found and show alternatives
3. Always mention actual product names, prices, and key details (THC%, size)
4. Be transparent about what you found vs. what was requested
5. Suggest alternatives only when exact matches aren't available

RESPONSE FORMAT:
- For exact matches: "I found [count] [product_name] options: [details]"
- For no matches: "I don't have [exact_request], but here are similar options: [alternatives]"
- For partial matches: "I found [product_name] but not in [missing_criteria]. Available options: [details]"

Generate a helpful, accurate response."""

        try:
            response = self.llm(prompt, max_tokens=200, echo=False)
            return response.get('choices', [{}])[0].get('text', '').strip()
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            if search_results:
                return f"I found {len(search_results)} products matching your search."
            return "I couldn't find products matching your criteria."
    
    def refine_search(self,
                      original_criteria: Dict[str, Any],
                      available_options: Dict[str, List[str]]) -> List[Dict[str, Any]]:
        """
        Generate refined search options when no results found
        
        Args:
            original_criteria: Original search that returned no results
            available_options: Available categories, sizes, etc. in database
            
        Returns:
            List of refined search criteria options
        """
        
        prompt = f"""The initial search returned no results. Suggest search refinements.

Original search: {json.dumps(original_criteria)}
Available in database: {json.dumps(available_options)}

Generate 3 alternative search strategies:

1. Broaden search by removing the most restrictive filter
2. Try similar products or categories
3. Adjust size or price constraints

Output JSON with three refined search options:
{{
  "refinement_1": {{modified_criteria}},
  "refinement_2": {{modified_criteria}},  
  "refinement_3": {{modified_criteria}}
}}"""

        try:
            response = self.llm(prompt, max_tokens=300, echo=False)
            response_text = response.get('choices', [{}])[0].get('text', '{}')
            
            # Clean and parse JSON
            response_text = response_text.strip()
            if response_text.startswith('```'):
                response_text = response_text[response_text.index('\n')+1:response_text.rfind('```')]
            
            result = json.loads(response_text.strip())
            
            refinements = []
            for key in ['refinement_1', 'refinement_2', 'refinement_3']:
                if key in result:
                    refinements.append(result[key])
            
            return refinements if refinements else [{}]
            
        except Exception as e:
            logger.error(f"Error refining search: {e}")
            # Return simple fallback refinements
            return [
                {k: v for k, v in original_criteria.items() if k != 'size'},
                {k: v for k, v in original_criteria.items() if k != 'product_name'},
                {'category': original_criteria.get('category')}
            ]