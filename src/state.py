from typing import Annotated, TypedDict, Dict
from pydantic import BaseModel, Field
from langgraph.graph.message import add_messages


class installation_list(BaseModel):
    to_install: list[str] = Field(..., description="List of software to install")


class AgentState(TypedDict, total=False):
    task: str
    to_install: list[str]
    installation_guides: Dict[str, str]
    installation_urls: Dict[str, str]
    messages: Annotated[list, add_messages]
