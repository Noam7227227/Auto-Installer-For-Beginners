from typing import TypedDict
from pydantic import BaseModel, Field

class installation_list(BaseModel):
    to_install: list[str] = Field(..., description="List of software to install")


class AgentState(TypedDict):
    task: str
    to_install: list[str]