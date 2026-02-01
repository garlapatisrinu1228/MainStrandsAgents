"""
GitHub Access Module for Strands Agent
This module provides functions to interact with GitHub repositories
"""


import os
from dotenv import load_dotenv
load_dotenv(dotenv_path='.env')
import requests
from typing import Dict, List, Any


class GitHubAccess:
    """Handle GitHub API interactions"""
    
    def __init__(self, token: str = None, username: str = None):
        """
        Initialize GitHub access
        
        Args:
            token: GitHub personal access token
            username: GitHub username
        """
        self.token = token or os.getenv('GITHUB_TOKEN')
        self.username = username or os.getenv('GITHUB_USERNAME')
        self.base_url = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github.v3+json"
        }
        if self.token:
            self.headers["Authorization"] = f"token {self.token}"
    
    def get_user_repos(self) -> List[Dict[str, Any]]:
        """Get all repositories for the authenticated user or specified username"""
        try:
            if self.username:
                url = f"{self.base_url}/users/{self.username}/repos"
            else:
                url = f"{self.base_url}/user/repos"

            repos = []
            page = 1
            while True:
                response = requests.get(
                    url,
                    headers=self.headers,
                    params={"per_page": 100, "page": page}
                )
                try:
                    response.raise_for_status()
                except Exception as e:
                    print(f"GitHub API Error: {e}\nURL: {response.url}\nResponse: {response.text}")
                    return {"error": f"{e} (URL: {response.url})", "details": response.text}

                page_repos = response.json()
                if not page_repos:
                    break

                repos.extend(page_repos)
                page += 1

            return repos
        except Exception as e:
            print(f"GitHub API Exception: {e}")
            return {"error": str(e)}
    
    def get_repo_contents(self, repo_name: str, path: str = "") -> List[Dict[str, Any]]:
        """
        Get contents of a repository at a specific path
        
        Args:
            repo_name: Name of the repository (e.g., 'username/repo')
            path: Path within the repository (default: root)
        """
        try:
            url = f"{self.base_url}/repos/{repo_name}/contents/{path}"
            response = requests.get(url, headers=self.headers)
            try:
                response.raise_for_status()
            except Exception as e:
                print(f"GitHub API Error: {e}\nURL: {response.url}\nResponse: {response.text}")
                return {"error": f"{e} (URL: {response.url})", "details": response.text}
            return response.json()
        except Exception as e:
            print(f"GitHub API Exception: {e}")
            return {"error": str(e)}
    
    def get_file_content(self, repo_name: str, file_path: str) -> str:
        """
        Get the content of a specific file
        
        Args:
            repo_name: Name of the repository
            file_path: Path to the file in the repository
        """
        try:
            url = f"{self.base_url}/repos/{repo_name}/contents/{file_path}"
            response = requests.get(url, headers=self.headers)
            try:
                response.raise_for_status()
            except Exception as e:
                print(f"GitHub API Error: {e}\nURL: {response.url}\nResponse: {response.text}")
                return f"Error: {e} (URL: {response.url})\nResponse: {response.text}"

            data = response.json()
            if data.get('encoding') == 'base64':
                import base64
                content = base64.b64decode(data['content']).decode('utf-8')
                return content
            return data.get('content', '')
        except Exception as e:
            print(f"GitHub API Exception: {e}")
            return f"Error: {str(e)}"
    
    def analyze_repository(self, repo_name: str) -> Dict[str, Any]:
        """
        Analyze a repository and return comprehensive information
        
        Args:
            repo_name: Name of the repository
        """
        try:
            # Get repository info
            repo_url = f"{self.base_url}/repos/{repo_name}"
            repo_response = requests.get(repo_url, headers=self.headers)
            try:
                repo_response.raise_for_status()
            except Exception as e:
                print(f"GitHub API Error: {e}\nURL: {repo_response.url}\nResponse: {repo_response.text}")
                return {"error": f"{e} (URL: {repo_response.url})", "details": repo_response.text}
            repo_info = repo_response.json()

            # Get all files recursively
            all_files = self._get_all_files(repo_name)

            # Analyze file types
            file_types = {}
            for file in all_files:
                ext = file.split('.')[-1] if '.' in file else 'no_extension'
                file_types[ext] = file_types.get(ext, 0) + 1
            return {
                "repo_name": repo_info.get('name'),
                "description": repo_info.get('description'),
                "language": repo_info.get('language'),
                "total_files": len(all_files),
                "file_types": file_types,
                "files": all_files,
                "stars": repo_info.get('stargazers_count'),
                "forks": repo_info.get('forks_count'),
                "size": repo_info.get('size'),
                "updated_at": repo_info.get('updated_at')
            }
        except Exception as e:
            print(f"GitHub API Exception: {e}")
            return {"error": str(e)}
    
    def _get_all_files(self, repo_name: str, path: str = "") -> List[str]:
        """Recursively get all files in a repository"""
        files = []
        try:
            contents = self.get_repo_contents(repo_name, path)

            if isinstance(contents, dict) and "error" in contents:
                return files

            for item in contents:
                if item['type'] == 'file':
                    files.append(item['path'])
                elif item['type'] == 'dir':
                    files.extend(self._get_all_files(repo_name, item['path']))
        except Exception:
            pass

        return files


def get_github_repos_info(username: str = None) -> str:
    """
    Get information about all GitHub repositories
    
    Args:
        username: GitHub username (optional, uses env var if not provided)
    """
    token = os.getenv('GITHUB_TOKEN')
    github = GitHubAccess(token=token, username=username)
    repos = github.get_user_repos()

    if isinstance(repos, dict) and "error" in repos:
        return f"Error accessing GitHub: {repos['error']}"
    if not repos:
        return "No repositories found."
    result = "Here are your GitHub repositories:\n\n"
    for idx, repo in enumerate(repos, 1):
        result += f"{idx}. **{repo['name']}**\n"
        if repo.get('language'):
            result += f"   - Language: {repo.get('language')}\n"
        if repo.get('description') and repo.get('description') != 'No description':
            result += f"   - Description: {repo.get('description')}\n"
        result += f"   - Stars: {repo.get('stargazers_count', 0)}\n"
        result += f"   - Private: {'Yes' if repo.get('private') else 'No'}\n\n"
    result += "If you need more details on any specific repository or assistance with something else, feel free to ask!"
    return result


def analyze_github_repo(repo_name: str, username: str = None) -> str:
    """
    Analyze a specific GitHub repository
    
    Args:
        repo_name: Name of the repository to analyze
        username: GitHub username (optional)
    """
    token = os.getenv('GITHUB_TOKEN')
    github = GitHubAccess(token=token, username=username)
    
    # If repo_name doesn't include username, add it
    if '/' not in repo_name and username:
        repo_name = f"{username}/{repo_name}"
    elif '/' not in repo_name and github.username:
        repo_name = f"{github.username}/{repo_name}"
    
    analysis = github.analyze_repository(repo_name)
    
    if "error" in analysis:
        return f"Error analyzing repository: {analysis['error']}"
    
    result = f"Repository Analysis: {analysis['repo_name']}\n"
    result += f"{'=' * 50}\n\n"
    result += f"Description: {analysis.get('description', 'No description')}\n"
    result += f"Primary Language: {analysis.get('language', 'Not specified')}\n"
    result += f"Total Files: {analysis['total_files']}\n"
    result += f"Stars: {analysis.get('stars', 0)}\n"
    result += f"Forks: {analysis.get('forks', 0)}\n"
    result += f"Last Updated: {analysis.get('updated_at', 'Unknown')}\n\n"
    
    result += "File Types Distribution:\n"
    for file_type, count in sorted(analysis['file_types'].items(), key=lambda x: x[1], reverse=True):
        result += f"  - .{file_type}: {count} files\n"
    
    result += f"\nAll Files ({analysis['total_files']}):\n"
    for file in analysis['files'][:50]:  # Show first 50 files
        result += f"  - {file}\n"
    
    if len(analysis['files']) > 50:
        result += f"\n  ... and {len(analysis['files']) - 50} more files\n"
    
    return result


def get_github_file_content(repo_name: str, file_path: str, username: str = None) -> str:
    """
    Get the content of a specific file in a GitHub repository
    
    Args:
        repo_name: Name of the repository
        file_path: Path to the file in the repository
        username: GitHub username (optional)
    """
    token = os.getenv('GITHUB_TOKEN')
    github = GitHubAccess(token=token, username=username)
    
    # If repo_name doesn't include username, add it
    if '/' not in repo_name and username:
        repo_name = f"{username}/{repo_name}"
    elif '/' not in repo_name and github.username:
        repo_name = f"{github.username}/{repo_name}"
    
    content = github.get_file_content(repo_name, file_path)
    
    if content.startswith("Error:"):
        return content
    
    return f"Content of {file_path} in {repo_name}:\n\n{content}"
