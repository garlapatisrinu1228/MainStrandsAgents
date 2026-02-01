"""
Session Manager for handling user sessions
"""
import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, Optional


class SessionManager:
    """Manage user sessions and their lifecycle"""
    
    def __init__(self, db):
        """Initialize session manager with storage backend (S3Storage or Database)"""
        self.db = db
        self.active_sessions: Dict[str, dict] = {}
    
    def create_session(self, user_identifier: str = None, session_title: str = "New Conversation") -> str:
        """
        Create a new session and return session ID
        """
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
    
    def get_session(self, session_id: str) -> Optional[dict]:
        """
        Get session data
        Returns session info or None if not found
        """
        # Check if session exists in database
        session_info = self.db.get_session(session_id)
        
        if not session_info:
            return None
        
        # Load from active sessions or create new entry
        if session_id not in self.active_sessions:
            # Load conversation history from database
            conversation_history = self.db.get_conversation_history(session_id)
            
            # Convert to format expected by agent
            formatted_history = []
            print(f"📥 Processing {len(conversation_history)} raw messages from database")
            i = 0
            while i < len(conversation_history):
                msg = conversation_history[i]
                
                # Parse tool_calls if it's a JSON string
                tool_calls = msg.get('tool_calls')
                if tool_calls and isinstance(tool_calls, str):
                    try:
                        tool_calls = json.loads(tool_calls)
                    except json.JSONDecodeError:
                        print(f"⚠️ Failed to parse tool_calls JSON at position {i}: {tool_calls}")
                        tool_calls = None
                
                print(f"  Position {i}: role={msg['role']}, has_tool_calls={bool(tool_calls)}, tool_call_id={msg.get('tool_call_id')}")
                
                formatted_msg = {
                    'role': msg['role'],
                    'content': msg['content'] or ""
                }
                
                # Handle assistant messages with tool_calls
                if msg['role'] == 'assistant' and tool_calls:
                    # Ensure tool_calls is properly formatted
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
                    else:
                        # Assistant message with empty or invalid tool_calls - treat as regular message
                        print(f"⚠️ Assistant message at position {i} has invalid tool_calls: {tool_calls}")
                        formatted_history.append(formatted_msg)
                        i += 1
                        continue
                
                # Skip orphaned tool messages (without preceding assistant message with tool_calls)
                elif msg['role'] == 'tool':
                    print(f"⚠️ Skipping orphaned tool message at position {i}: tool_call_id={msg.get('tool_call_id')}")
                    i += 1
                    continue
                
                formatted_history.append(formatted_msg)
                i += 1
            
            print(f"📝 Loaded {len(formatted_history)} messages for session (filtered from {len(conversation_history)} raw messages)")
            
            self.active_sessions[session_id] = {
                'created_at': datetime.fromisoformat(session_info['created_at']),
                'last_activity': datetime.fromisoformat(session_info['last_activity']),
                'conversation_history': formatted_history
            }
        
        return self.active_sessions[session_id]
    
    def update_activity(self, session_id: str):
        """Update session last activity timestamp"""
        if session_id in self.active_sessions:
            self.active_sessions[session_id]['last_activity'] = datetime.now()
            self.db.update_session_activity(session_id)
    
    def add_message(self, session_id: str, role: str, content: str, tool_calls=None, tool_call_id=None, redacted_content=None):
        """Add a message to session history"""
        # Add to active session
        if session_id in self.active_sessions:
            message = {'role': role, 'content': content}
            if tool_calls:
                message['tool_calls'] = tool_calls
            if tool_call_id:
                message['tool_call_id'] = tool_call_id
            
            self.active_sessions[session_id]['conversation_history'].append(message)
            self.update_activity(session_id)
        
        # Save to database
        import json
        tool_calls_json = json.dumps(tool_calls) if tool_calls else None
        self.db.add_message(session_id, role, content, tool_calls_json, tool_call_id, redacted_content)
    
    def get_conversation_history(self, session_id: str) -> list:
        """Get conversation history for a session"""
        session = self.get_session(session_id)
        if session:
            return session['conversation_history']
        return []
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        # Remove from active sessions
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
        
        # Delete from database
        return self.db.delete_session(session_id)
    
    def clear_session_cache(self, session_id=None):
        """Clear session cache to force reload from database"""
        if session_id:
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
                print(f"🔄 Cleared cache for session {session_id}")
                return True
            return False
        else:
            # Clear all sessions
            count = len(self.active_sessions)
            self.active_sessions.clear()
            print(f"🔄 Cleared cache for {count} sessions")
            return True
    
    def list_sessions(self, limit: int = 50) -> list:
        """List all sessions"""
        return self.db.list_sessions(limit)
    
    def cleanup_old_sessions(self, days: int = 30) -> int:
        """
        Clean up sessions older than specified days
        Returns number of sessions deleted
        """
        deleted_count = self.db.cleanup_old_sessions(days)
        
        # Clean from active sessions too
        cutoff_time = datetime.now() - timedelta(days=days)
        to_remove = [
            sid for sid, data in self.active_sessions.items()
            if data['last_activity'] < cutoff_time
        ]
        
        for sid in to_remove:
            del self.active_sessions[sid]
        
        return deleted_count
    
    def session_exists(self, session_id: str) -> bool:
        """Check if a session exists"""
        return self.db.session_exists(session_id)
    
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
