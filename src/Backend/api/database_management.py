"""
Database Management API Endpoints
Provides super admin access to database tables with CRUD operations
"""

from fastapi import APIRouter, HTTPException, status, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import asyncpg
import logging
import os
import jwt
import re
from database.connection import get_db_pool
import json
from datetime import datetime, date
from decimal import Decimal
from uuid import UUID

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/database", tags=["database-management"])
security = HTTPBearer()

# JWT configuration (same as admin_auth.py)
JWT_SECRET = os.getenv('JWT_SECRET', 'dev-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'

def decode_token(token: str) -> dict:
    """Decode and validate JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

async def get_current_admin_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Get current admin user from token"""
    token = credentials.credentials
    payload = decode_token(token)

    # Check if user has admin role
    user_role = payload.get('role')
    if user_role not in ['super_admin', 'tenant_admin', 'store_manager', 'staff']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No admin access privileges"
        )

    # Return user info with is_super_admin flag
    return {
        'user_id': payload.get('user_id'),
        'email': payload.get('email'),
        'role': user_role,
        'is_super_admin': user_role == 'super_admin',
        'first_name': payload.get('first_name'),
        'last_name': payload.get('last_name'),
        'tenants': payload.get('tenants', []),
        'stores': payload.get('stores', [])
    }

async def check_super_admin(current_user: dict = Depends(get_current_admin_user)):
    """Check if the current user is a super admin"""
    if not current_user.get('is_super_admin', False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Super admin privileges required."
        )
    return current_user


def serialize_value(value):
    """Serialize database values to JSON-compatible format"""
    if value is None:
        return None
    elif isinstance(value, (datetime, date)):
        return value.isoformat()
    elif isinstance(value, Decimal):
        return float(value)
    elif isinstance(value, UUID):
        return str(value)
    elif isinstance(value, (dict, list)):
        return value
    elif isinstance(value, bytes):
        return value.hex()
    else:
        return value


@router.get("/tables")
async def get_all_tables(
    current_user: dict = Depends(check_super_admin)
):
    """
    Get list of all tables in the database with their metadata
    """
    try:
        db_pool = await get_db_pool()
        async with db_pool.acquire() as conn:
            # Get all tables with their metadata
            query = """
                SELECT DISTINCT ON (t.table_name)
                    t.table_name,
                    t.table_type,
                    obj_description(pgc.oid, 'pg_class') as table_comment,
                    pg_size_pretty(pg_table_size(pgc.oid)) as table_size,
                    (SELECT COUNT(*)
                     FROM information_schema.columns c
                     WHERE c.table_name = t.table_name
                     AND c.table_schema = t.table_schema) as column_count,
                    pgc.reltuples::bigint as estimated_row_count
                FROM information_schema.tables t
                JOIN pg_class pgc ON pgc.relname = t.table_name
                WHERE t.table_schema = 'public'
                AND t.table_type IN ('BASE TABLE', 'VIEW')
                ORDER BY t.table_name;
            """

            result = await conn.fetch(query)

            tables = []
            for row in result:
                # Get actual row count for smaller tables
                table_name = row['table_name']
                row_count = row['estimated_row_count']

                # For smaller tables, get exact count
                if row_count < 100000:  # Only get exact count for tables with < 100k rows
                    count_query = f"SELECT COUNT(*) as count FROM {table_name}"
                    try:
                        count_result = await conn.fetchval(count_query)
                        row_count = count_result
                    except:
                        pass  # Use estimated count if query fails

                tables.append({
                    'name': table_name,
                    'type': row['table_type'],
                    'comment': row['table_comment'],
                    'size': row['table_size'],
                    'column_count': row['column_count'],
                    'row_count': row_count
                })

            return {
                'success': True,
                'tables': tables,
                'total_tables': len(tables)
            }

    except Exception as e:
        logger.error(f"Error fetching tables: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch tables: {str(e)}"
        )


@router.get("/tables/{table_name}/schema")
async def get_table_schema(
    table_name: str,
    current_user: dict = Depends(check_super_admin)
):
    """
    Get the schema/structure of a specific table
    """
    try:
        db_pool = await get_db_pool()
        async with db_pool.acquire() as conn:
            # Get column information
            query = """
                SELECT
                    column_name,
                    data_type,
                    is_nullable,
                    column_default,
                    character_maximum_length,
                    numeric_precision,
                    numeric_scale
                FROM information_schema.columns
                WHERE table_name = $1 AND table_schema = 'public'
                ORDER BY ordinal_position;
            """

            columns = await conn.fetch(query, table_name)

            # Get constraints
            constraint_query = """
                SELECT
                    tc.constraint_name,
                    tc.constraint_type,
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                    ON tc.constraint_name = kcu.constraint_name
                LEFT JOIN information_schema.constraint_column_usage ccu
                    ON ccu.constraint_name = tc.constraint_name
                WHERE tc.table_name = $1 AND tc.table_schema = 'public';
            """

            constraints = await conn.fetch(constraint_query, table_name)

            # Get indexes
            index_query = """
                SELECT
                    indexname,
                    indexdef
                FROM pg_indexes
                WHERE tablename = $1 AND schemaname = 'public';
            """

            indexes = await conn.fetch(index_query, table_name)

            return {
                'success': True,
                'table_name': table_name,
                'columns': [dict(c) for c in columns],
                'constraints': [dict(c) for c in constraints],
                'indexes': [dict(i) for i in indexes]
            }

    except Exception as e:
        logger.error(f"Error fetching table schema: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch table schema: {str(e)}"
        )


@router.get("/tables/{table_name}/data")
async def get_table_data(
    table_name: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=1000),
    sort_by: Optional[str] = None,
    sort_order: str = Query('asc', regex='^(asc|desc)$'),
    search: Optional[str] = None,
    current_user: dict = Depends(check_super_admin)
):
    """
    Get data from a specific table with pagination
    """
    try:
        db_pool = await get_db_pool()
        async with db_pool.acquire() as conn:
            # Build the base query
            offset = (page - 1) * page_size

            # Get total count
            count_query = f"SELECT COUNT(*) FROM {table_name}"
            where_clause = ""

            if search:
                # Build search across all text columns
                col_query = """
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name = $1
                    AND data_type IN ('text', 'character varying', 'varchar', 'char')
                """
                text_cols = await conn.fetch(col_query, table_name)

                if text_cols:
                    search_conditions = [
                        f"CAST({col['column_name']} AS TEXT) ILIKE $1"
                        for col in text_cols
                    ]
                    where_clause = f" WHERE {' OR '.join(search_conditions)}"
                    count_query += where_clause

            if search:
                total_count = await conn.fetchval(count_query, f'%{search}%')
            else:
                total_count = await conn.fetchval(count_query)

            # Build data query
            data_query = f"SELECT * FROM {table_name}"

            if where_clause:
                data_query += where_clause

            if sort_by:
                # Validate sort column exists
                col_check = await conn.fetchval(
                    "SELECT 1 FROM information_schema.columns WHERE table_name = $1 AND column_name = $2",
                    table_name, sort_by
                )
                if col_check:
                    data_query += f" ORDER BY {sort_by} {sort_order.upper()}"

            data_query += f" LIMIT {page_size} OFFSET {offset}"

            # Fetch the data
            if search:
                rows = await conn.fetch(data_query, f'%{search}%')
            else:
                rows = await conn.fetch(data_query)

            # Serialize the data
            serialized_rows = []
            for row in rows:
                serialized_row = {}
                for key, value in row.items():
                    serialized_row[key] = serialize_value(value)
                serialized_rows.append(serialized_row)

            return {
                'success': True,
                'table_name': table_name,
                'data': serialized_rows,
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total_count': total_count,
                    'total_pages': (total_count + page_size - 1) // page_size
                }
            }

    except Exception as e:
        logger.error(f"Error fetching table data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch table data: {str(e)}"
        )


@router.post("/tables/{table_name}/data")
async def insert_table_row(
    table_name: str,
    row_data: Dict[str, Any],
    current_user: dict = Depends(check_super_admin)
):
    """
    Insert a new row into a table
    """
    try:
        db_pool = await get_db_pool()
        async with db_pool.acquire() as conn:
            # Get column types for the table
            type_query = """
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = $1 AND table_schema = 'public'
            """
            column_types = await conn.fetch(type_query, table_name)
            col_type_map = {row['column_name']: row['data_type'] for row in column_types}

            # Build insert query
            columns = list(row_data.keys())
            placeholders = [f'${i+1}' for i in range(len(columns))]

            # Convert values based on column types
            values = []
            for col in columns:
                val = row_data[col]

                # Convert datetime strings to datetime objects if needed
                if col in col_type_map:
                    col_type = col_type_map[col]
                    if col_type in ['timestamp', 'timestamp without time zone', 'timestamp with time zone']:
                        if isinstance(val, str):
                            try:
                                # Parse ISO format datetime string
                                val = datetime.fromisoformat(val.replace('Z', '+00:00'))
                            except:
                                pass  # Keep original value if parsing fails
                    elif col_type in ['date']:
                        if isinstance(val, str):
                            try:
                                # Parse ISO format date string
                                if 'T' in val:
                                    val = datetime.fromisoformat(val.replace('Z', '+00:00')).date()
                                else:
                                    val = date.fromisoformat(val)
                            except:
                                pass  # Keep original value if parsing fails
                    elif col_type in ['jsonb', 'json']:
                        # If value is already a dict or list, convert to JSON string
                        if isinstance(val, (dict, list)):
                            val = json.dumps(val)
                        elif isinstance(val, str):
                            # Validate that it's valid JSON
                            try:
                                json.loads(val)
                            except:
                                pass  # Keep original value if parsing fails

                values.append(val)

            query = f"""
                INSERT INTO {table_name} ({', '.join(columns)})
                VALUES ({', '.join(placeholders)})
                RETURNING *
            """

            result = await conn.fetchrow(query, *values)

            # Serialize the result
            serialized_result = {}
            for key, value in result.items():
                serialized_result[key] = serialize_value(value)

            return {
                'success': True,
                'message': f'Row inserted successfully into {table_name}',
                'data': serialized_result
            }

    except asyncpg.UniqueViolationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unique constraint violation: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error inserting row: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to insert row: {str(e)}"
        )


@router.put("/tables/{table_name}/data")
async def update_table_row(
    table_name: str,
    where_conditions: Dict[str, Any],
    update_data: Dict[str, Any],
    current_user: dict = Depends(check_super_admin)
):
    """
    Update row(s) in a table based on conditions
    """
    try:
        db_pool = await get_db_pool()
        async with db_pool.acquire() as conn:
            # Get column types for the table
            type_query = """
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = $1 AND table_schema = 'public'
            """
            column_types = await conn.fetch(type_query, table_name)
            col_type_map = {row['column_name']: row['data_type'] for row in column_types}

            # Build update query
            set_clauses = []
            where_clauses = []
            values = []
            param_count = 0

            # Build SET clauses with proper type conversion
            for col, val in update_data.items():
                param_count += 1
                set_clauses.append(f"{col} = ${param_count}")

                # Convert datetime strings to datetime objects if needed
                if col in col_type_map:
                    col_type = col_type_map[col]
                    if col_type in ['timestamp', 'timestamp without time zone', 'timestamp with time zone']:
                        if isinstance(val, str):
                            try:
                                # Parse ISO format datetime string
                                val = datetime.fromisoformat(val.replace('Z', '+00:00'))
                            except:
                                pass  # Keep original value if parsing fails
                    elif col_type in ['date']:
                        if isinstance(val, str):
                            try:
                                # Parse ISO format date string
                                if 'T' in val:
                                    val = datetime.fromisoformat(val.replace('Z', '+00:00')).date()
                                else:
                                    val = date.fromisoformat(val)
                            except:
                                pass  # Keep original value if parsing fails
                    elif col_type in ['jsonb', 'json']:
                        # If value is already a dict or list, convert to JSON string
                        if isinstance(val, (dict, list)):
                            val = json.dumps(val)
                        elif isinstance(val, str):
                            # Validate that it's valid JSON
                            try:
                                json.loads(val)
                            except:
                                pass  # Keep original value if parsing fails

                values.append(val)

            # Build WHERE clauses
            for col, val in where_conditions.items():
                param_count += 1
                where_clauses.append(f"{col} = ${param_count}")
                values.append(val)

            if not where_clauses:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="WHERE conditions are required for updates"
                )

            query = f"""
                UPDATE {table_name}
                SET {', '.join(set_clauses)}
                WHERE {' AND '.join(where_clauses)}
                RETURNING *
            """

            result = await conn.fetch(query, *values)

            # Serialize the results
            serialized_results = []
            for row in result:
                serialized_row = {}
                for key, value in row.items():
                    serialized_row[key] = serialize_value(value)
                serialized_results.append(serialized_row)

            return {
                'success': True,
                'message': f'{len(result)} row(s) updated in {table_name}',
                'data': serialized_results
            }

    except Exception as e:
        logger.error(f"Error updating row: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update row: {str(e)}"
        )


@router.delete("/tables/{table_name}/data")
async def delete_table_rows(
    table_name: str,
    where_conditions: Dict[str, Any],
    current_user: dict = Depends(check_super_admin)
):
    """
    Delete row(s) from a table based on conditions
    """
    try:
        db_pool = await get_db_pool()
        async with db_pool.acquire() as conn:
            # Build delete query
            where_clauses = []
            values = []

            for i, (col, val) in enumerate(where_conditions.items(), 1):
                where_clauses.append(f"{col} = ${i}")
                values.append(val)

            if not where_clauses:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="WHERE conditions are required for deletes"
                )

            query = f"""
                DELETE FROM {table_name}
                WHERE {' AND '.join(where_clauses)}
                RETURNING *
            """

            result = await conn.fetch(query, *values)

            return {
                'success': True,
                'message': f'{len(result)} row(s) deleted from {table_name}',
                'deleted_count': len(result)
            }

    except Exception as e:
        logger.error(f"Error deleting rows: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete rows: {str(e)}"
        )


class TruncateRequest(BaseModel):
    cascade: bool = False

@router.post("/tables/{table_name}/truncate")
async def truncate_table(
    table_name: str,
    request: TruncateRequest,
    current_user: dict = Depends(check_super_admin)
):
    """
    Truncate a table (remove all rows)
    """
    try:
        # Validate table name to prevent SQL injection
        if not table_name.replace('_', '').isalnum():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid table name"
            )

        db_pool = await get_db_pool()
        async with db_pool.acquire() as conn:
            # Check if table exists
            exists = await conn.fetchval(
                "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = $1 AND table_schema = 'public')",
                table_name
            )

            if not exists:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Table {table_name} not found"
                )

            # Get row count before truncate
            count_before = await conn.fetchval(f"SELECT COUNT(*) FROM {table_name}")

            # Truncate the table
            cascade_clause = "CASCADE" if request.cascade else "RESTRICT"
            await conn.execute(f"TRUNCATE TABLE {table_name} {cascade_clause}")

            return {
                'success': True,
                'message': f'Table {table_name} truncated successfully',
                'rows_deleted': count_before
            }

    except asyncpg.DependentObjectsStillExistError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot truncate table: dependent objects exist. Use cascade=true to truncate dependent tables."
        )
    except Exception as e:
        logger.error(f"Error truncating table: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to truncate table: {str(e)}"
        )


@router.delete("/tables/{table_name}/drop")
async def drop_table(
    table_name: str,
    cascade: bool = False,
    current_user: dict = Depends(check_super_admin)
):
    """
    Drop a table from the database
    """
    try:
        # Validate table name
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table_name):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid table name"
            )

        # List of protected tables that should not be dropped
        protected_tables = [
            'admin_users',
            'customer_auth',
            'stores',
            'store_addresses',
            'ocs_inventory',
            'ocs_products',
            'tenants',
            'admin_permissions',
            'admin_roles',
            'customer_profiles'
        ]

        if table_name.lower() in protected_tables:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Table {table_name} is protected and cannot be dropped"
            )

        db_pool = await get_db_pool()
        async with db_pool.acquire() as conn:
            # Check if table exists
            exists = await conn.fetchval(
                "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = $1 AND table_schema = 'public')",
                table_name
            )

            if not exists:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Table {table_name} not found"
                )

            # Get row count before drop
            count_before = await conn.fetchval(f"SELECT COUNT(*) FROM {table_name}")

            # Drop the table
            cascade_clause = "CASCADE" if cascade else "RESTRICT"
            await conn.execute(f"DROP TABLE {table_name} {cascade_clause}")

            return {
                'success': True,
                'message': f'Table {table_name} dropped successfully',
                'rows_deleted': count_before
            }

    except asyncpg.DependentObjectsStillExistError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot drop table: dependent objects exist. Use cascade=true to drop dependent objects."
        )
    except Exception as e:
        logger.error(f"Error dropping table: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to drop table: {str(e)}"
        )


@router.post("/query")
async def execute_query(
    query: str,
    current_user: dict = Depends(check_super_admin)
):
    """
    Execute a custom SQL query (SELECT only for safety)
    """
    try:
        # Only allow SELECT queries for safety
        query_lower = query.strip().lower()
        if not query_lower.startswith('select'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only SELECT queries are allowed through this endpoint"
            )

        # Check for potentially dangerous operations
        dangerous_keywords = ['drop', 'truncate', 'delete', 'update', 'insert', 'alter', 'create']
        for keyword in dangerous_keywords:
            if keyword in query_lower:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Query contains forbidden keyword: {keyword}"
                )

        db_pool = await get_db_pool()
        async with db_pool.acquire() as conn:
            result = await conn.fetch(query)

            # Serialize the results
            serialized_results = []
            for row in result:
                serialized_row = {}
                for key, value in row.items():
                    serialized_row[key] = serialize_value(value)
                serialized_results.append(serialized_row)

            return {
                'success': True,
                'data': serialized_results,
                'row_count': len(serialized_results)
            }

    except Exception as e:
        logger.error(f"Error executing query: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute query: {str(e)}"
        )


@router.get("/connection-info")
async def get_connection_info(
    current_user: dict = Depends(check_super_admin)
):
    """
    Get current database connection information
    """
    try:
        db_pool = await get_db_pool()
        async with db_pool.acquire() as conn:
            # Get database version and connection info
            version = await conn.fetchval("SELECT version()")
            current_database = await conn.fetchval("SELECT current_database()")
            current_user_db = await conn.fetchval("SELECT current_user")

            # Get database size
            size_query = """
                SELECT pg_size_pretty(pg_database_size(current_database())) as size
            """
            db_size = await conn.fetchval(size_query)

            # Get connection stats
            connection_stats = await conn.fetchrow("""
                SELECT
                    numbackends as active_connections,
                    (SELECT setting::int FROM pg_settings WHERE name = 'max_connections') as max_connections
                FROM pg_stat_database
                WHERE datname = current_database()
            """)

            return {
                'success': True,
                'connection_info': {
                    'host': os.getenv('DB_HOST', 'localhost'),
                    'port': int(os.getenv('DB_PORT', 5434)),
                    'database': current_database,
                    'user': current_user_db,
                    'version': version,
                    'size': db_size,
                    'active_connections': connection_stats['active_connections'],
                    'max_connections': connection_stats['max_connections']
                }
            }

    except Exception as e:
        logger.error(f"Error fetching connection info: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch connection info: {str(e)}"
        )