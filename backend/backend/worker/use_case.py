import asyncio
import json
import logging
import os
import sys
from pathlib import Path

from claude_code_sdk import query, ClaudeCodeOptions

# Set up logger
logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

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

def extract_use_cases(repo_path: str, output_path: str):
    """Extract use cases from documentation using Claude Code.
    
    Args:
        repo_path: Path to the repository documentation
        output_path: Path to save use_cases.json
    """
    import asyncio
    import os
    from pathlib import Path
    
    # Update prompt with actual paths
    prompt = PROMPT.replace("/workspace/repo", repo_path).replace("/workspace/data/use_cases.json", output_path)
    
    options = ClaudeCodeOptions(
        max_turns=300,
        system_prompt=SYSTEM_PROMPT,
        cwd=os.path.dirname(output_path),
        allowed_tools=[
            "Read", "Write", "Edit", "LS", "MultiEdit",
            "Glob", "Grep", "Task",
            "Bash", "NotebookRead",
            "TodoWrite", "exit_plan_mode"
        ]
    )
    
    async def run_extraction():
        messages = []
        turn_count = 0
        try:
            async for message in query(prompt=prompt, options=options):
                messages.append(message)
                turn_count += 1
                logger.info(f"Turn {turn_count} completed")
                logger.info(f"Message: {message}")
        except Exception as e:
            logger.error(f"Error in use case extraction: {e}")
            raise
        
        logger.info(f"Extraction completed with {len(messages)} messages")
        return messages
    
    return asyncio.run(run_extraction())

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python use_case.py <repo_path> <output_path>")
        sys.exit(1)
    
    repo_path = sys.argv[1]
    output_path = sys.argv[2]
    logger.info(f"Starting use case extraction from {repo_path} to {output_path}")
    extract_use_cases(repo_path, output_path)