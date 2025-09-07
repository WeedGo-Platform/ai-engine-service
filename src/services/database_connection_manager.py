"""
Database Connection Manager
Implements IDatabaseConnectionManager interface following SOLID principles
Handles database connection lifecycle management
"""

import psycopg2
import psycopg2.pool
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
import sys

# Import interface
sys.path.append(str(Path(__file__).parent.parent))
from core.interfaces import IDatabaseConnectionManager

logger = logging.getLogger(__name__)


class DatabaseConnectionManager(IDatabaseConnectionManager):
    """
    Database Connection Manager implementation
    Single Responsibility: Connection lifecycle management
    """
    
    def __init__(self, default_config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Database Connection Manager
        
        Args:
            default_config: Optional default database configuration
        """
        self.connections = {}
        self.connection_pools = {}
        self.default_config = default_config or self._get_default_config()
        logger.info("DatabaseConnectionManager initialized")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default database configuration"""
        import os
        return {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 5432)),
            'database': os.getenv('DB_NAME', 'weedgo'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'postgres'),
            'min_conn': 1,
            'max_conn': 10
        }
    
    def get_connection(self, connection_name: str = "default") -> Any:
        """
        Get a database connection by name
        
        Args:
            connection_name: Name of the connection
            
        Returns:
            Database connection object or None
        """
        # Check if connection pool exists
        if connection_name in self.connection_pools:
            try:
                pool = self.connection_pools[connection_name]
                conn = pool.getconn()
                if conn and not conn.closed:
                    return conn
                else:
                    # Connection is closed, remove it
                    if conn:
                        pool.putconn(conn)
                    logger.warning(f"Connection '{connection_name}' was closed, attempting reconnect")
                    return self._reconnect(connection_name)
            except Exception as e:
                logger.error(f"Failed to get connection from pool '{connection_name}': {e}")
                return None
        
        # Try to create connection if not exists
        if connection_name == "default" and connection_name not in self.connection_pools:
            if self.create_connection(connection_name, self.default_config):
                return self.get_connection(connection_name)
        
        logger.warning(f"Connection '{connection_name}' not found")
        return None
    
    def create_connection(self, connection_name: str, config: Dict[str, Any]) -> bool:
        """
        Create a new database connection pool
        
        Args:
            connection_name: Name for the connection
            config: Database configuration
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Close existing connection if any
            if connection_name in self.connection_pools:
                self.close_connection(connection_name)
            
            # Create connection pool
            min_conn = config.get('min_conn', 1)
            max_conn = config.get('max_conn', 10)
            
            pool = psycopg2.pool.ThreadedConnectionPool(
                min_conn,
                max_conn,
                host=config.get('host'),
                port=config.get('port'),
                database=config.get('database'),
                user=config.get('user'),
                password=config.get('password')
            )
            
            # Test connection
            test_conn = pool.getconn()
            if test_conn:
                test_conn.close()
                pool.putconn(test_conn)
                
                self.connection_pools[connection_name] = pool
                logger.info(f"Created connection pool '{connection_name}' with {min_conn}-{max_conn} connections")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to create connection '{connection_name}': {e}")
            return False
    
    def close_connection(self, connection_name: str) -> None:
        """
        Close a specific connection pool
        
        Args:
            connection_name: Name of the connection to close
        """
        try:
            if connection_name in self.connection_pools:
                pool = self.connection_pools[connection_name]
                pool.closeall()
                del self.connection_pools[connection_name]
                logger.info(f"Closed connection pool '{connection_name}'")
        except Exception as e:
            logger.error(f"Failed to close connection '{connection_name}': {e}")
    
    def close_all_connections(self) -> None:
        """Close all connection pools"""
        connection_names = list(self.connection_pools.keys())
        for name in connection_names:
            self.close_connection(name)
        logger.info("Closed all database connections")
    
    def get_connection_status(self, connection_name: str) -> Dict[str, Any]:
        """
        Get status of a specific connection pool
        
        Args:
            connection_name: Name of the connection
            
        Returns:
            Status dictionary
        """
        if connection_name not in self.connection_pools:
            return {
                'name': connection_name,
                'status': 'not_found',
                'connected': False
            }
        
        try:
            pool = self.connection_pools[connection_name]
            
            # Get pool statistics
            status = {
                'name': connection_name,
                'status': 'active',
                'connected': True,
                'min_connections': pool.minconn,
                'max_connections': pool.maxconn,
                'closed': pool.closed
            }
            
            # Test connection
            try:
                test_conn = pool.getconn()
                if test_conn:
                    status['connection_test'] = 'passed'
                    pool.putconn(test_conn)
                else:
                    status['connection_test'] = 'failed'
                    status['connected'] = False
            except:
                status['connection_test'] = 'failed'
                status['connected'] = False
            
            return status
            
        except Exception as e:
            return {
                'name': connection_name,
                'status': 'error',
                'connected': False,
                'error': str(e)
            }
    
    def list_connections(self) -> List[str]:
        """
        List all active connection pool names
        
        Returns:
            List of connection names
        """
        return list(self.connection_pools.keys())
    
    def _reconnect(self, connection_name: str) -> Optional[Any]:
        """
        Attempt to reconnect a connection
        
        Args:
            connection_name: Name of the connection
            
        Returns:
            New connection or None
        """
        if connection_name == "default":
            # Try to recreate with default config
            if self.create_connection(connection_name, self.default_config):
                return self.get_connection(connection_name)
        
        return None
    
    def return_connection(self, connection_name: str, conn: Any) -> None:
        """
        Return a connection to the pool
        
        Args:
            connection_name: Name of the connection pool
            conn: Connection to return
        """
        if connection_name in self.connection_pools:
            try:
                pool = self.connection_pools[connection_name]
                pool.putconn(conn)
            except Exception as e:
                logger.error(f"Failed to return connection to pool '{connection_name}': {e}")
    
    def __del__(self):
        """Cleanup on deletion"""
        try:
            self.close_all_connections()
        except:
            pass