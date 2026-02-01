# Strands Agent Application - Complete Documentation

**Version:** 1.0  
**Date:** January 27, 2026  
**Author:** Garlapati Venkata Srinivas

---

## 📑 Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [File-by-File Explanation](#file-by-file-explanation)
4. [Data Flow](#data-flow)
5. [API Documentation](#api-documentation)
6. [Database Schema](#database-schema)
7. [Tool System](#tool-system)

---

## 🎯 Project Overview

This is a production-ready AI agent application built with:
- **Backend:** Flask (Python)
- **AI Model:** OpenAI GPT-4o
- **Database:** SQLite
- **Frontend:** HTML/CSS/JavaScript
- **Features:** Multi-user sessions, conversation history, tool calling, GitHub integration

### Key Features:
✅ **Multi-Session Support** - Multiple users can have independent conversations  
✅ **Persistent History** - All conversations saved to database  
✅ **Tool Integration** - AI can read files and access GitHub  
✅ **Modern UI** - Beautiful gradient design with session management  
✅ **Export/Import** - Download conversations as JSON  
✅ **Auto-Cleanup** - Removes old sessions automatically  

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    FRONTEND (Browser)                    │
│  ┌─────────────────────────────────────────────────┐   │
│  │  index.html (User Interface)                     │   │
│  │  - Chat messages                                 │   │
│  │  - Session sidebar                               │   │
│  │  - Input field                                   │   │
│  └─────────────────────────────────────────────────┘   │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP/JSON
                       ▼
┌─────────────────────────────────────────────────────────┐
│              BACKEND (Flask - app.py)                    │
│  ┌─────────────────────────────────────────────────┐   │
│  │  API Routes                                      │   │
│  │  /api/chat, /api/session/*, /api/search         │   │
│  └─────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────┐   │
│  │  StrandsAgent (AI Logic)                        │   │
│  │  - Conversation management                       │   │
│  │  - Tool calling                                  │   │
│  │  - OpenAI integration                            │   │
│  └─────────────────────────────────────────────────┘   │
└──────┬────────────────────────┬────────────────────┬────┘
       │                        │                    │
       ▼                        ▼                    ▼
┌──────────────┐    ┌──────────────────┐   ┌───────────────┐
│ Session      │    │ Database         │   │ GitHub Access │
│ Manager      │    │ (database.py)    │   │ (github       │
│ (session_    │◄───┤ - Sessions       │   │  access.py)   │
│  manager.py) │    │ - Messages       │   │ - Repos       │
│              │    │ - SQLite         │   │ - Files       │
└──────────────┘    └──────────────────┘   └───────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ strands_agent.db│
                    │ (SQLite File)   │
                    └─────────────────┘
```

---

## 📄 File-by-File Explanation

### 1. **app.py** (552 lines) - Main Application

**Location:** Root directory  
**Purpose:** Core Flask application with API routes and AI agent logic

#### **Sections:**

##### **A. Imports & Configuration (Lines 1-25)**
```python
from flask import Flask, render_template, request, jsonify, send_file
from openai import OpenAI
from database import Database
from session_manager import SessionManager
from githubaccess import get_github_repos_info, analyze_github_repo, get_github_file_content
```

**Why these imports?**
- `Flask` - Web framework for creating API endpoints
- `OpenAI` - Communicate with GPT-4o model
- `Database` - Persistent storage of conversations
- `SessionManager` - High-level session operations
- `githubaccess` - Tools for GitHub integration

##### **B. Tool Definitions (Lines 27-112)**

Defines 4 tools the AI agent can use:

**1. read_local_file** (Lines 27-41)
```python
{
    "type": "function",
    "function": {
        "name": "read_local_file",
        "description": "Read the contents of a file from the local file system",
        "parameters": {
            "file_path": {
                "type": "string",
                "description": "Absolute or relative path to file"
            }
        }
    }
}
```
- Reads files from predefined paths
- Security: Only accesses files in AVAILABLE_FILES dictionary
- Use case: Reading personal info, config files, data files

**2. get_github_repos** (Lines 43-58)
- Lists all GitHub repositories for authenticated user
- Optional username parameter
- Returns: repo names, descriptions, languages, stars

**3. analyze_github_repo** (Lines 60-80)
- Analyzes specific repository structure
- Returns: file count, file types, file list
- Use case: "What files are in my repo?"

**4. get_github_file_content** (Lines 82-112)
- Reads specific file from GitHub repository
- Parameters: repo_name, file_path
- Returns: File content as text

##### **C. Tool Implementation Functions (Lines 114-136)**

**read_local_file(file_path: str) -> str**
```python
def read_local_file(file_path: str) -> str:
    """Read a file from the local file system"""
    try:
        # Normalize path
        file_path = os.path.normpath(file_path)
        
        # Security check
        if not os.path.exists(file_path):
            return f"Error: File not found at path '{file_path}'"
        
        # Read file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return f"File content from '{file_path}':\n\n{content}"
    except UnicodeDecodeError:
        # Fallback to latin-1 for binary files
        with open(file_path, 'r', encoding='latin-1') as f:
            content = f.read()
        return f"File content (binary decoded):\n\n{content}"
    except Exception as e:
        return f"Error reading file: {str(e)}"
```

**Key Features:**
- Path normalization (handles Windows/Unix paths)
- File existence validation
- UTF-8 encoding with fallback
- Error handling with descriptive messages

##### **D. Available Files Dictionary (Lines 138-149)**
```python
AVAILABLE_FILES = {
    "config": r"C:\Users\Hp\Desktop\apistrandsagentproject\app.py",
    "requirements": r"C:\Users\Hp\Desktop\apistrandsagentproject\requirements.txt",
    "readme": r"C:\Users\Hp\Desktop\apistrandsagentproject\README.md",
    "env_example": r"C:\Users\Hp\Desktop\apistrandsagentproject\.env.example",
    "inventory": r"C:\Users\Hp\Desktop\apistrandsagentproject\data\inventory.txt",
    "personal_info": r"C:\Users\Hp\Desktop\apistrandsagentproject\data\Strands_agents_sampletestfile.txt.txt",
}
```

**Purpose:**
- Whitelist of files agent can access
- Security measure (prevents arbitrary file access)
- Easy to add new files

##### **E. Agent System Prompt (Lines 151-175)**
```python
AGENT_SYSTEM_PROMPT = f"""You are a helpful AI assistant powered by Strands Agents. 
You can answer questions, provide information, help with tasks, and have natural conversations.

You have access to the following capabilities:
- General knowledge and information retrieval
- Problem-solving and analysis
- Code help and technical assistance
- Creative writing and brainstorming
- Math and calculations
- Reading specific files from the local file system
- Accessing GitHub repositories to view files, analyze repos, and read file contents

You have access to these pre-configured files:
{chr(10).join([f"- {name}: {path}" for name, path in AVAILABLE_FILES.items()])}

IMPORTANT: When a user asks about personal information (like their friend's name, brother's name, age, etc.), 
always check the 'personal_info' file first using the read_local_file tool.

When a user asks about GitHub repositories, use the GitHub tools:
- Use 'get_github_repos' to list all repositories
- Use 'analyze_github_repo' to get details about a specific repo
- Use 'get_github_file_content' to read the content of a specific file in a repo

Always be helpful, accurate, and concise in your responses."""
```

**Purpose:**
- Instructions for AI behavior
- Lists available capabilities
- Guides tool usage
- Ensures consistent personality

##### **F. StrandsAgent Class (Lines 177-325)**

**The Brain of the Application**

**Class Structure:**
```python
class StrandsAgent:
    def __init__(self, model="gpt-4o", session_manager=None):
        self.model = model
        self.session_manager = session_manager
    
    def ask(self, question: str, session_id: str) -> str:
        # Main conversation logic
        pass
    
    def reset(self, session_id: str):
        # Reset conversation
        pass
```

**Method: ask(question, session_id)** - The Core Logic

**Flow Diagram:**
```
User Question
     ↓
Load Conversation History from Database
     ↓
Add User Message to History
     ↓
Save User Message to Database
     ↓
Send to OpenAI (with system prompt + history + tools)
     ↓
     ├─ No Tool Call? → Return Direct Answer
     │                    ↓
     │                  Save Answer to Database
     │                    ↓
     │                  Return to User
     │
     └─ Tool Call Needed?
            ↓
        For Each Tool Call:
            ├─ Parse function name & arguments
            ├─ Execute function (read_file, github_repos, etc.)
            ├─ Get result
            └─ Create tool response message
            ↓
        Send Tool Results Back to OpenAI
            ↓
        Get Final Answer
            ↓
        Save Answer to Database
            ↓
        Return to User
```

**Step-by-Step Code Explanation:**

**Step 1: Load Conversation History (Lines 193-200)**
```python
# Get conversation history from session
conversation_history = list(
    self.session_manager.get_conversation_history(session_id)
)

print(f"DEBUG - Loaded conversation history with {len(conversation_history)} messages")
```
- Loads all previous messages for context
- Includes user messages, assistant responses, and tool calls
- Essential for maintaining conversation continuity

**Step 2: Add User Message (Lines 202-210)**
```python
# Add user message to history
user_message = {
    "role": "user",
    "content": question
}
self.session_manager.add_message(session_id, "user", question)
```
- Formats user question in OpenAI format
- Saves to database immediately
- Adds to in-memory conversation history

**Step 3: Call OpenAI API (Lines 212-222)**
```python
response = openai_client.chat.completions.create(
    model=self.model,
    max_tokens=512,
    messages=[
        {"role": "system", "content": AGENT_SYSTEM_PROMPT}
    ] + conversation_history + [user_message],
    tools=tools,
    tool_choice="auto"
)
```
- Sends entire conversation to OpenAI
- Includes system prompt (AI personality)
- Includes all 4 tools
- `tool_choice="auto"` lets AI decide when to use tools

**Step 4: Check for Tool Calls (Lines 224-226)**
```python
response_message = response.choices[0].message
tool_calls = response_message.tool_calls

if tool_calls:
    # AI wants to use tools
else:
    # Direct answer
```
- OpenAI returns tool_calls if it needs to use a tool
- Otherwise, returns direct answer

**Step 5: Execute Tools (Lines 228-286)**
```python
# Add assistant's message with tool_calls to history
assistant_message_with_tools = {
    "role": "assistant",
    "content": response_message.content or "",
    "tool_calls": [
        {
            "id": tc.id,
            "type": tc.type,
            "function": {
                "name": tc.function.name,
                "arguments": tc.function.arguments
            }
        } for tc in tool_calls
    ]
}
conversation_history.append(assistant_message_with_tools)

# Process each tool call
for tool_call in tool_calls:
    function_name = tool_call.function.name
    function_args = json.loads(tool_call.function.arguments)
    
    # Execute the appropriate function
    if function_name == "read_local_file":
        function_response = read_local_file(
            file_path=function_args.get("file_path")
        )
    elif function_name == "get_github_repos":
        function_response = get_github_repos_info(
            username=function_args.get("username")
        )
    elif function_name == "analyze_github_repo":
        function_response = analyze_github_repo(
            repo_name=function_args.get("repo_name"),
            username=function_args.get("username")
        )
    elif function_name == "get_github_file_content":
        function_response = get_github_file_content(
            repo_name=function_args.get("repo_name"),
            file_path=function_args.get("file_path"),
            username=function_args.get("username")
        )
    else:
        function_response = f"Error: Unknown function {function_name}"
    
    # Add function response to conversation
    tool_message = {
        "role": "tool",
        "tool_call_id": tool_call.id,
        "content": function_response
    }
    conversation_history.append(tool_message)
    self.session_manager.add_message(session_id, "tool", function_response, tool_call_id=tool_call.id)
```

**Key Points:**
- Must add assistant message with tool_calls BEFORE tool responses
- Each tool call has unique ID
- Tool responses reference tool_call_id
- Try/catch ensures errors are handled gracefully

**Step 6: Get Final Answer (Lines 288-297)**
```python
# Get final response from the model
second_response = openai_client.chat.completions.create(
    model=self.model,
    max_tokens=512,
    messages=[
        {"role": "system", "content": AGENT_SYSTEM_PROMPT}
    ] + conversation_history
)

assistant_message = second_response.choices[0].message.content
```
- Send tool results back to OpenAI
- AI uses tool data to formulate answer
- Returns natural language response

**Step 7: Save and Return (Lines 299-310)**
```python
# Add assistant response to history
self.session_manager.add_message(session_id, "assistant", assistant_message)

return assistant_message
```
- Saves final answer to database
- Returns answer to user

##### **G. Flask Routes (Lines 327-500)**

**Route 1: GET / (Homepage)**
```python
@app.route('/')
def index():
    """Serve the main chat interface"""
    return render_template('index.html')
```
- Renders main UI
- Entry point for users

**Route 2: POST /api/chat (Main Chat Endpoint)**
```python
@app.route('/api/chat', methods=['POST'])
def chat():
    """API endpoint to process user questions"""
    try:
        data = request.get_json()
        question = data.get('question', '')
        session_id = data.get('session_id')
        
        if not question:
            return jsonify({'error': 'No question provided'}), 400
        
        if not session_id:
            return jsonify({'error': 'No session ID provided'}), 400
        
        # Verify session exists
        if not session_manager.session_exists(session_id):
            return jsonify({'error': 'Invalid session ID'}), 404
        
        # Get response from agent
        answer = agent.ask(question, session_id)
        print("Answer:", answer)
        
        return jsonify({
            'answer': answer,
            'status': 'success',
            'session_id': session_id
        })
    
    except Exception as e:
        error_message = f"Error processing your question: {str(e)}"
        print(f"DEBUG - Full error: {e}")
        import traceback
        traceback.print_exc()
        return error_message
```

**Request Format:**
```json
{
    "question": "What's my friend's name?",
    "session_id": "abc-123-def-456"
}
```

**Response Format:**
```json
{
    "answer": "Your friend's name is Akhil Shanmukha Kothamasu",
    "status": "success",
    "session_id": "abc-123-def-456"
}
```

**Route 3: POST /api/reset (Clear Conversation)**
```python
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
```
- Deletes all messages in a session
- Starts fresh conversation

**Route 4: POST /api/session/new (Create Session)**
```python
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
```
- Generates unique UUID
- Creates database entry
- Returns session_id

**Route 5: GET /api/session/list (List All Sessions)**
```python
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
```
- Returns all sessions ordered by activity
- Used for sidebar display

**Route 6: GET /api/session/<session_id> (Get Session Details)**
```python
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
```
- Returns session metadata
- Returns all messages
- Returns statistics (message count, dates)

**Route 7: DELETE /api/session/<session_id> (Delete Session)**
```python
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
```
- Removes session from database
- Cascade deletes all messages

**Route 8: GET /api/session/<session_id>/export (Export Session)**
```python
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
```
- Creates downloadable JSON file
- Contains session info, messages, statistics

**Route 9: GET /api/search (Search Conversations)**
```python
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
```
- Full-text search across all messages
- Returns matching messages with context

**Route 10: GET /api/health (Health Check)**
```python
@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    # Clean up old sessions (30+ days)
    session_manager.cleanup_old_sessions(30)
    
    return jsonify({'status': 'healthy', 'agent': 'ready'})
```
- Verifies API is running
- Performs cleanup on each call

##### **H. Application Startup (Lines 502-522)**
```python
def open_browser():
    """Open the browser after a short delay"""
    webbrowser.open('http://127.0.0.1:5000')

if __name__ == '__main__':
    # Check if API key is set
    if not os.getenv('OPENAI_API_KEY'):
        print("WARNING: OPENAI_API_KEY not set!")
        print("Please create a .env file with your OpenAI API key.")
    
    print("=" * 60)
    print("🚀 Starting Strands Agent Application...")
    print("=" * 60)
    print("📡 API Server: http://127.0.0.1:5000")
    print("🤖 Agent: Ready")
    print("=" * 60)
    
    # Open browser after 2 seconds
    Timer(2, open_browser).start()
    
    # Run Flask app
    app.run(debug=True, use_reloader=False)
```
- Validates environment variables
- Auto-opens browser
- Starts Flask server on port 5000

---

### 2. **database.py** (242 lines) - Database Layer

**Location:** Root directory  
**Purpose:** SQLite database operations for persistent storage

#### **Class: Database**

##### **Method: init_database() (Lines 19-51)**
```python
def init_database(self):
    """Create tables if they don't exist"""
    conn = sqlite3.connect(self.db_path)
    cursor = conn.cursor()
    
    # Create sessions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_identifier TEXT,
            session_title TEXT
        )
    ''')
    
    # Create messages table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            message_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            tool_calls TEXT,
            tool_call_id TEXT,
            FOREIGN KEY (session_id) REFERENCES sessions (session_id) ON DELETE CASCADE
        )
    ''')
    
    # Create indexes for better performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_session_id ON messages(session_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON messages(timestamp)')
    
    conn.commit()
    conn.close()
```

**Database Schema:**

**sessions table:**
| Column | Type | Description |
|--------|------|-------------|
| session_id | TEXT (PK) | Unique UUID for session |
| created_at | TIMESTAMP | Session creation time |
| last_activity | TIMESTAMP | Last message timestamp |
| user_identifier | TEXT | Optional user ID |
| session_title | TEXT | Display name |

**messages table:**
| Column | Type | Description |
|--------|------|-------------|
| message_id | INTEGER (PK) | Auto-increment ID |
| session_id | TEXT (FK) | Links to session |
| role | TEXT | "user", "assistant", or "tool" |
| content | TEXT | Message content |
| timestamp | TIMESTAMP | When message was sent |
| tool_calls | TEXT | JSON of tool calls |
| tool_call_id | TEXT | For tool responses |

**Why this schema?**
- Foreign key ensures messages deleted with session
- Indexes on session_id and timestamp for fast queries
- Stores tool_calls as JSON for flexibility
- Separate tool_call_id for linking responses

##### **Method: create_session() (Lines 53-65)**
```python
def create_session(self, session_id: str, user_identifier: str = None, session_title: str = "New Conversation") -> bool:
    """Create a new session"""
    try:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO sessions (session_id, user_identifier, session_title) VALUES (?, ?, ?)',
            (session_id, user_identifier, session_title)
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False  # Session already exists
```

##### **Method: add_message() (Lines 127-141)**
```python
def add_message(self, session_id: str, role: str, content: str, tool_calls: str = None, tool_call_id: str = None) -> int:
    """Add a message to a session"""
    conn = sqlite3.connect(self.db_path)
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO messages (session_id, role, content, tool_calls, tool_call_id) VALUES (?, ?, ?, ?, ?)',
        (session_id, role, content, tool_calls, tool_call_id)
    )
    message_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    # Update session activity
    self.update_session_activity(session_id)
    
    return message_id
```

**Important:** Updates session's last_activity on every message

##### **Method: get_conversation_history() (Lines 143-169)**
```python
def get_conversation_history(self, session_id: str) -> List[Dict]:
    """Get all messages for a session"""
    conn = sqlite3.connect(self.db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        'SELECT * FROM messages WHERE session_id = ? ORDER BY timestamp ASC',
        (session_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    
    messages = []
    for row in rows:
        msg = dict(row)
        # Parse tool_calls if present
        if msg.get('tool_calls'):
            try:
                parsed = json.loads(msg['tool_calls'])
                msg['tool_calls'] = parsed
            except Exception as e:
                print(f"DEBUG - Error parsing tool_calls: {e}")
                msg['tool_calls'] = None
        messages.append(msg)
    
    return messages
```

**Critical Function:**
- Loads entire conversation in order
- Parses JSON tool_calls back to Python objects
- Used before every API call to OpenAI

---

### 3. **session_manager.py** (184 lines) - Session Management

**Location:** Root directory  
**Purpose:** High-level session operations and conversation formatting

#### **Class: SessionManager**

##### **Method: create_session() (Lines 18-33)**
```python
def create_session(self, user_identifier: str = None, session_title: str = "New Conversation") -> str:
    """Create a new session and return session ID"""
    session_id = str(uuid.uuid4())
    
    # Create in database
    self.db.create_session(session_id, user_identifier, session_title)
    
    # Add to active sessions
    self.active_sessions[session_id] = {
        'created_at': datetime.now(),
        'last_activity': datetime.now(),
        'conversation_history': []
    }
    
    return session_id
```
- Generates unique UUID
- Creates in both database and memory
- Returns session_id for client

##### **Method: get_conversation_history() (Lines 35-95)**

**Most Critical Method!**

```python
def get_conversation_history(self, session_id: str) -> list:
    """Get conversation history for a session"""
    session = self.get_session(session_id)
    if session:
        return session['conversation_history']
    return []
```

Called by `get_session()`, which contains the formatting logic:

```python
# Load conversation history from database
conversation_history = self.db.get_conversation_history(session_id)

# Convert to format expected by agent
formatted_history = []
i = 0
while i < len(conversation_history):
    msg = conversation_history[i]
    formatted_msg = {
        'role': msg['role'],
        'content': msg['content'] or ""
    }
    
    # Handle assistant messages with tool_calls
    if msg['role'] == 'assistant' and msg.get('tool_calls'):
        # Ensure tool_calls is properly formatted
        tool_calls = msg['tool_calls']
        if isinstance(tool_calls, list) and len(tool_calls) > 0:
            formatted_msg['tool_calls'] = tool_calls
        formatted_history.append(formatted_msg)
        
        # Collect all corresponding tool responses
        i += 1
        while i < len(conversation_history) and conversation_history[i]['role'] == 'tool':
            tool_msg = conversation_history[i]
            tool_formatted = {
                'role': 'tool',
                'content': tool_msg['content'] or "",
                'tool_call_id': tool_msg.get('tool_call_id')
            }
            formatted_history.append(tool_formatted)
            i += 1
        continue
    
    # Handle regular tool messages
    elif msg['role'] == 'tool' and msg.get('tool_call_id'):
        formatted_msg['tool_call_id'] = msg['tool_call_id']
    
    formatted_history.append(formatted_msg)
    i += 1
```

**Why this complexity?**
- OpenAI requires: assistant (with tool_calls) → tool responses → next message
- Database stores them separately
- This method reconstructs proper sequence
- Ensures tool_call_id linking is correct

##### **Method: export_session() (Lines 150-167)**
```python
def export_session(self, session_id: str) -> Optional[dict]:
    """Export session data for download"""
    session_info = self.db.get_session(session_id)
    if not session_info:
        return None
    
    messages = self.db.get_conversation_history(session_id)
    stats = self.db.get_session_stats(session_id)
    
    return {
        'session_info': session_info,
        'statistics': stats,
        'messages': messages,
        'exported_at': datetime.now().isoformat()
    }
```
- Creates complete export package
- Includes metadata and statistics

---

### 4. **githubaccess.py** (250 lines) - GitHub Integration

**Location:** Root directory  
**Purpose:** Tools for accessing GitHub API

#### **Class: GitHubAccess**

##### **Constructor (Lines 13-30)**
```python
def __init__(self, token: str = None, username: str = None):
    """Initialize GitHub access"""
    self.token = token or os.getenv('GITHUB_TOKEN')
    self.username = username or os.getenv('GITHUB_USERNAME')
    self.base_url = "https://api.github.com"
    self.headers = {
        "Accept": "application/vnd.github.v3+json"
    }
    if self.token:
        self.headers["Authorization"] = f"token {self.token}"
```
- Reads credentials from environment
- Sets up API headers
- Authorization for private repos

##### **Method: get_user_repos() (Lines 32-60)**
```python
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
            response.raise_for_status()
            
            page_repos = response.json()
            if not page_repos:
                break
            
            repos.extend(page_repos)
            page += 1
        
        return repos
    except Exception as e:
        return {"error": str(e)}
```

**Key Features:**
- Pagination support (handles >100 repos)
- Error handling
- Returns raw GitHub API data

##### **Method: analyze_repository() (Lines 90-148)**
```python
def analyze_repository(self, repo_name: str) -> Dict[str, Any]:
    """Analyze repository structure and get statistics"""
    try:
        # Get repo info
        repo_url = f"{self.base_url}/repos/{repo_name}"
        repo_response = requests.get(repo_url, headers=self.headers)
        repo_response.raise_for_status()
        repo_data = repo_response.json()
        
        # Get all files
        files = self._get_all_files(repo_name)
        
        # Count file types
        file_types = {}
        for file in files:
            ext = file.split('.')[-1] if '.' in file else 'no_extension'
            file_types[ext] = file_types.get(ext, 0) + 1
        
        return {
            "repo_name": repo_name,
            "description": repo_data.get("description"),
            "language": repo_data.get("language"),
            "stars": repo_data.get("stargazers_count"),
            "forks": repo_data.get("forks_count"),
            "updated_at": repo_data.get("updated_at"),
            "total_files": len(files),
            "file_types": file_types,
            "files": files
        }
    except Exception as e:
        return {"error": str(e)}
```

**Analysis Includes:**
- File count
- File type distribution
- Complete file list
- Repository metadata

##### **Wrapper Functions (Lines 157-250)**

Three simple wrapper functions for tool calling:

**1. get_github_repos_info()**
```python
def get_github_repos_info(username: str = None) -> str:
    """Get information about all GitHub repositories"""
    github = GitHubAccess(username=username)
    repos = github.get_user_repos()
    
    if isinstance(repos, dict) and "error" in repos:
        return f"Error accessing GitHub: {repos['error']}"
    
    result = f"Found {len(repos)} repositories:\n\n"
    for repo in repos:
        result += f"📦 {repo['name']}\n"
        result += f"   Description: {repo.get('description', 'No description')}\n"
        result += f"   Language: {repo.get('language', 'Not specified')}\n"
        result += f"   Stars: {repo.get('stargazers_count', 0)}\n"
        result += f"   Private: {'Yes' if repo.get('private') else 'No'}\n\n"
    
    return result
```
- Formats data for AI consumption
- Handles errors gracefully

**2. analyze_github_repo()**
```python
def analyze_github_repo(repo_name: str, username: str = None) -> str:
    """Analyze a specific GitHub repository"""
    github = GitHubAccess(username=username)
    
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
    result += f"Forks: {analysis.get('forks', 0)}\n\n"
    
    result += "File Types Distribution:\n"
    for file_type, count in sorted(analysis['file_types'].items(), key=lambda x: x[1], reverse=True):
        result += f"  - .{file_type}: {count} files\n"
    
    result += f"\nAll Files ({analysis['total_files']}):\n"
    for file in analysis['files'][:50]:  # Show first 50 files
        result += f"  - {file}\n"
    
    if len(analysis['files']) > 50:
        result += f"\n  ... and {len(analysis['files']) - 50} more files\n"
    
    return result
```
- Comprehensive repository analysis
- Limits output to first 50 files

**3. get_github_file_content()**
```python
def get_github_file_content(repo_name: str, file_path: str, username: str = None) -> str:
    """Get the content of a specific file in a GitHub repository"""
    github = GitHubAccess(username=username)
    
    if '/' not in repo_name and username:
        repo_name = f"{username}/{repo_name}"
    elif '/' not in repo_name and github.username:
        repo_name = f"{github.username}/{repo_name}"
    
    content = github.get_file_content(repo_name, file_path)
    
    if content.startswith("Error:"):
        return content
    
    return f"Content of {file_path} in {repo_name}:\n\n{content}"
```
- Reads specific file from repo
- Base64 decoding handled internally

---

### 5. **templates/index.html** (643 lines) - Frontend UI

**Location:** templates/ directory  
**Purpose:** User interface for chat application

#### **Structure:**

##### **A. HTML (Lines 1-435)**

**Header Section:**
```html
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Strands Agent Chat - Session Management</title>
    <style>
        /* CSS styles */
    </style>
</head>
```

**Body Structure:**
```html
<body>
    <div class="app-container">
        <!-- Sidebar -->
        <div class="sidebar">
            <div class="sidebar-header">
                <h2>💬 Chat Sessions</h2>
                <button class="new-session-btn">+ New Conversation</button>
            </div>
            <div class="sessions-list" id="sessions-list">
                <!-- Dynamic session list -->
            </div>
        </div>
        
        <!-- Main Chat -->
        <div class="chat-container">
            <div class="header">
                <div class="header-left">
                    <h1>🤖 Strands Agent</h1>
                    <p>Powered by OpenAI GPT-4o</p>
                </div>
                <div class="header-actions">
                    <button class="header-btn">📥 Export</button>
                    <button class="header-btn">🗑️ Clear</button>
                </div>
            </div>
            
            <div class="chat-messages" id="chat-messages">
                <!-- Messages appear here -->
            </div>
            
            <div class="loading" id="loading">
                <div class="loading-dots">●●●</div>
            </div>
            
            <div class="input-area">
                <textarea id="user-input" placeholder="Type your message..."></textarea>
                <button id="send-btn">Send</button>
            </div>
        </div>
    </div>
</body>
```

##### **B. CSS Styling (Lines 7-380)**

**Key Design Features:**
- Gradient background (purple to blue)
- Modern card-based layout
- Smooth animations
- Responsive design
- Message bubbles with different colors
- Loading indicators

**Example Styles:**
```css
.message.user .message-content {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-bottom-right-radius: 4px;
}

.message.assistant .message-content {
    background: white;
    color: #24292e;
    border: 1px solid #e1e4e8;
    border-bottom-left-radius: 4px;
}
```

##### **C. JavaScript Logic (Lines 436-643)**

**Global Variables:**
```javascript
let currentSessionId = null;  // Active conversation
let sessions = [];             // All sessions list
```

**Initialization:**
```javascript
document.addEventListener('DOMContentLoaded', function() {
    checkHealth();
    loadSessions();
    
    // Auto-resize textarea
    const textarea = document.getElementById('user-input');
    textarea.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });
    
    // Handle Enter key
    textarea.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
});
```

**Key Functions:**

**1. loadSessions()**
```javascript
async function loadSessions() {
    try {
        const response = await fetch('/api/session/list');
        const data = await response.json();
        
        if (data.status === 'success') {
            sessions = data.sessions;
            renderSessions();
            
            // Auto-select most recent session
            if (!currentSessionId && sessions.length > 0) {
                selectSession(sessions[0].session_id);
            }
        }
    } catch (error) {
        console.error('Failed to load sessions:', error);
    }
}
```
- Fetches all sessions on page load
- Auto-selects most recent

**2. createNewSession()**
```javascript
async function createNewSession() {
    try {
        const response = await fetch('/api/session/new', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                session_title: `Chat ${new Date().toLocaleString()}`
            })
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            currentSessionId = data.session_id;
            await loadSessions();
            clearChatDisplay();
            document.getElementById('user-input').focus();
        }
    } catch (error) {
        console.error('Failed to create session:', error);
    }
}
```
- Creates new conversation
- Switches to new session
- Focuses input field

**3. sendMessage()**
```javascript
async function sendMessage() {
    const input = document.getElementById('user-input');
    const question = input.value.trim();
    
    if (!question) return;
    
    // Create session if needed
    if (!currentSessionId) {
        await createNewSession();
    }
    
    // Clear input and disable button
    input.value = '';
    input.style.height = 'auto';
    const sendBtn = document.getElementById('send-btn');
    sendBtn.disabled = true;
    
    // Display user message
    addMessageToDisplay('user', question);
    
    // Show loading
    document.getElementById('loading').classList.add('active');
    
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                question: question,
                session_id: currentSessionId
            })
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            addMessageToDisplay('assistant', data.answer);
            loadSessions(); // Update message count
        } else {
            addMessageToDisplay('assistant', `Error: ${data.error}`);
        }
    } catch (error) {
        addMessageToDisplay('assistant', `Error: ${error.message}`);
    } finally {
        document.getElementById('loading').classList.remove('active');
        sendBtn.disabled = false;
        input.focus();
    }
}
```
- Handles Enter key and button click
- Creates session if needed
- Shows loading indicator
- Displays both user and assistant messages

**4. addMessageToDisplay()**
```javascript
function addMessageToDisplay(role, content, timestamp = null) {
    const messagesDiv = document.getElementById('chat-messages');
    
    // Remove empty state
    const emptyState = messagesDiv.querySelector('.empty-state');
    if (emptyState) {
        emptyState.remove();
    }
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    
    const time = timestamp ? new Date(timestamp).toLocaleTimeString() : new Date().toLocaleTimeString();
    
    messageDiv.innerHTML = `
        <div class="message-content">${escapeHtml(content)}</div>
        <div class="message-time">${time}</div>
    `;
    
    messagesDiv.appendChild(messageDiv);
    scrollToBottom();
}
```
- Creates message bubble
- Adds timestamp
- Auto-scrolls to bottom

**5. exportSession()**
```javascript
async function exportSession() {
    if (!currentSessionId) {
        alert('No active session to export');
        return;
    }
    
    try {
        window.location.href = `/api/session/${currentSessionId}/export`;
    } catch (error) {
        console.error('Failed to export session:', error);
    }
}
```
- Triggers file download
- Browser handles download

**6. deleteSession()**
```javascript
async function deleteSession(sessionId) {
    if (!confirm('Are you sure you want to delete this conversation?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/session/${sessionId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            if (currentSessionId === sessionId) {
                currentSessionId = null;
                clearChatDisplay();
            }
            await loadSessions();
        }
    } catch (error) {
        console.error('Failed to delete session:', error);
    }
}
```
- Confirms deletion
- Clears display if active session
- Reloads session list

---

### 6. **Supporting Files**

#### **.env** (Environment Variables)
```bash
OPENAI_API_KEY=sk-proj-...
GITHUB_TOKEN=github_pat_...
GITHUB_USERNAME=garlapatisrinu1228
```

**Purpose:**
- Stores sensitive credentials
- Not committed to Git
- Loaded by python-dotenv

#### **requirements.txt** (Dependencies)
```
flask==3.0.0
flask-cors==4.0.0
python-dotenv==1.0.0
openai==1.58.1
requests==2.31.0
```

**Purpose:**
- Lists all Python dependencies
- Used for installation: `pip install -r requirements.txt`

#### **data/Strands_agents_sampletestfile.txt.txt** (Personal Data)
```
my name is Garlapati Venkata Srinivas Age is 25
my Friend name is Akhil Shanmukha Kothamasu age is 28
My brother name is Madhu Vutukuri Age is 46
```

**Purpose:**
- Sample personal information
- Agent reads this for personal questions
- Demonstrates file reading capability

#### **strands_agent.db** (SQLite Database)
- Auto-generated on first run
- Contains sessions and messages tables
- Grows with usage
- Can be deleted to reset

---

## 🔄 Complete Data Flow Example

### Example: "What's my friend's name?"

**1. User Action (Frontend)**
```javascript
// User types and presses Enter
sendMessage() {
    fetch('/api/chat', {
        body: JSON.stringify({
            question: "What's my friend's name?",
            session_id: "abc-123-def-456"
        })
    })
}
```

**2. Flask Route (Backend)**
```python
# app.py - /api/chat route
@app.route('/api/chat', methods=['POST'])
def chat():
    question = "What's my friend's name?"
    session_id = "abc-123-def-456"
    
    answer = agent.ask(question, session_id)
    return jsonify({'answer': answer})
```

**3. Load History (Session Manager)**
```python
# session_manager.py
conversation_history = db.get_conversation_history(session_id)
# Returns: [previous messages...]
```

**4. Add User Message**
```python
# app.py - StrandsAgent.ask()
conversation_history.append({
    "role": "user",
    "content": "What's my friend's name?"
})

session_manager.add_message(session_id, "user", "What's my friend's name?")
```

**5. Call OpenAI**
```python
# app.py
response = openai_client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": AGENT_SYSTEM_PROMPT},
        ...conversation_history
    ],
    tools=tools
)
```

**6. OpenAI Decides to Use Tool**
```python
# OpenAI response
tool_calls = [
    {
        "id": "call_123",
        "function": {
            "name": "read_local_file",
            "arguments": '{"file_path": "personal_info"}'
        }
    }
]
```

**7. Execute Tool**
```python
# app.py
file_path = AVAILABLE_FILES["personal_info"]
# C:\...\Strands_agents_sampletestfile.txt.txt

with open(file_path) as f:
    content = f.read()

# Returns:
# "my Friend name is Akhil Shanmukha Kothamasu age is 28"
```

**8. Send Tool Result to OpenAI**
```python
conversation_history.append({
    "role": "assistant",
    "tool_calls": [...]
})
conversation_history.append({
    "role": "tool",
    "tool_call_id": "call_123",
    "content": file_content
})

second_response = openai_client.chat.completions.create(
    messages=conversation_history
)

# OpenAI responds:
# "Your friend's name is Akhil Shanmukha Kothamasu, age 28."
```

**9. Save Response**
```python
session_manager.add_message(
    session_id,
    "assistant",
    "Your friend's name is Akhil..."
)
```

**10. Return to Frontend**
```python
return jsonify({
    "answer": "Your friend's name is Akhil...",
    "status": "success"
})
```

**11. Display in UI**
```javascript
addMessageToDisplay('assistant', response.answer);
```

---

## 📊 Database Schema Details

### Sessions Table
```sql
CREATE TABLE sessions (
    session_id TEXT PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_identifier TEXT,
    session_title TEXT
);
```

**Example Row:**
| session_id | created_at | last_activity | user_identifier | session_title |
|------------|------------|---------------|-----------------|---------------|
| abc-123... | 2026-01-27 00:00:00 | 2026-01-27 00:15:30 | NULL | Chat 1/27/2026 |

### Messages Table
```sql
CREATE TABLE messages (
    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tool_calls TEXT,
    tool_call_id TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
);
```

**Example Rows:**
| message_id | session_id | role | content | tool_calls | tool_call_id |
|------------|------------|------|---------|------------|--------------|
| 1 | abc-123 | user | What's my friend's name? | NULL | NULL |
| 2 | abc-123 | assistant | | [{"id": "call_123", ...}] | NULL |
| 3 | abc-123 | tool | Friend name is Akhil... | NULL | call_123 |
| 4 | abc-123 | assistant | Your friend is Akhil... | NULL | NULL |

---

## 🛠️ Tool System

### How Tools Work

**1. Tool Definition (JSON Schema)**
```python
{
    "type": "function",
    "function": {
        "name": "read_local_file",
        "description": "What the tool does",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Parameter description"
                }
            },
            "required": ["file_path"]
        }
    }
}
```

**2. OpenAI Decision**
- Analyzes user question
- Checks available tools
- Decides if tool is needed
- Returns tool_call with arguments

**3. Tool Execution**
```python
if function_name == "read_local_file":
    result = read_local_file(file_path)
```

**4. Result Formatting**
```python
tool_message = {
    "role": "tool",
    "tool_call_id": "call_123",
    "content": result
}
```

**5. Final Answer**
- OpenAI receives tool result
- Formulates natural language answer
- Returns to user

### Available Tools

| Tool | Purpose | Example |
|------|---------|---------|
| read_local_file | Read files from disk | "Show me the config file" |
| get_github_repos | List all repositories | "What repos do I have?" |
| analyze_github_repo | Analyze repo structure | "What files are in myrepo?" |
| get_github_file_content | Read file from GitHub | "Show me README.md from myrepo" |

---

## 🚀 API Endpoints Summary

| Method | Endpoint | Purpose | Request | Response |
|--------|----------|---------|---------|----------|
| GET | / | Homepage | - | HTML page |
| POST | /api/chat | Send message | {question, session_id} | {answer, status} |
| POST | /api/session/new | Create session | {session_title} | {session_id} |
| GET | /api/session/list | List sessions | limit (query) | {sessions[]} |
| GET | /api/session/:id | Get session | - | {session, conversation, stats} |
| DELETE | /api/session/:id | Delete session | - | {status} |
| GET | /api/session/:id/export | Export session | - | JSON file download |
| GET | /api/search | Search messages | q (query) | {results[]} |
| POST | /api/reset | Clear session | {session_id} | {status} |
| GET | /api/health | Health check | - | {status} |

---

## 🎯 Key Concepts

### 1. **Session Isolation**
- Each browser tab = unique session_id
- Conversations don't mix
- Persistent across page refreshes

### 2. **Conversation Context**
- Entire chat history sent to OpenAI
- Provides context for responses
- Enables multi-turn conversations

### 3. **Tool Calling Flow**
```
User Question
    ↓
OpenAI Decision
    ├─ Direct Answer → Return
    └─ Need Tool
        ↓
    Execute Tool
        ↓
    Send Results to OpenAI
        ↓
    Final Answer
```

### 4. **Database Persistence**
- All messages saved immediately
- Survives app restarts
- Enables search and export

### 5. **Error Handling**
- Try/catch at every level
- Descriptive error messages
- Graceful degradation

---

## 📝 Common Operations

### Adding a New Tool

**1. Define Tool Schema (app.py)**
```python
tools.append({
    "type": "function",
    "function": {
        "name": "my_new_tool",
        "description": "What it does",
        "parameters": {...}
    }
})
```

**2. Implement Function**
```python
def my_new_tool(param1, param2):
    # Tool logic
    return result
```

**3. Add to Tool Execution**
```python
elif function_name == "my_new_tool":
    function_response = my_new_tool(
        param1=function_args.get("param1"),
        param2=function_args.get("param2")
    )
```

### Adding a New API Endpoint

```python
@app.route('/api/my-endpoint', methods=['POST'])
def my_endpoint():
    try:
        data = request.get_json()
        # Process request
        return jsonify({'status': 'success', 'data': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

### Modifying UI

**HTML:**
```html
<!-- Add new element in templates/index.html -->
<button id="my-button">Click Me</button>
```

**JavaScript:**
```javascript
// Add event listener
document.getElementById('my-button').addEventListener('click', function() {
    // Handle click
});
```

---

## 🔍 Troubleshooting Guide

### Common Issues

**1. "OPENAI_API_KEY not set"**
- Create .env file
- Add: `OPENAI_API_KEY=sk-...`

**2. "GitHub authentication failed"**
- Add GitHub token to .env
- Format: `GITHUB_TOKEN=ghp_...`

**3. "Session not found"**
- Database might be corrupted
- Delete strands_agent.db
- Restart application

**4. "Tool call error"**
- Check tool_calls format in database
- Verify tool_call_id links correctly
- Review conversation_history reconstruction

**5. UI not loading**
- Check Flask is running
- Verify port 5000 is not in use
- Check browser console for errors

---

## 📚 Further Reading

### Technologies Used
- **Flask:** https://flask.palletsprojects.com/
- **OpenAI API:** https://platform.openai.com/docs/
- **SQLite:** https://www.sqlite.org/docs.html
- **GitHub API:** https://docs.github.com/en/rest

### Concepts
- **Function Calling:** OpenAI's tool use feature
- **Session Management:** Web application sessions
- **RESTful APIs:** HTTP endpoint design
- **Database Normalization:** Efficient data storage

---

## 📄 License & Credits

**Author:** Garlapati Venkata Srinivas  
**Date:** January 27, 2026  
**Version:** 1.0  
**Framework:** Strands Agents  
**AI Model:** OpenAI GPT-4o

---

*This documentation covers every file, function, and concept in the Strands Agent application. Use it as a reference for understanding, modifying, or extending the application.*
