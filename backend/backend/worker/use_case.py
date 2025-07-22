from claude_code_sdk import query, ClaudeCodeOptions
import json

SYSTEM_PROMPT = """
You are a senior coding assistant.
"""

PROMPT = """
You are a senior coding assistant.
You are to analyse the documentation of a tool and identify use cases/examples present in the documentation.

INSTRUCTIONS:
1. You are to output the use cases in the following format:
2. Difficulty level can be one of the following: Beginner, Intermediate, Advanced.
3. Documentation source is the list of paths to the documentation.
4. Only use the markdown files in the documentation source.
5. At the end, we MUST have a produce a json file with the use cases.

```json
{
    "use_cases": [
        {
            "name": "Use Case 1",
            "description": "Description of Use Case 1",
            "success_criteria": ["Success Criteria 1", "Success Criteria 2"],
            "difficulty_level": "Beginner",
            "documentation_source": ["Documentation Source 1"]
        },
        {
            "name": "Use Case 2",
            "description": "Description of Use Case 2",
            "success_criteria": ["Success Criteria 3", "Success Criteria 4"],
            "difficulty_level": "Intermediate",
            "documentation_source": "Documentation Source 2"
        }
    ]
}
```
Save the output in a file called "use_cases.json" in the current directory.

Here is the path of the documentation:
/workspace/repo

Here is the where you should save the output:
/workspace/data/use_cases.json
"""

options = ClaudeCodeOptions(
    max_turns=300,
    system_prompt=SYSTEM_PROMPT,
    cwd="/Users/arshath/play/naptha/devagent/data",
    allowed_tools=[
        "Read", "Write", "Edit", "LS", "MultiEdit",
        "Glob", "Grep", "Task"
        "Bash", "NotebookRead",
        "TodoWrite", "exit_plan_mode"
    ]
)

async def extract_use_cases():
    messages = []
    turn_count = 0
    async for message in query(prompt=PROMPT, options=options):
        messages.append(message)
        turn_count += 1
        print(f"Turn {turn_count}")

    print(messages[-1])
    return messages

if __name__ == "__main__":
    import asyncio
    asyncio.run(extract_use_cases())