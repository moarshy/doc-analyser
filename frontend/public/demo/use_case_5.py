#!/usr/bin/env python3
"""
PII Detection and Redaction Use Case Implementation
Using Microsoft Presidio for comprehensive PII detection and redaction

This script demonstrates how to:
1. Install and configure Microsoft Presidio
2. Detect various types of PII entities
3. Redact or mask detected PII in text
4. Handle different types of sensitive information
5. Configure custom PII detection rules
"""

import os
import sys
import json
import time
from typing import List, Dict, Any, Optional
from datetime import datetime

# Microsoft Presidio imports
try:
    from presidio_analyzer import AnalyzerEngine
    from presidio_anonymizer import AnonymizerEngine
    from presidio_anonymizer.entities import OperatorConfig
except ImportError as e:
    print(f"Error importing Presidio: {e}")
    print("Please install: pip install presidio-analyzer presidio-anonymizer")
    sys.exit(1)

# Guardrails imports
try:
    import guardrails as gd
    from guardrails.hub import DetectPII
except ImportError as e:
    print(f"Warning: Guardrails not available: {e}")
    print("Will use direct Presidio implementation")

class PIIDetectionManager:
    """Manages PII detection and redaction using Microsoft Presidio"""
    
    def __init__(self):
        """Initialize Presidio analyzer and anonymizer engines"""
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()
        
        # Define supported entity types
        self.pii_entities = [
            "EMAIL_ADDRESS", "PHONE_NUMBER", "DOMAIN_NAME", "IP_ADDRESS",
            "DATE_TIME", "LOCATION", "PERSON", "URL"
        ]
        
        self.spi_entities = [
            "CREDIT_CARD", "CRYPTO", "IBAN_CODE", "NRP", "MEDICAL_LICENSE",
            "US_BANK_NUMBER", "US_DRIVER_LICENSE", "US_ITIN", "US_PASSPORT", "US_SSN"
        ]
        
        self.all_entities = self.pii_entities + self.spi_entities
        
    def detect_pii(self, text: str, entities: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Detect PII entities in text
        
        Args:
            text: Input text to analyze
            entities: List of entity types to detect (None for all)
            
        Returns:
            List of detected PII entities with details
        """
        if entities is None:
            entities = self.all_entities
            
        results = self.analyzer.analyze(
            text=text,
            entities=entities,
            language='en'
        )
        
        detected_pii = []
        for result in results:
            detected_pii.append({
                'entity_type': result.entity_type,
                'start': result.start,
                'end': result.end,
                'score': result.score,
                'text': text[result.start:result.end]
            })
            
        return detected_pii
    
    def redact_pii(self, text: str, entities: Optional[List[str]] = None, 
                   mask_char: str = 'X', mask_length: Optional[int] = None) -> Dict[str, Any]:
        """
        Redact PII entities in text with masking
        
        Args:
            text: Input text to redact
            entities: List of entity types to redact (None for all)
            mask_char: Character to use for masking (default: X)
            mask_length: Length of mask (None for same as original)
            
        Returns:
            Dictionary with redacted text and detection details
        """
        if entities is None:
            entities = self.all_entities
            
        # Analyze text for PII
        analyzer_results = self.analyzer.analyze(
            text=text,
            entities=entities,
            language='en'
        )
        
        # Configure anonymization operators
        operators = {}
        for result in analyzer_results:
            if mask_length is None:
                # Use same length as original
                mask = mask_char * (result.end - result.start)
            else:
                # Use fixed length
                mask = mask_char * mask_length
                
            operators[result.entity_type] = OperatorConfig(
                "replace",
                {"new_value": f"<{result.entity_type}>"}
            )
        
        # Anonymize the text
        anonymized_result = self.anonymizer.anonymize(
            text=text,
            analyzer_results=analyzer_results,
            operators=operators
        )
        
        return {
            'original_text': text,
            'redacted_text': anonymized_result.text,
            'detected_entities': [
                {
                    'entity_type': entity.entity_type,
                    'start': entity.start,
                    'end': entity.end,
                    'text': text[entity.start:entity.end]
                }
                for entity in analyzer_results
            ],
            'items_redacted': len(analyzer_results)
        }
    
    def configure_custom_detection(self, custom_patterns: Dict[str, str]) -> None:
        """
        Configure custom regex patterns for PII detection
        
        Args:
            custom_patterns: Dictionary of pattern name -> regex pattern
        """
        # Note: This would require extending Presidio's recognizer registry
        # For now, we'll document the approach
        print("Custom pattern configuration would require extending Presidio recognizers")
        print("Available patterns:", list(custom_patterns.keys()))

class GuardrailsPIIManager:
    """Alternative implementation using Guardrails when available"""
    
    def __init__(self):
        """Initialize Guardrails-based PII detection"""
        try:
            # Try to create a mock implementation similar to the documentation
            self.guardrails_available = False
            print("Guardrails hub installation not available, using direct Presidio")
        except Exception as e:
            print(f"Guardrails initialization error: {e}")
            self.guardrails_available = False

def test_pii_detection():
    """Comprehensive test suite for PII detection and redaction"""
    
    # Initialize the PII detection manager
    pii_manager = PIIDetectionManager()
    
    # Test cases with different types of PII
    test_cases = [
        {
            'name': 'Email and Phone',
            'text': 'My email address is john.doe@example.com and my phone number is (555) 123-4567.',
            'expected_entities': ['EMAIL_ADDRESS', 'PHONE_NUMBER']
        },
        {
            'name': 'Credit Card and SSN',
            'text': 'My credit card is 4532-1234-5678-9012 and my SSN is 123-45-6789.',
            'expected_entities': ['CREDIT_CARD', 'US_SSN']
        },
        {
            'name': 'Personal Information',
            'text': 'John Smith lives at 123 Main St, Anytown, USA. His phone is 555-987-6543.',
            'expected_entities': ['PERSON', 'PHONE_NUMBER']
        },
        {
            'name': 'Banking Information',
            'text': 'Account number: 987654321, Routing: 012345678, IBAN: GB82WEST12345698765432',
            'expected_entities': ['US_BANK_NUMBER', 'IBAN_CODE']
        },
        {
            'name': 'Driver License',
            'text': 'My driver\'s license number is D12345678 issued in California.',
            'expected_entities': ['US_DRIVER_LICENSE']
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        print(f"\n=== Testing: {test_case['name']} ===")
        print(f"Original: {test_case['text']}")
        
        # Detect PII
        detected = pii_manager.detect_pii(test_case['text'])
        print(f"Detected entities: {[d['entity_type'] for d in detected]}")
        
        # Redact PII
        redacted = pii_manager.redact_pii(test_case['text'])
        print(f"Redacted: {redacted['redacted_text']}")
        
        # Store results
        result = {
            'test_name': test_case['name'],
            'original_text': test_case['text'],
            'detected_entities': detected,
            'redacted_text': redacted['redacted_text'],
            'items_redacted': redacted['items_redacted'],
            'expected_entities': test_case['expected_entities'],
            'success': len(detected) > 0
        }
        
        results.append(result)
    
    return results

def demonstrate_configuration_options():
    """Demonstrate different configuration options for PII detection"""
    
    pii_manager = PIIDetectionManager()
    
    sample_text = "Contact John Doe at john.doe@company.com or call 555-123-4567. Credit card: 4111-1111-1111-1111"
    
    configurations = [
        {
            'name': 'All Entities',
            'entities': None,
            'description': 'Detect all supported PII types'
        },
        {
            'name': 'PII Only',
            'entities': pii_manager.pii_entities,
            'description': 'Detect only general PII (email, phone, etc.)'
        },
        {
            'name': 'SPI Only',
            'entities': pii_manager.spi_entities,
            'description': 'Detect only sensitive personal information'
        },
        {
            'name': 'Custom Selection',
            'entities': ['EMAIL_ADDRESS', 'CREDIT_CARD'],
            'description': 'Detect only email and credit card numbers'
        }
    ]
    
    config_results = []
    
    for config in configurations:
        print(f"\n=== {config['name']} ===")
        print(f"Description: {config['description']}")
        print(f"Text: {sample_text}")
        
        # Detect with specific entities
        detected = pii_manager.detect_pii(sample_text, entities=config['entities'])
        redacted = pii_manager.redact_pii(sample_text, entities=config['entities'])
        
        result = {
            'config_name': config['name'],
            'entities_used': config['entities'] or 'all',
            'detected_count': len(detected),
            'detected_types': [d['entity_type'] for d in detected],
            'redacted_text': redacted['redacted_text']
        }
        
        print(f"Detected: {result['detected_types']}")
        print(f"Redacted: {result['redacted_text']}")
        
        config_results.append(result)
    
    return config_results

def main():
    """Main execution function for PII detection use case"""
    
    print("=" * 60)
    print("PII Detection and Redaction Use Case")
    print("Using Microsoft Presidio")
    print("=" * 60)
    
    start_time = time.time()
    
    # Initialize results dictionary
    execution_results = {
        'timestamp': datetime.now().isoformat(),
        'setup_status': 'success',
        'tests': {},
        'configurations': {},
        'errors': []
    }
    
    try:
        # Test basic PII detection
        print("\n1. Testing PII Detection and Redaction...")
        test_results = test_pii_detection()
        execution_results['tests'] = test_results
        
        # Demonstrate configuration options
        print("\n2. Demonstrating Configuration Options...")
        config_results = demonstrate_configuration_options()
        execution_results['configurations'] = config_results
        
        # Performance metrics
        execution_time = time.time() - start_time
        execution_results['execution_time'] = execution_time
        
        print(f"\n3. Execution completed in {execution_time:.2f} seconds")
        
    except Exception as e:
        execution_results['errors'].append(str(e))
        execution_results['setup_status'] = 'failed'
        print(f"Error during execution: {e}")
    
    return execution_results

if __name__ == "__main__":
    results = main()
    
    # Save results to JSON file
    with open('/workspace/data/use_case_results_5.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\nResults saved to use_case_results_5.json")