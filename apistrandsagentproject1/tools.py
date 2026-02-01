"""
Tool functions for Strands Agent
All functions decorated with @tool
"""
import os
import json
from strands.tools.decorator import tool
from githubaccess import get_github_repos_info, analyze_github_repo as github_analyze, get_github_file_content as github_file_content
from s3_storage import S3Storage
from session_manager import SessionManager

# Initialize S3 storage for session tools
db = S3Storage()

AVAILABLE_FILES = {}

@tool
def export_session_data(session_id: str) -> str:
    """Export all data for a session as JSON string."""
    session_manager = SessionManager(db)
    session = session_manager.get_session(session_id)
    if not session:
        return f"Session {session_id} not found"
    return json.dumps(session, indent=2)

@tool
def get_s3_storage_info() -> str:
    """Get S3 storage configuration and status."""
    info = {
        "storage_type": "Amazon S3",
        "bucket": os.getenv('S3_BUCKET_NAME'),
        "region": os.getenv('AWS_REGION'),
        "status": "connected"
    }
    return json.dumps(info, indent=2)

@tool
def read_local_file(file_path: str) -> str:
    """Read content from a local file on the file system"""
    try:
        if not os.path.exists(file_path):
            return f"Error: File not found at path '{file_path}'"
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except Exception as e:
        return f"Error reading file: {str(e)}"

@tool
def get_github_repos() -> str:
    """Get list of all GitHub repositories for the configured user"""
    username = os.getenv('GITHUB_USERNAME')
    return get_github_repos_info(username=username)

@tool
def analyze_github_repo(repo_name: str) -> str:
    """Analyze a GitHub repository structure and file types"""
    username = os.getenv('GITHUB_USERNAME')
    return github_analyze(repo_name, username=username)

@tool
def get_github_file_content(repo_name: str, file_path: str) -> str:
    """Read the content of a specific file from a GitHub repository"""
    username = os.getenv('GITHUB_USERNAME')
    return github_file_content(repo_name, file_path, username=username)

@tool
def list_chat_sessions(limit: int = 50) -> str:
    """List all chat sessions with details"""
    sessions = db.list_sessions(limit)
    return json.dumps(sessions, indent=2)

@tool
def get_session_details(session_id: str) -> str:
    """Get details of a specific chat session"""
    session = db.get_session(session_id)
    if not session:
        return f"Session {session_id} not found"
    return json.dumps(session, indent=2)

@tool
def search_conversations(query: str, limit: int = 50) -> str:
    """Search through conversation history for specific content"""
    results = db.search_messages(query, limit)
    return json.dumps(results, indent=2)

@tool
def get_pii_redaction_stats(session_id: str) -> str:
    """Get PII redaction statistics for a session (stub/compatibility)."""
    return json.dumps({"error": "PII redaction stats not implemented in tools.py"})

@tool
def get_s3_storage_info() -> str:
    """Alias for get_storage_info for backward compatibility."""
    return get_storage_info()

@tool
def get_storage_info() -> str:
    """Get storage configuration and status (alias for S3)."""
    info = {
        "storage_type": "Amazon S3",
        "bucket": os.getenv('S3_BUCKET_NAME'),
        "region": os.getenv('AWS_REGION'),
        "status": "connected"
    }
    return json.dumps(info, indent=2)
