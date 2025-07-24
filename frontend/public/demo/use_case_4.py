#!/usr/bin/env python3
"""
Bug-Free Code Generation Use Case
Using Guardrails AI to generate executable Python code for programming challenges
"""

import ast
import sys
import time
from typing import Dict, Any

from guardrails import Guard
from guardrails.validator_base import Validator, register_validator
from guardrails.classes import FailResult, PassResult, ValidationResult

# Create a custom Python syntax validator
@register_validator(name="python_syntax", data_type="string")
class PythonSyntaxValidator(Validator):
    """Validates that a string contains valid Python syntax."""
    
    def validate(self, value: str, metadata: Dict[str, Any]) -> ValidationResult:
        """Validate Python syntax by attempting to parse with AST."""
        try:
            # Attempt to parse the code
            ast.parse(value)
            return PassResult()
        except SyntaxError as e:
            return FailResult(
                error_message=f"Invalid Python syntax: {str(e)}",
                fix_value=None
            )
        except Exception as e:
            return FailResult(
                error_message=f"Code validation error: {str(e)}",
                fix_value=None
            )

    def _inference_local(self, model_input: Any) -> Any:
        """Local inference for syntax checking."""
        return self.validate(model_input, {})

def setup_guard():
    """Set up the Guard with Python syntax validation."""
    guard = Guard().use(PythonSyntaxValidator(on_fail="reask"))
    return guard

def test_generated_code(code: str) -> bool:
    """Test that generated code is executable."""
    try:
        # Try to compile the code
        compiled_code = compile(code, '<string>', 'exec')
        
        # Create a safe execution environment
        safe_globals = {
            '__builtins__': {
                'len': len,
                'range': range,
                'enumerate': enumerate,
                'max': max,
                'min': min,
                'sum': sum,
                'str': str,
                'int': int,
                'float': float,
                'list': list,
                'dict': dict,
                'set': set,
                'print': print,
            }
        }
        
        # Execute the code in a controlled environment
        exec(compiled_code, safe_globals)
        return True
    except Exception as e:
        print(f"Code execution failed: {e}")
        return False

def generate_leetcode_solution(problem_description: str, guard: Guard) -> str:
    """Generate a bug-free solution for a LeetCode problem."""
    
    prompt = f"""
Given the following LeetCode problem description, write a complete Python solution that:
1. Solves the problem correctly
2. Uses proper Python syntax and best practices
3. Includes necessary function definitions and imports
4. Is ready to be executed directly

Problem Description:
{problem_description}

Please provide only the Python code without any markdown formatting or explanations.
"""

    try:
        # For demonstration purposes, we'll use a mock response
        # In a real scenario, this would use an LLM API call
        
        # Mock LLM response for testing
        if "longest palindromic substring" in problem_description.lower():
            solution = '''def longest_palindrome(s: str) -> str:
    if len(s) == 0:
        return ""
    
    start, end = 0, 0
    
    def expand_around_center(left: int, right: int) -> int:
        while left >= 0 and right < len(s) and s[left] == s[right]:
            left -= 1
            right += 1
        return right - left - 1
    
    for i in range(len(s)):
        len1 = expand_around_center(i, i)
        len2 = expand_around_center(i, i + 1)
        max_len = max(len1, len2)
        
        if max_len > end - start:
            start = i - (max_len - 1) // 2
            end = i + max_len // 2
    
    return s[start:end + 1]'''
        elif "two sum" in problem_description.lower():
            solution = '''def two_sum(nums, target):
    num_map = {}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in num_map:
            return [num_map[complement], i]
        num_map[num] = i
    return []'''
        else:
            solution = '''def solve_problem(input_data):
    # Default implementation
    return input_data'''
        
        # Validate the solution using our guard
        try:
            validation_result = guard.validate(solution)
            if hasattr(validation_result, 'validated_output'):
                return validation_result.validated_output
            else:
                return solution
        except Exception as e:
            print(f"Validation error: {e}")
            return solution
            
    except Exception as e:
        print(f"Error generating solution: {e}")
        return None

def main():
    """Main execution function for the use case."""
    start_time = time.time()
    
    print("=== Bug-Free Code Generation Use Case ===")
    print("Setting up Guard with Python syntax validation...")
    
    # Step 1: Create Guard with syntax checking
    guard = setup_guard()
    print("✓ Guard created successfully")
    
    # Step 2: Test with sample problems
    test_problems = [
        "Given a string s, find the longest palindromic substring in s. You may assume that the maximum length of s is 1000.",
        "Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.",
    ]
    
    results = []
    
    for i, problem in enumerate(test_problems, 1):
        print(f"\n--- Problem {i} ---")
        print(f"Description: {problem}")
        
        # Generate solution
        solution = generate_leetcode_solution(problem, guard)
        if solution:
            print("Generated solution:")
            print(solution)
            
            # Validate code syntax
            validator = PythonSyntaxValidator()
            validation_result = validator.validate(solution, {})
            
            if isinstance(validation_result, PassResult):
                print("✓ Syntax validation passed")
                
                # Test code execution
                execution_success = test_generated_code(solution)
                if execution_success:
                    print("✓ Code execution successful")
                    results.append({
                        "problem": i,
                        "status": "success",
                        "solution": solution
                    })
                else:
                    print("✗ Code execution failed")
                    results.append({
                        "problem": i,
                        "status": "execution_failed"
                    })
            else:
                print(f"✗ Syntax validation failed: {validation_result.error_message}")
                results.append({
                    "problem": i,
                    "status": "validation_failed",
                    "error": validation_result.error_message
                })
        else:
            print("✗ Failed to generate solution")
            results.append({
                "problem": i,
                "status": "generation_failed"
            })
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    print(f"\n=== Execution Summary ===")
    print(f"Total execution time: {execution_time:.2f} seconds")
    print(f"Problems processed: {len(test_problems)}")
    
    successful = sum(1 for r in results if r["status"] == "success")
    print(f"Successful generations: {successful}/{len(test_problems)}")
    
    return {
        "execution_time": execution_time,
        "problems_processed": len(test_problems),
        "successful_generations": successful,
        "results": results
    }

if __name__ == "__main__":
    main()