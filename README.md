# Auto-Installer for Beginners (AIFB)
"Because installing software shouldn't feel like a side-quest."

AIFB (Auto-Installer for Beginners) is an intelligent, agentic system that transforms natural language requests into fully installed software. No more navigating confusing download pages or clicking through "Next-Next-Finish" wizards.

## Why AIFB?
Traditional installers are tedious. AIFB uses Agentic AI to act as your personal system administrator.

Broad Coverage: If it's on Chocolatey, AIFB can install it.

Zero-Click Execution: The agent handles license agreements, paths, and dependencies automatically.

Natural Language Discovery: Tell the agent "I want to start editing videos" and it will research and suggest (then install) the best tools like DaVinci Resolve or OBS.

## Architecture
AIFB splits the "thinking" from the "doing" to keep your system secure and the AI responsive:

1. The Brain (LangGraph Agent): Processes user requests, researches softwares and relevant tools and packages , and sends commands via a secure socket.

2. The Muscle (Desktop Agent): A background Windows service (managed by NSSM) that listens for commands and executes them via subprocess.

3. The Package Manager: Chocolatey handles the heavy lifting of installation.

## Tech Stack
Orchestration: LangGraph (for complex multi-step installs).

LLM Gateway: OpenRouter (access to Claude/GPT-4 for research).

Service Wrapper: NSSM (Non-Sucking Service Manager).

Package Engine: Chocolatey.

IPC: Python multiprocessing.connection for brain-to-muscle communication.

## Quick Start
1. Installation
`git clone https://github.com/Noam7227227/Auto-Installer-For-Beginners
cd Auto-Installer-For-Beginners
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt`

2. Launch the Brain
Ensure your .env has your OPENROUTER_API_KEY, then:
`python src/main.py`

3. Deploy the Muscle (Admin Required)
Run our automated setup script to install the background service (run as admin):
`.\install-agent.ps1`

## Example Prompts
- "I need the basics: Chrome, Spotify, and VLC."

- "Set up a workstation for a Graphic Designer."

- "I want to play Minecraft, install whatever I need for that."

- "Install the professional version of PyCharm and Docker."


