# Snowflake Remote MCP Server V2.1

Remote MCP server for Snowflake database access with write capabilities.

## 🚀 Features

**V2.1 - Write-Enabled:**
- ✅ **Read Operations:** SELECT, SHOW, DESCRIBE
- ✅ **Write Operations:** INSERT, UPDATE, DELETE (with safety checks)
- ✅ **DDL Operations:** CREATE, ALTER
- 🔒 **Security:** Blocks DROP/TRUNCATE, requires WHERE for UPDATE/DELETE
- ⚡ **Optimizations:** Auto-LIMIT, token-optimized responses, column truncation

## 📡 Deployment

### Option 1: Auto-Deploy via Cloud Build Trigger (Recommended)

**One-time setup:**
```bash
# In Google Cloud Console → Cloud Build → Triggers → Create Trigger
Name: snowflake-mcp-auto-deploy
Event: Push to branch
Branch: ^main$
Configuration: Cloud Build configuration file (cloudbuild.yaml)
```

Then: Push to main → Auto-deploy (3-5 min)

### Option 2: Manual Deploy

```bash
# In Cloud Shell
cd ~/snowflake-mcp-remote
git pull

gcloud run deploy snowflake-mcp \
  --source . \
  --region=europe-west1 \
  --platform=managed \
  --allow-unauthenticated \
  --update-secrets=SNOWFLAKE_PRIVATE_KEY_CONTENT=snowflake-private-key:latest
```

## 🔗 Usage

**Service URL:** `https://snowflake-mcp-va6ytiztka-ew.a.run.app/mcp`

**Add to claude.ai:**
1. Settings → Connectors → Add Custom Connector
2. Name: Snowflake PDC V2.1
3. URL: (service URL above)
4. Save

## 🛠️ Tools

### `snowflake_query(sql: str, max_rows: int = 20)`

Execute SQL with automatic optimizations.

**Examples:**

```python
# Read operations
snowflake_query("SELECT * FROM PRODUCT")

# Write operations (NEW in V2.1!)
snowflake_query("INSERT INTO PRODUCT (PRODUCT_ID, REGION) VALUES ('123', 'US')")

snowflake_query("UPDATE PRODUCT SET IS_ACTIVE = FALSE WHERE PRODUCT_ID = '123'")

snowflake_query("DELETE FROM PRODUCT_QUEUE WHERE STATUS = 'completed' AND CREATED_AT < '2024-01-01'")

# DDL operations
snowflake_query("CREATE VIEW active_products AS SELECT * FROM PRODUCT WHERE IS_ACTIVE = TRUE")
```

**Safety Features:**
- UPDATE/DELETE require WHERE clause
- DROP/TRUNCATE blocked
- Auto-LIMIT for SELECT queries

### `connection_status()`

Check connection health and capabilities.

## 📊 Version History

- **V2.1** (2025-11-02): Write operations enabled with safety checks
- **V2.0** (2025-10-29): Initial remote MCP with read + DDL
- **V1.0** (2025-10-24): Local MCP prototype

## 🔐 Security

**Environment Variables:**
- `SNOWFLAKE_ACCOUNT`: RRNMGCG-PRODUCTDATACLOUD
- `SNOWFLAKE_USER`: PDCDAVID
- `SNOWFLAKE_DATABASE`: PRODUCT_DATA_CLOUD
- `SNOWFLAKE_SCHEMA`: PDC_PRODUCTS
- `SNOWFLAKE_WAREHOUSE`: COMPUTE_WH
- `SNOWFLAKE_ROLE`: ACCOUNTADMIN

**Secrets (Secret Manager):**
- `SNOWFLAKE_PRIVATE_KEY_CONTENT`: Base64-encoded JWT private key

## 📝 Development

**Local testing:**
```bash
cd ~/snowflake-mcp-remote
python -m fastmcp dev server.py
```

**Dependencies:**
- Python 3.12
- fastmcp >= 0.2.0
- snowflake-connector-python >= 3.7.0
- cryptography >= 41.0.0

---

**Maintained by:** David (Product Owner) + Claude (Lead Developer)  
**Last Updated:** 2025-11-02  
**Status:** 🟢 Production Ready
