"""
Provincial Catalog Repository Interface and Implementation
Following Repository Pattern from DDD Architecture

Handles bulk import of provincial cannabis product catalogs (OCS, SQDC, AGLC, etc.)
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from decimal import Decimal
import asyncpg
import logging

from ..entities.ocs_product import OcsProduct

logger = logging.getLogger(__name__)


class IProvincialCatalogRepository(ABC):
    """Repository interface for Provincial Catalog operations"""

    @abstractmethod
    async def bulk_upsert(self, products: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Bulk upsert products from provincial catalog

        Args:
            products: List of product dictionaries with catalog data

        Returns:
            Statistics dict with inserted, updated, and error counts
        """
        pass

    @abstractmethod
    async def get_by_variant_number(self, ocs_variant_number: str) -> Optional[Dict[str, Any]]:
        """Get product by OCS variant number"""
        pass

    @abstractmethod
    async def delete_all(self) -> int:
        """Delete all products from catalog (for fresh import)"""
        pass

    @abstractmethod
    async def get_statistics(self) -> Dict[str, Any]:
        """Get catalog statistics"""
        pass


class AsyncPGProvincialCatalogRepository(IProvincialCatalogRepository):
    """AsyncPG implementation of provincial catalog repository"""

    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool

    async def bulk_upsert(self, products: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Bulk upsert products using UPSERT (INSERT ... ON CONFLICT)

        This method:
        1. Validates each product record
        2. Inserts new products or updates existing ones based on ocs_variant_number
        3. Returns statistics about the operation
        """
        stats = {
            'totalRecords': len(products),
            'inserted': 0,
            'updated': 0,
            'errors': 0,
            'error_details': []
        }

        if not products:
            return stats

        async with self.db_pool.acquire() as conn:
            # Get existing columns from database
            existing_columns = await conn.fetch("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'ocs_product_catalog'
            """)
            db_columns = {row['column_name'] for row in existing_columns}

            for idx, product_data in enumerate(products):
                try:
                    # Build column lists and values for upsert
                    columns = []
                    values = []
                    update_sets = []
                    placeholders = []

                    # Add ocs_variant_number (required field)
                    if 'ocs_variant_number' not in product_data or not product_data['ocs_variant_number']:
                        error_msg = f"Row {idx}: Missing required field 'ocs_variant_number'"
                        stats['errors'] += 1
                        if len(stats['error_details']) < 20:
                            stats['error_details'].append(error_msg)
                        continue

                    # Process each field
                    for db_col, value in product_data.items():
                        # Skip fields that don't exist in database
                        if db_col not in db_columns:
                            continue

                        # Skip auto-generated fields
                        if db_col in ['id', 'created_at']:
                            continue

                        # Skip null values
                        if value is None:
                            continue

                        columns.append(db_col)
                        values.append(value)
                        placeholders.append(f"${len(values)}")

                        # Add to update set (for ON CONFLICT)
                        if db_col not in ['ocs_variant_number']:  # Don't update the unique key
                            update_sets.append(f"{db_col} = EXCLUDED.{db_col}")

                    # Add updated_at
                    columns.append('updated_at')
                    values.append(datetime.utcnow())
                    placeholders.append(f"${len(values)}")
                    update_sets.append("updated_at = EXCLUDED.updated_at")

                    # Build the UPSERT query
                    insert_query = f"""
                        INSERT INTO ocs_product_catalog ({', '.join(columns)})
                        VALUES ({', '.join(placeholders)})
                        ON CONFLICT (ocs_variant_number) DO UPDATE SET
                        {', '.join(update_sets)}
                        RETURNING (xmax = 0) as inserted
                    """

                    # Execute the query
                    result = await conn.fetchrow(insert_query, *values)

                    if result and result['inserted']:
                        stats['inserted'] += 1
                    else:
                        stats['updated'] += 1

                except Exception as e:
                    error_msg = f"Row {idx}: {str(e)}"
                    logger.error(f"Error upserting product: {error_msg}")
                    stats['errors'] += 1
                    if len(stats['error_details']) < 20:
                        stats['error_details'].append(error_msg)
                    continue

        logger.info(f"Bulk upsert completed: {stats['inserted']} inserted, {stats['updated']} updated, {stats['errors']} errors")
        return stats

    async def get_by_variant_number(self, ocs_variant_number: str) -> Optional[Dict[str, Any]]:
        """Get product by OCS variant number"""
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM ocs_product_catalog WHERE ocs_variant_number = $1",
                ocs_variant_number
            )

            if not row:
                return None

            return dict(row)

    async def delete_all(self) -> int:
        """Delete all products from catalog"""
        async with self.db_pool.acquire() as conn:
            result = await conn.execute("DELETE FROM ocs_product_catalog")
            # Result format is "DELETE N" where N is the number of rows deleted
            count = int(result.split()[-1]) if result else 0
            logger.info(f"Deleted {count} products from catalog")
            return count

    async def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive catalog statistics"""
        async with self.db_pool.acquire() as conn:
            stats_query = """
                SELECT
                    COUNT(*) as total_products,
                    COUNT(DISTINCT brand) as total_brands,
                    COUNT(DISTINCT category) as total_categories,
                    COUNT(*) FILTER (WHERE unit_price IS NOT NULL) as products_with_price,
                    AVG(unit_price) as avg_price,
                    MIN(unit_price) as min_price,
                    MAX(unit_price) as max_price
                FROM ocs_product_catalog
            """
            stats = await conn.fetchrow(stats_query)

            return {
                'total_products': stats['total_products'] or 0,
                'total_brands': stats['total_brands'] or 0,
                'total_categories': stats['total_categories'] or 0,
                'products_with_price': stats['products_with_price'] or 0,
                'avg_price': float(stats['avg_price']) if stats['avg_price'] else 0.0,
                'min_price': float(stats['min_price']) if stats['min_price'] else 0.0,
                'max_price': float(stats['max_price']) if stats['max_price'] else 0.0
            }
