from typing import TypedDict
from app.llm import call_llm
from langgraph.graph import END, START, StateGraph


class AgentState(TypedDict):
    messages: list[dict[str, str]]


async def receive_message(state: AgentState) -> dict:
    response = await call_llm(state["messages"])

    return {
        "messages": state["messages"] + [
            {"role": "assistant", "content": response}
        ]
    }


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("receive_message", receive_message)
    graph.add_edge(START, "receive_message")
    graph.add_edge("receive_message", END)

    return graph.compile()
