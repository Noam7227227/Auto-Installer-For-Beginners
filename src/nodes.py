from langgraph.types import interrupt
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage
from src.state import AgentState, installation_list, InterpreterOutput, MainAppSuggestions, SideToolSuggestions
from dotenv import load_dotenv
from tavily import TavilyClient
from pydantic import BaseModel, Field
import os

load_dotenv()
llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


def _get_content(m) -> str:
    return m.content if hasattr(m, "content") else m["content"]

def _get_role(m) -> str:
    if hasattr(m, "type"):
        return "USER" if m.type == "human" else "ASSISTANT"
    return m["role"].upper()

def _parse_side_tool_response(response: str, side_tools: list) -> list:
    r = response.lower().strip()
    if r in ("yes", "y", "all", "ok", "sure", "yeah", "install all"):
        return [t["name"] for t in side_tools]
    if any(p in r for p in ("skip all", "none", "no thanks", "nothing", "just the main", "only the main")):
        return []
    for prefix in ("only ", "just "):
        if r.startswith(prefix):
            keep_text = r[len(prefix):]
            return [t["name"] for t in side_tools if any(w in keep_text for w in t["name"].lower().split())]
    return [t["name"] for t in side_tools if not any(w in r for w in t["name"].lower().split())]


# ── interpreter ───────────────────────────────────────────────────────────────
def interpreter(state: AgentState) -> dict:
    messages = state.get("messages", [])
    convo = "\n".join(f"{_get_role(m)}: {_get_content(m)}" for m in messages) if messages else "(no conversation yet)"
    user_messages = [m for m in messages if _get_role(m) == "USER"]
    force_ready = len(user_messages) >= 3

    prompt = f"""You help users find the best software for their needs on Windows.

Conversation so far:
{convo}

Classify the task as:
- "consumption": watching, listening, planning, organizing, browsing, communicating, scheduling
- "creation": coding, designing, editing video/photos, producing music, building apps

IMPORTANT DISTINCTIONS:
- "watch a movie" = user wants to stream movies (Netflix, Disney+) → consumption, refined_task = "stream and watch movies on Windows"
- "play a video file" or "watch local videos" = user wants a media player (VLC) → consumption, refined_task = "play local video files on Windows"
- "listen to music" = streaming (Spotify) vs "play music files" = local player (foobar2000)
- When unclear, ask ONE question: "Do you want to stream movies online, or play video files stored on your computer?"

For CONSUMPTION: ready=True immediately once the task is clear
For CREATION: need (1) what to build, (2) experience level, (3) paid or free → ask one at a time

{"YOU MUST set ready=True NOW." if force_ready else "Max 2 follow-up questions."}

Never ask about OS. refined_task format: 'stream and watch movies on Windows' or 'C development for a beginner, free tools, on Windows'"""

    structured_llm = llm.with_structured_output(InterpreterOutput)
    result = structured_llm.invoke(prompt)

    if force_ready and not result.ready:
        all_text = " ".join(_get_content(m).lower() for m in messages)
        result.ready = True
        result.task_type = result.task_type or "consumption"
        result.paid_preference = result.paid_preference or "any"
        result.refined_task = result.refined_task or all_text[:80] + " on Windows"

    if result.ready:
        # If LLM returned None for refined_task, build it from the conversation
        if not result.refined_task:
            user_text = " ".join(
                _get_content(m) for m in messages if _get_role(m) == "USER"
            )
            result.refined_task = user_text.strip() + " on Windows"

        print(f"\nAssistant: Got it! Let me find the best options for you.\n")
        return {
            "interpreter_ready": True,
            "task": result.refined_task,
            "task_type": result.task_type or "consumption",
            "paid_preference": result.paid_preference or "any",
            "messages": [AIMessage(content=f"Task: {result.refined_task}")],
        }
    else:
        print(f"\nAssistant: {result.follow_up_question}")
        return {
            "interpreter_ready": False,
            "messages": [AIMessage(content=result.follow_up_question)],
        }


def human_input(state: AgentState) -> dict:
    user_reply = interrupt("waiting_for_user")
    return {"messages": [HumanMessage(content=user_reply)]}


# ── detect_medium: web or desktop? ───────────────────────────────────────────
def detect_medium(state: AgentState) -> dict:
    task = state["task"]

    class MediumOutput(BaseModel):
        medium: str = Field(..., description="'web' if best done in a browser, 'desktop' if needs installed software")

    structured_llm = llm.with_structured_output(MediumOutput)
    result = structured_llm.invoke(f"""Is this task best done via a website/web app, or by installing desktop software?

Task: {task}

Answer 'web' for: trip planning, booking hotels, email, social media, online maps, streaming services
Answer 'desktop' for: programming/coding, video editing, photo editing, music production, gaming, office work

Task to classify: {task}""")

    return {"task_medium": result.medium}


def suggest_web_options(state: AgentState) -> dict:
    task = state["task"]

    class WebOption(BaseModel):
        name: str
        url: str
        description: str
        why_recommended: str

    class WebOptionsList(BaseModel):
        options: list[WebOption]

    # Step 1: LLM picks the right websites from its own knowledge
    structured_llm = llm.with_structured_output(WebOptionsList)
    result = structured_llm.invoke(f"""Suggest 1-3 real websites or online services for: {task}

Only suggest websites that DIRECTLY help the user accomplish "{task}".
Use your own knowledge — do not guess or hallucinate URLs.

Examples of correct matching:
- "plan a trip" → wanderlog.com, tripit.com, roadtrippers.com, google.com/travel
- "book a hotel" → booking.com, hotels.com, airbnb.com
- "manage tasks" → todoist.com, notion.so, trello.com
- "edit documents online" → docs.google.com, office.com
- "learn a language" → duolingo.com, babbel.com

Include the real URL for each option.""")

    print(f"\nThis task is best done online — no installation needed!\n")
    print("Here are the top websites for you:\n")
    for i, opt in enumerate(result.options, 1):
        print(f"  [{i}] {opt.name}  →  {opt.url}")
        print(f"      {opt.description}")
        print(f"      Why: {opt.why_recommended}\n")

    print("You can open any of these directly in your browser.")
    print("\nWould you prefer a desktop app instead? (type 'yes' for desktop app, or press Enter to finish)")

    return {
        "web_options": [{"name": o.name, "url": o.url, "description": o.description} for o in result.options],
        "messages": [AIMessage(content="Would you prefer a desktop app instead?")],
    }

# ── human_picks_web_or_desktop ────────────────────────────────────────────────
def human_picks_web_or_desktop(state: AgentState) -> dict:
    response = interrupt("web_or_desktop")
    wants_desktop = response.lower().strip() in ("yes", "y", "desktop", "app", "install", "desktop app")
    return {
        "task_medium": "desktop" if wants_desktop else "web",
        "messages": [HumanMessage(content=response)],
    }


# ── finalize_web ──────────────────────────────────────────────────────────────
def finalize_web(state: AgentState) -> dict:
    web_options = state.get("web_options", [])
    print(f"\nAssistant: No installation needed! Open these in your browser:")
    for opt in web_options:
        print(f"  • {opt['name']}: {opt.get('url', '')}")
    return {
        "to_install": [],
        "messages": [AIMessage(content="Use these web services directly in your browser.")],
    }


def suggest_main_apps(state: AgentState) -> dict:
    task = state["task"]
    paid_pref = state.get("paid_preference") or "any"
    paid_clause = {"free": "free only", "paid": "paid", "any": "free or paid"}.get(paid_pref, "free or paid")

    print(f"\nAssistant: Finding options for: '{task}'...\n")   # debug line

    structured_llm = llm.with_structured_output(MainAppSuggestions)
    result = structured_llm.invoke(f"""I need you to suggest real Windows desktop apps.

The user's task is: "{task}"

You MUST suggest 1-3 real, installable Windows apps that help with this task.
Do NOT return None, empty strings, or placeholder values.

IMPORTANT DISTINCTIONS — read the task carefully:
- "stream and watch movies" → Netflix app, Amazon Prime Video app, Disney+ app
- "play local video files" → VLC Media Player, KMPlayer, PotPlayer
- "stream music" → Spotify, Amazon Music, YouTube Music
- "play local music files" → foobar2000, MusicBee, MediaMonkey
- "trip/travel planning" → TripIt, Google Earth Pro, Roadtrippers
- "C programming, beginner" → VS Code, CLion, Code::Blocks
- "photo editing" → GIMP, Paint.NET, Lightroom
- "video editing" → DaVinci Resolve, Shotcut, Kdenlive
- "writing/documents" → LibreOffice Writer, Microsoft Word, Notion
- "note taking" → Obsidian, Notion, OneNote
- "task management" → Todoist, TickTick, Microsoft To Do

Preference: {paid_clause}

For each app fill in ALL fields with real content:
- name: the actual app name
- description: one sentence about what it is
- why_recommended: why it fits this exact task
- unique_advantage: what it has that the other suggestions don't""")

    # Filter out any None results just in case
    valid_options = [o for o in result.options if o.name and o.name.lower() not in ("none", "n/a", "")]

    if not valid_options:
        # Hard fallback — use the LLM with a simpler direct prompt
        fallback = llm.invoke(f"Name the 3 best Windows apps for: {task}. Reply with just the app names, one per line.").content
        names = [line.strip() for line in fallback.strip().split("\n") if line.strip()][:3]
        valid_options = [{"name": n, "description": "", "why": "", "unique": ""} for n in names]
        print("\nHere are the best options for you:\n")
        for i, opt in enumerate(valid_options, 1):
            print(f"  [{i}] {opt['name']}\n")
        return {
            "main_app_options": valid_options,
            "messages": [AIMessage(content=f"Here are {len(valid_options)} options. Which would you like? (enter a number)")],
        }

    # Tavily enriches each valid suggestion
    enriched_options = []
    for opt in valid_options:
        try:
            search = tavily.search(query=f"{opt.name} Windows app 2024", max_results=2)
            extra = search["results"][0]["content"][:200] if search["results"] else ""
        except Exception:
            extra = ""
        enriched_options.append({
            "name": opt.name,
            "description": opt.description,
            "why": opt.why_recommended,
            "unique": opt.unique_advantage,
            "extra": extra,
        })

    print("\nHere are the best options for you:\n")
    for i, opt in enumerate(enriched_options, 1):
        print(f"  [{i}] {opt['name']}")
        print(f"      {opt['description']}")
        print(f"      Why for you: {opt['why']}")
        print(f"      Unique advantage: {opt['unique']}\n")

    web_note = llm.invoke(
        f"For the task '{task}', is there a useful free website that does the same thing? "
        f"If yes, reply with ONE line only, like: 'Also available online: wanderlog.com' "
        f"If no good web alternative exists, reply with exactly: 'none'"
    ).content.strip()

    if web_note.lower() != "none":
        print(f"  Tip: {web_note}\n")

    return {
        "main_app_options": enriched_options,
        "messages": [AIMessage(content=f"Here are {len(enriched_options)} options. Which would you like? (enter a number)")],
    }
    
def human_picks_main(state: AgentState) -> dict:
    print("Which would you like to install? (enter 1, 2, or 3)")
    choice = interrupt("waiting_for_main_app_choice")

    options = state.get("main_app_options", [])
    try:
        index = int(choice.strip()) - 1
        chosen = options[index]["name"] if 0 <= index < len(options) else options[0]["name"]
    except (ValueError, IndexError):
        chosen = next((o["name"] for o in options if o["name"].lower() in choice.lower()), options[0]["name"])

    print(f"\nAssistant: Great choice! You selected {chosen}.\n")
    return {
        "chosen_main_app": chosen,
        "messages": [AIMessage(content=f"Selected: {chosen}")],
    }


def finalize_consumption(state: AgentState) -> dict:
    chosen = state["chosen_main_app"]
    print(f"\nAssistant: Here is your final installation list:")
    print(f"  • {chosen}")
    return {
        "to_install": [chosen],
        "messages": [AIMessage(content=f"Final list: {chosen}")],
    }


def suggest_side_tools(state: AgentState) -> dict:
    task = state["task"]
    chosen = state["chosen_main_app"]
    structured_llm = llm.with_structured_output(SideToolSuggestions)

    result = structured_llm.invoke(f"""The user wants to: {task}
They chose {chosen} on Windows.

List only truly essential companion tools needed alongside {chosen}.
Do NOT include {chosen} itself. Only genuinely required tools.
For each: one sentence on what it does and why it's needed.""")

    if not result.tools:
        print(f"\nAssistant: No additional tools needed alongside {chosen}.\n")
        return {
            "side_tools": [],
            "messages": [AIMessage(content="No side tools needed.")],
        }

    print(f"\nAlong with {chosen}, here are the recommended companion tools:\n")
    for tool in result.tools:
        print(f"  • {tool.name}")
        print(f"    {tool.what_it_does}\n")

    print("Type 'yes' to install all, 'only <name>' to keep specific ones, or 'skip <name>' to remove some.")

    return {
        "side_tools": [{"name": t.name, "what_it_does": t.what_it_does} for t in result.tools],
        "messages": [AIMessage(content="Which side tools would you like?")],
    }


def human_confirms_side_tools(state: AgentState) -> dict:
    side_tools = state.get("side_tools", [])

    if not side_tools:
        final_list = [state["chosen_main_app"]]
        print(f"\nAssistant: Final installation list:")
        for item in final_list:
            print(f"  • {item}")
        return {
            "to_install": final_list,
            "messages": [AIMessage(content=f"Final list: {', '.join(final_list)}")],
        }

    response = interrupt("waiting_for_side_tools_confirmation")
    confirmed_side = _parse_side_tool_response(response, side_tools)
    final_list = [state["chosen_main_app"]] + confirmed_side

    print(f"\nAssistant: Perfect! Here is your final installation list:")
    for item in final_list:
        print(f"  • {item}")

    return {
        "to_install": final_list,
        "messages": [AIMessage(content=f"Final list: {', '.join(final_list)}")],
    }


def installments_filler(state: AgentState):
    task = state["task"]
    structured_llm = llm.with_structured_output(installation_list)
    result = structured_llm.invoke(f"List software to install for: '{task}'. Names only.")
    return {"to_install": result.to_install}