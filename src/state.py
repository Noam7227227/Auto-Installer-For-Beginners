from typing import Annotated, TypedDict, Dict, Optional, Annotated
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field
from langgraph.graph.message import add_messages


class installation_list(BaseModel):
    to_install: list[str] = Field(..., description="List of software to install")


class InterpreterOutput(BaseModel):
    ready: bool
    follow_up_question: Optional[str] = Field(None)
    refined_task: Optional[str] = Field(None)
    task_type: Optional[str] = Field(None, description="'consumption' or 'creation'")
    paid_preference: Optional[str] = Field(None, description="'free', 'paid', or 'any'")

class AppOption(BaseModel):
    name: str = Field(..., description="IDE or editor name")
    description: str = Field(..., description="One sentence: what it is")
    why_recommended: str = Field(..., description="Why it suits this specific user")
    unique_advantage: str = Field(..., description="What this option offers that the other suggested options don't")

class MainAppSuggestions(BaseModel):
    options: list[AppOption] = Field(..., description="1 to 3 options, best fit first")

class SideTool(BaseModel):
    name: str
    what_it_does: str = Field(..., description="One sentence: what this tool does and why it is needed")

class SideToolSuggestions(BaseModel):
    tools: list[SideTool]


class InterpreterOutput(BaseModel):
    ready: bool
    follow_up_question: Optional[str] = Field(None)
    refined_task: Optional[str] = Field(None)
    task_type: Optional[str] = Field(None, description="'consumption' or 'creation'")
    paid_preference: Optional[str] = Field(None, description="'free', 'paid', or 'any'")

class AppOption(BaseModel):
    name: str = Field(..., description="IDE or editor name")
    description: str = Field(..., description="One sentence: what it is")
    why_recommended: str = Field(..., description="Why it suits this specific user")
    unique_advantage: str = Field(..., description="What this option offers that the other suggested options don't")

class MainAppSuggestions(BaseModel):
    options: list[AppOption] = Field(..., description="1 to 3 options, best fit first")

class SideTool(BaseModel):
    name: str
    what_it_does: str = Field(..., description="One sentence: what this tool does and why it is needed")

class SideToolSuggestions(BaseModel):
    tools: list[SideTool]


class AgentState(TypedDict):
    task: str
    to_install: list[str]
    messages: Annotated[list, add_messages]
    interpreter_ready: bool
    task_type: Optional[str]
    task_medium: Optional[str]
    paid_preference: Optional[str]
    main_app_options: Optional[list]
    chosen_main_app: Optional[str]
    side_tools: Optional[list]
    web_options: Optional[list]
    installation_messages: Optional[list]
    installation_guides: Dict[str, str]
    installation_urls: Dict[str, str]
