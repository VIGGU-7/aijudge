"""
Fetches GitHub repository contents for codebase analysis.
"""
import os
import httpx
import re
from typing import Optional


GITHUB_API = "https://api.github.com"
CODE_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".cpp", ".c", ".go",
    ".rs", ".rb", ".php", ".swift", ".kt", ".html", ".css", ".scss",
    ".vue", ".svelte", ".dart", ".r", ".sql",
}
CONFIG_FILES = {
    "package.json", "requirements.txt", "Pipfile", "Cargo.toml",
    "go.mod", "pom.xml", "build.gradle", "Dockerfile", "docker-compose.yml",
    "Makefile", ".env.example", "tsconfig.json", "vite.config.js",
    "vite.config.ts", "next.config.js", "tailwind.config.js",
}


def _parse_repo_url(url: str):
    """Extract owner and repo name from a GitHub URL."""
    patterns = [
        r"github\.com/([^/]+)/([^/\s?.#]+)",
        r"^([^/]+)/([^/\s]+)$",
    ]
    for p in patterns:
        m = re.search(p, url.strip().rstrip("/").rstrip(".git"))
        if m:
            return m.group(1), m.group(2)
    return None, None


async def fetch_repo(repo_url: str, github_token: Optional[str] = None) -> dict:
    """
    Fetch repository contents from GitHub.
    Returns file tree, key files, README, and detected tech stack.
    """
    owner, repo = _parse_repo_url(repo_url)
    if not owner or not repo:
        return {"error": f"Could not parse GitHub URL: {repo_url}"}

    token = github_token or os.environ.get("GITHUB_TOKEN", "")
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"

    result = {
        "owner": owner,
        "repo": repo,
        "file_tree": "",
        "key_files": [],
        "readme": "",
        "tech_stack": [],
        "total_files": 0,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Get repository tree (recursive)
        try:
            tree_resp = await client.get(
                f"{GITHUB_API}/repos/{owner}/{repo}/git/trees/main?recursive=1",
                headers=headers,
            )
            if tree_resp.status_code == 404:
                tree_resp = await client.get(
                    f"{GITHUB_API}/repos/{owner}/{repo}/git/trees/master?recursive=1",
                    headers=headers,
                )
            if tree_resp.status_code != 200:
                return {"error": f"GitHub API error: {tree_resp.status_code} — {tree_resp.text[:200]}"}

            tree_data = tree_resp.json()
            items = tree_data.get("tree", [])

            # Build file tree string
            tree_lines = []
            for item in items:
                if item["type"] == "blob":
                    tree_lines.append(item["path"])
            result["file_tree"] = "\n".join(tree_lines[:500])
            result["total_files"] = len(tree_lines)

        except httpx.RequestError as e:
            return {"error": f"Network error: {e}"}

        # 2. Detect tech stack from file presence
        tech_stack = set()
        filenames_lower = {item["path"].split("/")[-1].lower() for item in items if item["type"] == "blob"}
        all_extensions = {os.path.splitext(item["path"])[1].lower() for item in items if item["type"] == "blob"}

        if "package.json" in filenames_lower:
            tech_stack.add("Node.js")
        if ".jsx" in all_extensions or ".tsx" in all_extensions:
            tech_stack.add("React")
        if "next.config.js" in filenames_lower or "next.config.ts" in filenames_lower:
            tech_stack.add("Next.js")
        if "requirements.txt" in filenames_lower or "setup.py" in filenames_lower:
            tech_stack.add("Python")
        if ".py" in all_extensions:
            tech_stack.add("Python")
        if "Cargo.toml" in filenames_lower:
            tech_stack.add("Rust")
        if "go.mod" in filenames_lower:
            tech_stack.add("Go")
        if "Dockerfile" in filenames_lower:
            tech_stack.add("Docker")
        if ".vue" in all_extensions:
            tech_stack.add("Vue.js")
        if "tailwind.config.js" in filenames_lower:
            tech_stack.add("TailwindCSS")
        if ".ts" in all_extensions:
            tech_stack.add("TypeScript")
        result["tech_stack"] = list(tech_stack)

        # 3. Fetch README
        for readme_name in ["README.md", "readme.md", "README.rst", "README"]:
            try:
                r = await client.get(
                    f"{GITHUB_API}/repos/{owner}/{repo}/contents/{readme_name}",
                    headers={**headers, "Accept": "application/vnd.github.v3.raw"},
                )
                if r.status_code == 200:
                    result["readme"] = r.text[:5000]
                    break
            except httpx.RequestError:
                continue

        # 4. Fetch key source files (up to 15)
        key_paths = []
        for item in items:
            if item["type"] != "blob":
                continue
            name = item["path"].split("/")[-1]
            ext = os.path.splitext(name)[1].lower()

            # Prioritise config files and source files
            if name.lower() in CONFIG_FILES:
                key_paths.append(item["path"])
            elif ext in CODE_EXTENSIONS and item.get("size", 0) < 50000:
                key_paths.append(item["path"])

            if len(key_paths) >= 20:
                break

        # Fetch file contents
        for path in key_paths[:15]:
            try:
                r = await client.get(
                    f"{GITHUB_API}/repos/{owner}/{repo}/contents/{path}",
                    headers={**headers, "Accept": "application/vnd.github.v3.raw"},
                )
                if r.status_code == 200:
                    result["key_files"].append({
                        "path": path,
                        "content": r.text[:5000],
                        "language": os.path.splitext(path)[1].lstrip("."),
                    })
            except httpx.RequestError:
                continue

    return result
