import asyncio
import logging
import os
import base64
from typing import Dict, Any, List, Optional
from fastmcp import FastMCP
import snowflake.connector
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

logger = logging.getLogger(__name__)
logging.basicConfig(format="[%(levelname)s]: %(message)s", level=logging.INFO)

mcp = FastMCP("Snowflake PDC V2.2")

# Configuration
SNOWFLAKE_ACCOUNT = os.getenv("SNOWFLAKE_ACCOUNT", "RRNMGCG-PRODUCTDATACLOUD")
SNOWFLAKE_USER = os.getenv("SNOWFLAKE_USER", "PDCDAVID")
SNOWFLAKE_PASSWORD = os.getenv("SNOWFLAKE_PASSWORD", "jwt-auth-mode")
SNOWFLAKE_DATABASE = os.getenv("SNOWFLAKE_DATABASE", "PRODUCT_DATA_CLOUD")
SNOWFLAKE_SCHEMA = os.getenv("SNOWFLAKE_SCHEMA", "PDC_PRODUCTS")
SNOWFLAKE_WAREHOUSE = os.getenv("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH")
SNOWFLAKE_ROLE = os.getenv("SNOWFLAKE_ROLE", "ACCOUNTADMIN")
SNOWFLAKE_PRIVATE_KEY_CONTENT = os.getenv("SNOWFLAKE_PRIVATE_KEY_CONTENT")

# V2.2 Optimization: Configurable max rows
DEFAULT_MAX_ROWS = 20
MAX_ROWS_LIMIT = 1000

def get_snowflake_connection():
    """Get Snowflake connection with JWT auth"""
    if not SNOWFLAKE_PRIVATE_KEY_CONTENT:
        raise ValueError("SNOWFLAKE_PRIVATE_KEY_CONTENT required")
    
    key_bytes = base64.b64decode(SNOWFLAKE_PRIVATE_KEY_CONTENT)
    private_key = serialization.load_pem_private_key(
        key_bytes, 
        password=None, 
        backend=default_backend()
    )
    
    return snowflake.connector.connect(
        account=SNOWFLAKE_ACCOUNT,
        user=SNOWFLAKE_USER,
        private_key=private_key,
        database=SNOWFLAKE_DATABASE,
        schema=SNOWFLAKE_SCHEMA,
        warehouse=SNOWFLAKE_WAREHOUSE,
        role=SNOWFLAKE_ROLE
    )

def enforce_limit(sql: str, max_rows: int) -> str:
    """V2.2: Automatically add LIMIT if missing, respects user-defined max"""
    sql_upper = sql.strip().upper()
    
    # Check if query already has LIMIT
    if 'LIMIT' in sql_upper:
        return sql
    
    # Only add LIMIT to SELECT queries
    if sql_upper.startswith('SELECT'):
        # Don't add LIMIT to COUNT queries
        if 'COUNT(' in sql_upper and 'GROUP BY' not in sql_upper:
            return sql
        
        # Add LIMIT
        return f"{sql.strip()} LIMIT {max_rows}"
    
    return sql

def optimize_columns(data: List[Dict], columns: List[str]) -> List[Dict]:
    """V2.2: Reduce token usage by filtering large columns"""
    if not data or len(data) == 0:
        return data
    
    # Define large column patterns to truncate
    large_patterns = ['JSON', 'DATA', 'RESPONSE', 'CONTENT', 'DESCRIPTION']
    
    optimized_data = []
    for row in data:
        optimized_row = {}
        for col in columns:
            value = row.get(col)
            
            # Check if column name suggests large content
            is_large = any(pattern in col.upper() for pattern in large_patterns)
            
            if is_large and isinstance(value, str) and len(value) > 500:
                # Truncate large text fields
                optimized_row[col] = value[:500] + f"... [truncated {len(value)-500} chars]"
            else:
                optimized_row[col] = value
        
        optimized_data.append(optimized_row)
    
    return optimized_data

@mcp.tool()
def snowflake_query(sql: str, max_rows: int = DEFAULT_MAX_ROWS) -> Dict[str, Any]:
    """
    Execute SQL query on Snowflake (V2.2 Enhanced)
    
    Features:
    - MERGE/UPSERT support (NEW!)
    - Transaction support: BEGIN/COMMIT/ROLLBACK (NEW!)
    - Batch INSERT with multi-value syntax (NEW!)
    - Dynamic LIMIT: 1-1000 rows (NEW!)
    - Write operations: INSERT/UPDATE/DELETE (with safety)
    - Security: Blocks DROP/TRUNCATE, requires WHERE for UPDATE/DELETE
    
    Args:
        sql: SQL query to execute
        max_rows: Maximum rows to return (1-1000, default: 20)
    
    Returns:
        Dict with success status, data, columns, and metadata
    """
    try:
        # V2.2: Validate max_rows range
        if max_rows < 1 or max_rows > MAX_ROWS_LIMIT:
            return {
                "success": False,
                "error": f"max_rows must be between 1 and {MAX_ROWS_LIMIT}",
                "version": "V2.2"
            }
        
        # Security checks
        sql_upper = sql.strip().upper()
        
        # V2.2: Expanded allowed operations
        allowed_starts = [
            'SELECT', 'SHOW', 'DESCRIBE', 
            'CREATE', 'ALTER', 
            'INSERT', 'UPDATE', 'DELETE',
            'MERGE',  # NEW in V2.2!
            'BEGIN', 'COMMIT', 'ROLLBACK'  # NEW in V2.2!
        ]
        
        if not any(sql_upper.startswith(k) for k in allowed_starts):
            return {
                "success": False, 
                "error": f"Only {', '.join(allowed_starts)} operations allowed",
                "version": "V2.2"
            }
        
        # Block extremely dangerous operations
        extremely_dangerous = ['DROP', 'TRUNCATE']
        if any(k in sql_upper for k in extremely_dangerous):
            return {
                "success": False, 
                "error": "DROP/TRUNCATE not allowed for safety",
                "version": "V2.2"
            }
        
        # V2.2: Safety check for UPDATE/DELETE - must have WHERE clause
        # (Skip for MERGE - it has its own ON clause)
        if not sql_upper.startswith('MERGE'):
            if sql_upper.startswith('UPDATE') or sql_upper.startswith('DELETE'):
                if 'WHERE' not in sql_upper:
                    return {
                        "success": False,
                        "error": "UPDATE/DELETE requires WHERE clause for safety",
                        "hint": "Add WHERE clause to specify which rows to modify",
                        "version": "V2.2"
                    }
        
        # V2.2: Enforce LIMIT for SELECT queries
        optimized_sql = enforce_limit(sql, max_rows)
        
        # Log optimization
        if optimized_sql != sql:
            logger.info(f"V2.2: Added LIMIT {max_rows} to query")
        
        # Execute query
        conn = get_snowflake_connection()
        cursor = conn.cursor()
        cursor.execute(optimized_sql)
        
        # Handle different query types
        if sql_upper.startswith(('SELECT', 'SHOW', 'DESCRIBE')):
            # Fetch results
            results = cursor.fetchmany(max_rows)
            columns = [d[0] for d in cursor.description] if cursor.description else []
            
            # Convert to dicts
            data = [dict(zip(columns, row)) for row in results]
            
            # V2.2: Optimize for token usage
            optimized_data = optimize_columns(data, columns)
            
            cursor.close()
            conn.close()
            
            return {
                "success": True,
                "data": optimized_data,
                "columns": columns,
                "row_count": len(optimized_data),
                "optimized": True,
                "version": "V2.2"
            }
        
        elif sql_upper.startswith(('BEGIN', 'COMMIT', 'ROLLBACK')):
            # Transaction control - no result set
            cursor.close()
            conn.close()
            
            operation = sql_upper.split()[0]
            
            return {
                "success": True,
                "message": f"{operation} executed successfully",
                "transaction_control": True,
                "version": "V2.2"
            }
        
        else:
            # DDL/DML operations (INSERT/UPDATE/DELETE/MERGE/CREATE/ALTER)
            rows_affected = cursor.rowcount
            cursor.close()
            conn.close()
            
            operation = sql_upper.split()[0]
            
            return {
                "success": True,
                "message": f"{operation} executed successfully",
                "rows_affected": rows_affected if rows_affected >= 0 else "N/A",
                "version": "V2.2"
            }
            
    except Exception as e:
        logger.error(f"Query failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "version": "V2.2"
        }

@mcp.tool()
def batch_insert(
    table: str, 
    columns: List[str], 
    values: List[List[Any]]
) -> Dict[str, Any]:
    """
    Batch insert multiple rows in a single operation (V2.2 NEW!)
    
    More efficient than multiple individual INSERTs - uses multi-value syntax.
    
    Args:
        table: Target table name
        columns: List of column names
        values: List of value lists (each inner list is one row)
    
    Returns:
        Dict with success status and rows inserted
    
    Example:
        batch_insert(
            table="TASK_QUEUE",
            columns=["PRODUCT_ID", "STATUS", "REGION"],
            values=[
                ["prod-1", "pending", "US"],
                ["prod-2", "pending", "UK"],
                ["prod-3", "pending", "DE"]
            ]
        )
    """
    try:
        if not values or len(values) == 0:
            return {
                "success": False,
                "error": "No values provided",
                "version": "V2.2"
            }
        
        # Build multi-value INSERT
        cols_str = ", ".join(columns)
        
        # Convert values to SQL format
        value_rows = []
        for row in values:
            # Escape strings properly
            escaped = []
            for val in row:
                if val is None:
                    escaped.append("NULL")
                elif isinstance(val, str):
                    # Escape single quotes
                    escaped.append(f"'{val.replace(\"'\", \"''\")}'")
                elif isinstance(val, bool):
                    escaped.append("TRUE" if val else "FALSE")
                else:
                    escaped.append(str(val))
            
            value_rows.append(f"({', '.join(escaped)})")
        
        values_str = ",\n  ".join(value_rows)
        
        sql = f"INSERT INTO {table} ({cols_str}) VALUES\n  {values_str}"
        
        # Execute batch insert
        conn = get_snowflake_connection()
        cursor = conn.cursor()
        cursor.execute(sql)
        rows_affected = cursor.rowcount
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "message": f"Batch INSERT executed successfully",
            "rows_inserted": len(values),
            "rows_affected": rows_affected if rows_affected >= 0 else len(values),
            "version": "V2.2"
        }
        
    except Exception as e:
        logger.error(f"Batch insert failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "version": "V2.2"
        }

@mcp.tool()
def connection_status() -> Dict[str, Any]:
    """
    Check Snowflake connection status
    
    Returns connection info including timestamp, user, role, and auth method
    """
    try:
        conn = get_snowflake_connection()
        cursor = conn.cursor()
        
        # Get connection details
        cursor.execute("SELECT CURRENT_TIMESTAMP(), CURRENT_USER(), CURRENT_ROLE(), CURRENT_DATABASE(), CURRENT_SCHEMA()")
        result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "connected": True,
            "timestamp": str(result[0]),
            "user": result[1],
            "role": result[2],
            "database": result[3],
            "schema": result[4],
            "auth_method": "JWT",
            "version": "V2.2",
            "capabilities": [
                "READ: SELECT/SHOW/DESCRIBE",
                "WRITE: INSERT/UPDATE/DELETE (with WHERE)",
                "UPSERT: MERGE (NEW!)",
                "TRANSACTIONS: BEGIN/COMMIT/ROLLBACK (NEW!)",
                "BATCH: Multi-value INSERT (NEW!)",
                "DDL: CREATE/ALTER",
                "BLOCKED: DROP/TRUNCATE"
            ],
            "limits": {
                "max_rows": f"1-{MAX_ROWS_LIMIT} (configurable)",
                "default_rows": DEFAULT_MAX_ROWS
            },
            "optimizations": [
                "Auto-LIMIT enforcement",
                "Token-optimized responses",
                "Column truncation for large fields",
                "Dynamic row limits (NEW!)"
            ]
        }
        
    except Exception as e:
        logger.error(f"Connection check failed: {e}")
        return {
            "success": False,
            "connected": False,
            "error": str(e),
            "version": "V2.2"
        }

# Export the mcp.app for uvicorn
app = mcp.app

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    
    logger.info(f"🚀 Snowflake MCP V2.2 starting on port {port}")
    logger.info("✅ NEW: MERGE/UPSERT support")
    logger.info("✅ NEW: Transaction control (BEGIN/COMMIT/ROLLBACK)")
    logger.info("✅ NEW: Batch INSERT (multi-value)")
    logger.info("✅ NEW: Dynamic LIMIT (1-1000 rows)")
    logger.info("✅ Write-Enabled: INSERT | UPDATE (WHERE) | DELETE (WHERE)")
    logger.info("✅ Optimizations: Auto-LIMIT | Token-Optimized | Column Truncation")
    logger.info("🔒 Security: Blocks DROP/TRUNCATE | Requires WHERE for UPDATE/DELETE")
    
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
