from tavily import TavilyClient
import os
from dotenv import load_dotenv

load_dotenv()
_tavily = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

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

def download_link_search(software_name: str) -> str:
    """
    Searches the internet using Tavily to find the official download link for a specific software.
    
    Args:
        software_name: The name of the software to find (e.g., 'Git', 'Python 3.12', 'VS Code')
    """
    print(f"[SEARCHING] Finding official download link for: {software_name}...")
    
    # Constructing a specific query helps Tavily find the "direct" link
    query = f"official download link for {software_name} for Windows"
    
    try:
        # We use search_depth="advanced" to get more reliable results for technical links
        search_result = _tavily.search(query=query, search_depth="advanced", max_results=10)
        
        # Look for the most relevant result
        if search_result and "results" in search_result:
            for result in search_result["results"]:
                url = result.get("url", "")
                
                # Simple logic to prioritize "official" looking domains
                # You can expand this list as needed
                if any(ext in url.lower() for ext in [".exe", ".msi", "download", "release"]):
                    print(f"[FOUND] Official link identified: {url}")
                    return url
            
            # If no direct file link, return the top result
            top_url = search_result["results"][0]["url"]
            print(f"[FOUND] Best available link: {top_url}")

            return installation_url
            
        print(f"[NOT FOUND] No reliable links found for {software_name}.")
        return f"Error: Could not find an official download link for {software_name}."

    except Exception as e:
        print(f"[ERROR] Tavily search failed: {e}")
        return f"Error: Search failed for {software_name}."

def choco_command_search(software_name: str) -> str:
    """
    Searches the internet using Tavily to find the correct choco install command for a given software, if it exists.
    
    Args:
        software_name: The name of the software to find (e.g., 'Git', 'Python 3.12', 'VS Code')
    """
    
    # Constructing a specific query helps Tavily find the "direct" link
    query = f"official choco install command for {software_name} for Windows"
    
    try:
        # We use search_depth="advanced" to get more reliable results for technical links
        search_result = _tavily.search(query=query, search_depth="advanced", max_results=10)
        
        if search_result and "results" in search_result:
            for result in search_result["results"]:
                url = result.get("url", "")
                
                # Simple logic to prioritize "official" looking domains
                # You can expand this list as needed
                if "chocolatey.org" in url.lower():
                    print(f"[FOUND] Official Chocolatey command identified: {url}")
                    return url
            
            # If no direct command link, return the top result
            top_url = search_result["results"][0]["url"]
            print(f"[FOUND] Best available link: {top_url}")

            return top_url
    except Exception as e:
        print(f"[ERROR] Tavily search failed: {e}")
        return f"Error: Search failed for {software_name}."


def research_installer_tool(software_name: str) -> str:
    """
    Uses Tavily to research the installation process for a given software.
    If the softawre can be downloaded using bash commands (e.g pip, npm, winget), this is the best option.
    Otherwise suggest using chocolatey if a command is available. Do not suggest downloading an installer directly.
    
    Args:
        software_name: The name of the software to research (e.g., 'Git', 'Python 3.12', 'VS Code')
    """
    print(f"[RESEARCHING] Finding installation instructions for: {software_name}...")
    
    query = f"how to install {software_name} on Windows using command line tools or chocolatey?"
    
    try:
        search_result = _tavily.search(query=query, search_depth="advanced", max_results=5)
        
        if search_result and "results" in search_result:
            instructions = []
            for result in search_result["results"]:
                title = result.get("title", "")
                url = result.get("url", "")
                instructions.append(f"{title}: {url}")
            
            print(f"[FOUND] Installation instructions found for {software_name}.")
            return "\n".join(instructions)
        
        print(f"[NOT FOUND] No installation instructions found for {software_name}.")
        return f"Error: Could not find installation instructions for {software_name}."

    except Exception as e:
        print(f"[ERROR] Tavily search failed: {e}")
        return f"Error: Search failed for installation instructions of {software_name}."

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
        "name": "download_link_search",
        "description": "Searches the internet to find download links, documentation, or software information.",
        "parameters": {
            "type": "object",
            "properties": {
                "software_name": {"type": "string", "description": "The name of the software to search for."}
            },
            "required": ["software_name"]
        }
    },
    {
        "name": "choco_command_search",
        "description": "Searches for Chocolatey package commands to install software.",
        "parameters": {
            "type": "object",
            "properties": {
                "software_name": {"type": "string", "description": "The name of the software to search for."}
            },
            "required": ["software_name"]
        }
    }
]

tools_names = [tool["name"] for tool in tools]