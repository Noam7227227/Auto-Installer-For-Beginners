from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.tools import StructuredTool
from dotenv import load_dotenv

from src.state import AgentState, installation_list
from src.tools import (
    tools,
    execute_system_command,
    set_env_variable,
    download_from_link,
    brave_search,
)

load_dotenv()

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)

# Wrap the mock functions as LangChain tools so a ToolNode can execute them.
# We do NOT modify the original functions or the `tools` schema list.
_FN_MAP = {
    "execute_system_command": execute_system_command,
    "set_env_variable": set_env_variable,
    "download_from_link": download_from_link,
    "brave_search": brave_search,
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


INSTALLER_SYSTEM_PROMPT = """You are an autonomous software-installation agent on a Windows machine.

You have access to these tools: brave_search, download_from_link, execute_system_command, set_env_variable.

For each piece of software the user gives you, follow this loop:
  1. Call `brave_search` to find an official download URL.
  2. Call `download_from_link` with that URL and a local destination path.
  3. Call `execute_system_command` to run the installer silently.
  4. Optionally call `set_env_variable` if the software requires PATH/env updates.

TOOL-CALL SYNTAX RULES (CRITICAL — follow exactly):
- Emit tool calls ONLY through the structured tool_calls interface. Never paste raw JSON into the assistant text.
- Every tool call MUST be a complete, well-formed JSON object: every `{` paired with `}`, every `[` paired with `]`,
  every `"` paired, and every `<` paired with `>`. Do NOT drop or omit any closing bracket, brace, quote,
  or angle bracket. Re-check the syntax before emitting.
- Argument names MUST match the schema exactly (e.g. `command`, `url`, `destination_path`, `key`, `value`, `query`).
- One logical action per tool call. Do not concatenate commands inside a single string unless absolutely needed.
- After all software is installed, reply with a short plain-text summary and NO further tool calls.
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


def software_installer_node(state: AgentState):
    """
    Assistant node: decides which tool to call next based on the conversation so far.
    On the first turn it seeds the conversation with the system prompt and the
    install list; on later turns it just continues from the running message history.
    """
    messages = state.get("messages", [])

    if not messages:
        software_list = state.get("to_install", []) or state.get("software_list", [])
        seed = [
            SystemMessage(content=INSTALLER_SYSTEM_PROMPT),
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
