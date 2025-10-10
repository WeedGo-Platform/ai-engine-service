"""
Product Search Tool - Uses Repository Pattern with Dependency Injection
Provides comprehensive product search capabilities for the cannabis dispensary
"""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class ProductSearchTool:
    """Tool for searching cannabis products using repository pattern"""

    def __init__(self, product_repository=None):
        """
        Initialize the product search tool with dependency injection

        Args:
            product_repository: ProductRepository instance (optional)
        """
        self.product_repository = product_repository

        # Lazy initialization if repository not provided
        if not self.product_repository:
            self._initialize_repository()

        if self.product_repository:
            count = self.product_repository.get_product_count()
            logger.info(f"ProductSearchTool initialized with {count} products available")
        else:
            logger.warning("ProductSearchTool initialized without repository")

    def _initialize_repository(self):
        """Lazy initialization of repository with proper dependencies"""
        try:
            import os
            import sys
            from pathlib import Path

            # Add parent directories to path
            backend_path = Path(__file__).parent.parent.parent
            sys.path.insert(0, str(backend_path))

            # Import dependencies
            from services.database_connection_manager import DatabaseConnectionManager
            from core.repositories.product_repository import ProductRepository

            # Initialize with proper configuration
            config = {
                'host': os.getenv('DB_HOST', 'localhost'),
                'port': int(os.getenv('DB_PORT', 5434)),
                'database': os.getenv('DB_NAME', 'ai_engine'),
                'user': os.getenv('DB_USER', 'weedgo'),
                'password': os.getenv('DB_PASSWORD', 'your_password_here'),
                'min_conn': 1,
                'max_conn': 10
            }

            # Create connection manager and repository
            connection_manager = DatabaseConnectionManager(default_config=config)
            self.product_repository = ProductRepository(connection_manager)
            logger.info("Repository initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize repository: {e}")
            self.product_repository = None

    def search_products(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        strain_type: Optional[str] = None,
        min_thc: Optional[float] = None,
        max_thc: Optional[float] = None,
        min_cbd: Optional[float] = None,
        max_cbd: Optional[float] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        effects: Optional[List[str]] = None,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Search for products with various filters

        Args:
            query: Text search query
            category: Product category (flower, edibles, concentrates, etc.)
            strain_type: Strain type (indica, sativa, hybrid)
            min_thc: Minimum THC percentage
            max_thc: Maximum THC percentage
            min_cbd: Minimum CBD percentage
            max_cbd: Maximum CBD percentage
            min_price: Minimum price
            max_price: Maximum price
            effects: List of desired effects
            limit: Maximum number of results

        Returns:
            Dictionary with search results
        """
        if not self.product_repository:
            return {
                "success": False,
                "error": "Product repository not available",
                "products": []
            }

        try:
            # Delegate to repository
            products = self.product_repository.search_products(
                query=query,
                category=category,
                strain_type=strain_type,
                min_thc=min_thc,
                max_thc=max_thc,
                min_cbd=min_cbd,
                max_cbd=max_cbd,
                min_price=min_price,
                max_price=max_price,
                effects=effects,
                limit=limit
            )

            return {
                "success": True,
                "count": len(products),
                "products": products,
                "filters_applied": {
                    "query": query,
                    "category": category,
                    "strain_type": strain_type,
                    "thc_range": [min_thc, max_thc] if min_thc or max_thc else None,
                    "cbd_range": [min_cbd, max_cbd] if min_cbd or max_cbd else None,
                    "price_range": [min_price, max_price] if min_price or max_price else None,
                    "effects": effects
                }
            }

        except Exception as e:
            logger.error(f"Product search failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "products": []
            }

    def get_product_count(self) -> int:
        """Get total number of products in database"""
        if not self.product_repository:
            return 0
        return self.product_repository.get_product_count()

    def get_trending_products(self, limit: int = 10) -> Dict[str, Any]:
        """Get trending products based on availability and popularity"""
        if not self.product_repository:
            return {"success": False, "error": "Product repository not available", "products": []}

        try:
            products = self.product_repository.get_trending_products(limit)
            return {
                "success": True,
                "count": len(products),
                "products": products
            }
        except Exception as e:
            logger.error(f"Failed to get trending products: {e}")
            return {"success": False, "error": str(e), "products": []}