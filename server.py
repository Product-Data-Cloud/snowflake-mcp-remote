import asyncio
import logging
import os
import base64
from typing import Dict, Any, List
from fastmcp import FastMCP
import snowflake.connector
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

logger = logging.getLogger(__name__)
logging.basicConfig(format="[%(levelname)s]: %(message)s", level=logging.INFO)

mcp = FastMCP("Snowflake PDC V2.0")

# Configuration
SNOWFLAKE_ACCOUNT = os.getenv("SNOWFLAKE_ACCOUNT", "RRNMGCG-PRODUCTDATACLOUD")
SNOWFLAKE_USER = os.getenv("SNOWFLAKE_USER", "PDCDAVID")
SNOWFLAKE_PASSWORD = os.getenv("SNOWFLAKE_PASSWORD", "jwt-auth-mode")
SNOWFLAKE_DATABASE = os.getenv("SNOWFLAKE_DATABASE", "PRODUCT_DATA_CLOUD")
SNOWFLAKE_SCHEMA = os.getenv("SNOWFLAKE_SCHEMA", "PDC_PRODUCTS")
SNOWFLAKE_WAREHOUSE = os.getenv("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH")
SNOWFLAKE_ROLE = os.getenv("SNOWFLAKE_ROLE", "ACCOUNTADMIN")
SNOWFLAKE_PRIVATE_KEY_CONTENT = os.getenv("SNOWFLAKE_PRIVATE_KEY_CONTENT")

# V2.0 Optimization: Default max rows
DEFAULT_MAX_ROWS = 20

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
    """V2.0: Automatically add LIMIT if missing"""
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
    """V2.0: Reduce token usage by filtering large columns"""
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
    Execute SQL query on Snowflake (V2.0 Optimized)
    
    Features:
    - Automatic LIMIT enforcement (default: 20 rows)
    - Token optimization (truncates large fields)
    - Security checks (no DROP/DELETE/TRUNCATE)
    
    Args:
        sql: SQL query to execute
        max_rows: Maximum rows to return (default: 20)
    
    Returns:
        Dict with success status, data, columns, and metadata
    """
    try:
        # Security checks
        sql_upper = sql.strip().upper()
        
        # Allow only safe operations
        allowed_starts = ['SELECT', 'SHOW', 'DESCRIBE', 'CREATE', 'ALTER']
        if not any(sql_upper.startswith(k) for k in allowed_starts):
            return {
                "success": False, 
                "error": "Only SELECT/SHOW/DESCRIBE/CREATE/ALTER allowed"
            }
        
        # Block dangerous operations
        dangerous = ['DROP', 'DELETE', 'TRUNCATE']
        if any(k in sql_upper for k in dangerous):
            return {
                "success": False, 
                "error": "DROP/DELETE/TRUNCATE not allowed"
            }
        
        # V2.0: Enforce LIMIT for SELECT queries
        optimized_sql = enforce_limit(sql, max_rows)
        
        # Log optimization
        if optimized_sql != sql:
            logger.info(f"V2.0: Added LIMIT {max_rows} to query")
        
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
            
            # V2.0: Optimize for token usage
            optimized_data = optimize_columns(data, columns)
            
            cursor.close()
            conn.close()
            
            return {
                "success": True,
                "data": optimized_data,
                "columns": columns,
                "row_count": len(optimized_data),
                "optimized": True,
                "version": "V2.0"
            }
        else:
            # DDL operations
            cursor.close()
            conn.close()
            
            return {
                "success": True,
                "message": "DDL executed successfully",
                "version": "V2.0"
            }
            
    except Exception as e:
        logger.error(f"Query failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "version": "V2.0"
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
            "version": "V2.0",
            "optimizations": [
                "Auto-LIMIT enforcement",
                "Token-optimized responses",
                "Column truncation for large fields"
            ]
        }
        
    except Exception as e:
        logger.error(f"Connection check failed: {e}")
        return {
            "success": False,
            "connected": False,
            "error": str(e),
            "version": "V2.0"
        }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    logger.info(f"🚀 Snowflake MCP V2.0 starting on port {port}")
    logger.info("✅ Optimizations: Auto-LIMIT | Token-Optimized | Column Truncation")
    
    asyncio.run(
        mcp.run_async(
            transport="streamable-http",
            host="0.0.0.0",
            port=port,
        )
    )
