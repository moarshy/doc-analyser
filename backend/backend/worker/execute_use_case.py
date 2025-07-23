import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from datetime import datetime, timezone
from claude_code_sdk import query, ClaudeCodeOptions

# Set up logger
logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

PROMPT = """
You are a senior coding assistant.
You will try to execute the use case.
In doing so, you will need to use the documentation to understand the use case. You will identify the usefulness of the documentation.

Here is the use case you need to implement:
Use Case Name: {use_case_name}
Use Case Description: {use_case_description}
Use Case Success Criteria: {use_case_success_criteria}
Use Case Difficulty Level: {use_case_difficulty_level}
Use Case Documentation Source: {use_case_documentation_source}


INSTRUCTIONS:
1. Use the documentation to understand the use case.
2. MUST save the working code as {code_file_name}.py or {code_file_name}.js (choose the appropriate extension based on the language)
3. Execute the code and see if it works.
4. Keep track of how the documentation was used to execute the use case.
5. MUST save the final results as {results_file_name} in JSON format
6. It is important that you use the underlying library to implement the use case.
7. YOU MUST USE THE LIBRARY TO IMPLEMENT THE USE CASE.
8. You must first install the library and its dependencies. 
9. CRITICAL: Ensure both files ({code_file_name}.py/.js or other language extension) and {results_file_name} are created in the working directory.

OUTPUT_FORMAT:

```json
{{
    "execution_status": "success|failure|partial",
    "execution_results": "Detailed execution results including output, errors, etc.",
    "documentation_sources_used": ["List of documentation files/sections referenced"],
    "documentation_usefulness": ["How the documentation helped accomplish the task"],
    "documentation_weaknesses": ["What was missing, unclear, or incorrect in the docs"],
    "documentation_improvements": ["Specific suggestions to improve the documentation"],
    "code_file_path": "{code_file_name}.py",
    "execution_time": "Time taken to complete the task",
    "success_criteria_met": ["Which success criteria were achieved"],
    "challenges_encountered": ["Any difficulties during implementation"]
}}
```
All files must be saved in the pwd: {cwd}
Save this output as: {results_file_name} in the pwd: {cwd}

Repository Context:
- Repo Path: /workspace/repo
- Include Folders: {include_folders}
- Focus on documentation in these folders to understand how to implement the use case
- Look for examples, API references, tutorials, and guides

Remember: Your goal is to evaluate how well the documentation enables someone to implement this use case successfully based on the repository context.
"""

SYSTEM_PROMPT = """
You are a senior coding assistant specialized in evaluating documentation quality through practical implementation.

Your task is to:
1. Implement use cases based solely on the available documentation
2. Evaluate how helpful, complete, and accurate the documentation is
3. Provide constructive feedback to improve documentation quality

Be thorough in your evaluation and specific in your feedback.
"""

async def execute_use_case(prompt: str, cwd: str):
    options = ClaudeCodeOptions(
        max_turns=300,
        system_prompt=SYSTEM_PROMPT,
        cwd=cwd,
        allowed_tools=[
            "Read", "Write", "Edit", 
            "LS", "MultiEdit",
            "Glob", "Grep", "Task",  
            "Bash", "NotebookRead",
            "TodoWrite", "exit_plan_mode"
        ]
    )

    messages = []
    turn_count = 0
    async for message in query(prompt=prompt, options=options):
        messages.append(message)
        turn_count += 1
        logger.info(f"Turn {turn_count}")
    
    logger.info(messages[-1])
    return messages

async def execute_use_cases(cwd: str, use_case_json_path: str, repo_path: str, include_folders: list[str]):
    """Execute all use cases from JSON file.
    
    Args:
        cwd: Working directory for execution
        use_case_json_path: Path to use_cases.json
        repo_path: Path to repository
        include_folders: Folders to include in analysis
    """
    # Read the use cases from the json file
    try:
        with open(use_case_json_path, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        logger.error(f"Error: Could not find use case file at {use_case_json_path}")
        return
    except json.JSONDecodeError as e:
        logger.error(f"Error: Invalid JSON in use case file: {e}")
        return

    # Handle different possible JSON structures
    use_cases = data.get('use_cases', data) if isinstance(data, dict) else data
    
    if not isinstance(use_cases, list):
        logger.error(f"Error: Expected list of use cases, got {type(use_cases)}")
        return

    logger.info(f"Found {len(use_cases)} use cases to execute")

    # Execute the use cases
    for i, use_case in enumerate(use_cases):
        logger.info(f"{'='*50}")
        logger.info(f"Executing Use Case {i+1}/{len(use_cases)}")
        logger.info(f"Name: {use_case.get('name', 'Unnamed')}")
        logger.info(f"{'='*50}")
        
        # Handle both string and list formats for success_criteria
        success_criteria = use_case.get("success_criteria", [])
        if isinstance(success_criteria, list):
            success_criteria_str = "\n".join(f"- {criterion}" for criterion in success_criteria)
        else:
            success_criteria_str = str(success_criteria)
        
        # Handle both string and list formats for include_folders
        include_folders_str = ", ".join(include_folders) if isinstance(include_folders, list) else str(include_folders)
        
        # Format the prompt using .format() method
        prompt = PROMPT.format(
            use_case_name=use_case.get("name", "Unnamed Use Case"),
            use_case_description=use_case.get("description", "No description provided"),
            use_case_success_criteria=success_criteria_str,
            use_case_difficulty_level=use_case.get("difficulty_level", "Unknown"),
            use_case_documentation_source=use_case.get("documentation_source", "Unknown"),
            code_file_name=f"use_case_{i+1}",
            results_file_name=f"use_case_{i+1}_results.json",
            cwd=cwd,
            include_folders=include_folders_str
        )

        try:
            messages = await execute_use_case(prompt, cwd)
            logger.info(f"Use case {i+1} execution completed")
            
            # Optional: Add a small delay between executions
            await asyncio.sleep(1)
            
        except Exception as e:
            logger.error(f"Error executing use case {i+1}: {e}")
            continue

    logger.info("All use cases completed!")
    
async def execute_single_use_case_by_id(use_case_json_path: str, output_dir: str, use_case_id: int, include_folders: list[str], repo_path: str = "/workspace/repo"):
    """Execute a specific use case by ID.
    
    Args:
        use_case_json_path: Path to use_cases.json
        output_dir: Directory to save results
        use_case_id: The specific use case ID to execute (0-n)
        include_folders: Folders to include in analysis
        repo_path: Path to repository
    """
    try:
        with open(use_case_json_path, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        logger.error(f"Error: Could not find use case file at {use_case_json_path}")
        return
    except json.JSONDecodeError as e:
        logger.error(f"Error: Invalid JSON in use case file: {e}")
        return

    # Handle different possible JSON structures
    use_cases = data.get('use_cases', data) if isinstance(data, dict) else data
    
    if not isinstance(use_cases, list):
        logger.error(f"Error: Expected list of use cases, got {type(use_cases)}")
        return

    if use_case_id < 0 or use_case_id >= len(use_cases):
        logger.error(f"Error: Invalid use case ID {use_case_id}, valid range is 0-{len(use_cases)-1}")
        return

    use_case = use_cases[use_case_id]
    logger.info(f"Executing use case {use_case_id}: {use_case.get('name', 'Unnamed')}")
    
    # Execute the single use case
    await execute_single_use_case_async(use_case, repo_path, output_dir, include_folders, use_case_id)

async def execute_single_use_case_async(use_case: dict, repo_path: str, output_dir: str, include_folders: list[str], use_case_index: int):
    """Async version of execute_single_use_case with file generation."""
    # Ensure output directory exists
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Include folders: {include_folders}")
    logger.info(f"Use case index: {use_case_index}")
    logger.info(f"Use case: {use_case}")
    logger.info(f"Repo path: {repo_path}")
    os.makedirs(output_dir, exist_ok=True)
    
    # Handle both string and list formats for success_criteria
    success_criteria = use_case.get("success_criteria", [])
    if isinstance(success_criteria, list):
        success_criteria_str = "\n".join(f"- {criterion}" for criterion in success_criteria)
    else:
        success_criteria_str = str(success_criteria)
    
    include_folders_str = ", ".join(include_folders) if isinstance(include_folders, list) else str(include_folders)
    
    # Generate file names with index
    code_file_name = f"use_case_{use_case_index}"
    results_file_name = f"use_case_results_{use_case_index}.json"

    logger.info(f"Code file name: {code_file_name}")
    logger.info(f"Results file name: {results_file_name}")
    
    # Format prompt
    prompt = PROMPT.format(
        use_case_name=use_case.get("name", f"Use Case {use_case_index}"),
        use_case_description=use_case.get("description", "No description provided"),
        use_case_success_criteria=success_criteria_str,
        use_case_difficulty_level=use_case.get("difficulty_level", "Unknown"),
        use_case_documentation_source=use_case.get("documentation_source", "Unknown"),
        code_file_name=code_file_name,
        results_file_name=results_file_name,
        cwd=output_dir,
        include_folders=include_folders_str
    )
    logger.info(f"Prompt: {prompt}")
    
    try:
        # Execute the use case and get generated code
        await execute_use_case(prompt, output_dir)
        
    except Exception as e:
        logger.error(f"Error executing use case {use_case_index}: {e}")
        
        # Save error results
        error_results = {
            "use_case_name": use_case.get("name", f"Use Case {use_case_index}"),
            "use_case_index": use_case_index,
            "error": str(e),
            "success": False,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        error_file_path = os.path.join(output_dir, results_file_name)
        with open(error_file_path, "w") as f:
            json.dump(error_results, f, indent=2, default=str)

if __name__ == "__main__":
    import sys
    import asyncio
    
    if len(sys.argv) < 4:
        print("Usage: python execute_use_case.py <use_case_json_path> <output_dir> <include_folders> [use_case_id]")
        print("  use_case_id: Optional, specific use case to execute (0-n). If not provided, executes all use cases.")
        sys.exit(1)
    
    use_case_json_path = sys.argv[1]
    output_dir = sys.argv[2]
    include_folders = sys.argv[3].split(",")
    
    # Check if specific use case ID is provided
    if len(sys.argv) >= 5:
        try:
            use_case_id = int(sys.argv[4])
            print(f"Executing single use case ID: {use_case_id}")
            try:
                asyncio.run(execute_single_use_case_by_id(
                    use_case_json_path, output_dir, use_case_id, include_folders
                ))
            except KeyboardInterrupt:
                print("\nExecution interrupted by user")
            except Exception as e:
                print(f"Unexpected error: {e}")
                import traceback
                traceback.print_exc()
        except ValueError:
            print("Error: use_case_id must be an integer")
            sys.exit(1)
    else:
        # Execute all use cases (backward compatibility)
        print("Starting use case execution...")
        print(f"Use cases file: {use_case_json_path}")
        print(f"Output directory: {output_dir}")
        print(f"Include folders: {include_folders}")
        
        try:
            # Read use cases
            with open(use_case_json_path, "r") as f:
                data = json.load(f)
            use_cases = data.get('use_cases', data) if isinstance(data, dict) else data
            
            # Execute each use case with index
            for i, use_case in enumerate(use_cases):
                print(f"Executing use case {i}: {use_case.get('name', 'Unnamed')}")
                asyncio.run(execute_single_use_case_async(
                    use_case, "/workspace/repo", output_dir, include_folders, i
                ))
                
        except KeyboardInterrupt:
            print("\nExecution interrupted by user")
        except Exception as e:
            print(f"Unexpected error: {e}")
            import traceback
            traceback.print_exc()