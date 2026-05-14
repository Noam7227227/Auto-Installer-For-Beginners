import typing

def execute_system_command(command: str) -> str:
    """
    Executes a shell command on the host system.
    
    Args:
        command: The full string of the command to be executed (e.g., 'ls -la' or 'dir').
    """
    print(f"[MOCK EXECUTION] Running command: {command}")
    return f"Success: Command '{command}' executed (Mock)."

def set_env_variable(key: str, value: str) -> str:
    """
    Creates or updates an environment variable in the current session.
    
    Args:
        key: The name of the environment variable.
        value: The value to assign to the variable.
    """
    print(f"[MOCK EXECUTION] Setting environment variable: {key}={value}")
    return f"Success: Environment variable '{key}' set to '{value}' (Mock)."

def download_from_link(url: str, destination_path: str) -> str:
    """
    Downloads a program or file from a specific URL to a local path.
    
    Args:
        url: The direct download link for the file.
        destination_path: The local directory or filename where the file should be saved.
    """
    print(f"[MOCK EXECUTION] Downloading from {url} to {destination_path}")
    return f"Success: Downloaded file from {url} to {destination_path} (Mock)."

def brave_search(query: str) -> str:
    """
    Searches the internet to find download links, documentation, or software information.
    
    Args:
        query: The search terms (e.g., 'official download link for Git Windows')
    """
    # This simulates a search engine returning a result
    print(f"[MOCK SEARCH] Searching for: {query}")
    
    # Simple logic to make the mock feel "real"
    mock_links = {
        "git": "https://git-scm.com/download/win",
        "python": "https://www.python.org/downloads/",
        "vscode": "https://code.visualstudio.com/download",
        "node": "https://nodejs.org/en/download/"
    }
    
    # Try to find a match in our mock dictionary, otherwise return a generic link
    for key in mock_links:
        if key in query.lower():
            return mock_links[key]
            
    return "https://example.com/software-download-link"

tools = [
    {
        "name": "execute_system_command",
        "description": "Executes a shell command on the host system.",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "The command to run."}
            },
            "required": ["command"]
        }
    },
    {
        "name": "set_env_variable",
        "description": "Creates or updates an environment variable.",
        "parameters": {
            "type": "object",
            "properties": {
                "key": {"type": "string", "description": "The variable name."},
                "value": {"type": "string", "description": "The variable value."}
            },
            "required": ["key", "value"]
        }
    },
    {
        "name": "download_from_link",
        "description": "Downloads a program or file from a URL to a local destination.",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "The source URL."},
                "destination_path": {"type": "string", "description": "The local path to save the file."}
            },
            "required": ["url", "destination_path"]
        }
    },
    {
        "name": "brave_search",
        "description": "Searches the internet to find download links, documentation, or software information.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search terms to look up."}
            },
            "required": ["query"]
        }
    }
]

tools_names = [tool["name"] for tool in tools]