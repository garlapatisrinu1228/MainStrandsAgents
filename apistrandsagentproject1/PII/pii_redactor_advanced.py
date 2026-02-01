"""
Advanced PII Redaction Engine using LLM Guard (Strands-recommended approach)
Provides enterprise-grade PII detection with BERT-based NER
"""
from typing import Dict, Tuple, Optional
try:
    from llm_guard.vault import Vault
    from llm_guard.input_scanners import Anonymize
    from llm_guard.input_scanners.anonymize_helpers import BERT_LARGE_NER_CONF
    LLM_GUARD_AVAILABLE = True
except ImportError:
    LLM_GUARD_AVAILABLE = False
    print("⚠️ LLM Guard not installed. Install with: pip install llm-guard")
    print("⚠️ Falling back to regex-based PII redaction")


class AdvancedPIIRedactor:
    """
    Advanced PII Redaction using LLM Guard with BERT NER
    Follows Strands Agents recommended implementation
    """
    
    def __init__(self, use_llm_guard: bool = True):
        """
        Initialize PII redactor
        
        Args:
            use_llm_guard: If True and available, use LLM Guard. Otherwise use regex fallback.
        """
        self.use_llm_guard = use_llm_guard and LLM_GUARD_AVAILABLE
        
        if self.use_llm_guard:
            # Initialize LLM Guard Vault for storing/restoring original values
            self.vault = Vault()
            print("✅ Advanced PII Redaction initialized (LLM Guard + BERT NER)")
        else:
            # Fallback to regex-based redaction
            from PII.pii_redactor import PIIRedactor
            self.fallback_redactor = PIIRedactor()
            print("⚠️ Using regex-based PII redaction (fallback mode)")
    
    def _create_scanner(self) -> 'Anonymize':
        """Create anonymize scanner with BERT NER configuration"""
        return Anonymize(
            vault=self.vault,
            recognizer_conf=BERT_LARGE_NER_CONF,
            language="en"
        )
    
    def redact(self, text: str, session_id: str) -> Tuple[str, Dict]:
        """
        Redact PII from text using LLM Guard or fallback to regex
        
        Args:
            text: Text to redact
            session_id: Session identifier for tracking
            
        Returns:
            Tuple of (redacted_text, metadata)
        """
        if not text:
            return text, {}
        
        if self.use_llm_guard:
            try:
                scanner = self._create_scanner()
                
                # Scan and redact PII
                sanitized_text, is_valid, risk_score = scanner.scan(text)
                
                # Build metadata
                metadata = {
                    'method': 'llm_guard_bert_ner',
                    'is_valid': is_valid,
                    'risk_score': risk_score,
                    'original_length': len(text),
                    'redacted_length': len(sanitized_text),
                    'session_id': session_id
                }
                
                # Count redacted entities
                redactions_count = text.count('[') - sanitized_text.count('[')
                metadata['redactions_count'] = max(0, redactions_count)
                
                return sanitized_text, metadata
                
            except Exception as e:
                print(f"⚠️ LLM Guard redaction failed: {e}, falling back to regex")
                return self.fallback_redactor.redact(text, session_id)
        else:
            # Use regex fallback
            return self.fallback_redactor.redact(text, session_id)
    
    def restore(self, text: str, session_id: str) -> str:
        """
        Restore original PII from redacted text
        Note: LLM Guard Vault automatically handles restoration
        
        Args:
            text: Redacted text
            session_id: Session identifier
            
        Returns:
            Original text with PII restored
        """
        if self.use_llm_guard:
            # LLM Guard vault can restore if needed
            # For now, return as-is since we want to keep storage redacted
            return text
        else:
            return self.fallback_redactor.restore(text, session_id)
    
    def get_redaction_stats(self, session_id: str) -> Dict:
        """
        Get statistics about redactions for a session
        
        Args:
            session_id: Session identifier
            
        Returns:
            Dictionary with redaction statistics
        """
        if self.use_llm_guard:
            return {
                'method': 'llm_guard_bert_ner',
                'vault_size': len(self.vault),
                'session_id': session_id
            }
        else:
            return self.fallback_redactor.get_redaction_stats(session_id)
    
    def export_redaction_map(self, session_id: str) -> Dict:
        """
        Export redaction mapping for auditing
        
        Args:
            session_id: Session identifier
            
        Returns:
            Dictionary with redaction mappings
        """
        if self.use_llm_guard:
            return {
                'method': 'llm_guard_bert_ner',
                'note': 'LLM Guard uses Vault for secure storage',
                'session_id': session_id
            }
        else:
            return self.fallback_redactor.export_redaction_map(session_id)
    
    def clear_session(self, session_id: str):
        """
        Clear session data
        
        Args:
            session_id: Session identifier to clear
        """
        if not self.use_llm_guard:
            self.fallback_redactor.clear_session(session_id)


def masking_function(data, **kwargs):
    """
    Strands-recommended masking function
    Can be used with observability platforms like Langfuse
    
    Args:
        data: Data to mask (string, dict, or list)
        **kwargs: Additional arguments
        
    Returns:
        Masked data
    """
    if isinstance(data, str):
        redactor = AdvancedPIIRedactor(use_llm_guard=True)
        sanitized_data, _ = redactor.redact(data, session_id=kwargs.get('session_id', 'default'))
        return sanitized_data
    elif isinstance(data, dict):
        return {k: masking_function(v, **kwargs) for k, v in data.items()}
    elif isinstance(data, list):
        return [masking_function(item, **kwargs) for item in data]
    return data
