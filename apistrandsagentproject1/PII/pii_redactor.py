"""
PII Redaction Engine
Detects and redacts personally identifiable information
"""
import re
import json
from typing import Dict, List, Tuple
from PII.pii_patterns import PII_PATTERNS, KNOWN_NAMES


class PIIRedactor:
    """Redact and restore PII in text"""
    
    def __init__(self):
        self.redaction_map = {}  # {session_id: {token: original_value}}
        self.token_counters = {}  # {session_id: {pii_type: counter}}
    
    def redact(self, text: str, session_id: str) -> Tuple[str, Dict]:
        """
        Redact PII from text
        Returns: (redacted_text, redaction_metadata)
        """
        if not text:
            return text, {}
        
        redacted_text = text
        redactions = {}
        
        # Initialize session maps
        if session_id not in self.redaction_map:
            self.redaction_map[session_id] = {}
            self.token_counters[session_id] = {}
        
        # First: Redact known names (specific to your data)
        for name in KNOWN_NAMES:
            if name in redacted_text:
                token = self._get_or_create_token(session_id, 'PERSON', name)
                redacted_text = redacted_text.replace(name, f"[{token}]")
                redactions[token] = {
                    'type': 'PERSON',
                    'original': name,
                    'description': 'Known person name'
                }
        
        # Then: Redact other PII patterns
        for pii_type, config in PII_PATTERNS.items():
            pattern = config['pattern']
            label = config['label']
            
            matches = re.finditer(pattern, redacted_text)
            for match in matches:
                original_value = match.group(0)
                
                # Skip if already redacted
                if original_value.startswith('[') and original_value.endswith(']'):
                    continue
                
                # Create or get existing token
                token = self._get_or_create_token(session_id, label, original_value)
                
                # Replace in text
                redacted_text = redacted_text.replace(original_value, f"[{token}]")
                
                # Store metadata
                redactions[token] = {
                    'type': label,
                    'original': original_value,
                    'description': config['description']
                }
        
        return redacted_text, redactions
    
    def restore(self, text: str, session_id: str) -> str:
        """
        Restore original PII from redacted text
        """
        if not text or session_id not in self.redaction_map:
            return text
        
        restored_text = text
        session_map = self.redaction_map[session_id]
        
        # Replace all tokens with original values
        for token, original_value in session_map.items():
            restored_text = restored_text.replace(f"[{token}]", original_value)
        
        return restored_text
    
    def _get_or_create_token(self, session_id: str, pii_type: str, original_value: str) -> str:
        """
        Get existing token or create new one for PII value
        """
        session_map = self.redaction_map[session_id]
        
        # Check if this value already has a token
        for token, value in session_map.items():
            if value == original_value:
                return token
        
        # Create new token
        if pii_type not in self.token_counters[session_id]:
            self.token_counters[session_id][pii_type] = 0
        
        self.token_counters[session_id][pii_type] += 1
        counter = self.token_counters[session_id][pii_type]
        token = f"{pii_type}_{counter}"
        
        # Store mapping
        session_map[token] = original_value
        
        return token
    
    def get_redaction_stats(self, session_id: str) -> Dict:
        """Get statistics about redactions for a session"""
        if session_id not in self.redaction_map:
            return {'total_redactions': 0, 'by_type': {}}
        
        session_map = self.redaction_map[session_id]
        by_type = {}
        
        for token in session_map.keys():
            pii_type = token.rsplit('_', 1)[0]
            by_type[pii_type] = by_type.get(pii_type, 0) + 1
        
        return {
            'total_redactions': len(session_map),
            'by_type': by_type
        }
    
    def clear_session(self, session_id: str):
        """Clear redaction data for a session"""
        if session_id in self.redaction_map:
            del self.redaction_map[session_id]
        if session_id in self.token_counters:
            del self.token_counters[session_id]
    
    def export_redaction_map(self, session_id: str) -> Dict:
        """Export redaction map for a session"""
        if session_id not in self.redaction_map:
            return {}
        
        return {
            'session_id': session_id,
            'redaction_map': self.redaction_map[session_id],
            'stats': self.get_redaction_stats(session_id)
        }
