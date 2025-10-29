import asyncio
import logging
import os
import base64
from typing import Dict, Any
from fastmcp import FastMCP
import snowflake.connector
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

logger = logging.getLogger(__name__)
logging.basicConfig(format="[%(levelname)s]: %(message)s", level=logging.INFO)

mcp = FastMCP("Snowflake PDC")

SNOWFLAKE_ACCOUNT = os.getenv("SNOWFLAKE_ACCOUNT", "RRNMGCG-PRODUCTDATACLOUD")
SNOWFLAKE_USER = os.getenv("SNOWFLAKE_USER", "PDCDAVID")
SNOWFLAKE_PASSWORD = os.getenv("SNOWFLAKE_PASSWORD", "jwt-auth-mode")
SNOWFLAKE_DATABASE = os.getenv("SNOWFLAKE_DATABASE", "PRODUCT_DATA_CLOUD")
SNOWFLAKE_SCHEMA = os.getenv("SNOWFLAKE_SCHEMA", "PDC_PRODUCTS")
SNOWFLAKE_WAREHOUSE = os.getenv("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH")
SNOWFLAKE_ROLE = os.getenv("SNOWFLAKE_ROLE", "ACCOUNTADMIN")
SNOWFLAKE_PRIVATE_KEY_CONTENT = os.getenv("SNOWFLAKE_PRIVATE_KEY_CONTENT")

def get_snowflake_connection():
    if not SNOWFLAKE_PRIVATE_KEY_CONTENT:
        raise ValueError("SNOWFLAKE_PRIVATE_KEY_CONTENT required")
    key_bytes = base64.b64decode(SNOWFLAKE_PRIVATE_KEY_CONTENT)
    private_key = serialization.load_pem_private_key(key_bytes, password=None, backend=default_backend())
    return snowflake.connector.connect(
        account=SNOWFLAKE_ACCOUNT, user=SNOWFLAKE_USER, private_key=private_key,
        database=SNOWFLAKE_DATABASE, schema=SNOWFLAKE_SCHEMA,
        warehouse=SNOWFLAKE_WAREHOUSE, role=SNOWFLAKE_ROLE
    )

@mcp.tool()
def snowflake_query(sql: str, max_rows: int = 20) -> Dict[str, Any]:
    """Execute SQL query on Snowflake"""
    try:
        sql_upper = sql.strip().upper()
        allowed_starts = ['SELECT', 'SHOW', 'DESCRIBE', 'CREATE', 'ALTER']
        if not any(sql_upper.startswith(k) for k in allowed_starts):
            return {"success": False, "error": "Only SELECT/SHOW/DESCRIBE/CREATE/ALTER allowed"}
        dangerous = ['DROP', 'DELETE', 'TRUNCATE']
        if any(k in sql_upper for k in dangerous):
            return {"success": False, "error": "DROP/DELETE/TRUNCATE not allowed"}
        
        conn = get_snowflake_connection()
        cursor = conn.cursor()
        cursor.execute(sql)
        
        if sql_upper.startswith(('SELECT', 'SHOW', 'DESCRIBE')):
            results = cursor.fetchmany(max_rows)
            columns = [d[0] for d in cursor.description] if cursor.description else []
            data = [dict(zip(columns, row)) for row in results]
            cursor.close()
            conn.close()
            return {"success": True, "data": data, "columns": columns, "row_count": len(data)}
        else:
            cursor.close()
            conn.close()
            return {"success": True, "message": "DDL executed"}
    except Exception as e:
        logger.error(f"Query failed: {e}")
        return {"success": False, "error": str(e)}

@mcp.tool()
def connection_status() -> Dict[str, Any]:
    """Check Snowflake connection"""
    try:
        conn = get_snowflake_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT CURRENT_TIMESTAMP(), CURRENT_USER(), CURRENT_ROLE()")
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return {"success": True, "connected": True, "timestamp": str(result[0]), 
                "user": result[1], "role": result[2], "auth_method": "JWT"}
    except Exception as e:
        return {"success": False, "connected": False, "error": str(e)}

if __name__ == "__main__":
    logger.info(f"🚀 MCP server starting on port {os.getenv('PORT', 8080)}")
    asyncio.run(
        mcp.run_async(
            transport="streamable-http",
            host="0.0.0.0",
            port=int(os.getenv("PORT", 8080)),
        )
    )
