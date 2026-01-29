"""
Chat Storage - JSON-based session persistence per user
"""
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
import uuid


class ChatStorage:
    def __init__(self, storage_file="documents/json/chat_sessions.json"):
        self.storage_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            storage_file
        )
        self._ensure_file_exists()
    
    def _ensure_file_exists(self):
        """Create storage file if it doesn't exist"""
        if not os.path.exists(self.storage_file):
            with open(self.storage_file, 'w') as f:
                json.dump({}, f)
    
    def _load_data(self) -> Dict:
        """Load all data from storage file"""
        try:
            with open(self.storage_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    
    def _save_data(self, data: Dict):
        """Save all data to storage file"""
        with open(self.storage_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def get_user_sessions(self, user_email: str) -> List[Dict]:
        """Get all sessions for a user"""
        data = self._load_data()
        user_data = data.get(user_email, {})
        
        # Convert to list format
        sessions = []
        for session_id, session_data in user_data.items():
            sessions.append({
                'id': session_id,
                'created_at': session_data.get('created_at'),
                'updated_at': session_data.get('updated_at'),
                'model': session_data.get('model'),
                'messages': session_data.get('messages', [])
            })
        
        # Sort by updated_at descending
        sessions.sort(key=lambda x: x.get('updated_at', x.get('created_at', '')), reverse=True)
        return sessions
    
    def get_session(self, user_email: str, session_id: str) -> Optional[Dict]:
        """Get a specific session"""
        data = self._load_data()
        user_data = data.get(user_email, {})
        session_data = user_data.get(session_id)
        
        if session_data:
            return {
                'id': session_id,
                'created_at': session_data.get('created_at'),
                'updated_at': session_data.get('updated_at'),
                'model': session_data.get('model'),
                'messages': session_data.get('messages', [])
            }
        return None
    
    def get_session_messages(self, user_email: str, session_id: str) -> List[Dict]:
        """Get messages for a session"""
        session = self.get_session(user_email, session_id)
        return session['messages'] if session else []
    
    def create_session(self, user_email: str, model: str = 'gemini-2.0-flash-exp') -> Dict:
        """Create a new chat session"""
        data = self._load_data()
        
        if user_email not in data:
            data[user_email] = {}
        
        session_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat() + 'Z'
        
        data[user_email][session_id] = {
            'created_at': now,
            'updated_at': now,
            'model': model,
            'messages': []
        }
        
        self._save_data(data)
        
        return {
            'id': session_id,
            'created_at': now,
            'updated_at': now,
            'model': model,
            'messages': []
        }
    
    def save_message(self, user_email: str, session_id: str, role: str, content: str) -> bool:
        """Add a message to a session"""
        data = self._load_data()
        
        if user_email not in data or session_id not in data[user_email]:
            return False
        
        now = datetime.utcnow().isoformat() + 'Z'
        message = {
            'role': role,
            'content': content,
            'timestamp': now
        }
        
        data[user_email][session_id]['messages'].append(message)
        data[user_email][session_id]['updated_at'] = now
        
        self._save_data(data)
        return True
    
    def delete_session(self, user_email: str, session_id: str) -> bool:
        """Delete a session"""
        data = self._load_data()
        
        if user_email in data and session_id in data[user_email]:
            del data[user_email][session_id]
            self._save_data(data)
            return True
        
        return False


# Singleton instance
_chat_storage = None

def get_chat_storage() -> ChatStorage:
    """Get or create the singleton ChatStorage instance"""
    global _chat_storage
    if _chat_storage is None:
        _chat_storage = ChatStorage()
    return _chat_storage
