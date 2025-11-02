# Changelog - Snowflake MCP Server

All notable changes to this project will be documented in this file.

## [V2.1] - 2025-11-02

### 🎉 Added - Write Operations Enabled!

**New Capabilities:**
- ✅ INSERT operations
- ✅ UPDATE operations (requires WHERE clause)
- ✅ DELETE operations (requires WHERE clause)

**Security Enhancements:**
- 🔒 UPDATE/DELETE without WHERE clause → Blocked
- 🔒 DROP/TRUNCATE operations → Blocked
- ✅ Safe write operations for development

**URL Changed:**
- Old: `https://snowflake-mcp-va6ytiztka-ew.a.run.app`
- New: `https://snowflake-mcp-409811184795.europe-west1.run.app`

### ✅ Tested
- INSERT into TASK_QUEUE: ✅ 1 row inserted
- UPDATE with WHERE: ✅ 1 row updated  
- DELETE with WHERE: ✅ 1 row deleted
- DELETE without WHERE: 🔒 Blocked as expected

### 📝 Documentation
- Added comprehensive README.md
- Added QUICKREF.md for fast reference
- Fixed cloudbuild.yaml Secret Manager reference

---

## [V2.0] - 2025-10-29

### Initial Remote MCP Release

**Features:**
- ✅ Remote MCP server on Cloud Run
- ✅ JWT authentication via Secret Manager
- ✅ Read operations (SELECT, SHOW, DESCRIBE)
- ✅ DDL operations (CREATE, ALTER)
- ✅ Token optimization (auto-LIMIT, column truncation)
- 🔒 Write operations blocked for safety

**Infrastructure:**
- Cloud Run deployment
- GitHub repository: Product-Data-Cloud/snowflake-mcp-remote
- Manual deployment via gcloud CLI

---

## [V1.0] - 2025-10-24

### Local MCP Prototype

**Features:**
- ✅ Local MCP server
- ✅ Basic Snowflake queries
- ⚠️ Required Claude Desktop App
- ⚠️ No mobile support

**Deprecated:** Local-only approach replaced by Remote MCP V2.0

---

**Maintained by:** David (Product Owner) + Claude (Lead Developer)  
**Repository:** https://github.com/Product-Data-Cloud/snowflake-mcp-remote
