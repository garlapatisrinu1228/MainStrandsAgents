"""
PII Detection Patterns
Regex patterns for identifying different types of PII
"""
import re

# Comprehensive PII patterns
PII_PATTERNS = {
    'email': {
        'pattern': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        'label': 'EMAIL',
        'description': 'Email address'
    },
    'phone': {
        'pattern': r'\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b',
        'label': 'PHONE',
        'description': 'Phone number'
    },
    'ssn': {
        'pattern': r'\b\d{3}-\d{2}-\d{4}\b',
        'label': 'SSN',
        'description': 'Social Security Number'
    },
    'credit_card': {
        'pattern': r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
        'label': 'CREDIT_CARD',
        'description': 'Credit card number'
    },
    'ip_address': {
        'pattern': r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
        'label': 'IP_ADDRESS',
        'description': 'IP address'
    },
    'date_of_birth': {
        'pattern': r'\b(?:0[1-9]|1[0-2])[/-](?:0[1-9]|[12][0-9]|3[01])[/-](?:19|20)\d{2}\b',
        'label': 'DOB',
        'description': 'Date of birth'
    },
    'name': {
        # Common Indian and Western names pattern
        'pattern': r'\b(?:[A-Z][a-z]+ ){1,2}[A-Z][a-z]+\b',
        'label': 'PERSON',
        'description': 'Person name'
    },
    'address': {
        'pattern': r'\b\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr)\b',
        'label': 'ADDRESS',
        'description': 'Physical address'
    }
}

# Specific names from your data file
KNOWN_NAMES = [
    "Garlapati Venkata Srinivas",
    "Akhil Shanmukha Kothamasu", 
    "Madhu Vutukuri",
    "Srinivas",
    "Akhil",
    "Madhu"
]
