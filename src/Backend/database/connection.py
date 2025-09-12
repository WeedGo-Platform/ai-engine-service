"""
Database Connection Module
Provides database connection utilities for the accessories system
Supports both sync (psycopg2) and async (asyncpg) connections
"""

import os
import psycopg2
from psycopg2 import pool
import asyncpg
import logging
from typing import Optional
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# Database configuration (OS-agnostic, uses environment variables)
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5434)),
    'database': os.getenv('DB_NAME', 'ai_engine'),
    'user': os.getenv('DB_USER', 'weedgo'),
    'password': os.getenv('DB_PASSWORD', 'weedgo123')
}

# Connection pools for better performance
connection_pool = None
async_pool = None

def init_connection_pool(minconn=1, maxconn=10):
    """Initialize database connection pool"""
    global connection_pool
    try:
        connection_pool = psycopg2.pool.SimpleConnectionPool(
            minconn, maxconn, **DB_CONFIG
        )
        logger.info("Database connection pool initialized")
        return connection_pool
    except Exception as e:
        logger.error(f"Failed to initialize connection pool: {e}")
        return None

def get_db_connection():
    """Get a database connection from pool or create new one"""
    global connection_pool
    
    # Try to get from pool first
    if connection_pool:
        try:
            conn = connection_pool.getconn()
            if conn:
                return conn
        except Exception as e:
            logger.warning(f"Failed to get connection from pool: {e}")
    
    # Fallback to direct connection
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        logger.error(f"Failed to create database connection: {e}")
        raise

def release_connection(conn):
    """Return connection to pool"""
    global connection_pool
    if connection_pool and conn:
        try:
            connection_pool.putconn(conn)
        except Exception as e:
            logger.warning(f"Failed to return connection to pool: {e}")
            try:
                conn.close()
            except:
                pass

@contextmanager
def get_db():
    """Context manager for database connections"""
    conn = None
    try:
        conn = get_db_connection()
        yield conn
    finally:
        if conn:
            release_connection(conn)

async def get_db_pool():
    """Get or create async database connection pool (for asyncpg)"""
    global async_pool
    if async_pool is None:
        try:
            async_pool = await asyncpg.create_pool(
                host=DB_CONFIG['host'],
                port=DB_CONFIG['port'],
                database=DB_CONFIG['database'],
                user=DB_CONFIG['user'],
                password=DB_CONFIG['password'],
                min_size=1,
                max_size=10
            )
            logger.info("Async database pool initialized")
        except Exception as e:
            logger.error(f"Failed to create async pool: {e}")
            raise
    return async_pool

# Initialize sync pool on module import
init_connection_pool()