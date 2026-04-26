import os
import zipfile
import httpx
import shutil
import tempfile
from typing import List, Dict, Optional
from app.utils.repo_scanner import RepoScanner
from app.services.plagiarism.orchestrator import PlagiarismOrchestrator
from app.schemas.final_report import FinalPlagiarismReport

class RepoIngestionService:
    """
    Handles downloading and extracting repositories from URLs for analysis.
    """

    def __init__(self):
        self.scanner = RepoScanner()
        self.orchestrator = PlagiarismOrchestrator()

    async def analyze_repo_url(self, repo_url: str) -> List[FinalPlagiarismReport]:
        """
        Main entry point for analyzing a remote repository.
        """
        # Convert GitHub URL to ZIP URL if necessary
        zip_url = self._get_zip_url(repo_url)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            zip_path = os.path.join(temp_dir, "repo.zip")
            extract_path = os.path.join(temp_dir, "extracted")
            
            # 1. Download
            print(f"Downloading from {zip_url}...")
            async with httpx.AsyncClient(follow_redirects=True, timeout=60.0) as client:
                response = await client.get(zip_url)
                if response.status_code != 200:
                    raise Exception(f"Failed to download repository: {response.status_code}")
                
                with open(zip_path, "wb") as f:
                    f.write(response.content)

            # 2. Extract
            print("Extracting archive...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)

            # 3. Handle GitHub's extra root folder in ZIPs
            inner_dirs = os.listdir(extract_path)
            if len(inner_dirs) == 1 and os.path.isdir(os.path.join(extract_path, inner_dirs[0])):
                working_path = os.path.join(extract_path, inner_dirs[0])
            else:
                working_path = extract_path

            # 4. Scan and Analyze
            submissions = self.scanner.scan_submissions_root(working_path)
            
            if not submissions:
                # If no sub-folders found, treat the entire root as one submission
                # This might happen if the repo itself IS the submission
                print("No sub-directories found. Treating root as single submission.")
                files = self.scanner.scan_directory(working_path)
                if files:
                    submissions = [{
                        "id": "single_repo",
                        "files": files,
                        "language": "python" # Default heuristic
                    }]

            if len(submissions) < 2:
                # Plagiarism needs at least 2 submissions to compare
                print("Not enough submissions found for pairwise comparison.")
                return []

            return await self.orchestrator.run_batch_analysis(submissions)

    def _get_zip_url(self, repo_url: str) -> str:
        """
        Converts a standard GitHub URL to a ZIP download URL.
        """
        url = repo_url.strip("/")
        if "github.com" in url and not url.endswith(".zip"):
            if "/tree/" in url:
                # Handle branch URLs: github.com/user/repo/tree/branch
                parts = url.split("/")
                repo_base = "/".join(parts[:5])
                branch = parts[6]
                return f"{repo_base}/archive/refs/heads/{branch}.zip"
            return f"{url}/archive/refs/heads/main.zip"
        return url
