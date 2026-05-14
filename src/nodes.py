from langchain_groq import ChatGroq
from src.state import AgentState, installation_list
from dotenv import load_dotenv
load_dotenv()

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)

def installments_filler(state: AgentState):
    task = state["task"]
    structured_llm = llm.with_structured_output(installation_list)
    prompt = f"Given the task: '{task}', list the software that needs to be installed to accomplish this task. Return only the names of the software without any additional text."
    result = structured_llm.invoke(prompt)
    return {"to_install": result.to_install}