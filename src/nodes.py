from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.tools import StructuredTool

from dotenv import load_dotenv

from src.state import AgentState, installation_list
from src.tools import (
    research_installer_tool,
    tools,
    execute_system_command,
    set_env_variable,
    download_from_link,
    download_link_search,
    choco_command_search,
)

load_dotenv()

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)

# Wrap the mock functions as LangChain tools so a ToolNode can execute them.
# We do NOT modify the original functions or the `tools` schema list.
_FN_MAP = {
    "execute_system_command": execute_system_command,
    "set_env_variable": set_env_variable,
    "download_from_link": download_from_link,
    "download_link_search": download_link_search,
    "choco_command_search": choco_command_search,
}

lc_tools = [
    StructuredTool.from_function(
        func=_FN_MAP[t["name"]],
        name=t["name"],
        description=t["description"],
    )
    for t in tools
]

llm_with_tools = llm.bind_tools(lc_tools)


INSTALLER_SYSTEM_PROMPT = """SYSTEM MESSAGE:
You are an expert System Automation Agent. Your goal is to install softwares by following the provided Research Guides exactly.

TOOLS AVAILABLE:
- download_link_search: Use this to find a direct URL if the guide mentions a download.
- download_from_link: Use this to save a file to the local disk.
- execute_system_command: Use this to run installers (.exe, .msi) or shell commands (pip, npm, winget).
- set_env_variable: Use this if the guide mentions updating the PATH or specific variables.
- choco_command_search: Use this to find Chocolatey package commands for installing software.

INSTRUCTIONS:
1. Review the `installation_guides` provided in the state for each software.
2. DECIDE the path based on the guide:
   - IF THE GUIDE SAYS "USE A COMMAND" (e.g., pip, npm, winget):
     * Call `execute_system_command` immediately with the suggested command.
   - IF THE GUIDE SAYS "DOWNLOAD AND RUN":
     * Call `download_link_search` to find the official link.
     * Call `download_from_link` to download the file.
     * Call `execute_system_command` to run the installer silently (e.g., /S or /silent flags).
3. If the guide mentions environment variables, call `set_env_variable` as the final step.

TOOL-CALL SYNTAX RULES (CRITICAL — follow exactly):
- Emit tool calls ONLY through the structured tool_calls interface. Never paste raw JSON into the assistant text.
- Every tool call MUST be a complete, well-formed JSON object: every `{` paired with `}`, every `[` paired with `]`,
  every `"` paired, and every `<` paired with `>`. Do NOT drop or omit any closing bracket, brace, quote,
  or angle bracket. Re-check the syntax before emitting.
- Argument names MUST match the schema exactly (e.g. `command`, `url`, `destination_path`, `key`, `value`, `query`).
- One logical action per tool call. Do not concatenate commands inside a single string unless absolutely needed.
- After all software is installed, reply with a short plain-text summary and NO further tool calls.

CURRENT TASK:
Install the following softwares: {to_install}
Research Guides: {installation_guides}
"""


def install_filler(state: AgentState):
    task = state["task"]
    structured_llm = llm.with_structured_output(installation_list)
    prompt = (
        f"Given the task: '{task}', list the software that needs to be installed "
        "to accomplish this task. Return only the names of the software."
    )
    result = structured_llm.invoke(prompt)
    return {"to_install": result.to_install}


def research_installer(state: AgentState):
    # Ensure the dictionary exists
    guides = state.get("installation_guides", {})
    
    for software in state["to_install"]:
        # 1. Call your search function directly to get the raw results
        raw_results = research_installer_tool(software)
        
        # 2. Use the LLM to summarize the raw links into a clean instruction
        prompt = (
            f"I found the following information for installing {software} on Windows:\n"
            f"{raw_results}\n\n"
            "Please summarize this into a clear, 1-2 sentence installation guide. "
            "Tell me if I should use a download link or a command like 'pip' or 'npm'."
        )
        
        # We invoke the LLM normally (no tools needed) to process the search text
        response = llm.invoke(prompt)
        
        # 3. Store the clean summary
        guides[software] = response.content
        
    return {"installation_guides": guides}

def software_installer_node(state: AgentState):
    """
    Assistant node: decides which tool to call next based on the conversation so far.
    On the first turn it seeds the conversation with the system prompt and the
    install list; on later turns it just continues from the running message history.
    """
    messages = state.get("messages", [])

    if not messages:
        software_list = state.get("to_install", []) or state.get("software_list", [])
        
        guides_str = str(state.get("installation_guides", {}))
        software_str = ", ".join(software_list)

        system_content = INSTALLER_SYSTEM_PROMPT.replace(
            "{to_install}", software_str
        ).replace(
            "{installation_guides}", guides_str
        )

        seed = [
            SystemMessage(content=system_content),
            HumanMessage(
                content=(
                    "Please install the following software, one at a time, using the tools: "
                    f"{', '.join(software_list)}."
                )
            ),
        ]
        response = llm_with_tools.invoke(seed)
        return {"messages": seed + [response]}

    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}