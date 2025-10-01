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

        # Extract product subcategories (exact matches from database)
        subcategories = {
            "pre-roll": "Pre-Rolls",
            "preroll": "Pre-Rolls",
            "pre-rolls": "Pre-Rolls",
            "prerolls": "Pre-Rolls",
            "pre roll": "Pre-Rolls",
            "dried flower": "Dried Flower",
            "flower": "Dried Flower",
            "flowers": "Dried Flower",
            "bud": "Dried Flower",
            "buds": "Dried Flower",
            "edible": "Edibles",
            "edibles": "Edibles",
            "gummies": "Edibles",
            "gummy": "Edibles",
            "chocolate": "Edibles",
            "concentrate": "Concentrates",
            "concentrates": "Concentrates",
            "shatter": "Concentrates",
            "wax": "Concentrates",
            "vape": "Vaporizers",
            "vapes": "Vaporizers",
            "vaporizer": "Vaporizers",
            "cartridge": "Vaporizers",
            "cartridges": "Vaporizers",
            "oil": "Oils & Capsules",
            "oils": "Oils & Capsules",
            "capsule": "Oils & Capsules",
            "capsules": "Oils & Capsules"
        }

        for keyword, subcategory in subcategories.items():
            if keyword in query_lower:
                params["subCategory"] = subcategory
                break

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
        try:
            # Use LLM-based entity extraction if agent_pool is available
            params = {}
            if self.agent_pool and hasattr(self.agent_pool, 'extract_and_build_search_params'):
                try:
                    logger.info(f"Using LLM entity extraction for query: {query}")
                    extraction_result = await self.agent_pool.extract_and_build_search_params(
                        message=query,
                        session_id=session_id,
                        user_id=user_id
                    )

                    # Handle different result types
                    if extraction_result.get("type") == "search":
                        # Use extracted parameters
                        params = extraction_result.get("params", {})
                        logger.info(f"LLM extracted params: {params}")
                    elif extraction_result.get("type") == "quick_actions":
                        # Return quick actions for disambiguation
                        logger.info(f"LLM needs clarification, returning quick actions")
                        return {
                            "success": True,
                            "needs_clarification": True,
                            "quick_actions": extraction_result.get("data", {}),
                            "products": []
                        }
                    elif extraction_result.get("type") == "error":
                        # Log error but fall back to legacy extraction
                        logger.warning(f"LLM extraction error: {extraction_result.get('message')}, falling back to legacy")
                        params = self._extract_search_params_legacy(query)
                    else:
                        # Unknown type, fall back to legacy
                        logger.warning(f"Unknown extraction result type: {extraction_result.get('type')}, falling back to legacy")
                        params = self._extract_search_params_legacy(query)

                except Exception as e:
                    logger.error(f"LLM entity extraction failed: {e}, falling back to legacy")
                    params = self._extract_search_params_legacy(query)
            else:
                # Fall back to legacy hardcoded extraction
                logger.info(f"Agent pool not available, using legacy extraction")
                params = self._extract_search_params_legacy(query)

            # Set pagination
            params["page"] = 1
            params["pageSize"] = limit

            # Add store_id if provided
            if store_id:
                params["store_id"] = store_id

            # Override with explicit parameters if provided
            if category:
                params["category"] = category
            if strain_type:
                params["plantType"] = strain_type

            logger.info(f"Smart product search calling /api/products with params: {params}")

            response = await self.client.get(
                f"{self.base_url}/api/products",
                params=params
            )
            response.raise_for_status()

            data = response.json()
            products = data.get("data", [])  # API returns "data" not "products"

            logger.info(f"Smart product search returned {len(products)} products")

            # Store product list in session metadata for product selection
            if session_id and self.agent_pool and products:
                try:
                    self.agent_pool.store_product_list_for_session(session_id, products)
                except Exception as e:
                    logger.error(f"Failed to store product list in session: {e}")

            return {
                "success": True,
                "products": products,
                "total": data.get("total", len(products)),
                "query": query
            }

        except Exception as e:
            logger.error(f"Smart product search failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "products": []
            }

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
