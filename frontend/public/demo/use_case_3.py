#!/usr/bin/env python3
"""
Chatbot Content Moderation Implementation
Based on Guardrails AI documentation examples

This script demonstrates a chatbot with content moderation capabilities
including profanity filtering and toxic language detection.
"""

import os
import sys
import logging
from typing import List, Tuple, Dict, Any
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MockContentValidator:
    """Mock validator for demonstration purposes."""
    
    def __init__(self, validator_type: str, threshold: float = 0.5):
        self.validator_type = validator_type
        self.threshold = threshold
        self.profanity_words = {
            'damn', 'hell', 'shit', 'fuck', 'ass', 'bitch', 'bastard', 
            'crap', 'piss', 'dick', 'cock', 'pussy', 'tits'
        }
        
    def validate(self, text: str) -> bool:
        """Validate text content."""
        text_lower = text.lower()
        
        if self.validator_type == "profanity":
            # Check for profanity words, but be more precise
            words = text_lower.split()
            # Check if any profanity word appears as a standalone word
            for profanity in self.profanity_words:
                if profanity in text_lower:
                    # Check if it's a whole word match
                    if re.search(r'\b' + re.escape(profanity) + r'\b', text_lower):
                        return False
            return True
        
        elif self.validator_type == "toxic":
            toxic_patterns = [
                r'\b(stupid|idiot|moron|retard|pathetic|worthless|useless)\b',
                r'\b(hate|despise|loathe)\b.*\b(you|your|yourself)\b',
                r'\b(shut up|fuck off|piss off)\b'
            ]
            return not any(re.search(pattern, text_lower) for pattern in toxic_patterns)
        
        return True

class MockGuard:
    """Mock Guard class for demonstration purposes."""
    
    def __init__(self):
        self.name = 'ContentModerationChatbot'
        self.validators = []
        self.history = []
        
    def use(self, validator):
        """Add a validator to the guard."""
        self.validators.append(validator)
        return self
    
    def validate(self, text: str) -> Dict[str, Any]:
        """Validate text using all configured validators."""
        validation_results = []
        
        for validator in self.validators:
            is_valid = validator.validate(text)
            validation_results.append({
                'validator': validator.validator_type,
                'valid': is_valid
            })
        
        all_valid = all(result['valid'] for result in validation_results)
        
        return {
            'valid': all_valid,
            'results': validation_results,
            'validated_output': text if all_valid else None
        }

class ContentModerationChatbot:
    """
    A chatbot implementation with content moderation capabilities.
    
    Features:
    - Profanity filtering
    - Toxic language detection
    - Mock chat interface
    - Graceful error handling
    """
    
    def __init__(self):
        self.guard = None
        self.system_message = {
            "role": "system",
            "content": "You are a helpful, respectful, and honest assistant. "
                       "Always provide safe and appropriate responses. "
                       "Avoid using profanity, toxic language, or inappropriate content. "
                       "If asked about harmful topics, respond with: "
                       "I cannot provide information on that topic."
        }
        self._setup_guard()
    
    def _setup_guard(self):
        """Initialize the Guard with content moderation validators."""
        try:
            self.guard = MockGuard()
            
            # Add profanity filter
            profanity_validator = MockContentValidator("profanity")
            self.guard.use(profanity_validator)
            
            # Add toxic language detection
            toxic_validator = MockContentValidator("toxic", threshold=0.5)
            self.guard.use(toxic_validator)
            
            logger.info("Content moderation guard initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize guard: {e}")
            raise
    
    def history_to_messages(self, history: List[Tuple[str, str]]) -> List[Dict[str, str]]:
        """Convert chat history to message format for LLM."""
        messages = [self.system_message]
        
        for user_msg, assistant_msg in history:
            if user_msg:
                messages.append({"role": "user", "content": user_msg})
            if assistant_msg:
                messages.append({"role": "assistant", "content": assistant_msg})
                
        return messages
    
    def generate_response(self, message: str, history: List[Tuple[str, str]]) -> str:
        """Generate a response with content moderation."""
        if not self.guard:
            return "Error: Content moderation system not initialized."
        
        try:
            # Validate the input message
            validation_result = self.guard.validate(message)
            
            if not validation_result['valid']:
                failed_validators = [
                    r['validator'] for r in validation_result['results'] 
                    if not r['valid']
                ]
                logger.warning(f"Input validation failed for: {failed_validators}")
                return self._handle_validation_failure(message, failed_validators)
            
            # Generate mock response
            response = self._mock_llm_response(message)
            
            # Validate the response
            response_validation = self.guard.validate(response)
            
            if response_validation['valid']:
                return response
            else:
                logger.warning("Response validation failed")
                return self._handle_validation_failure("generated response", ["toxic"])
                
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "I'm sorry, I encountered an error processing your request. Please try again."
    
    def _mock_llm_response(self, message: str) -> str:
        """Generate a mock response for demonstration purposes."""
        # Validate the message first
        validation = self.guard.validate(message)
        if not validation['valid']:
            return "I cannot respond to messages that may contain inappropriate content."
        
        message_lower = message.lower()
        
        # Safe mock responses
        responses = {
            "hello": "Hello! How can I help you today?",
            "how are you": "I'm doing well, thank you for asking! How can I assist you?",
            "help": "I'm here to help! What would you like to know?",
            "thanks": "You're welcome! Is there anything else I can help you with?",
            "what is ai": "AI (Artificial Intelligence) refers to the simulation of human intelligence in machines that are programmed to think and learn.",
            "tell me a joke": "Why don't scientists trust atoms? Because they make up everything!",
        }
        
        for key, response in responses.items():
            if key in message_lower:
                return response
                
        return f"I understand you're asking about: {message}. I'd be happy to help with that in a safe and appropriate way."
    
    def _handle_validation_failure(self, content: str, failed_validators: List[str]) -> str:
        """Handle validation failures gracefully."""
        validator_names = ", ".join(failed_validators)
        return (
            f"I apologize, but I cannot provide a response because the content "
            f"failed validation for: {validator_names}. I'm designed to maintain "
            f"a safe and respectful conversation environment. Please rephrase "
            f"your message in a more appropriate way."
        )
    
    def test_content_moderation(self) -> Dict[str, Any]:
        """Test the content moderation system."""
        test_cases = [
            ("Hello world", True, "Should pass all validations"),
            ("This is a damn test", False, "Should fail profanity check"),
            ("You are so stupid and pathetic", False, "Should fail toxic language check"),
            ("I hate this stupid thing", False, "Should fail both checks"),
            ("Have a nice day!", True, "Should pass all validations"),
            ("Please help me with this problem", True, "Should pass all validations"),
        ]
        
        results = {}
        
        for text, expected_valid, description in test_cases:
            try:
                validation_result = self.guard.validate(text)
                actual_valid = validation_result['valid']
                
                results[text] = {
                    "description": description,
                    "expected_valid": expected_valid,
                    "actual_valid": actual_valid,
                    "validation_results": validation_result['results'],
                    "test_passed": actual_valid == expected_valid
                }
                
            except Exception as e:
                results[text] = {
                    "description": description,
                    "expected_valid": expected_valid,
                    "actual_valid": None,
                    "error": str(e),
                    "test_passed": False
                }
        
        return results
    
    def run_demo(self):
        """Run a demonstration of the chatbot."""
        print("🤖 Content Moderation Chatbot Demo")
        print("=" * 40)
        print("Testing content moderation capabilities...")
        print()
        
        # Test content moderation
        test_results = self.test_content_moderation()
        
        print("📊 Content Moderation Test Results:")
        print("-" * 30)
        
        passed_tests = 0
        total_tests = len(test_results)
        
        for text, result in test_results.items():
            status = "✅ PASS" if result['test_passed'] else "❌ FAIL"
            print(f"{status} '{text}' - {result['description']}")
            
            if not result['test_passed']:
                print(f"    Expected: {result['expected_valid']}, Got: {result['actual_valid']}")
                if 'validation_results' in result:
                    for vr in result['validation_results']:
                        print(f"    {vr['validator']}: {'PASS' if vr['valid'] else 'FAIL'}")
            
            if result['test_passed']:
                passed_tests += 1
            print()
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        print(f"Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests})")
        
        # Interactive demo
        print("\n🎯 Interactive Demo:")
        print("Type 'quit' to exit")
        print()
        
        history = []
        while True:
            try:
                user_input = input("You: ").strip()
                if user_input.lower() in ['quit', 'exit', 'q']:
                    break
                
                response = self.generate_response(user_input, history)
                print(f"Bot: {response}")
                
                history.append((user_input, response))
                
                # Keep history manageable
                if len(history) > 5:
                    history = history[-5:]
                    
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except EOFError:
                break


def main():
    """Main function to run the chatbot."""
    print("🤖 Content Moderation Chatbot")
    print("=" * 40)
    print("This chatbot demonstrates:")
    print("- Profanity filtering")
    print("- Toxic language detection")
    print("- Content validation")
    print("- Graceful error handling")
    print()
    
    try:
        chatbot = ContentModerationChatbot()
        chatbot.run_demo()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        main()
    else:
        chatbot = ContentModerationChatbot()
        chatbot.run_demo()