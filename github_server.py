import asyncio
import logging
import os
from typing import Dict, Any, List, Optional
from fastmcp import FastMCP
import requests
import json
import base64

logger = logging.getLogger(__name__)
logging.basicConfig(format="[%(levelname)s]: %(message)s", level=logging.INFO)

mcp = FastMCP("GitHub PDC V1.0")

# Configuration
GITHUB_TOKEN = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")
GITHUB_API_BASE = "https://api.github.com"

def get_headers():
    """Get GitHub API headers with authentication"""
    if not GITHUB_TOKEN:
        raise ValueError("GITHUB_PERSONAL_ACCESS_TOKEN required")
    
    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }

@mcp.tool()
def create_pull_request(
    repo: str,
    title: str,
    head: str,
    base: str = "main",
    body: Optional[str] = None,
    draft: bool = False
) -> Dict[str, Any]:
    """
    Create a new pull request
    
    Args:
        repo: Repository in format 'owner/repo'
        title: PR title
        head: Branch name containing changes
        base: Base branch (default: 'main')
        body: PR description (optional)
        draft: Create as draft PR (default: False)
    
    Returns:
        Dict with PR details (number, url, state)
    """
    try:
        url = f"{GITHUB_API_BASE}/repos/{repo}/pulls"
        
        data = {
            "title": title,
            "head": head,
            "base": base,
            "draft": draft
        }
        
        if body:
            data["body"] = body
        
        response = requests.post(url, headers=get_headers(), json=data)
        response.raise_for_status()
        
        pr = response.json()
        
        return {
            "success": True,
            "pr_number": pr["number"],
            "pr_url": pr["html_url"],
            "state": pr["state"],
            "draft": pr["draft"],
            "message": f"Pull request #{pr['number']} created successfully"
        }
        
    except Exception as e:
        logger.error(f"Create PR failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@mcp.tool()
def create_branch(
    repo: str,
    branch_name: str,
    from_branch: str = "main"
) -> Dict[str, Any]:
    """
    Create a new branch from an existing branch
    
    Args:
        repo: Repository in format 'owner/repo'
        branch_name: Name for the new branch
        from_branch: Source branch (default: 'main')
    
    Returns:
        Dict with success status and branch details
    """
    try:
        # Get the SHA of the source branch
        ref_url = f"{GITHUB_API_BASE}/repos/{repo}/git/ref/heads/{from_branch}"
        ref_response = requests.get(ref_url, headers=get_headers())
        ref_response.raise_for_status()
        
        source_sha = ref_response.json()["object"]["sha"]
        
        # Create new branch
        create_url = f"{GITHUB_API_BASE}/repos/{repo}/git/refs"
        data = {
            "ref": f"refs/heads/{branch_name}",
            "sha": source_sha
        }
        
        response = requests.post(create_url, headers=get_headers(), json=data)
        response.raise_for_status()
        
        return {
            "success": True,
            "branch": branch_name,
            "from_branch": from_branch,
            "sha": source_sha,
            "message": f"Branch '{branch_name}' created from '{from_branch}'"
        }
        
    except Exception as e:
        logger.error(f"Create branch failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@mcp.tool()
def list_branches(
    repo: str,
    limit: int = 30
) -> Dict[str, Any]:
    """
    List branches in a repository
    
    Args:
        repo: Repository in format 'owner/repo'
        limit: Maximum number of branches to return (1-100)
    
    Returns:
        Dict with list of branches
    """
    try:
        url = f"{GITHUB_API_BASE}/repos/{repo}/branches"
        params = {"per_page": min(limit, 100)}
        
        response = requests.get(url, headers=get_headers(), params=params)
        response.raise_for_status()
        
        branches = response.json()
        
        branch_list = [
            {
                "name": b["name"],
                "protected": b["protected"],
                "commit_sha": b["commit"]["sha"]
            }
            for b in branches
        ]
        
        return {
            "success": True,
            "branches": branch_list,
            "count": len(branch_list)
        }
        
    except Exception as e:
        logger.error(f"List branches failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@mcp.tool()
def create_issue(
    repo: str,
    title: str,
    body: Optional[str] = None,
    labels: Optional[List[str]] = None,
    assignees: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Create a new issue
    
    Args:
        repo: Repository in format 'owner/repo'
        title: Issue title
        body: Issue description (optional)
        labels: List of label names (optional)
        assignees: List of usernames to assign (optional)
    
    Returns:
        Dict with issue details (number, url, state)
    """
    try:
        url = f"{GITHUB_API_BASE}/repos/{repo}/issues"
        
        data = {"title": title}
        
        if body:
            data["body"] = body
        if labels:
            data["labels"] = labels
        if assignees:
            data["assignees"] = assignees
        
        response = requests.post(url, headers=get_headers(), json=data)
        response.raise_for_status()
        
        issue = response.json()
        
        return {
            "success": True,
            "issue_number": issue["number"],
            "issue_url": issue["html_url"],
            "state": issue["state"],
            "message": f"Issue #{issue['number']} created successfully"
        }
        
    except Exception as e:
        logger.error(f"Create issue failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@mcp.tool()
def list_commits(
    repo: str,
    branch: str = "main",
    limit: int = 30
) -> Dict[str, Any]:
    """
    List commits in a branch
    
    Args:
        repo: Repository in format 'owner/repo'
        branch: Branch name (default: 'main')
        limit: Maximum number of commits (1-100)
    
    Returns:
        Dict with list of commits
    """
    try:
        url = f"{GITHUB_API_BASE}/repos/{repo}/commits"
        params = {
            "sha": branch,
            "per_page": min(limit, 100)
        }
        
        response = requests.get(url, headers=get_headers(), params=params)
        response.raise_for_status()
        
        commits = response.json()
        
        commit_list = [
            {
                "sha": c["sha"][:7],
                "message": c["commit"]["message"].split('\n')[0],
                "author": c["commit"]["author"]["name"],
                "date": c["commit"]["author"]["date"]
            }
            for c in commits
        ]
        
        return {
            "success": True,
            "commits": commit_list,
            "count": len(commit_list),
            "branch": branch
        }
        
    except Exception as e:
        logger.error(f"List commits failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@mcp.tool()
def search_code(
    repo: str,
    query: str,
    limit: int = 10
) -> Dict[str, Any]:
    """
    Search code in a repository
    
    Args:
        repo: Repository in format 'owner/repo'
        query: Search query
        limit: Maximum results (1-30)
    
    Returns:
        Dict with search results
    """
    try:
        # GitHub search API requires repo: prefix
        full_query = f"{query} repo:{repo}"
        
        url = f"{GITHUB_API_BASE}/search/code"
        params = {
            "q": full_query,
            "per_page": min(limit, 30)
        }
        
        response = requests.get(url, headers=get_headers(), params=params)
        response.raise_for_status()
        
        data = response.json()
        
        results = [
            {
                "path": item["path"],
                "url": item["html_url"],
                "repository": item["repository"]["full_name"]
            }
            for item in data.get("items", [])
        ]
        
        return {
            "success": True,
            "results": results,
            "total_count": data.get("total_count", 0),
            "query": query
        }
        
    except Exception as e:
        logger.error(f"Search code failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@mcp.tool()
def push_files(
    repo: str,
    branch: str,
    files: List[Dict[str, str]],
    commit_message: str
) -> Dict[str, Any]:
    """
    Push multiple files in a single commit (batch operation)
    
    Args:
        repo: Repository in format 'owner/repo'
        branch: Target branch
        files: List of dicts with 'path' and 'content' keys
        commit_message: Commit message
    
    Returns:
        Dict with commit details
    
    Example:
        push_files(
            repo="owner/repo",
            branch="main",
            files=[
                {"path": "file1.py", "content": "print('hello')"},
                {"path": "file2.py", "content": "print('world')"},
                {"path": "docs/README.md", "content": "# Docs"}
            ],
            commit_message="Add multiple files"
        )
    """
    try:
        # Get reference for the branch
        ref_url = f"{GITHUB_API_BASE}/repos/{repo}/git/ref/heads/{branch}"
        ref_response = requests.get(ref_url, headers=get_headers())
        ref_response.raise_for_status()
        
        base_sha = ref_response.json()["object"]["sha"]
        
        # Get base tree
        commit_url = f"{GITHUB_API_BASE}/repos/{repo}/git/commits/{base_sha}"
        commit_response = requests.get(commit_url, headers=get_headers())
        commit_response.raise_for_status()
        
        base_tree_sha = commit_response.json()["tree"]["sha"]
        
        # Create blobs for each file
        tree_items = []
        for file_info in files:
            # Create blob
            blob_url = f"{GITHUB_API_BASE}/repos/{repo}/git/blobs"
            blob_data = {
                "content": file_info["content"],
                "encoding": "utf-8"
            }
            
            blob_response = requests.post(blob_url, headers=get_headers(), json=blob_data)
            blob_response.raise_for_status()
            
            blob_sha = blob_response.json()["sha"]
            
            tree_items.append({
                "path": file_info["path"],
                "mode": "100644",
                "type": "blob",
                "sha": blob_sha
            })
        
        # Create tree
        tree_url = f"{GITHUB_API_BASE}/repos/{repo}/git/trees"
        tree_data = {
            "base_tree": base_tree_sha,
            "tree": tree_items
        }
        
        tree_response = requests.post(tree_url, headers=get_headers(), json=tree_data)
        tree_response.raise_for_status()
        
        new_tree_sha = tree_response.json()["sha"]
        
        # Create commit
        commit_create_url = f"{GITHUB_API_BASE}/repos/{repo}/git/commits"
        commit_data = {
            "message": commit_message,
            "tree": new_tree_sha,
            "parents": [base_sha]
        }
        
        commit_create_response = requests.post(commit_create_url, headers=get_headers(), json=commit_data)
        commit_create_response.raise_for_status()
        
        new_commit_sha = commit_create_response.json()["sha"]
        
        # Update reference
        ref_update_url = f"{GITHUB_API_BASE}/repos/{repo}/git/refs/heads/{branch}"
        ref_data = {"sha": new_commit_sha}
        
        ref_update_response = requests.patch(ref_update_url, headers=get_headers(), json=ref_data)
        ref_update_response.raise_for_status()
        
        return {
            "success": True,
            "commit_sha": new_commit_sha[:7],
            "files_pushed": len(files),
            "branch": branch,
            "message": f"Pushed {len(files)} files in 1 commit"
        }
        
    except Exception as e:
        logger.error(f"Push files failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@mcp.tool()
def connection_status() -> Dict[str, Any]:
    """
    Check GitHub API connection status
    
    Returns connection info and available features
    """
    try:
        url = f"{GITHUB_API_BASE}/user"
        response = requests.get(url, headers=get_headers())
        response.raise_for_status()
        
        user = response.json()
        
        return {
            "success": True,
            "connected": True,
            "user": user["login"],
            "name": user.get("name"),
            "version": "V1.0",
            "capabilities": [
                "Pull Requests: create",
                "Branches: create, list",
                "Issues: create",
                "Commits: list",
                "Code: search",
                "Files: push (batch)"
            ]
        }
        
    except Exception as e:
        logger.error(f"Connection check failed: {e}")
        return {
            "success": False,
            "connected": False,
            "error": str(e),
            "version": "V1.0"
        }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8081))
    logger.info(f"🚀 GitHub MCP V1.0 starting on port {port}")
    logger.info("✅ Pull Requests: create")
    logger.info("✅ Branches: create, list")
    logger.info("✅ Issues: create")
    logger.info("✅ Commits: list")
    logger.info("✅ Code: search")
    logger.info("✅ Files: push (batch)")
    
    asyncio.run(
        mcp.run_async(
            transport="streamable-http",
            host="0.0.0.0",
            port=port,
        )
    )
