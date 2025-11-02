# GitHub Remote MCP Server V1.0

Remote MCP server for GitHub API with advanced development features.

## 🚀 Features

**V1.0 - Full-Featured:**
- ✅ **Pull Requests:** Create PRs with draft support
- ✅ **Branch Management:** Create and list branches
- ✅ **Issue Management:** Create issues with labels and assignees
- ✅ **Commit History:** List commits for any branch
- ✅ **Code Search:** Search code across repository
- ✅ **Batch File Push:** Push multiple files in single commit

## 📡 Deployment

### Prerequisites

1. **GitHub Personal Access Token (PAT)**
   - Go to GitHub → Settings → Developer settings → Personal access tokens
   - Generate new token (classic)
   - Required scopes: `repo` (full control of private repositories)
   - Copy the token

2. **Store in Secret Manager**
   ```bash
   # In Cloud Shell
   echo -n "YOUR_GITHUB_TOKEN" | gcloud secrets create github-pat \
     --data-file=- \
     --project=productdatacloud
   ```

### Deploy

```bash
# In Cloud Shell
cd ~/snowflake-mcp-remote
git pull

# Set project
gcloud config set project productdatacloud

# Deploy GitHub MCP
gcloud builds submit \
  --config=cloudbuild-github.yaml \
  --project=productdatacloud
```

**OR use Cloud Build Trigger:**
```
Name: github-mcp-auto-deploy
Event: Push to branch
Branch: ^main$
Configuration: cloudbuild-github.yaml
```

## 🔗 Usage

**Service URL:** `https://github-mcp-409811184795.europe-west1.run.app`

**Add to claude.ai:**
1. Settings → Connectors → Add Custom Connector
2. Name: GitHub PDC V1.0
3. URL: (service URL above)
4. Save

## 🛠️ Tools

### `create_pull_request`

Create a pull request from branch.

```python
create_pull_request(
    repo="Product-Data-Cloud/pdc-monorepo",
    title="Add new feature X",
    head="feature-x",
    base="main",
    body="This PR adds feature X with tests",
    draft=False
)
```

### `create_branch`

Create a new branch from existing branch.

```python
create_branch(
    repo="Product-Data-Cloud/pdc-monorepo",
    branch_name="feature-new-api",
    from_branch="main"
)
```

### `list_branches`

List all branches in repository.

```python
list_branches(
    repo="Product-Data-Cloud/pdc-monorepo",
    limit=30
)
```

### `create_issue`

Create a new issue with labels.

```python
create_issue(
    repo="Product-Data-Cloud/pdc-monorepo",
    title="Bug: API returns 500",
    body="Description of the bug...",
    labels=["bug", "high-priority"],
    assignees=["username"]
)
```

### `list_commits`

List commits for a branch.

```python
list_commits(
    repo="Product-Data-Cloud/pdc-monorepo",
    branch="main",
    limit=30
)
```

### `search_code`

Search code in repository.

```python
search_code(
    repo="Product-Data-Cloud/pdc-monorepo",
    query="def process_product",
    limit=10
)
```

### `push_files` (Batch Operation!)

Push multiple files in one commit - very efficient!

```python
push_files(
    repo="Product-Data-Cloud/pdc-monorepo",
    branch="main",
    files=[
        {
            "path": "src/feature.py",
            "content": "def new_feature():\n    pass"
        },
        {
            "path": "tests/test_feature.py",
            "content": "def test_new_feature():\n    assert True"
        },
        {
            "path": "docs/feature.md",
            "content": "# New Feature\n\nDocumentation..."
        }
    ],
    commit_message="Add new feature with tests and docs"
)
```

**Benefits:**
- 1 commit instead of 3
- Atomic operation (all files or none)
- Cleaner git history

## 🎯 Use Cases

### Development Workflow
```python
# 1. Create feature branch
create_branch(
    repo="owner/repo",
    branch_name="feature-user-auth",
    from_branch="main"
)

# 2. Push code + tests + docs in one commit
push_files(
    repo="owner/repo",
    branch="feature-user-auth",
    files=[
        {"path": "src/auth.py", "content": "..."},
        {"path": "tests/test_auth.py", "content": "..."},
        {"path": "docs/auth.md", "content": "..."}
    ],
    commit_message="Implement user authentication"
)

# 3. Create PR
create_pull_request(
    repo="owner/repo",
    title="Add user authentication",
    head="feature-user-auth",
    base="main",
    body="Implements JWT-based user authentication"
)
```

### Bug Tracking
```python
# Create issue from error analysis
create_issue(
    repo="owner/repo",
    title="Performance: Slow query in product search",
    body="Query takes 5+ seconds with 1000+ products",
    labels=["performance", "database"],
    assignees=["david"]
)
```

### Code Review
```python
# Search for specific patterns
search_code(
    repo="owner/repo",
    query="TODO",
    limit=20
)
```

## 🔐 Environment & Secrets

**Secrets (Secret Manager):**
- `GITHUB_PERSONAL_ACCESS_TOKEN`: GitHub PAT with repo scope

## 📝 Development

**Local testing:**
```bash
cd ~/snowflake-mcp-remote
export GITHUB_PERSONAL_ACCESS_TOKEN="your_token"
python github_server.py
```

**Dependencies:**
- Python 3.12
- fastmcp >= 0.2.0
- requests >= 2.31.0

---

**Maintained by:** David (Product Owner) + Claude (Lead Developer)  
**Last Updated:** 2025-11-02  
**Status:** 🟢 Ready for Deploy
