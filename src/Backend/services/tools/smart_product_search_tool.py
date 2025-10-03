"""
Smart Product Search Tool
Calls /api/products endpoint to retrieve real products from database
Replaces hallucinated product recommendations with actual inventory
Uses LLM-based entity extraction for multilingual query understanding
"""

import httpx
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class SmartProductSearchTool:
    """Tool for searching products via API with context awareness"""

    def __init__(self, base_url: str = "http://localhost:5024", agent_pool=None):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
        self.agent_pool = agent_pool  # Reference to agent pool for LLM entity extraction

    def _extract_search_params_legacy(self, query: str) -> Dict[str, Any]:
        """Extract structured search parameters from natural language query"""
        query_lower = query.lower()
        params = {}

        # Extract plant type (sativa, indica, hybrid)
        if "sativa" in query_lower:
            params["plantType"] = "sativa"
        elif "indica" in query_lower:
            params["plantType"] = "indica"
        elif "hybrid" in query_lower:
            params["plantType"] = "hybrid"

        # Note: Subcategory extraction now handled by LLM entity extractor
        # which dynamically fetches categories/subcategories from /api/products/categories and /api/products/sub-categories
        # This ensures we always use current database values without hardcoding

        # Always filter to in-stock products
        params["inStock"] = "true"

        # Default sorting by name
        params["sortBy"] = "name"
        params["sortOrder"] = "asc"

        return params

    async def search(
        self,
        query: str,
        store_id: Optional[str] = None,
        limit: int = 5,
        category: Optional[str] = None,
        min_thc: Optional[float] = None,
        max_thc: Optional[float] = None,
        min_cbd: Optional[float] = None,
        max_cbd: Optional[float] = None,
        strain_type: Optional[str] = None,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search for products using /api/products endpoint with LLM-based entity extraction

        Args:
            query: Search query from user
            store_id: Store ID from session context
            limit: Maximum number of products to return
            category: Product category filter
            min_thc: Minimum THC content
            max_thc: Maximum THC content
            min_cbd: Minimum CBD content
            max_cbd: Maximum CBD content
            strain_type: Strain type filter (sativa, indica, hybrid)
            session_id: Session ID for context
            user_id: User ID for preference learning

        Returns:
            Dict with products list and metadata
        """
        logger.info(f"[SmartProductSearch] START - Query: '{query}', Store: {store_id}, Session: {session_id}")
        logger.info(f"[SmartProductSearch] Input params - limit: {limit}, category: {category}, strain_type: {strain_type}")

        try:
            # Use LLM-based entity extraction if agent_pool is available
            params = {}
            if self.agent_pool and hasattr(self.agent_pool, 'extract_and_build_search_params'):
                try:
                    logger.info(f"[SmartProductSearch] Using LLM entity extraction for query: {query}")
                    logger.info(f"[SmartProductSearch] Agent pool available: {self.agent_pool is not None}")

                    extraction_result = await self.agent_pool.extract_and_build_search_params(
                        message=query,
                        session_id=session_id,
                        user_id=user_id
                    )

                    logger.info(f"[SmartProductSearch] Extraction result type: {extraction_result.get('type')}")
                    logger.info(f"[SmartProductSearch] Full extraction result: {extraction_result}")

                    # Handle different result types
                    if extraction_result.get("type") == "search":
                        # Use extracted parameters
                        params = extraction_result.get("params", {})
                        logger.info(f"[SmartProductSearch] ✅ LLM extracted search params: {params}")
                    elif extraction_result.get("type") == "quick_actions":
                        # Return quick actions for disambiguation
                        logger.info(f"[SmartProductSearch] 🔄 LLM needs clarification, returning quick actions")
                        quick_actions_data = extraction_result.get("data", {})
                        logger.info(f"[SmartProductSearch] Quick actions data: {quick_actions_data}")
                        return {
                            "success": True,
                            "needs_clarification": True,
                            "quick_actions": quick_actions_data,
                            "products": []
                        }
                    elif extraction_result.get("type") == "error":
                        # Log error but fall back to legacy extraction
                        error_msg = extraction_result.get('message', 'Unknown error')
                        logger.warning(f"[SmartProductSearch] ⚠️ LLM extraction error: {error_msg}, falling back to legacy")
                        params = self._extract_search_params_legacy(query)
                    else:
                        # Unknown type, fall back to legacy
                        logger.warning(f"[SmartProductSearch] ❓ Unknown extraction result type: {extraction_result.get('type')}, falling back to legacy")
                        params = self._extract_search_params_legacy(query)

                except Exception as e:
                    logger.error(f"[SmartProductSearch] ❌ LLM entity extraction failed: {e}, falling back to legacy", exc_info=True)
                    params = self._extract_search_params_legacy(query)
            else:
                # Fall back to legacy hardcoded extraction
                logger.info(f"[SmartProductSearch] 📌 Agent pool not available, using legacy extraction")
                logger.info(f"[SmartProductSearch] Agent pool status: {self.agent_pool}")
                params = self._extract_search_params_legacy(query)
                logger.info(f"[SmartProductSearch] Legacy extracted params: {params}")

            # Set pagination
            params["page"] = 1
            params["pageSize"] = limit

            # Add store_id if provided
            if store_id:
                params["store_id"] = store_id
                logger.info(f"[SmartProductSearch] Added store_id to params: {store_id}")

            # Override with explicit parameters if provided
            if category:
                params["category"] = category
            if strain_type:
                params["plantType"] = strain_type

            logger.info(f"[SmartProductSearch] 🔍 Calling /api/products with final params: {params}")
            logger.info(f"[SmartProductSearch] API URL: {self.base_url}/api/products")

            response = await self.client.get(
                f"{self.base_url}/api/products",
                params=params
            )

            logger.info(f"[SmartProductSearch] API Response Status: {response.status_code}")

            response.raise_for_status()

            data = response.json()
            logger.info(f"[SmartProductSearch] API Response Keys: {list(data.keys())}")

            products = data.get("data", [])  # API returns "data" not "products"

            logger.info(f"[SmartProductSearch] ✅ Returned {len(products)} products")
            if products and len(products) > 0:
                logger.info(f"[SmartProductSearch] First product sample: {products[0].get('name', 'No name')} - {products[0].get('sku', 'No SKU')}")

            # Store product list in session metadata for product selection
            if session_id and self.agent_pool and products:
                try:
                    logger.info(f"[SmartProductSearch] Storing {len(products)} products in session {session_id}")
                    self.agent_pool.store_product_list_for_session(session_id, products)
                except Exception as e:
                    logger.error(f"[SmartProductSearch] Failed to store product list in session: {e}")

            result = {
                "success": True,
                "products": products,
                "total": data.get("total", len(products)),
                "query": query
            }

            logger.info(f"[SmartProductSearch] END - Success: {result['success']}, Products: {len(products)}")
            return result

        except Exception as e:
            logger.error(f"[SmartProductSearch] ❌ FAILED: {e}", exc_info=True)
            logger.error(f"[SmartProductSearch] Error type: {type(e).__name__}")
            return {
                "success": False,
                "error": str(e),
                "products": []
            }

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
