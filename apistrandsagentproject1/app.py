# --- TOOL DECORATOR ---
def tool(func):
    """Decorator to mark a function as a tool (for agent frameworks or future integration)."""
    func.is_tool = True
    return func

import os
# Sliding window size for chat history (number of user+assistant messages)
SLIDING_WINDOW_SIZE = int(os.getenv('SLIDING_WINDOW_SIZE', 20))
from dotenv import load_dotenv
load_dotenv()
import openai

OPENAI_MODEL = "gpt-4o"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY not set in environment.")
openai.api_key = OPENAI_API_KEY

from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import os
from dotenv import load_dotenv
import webbrowser
from threading import Timer
import json
from s3_storage import S3Storage
from session_manager import SessionManager
from PII.pii_redactor import PIIRedactor
import io
import openai

# Import all tools
from tools import (
    read_local_file,
    get_github_repos,
    analyze_github_repo,
    get_github_file_content,
    list_chat_sessions,
    get_session_details,
    search_conversations,
    get_pii_redaction_stats,
    export_session_data,
    get_s3_storage_info,
    AVAILABLE_FILES
)

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Initialize S3 Storage and Session Manager
db = S3Storage()
session_manager = SessionManager(db)

# Initialize PII Redactor
pii_redactor = PIIRedactor()  # Regex-based (reliable)

# Try to load advanced PII redactor if enabled
USE_ADVANCED_PII_REDACTION = os.getenv('USE_ADVANCED_PII', 'false').lower() == 'true'
if USE_ADVANCED_PII_REDACTION:
    try:
        from PII.pii_redactor_advanced import AdvancedPIIRedactor
        pii_redactor_advanced = AdvancedPIIRedactor(use_llm_guard=True)
        active_pii_redactor = pii_redactor_advanced
        print("🔒 PII Redaction: Advanced (LLM Guard + BERT NER)")
    except ImportError as e:
        print(f"⚠️ Could not load advanced PII redactor: {e}")
        print("⚠️ Falling back to regex-based PII redaction")
        active_pii_redactor = pii_redactor
        print("🔒 PII Redaction: Regex-based")
else:
    active_pii_redactor = pii_redactor
    print("🔒 PII Redaction: Regex-based")

# Agent system prompt
AGENT_SYSTEM_PROMPT = "You are a helpful AI assistant."

class StrandsAgentWrapper:
    """Wrapper for Strands Agent with session management"""
    def __init__(self, session_manager):
        self.session_manager = session_manager

    @tool
    def ask(self, question: str, session_id: str, enable_pii_redaction: bool = True) -> dict:
        """
        Process a user question and return an answer
        Returns: dict with 'answer', 'pii_redaction_enabled', 'redaction_stats', etc.
        """
        # Get conversation history from session
        conversation_history = list(
            self.session_manager.get_conversation_history(session_id)
        )
        print(f"DEBUG - Loaded conversation history with {len(conversation_history)} messages")
        # Apply sliding window: only keep last N user/assistant messages
        filtered_history = [msg for msg in conversation_history if msg["role"] in ("user", "assistant")]
        if SLIDING_WINDOW_SIZE > 0:
            filtered_history = filtered_history[-SLIDING_WINDOW_SIZE:]
        # PII REDACTION: Redact question ONLY for database storage
        redacted_question = question
        redaction_metadata = {}
        if enable_pii_redaction:
            redacted_question, redaction_metadata = active_pii_redactor.redact(question, session_id)
            print(f"DEBUG - Original question (to OpenAI): {question}")
            print(f"DEBUG - Redacted question (to DB): {redacted_question}")
            print(f"DEBUG - Redactions found: {len(redaction_metadata)}")
        # Save REDACTED version to database (privacy protection)
        self.session_manager.add_message(
            session_id, 
            "user", 
            redacted_question,  # Store REDACTED question
            redacted_content=None
        )

        # --- FORCE TOOL CALL FOR GITHUB REPOS IF CREDENTIALS ARE SET ---
        import re
        github_token = os.getenv('GITHUB_TOKEN')
        github_username = os.getenv('GITHUB_USERNAME')
        print(f"[DEBUG] GITHUB_TOKEN set: {bool(github_token)} | GITHUB_USERNAME: {github_username}")
        print(f"[DEBUG] Incoming question: {question}")

        # --- FORCE TOOL CALL FOR SINGLE REPO ANALYSIS (PRIORITY) ---
        if github_token and github_username:
            analyze_patterns = [
                r"analy[sz]e github repo",
                r"analy[sz]e repo",
                r"repo structure",
                r"repo files",
                r"what files are in (the|my)? ?repo",
                r"file types? in repo",
                r"analy[sz]e ([\\w-]+) repo",
                r"repo summary",
                r"repo details",
                r"how many files are in ([\\w-]+) repo",
                r"number of files in ([\\w-]+) repo",
                r"count files in ([\\w-]+) repo",
                r"list all files in ([\\w-]+) repo",
                r"show all files in ([\\w-]+) repo",
                r"which files are in ([\\w-]+) repo",
                r"files in ([\\w-]+) repo",
                r"file count in ([\\w-]+) repo",
                r"total files in ([\\w-]+) repo",
                r"repo ([\\w-]+) files",
                r"how many files are there in ([\\w-]+)",
                r"how many files in ([\\w-]+)",
                r"number of files in ([\\w-]+)",
                r"total files in ([\\w-]+)",
                r"count files in ([\\w-]+)",
            ]
            matched_analyze = []
            repo_name = None
            for pat in analyze_patterns:
                m = re.search(pat, question, re.IGNORECASE)
                if m:
                    matched_analyze.append(pat)
                    repo_name_match = re.search(r"([\w-]+) repo|in ([\w-]+)$|in ([\w-]+) ", question, re.IGNORECASE)
                    if repo_name_match:
                        # Try to get the repo name from the right group
                        repo_name = next((g for g in repo_name_match.groups() if g), None)
                    else:
                        # Try to extract repo name directly
                        repo_name = m.group(1) if m.lastindex else None
                    break
            print(f"[DEBUG] analyze_patterns matched: {matched_analyze} | repo_name extracted: {repo_name}")
            if repo_name:
                from tools import analyze_github_repo
                analysis = analyze_github_repo(repo_name)
                self.session_manager.add_message(
                    session_id,
                    "assistant",
                    analysis,
                    redacted_content=None
                )
                if not hasattr(self, '_last_repo_query'):
                    self._last_repo_query = {}
                self._last_repo_query[session_id] = {'repo': repo_name, 'analysis': analysis}
                return {
                    'answer': analysis,
                    'pii_redaction_enabled': enable_pii_redaction
                }

        # --- FORCE TOOL CALL FOR FILE TYPES IN ALL REPOS (ONLY IF 'all repos' or similar is present) ---
        if github_token and github_username:
            file_types_patterns = [
                r"file types? in (all|total|every|my)? ?repos?",
                r"what type of files.*all repos?",
                r"types? of files.*all repos?",
                r"list all file types.*all repos?",
                r"what files are in (all|every|my|the)? ?repos?",
                r"which files are in (all|every|my|the)? ?repos?",
                r"show all file types.*all repos?",
                r"show me file types.*all repos?",
                r"how many file types.*all repos?",
                r"file extension[s]? in all repos?",
                r"filetype[s]? in all repos?",
                r"file types? across all repos?",
                r"repo file types? across all repos?",
                r"repos? file types?",
            ]
            matched = [pat for pat in file_types_patterns if re.search(pat, question, re.IGNORECASE)]
            print(f"[DEBUG] file_types_patterns matched: {matched}")
            if matched:
                from tools import get_github_repos, analyze_github_repo
                repos_result = get_github_repos()
                repo_names = []
                import re as _re
                for line in repos_result.splitlines():
                    m = _re.match(r"\d+\. \*\*(.+?)\*\*", line)
                    if m:
                        repo_names.append(m.group(1))
                summary = []
                found_any = False
                for repo in repo_names:
                    analysis = analyze_github_repo(repo)
                    # Extract file types and file names
                    file_types = {}
                    files_section = False
                    files = []
                    for l in analysis.splitlines():
                        if l.strip().startswith("File types:"):
                            continue
                        if l.strip().startswith("- ."):
                            parts = l.strip().split(":")
                            if len(parts) == 2:
                                ext = parts[0].replace("- .", "").strip()
                                count = parts[1].strip()
                                file_types[ext] = {"count": count, "files": []}
                        if l.strip().startswith("All Files"):
                            files_section = True
                            continue
                        if files_section:
                            l = l.strip()
                            if not l or not l.startswith("-"):
                                break
                            file_path = l.lstrip("- ")
                            files.append(file_path)
                    for file_path in files:
                        ext = file_path.split(".")[-1] if "." in file_path else "no_ext"
                        if ext in file_types:
                            file_types[ext]["files"].append(file_path)
                        else:
                            file_types[ext] = {"count": 1, "files": [file_path]}
                    if file_types:
                        found_any = True
                        section = f"**{repo}**\n"
                        for ext, info in file_types.items():
                            section += f"- .{ext}: {len(info['files'])} files\n"
                            for fname in info['files']:
                                section += f"    - {fname}\n"
                        summary.append(section)
                    else:
                        summary.append(f"**{repo}**\n(No files found)\n")
                if found_any:
                    result = "File types in all your repositories (grouped by repo, with file names):\n\n" + "\n".join(summary)
                else:
                    result = "No files found in any of your repositories."
                self.session_manager.add_message(
                    session_id,
                    "assistant",
                    result,
                    redacted_content=None
                )
                return {
                    'answer': result,
                    'pii_redaction_enabled': enable_pii_redaction
                }

            # --- FORCE TOOL CALL FOR LISTING YAML FILES IN A REPO ---
            yaml_patterns = [
                r"(what|which|list|show|display).*(yaml|yml) files.*in ([\w\-]+)",
                r"(yaml|yml) files.*in ([\w\-]+)",
                r"list all (yaml|yml) files.*([\w\-]+)",
            ]
            repo_name = None
            for pat in yaml_patterns:
                m = re.search(pat, question, re.IGNORECASE)
                if m:
                    if m.lastindex:
                        repo_name = m.group(m.lastindex)
                    else:
                        repo_match = re.search(r'in ([\w\-]+)', question, re.IGNORECASE)
                        if repo_match:
                            repo_name = repo_match.group(1)
                    break
            if repo_name:
                from tools import analyze_github_repo
                analysis = analyze_github_repo(repo_name)
                yaml_files = []
                in_files_section = False
                for l in analysis.splitlines():
                    if l.strip().startswith("All Files"):
                        in_files_section = True
                        continue
                    if in_files_section:
                        l = l.strip()
                        if not l or not l.startswith("-"):
                            break
                        file_path = l.lstrip("- ")
                        if file_path.endswith('.yml') or file_path.endswith('.yaml'):
                            yaml_files.append(file_path)
                if yaml_files:
                    result = f"YAML files in {repo_name} repo:\n\n" + "\n".join(yaml_files)
                else:
                    result = f"No YAML (.yml/.yaml) files found in {repo_name} repo."
                self.session_manager.add_message(
                    session_id,
                    "assistant",
                    result,
                    redacted_content=None
                )
                return {
                    'answer': result,
                    'pii_redaction_enabled': enable_pii_redaction
                }
        if github_token and github_username:
            # Patterns for different GitHub actions
            repo_list_patterns = [
                r"github repos?", r"github repositories?", r"list my github", r"show.*github repos?", r"my github projects?"
            ]
            analyze_patterns = [
                r"analy[sz]e github repo",
                r"analy[sz]e repo",
                r"repo structure",
                r"repo files",
                r"what files are in (the|my)? ?repo",
                r"file types? in repo",
                r"analy[sz]e ([\\w-]+) repo",
                r"repo summary",
                r"repo details",
                r"how many files are in ([\\w-]+) repo",
                r"number of files in ([\\w-]+) repo",
                r"count files in ([\\w-]+) repo",
                r"list all files in ([\\w-]+) repo",
                r"show all files in ([\\w-]+) repo",
                r"which files are in ([\\w-]+) repo",
                r"files in ([\\w-]+) repo",
                r"file count in ([\\w-]+) repo",
                r"total files in ([\\w-]+) repo",
                r"repo ([\\w-]+) files",
                r"how many files are there in ([\\w-]+)",
                r"how many files in ([\\w-]+)",
                r"number of files in ([\\w-]+)",
                r"total files in ([\\w-]+)",
                r"count files in ([\\w-]+)",
            ]
            file_content_patterns = [
                r"read file from github", r"show file .* in repo", r"get file .* from repo", r"file content in repo", r"readme from repo", r"content of ([\\w./-]+) in repo", r"show ([\\w./-]+) in repo"
            ]

            matched_repo_list = [pat for pat in repo_list_patterns if re.search(pat, question, re.IGNORECASE)]
            print(f"[DEBUG] repo_list_patterns matched: {matched_repo_list}")
            if matched_repo_list:
                from tools import get_github_repos
                tool_result = get_github_repos()
                self.session_manager.add_message(
                    session_id,
                    "assistant",
                    tool_result,
                    redacted_content=None
                )
                return {
                    'answer': tool_result,
                    'pii_redaction_enabled': enable_pii_redaction
                }


            # Check for analyze repo
            repo_name = None
            matched_analyze = []
            for pat in analyze_patterns:
                m = re.search(pat, question, re.IGNORECASE)
                if m:
                    matched_analyze.append(pat)
                    # Try to extract repo name from question
                    repo_name_match = re.search(r"([\w-]+) repo", question, re.IGNORECASE)
                    if repo_name_match:
                        repo_name = repo_name_match.group(1)
                    break
            print(f"[DEBUG] analyze_patterns matched: {matched_analyze} | repo_name extracted: {repo_name}")
            if repo_name:
                from tools import analyze_github_repo
                analysis = analyze_github_repo(repo_name)
                # If user asks for file count, store the last repo and analysis in session for follow-up
                self.session_manager.add_message(
                    session_id,
                    "assistant",
                    analysis,
                    redacted_content=None
                )
                # Store last repo and analysis for follow-up
                if not hasattr(self, '_last_repo_query'):
                    self._last_repo_query = {}
                self._last_repo_query[session_id] = {'repo': repo_name, 'analysis': analysis}
                return {
                    'answer': analysis,
                    'pii_redaction_enabled': enable_pii_redaction
                }

            # Expanded follow-up detection for file listing
            followup_file_list_patterns = [
                r"^yes$",
                r"^what are those\??$",
                r"^show me (the )?files$",
                r"^list (them|the files)$",
                r"^which files$",
                r"^display (the )?files$",
                r"^can you show (the )?files$",
                r"^list all files$",
                r"^show all files$",
                r"^show files$",
                r"^list files$",
                r"^give me (the )?files$",
                r"^what files$",
                r"^files\??$",
                r"^can i see (the )?files$",
                r"^please show (the )?files$",
                r"^please list (the )?files$",
                r"^reveal (the )?files$",
                r"^enumerate (the )?files$",
            ]
            if any(re.match(pat, question.strip().lower()) for pat in followup_file_list_patterns):
                last = getattr(self, '_last_repo_query', {}).get(session_id)
                if last:
                    analysis = last['analysis']
                    files = []
                    in_files_section = False
                    for l in analysis.splitlines():
                        if l.strip().startswith("All Files"):
                            in_files_section = True
                            continue
                        if in_files_section:
                            l = l.strip()
                            if not l or not l.startswith("-"):
                                break
                            file_path = l.lstrip("- ")
                            files.append(file_path)
                    if files:
                        result = f"Files in {last['repo']} repo:\n\n" + "\n".join(files)
                    else:
                        result = f"No files found in {last['repo']} repo."
                    self.session_manager.add_message(
                        session_id,
                        "assistant",
                        result,
                        redacted_content=None
                    )
                    return {
                        'answer': result,
                        'pii_redaction_enabled': enable_pii_redaction
                    }

            # Check for get file content from repo
            repo_name = None
            file_path = None
            for pat in file_content_patterns:
                m = re.search(pat, question, re.IGNORECASE)
                if m:
                    # Try to extract file path and repo name
                    file_match = re.search(r"file ([\w./-]+) in ([\w-]+) repo", question, re.IGNORECASE)
                    if file_match:
                        file_path = file_match.group(1)
                        repo_name = file_match.group(2)
                    break
            if repo_name and file_path:
                from tools import get_github_file_content
                tool_result = get_github_file_content(repo_name, file_path)
                self.session_manager.add_message(
                    session_id,
                    "assistant",
                    tool_result,
                    redacted_content=None
                )
                return {
                    'answer': tool_result,
                    'pii_redaction_enabled': enable_pii_redaction
                }

        try:
            # Prepare OpenAI chat history with sliding window
            messages = [{"role": "system", "content": AGENT_SYSTEM_PROMPT}]
            for msg in filtered_history:
                messages.append({"role": msg["role"], "content": msg["content"]})
            messages.append({"role": "user", "content": question})
            print("DEBUG - Messages sent to OpenAI (sliding window):")
            for i, m in enumerate(messages):
                print(f"  {i}: role={m['role']}, content={m['content'][:80]}{'...' if len(m['content'])>80 else ''}")

            response = openai.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages,
                temperature=0.7,
                max_tokens=512
            )
            assistant_message = response.choices[0].message.content

            # PII REDACTION: Redact assistant response ONLY for database storage
            redacted_answer = assistant_message
            if enable_pii_redaction and assistant_message:
                redacted_answer, _ = active_pii_redactor.redact(assistant_message, session_id)
                print(f"DEBUG - Original answer (to user): {assistant_message}")
                print(f"DEBUG - Redacted answer (to DB): {redacted_answer}")
            # Save response with REDACTED version in database
            self.session_manager.add_message(
                session_id, 
                "assistant", 
                redacted_answer,  # Store REDACTED answer (privacy)
                redacted_content=None
            )
            print("Answer:", assistant_message)
            # Return comprehensive response
            response_data = {
                'answer': assistant_message,  # Return ORIGINAL answer to user
                'pii_redaction_enabled': enable_pii_redaction
            }
            if enable_pii_redaction:
                response_data['redacted_question'] = redacted_question
                response_data['redaction_stats'] = active_pii_redactor.get_redaction_stats(session_id)
            return response_data
        except Exception as e:
            error_message = f"Error processing your question: {str(e)}"
            print(f"DEBUG - Full error: {e}")
            print(f"DEBUG - Error type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            return {'answer': error_message, 'error': True}

    @tool
    def reset(self, session_id: str):
        """Reset conversation history for a session"""
        if self.session_manager:
            self.session_manager.delete_session(session_id)

# Global agent instance
agent = StrandsAgentWrapper(session_manager)


@tool
@app.route('/')
def index():
    """Serve the main chat interface"""
    return render_template('index.html')


@tool
@app.route('/api/chat', methods=['POST'])
def chat():
    """API endpoint to process user questions with PII redaction"""
    try:
        data = request.get_json()
        question = data.get('question', '')
        session_id = data.get('session_id')
        enable_pii_redaction = data.get('enable_pii_redaction', True)  # Default: enabled
        
        if not question:
            return jsonify({'error': 'No question provided'}), 400
        
        if not session_id:
            return jsonify({'error': 'No session ID provided'}), 400
        
        # Verify session exists
        if not session_manager.session_exists(session_id):
            return jsonify({'error': 'Invalid session ID'}), 404
        
        # Get response from agent
        result = agent.ask(question, session_id, enable_pii_redaction)
        
        return jsonify({
            'answer': result.get('answer'),
            'status': 'success',
            'session_id': session_id,
            'pii_redaction_enabled': result.get('pii_redaction_enabled', False),
            'redaction_stats': result.get('redaction_stats', {}),
            'redacted_question': result.get('redacted_question')
        })
    
    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500


@tool
@app.route('/api/reset', methods=['POST'])
def reset():
    """Reset the conversation for a session"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        
        if not session_id:
            return jsonify({'error': 'No session ID provided'}), 400
        
        agent.reset(session_id)
        return jsonify({'status': 'success', 'message': 'Conversation reset'})
    
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500


@tool
@app.route('/api/session/new', methods=['POST'])
def create_new_session():
    """Create a new chat session"""
    try:
        data = request.get_json() or {}
        user_identifier = data.get('user_identifier')
        session_title = data.get('session_title', 'New Conversation')
        
        session_id = session_manager.create_session(user_identifier, session_title)
        
        return jsonify({
            'status': 'success',
            'session_id': session_id,
            'message': 'Session created successfully'
        })
    
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500


@tool
@app.route('/api/session/list', methods=['GET'])
def list_sessions():
    """Get list of all sessions"""
    try:
        limit = request.args.get('limit', 50, type=int)
        sessions = session_manager.list_sessions(limit)
        
        return jsonify({
            'status': 'success',
            'sessions': sessions
        })
    
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500


@tool
@app.route('/api/session/<session_id>', methods=['GET'])
def get_session(session_id):
    """Get session details and conversation history"""
    try:
        session_info = db.get_session(session_id)
        
        if not session_info:
            return jsonify({'error': 'Session not found'}), 404
        
        conversation = db.get_conversation_history(session_id)
        stats = db.get_session_stats(session_id)
        
        return jsonify({
            'status': 'success',
            'session': session_info,
            'conversation': conversation,
            'stats': stats
        })
    
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500


@tool
@app.route('/api/session/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    """Delete a session"""
    try:
        success = session_manager.delete_session(session_id)
        
        if not success:
            return jsonify({'error': 'Session not found'}), 404
        
        return jsonify({
            'status': 'success',
            'message': 'Session deleted successfully'
        })
    
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500


@tool
@app.route('/api/session/<session_id>/export', methods=['GET'])
def export_session(session_id):
    """Export session data as JSON file"""
    try:
        export_data = session_manager.export_session(session_id)
        
        if not export_data:
            return jsonify({'error': 'Session not found'}), 404
        
        # Create JSON file in memory
        json_str = json.dumps(export_data, indent=2)
        json_bytes = io.BytesIO(json_str.encode('utf-8'))
        
        return send_file(
            json_bytes,
            mimetype='application/json',
            as_attachment=True,
            download_name=f'session_{session_id[:8]}_export.json'
        )
    
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500


@tool
@app.route('/api/search', methods=['GET'])
def search_conversations():
    """Search through conversation history"""
    try:
        query = request.args.get('q', '')
        limit = request.args.get('limit', 50, type=int)
        
        if not query:
            return jsonify({'error': 'No search query provided'}), 400
        
        results = db.search_messages(query, limit)
        
        return jsonify({
            'status': 'success',
            'results': results,
            'count': len(results)
        })
    
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500


@tool
@app.route('/api/session/<session_id>/redaction-stats', methods=['GET'])
def get_redaction_stats(session_id):
    """Get PII redaction statistics for a session"""
    try:
        stats = active_pii_redactor.get_redaction_stats(session_id)
        return jsonify({
            'status': 'success',
            'stats': stats
        })
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500


@tool
@app.route('/api/session/<session_id>/redaction-map', methods=['GET'])
def export_redaction_map(session_id):
    """Export redaction map for auditing"""
    try:
        redaction_map = active_pii_redactor.export_redaction_map(session_id)
        return jsonify({
            'status': 'success',
            'redaction_map': redaction_map
        })
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500


@tool
@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    # Clean up old sessions (30+ days)
    session_manager.cleanup_old_sessions(30)
    
    return jsonify({'status': 'healthy', 'agent': 'ready'})


@tool
@app.route('/api/session/<session_id>/clear-cache', methods=['POST'])
def clear_session_cache(session_id):
    """Clear session cache to force reload from database"""
    try:
        result = session_manager.clear_session_cache(session_id)
        if result:
            return jsonify({
                'status': 'success',
                'message': f'Cache cleared for session {session_id}'
            })
        else:
            return jsonify({
                'status': 'not_found',
                'message': f'Session {session_id} not in cache'
            })
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500


@tool
@app.route('/api/cache/clear-all', methods=['POST'])
def clear_all_cache():
    """Clear all session caches"""
    try:
        session_manager.clear_session_cache()
        return jsonify({
            'status': 'success',
            'message': 'All session caches cleared'
        })
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500


@tool
def open_browser():
    """Open the browser after a short delay"""
    webbrowser.open('http://127.0.0.1:5000')


if __name__ == '__main__':
    # Check if API key is set
    if not os.getenv('OPENAI_API_KEY') or os.getenv('OPENAI_API_KEY') == 'your_openai_api_key_here':
        print("=" * 60)
        print("WARNING: OPENAI_API_KEY not set!")
        print("Please create a .env file with your OpenAI API key.")
        print("Copy .env.example to .env and add your key.")
        print("=" * 60)
    
    print("=" * 60)
    print("🚀 Starting Strands Agent Application...")
    print("=" * 60)
    print("📡 API Server: http://127.0.0.1:5000")
    print("🤖 Agent: Ready")    
    print("💾 Storage: Amazon S3")    
    print("=" * 60)
    print("Opening browser in 2 seconds...")
    print("=" * 60)
    
    # Open browser after 2 seconds
    Timer(2, open_browser).start()
    
    # Run Flask app
    app.run(debug=True, use_reloader=False)
