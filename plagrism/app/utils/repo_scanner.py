import os
from typing import Dict, List, Optional

class RepoScanner:
    """
    Utility to scan directories and extract source code files for analysis.
    """

    def __init__(self, allowed_extensions: List[str] = [".py", ".js", ".ts", ".java", ".cpp"]):
        self.allowed_extensions = [ext.lower() for ext in allowed_extensions]

    def scan_directory(self, root_path: str) -> Dict[str, str]:
        """
        Scans a single directory and returns a map of {relative_path: content}.
        """
        files_content = {}
        for root, _, files in os.walk(root_path):
            for file in files:
                _, ext = os.path.splitext(file)
                if ext.lower() in self.allowed_extensions:
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, root_path)
                    try:
                        with open(full_path, "r", encoding="utf-8") as f:
                            files_content[rel_path] = f.read()
                    except Exception as e:
                        print(f"Error reading {full_path}: {e}")
        return files_content

    def scan_submissions_root(self, submissions_root: str) -> List[Dict[str, any]]:
        """
        Scans a directory where each sub-directory is a separate submission.
        Returns a list of submissions ready for the shortlisting service.
        """
        submissions = []
        for item in os.listdir(submissions_root):
            sub_path = os.path.join(submissions_root, item)
            if os.path.isdir(sub_path):
                print(f"Scanning submission: {item}...")
                files = self.scan_directory(sub_path)
                if files:
                    # Determine language from the first file found (heuristic)
                    first_file = list(files.keys())[0]
                    _, ext = os.path.splitext(first_file)
                    
                    submissions.append({
                        "id": item, # Directory name as ID
                        "files": files,
                        "language": self._get_language_name(ext)
                    })
        return submissions

    def _get_language_name(self, ext: str) -> str:
        mapping = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".java": "java",
            ".cpp": "cpp"
        }
        return mapping.get(ext.lower(), "unknown")
