# Snowflake MCP V2.1 - Quick Reference

**Service URL:** `https://snowflake-mcp-409811184795.europe-west1.run.app`

**Version:** V2.1 (Write-Enabled)  
**Status:** 🟢 Production Ready  
**Last Deploy:** 2025-11-02

---

## 🔗 Add to claude.ai

1. Open https://claude.ai
2. Settings → Connectors → Add Custom Connector
3. **Name:** Snowflake PDC V2.1
4. **URL:** `https://snowflake-mcp-409811184795.europe-west1.run.app`
5. Save

✅ Works on Desktop, Mobile, Tablet!

---

## ✨ Features V2.1

### Write Operations (NEW!)
```sql
-- INSERT
INSERT INTO TASK_QUEUE (PRODUCT_ID, STATUS) VALUES ('123', 'pending')

-- UPDATE (requires WHERE)
UPDATE TASK_QUEUE SET STATUS = 'completed' WHERE PRODUCT_ID = '123'

-- DELETE (requires WHERE)
DELETE FROM TASK_QUEUE WHERE STATUS = 'completed' AND CREATED_AT < '2024-01-01'
```

### Read Operations
```sql
-- SELECT (auto-LIMIT 20)
SELECT * FROM PRODUCT

-- SHOW/DESCRIBE
SHOW TABLES
DESCRIBE TABLE PRODUCT
```

### DDL Operations
```sql
-- CREATE
CREATE VIEW active_products AS SELECT * FROM PRODUCT WHERE IS_ACTIVE = TRUE

-- ALTER
ALTER TABLE PRODUCT ADD COLUMN new_field VARCHAR(255)
```

---

## 🔒 Security

**Allowed:**
- ✅ SELECT, SHOW, DESCRIBE
- ✅ INSERT
- ✅ UPDATE (with WHERE)
- ✅ DELETE (with WHERE)
- ✅ CREATE, ALTER

**Blocked:**
- ❌ DROP
- ❌ TRUNCATE
- ❌ UPDATE without WHERE
- ❌ DELETE without WHERE

---

## 📊 Connection Info

```json
{
  "user": "PDCDAVID",
  "role": "ACCOUNTADMIN",
  "database": "PRODUCT_DATA_CLOUD",
  "schema": "PDC_PRODUCTS",
  "auth": "JWT",
  "version": "V2.1"
}
```

---

## 🧪 Tested Operations

| Operation | Status | Test Date |
|-----------|--------|-----------|
| INSERT | ✅ Working | 2025-11-02 |
| UPDATE (WHERE) | ✅ Working | 2025-11-02 |
| DELETE (WHERE) | ✅ Working | 2025-11-02 |
| DELETE (no WHERE) | 🔒 Blocked | 2025-11-02 |
| SELECT | ✅ Working | 2025-11-02 |
| DESCRIBE | ✅ Working | 2025-11-02 |

---

**Need help?** See [README.md](README.md) for full documentation.
