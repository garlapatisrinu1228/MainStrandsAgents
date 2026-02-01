"""
Amazon S3 Storage Backend for Strands Agent
Replaces SQLite database with S3 JSON storage
"""
import boto3
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from botocore.exceptions import ClientError


class S3Storage:
    """S3-based storage for sessions and conversations"""
    
    def __init__(self, bucket_name: str = None):
        """Initialize S3 client and bucket"""
        self.s3_client = boto3.client('s3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        self.bucket_name = bucket_name or os.getenv('S3_BUCKET_NAME')
        
        if not self.bucket_name:
            raise ValueError("S3_BUCKET_NAME must be set in environment variables")
        
        # Ensure bucket exists
        self._ensure_bucket_exists()
        
        print(f"✅ S3 Storage initialized: {self.bucket_name}")
    
    def _ensure_bucket_exists(self):
        """Create bucket if it doesn't exist"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                # Bucket doesn't exist, create it
                try:
                    region = os.getenv('AWS_REGION', 'us-east-1')
                    if region == 'us-east-1':
                        self.s3_client.create_bucket(Bucket=self.bucket_name)
                    else:
                        self.s3_client.create_bucket(
                            Bucket=self.bucket_name,
                            CreateBucketConfiguration={'LocationConstraint': region}
                        )
                    print(f"✅ Created S3 bucket: {self.bucket_name}")
                except ClientError as create_error:
                    print(f"⚠️ Could not create bucket: {create_error}")
            else:
                raise
    
    def _s3_get(self, key: str) -> Optional[Dict]:
        """Get JSON object from S3"""
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
            data = json.loads(response['Body'].read().decode('utf-8'))
            return data
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                return None
            raise
    
    def _s3_put(self, key: str, data: Dict):
        """Put JSON object to S3"""
        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=json.dumps(data, indent=2),
            ContentType='application/json'
        )
    
    def _s3_delete(self, key: str):
        """Delete object from S3"""
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
        except ClientError:
            pass
    
    def _s3_list(self, prefix: str) -> List[str]:
        """List all keys with given prefix"""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            if 'Contents' in response:
                return [obj['Key'] for obj in response['Contents']]
            return []
        except ClientError:
            return []
    
    # ==================== SESSION METHODS ====================
    
    def create_session(self, session_id: str, user_identifier: str = None, 
                      session_title: str = "New Conversation") -> bool:
        """Create a new session in S3"""
        try:
            session_data = {
                'session_id': session_id,
                'user_identifier': user_identifier,
                'session_title': session_title,
                'created_at': datetime.utcnow().isoformat(),
                'last_activity': datetime.utcnow().isoformat(),
                'pii_redaction_enabled': 1,
                'message_count': 0
            }
            
            # Store session metadata
            self._s3_put(f"sessions/{session_id}.json", session_data)
            
            # Initialize empty conversation
            self._s3_put(f"conversations/{session_id}/messages.json", {
                'session_id': session_id,
                'messages': []
            })
            
            return True
        except Exception as e:
            print(f"Error creating session: {e}")
            return False
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session metadata"""
        return self._s3_get(f"sessions/{session_id}.json")
    
    def session_exists(self, session_id: str) -> bool:
        """Check if session exists"""
        return self.get_session(session_id) is not None
    
    def update_session_activity(self, session_id: str):
        """Update session last activity timestamp"""
        session = self.get_session(session_id)
        if session:
            session['last_activity'] = datetime.utcnow().isoformat()
            self._s3_put(f"sessions/{session_id}.json", session)
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session and all its messages"""
        try:
            # Delete session metadata
            self._s3_delete(f"sessions/{session_id}.json")
            
            # Delete conversation messages
            self._s3_delete(f"conversations/{session_id}/messages.json")
            
            return True
        except Exception as e:
            print(f"Error deleting session: {e}")
            return False
    
    def list_sessions(self, limit: int = 50) -> List[Dict]:
        """List all sessions, sorted by last activity"""
        try:
            session_keys = self._s3_list("sessions/")
            sessions = []
            
            for key in session_keys:
                session = self._s3_get(key)
                if session:
                    sessions.append(session)
            
            # Sort by last_activity (most recent first)
            sessions.sort(key=lambda x: x.get('last_activity', ''), reverse=True)
            
            return sessions[:limit]
        except Exception as e:
            print(f"Error listing sessions: {e}")
            return []
    
    def get_session_stats(self, session_id: str) -> Dict:
        """Get statistics for a session"""
        messages_data = self._s3_get(f"conversations/{session_id}/messages.json")
        
        if not messages_data:
            return {
                'total_messages': 0,
                'user_messages': 0,
                'assistant_messages': 0
            }
        
        messages = messages_data.get('messages', [])
        
        return {
            'total_messages': len(messages),
            'user_messages': sum(1 for m in messages if m.get('role') == 'user'),
            'assistant_messages': sum(1 for m in messages if m.get('role') == 'assistant')
        }
    
    # ==================== MESSAGE METHODS ====================
    
    def add_message(self, session_id: str, role: str, content: str, 
                   tool_calls_json: str = None, tool_call_id: str = None,
                   redacted_content: str = None):
        """Add a message to conversation"""
        try:
            # Get existing messages
            messages_data = self._s3_get(f"conversations/{session_id}/messages.json")
            
            if not messages_data:
                messages_data = {'session_id': session_id, 'messages': []}
            
            # Create new message
            message = {
                'message_id': len(messages_data['messages']) + 1,
                'role': role,
                'content': content,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            if tool_calls_json:
                message['tool_calls'] = tool_calls_json
            
            if tool_call_id:
                message['tool_call_id'] = tool_call_id
            
            if redacted_content:
                message['redacted_content'] = redacted_content
            
            # Add message
            messages_data['messages'].append(message)
            
            # Save back to S3
            self._s3_put(f"conversations/{session_id}/messages.json", messages_data)
            
            # Update session activity and message count
            session = self.get_session(session_id)
            if session:
                session['last_activity'] = datetime.utcnow().isoformat()
                session['message_count'] = len(messages_data['messages'])
                self._s3_put(f"sessions/{session_id}.json", session)
            
        except Exception as e:
            print(f"Error adding message: {e}")
    
    def get_conversation_history(self, session_id: str) -> List[Dict]:
        """Get all messages for a session"""
        messages_data = self._s3_get(f"conversations/{session_id}/messages.json")
        
        if not messages_data:
            return []
        
        return messages_data.get('messages', [])
    
    def search_messages(self, query: str, limit: int = 50) -> List[Dict]:
        """Search messages across all sessions"""
        try:
            results = []
            conversation_keys = self._s3_list("conversations/")
            
            for key in conversation_keys:
                if not key.endswith('/messages.json'):
                    continue
                
                messages_data = self._s3_get(key)
                if not messages_data:
                    continue
                
                session_id = messages_data.get('session_id')
                
                for msg in messages_data.get('messages', []):
                    if query.lower() in msg.get('content', '').lower():
                        results.append({
                            'session_id': session_id,
                            'message_id': msg.get('message_id'),
                            'role': msg.get('role'),
                            'content': msg.get('content'),
                            'timestamp': msg.get('timestamp')
                        })
                        
                        if len(results) >= limit:
                            return results
            
            return results
        except Exception as e:
            print(f"Error searching messages: {e}")
            return []
    
    # ==================== CLEANUP METHODS ====================
    
    def cleanup_old_sessions(self, days: int = 30):
        """Delete sessions older than specified days"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            sessions = self.list_sessions(limit=1000)
            
            deleted_count = 0
            for session in sessions:
                last_activity = datetime.fromisoformat(session.get('last_activity', ''))
                
                if last_activity < cutoff_date:
                    self.delete_session(session['session_id'])
                    deleted_count += 1
            
            if deleted_count > 0:
                print(f"🧹 Cleaned up {deleted_count} old sessions")
        except Exception as e:
            print(f"Error cleaning up sessions: {e}")
    
    def get_storage_stats(self) -> Dict:
        """Get overall storage statistics"""
        try:
            sessions = self.list_sessions(limit=1000)
            total_messages = sum(s.get('message_count', 0) for s in sessions)
            
            return {
                'total_sessions': len(sessions),
                'total_messages': total_messages,
                'storage_backend': 'Amazon S3',
                'bucket_name': self.bucket_name,
                'region': os.getenv('AWS_REGION', 'us-east-1')
            }
        except Exception as e:
            print(f"Error getting storage stats: {e}")
            return {}


# ==================== MIGRATION UTILITY ====================

def migrate_sqlite_to_s3(sqlite_db_path: str, s3_storage: S3Storage):
    """Migrate data from SQLite to S3"""
    import sqlite3
    
    print("🔄 Starting migration from SQLite to S3...")
    
    try:
        conn = sqlite3.connect(sqlite_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Migrate sessions
        cursor.execute('SELECT * FROM sessions')
        sessions = cursor.fetchall()
        
        for session in sessions:
            session_dict = dict(session)
            s3_storage.create_session(
                session_id=session_dict['session_id'],
                user_identifier=session_dict.get('user_identifier'),
                session_title=session_dict.get('session_title', 'New Conversation')
            )
            
            # Update timestamps
            session_data = s3_storage.get_session(session_dict['session_id'])
            session_data['created_at'] = session_dict['created_at']
            session_data['last_activity'] = session_dict['last_activity']
            s3_storage._s3_put(f"sessions/{session_dict['session_id']}.json", session_data)
        
        print(f"✅ Migrated {len(sessions)} sessions")
        
        # Migrate messages
        cursor.execute('SELECT * FROM messages ORDER BY timestamp')
        messages = cursor.fetchall()
        
        for msg in messages:
            msg_dict = dict(msg)
            s3_storage.add_message(
                session_id=msg_dict['session_id'],
                role=msg_dict['role'],
                content=msg_dict['content'],
                tool_calls_json=msg_dict.get('tool_calls'),
                tool_call_id=msg_dict.get('tool_call_id'),
                redacted_content=msg_dict.get('redacted_content')
            )
        
        print(f"✅ Migrated {len(messages)} messages")
        
        conn.close()
        print("✅ Migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise
