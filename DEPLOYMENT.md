# 🚀 DEPLOYMENT GUIDE - Both MCPs

Complete guide to deploy both Snowflake MCP V2.2 and GitHub MCP V1.0.

## 📋 PREREQUISITES

### 1. Snowflake MCP (Already Done ✅)
- Secret `snowflake-private-key` exists in Secret Manager
- Working JWT authentication

### 2. GitHub MCP (NEW!)
- Need GitHub Personal Access Token (PAT)

**Create GitHub PAT:**
```
1. Go to: https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Name: "PDC MCP Server"
4. Scopes: Check "repo" (full control)
5. Click "Generate token"
6. COPY TOKEN (you won't see it again!)
```

**Store in Secret Manager:**
```bash
# In Cloud Shell
echo -n "YOUR_GITHUB_TOKEN_HERE" | gcloud secrets create github-pat \
  --data-file=- \
  --project=productdatacloud
```

---

## 🎯 DEPLOYMENT STEPS

### Option A: Deploy Both NOW (Manual)

```bash
# In Cloud Shell
cd ~/snowflake-mcp-remote
git pull

# Set project
gcloud config set project productdatacloud

# 1. Deploy Snowflake MCP V2.2
echo "🔵 Deploying Snowflake MCP V2.2..."
gcloud run deploy snowflake-mcp \
  --source . \
  --region=europe-west1 \
  --platform=managed \
  --allow-unauthenticated \
  --update-secrets=SNOWFLAKE_PRIVATE_KEY_CONTENT=snowflake-private-key:latest

# 2. Deploy GitHub MCP V1.0
echo "🟢 Deploying GitHub MCP V1.0..."
gcloud builds submit \
  --config=cloudbuild-github.yaml \
  --project=productdatacloud

echo "✅ Both MCPs deployed!"
```

### Option B: Auto-Deploy (Cloud Build Triggers)

**Setup once, then auto-deploy on git push:**

#### 1. Snowflake MCP Trigger
```
Name: snowflake-mcp-auto-deploy
Repository: Product-Data-Cloud/snowflake-mcp-remote
Event: Push to branch
Branch: ^main$
Configuration type: Cloud Build configuration file
Location: cloudbuild.yaml
```

#### 2. GitHub MCP Trigger
```
Name: github-mcp-auto-deploy
Repository: Product-Data-Cloud/snowflake-mcp-remote
Event: Push to branch
Branch: ^main$
Configuration type: Cloud Build configuration file
Location: cloudbuild-github.yaml
```

**Then:** Push to main → Both auto-deploy!

---

## 🔗 SERVICE URLS (After Deploy)

**Snowflake MCP V2.2:**
```
https://snowflake-mcp-409811184795.europe-west1.run.app
```

**GitHub MCP V1.0:**
```
https://github-mcp-409811184795.europe-west1.run.app
```

---

## 📱 ADD TO CLAUDE.AI

**In claude.ai → Settings → Connectors:**

### 1. Snowflake PDC V2.2
```
Name: Snowflake PDC V2.2
URL: https://snowflake-mcp-409811184795.europe-west1.run.app
```

### 2. GitHub PDC V1.0
```
Name: GitHub PDC V1.0
URL: https://github-mcp-409811184795.europe-west1.run.app
```

**Save both!** ✅

---

## ✅ VERIFY DEPLOYMENT

Test beide MCPs:

```
# In claude.ai chat:

1. Test Snowflake MCP V2.2:
   "Check Snowflake connection status"
   
2. Test GitHub MCP V1.0:
   "Check GitHub connection status"
   
3. Test new features:
   "Show me what new features Snowflake MCP V2.2 has"
   "What can GitHub MCP do?"
```

---

## 🎉 NEW FEATURES AVAILABLE

### Snowflake MCP V2.2
- ✅ **MERGE** (UPSERT) - Sync PRODUCT_RAW → PRODUCT
- ✅ **Transactions** - BEGIN/COMMIT/ROLLBACK
- ✅ **Batch INSERT** - 1000 rows in 1 call
- ✅ **Dynamic LIMIT** - 1-1000 rows

### GitHub MCP V1.0
- ✅ **Pull Requests** - Create PRs
- ✅ **Branches** - Create/list branches
- ✅ **Issues** - Create issues
- ✅ **Commits** - List commit history
- ✅ **Search** - Search code
- ✅ **Batch Push** - Multiple files in 1 commit

---

## 🔧 TROUBLESHOOTING

### Snowflake MCP Deploy Fails
```bash
# Check logs
gcloud run services logs read snowflake-mcp \
  --region=europe-west1 \
  --project=productdatacloud \
  --limit=50
```

### GitHub MCP Deploy Fails
```bash
# Check build logs
gcloud builds list --limit=5

# Check service logs
gcloud run services logs read github-mcp \
  --region=europe-west1 \
  --project=productdatacloud \
  --limit=50
```

### GitHub PAT Issues
```bash
# Verify secret exists
gcloud secrets describe github-pat

# Update if needed
echo -n "NEW_TOKEN" | gcloud secrets versions add github-pat \
  --data-file=-
```

---

## 📊 COST

**Both services:**
- Free tier: 2 million requests/month
- Your usage: ~1000 requests/month
- **Cost: 0€/month** ✅

---

## 📝 MAINTENANCE

**Update MCPs:**
```bash
# Make changes to code
# Commit to GitHub
git push

# If auto-deploy enabled: Done! (3-5 min)
# If manual: Run deploy commands above
```

---

**Questions? Check individual READMEs:**
- Snowflake: [README.md](README.md)
- GitHub: [README-GITHUB.md](README-GITHUB.md)

**Last Updated:** 2025-11-02  
**Status:** 🟢 Production Ready
