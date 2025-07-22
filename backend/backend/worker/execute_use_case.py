from claude_code_sdk import query, ClaudeCodeOptions
import json

PROMPT = """
Here is the use case:
Use Case Name: {use_case_name}
Use Case Description: {use_case_description}
Use Case Success Criteria: {use_case_success_criteria}
Use Case Difficulty Level: {use_case_difficulty_level}
Use Case Documentation Source: {use_case_documentation_source}

You are a senior coding assistant.
You will try to execute the use case.
In doing so, you will need to use the documentation to understand the use case. You will identify the usefulness of the documentation.

INSTRUCTIONS:
1. Understand the use case.
2. Use the documentation to understand the use case.
3. Save the code as {code_file_name}.py or {code_file_name}.js
4. Execute the code and see if it works.
5. Keep track of how the documentation was used to execute the use case.
6. In the end, you will need to produce a json file with the execution results.
7. It is important that you use the underlying library to implement the use case.
8. YOU MUST USE THE LIBRARY TO IMPLEMENT THE USE CASE.
9. You must first install the library and its dependencies.

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
- Repo Path: {repo_path}
- Include Folders: {include_folders}
- Focus on documentation in these folders to understand how to implement the use case
- Look for examples, API references, tutorials, and guides

Remember: Your goal is to evaluate how well the documentation enables someone to implement this use case successfully.
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
            "Read", "Write", "Edit", "LS", "MultiEdit",
            "Glob", "Grep", "Task",  # Fixed missing comma
            "Bash", "NotebookRead",
            "TodoWrite", "exit_plan_mode"
        ]
    )

    messages = []
    turn_count = 0
    async for message in query(prompt=prompt, options=options):
        messages.append(message)
        turn_count += 1
        print(f"Turn {turn_count}")
    
    print(messages[-1])
    return messages

async def execute_use_cases(cwd: str, use_case_json_path: str, repo_path: str, include_folders: list[str]):
    # Read the use cases from the json file
    try:
        with open(use_case_json_path, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Could not find use case file at {use_case_json_path}")
        return
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in use case file: {e}")
        return

    # Handle different possible JSON structures
    use_cases = data.get('use_cases', data) if isinstance(data, dict) else data
    
    if not isinstance(use_cases, list):
        print(f"Error: Expected list of use cases, got {type(use_cases)}")
        return

    print(f"Found {len(use_cases)} use cases to execute")

    # Execute the use cases
    for i, use_case in enumerate(use_cases):
        print(f"\n{'='*50}")
        print(f"Executing Use Case {i+1}/{len(use_cases)}")
        print(f"Name: {use_case.get('name', 'Unnamed')}")
        print(f"{'='*50}")
        
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
            repo_path=repo_path,
            include_folders=include_folders_str,
            code_file_name=f"use_case_{i+1}",
            results_file_name=f"use_case_{i+1}_results.json",
            cwd=cwd
        )

        try:
            messages = await execute_use_case(prompt, cwd)
            print(f"Use case {i+1} execution completed")
            
            # Optional: Add a small delay between executions
            import asyncio
            await asyncio.sleep(1)
            
        except Exception as e:
            print(f"Error executing use case {i+1}: {e}")
            continue

    print(f"\nAll use cases completed!")


if __name__ == "__main__":

    import asyncio
    
    # Configuration
    config = {
        "cwd": "/Users/arshath/play/naptha/devagent/data",
        "use_case_json_path": "/Users/arshath/play/naptha/devagent/data/use_cases.json",
        "repo_path": "/Users/arshath/play/naptha/devagent/data/guardrails",
        "include_folders": ["docs"]
    }
    
    print("Starting use case execution...")
    print(f"Working directory: {config['cwd']}")
    print(f"Use cases file: {config['use_case_json_path']}")
    print(f"Repository path: {config['repo_path']}")
    print(f"Include folders: {config['include_folders']}")
    
    try:
        asyncio.run(execute_use_cases(**config))
    except KeyboardInterrupt:
        print("\nExecution interrupted by user")
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()