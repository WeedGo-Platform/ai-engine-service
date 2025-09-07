"""
Database Search Tool
Implements IDatabaseSearchTool interface following SOLID principles
Provides database search functionality that agents can enroll to use
"""

import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
import sys

# Import interfaces
sys.path.append(str(Path(__file__).parent.parent.parent))
from core.interfaces import IDatabaseSearchTool, IDatabaseConnectionManager
from services.database_connection_manager import DatabaseConnectionManager

logger = logging.getLogger(__name__)


class DatabaseSearchTool(IDatabaseSearchTool):
    """
    Database Search Tool implementation
    Single Responsibility: Execute database searches with supplied parameters
    """
    
    def __init__(self, connection_manager: Optional[IDatabaseConnectionManager] = None):
        """
        Initialize the Database Search Tool
        
        Args:
            connection_manager: Optional connection manager instance
        """
        self.connection_manager = connection_manager or DatabaseConnectionManager()
        self.current_connection = None
        self.connection_name = "search_tool"
        logger.info("DatabaseSearchTool initialized")
    
    def connect(self, connection_params: Dict[str, Any]) -> bool:
        """
        Establish database connection
        
        Args:
            connection_params: Database connection parameters
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create connection through manager
            success = self.connection_manager.create_connection(
                self.connection_name,
                connection_params
            )
            
            if success:
                self.current_connection = self.connection_manager.get_connection(self.connection_name)
                logger.info("Database search tool connected successfully")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            return False
    
    def disconnect(self) -> None:
        """Close database connection"""
        try:
            if self.current_connection:
                # Return connection to pool
                self.connection_manager.return_connection(self.connection_name, self.current_connection)
                self.current_connection = None
            
            # Close the connection pool
            self.connection_manager.close_connection(self.connection_name)
            logger.info("Database search tool disconnected")
            
        except Exception as e:
            logger.error(f"Error disconnecting: {e}")
    
    def search(self, query_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Execute generic search query with parameters
        
        Args:
            query_params: Query parameters including:
                - table: Table name to search
                - filters: Dictionary of column:value filters
                - columns: List of columns to return
                - limit: Maximum results
                - order_by: Column to sort by
                
        Returns:
            List of matching records
        """
        if not self.is_connected():
            logger.error("Database not connected")
            return []
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Build query
            table = query_params.get('table', 'products')
            filters = query_params.get('filters', {})
            columns = query_params.get('columns', ['*'])
            limit = query_params.get('limit', 10)
            order_by = query_params.get('order_by', None)
            
            # Construct SELECT
            column_str = ', '.join(columns) if columns != ['*'] else '*'
            query = f"SELECT {column_str} FROM {table}"
            
            # Add WHERE clause
            where_conditions = []
            params = []
            
            for col, val in filters.items():
                if isinstance(val, list):
                    # Handle IN clause
                    placeholders = ', '.join(['%s'] * len(val))
                    where_conditions.append(f"{col} IN ({placeholders})")
                    params.extend(val)
                elif isinstance(val, dict):
                    # Handle operators like {'gt': 50, 'lt': 100}
                    for op, op_val in val.items():
                        if op == 'gt':
                            where_conditions.append(f"{col} > %s")
                        elif op == 'gte':
                            where_conditions.append(f"{col} >= %s")
                        elif op == 'lt':
                            where_conditions.append(f"{col} < %s")
                        elif op == 'lte':
                            where_conditions.append(f"{col} <= %s")
                        elif op == 'like':
                            where_conditions.append(f"{col} ILIKE %s")
                        elif op == 'not':
                            where_conditions.append(f"{col} != %s")
                        params.append(op_val)
                else:
                    # Simple equality
                    where_conditions.append(f"{col} = %s")
                    params.append(val)
            
            if where_conditions:
                query += " WHERE " + " AND ".join(where_conditions)
            
            # Add ORDER BY
            if order_by:
                query += f" ORDER BY {order_by}"
            
            # Add LIMIT
            query += f" LIMIT {limit}"
            
            # Execute query
            cursor.execute(query, params)
            
            # Get column names
            col_names = [desc[0] for desc in cursor.description]
            
            # Fetch results
            rows = cursor.fetchall()
            results = []
            
            for row in rows:
                result = dict(zip(col_names, row))
                # Convert any non-serializable types
                for key, val in result.items():
                    if hasattr(val, 'isoformat'):
                        result[key] = val.isoformat()
                    elif isinstance(val, bytes):
                        result[key] = val.decode('utf-8', errors='ignore')
                results.append(result)
            
            cursor.close()
            return results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def search_products(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Search for products with specific filters
        
        Args:
            filters: Product search filters
            
        Returns:
            List of matching products
        """
        query_params = {
            'table': 'products',
            'filters': filters,
            'columns': [
                'id', 'name', 'category', 'subcategory',
                'thc_content', 'cbd_content', 'price',
                'in_stock', 'description', 'effects'
            ],
            'limit': filters.get('limit', 10),
            'order_by': filters.get('order_by', 'name')
        }
        
        # Remove meta keys from filters
        for key in ['limit', 'order_by']:
            if key in query_params['filters']:
                del query_params['filters'][key]
        
        return self.search(query_params)
    
    def search_by_category(self, category: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search products by category
        
        Args:
            category: Product category
            limit: Maximum results
            
        Returns:
            List of products in category
        """
        return self.search_products({
            'category': category,
            'in_stock': True,
            'limit': limit
        })
    
    def search_by_effects(self, effects: List[str], limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search products by effects
        
        Args:
            effects: List of desired effects
            limit: Maximum results
            
        Returns:
            List of products with matching effects
        """
        if not self.is_connected():
            return []
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Build query for products with any of the specified effects
            effects_conditions = []
            params = []
            
            for effect in effects:
                effects_conditions.append("effects::text ILIKE %s")
                params.append(f"%{effect}%")
            
            query = f"""
                SELECT id, name, category, subcategory,
                       thc_content, cbd_content, price,
                       in_stock, description, effects
                FROM products
                WHERE in_stock = true
                  AND ({' OR '.join(effects_conditions)})
                LIMIT %s
            """
            params.append(limit)
            
            cursor.execute(query, params)
            
            # Get column names and fetch results
            col_names = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            results = []
            
            for row in rows:
                result = dict(zip(col_names, row))
                # Convert effects JSON to list if needed
                if isinstance(result.get('effects'), str):
                    try:
                        result['effects'] = json.loads(result['effects'])
                    except:
                        pass
                results.append(result)
            
            cursor.close()
            return results
            
        except Exception as e:
            logger.error(f"Search by effects failed: {e}")
            return []
    
    def get_product_details(self, product_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific product
        
        Args:
            product_id: Product identifier
            
        Returns:
            Product details or None
        """
        results = self.search({
            'table': 'products',
            'filters': {'id': product_id},
            'limit': 1
        })
        
        return results[0] if results else None
    
    def is_connected(self) -> bool:
        """
        Check if database is connected
        
        Returns:
            True if connected, False otherwise
        """
        if not self.current_connection:
            # Try to get connection from pool
            self.current_connection = self.connection_manager.get_connection(self.connection_name)
        
        if self.current_connection:
            try:
                # Test connection
                cursor = self.current_connection.cursor()
                cursor.execute("SELECT 1")
                cursor.close()
                return True
            except:
                self.current_connection = None
                return False
        
        return False
    
    def _get_connection(self):
        """
        Get active connection
        
        Returns:
            Database connection
        """
        if not self.current_connection:
            self.current_connection = self.connection_manager.get_connection(self.connection_name)
        return self.current_connection
    
    def execute_raw_query(self, query: str, params: Optional[List] = None) -> List[Dict[str, Any]]:
        """
        Execute a raw SQL query (for advanced use)
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            Query results
        """
        if not self.is_connected():
            logger.error("Database not connected")
            return []
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Execute query
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # Get results for SELECT queries
            if cursor.description:
                col_names = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                results = []
                
                for row in rows:
                    result = dict(zip(col_names, row))
                    results.append(result)
                
                cursor.close()
                return results
            else:
                # For non-SELECT queries
                conn.commit()
                cursor.close()
                return [{'affected_rows': cursor.rowcount}]
                
        except Exception as e:
            logger.error(f"Raw query execution failed: {e}")
            if conn:
                conn.rollback()
            return []
    
    def __del__(self):
        """Cleanup on deletion"""
        try:
            self.disconnect()
        except:
            pass